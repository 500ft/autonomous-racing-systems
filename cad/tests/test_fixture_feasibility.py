#!/usr/bin/env python3
"""W3.1 checks: the screen reproduces the frozen measurement-contract arithmetic, refuses to treat a
missing term as zero, and cannot hide the root-rotation contribution.

Stdlib only, so this runs in the portable environment as well as the pinned CAD one."""
from __future__ import annotations

import json, math, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cad import fixture_feasibility as ff  # noqa: E402
from experiments import mast_physical_validation as mpv  # noqa: E402

FAST = 150   # trials; the assertions below are about magnitudes, not third decimals


def screened(**over):
    cfg = dict(ff.NOMINAL)
    cfg.update(fixture_stiffness_n_per_mm_x=8000.0, fixture_stiffness_n_per_mm_y=8000.0)
    cfg.update(over)
    return ff.run(cfg, trials=FAST)


class ContractArithmeticTests(unittest.TestCase):
    def test_specimen_stiffness_matches_the_measurement_contract(self):
        self.assertAlmostEqual(ff.specimen_stiffness_n_per_mm(), 775.9836594264038, places=6)

    def test_fixture_target_is_ten_times_specimen(self):
        k = ff.specimen_stiffness_n_per_mm()
        self.assertAlmostEqual(ff.required_fixture_stiffness(k), 7759.836594264038, places=5)
        self.assertAlmostEqual(ff.required_fixture_stiffness(k), 7759.84, places=2)

    def test_ideal_four_newton_deflection_is_5_155_micrometres(self):
        d = ff.run(trials=1)["ideal_signal"]["deflection_at_4N_mm"]
        self.assertAlmostEqual(d * 1000.0, 5.15475, places=4)      # micrometres

    def test_second_moment_matches_the_design_document(self):
        self.assertAlmostEqual(ff.second_moment_mm4(20.0, 1.5), 3754.154, places=2)

    def test_station_spacing_gives_the_contract_rotation_uncertainty(self):
        # 1 um step over a 100 mm baseline: 4.08 urad, and 0.408 um at a 100 mm lever.
        theta = ff.rotation_sd_rad(0.001, 100.0)
        self.assertAlmostEqual(theta * 1e6, 4.082482904638631, places=6)
        self.assertAlmostEqual(theta * 100.0 * 1000.0, 0.4082482904638631, places=6)

    def test_gates_are_imported_from_the_frozen_protocol_not_restated(self):
        g = ff.run(trials=1)["gates"]
        self.assertEqual(g["relative_U95_max"], mpv.MAX_RELATIVE_U95)
        self.assertEqual(g["r_squared_min"], mpv.MIN_R_SQUARED)
        self.assertEqual(g["hysteresis_fraction_max"], mpv.MAX_HYSTERESIS_FRACTION)
        self.assertEqual(g["fea_relative_error_max"], mpv.MAX_FEA_RELATIVE_ERROR)
        self.assertEqual(g["indicator_counts_min"], mpv.REQUIRED_INDICATOR_COUNTS)

    def test_matrix_is_the_frozen_campaign_matrix(self):
        m = ff.run(trials=1)["matrix"]
        self.assertEqual(tuple(m["load_levels_n"]), mpv.LOAD_LEVELS_N)
        self.assertEqual((m["cycles"], m["axes"], m["directions"]), (3, ["x", "y"], ["load", "unload"]))
        self.assertEqual(m["points_per_axis"], 3 * 2 * 5)

    def test_hand_and_fea_compliance_are_kept_distinct(self):
        s = ff.run(trials=1)
        self.assertNotAlmostEqual(s["specimen"]["compliance_mm_per_n"],
                                  s["ideal_signal"]["fea_compliance_mm_per_n"], places=5)
        self.assertEqual(s["ideal_signal"]["fea_compliance_mm_per_n"], mpv.FEA_COMPLIANCE_MM_PER_N)


class UnknownNeverZeroTests(unittest.TestCase):
    def test_nominal_case_is_unknown_because_no_fixture_exists(self):
        s = ff.run(trials=FAST)
        self.assertEqual(s["verdict"], "UNKNOWN")
        self.assertIn("fixture_stiffness_n_per_mm_x", s["unknown_terms"])
        self.assertIsNone(s["dominant_terms"])
        self.assertEqual(s["stiffness_screen"]["verdict"], "UNKNOWN")
        for axis in ("x", "y"):
            self.assertEqual(s["axes"][axis]["verdict"], "UNKNOWN")

    def test_a_missing_term_cannot_be_silently_dropped(self):
        s = screened(repeatability_mm=None)
        self.assertEqual(s["verdict"], "UNKNOWN")
        self.assertIn("repeatability_mm", s["unknown_terms"])

    def test_missing_resolution_makes_three_derived_terms_unknown(self):
        s = screened(indicator_resolution_mm=None)
        self.assertEqual(s["verdict"], "UNKNOWN")
        for t in ("tip_quantization_mm", "root_quantization_mm", "residual_root_rotation_mm"):
            self.assertIn(t, s["unknown_terms"])

    def test_unknown_verdict_claims_no_number(self):
        s = ff.run(trials=FAST)
        self.assertIn("never treated as zero", s["verdict_note"])


