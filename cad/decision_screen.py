#!/usr/bin/env python3
"""W3.2 decision screen: reproducible scenarios behind the three input requests (closeout T1).

    python cad/decision_screen.py --output evidence/week-2026-09-19/decision_screen

Writes scenarios.json, results.json and reproduction.txt. It answers one question: which *feasible
intervention* most reduces the risk that a campaign is rejected, given that every physical term here
is ASSUMED. It is not a measurement, not a purchase specification, and not an approved threshold.

Why pass fractions and not medians: at 0.3 um assumed repeatability the median R^2 passes while a
substantial fraction of simulated campaigns is rejected. A passing median is not campaign reliability.
"""
from __future__ import annotations

import argparse, json, math, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cad import fixture_feasibility as ff  # noqa: E402

SEED = 20260925
TRIALS = 1000
BOUNDARY_TRIALS = 5000          # decision-boundary cases get more draws
ASSUMED_STIFFNESS = 8000.0      # to exercise the screen only; no fixture exists
ADVERSE_ROTATION = 0.00025      # mm/N, explicitly synthetic adverse case


def base_cfg(**over):
    """Nominal terms plus an explicitly ASSUMED fixture stiffness, so the axes can be simulated."""
    cfg = dict(ff.NOMINAL)
    cfg.update(fixture_stiffness_n_per_mm_x=ASSUMED_STIFFNESS, fixture_stiffness_n_per_mm_y=ASSUMED_STIFFNESS)
    cfg.update(over)
    return cfg


def one(cfg, trials, seed=SEED):
    """Per-axis distribution plus the joint two-axis campaign result."""
    t = ff.terms(cfg)
    compliance = 1.0 / ff.specimen_stiffness_n_per_mm()
    axis = ff.screen_axis(compliance, t, cfg, trials, seed)
    joint = ff.screen_campaign(compliance, t, cfg, trials, seed + 1)
    return dict(
        repeatability_mm=cfg["repeatability_mm"], resolution_mm=cfg["indicator_resolution_mm"],
        root_station_spacing_mm=cfg["root_station_spacing_mm"],
        uncorrected_root_rotation_mm_per_n=cfg["uncorrected_root_rotation_mm_per_n"],
        trials=trials, seed=seed,
        r2_median=axis["r2_q50"], r2_q05=axis["r2_q05"], r2_q95=axis["r2_q95"],
        r2_pass_fraction=axis["r2_pass_fraction"], r2_pass_fraction_se=axis["r2_pass_fraction_se"],
        both_axes_pass_fraction=joint["both_axes_r2_pass_fraction"],
        both_axes_pass_fraction_se=joint["both_axes_pass_fraction_se"],
        relative_U95=axis["relative_U95"], relative_bias=axis["relative_bias"],
        slope_interval_mm_per_n=[axis["interval_2p5_mm_per_n"], axis["interval_97p5_mm_per_n"]],
        passes_r2_gate=axis["passes_r_squared_gate"], passes_u95_gate=axis["passes_relative_u95_gate"],
    )


