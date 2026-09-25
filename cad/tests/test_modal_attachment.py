#!/usr/bin/env python3
"""Deck invariants for the three modal attachment modes (closeout T3).

No solver is run here: these check what the generated deck CONTAINS, which is the part that silently
went wrong before. The solved frequencies live in runs/mast_modal_attachment_20260925/study.json."""
from __future__ import annotations

import json, math, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
STUDY = ROOT / "runs" / "mast_modal_attachment_20260925" / "study.json"


class FakeMesh:
    """A two-node stand-in: one off-axis tip node and one root node. Enough to exercise deck writing
    without meshing, since the invariants under test are textual."""

    def __init__(self):
        self.nodes = {1: (0.0, 0.0, 0.0), 2: (0.0085, 0.0, 0.1)}
        self.c3d10 = []
        self.root_nodes = [1]
        self.tip_nodes = [2]
        self.tip_center_node = 2
        self.gauge_nodes = []


def deck(attachment):
    import mast_fea as mf
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.inp"
        rec = mf.write_modal_inp(FakeMesh(), p, attachment=attachment)
        return p.read_text(), rec


class DeckInvariantTests(unittest.TestCase):
    def test_legacy_has_no_coupling_and_sits_off_axis(self):
        txt, rec = deck("legacy")
        self.assertNotIn("*RIGID BODY", txt)
        self.assertFalse(rec["rigid_coupled_to_tip_plane"])
        self.assertAlmostEqual(rec["radial_offset_m"], 0.0085, places=9)
        self.assertEqual(rec["mass_node"], 2)          # the existing wall node

    def test_centred_reference_is_on_the_axis(self):
        txt, rec = deck("coupled_centred")
        self.assertIn("*RIGID BODY", txt)
        self.assertEqual(rec["radial_offset_m"], 0.0)
        x, y, z = rec["mass_node_coords_m"]
        self.assertEqual((x, y), (0.0, 0.0))
        self.assertAlmostEqual(z, 0.1, places=9)       # still at the tip plane

    def test_eccentric_and_centred_share_one_coupling_definition(self):
        """B and C must differ ONLY in position, or the comparison isolates nothing."""
        tb, rb = deck("coupled_eccentric")
        tc, rc = deck("coupled_centred")
        coup = lambda t: [l for l in t.splitlines() if l.startswith("*RIGID BODY")]
        self.assertEqual(coup(tb), coup(tc))
        self.assertTrue(rb["rigid_coupled_to_tip_plane"] and rc["rigid_coupled_to_tip_plane"])
        self.assertNotEqual(rb["mass_node_coords_m"], rc["mass_node_coords_m"])

    def test_every_mode_fixes_the_root_and_adds_the_same_mass(self):
        for att in ("legacy", "coupled_eccentric", "coupled_centred"):
            txt, rec = deck(att)
            with self.subTest(attachment=att):
                self.assertIn("NROOT, 1, 3", txt)
                self.assertIn("*MASS, ELSET=ETIPMASS", txt)
                self.assertAlmostEqual(rec["added_mass_kg"], 0.175, places=6)

    def test_no_independent_rotation_reference_node_is_declared(self):
        """A free artificial rotation DOF would introduce spurious near-zero modes."""
        for att in ("coupled_eccentric", "coupled_centred"):
            txt, _ = deck(att)
            self.assertNotIn("ROT NODE", txt)

    def test_unknown_attachment_is_refused(self):
        with self.assertRaises(ValueError):
            deck("something_else")


@unittest.skipUnless(STUDY.exists(), "solver study not present")
class SolvedStudyTests(unittest.TestCase):
    """Guards on the committed solver evidence, so a later edit cannot quietly restate it."""

    @classmethod
    def setUpClass(cls):
        cls.s = json.loads(STUDY.read_text())

    def test_legacy_reproduces_the_committed_historical_frequency(self):
        hz = self.s["cases"]["legacy"]["identification"]["first_bending_hz"]
        self.assertAlmostEqual(hz, 285.5, delta=0.1)

    def test_no_case_produced_a_spurious_mechanism(self):
        for name, c in self.s["cases"].items():
            with self.subTest(case=name):
                self.assertEqual(c["checks"]["near_zero_modes"], [])
                self.assertAlmostEqual(c["checks"]["added_mass_kg"], 0.175, places=6)

    def test_the_centred_case_is_axisymmetric(self):
        """A centred mass on an axisymmetric tube must give a near-degenerate bending pair. This is an
        independent physical check that the coupling is doing what it claims."""
        pair = self.s["cases"]["coupled_centred"]["identification"]["bending_pair_hz"]
        self.assertLess(abs(pair[1] - pair[0]), 0.05)
        legacy = self.s["cases"]["legacy"]["identification"]["bending_pair_hz"]
        self.assertGreater(abs(legacy[1] - legacy[0]), 5.0)   # the off-axis mass splits the pair

    def test_the_confounded_comparison_is_labelled_as_such(self):
        c = self.s["confounded_comparison"]
        self.assertIn("NOT the eccentricity effect", c["warning"])

    def test_no_new_headline_frequency_is_adopted(self):
        self.assertFalse(self.s["adoption"]["adopted"])
        self.assertIn("convergence", self.s["adoption"]["reason"])
        self.assertEqual(self.s["historical_reference"]["committed_fea_hz"], 285.5)


if __name__ == "__main__":
    unittest.main()
