#!/usr/bin/env python3
"""E3 checks: the fit recovers a known affine mapping, and every fault class is caught.

All fixtures are synthetic. Nothing here establishes a real calibration; the record fields that would
carry one are empty in every fixture."""
from __future__ import annotations

import json, math, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_cell_calibration as lc  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "load_cell_calibration"
B_TRUE, A_TRUE = 2.0e-5, -0.40      # the mapping the fixtures were generated from


def run(name):
    return lc.analyse(lc.load(FIX / f"{name}.json"))


def blockers(result):
    return " | ".join(b["blocker"] for b in result["blockers"])


class RecoveryTests(unittest.TestCase):
    def test_recovers_the_known_affine_mapping(self):
        r = run("known_affine")
        self.assertEqual(r["failed_conditions"], [], blockers(r))
        self.assertAlmostEqual(r["fit"]["slope_N_per_count"], B_TRUE, delta=B_TRUE * 0.005)
        self.assertAlmostEqual(r["fit"]["intercept_N"], A_TRUE, delta=0.02)
        # the fitted slope must sit inside its own stated standard error of the truth
        self.assertLess(abs(r["fit"]["slope_N_per_count"] - B_TRUE), 3 * r["fit"]["u_slope"])

    def test_reports_uncertainty_at_every_campaign_force(self):
        r = run("known_affine")
        levels = [u["force_N"] for u in r["force_uncertainty"]]
        self.assertEqual(levels, list(lc.CAMPAIGN_FORCES_N))
        for u in r["force_uncertainty"]:
            self.assertTrue(u["in_calibrated_range"], u)
            self.assertGreater(u["U95_N"], 0)

    def test_only_a_reviewed_record_with_held_out_points_is_usable(self):
        """Every required condition must pass. An unreviewed record with nothing held out is not
        usable however well it fits: that was the defect this replaces."""
        plain = run("known_affine")
        self.assertEqual(plain["verdict"], "CALIBRATION_INCOMPLETE")
        self.assertEqual(set(plain["unevaluable_conditions"]), {"held_out_scored", "reviewed"})
        full = run("known_affine_reviewed")
        self.assertEqual(full["verdict"], "CALIBRATION_USABLE", blockers(full))
        self.assertEqual((full["failed_conditions"], full["unevaluable_conditions"]), ([], []))

    def test_held_out_points_do_not_move_the_coefficients(self):
        import load_cell_calibration as _lc
        rec = _lc.load(FIX / "known_affine_reviewed.json")
        with_ho = _lc.analyse(rec)["fit"]["slope_N_per_count"]
        rec_no = dict(rec); rec_no.pop("verification_points")
        self.assertAlmostEqual(with_ho, _lc.analyse(rec_no)["fit"]["slope_N_per_count"], places=15)
        self.assertEqual(with_ho, with_ho)
        self.assertGreater(_lc.analyse(rec)["held_out"]["n"], 0)

    def test_coverage_factor_is_t_based_not_assumed_two(self):
        self.assertAlmostEqual(lc.coverage_factor(3), 3.182)   # small sample: far above 2
        self.assertAlmostEqual(lc.coverage_factor(10), 2.228)
        self.assertAlmostEqual(lc.coverage_factor(500), 1.960)
        self.assertIsNone(lc.coverage_factor(0))
        r = run("known_affine")
        self.assertEqual(r["coverage"]["degrees_of_freedom"], r["fit"]["n"] - 2)

    def test_r_squared_is_never_reported(self):
        blob = json.dumps(run("known_affine")).lower()
        self.assertNotIn("r_squared", blob)
        self.assertNotIn("r2", blob)
        self.assertIn("lack_of_fit_statistic", blob)

    @staticmethod
    def _ols(x, y):
        n = len(x); mx = sum(x) / n; my = sum(y) / n
        return sum((x[i] - mx) * (y[i] - my) for i in range(n)) / sum((xi - mx) ** 2 for xi in x)

    def test_at_this_cell_s_noise_level_ols_and_york_agree(self):
        """Honest scope of the method choice. The fixture's count noise is a negligible fraction of
        the count spread, so attenuation is immaterial and the two estimators coincide. The York fit
        is still the correct default because nothing guarantees that stays true."""
        rec = lc.load(FIX / "known_affine.json")
        pts = rec["points"]
        ols = self._ols([p["counts_mean"] for p in pts], [lc.applied_force(p, rec) for p in pts])
        york = run("known_affine")["fit"]["slope_N_per_count"]
        self.assertAlmostEqual(ols, york, delta=B_TRUE * 0.001)

    def test_york_removes_the_ols_attenuation_bias(self):
        """Why the estimator matters. Attenuation is a statement about bias, so it is measured over
        repeated draws, not one: a single noisy draw can put either estimator closer to the truth."""
        import random
        random.seed(11)
        rec = lc.load(FIX / "known_affine.json")
        base, sd, draws = rec["points"], 60_000.0, 200
        ols_s, york_s = [], []
        for _ in range(draws):
            pts = [dict(p, counts_mean=p["counts_mean"] + random.gauss(0, sd), counts_sd=sd, n=1)
                   for p in base]
            y = [lc.applied_force(p, rec) for p in pts]
            ols_s.append(self._ols([p["counts_mean"] for p in pts], y))
            york_s.append(lc.york_fit([p["counts_mean"] for p in pts], y, [sd] * len(pts),
                                      [lc.u_force(p, rec) for p in pts])["slope_N_per_count"])
        mean_ols = sum(ols_s) / draws
        mean_york = sum(york_s) / draws
        self.assertLess(mean_ols, B_TRUE * 0.99)                       # OLS biased toward zero
        self.assertLess(abs(mean_york - B_TRUE), abs(mean_ols - B_TRUE))