def build():
    rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    scenarios, results = {}, {}

    # 1. The authoritative missing-input state. Never replaced by an assumed-stiffness scenario.
    nominal = ff.run(trials=200, seed=SEED)
    scenarios["S0_nominal_authoritative"] = dict(
        config=dict(ff.NOMINAL), role="authoritative nominal state",
        note="no fixture exists, so fixture stiffness is UNKNOWN on both axes and the screen refuses")
    results["S0_nominal_authoritative"] = dict(
        verdict=nominal["verdict"], unknown_terms=nominal["unknown_terms"],
        unresolved_gates=nominal.get("unresolved_gates"),
        scope="This is the real state. Every scenario below ADDS an assumed fixture stiffness purely "
              "to make the axes simulable; none of them replaces this result.")

    # 2. The two repeatability cases at boundary resolution.
    for name, rep in (("S1_repeatability_0p5um", 5e-4), ("S2_repeatability_0p3um", 3e-4)):
        cfg = base_cfg(repeatability_mm=rep)
        scenarios[name] = dict(config=cfg, role="reported repeatability case",
                               evidence_state="ASSUMED: no installed-performance record exists")
        results[name] = one(cfg, BOUNDARY_TRIALS) | dict(
            scope="single- and two-axis R^2 rejection risk under assumed terms only")

    # 3. Sensitivity grid. Deliberately assumed alternatives, not register fills.
    for rep in (2e-4, 3e-4, 5e-4):
        for res in (5e-4, 1e-3):
            for spacing in (40.0, 100.0):
                key = f"S3_rep{rep*1e3:g}um_res{res*1e3:g}um_sp{spacing:g}mm"
                cfg = base_cfg(repeatability_mm=rep, indicator_resolution_mm=res,
                               root_station_spacing_mm=spacing)
                scenarios[key] = dict(config=cfg, role="sensitivity grid point",
                                      evidence_state="ASSUMED alternative, not an approved design")
                results[key] = one(cfg, TRIALS) | dict(scope="grid point; refine before deciding")

    # 4. Residual rotation bias varied on its own.
    for name, rot in (("S4_rotation_zero", 0.0), ("S4_rotation_adverse", ADVERSE_ROTATION)):
        cfg = base_cfg(repeatability_mm=3e-4, uncorrected_root_rotation_mm_per_n=rot)
        scenarios[name] = dict(config=cfg, role="rotation-bias case",
                               evidence_state="zero is an explicit IDEAL assumption; the adverse value "
                                              "is explicitly synthetic, not observed")
        results[name] = one(cfg, BOUNDARY_TRIALS) | dict(
            scope="shows that a good R^2 and a small U95 do not imply an accurate compliance estimate")

    # 5. Interventions from one common baseline, reported separately.
    baseline = base_cfg(repeatability_mm=5e-4, indicator_resolution_mm=1e-3, root_station_spacing_mm=40.0)
    interventions = {
        "I0_baseline": {},
        "I1_finer_resolution": dict(indicator_resolution_mm=5e-4),
        "I2_better_repeatability": dict(repeatability_mm=3e-4),
        "I3_wider_station_spacing": dict(root_station_spacing_mm=100.0),
    }
    for key, over in interventions.items():
        cfg = dict(baseline); cfg.update(over)
        scenarios[key] = dict(config=cfg, role="intervention comparison", changed=over or "none")
        results[key] = one(cfg, BOUNDARY_TRIALS) | dict(
            scope="one intervention at a time from a common baseline; effects are reported separately "
                  "and are NOT additive, and no cost or ROI is claimed")

    gates = ff.run(base_cfg(repeatability_mm=3e-4), trials=120, seed=SEED)["gate_status"]
    return dict(
        label=ff.LABEL, schema="decision-screen/1", source_commit=rev, seed=SEED,
        python=platform.python_version(), generated=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        trials_default=TRIALS, trials_boundary=BOUNDARY_TRIALS,
        r2_pass_fraction_screen=ff.R2_PASS_FRACTION_MIN,
        gate_scope={k: v["status"] for k, v in gates.items()},
        gate_scope_note="Gates marked not_evaluated are frozen campaign requirements this screen does "
                        "not simulate. Passing the simulated subset is not passing every campaign gate.",
        scenarios=scenarios), results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(argv)
    meta, results = build()
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / "scenarios.json").write_text(json.dumps(meta, indent=1) + "\n")
    (a.output / "results.json").write_text(json.dumps(
        dict(schema="decision-screen-results/1", source_commit=meta["source_commit"],
             seed=meta["seed"], results=results), indent=1) + "\n")
    print(f"{len(results)} scenarios -> {a.output}")
    for k in ("S1_repeatability_0p5um", "S2_repeatability_0p3um"):
        r = results[k]
        print(f"  {k}: median R2 {r['r2_median']:.6f}  per-axis pass {r['r2_pass_fraction']:.4f}"
              f" +/- {r['r2_pass_fraction_se']:.4f}  both-axes {r['both_axes_pass_fraction']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
