#!/usr/bin/env python3
"""Nominal fixture feasibility screen for the mast compliance campaign (week plan W3.1).

    python cad/fixture_feasibility.py                      # screen the nominal case
    python cad/fixture_feasibility.py --output runs/mast_fixture_feasibility

NOMINAL FEASIBILITY SCREEN ONLY. It asks one question: could the proposed fixture and instruments
resolve the specimen's compliance to the frozen relative U95 <= 10 % gate on both axes? It measures
nothing, and a pass here is not permission to load anything.

Two design rules this obeys:

  * The fitted-slope uncertainty is obtained by propagating the declared error terms through the
    *actual* campaign estimator, `experiments/mast_physical_validation.py::_linear_fit`, by Monte
    Carlo (JCGM 101). A second estimator would be a second source of truth.
  * A missing physical term is UNKNOWN, never zero. Any UNKNOWN makes the whole screen UNKNOWN; the
    screen cannot conclude "feasible" by leaving a term out.

The observable the estimator fits is (tip reading - fixture reading) against measured force, so root
quantization enters the budget twice and residual root rotation enters once through the load height.
"""
from __future__ import annotations

import argparse, json, math, random, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.mast_physical_validation import (  # noqa: E402  the one estimator, imported not copied
    _linear_fit, LOAD_LEVELS_N, MAX_RELATIVE_U95, MIN_R_SQUARED, MAX_HYSTERESIS_FRACTION,
    MAX_FEA_RELATIVE_ERROR, REQUIRED_INDICATOR_COUNTS, FEA_COMPLIANCE_MM_PER_N,
)

LABEL = "NOMINAL FEASIBILITY SCREEN ONLY: no measurement, no calibration, no campaign authorisation."
CYCLES = 3
DIRECTIONS = ("load", "unload")
AXES = ("x", "y")
DEFAULT_TRIALS = 400
FIXTURE_STIFFNESS_RATIO_MIN = 10.0


# --------------------------------------------------------------------------- specimen


def second_moment_mm4(od_mm: float, wall_mm: float) -> float:
    return math.pi / 64.0 * (od_mm ** 4 - (od_mm - 2.0 * wall_mm) ** 4)


def specimen_stiffness_n_per_mm(e_n_per_mm2=68900.0, length_mm=100.0, od_mm=20.0, wall_mm=1.5) -> float:
    """k = 3EI/L^3 for the accepted nominal tube. Hand model, not FEA, not measured."""
    return 3.0 * e_n_per_mm2 * second_moment_mm4(od_mm, wall_mm) / length_mm ** 3


def required_fixture_stiffness(k_specimen: float) -> float:
    return FIXTURE_STIFFNESS_RATIO_MIN * k_specimen


# --------------------------------------------------------------------------- error terms


def quantization_sd(resolution_mm):
    """Uniform quantization standard uncertainty for a given indicator step."""
    return None if resolution_mm is None else resolution_mm / math.sqrt(12.0)


def rotation_sd_rad(resolution_mm, station_spacing_mm):
    """Root rotation uncertainty from two independent root stations a known distance apart.

    This is the term the station spacing actually buys: a wider baseline observes rotation better."""
    if resolution_mm is None or not station_spacing_mm:
        return None
    return math.sqrt(2.0) * quantization_sd(resolution_mm) / station_spacing_mm


def terms(cfg: dict) -> dict:
    """Assemble every declared term. A term that cannot be derived stays None (UNKNOWN)."""
    res = cfg.get("indicator_resolution_mm")
    q = quantization_sd(res)
    theta = rotation_sd_rad(res, cfg.get("root_station_spacing_mm"))
    lh = cfg.get("load_height_mm")
    return {
        "tip_quantization_mm": q,
        "root_quantization_mm": q,
        "repeatability_mm": cfg.get("repeatability_mm"),
        "residual_root_rotation_mm": (None if theta is None or lh is None else theta * lh),
        "force_relative": cfg.get("force_relative_standard_uncertainty"),
        "root_rotation_sd_rad": theta,
    }


def unknown_terms(t: dict, cfg: dict) -> list:
    out = [k for k, v in t.items() if v is None]
    for k in ("indicator_resolution_mm", "root_station_spacing_mm", "load_height_mm",
              "fixture_stiffness_n_per_mm_x", "fixture_stiffness_n_per_mm_y"):
        if cfg.get(k) is None:
            out.append(k)
    return sorted(set(out))


# --------------------------------------------------------------------------- monte carlo


def _trial_slope(rng, compliance_true, t, cfg):
    """One synthetic campaign on one axis, fitted with the real campaign estimator."""
    pts = []
    for _ in range(CYCLES):
        for _d in DIRECTIONS:
            for level in LOAD_LEVELS_N:
                u_f = t["force_relative"] * level
                f_true = level + rng.gauss(0.0, u_f)
                f_measured = level + rng.gauss(0.0, u_f)   # the recorded force, independently in error
                d_true = compliance_true * f_true
                tip = (d_true
                       + rng.gauss(0.0, t["tip_quantization_mm"])
                       + rng.gauss(0.0, t["repeatability_mm"])
                       + rng.gauss(0.0, t["residual_root_rotation_mm"]))
                fixture = (rng.gauss(0.0, t["root_quantization_mm"])
                           + rng.gauss(0.0, t["repeatability_mm"]))
                pts.append((f_measured, tip - fixture))
    slope, _intercept, r2 = _linear_fit(pts)
    return slope, r2


