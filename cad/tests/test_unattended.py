#!/usr/bin/env python3
"""Offline checks for the unattended-host helper, against a fake COM object.

The helper cannot be exercised on the SOLIDWORKS host from CI, so the contract it must honour is
pinned here: apply the toggle, read it back, record the outcome, never raise, and restore the host."""
from __future__ import annotations

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solidworks"))
import unattended  # noqa: E402

ID = unattended.SW_INPUT_DIM_VAL_ON_CREATE


class FakeSw:
    """Minimal stand-in for ISldWorks' two user-preference members."""

    def __init__(self, initial=True, write_fails=False, ignores_write=False):
        self.toggles = {ID: initial}
        self.write_fails = write_fails
        self.ignores_write = ignores_write
        self.writes = []

    def GetUserPreferenceToggle(self, ident):
        return self.toggles[ident]

    def SetUserPreferenceToggle(self, ident, value):
        self.writes.append((ident, value))
        if self.write_fails:
            raise OSError("COM error -2147352567")
        if not self.ignores_write:
            self.toggles[ident] = value


class BeginTests(unittest.TestCase):
    def test_identifier_is_the_verified_value(self):
        self.assertEqual(ID, 10)

    def test_disables_the_dimension_prompt_and_reports_it(self):
        sw = FakeSw(initial=True)
        saved, journal = unattended.begin(sw)
        self.assertFalse(sw.toggles[ID])
        entry = journal["input_dimension_value_on_create"]
        self.assertEqual((entry["was"], entry["now"], entry["applied"]), (True, False, True))
        self.assertEqual(entry["preference_id"], 10)
        self.assertEqual(saved, {ID: True})

    def test_already_off_is_still_recorded_as_applied(self):
        sw = FakeSw(initial=False)
        saved, journal = unattended.begin(sw)
        self.assertTrue(journal["input_dimension_value_on_create"]["applied"])
        self.assertEqual(saved, {ID: False})

    def test_a_write_that_raises_is_recorded_not_propagated(self):
        sw = FakeSw(initial=True, write_fails=True)
        saved, journal = unattended.begin(sw)          # must not raise
        entry = journal["input_dimension_value_on_create"]
        self.assertFalse(entry["applied"])
        self.assertIn("COM error", entry["error"])
        self.assertIn("Input dimension value", entry["note"])
        self.assertEqual(saved, {})                    # nothing to restore

    def test_a_write_that_is_silently_ignored_is_caught_by_read_back(self):
        sw = FakeSw(initial=True, ignores_write=True)
        _saved, journal = unattended.begin(sw)
        entry = journal["input_dimension_value_on_create"]
        self.assertFalse(entry["applied"])
        self.assertIn("may block", entry["note"])


class EndTests(unittest.TestCase):
    def test_restores_the_host_setting(self):
        sw = FakeSw(initial=True)
        saved, _ = unattended.begin(sw)
        self.assertFalse(sw.toggles[ID])
        self.assertEqual(unattended.end(sw, saved), {ID: True})
        self.assertTrue(sw.toggles[ID])                # host left as the operator had it

    def test_end_never_raises_on_a_failing_host(self):
        sw = FakeSw(initial=True)
        saved, _ = unattended.begin(sw)
        sw.write_fails = True
        self.assertEqual(unattended.end(sw, saved), {ID: False})

    def test_end_tolerates_no_saved_state(self):
        self.assertEqual(unattended.end(FakeSw(), None), {})


class HonestyTests(unittest.TestCase):
    def test_module_declares_it_is_not_host_verified(self):
        text = (Path(unattended.__file__)).read_text()
        self.assertIn("NOT HOST-VERIFIED", text)
        self.assertIn("read back", text)

    def test_module_does_not_claim_to_suppress_every_dialog(self):
        text = (Path(unattended.__file__)).read_text()
        self.assertIn("not a general", text)


if __name__ == "__main__":
    unittest.main()
