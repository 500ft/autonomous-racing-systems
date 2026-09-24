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


def cfg_with(**over):
    cfg = dict(ff.NOMINAL)
    cfg.update(fixture_stiffness_n_per_mm_x=8000.0, fixture_stiffness_n_per_mm_y=8000.0)
    cfg.update(over)
    return cfg


def screened(**over):
    """A config that passes every gate, so the PLAUSIBLE path is testable.

    The repeatability of the NOMINAL block is deliberately not used here: at 0.5 um it does not reach
    the frozen R^2 >= 0.99 gate, which is a finding of the screen, not a defect (see
    PassingRequiresEveryGateTests.test_nominal_assumed_repeatability_misses_the_r_squared_gate)."""
    cfg = cfg_with(repeatability_mm=0.00005)
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


class PassingRequiresEveryGateTests(unittest.TestCase):
    """Regression cover for the reported defect: declared values were displayed but never consulted."""

    def test_one_newton_per_mm_fixture_fails(self):
        s = ff.run(cfg_with(fixture_stiffness_n_per_mm_x=1.0, fixture_stiffness_n_per_mm_y=1.0,
                            repeatability_mm=0.00005), trials=FAST)
        self.assertEqual(s["verdict"], "NOT_PLAUSIBLE_AS_CONFIGURED")
        self.assertIn("fixture_stiffness_x", s["failed_gates"])
        self.assertIn("required", s["gate_status"]["fixture_stiffness_x"]["reason"])

    def test_one_bad_axis_is_enough_to_fail(self):
        s = ff.run(cfg_with(fixture_stiffness_n_per_mm_y=1.0, repeatability_mm=0.00005), trials=FAST)
        self.assertEqual(s["verdict"], "NOT_PLAUSIBLE_AS_CONFIGURED")
        self.assertEqual(s["failed_gates"], ["fixture_stiffness_y"])
        self.assertEqual(s["gate_status"]["fixture_stiffness_x"]["status"], "pass")

    def test_non_positive_stiffness_fails(self):
        s = ff.run(cfg_with(fixture_stiffness_n_per_mm_x=-5.0, repeatability_mm=0.00005), trials=FAST)
        self.assertIn("fixture_stiffness_x", s["failed_gates"])
        self.assertIn("not positive", s["gate_status"]["fixture_stiffness_x"]["reason"])

    def test_a_failed_r_squared_gate_prevents_plausible(self):
        s = ff.run(cfg_with(repeatability_mm=0.002), trials=FAST)
        self.assertIn("r_squared_x", s["failed_gates"])
        self.assertEqual(s["verdict"], "NOT_PLAUSIBLE_AS_CONFIGURED")

    def test_nominal_assumed_repeatability_misses_the_r_squared_gate(self):
        """A finding, not a defect: 0.5 um repeatability against a 26 um full-scale signal does not
        reach R^2 >= 0.99, and the screen now says so instead of reporting it and moving on."""
        s = ff.run(cfg_with(), trials=FAST)
        self.assertLess(s["axes"]["x"]["median_r_squared"], 0.99)
        self.assertEqual(s["verdict"], "NOT_PLAUSIBLE_AS_CONFIGURED")

    def test_every_gate_has_an_explicit_status(self):
        s = screened()
        self.assertTrue(all(g["status"] in ("pass", "fail", "unknown", "not_evaluated")
                            for g in s["gate_status"].values()))
        for key in ("fixture_stiffness_x", "fixture_stiffness_y", "relative_u95_x", "r_squared_x",
                    "indicator_resolution_and_counts", "specimen_dimensions_positive"):
            self.assertIn(key, s["gate_status"])


class SharedErrorTests(unittest.TestCase):
    """A shared error does not average away. Modelling everything as independent noise hid that."""

    @staticmethod
    def _only(term, value, cycles):
        # Isolate the term under test: quantization at 1 um would otherwise dominate and average
        # down with cycle count, masking what this test is about.
        base = dict(force_gain_relative_standard_uncertainty=0.0,
                    force_readout_relative_standard_uncertainty=0.0,
                    repeatability_mm=1e-12, uncorrected_root_rotation_mm_per_n=0.0,
                    indicator_resolution_mm=1e-9)
        base[term] = value
        old = ff.CYCLES
        ff.CYCLES = cycles
        try:
            return ff.run(cfg_with(**base), trials=FAST)["axes"]["x"]
        finally:
            ff.CYCLES = old

    def test_readout_noise_averages_down_but_calibration_gain_does_not(self):
        read_3 = self._only("force_readout_relative_standard_uncertainty", 0.004, 3)
        read_12 = self._only("force_readout_relative_standard_uncertainty", 0.004, 12)
        gain_3 = self._only("force_gain_relative_standard_uncertainty", 0.004, 3)
        gain_12 = self._only("force_gain_relative_standard_uncertainty", 0.004, 12)
        self.assertLess(read_12["relative_U95"], 0.75 * read_3["relative_U95"])   # shrinks with repeats
        self.assertGreater(gain_12["relative_U95"], 0.80 * gain_3["relative_U95"])  # does not

    def test_quantization_is_rounding_not_gaussian_noise(self):
        self.assertEqual(ff._quantize(0.00123, 0.001), 0.001)
        self.assertEqual(ff._quantize(0.00159, 0.001), 0.002)
        self.assertEqual(ff._quantize(0.5, None), 0.5)

    def test_uncorrected_root_rotation_biases_the_slope_while_r_squared_stays_high(self):
        """The counterexample: excellent linearity cannot detect a load-proportional root motion."""
        s = ff.run(cfg_with(repeatability_mm=1e-9, uncorrected_root_rotation_mm_per_n=0.005 / 20.0,
                            force_gain_relative_standard_uncertainty=0.0,
                            force_readout_relative_standard_uncertainty=0.0), trials=60)
        a = s["axes"]["x"]
        self.assertGreater(a["relative_bias"], 0.15)            # a large bias
        self.assertGreater(a["median_r_squared"], 0.99)         # with the linearity gate satisfied
        self.assertLess(a["relative_U95"], 0.10)                # and the scatter gate satisfied too

    def test_the_frozen_fea_basis_reproduces_the_reviewed_figure(self):
        # 0.005 mm of uncorrected root motion at 20 N, against the frozen FEA compliance.
        bias = (0.005 / 20.0) / mpv.FEA_COMPLIANCE_MM_PER_N
        self.assertAlmostEqual(100.0 * bias, 18.2898, places=3)


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

    def test_force_readout_is_not_the_dominant_term(self):
        """The screen's operational point: more ADC bits would not buy the campaign anything."""
        s = ff.run(cfg_with(), trials=FAST)
        ranked = [r["term"] for r in s["dominant_terms"]]
        self.assertIn("force_readout_relative", ranked)
        self.assertNotEqual(ranked[0], "force_readout_relative")


class LabellingAndCliTests(unittest.TestCase):
    def test_screen_is_labelled_and_claims_no_readiness(self):
        s = screened()
        self.assertIn("NOMINAL FEASIBILITY SCREEN ONLY", s["label"])
        self.assertEqual(s["verdict"], "PLAUSIBLE_PENDING_PHYSICAL_INPUTS", s["failed_gates"])
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

    def test_cli_is_non_zero_while_any_gate_is_unmet(self):
        """Declaring a fixture stiffness is not the same as satisfying every gate."""
        script = str(ROOT / "cad/fixture_feasibility.py")
        p = subprocess.run([sys.executable, script, "--trials", "40",
                            "--assume-fixture-stiffness", "8000"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2, p.stdout[:400])


if __name__ == "__main__":
    unittest.main()