def screen_axis(compliance_true, t, cfg, trials, seed):
    rng = random.Random(seed)
    slopes, r2s = [], []
    for _ in range(trials):
        s, r2 = _trial_slope(rng, compliance_true, t, cfg)
        slopes.append(s)
        if r2 is not None:
            r2s.append(r2)
    u = statistics.stdev(slopes)
    u95 = 1.96 * u                      # coverage over the Monte Carlo distribution of the estimator
    return dict(mean_fitted_compliance_mm_per_n=statistics.fmean(slopes),
                u_fitted_compliance_mm_per_n=u, U95_mm_per_n=u95,
                relative_U95=u95 / compliance_true,
                passes_relative_u95_gate=bool(u95 / compliance_true <= MAX_RELATIVE_U95),
                median_r_squared=(statistics.median(r2s) if r2s else None),
                passes_r_squared_gate=bool(r2s and statistics.median(r2s) >= MIN_R_SQUARED),
                trials=trials)


def rank_terms(compliance_true, t, cfg, trials, seed):
    """Which single term dominates the fitted-slope uncertainty. One term live at a time.

    This is the point of the screen: it says what to go and measure next, instead of assuming that
    more ADC bits fix the largest error."""
    ranking = []
    for name in ("tip_quantization_mm", "root_quantization_mm", "repeatability_mm",
                 "residual_root_rotation_mm", "force_relative"):
        only = {k: (0.0 if k != name else v) for k, v in t.items() if k != "root_rotation_sd_rad"}
        only["root_rotation_sd_rad"] = t["root_rotation_sd_rad"]
        r = screen_axis(compliance_true, only, cfg, max(120, trials // 3), seed + 17)
        ranking.append(dict(term=name, relative_U95_alone=r["relative_U95"],
                            U95_mm_per_n_alone=r["U95_mm_per_n"]))
    ranking.sort(key=lambda d: d["relative_U95_alone"], reverse=True)
    for i, d in enumerate(ranking, 1):
        d["rank"] = i
    return ranking


# --------------------------------------------------------------------------- force chain


def force_chain_cases(cfg: dict) -> list:
    """Candidate force channels. No real calibration exists, so every sensitivity is ASSUMED."""
    out = []
    for case in cfg.get("force_chain_cases", []):
        cap = case.get("capacity_N")
        worst = max(LOAD_LEVELS_N)
        out.append(dict(
            case | dict(
                covers_campaign_range=bool(cap is not None and cap >= worst),
                refusal=(None if cap is None or cap >= worst else
                         f"capacity {cap} N cannot reach the {worst} N campaign level"),
                evidence="ASSUMED sensitivity; no calibration record exists. Replace with an E3 "
                         "CALIBRATION_USABLE result before any physical decision.")))
    return out


# --------------------------------------------------------------------------- screen


NOMINAL = dict(
    label=LABEL,
    specimen=dict(e_n_per_mm2=68900.0, length_mm=100.0, od_mm=20.0, wall_mm=1.5,
                  evidence_state="design_choice / model_assumption per cad/roboracer/parameters.csv"),
    indicator_resolution_mm=0.001,          # protocol floor; a real indicator needs a calibration record
    root_station_spacing_mm=100.0,          # proposed; register row is pending
    load_height_mm=100.0,                   # equals mast length by design choice
    repeatability_mm=0.0005,                # ASSUMED reading repeatability, no record
    force_relative_standard_uncertainty=0.005,   # ASSUMED 0.5 % of reading, no calibration
    fixture_stiffness_n_per_mm_x=None,      # UNKNOWN: no fixture design exists
    fixture_stiffness_n_per_mm_y=None,
    force_chain_cases=[
        dict(cell_id="LC-5KG-01", capacity_N=49.05, role="primary candidate"),
        dict(cell_id="LC-1KG-01", capacity_N=9.81, role="negative control at 20 N"),
    ],
)


def run(cfg: dict = None, trials: int = DEFAULT_TRIALS, seed: int = 20260923) -> dict:
    cfg = dict(NOMINAL if cfg is None else cfg)
    sp = cfg["specimen"]
    k = specimen_stiffness_n_per_mm(sp["e_n_per_mm2"], sp["length_mm"], sp["od_mm"], sp["wall_mm"])
    compliance_hand = 1.0 / k
    t = terms(cfg)
    unknown = unknown_terms(t, cfg)

    out = dict(label=LABEL, schema="fixture-feasibility/1",
               specimen=sp | dict(second_moment_mm4=second_moment_mm4(sp["od_mm"], sp["wall_mm"]),
                                  stiffness_n_per_mm=k, compliance_mm_per_n=compliance_hand),
               stiffness_screen=dict(
                   required_per_axis_n_per_mm=required_fixture_stiffness(k),
                   ratio_minimum=FIXTURE_STIFFNESS_RATIO_MIN,
                   declared_x=cfg.get("fixture_stiffness_n_per_mm_x"),
                   declared_y=cfg.get("fixture_stiffness_n_per_mm_y"),
                   verdict="UNKNOWN" if cfg.get("fixture_stiffness_n_per_mm_x") is None
                           or cfg.get("fixture_stiffness_n_per_mm_y") is None else "EVALUATED",
                   note="a rigid-looking CAD model is not stiffness evidence; this ratio does not "
                        "constrain root rotation, which is budgeted separately"),
               ideal_signal=dict(
                   deflection_at_4N_mm=4.0 * compliance_hand,
                   deflection_at_20N_mm=20.0 * compliance_hand,
                   fea_compliance_mm_per_n=FEA_COMPLIANCE_MM_PER_N,
                   fea_deflection_at_20N_mm=20.0 * FEA_COMPLIANCE_MM_PER_N,
                   note="hand-model and FEA compliances are different quantities and are kept apart"),
               terms=t, unknown_terms=unknown,
               matrix=dict(load_levels_n=list(LOAD_LEVELS_N), cycles=CYCLES,
                           directions=list(DIRECTIONS), axes=list(AXES),
                           points_per_axis=CYCLES * len(DIRECTIONS) * len(LOAD_LEVELS_N)),
               gates=dict(relative_U95_max=MAX_RELATIVE_U95, r_squared_min=MIN_R_SQUARED,
                          hysteresis_fraction_max=MAX_HYSTERESIS_FRACTION,
                          fea_relative_error_max=MAX_FEA_RELATIVE_ERROR,
                          indicator_counts_min=REQUIRED_INDICATOR_COUNTS,
                          note="frozen campaign gates, imported not restated; this screen does not "
                               "relax or reinterpret any of them"),
               force_chain=force_chain_cases(cfg))

    counts_at_20N = 20.0 * FEA_COMPLIANCE_MM_PER_N / cfg["indicator_resolution_mm"] \
        if cfg.get("indicator_resolution_mm") else None
    out["indicator_screen"] = dict(
        resolution_mm=cfg.get("indicator_resolution_mm"),
        counts_at_full_scale=counts_at_20N,
        passes=bool(counts_at_20N is not None and counts_at_20N >= REQUIRED_INDICATOR_COUNTS
                    and cfg["indicator_resolution_mm"] <= 0.001),
        note="full-scale screen only; it does not mean the 4 N point has 20 counts")

    if unknown:
        out["axes"] = {a: dict(verdict="UNKNOWN", reason="one or more terms are UNKNOWN") for a in AXES}
        out["dominant_terms"] = None
        out["verdict"] = "UNKNOWN"
        out["verdict_note"] = ("Terms are missing, so no feasibility number is claimed. A missing term "
                              "is never treated as zero.")
        return out

    out["axes"] = {a: screen_axis(compliance_hand, t, cfg, trials, seed + i)
                   for i, a in enumerate(AXES)}
    out["dominant_terms"] = rank_terms(compliance_hand, t, cfg, trials, seed)
    both = all(out["axes"][a]["passes_relative_u95_gate"] for a in AXES)
    out["verdict"] = "PLAUSIBLE_PENDING_PHYSICAL_INPUTS" if both else "NOT_PLAUSIBLE_AS_CONFIGURED"
    out["verdict_note"] = ("Plausible means the declared, largely ASSUMED terms would satisfy the "
                           "frozen gate. It is not a measurement, not a fixture design, and not "
                           "campaign readiness.")
    out["next_measurement"] = (out["dominant_terms"][0]["term"] if out["dominant_terms"] else None)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, help="directory for nominal_screen.json")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--assume-fixture-stiffness", type=float,
                    help="declare both axes at this N/mm to exercise the screen (clearly ASSUMED)")
    a = ap.parse_args(argv)

    cfg = dict(NOMINAL)
    if a.assume_fixture_stiffness is not None:
        cfg["fixture_stiffness_n_per_mm_x"] = a.assume_fixture_stiffness
        cfg["fixture_stiffness_n_per_mm_y"] = a.assume_fixture_stiffness
    result = run(cfg, trials=a.trials)
    if a.output:
        a.output.mkdir(parents=True, exist_ok=True)
        (a.output / "nominal_screen.json").write_text(json.dumps(result, indent=1) + "\n")
    else:
        print(json.dumps(result, indent=1))
    print(f"{result['verdict']}: k={result['specimen']['stiffness_n_per_mm']:.3f} N/mm, "
          f"fixture target {result['stiffness_screen']['required_per_axis_n_per_mm']:.2f} N/mm/axis, "
          f"{len(result['unknown_terms'])} UNKNOWN terms", file=sys.stderr)
    for u in result["unknown_terms"]:
        print(f"  UNKNOWN {u}", file=sys.stderr)
    return 0 if result["verdict"].startswith("PLAUSIBLE") else 2


if __name__ == "__main__":
    sys.exit(main())