class FaultTests(unittest.TestCase):
    def test_missing_reference_uncertainty_is_fatal(self):
        r = run("missing_uncertainty")
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("no reference-mass uncertainty", blockers(r))
        self.assertNotIn("fit", r)                      # refused records are never fitted

    def test_one_kg_cell_cannot_serve_the_full_profile(self):
        r = run("wrong_cell_1kg")
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("cannot reach the 20.0 N campaign level", blockers(r))
        self.assertIn("over capacity", blockers(r))

    def test_wrong_units_masses_entered_as_newtons(self):
        r = run("wrong_units")
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("over capacity", blockers(r))     # 20 kg * g = 196 N on a 49 N cell

    def test_inadequate_range_flags_extrapolation(self):
        r = run("inadequate_range")
        self.assertEqual(r["verdict"], "CALIBRATION_INCOMPLETE")
        self.assertIn("would be extrapolated", blockers(r))
        self.assertFalse(r["force_uncertainty"][-1]["in_calibrated_range"])
        self.assertIn("EXTRAPOLATION", r["force_uncertainty"][-1]["note"])

    def test_clipping_is_fatal(self):
        r = run("clipping")
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("saturated counts", blockers(r))

    def test_hysteresis_over_the_declared_limit(self):
        r = run("hysteresis")
        self.assertEqual(r["verdict"], "CALIBRATION_INCOMPLETE")
        self.assertGreater(abs(r["hysteresis"]["percent_of_full_scale"]), 5.0)
        self.assertIn("hysteresis", blockers(r))

    def test_zero_drift_over_the_declared_limit(self):
        r = run("zero_drift")
        self.assertEqual(r["verdict"], "CALIBRATION_INCOMPLETE")
        self.assertIn("zero drift", blockers(r))
        self.assertGreater(abs(r["zero_drift"]["force_N"]), 0)

    def test_coarse_reference_masses(self):
        r = run("coarse_references")
        self.assertEqual(r["verdict"], "CALIBRATION_INCOMPLETE")
        self.assertIn("coarser than 1 %", blockers(r))

    def test_unreviewed_record_cannot_be_promoted(self):
        r = run("promoted_unreviewed")
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("promoted to campaign-ready while unreviewed", blockers(r))

    def test_changed_mounting_requires_a_recheck(self):
        rec = lc.load(FIX / "known_affine.json")
        rec["mount_changed_since_calibration"] = True
        r = lc.analyse(rec)
        self.assertEqual(r["verdict"], "REFUSED")
        self.assertIn("mounting changed", blockers(r))


class ConversionTests(unittest.TestCase):
    def test_conversion_inside_range_round_trips(self):
        rec = lc.load(FIX / "known_affine.json")
        r = lc.analyse(rec)
        counts = (12.0 - r["fit"]["intercept_N"]) / r["fit"]["slope_N_per_count"]
        self.assertAlmostEqual(lc.convert(rec, r, counts)["force_N"], 12.0, places=6)

    def test_conversion_outside_calibrated_range_is_refused(self):
        rec = lc.load(FIX / "known_affine.json")
        r = lc.analyse(rec)
        with self.assertRaises(SystemExit):
            lc.convert(rec, r, r["calibrated_counts_range"][1] * 2)

    def test_refused_record_cannot_convert(self):
        rec = lc.load(FIX / "missing_uncertainty.json")
        with self.assertRaises(SystemExit):
            lc.convert(rec, lc.analyse(rec), 100000)

    def test_config_mismatch_is_refused_at_the_cli(self):
        p = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "experiments/load_cell_calibration.py"),
                            "--input", str(FIX / "known_affine.json"), "--expect-config", "g64-ldo3V0-10sps-ch1"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("REFUSED", p.stderr)


class LabellingTests(unittest.TestCase):
    def test_every_fixture_is_labelled_synthetic_with_no_real_calibration(self):
        for f in sorted(FIX.glob("*.json")):
            rec = json.loads(f.read_text())
            with self.subTest(fixture=f.name):
                self.assertEqual(rec["source_kind"], "synthetic")
                self.assertIn("SOFTWARE CHECK", rec["label"])
                if rec["reviewer_state"] != "unreviewed":
                    # a fixture may carry a reviewed state only to exercise the usable path,
                    # and must then say in its own label that the review is synthetic
                    self.assertIn("SYNTHETIC", rec["label"])

    def test_a_usable_verdict_does_not_claim_campaign_readiness(self):
        r = run("known_affine_reviewed")
        self.assertIn("not campaign readiness", r["verdict_note"])

    def test_cli_exit_codes(self):
        script = str(Path(__file__).resolve().parents[1] / "experiments/load_cell_calibration.py")
        with tempfile.TemporaryDirectory() as d:
            ok = subprocess.run([sys.executable, script, "--input", str(FIX / "known_affine_reviewed.json"),
                                 "--output", d], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue((Path(d) / "analysis.json").exists())
            bad = subprocess.run([sys.executable, script, "--input", str(FIX / "clipping.json"),
                                  "--output", d], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
