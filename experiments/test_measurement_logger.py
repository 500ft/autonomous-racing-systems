#!/usr/bin/env python3
"""E2 checks: replay is deterministic and dependency-free; every fault class is retained and flagged."""
from __future__ import annotations

import csv, json, sys, tempfile, types, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measurement_logger as ml  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "measurement_logger"


def rows(out: Path):
    with (out / "samples.csv").open(newline="") as f:
        return list(csv.DictReader(f))


class ReplayTests(unittest.TestCase):
    def test_replay_imports_no_serial_dependency(self):
        self.assertNotIn("serial", sys.modules)

    def test_valid_session_is_clean_and_labelled_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            m = ml.replay(FIX / "valid.jsonl", Path(d), "synthetic")
            self.assertEqual((m["n_samples"], m["n_clean_samples"], m["n_flags"], m["n_errors"]), (30, 30, 0, 0))
            self.assertEqual(m["source_kind"], "synthetic")
            self.assertIsNone(m["calibration_id"])
            self.assertNotIn("force", open(Path(d) / "samples.csv").readline())
            self.assertEqual((Path(d) / "stream.jsonl").read_bytes(), (FIX / "valid.jsonl").read_bytes())

    def test_every_fault_class_is_retained_and_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            ml.replay(FIX / "faults.jsonl", Path(d), "synthetic")
            counts = json.loads((Path(d) / "diagnostics.json").read_text())["flag_counts"]
            for flag in ("sequence_gap", "duplicate_sequence", "sequence_reversal", "timing_gap", "clipping",
                         "invalid_value", "malformed_line", "config_change", "session_boundary"):
                self.assertIn(flag, counts, flag)
            r = rows(Path(d))
            self.assertEqual(sum(1 for x in r if x["type"] == "error"), 1)
            self.assertEqual([x["raw_counts"] for x in r if "invalid_value" in x["flags"]], [""])  # retained, value blanked
            # a device reset (new session record) restarts seq without a reversal flag
            second = [x for x in r if x["session_id"] == "1a2b3c4d-77aa88bb"]
            self.assertEqual([x["flags"] for x in second], ["", ""])

    def test_replay_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ml.replay(FIX / "faults.jsonl", Path(a), "synthetic"); ml.replay(FIX / "faults.jsonl", Path(b), "synthetic")
            for name in ("samples.csv", "diagnostics.json"):
                self.assertEqual((Path(a) / name).read_bytes(), (Path(b) / name).read_bytes(), name)

    def test_measured_replay_refuses_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                ml.replay(FIX / "valid.jsonl", Path(d), "measured", "0" * 64)
            good = ml.sha256((FIX / "valid.jsonl").read_bytes())
            self.assertEqual(ml.replay(FIX / "valid.jsonl", Path(d), "measured", good)["source_kind"], "measured")

    def test_missing_samples_and_corrupt_values_never_interpolate(self):
        lines = (FIX / "valid.jsonl").read_text().splitlines(True)
        del lines[10:13]                                   # three missing conversions
        lines.insert(5, '{"type":"sample","schema_version":1,"session_id":"1a2b3c4d-9f0e1d2c","seq":4,"t_ns":1500000000,"config_id":"g128-ldo3V0-10sps-ch1","status":"ok","raw_counts":1.5e999}\n')
        samples, diags, _ = ml.parse(lines)
        flags = {d["flag"] for d in diags}
        self.assertIn("sequence_gap", flags); self.assertIn("duplicate_sequence", flags)
        self.assertEqual(len(samples), 28)                 # 30 - 3 + 1: nothing filled in, nothing dropped


class CaptureTests(unittest.TestCase):
    """Serial capture with a fake pyserial: split lines, disconnect, host times."""

    def _fake_serial(self, chunks, raise_after=None):
        mod = types.ModuleType("serial")
        class SerialException(Exception): ...
        class Serial:
            def __init__(self, *a, **k): self.i = 0
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, n):
                if raise_after is not None and self.i >= raise_after:
                    raise SerialException("device disconnected")
                c = chunks[self.i] if self.i < len(chunks) else b""
                self.i += 1
                return c
        mod.Serial, mod.SerialException = Serial, SerialException
        return mod

    def _run(self, chunks, raise_after=None):
        sys.modules["serial"] = self._fake_serial(chunks, raise_after)
        try:
            with tempfile.TemporaryDirectory() as d:
                m = ml.capture("FAKE", seconds=0.5, out=Path(d), source_kind="measured", timeout=0.05, baud=115200)
                return m, rows(Path(d)), (Path(d) / "host_times.csv").read_text().splitlines()
        finally:
            del sys.modules["serial"]

    def test_split_lines_reassemble_identically(self):
        data = (FIX / "valid.jsonl").read_bytes()
        chunks = [data[i:i + 37] for i in range(0, len(data), 37)]        # boundaries land mid-record
        m, r, host = self._run(chunks)
        self.assertEqual((m["n_samples"], m["n_flags"], m["complete"]), (30, 0, True))
        self.assertEqual(len(host), 1 + 31)                                 # header + session + 30 samples
        self.assertEqual(m["source_kind"], "measured")

    def test_disconnect_is_truncated_not_complete(self):
        data = (FIX / "valid.jsonl").read_bytes()
        chunks = [data[i:i + 200] for i in range(0, len(data), 200)]
        m, r, _ = self._run(chunks, raise_after=8)
        self.assertFalse(m["complete"]); self.assertIn("disconnected", m["truncated_reason"])
        self.assertGreater(m["n_samples"], 0)                               # what arrived stays inspectable

    def test_no_data_is_a_capture_prerequisite_not_a_crash(self):
        m, r, _ = self._run([b""] * 50)
        self.assertFalse(m["complete"]); self.assertEqual(r, [])


if __name__ == "__main__":
    unittest.main()