class RootRotationTests(unittest.TestCase):
    def test_fifty_microradians_at_a_hundred_mm_lever_is_five_micrometres(self):
        s = screened(root_station_spacing_mm=None)          # spacing unknown -> UNKNOWN, not zero
        self.assertEqual(s["verdict"], "UNKNOWN")
        # the bounded-rotation figure the contract quotes, stated directly
        self.assertAlmostEqual(50e-6 * 100.0 * 1000.0, 5.0, places=9)

    def test_an_uncorrected_fifty_microradian_rotation_dominates_the_budget(self):
        """Spacing so coarse that the observed rotation uncertainty reaches 50 urad."""
        spacing = math.sqrt(2.0) * ff.quantization_sd(0.001) / 50e-6     # mm
        s = screened(root_station_spacing_mm=spacing)
        self.assertAlmostEqual(s["terms"]["root_rotation_sd_rad"], 50e-6, places=9)
        self.assertAlmostEqual(s["terms"]["residual_root_rotation_mm"] * 1000.0, 5.0, places=6)
        top = s["dominant_terms"][0]
        self.assertEqual(top["term"], "residual_root_rotation_mm")
        self.assertGreater(s["axes"]["x"]["relative_U95"], screened()["axes"]["x"]["relative_U95"])

    def test_root_rotation_is_not_covered_by_the_stiffness_ratio(self):
        note = ff.run(trials=1)["stiffness_screen"]["note"]
        self.assertIn("does not", note)
        self.assertIn("root rotation", note)


class ForceChainTests(unittest.TestCase):
    def test_five_kg_cell_covers_the_range_and_one_kg_does_not(self):
        cases = {c["cell_id"]: c for c in ff.run(trials=1)["force_chain"]}
        self.assertTrue(cases["LC-5KG-01"]["covers_campaign_range"])
        self.assertIsNone(cases["LC-5KG-01"]["refusal"])
        self.assertFalse(cases["LC-1KG-01"]["covers_campaign_range"])
        self.assertIn("cannot reach the 20.0 N campaign level", cases["LC-1KG-01"]["refusal"])

    def test_every_force_case_is_labelled_assumed_with_no_calibration(self):
        for c in ff.run(trials=1)["force_chain"]:
            self.assertIn("ASSUMED", c["evidence"])
            self.assertIn("no calibration record exists", c["evidence"])

    def test_force_uncertainty_is_not_the_dominant_term(self):
        """The screen's operational point: more ADC bits would not buy the campaign anything."""
        s = screened()
        ranked = [r["term"] for r in s["dominant_terms"]]
        self.assertEqual(ranked[-1], "force_relative")
        self.assertIn(s["next_measurement"], ("repeatability_mm", "residual_root_rotation_mm"))


class LabellingAndCliTests(unittest.TestCase):
    def test_screen_is_labelled_and_claims_no_readiness(self):
        s = screened()
        self.assertIn("NOMINAL FEASIBILITY SCREEN ONLY", s["label"])
        self.assertTrue(s["verdict"].startswith("PLAUSIBLE"))
        self.assertIn("not campaign readiness", s["verdict_note"])
        self.assertIn("not a measurement", s["verdict_note"])

    def test_indicator_screen_does_not_overclaim_the_low_load_point(self):
        s = screened()
        self.assertIn("does not mean the 4 N point has 20 counts", s["indicator_screen"]["note"])
        self.assertGreaterEqual(s["indicator_screen"]["counts_at_full_scale"],
                                mpv.REQUIRED_INDICATOR_COUNTS)

    def test_cli_exits_two_while_terms_are_unknown(self):
        script = str(ROOT / "cad/fixture_feasibility.py")
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, script, "--trials", "40", "--output", d],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("UNKNOWN", p.stderr)
            written = json.loads((Path(d) / "nominal_screen.json").read_text())
            self.assertEqual(written["verdict"], "UNKNOWN")

    def test_cli_exits_zero_only_with_an_explicitly_assumed_fixture(self):
        script = str(ROOT / "cad/fixture_feasibility.py")
        p = subprocess.run([sys.executable, script, "--trials", "40",
                            "--assume-fixture-stiffness", "8000"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
