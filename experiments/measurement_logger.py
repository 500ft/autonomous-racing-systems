#!/usr/bin/env python3
"""Host recorder and deterministic replay for the measurement_node NDJSON stream (week plan E2).

    python experiments/measurement_logger.py --replay experiments/fixtures/measurement_logger/valid.jsonl --output OUT
    python experiments/measurement_logger.py --port /dev/tty.usbmodem* --seconds 60 --output OUT --source-kind measured

Replay needs nothing beyond the standard library. Serial capture imports pyserial lazily; without a
board there is nothing to capture and that is a prerequisite, not a replay failure.

Output directory: stream.jsonl (input bytes, unchanged), samples.csv, diagnostics.json, manifest.json,
and for live capture host_times.csv (line number -> host receive ns). Raw counts are uncalibrated ADC
output; force_N does not exist here because no calibration record exists (E3).
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL_SCALE = (1 << 23) - 1
GAP_PERIODS = 3.0          # a timing gap is > this many nominal conversion periods


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(lines):
    """Parse NDJSON lines into (samples, diagnostics). Deterministic for identical input.

    Every input line is either a session/sample/error record or a malformed line; nothing is
    dropped, interpolated, or reordered. Flags travel with the record that raised them."""
    samples, diags, sessions = [], [], []
    cur = None          # current session record
    last = None         # last sample or error in the current session
    seen_seq = set()
    for n, line in enumerate(lines, 1):
        text = line.rstrip("\r\n")
        if not text.strip():
            continue
        try:
            rec = json.loads(text)
            if not isinstance(rec, dict):
                raise ValueError("not an object")
        except ValueError as e:
            diags.append(dict(line=n, flag="malformed_line", detail=str(e), raw=text[:200]))
            continue
        kind = rec.get("type")
        if kind == "session":
            if cur is not None:
                diags.append(dict(line=n, flag="session_boundary", detail=f"{cur.get('session_id')} -> {rec.get('session_id')}"))
            cur, last, seen_seq = rec, None, set()
            sessions.append(rec)
            continue
        if kind not in ("sample", "error"):
            diags.append(dict(line=n, flag="unknown_record_type", detail=str(kind)))
            continue
        flags = []
        if cur is None:
            flags.append("sample_before_session")
        elif rec.get("session_id") != cur.get("session_id"):
            flags.append("session_id_mismatch")
        if cur is not None and rec.get("config_id") != cur.get("config_id"):
            flags.append("config_change")
        seq, t = rec.get("seq"), rec.get("t_ns")
        if not isinstance(seq, int) or not isinstance(t, int):
            flags.append("invalid_header")
        else:
            if seq in seen_seq:
                flags.append("duplicate_sequence")   # same conversion identity seen twice = stale
            seen_seq.add(seq)
            if last is not None:
                ls, lt = last.get("seq"), last.get("t_ns")
                if isinstance(ls, int) and seq < ls:
                    flags.append("sequence_reversal")
                elif isinstance(ls, int) and seq > ls + 1:
                    flags.append(f"sequence_gap:{seq - ls - 1}")
                if isinstance(lt, int) and t < lt:
                    flags.append("time_reversal")
                elif isinstance(lt, int) and cur is not None:
                    rate = (cur.get("config") or {}).get("poll_rate_sps")
                    if rate and (t - lt) > GAP_PERIODS * 1e9 / rate:
                        flags.append(f"timing_gap:{(t - lt) / 1e6:.1f}ms")
        raw = rec.get("raw_counts") if kind == "sample" else None
        if kind == "sample":
            if not isinstance(raw, int) or isinstance(raw, bool) or (isinstance(raw, float) and not math.isfinite(raw)):
                flags.append("invalid_value")
                raw = None
            elif abs(raw) >= FULL_SCALE:
                flags.append("clipping")
        samples.append(dict(line=n, type=kind, session_id=rec.get("session_id"), seq=seq, t_ns=t,
                            raw_counts=raw, status=rec.get("status"), detail=rec.get("detail"), flags=";".join(flags)))
        for f in flags:
            diags.append(dict(line=n, flag=f.split(":")[0], detail=f))
        last = rec
    return samples, diags, sessions


def write_outputs(out: Path, raw_bytes: bytes, samples, diags, sessions, manifest):
    out.mkdir(parents=True, exist_ok=True)
    (out / "stream.jsonl").write_bytes(raw_bytes)
    with (out / "samples.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["line", "type", "session_id", "seq", "t_ns", "raw_counts", "status", "detail", "flags"])
        w.writeheader(); w.writerows(samples)
    counts = {}
    for d in diags:
        counts[d["flag"]] = counts.get(d["flag"], 0) + 1
    (out / "diagnostics.json").write_text(json.dumps(dict(flag_counts=counts, entries=diags), indent=1) + "\n")
    ok = [s for s in samples if s["type"] == "sample" and not s["flags"]]
    manifest.update(
        schema_version=(sessions[0].get("schema_version") if sessions else None),
        sensor_id=(sessions[0].get("sensor_id") if sessions else None),
        config_id=(sessions[0].get("config_id") if sessions else None),
        firmware=(sessions[0].get("firmware") if sessions else None),
        calibration_id=None, units="adc_counts_24bit_signed (uncalibrated; force_N absent until an E3 calibration record exists)",
        sessions=[s.get("session_id") for s in sessions], n_lines=len(raw_bytes.splitlines()),
        n_samples=sum(1 for s in samples if s["type"] == "sample"), n_clean_samples=len(ok),
        n_errors=sum(1 for s in samples if s["type"] == "error"), n_flags=len(diags),
        t_ns_first=(ok[0]["t_ns"] if ok else None), t_ns_last=(ok[-1]["t_ns"] if ok else None),
        stream_sha256=sha256(raw_bytes),
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def source_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def replay(path: Path, out: Path, source_kind: str, measured_sha: str | None = None):
    raw = path.read_bytes()
    if source_kind == "measured" and measured_sha and sha256(raw) != measured_sha:
        raise SystemExit(f"REFUSED: {path} sha256 does not match the recorded measured-source hash")
    samples, diags, sessions = parse(raw.decode("utf-8", errors="replace").splitlines(True))
    manifest = dict(source_kind=source_kind, source_path=str(path), source_sha256=sha256(raw),
                    source_commit=source_commit(), mode="replay", complete=True, truncated_reason=None,
                    note="replay does not change the evidence class of its input; host receive times are not reproduced")
    return write_outputs(out, raw, samples, diags, sessions, manifest)


def capture(port: str, seconds: float, out: Path, source_kind: str, timeout: float, baud: int):
    try:
        import serial  # pyserial, only needed here
    except ImportError:
        raise SystemExit("capture needs pyserial (pip install pyserial); replay does not")
    chunks, host_times, buf, truncated = [], [], b"", None
    t0 = time.monotonic()
    lines = 0
    try:
        with serial.Serial(port, baud, timeout=timeout) as s:
            while time.monotonic() - t0 < seconds:
                data = s.read(4096)
                if not data:
                    if time.monotonic() - t0 > timeout and not chunks:
                        truncated = f"no data within {timeout}s"
                        break
                    continue
                chunks.append(data); buf += data
                while b"\n" in buf:
                    _, buf = buf.split(b"\n", 1)
                    lines += 1
                    host_times.append((lines, time.time_ns()))
    except KeyboardInterrupt:
        truncated = "interrupted"
    except (OSError, serial.SerialException) as e:
        truncated = f"serial error: {e}"
    raw = b"".join(chunks)
    if buf:
        truncated = truncated or "partial last line"
    samples, diags, sessions = parse(raw.decode("utf-8", errors="replace").splitlines(True))
    out.mkdir(parents=True, exist_ok=True)
    with (out / "host_times.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["line", "host_recv_ns"]); w.writerows(host_times)
    manifest = dict(source_kind=source_kind, source_path=port, source_commit=source_commit(), mode="capture",
                    host_start_ns=int(t0 * 1e9), wall_clock_start=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    complete=truncated is None, truncated_reason=truncated, note="host_times.csv holds USB arrival, not the sampling instant")
    return write_outputs(out, raw, samples, diags, sessions, manifest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replay", type=Path, help="NDJSON file to replay")
    ap.add_argument("--port", help="serial device for live capture")
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-kind", choices=["synthetic", "measured"], default="synthetic")
    ap.add_argument("--measured-sha256", help="on replay of a measured file, refuse if the file hash differs")
    a = ap.parse_args(argv)
    if bool(a.replay) == bool(a.port):
        ap.error("give exactly one of --replay or --port")
    m = replay(a.replay, a.output, a.source_kind, a.measured_sha256) if a.replay else capture(a.port, a.seconds, a.output, a.source_kind, a.timeout, a.baud)
    print(f"{m['mode']} {m['source_kind']}: {m['n_samples']} samples ({m['n_clean_samples']} clean), {m['n_errors']} errors, "
          f"{m['n_flags']} flags, complete={m['complete']} -> {a.output}")
    return 0 if m["complete"] else 3


if __name__ == "__main__":
    sys.exit(main())
