#!/usr/bin/env python3
"""Load-cell force calibration record and analysis (week plan E3). Stdlib only.

    python experiments/load_cell_calibration.py --input RECORD.json --output DIR
    python experiments/load_cell_calibration.py --input RECORD.json --convert 123456

Fits an affine counts-to-force model for ONE cell + mount + channel + ADC configuration and reports
the force uncertainty it supports at the campaign levels. Exits 2 and prints REFUSED when the record
is incomplete or used outside what it establishes.

Three method choices follow literature/04-measurement-uncertainty-and-calibration.md:

  * The fit is errors-in-variables (York 1966; York et al. 2004), not ordinary least squares, because
    the reference force carries mass and g uncertainty while the counts carry noise. OLS would bias
    the slope, and therefore the derived force, low.
  * Fit quality is reported as a lack-of-fit versus pure-error decomposition, not R^2. The correlation
    coefficient is discouraged as a calibration metric (Analytical Methods Committee 1994/2005): a
    value near 1 is compatible with visible curvature.
  * The coverage factor comes from Student's t at the fit's degrees of freedom, not an automatic k=2
    (EA-4/02 M:2022 section 5). k=2 is only reported when the degrees of freedom are large.

This tool calibrates a force channel. It establishes nothing about the mast, the fixture, or any
displacement, and it writes nothing into the campaign evaluator's inputs.
"""
from __future__ import annotations

import argparse, hashlib, json, math, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "load-cell-calibration/1"
CAMPAIGN_FORCES_N = (4.0, 8.0, 12.0, 16.0, 20.0)   # docs/specs/mast-physical-validation/design.md
FULL_SCALE_COUNTS = (1 << 23) - 1                  # NAU7802 24-bit signed
REVIEW_STATES = ("unreviewed", "reviewed", "rejected")

# Two-sided 95 % Student-t by degrees of freedom. Beyond 30, 1.96 is used and reported as k=2-like.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
        10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110,
        18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
        26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def coverage_factor(nu):
    """k for 95 % coverage at nu effective degrees of freedom (EA-4/02 s.5)."""
    if nu is None or nu < 1:
        return None
    return _T95.get(int(nu), 1.960)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- record


def load(path: Path) -> dict:
    rec = json.loads(Path(path).read_text())
    if rec.get("schema") != SCHEMA:
        raise SystemExit(f"REFUSED: schema is {rec.get('schema')!r}, expected {SCHEMA!r}")
    return rec


def applied_force(point: dict, rec: dict) -> float:
    """Tare-subtracted applied force, F = m*g. The tare is what the mount already carries."""
    return point["reference_mass_kg"] * rec["g_m_s2"]


def total_cell_load(point: dict, rec: dict) -> float:
    """Gross load the cell actually sees: applied force plus supported tare. Capacity applies here."""
    return applied_force(point, rec) + rec.get("tare_N", 0.0)


def u_force(point: dict, rec: dict) -> float:
    """Standard uncertainty of the reference force from mass and g."""
    um = point.get("u_reference_mass_kg")
    if um is None:
        return None
    ug = rec.get("u_g_m_s2", 0.0)
    m, g = point["reference_mass_kg"], rec["g_m_s2"]
    return math.sqrt((g * um) ** 2 + (m * ug) ** 2)


# --------------------------------------------------------------------------- fit


def york_fit(x, y, ux, uy, tol=1e-12, max_iter=200):
    """Errors-in-variables straight line y = a + b x (York 1966; York et al. 2004, eqs 1-19).

    x, y are the observations; ux, uy their standard uncertainties. Errors are taken uncorrelated
    per point. Returns slope, intercept, their standard errors and covariance."""
    n = len(x)
    if n < 3:
        raise ValueError("need at least 3 points to fit and leave a residual degree of freedom")
    wx = [1.0 / (s * s) for s in ux]
    wy = [1.0 / (s * s) for s in uy]
    sx, sy = sum(x) / n, sum(y) / n
    sxx = sum((xi - sx) ** 2 for xi in x)
    b = (sum((x[i] - sx) * (y[i] - sy) for i in range(n)) / sxx) if sxx else 0.0  # OLS start
    W = u = None
    for _ in range(max_iter):
        W = [wx[i] * wy[i] / (wx[i] + b * b * wy[i]) for i in range(n)]
        sw = sum(W)
        xb = sum(W[i] * x[i] for i in range(n)) / sw
        yb = sum(W[i] * y[i] for i in range(n)) / sw
        U = [xi - xb for xi in x]
        V = [yi - yb for yi in y]
        beta = [W[i] * (U[i] / wy[i] + b * V[i] / wx[i]) for i in range(n)]
        den = sum(W[i] * beta[i] * U[i] for i in range(n))
        if den == 0:
            break
        b_new = sum(W[i] * beta[i] * V[i] for i in range(n)) / den
        if abs(b_new - b) <= tol * max(1.0, abs(b)):
            b = b_new
            break
        b = b_new
    W = [wx[i] * wy[i] / (wx[i] + b * b * wy[i]) for i in range(n)]
    sw = sum(W)
    xb = sum(W[i] * x[i] for i in range(n)) / sw
    yb = sum(W[i] * y[i] for i in range(n)) / sw
    a = yb - b * xb
    U = [xi - xb for xi in x]
    V = [yi - yb for yi in y]
    beta = [W[i] * (U[i] / wy[i] + b * V[i] / wx[i]) for i in range(n)]
    xadj = [xb + bi for bi in beta]
    xab = sum(W[i] * xadj[i] for i in range(n)) / sw
    u = [xi - xab for xi in xadj]
    suu = sum(W[i] * u[i] ** 2 for i in range(n))
    var_b = 1.0 / suu if suu else float("inf")
    var_a = 1.0 / sw + xab * xab * var_b
    cov_ab = -xab * var_b
    resid = [y[i] - (a + b * x[i]) for i in range(n)]
    return dict(slope_N_per_count=b, intercept_N=a, u_slope=math.sqrt(var_b), u_intercept=math.sqrt(var_a),
                cov_intercept_slope=cov_ab, residuals_N=resid, n=n, dof=n - 2)


def lack_of_fit(levels, resid_by_level):
    """Decompose residual scatter into pure error (within a repeated level) and lack of fit.

    This is the AMC (1994/2005) replacement for quoting R^2: it asks whether the deviation from the
    line is bigger than the repeatability of the measurement itself. Needs replicate points."""
    pure_ss = pure_dof = 0.0
    lof_ss = 0.0
    lof_dof = 0
    for lv in levels:
        rs = resid_by_level[lv]
        if len(rs) >= 2:
            m = statistics.fmean(rs)
            pure_ss += sum((r - m) ** 2 for r in rs)
            pure_dof += len(rs) - 1
            lof_ss += len(rs) * m * m
            lof_dof += 1
        else:
            lof_ss += rs[0] ** 2
            lof_dof += 1
    lof_dof = max(0, lof_dof - 2)
    if pure_dof < 1 or lof_dof < 1:
        return dict(verdict="NOT_EVALUABLE", reason="needs replicates at 3 or more levels", pure_error_sd_N=None,
                    lack_of_fit_F=None, pure_error_dof=pure_dof, lack_of_fit_dof=lof_dof)
    pure_ms, lof_ms = pure_ss / pure_dof, lof_ss / lof_dof
    F = (lof_ms / pure_ms) if pure_ms > 0 else float("inf")
    return dict(verdict=("LACK_OF_FIT_NOT_SIGNIFICANT" if F <= 5.0 else "LACK_OF_FIT_SIGNIFICANT"),
                reason="F = lack-of-fit mean square / pure-error mean square; compared against 5.0 as a "
                       "conservative fixed screen, not a tabulated critical value",
                pure_error_sd_N=math.sqrt(pure_ms), lack_of_fit_F=F,
                pure_error_dof=pure_dof, lack_of_fit_dof=lof_dof)


# --------------------------------------------------------------------------- analysis


def analyse(rec: dict) -> dict:
    pts = rec.get("points") or []
    out = dict(schema=SCHEMA, label=rec.get("label"), cell_id=rec.get("cell_id"),
               config_id=rec.get("config_id"), reviewer_state=rec.get("reviewer_state"),
               source_kind=rec.get("source_kind"), n_points=len(pts))
    blockers = validate(rec)
    out["blockers"] = blockers
    if any(b["fatal"] for b in blockers):
        out["verdict"] = "REFUSED"
        return out

    x = [p["counts_mean"] for p in pts]
    y = [applied_force(p, rec) for p in pts]
    ux = [p["counts_sd"] / math.sqrt(p.get("n", 1)) for p in pts]
    uy = [u_force(p, rec) for p in pts]
    fit = york_fit(x, y, ux, uy)
    out["fit"] = {k: v for k, v in fit.items() if k != "residuals_N"}
    out["fit"]["method"] = "York errors-in-variables (both axes uncertain); NOT ordinary least squares"
    out["residuals_N"] = [round(r, 6) for r in fit["residuals_N"]]

    by_level = {}
    for p, r in zip(pts, fit["residuals_N"]):
        by_level.setdefault(round(p["nominal_mass_kg"], 6), []).append(r)
    out["fit_quality"] = lack_of_fit(sorted(by_level), by_level)
    out["fit_quality"]["note"] = "R^2 is deliberately not reported: discouraged as a calibration metric"

    b, a = fit["slope_N_per_count"], fit["intercept_N"]
    out["hysteresis"] = hysteresis(pts, rec, b, a)
    out["zero_drift"] = zero_drift(rec, b)
    out["repeatability"] = repeatability(pts, rec, b, a)

    lo, hi = min(y), max(y)
    out["calibrated_force_range_N"] = [lo, hi]
    out["calibrated_counts_range"] = [min(x), max(x)]
    nu = fit["dof"]
    k = coverage_factor(nu)
    out["coverage"] = dict(factor_k=k, degrees_of_freedom=nu, basis="Student t, two-sided 95 %",
                           note="k=2 is not assumed; it is used only when dof are large (EA-4/02 s.5)")
    out["force_uncertainty"] = [force_uncertainty(F, fit, out, rec) for F in CAMPAIGN_FORCES_N]

    # Predeclared limits, checked only after the fit because both are expressed in force.
    h_lim = rec.get("hysteresis_limit_percent_fs", 5.0)
    h = out["hysteresis"].get("percent_of_full_scale")
    if h is not None and abs(h) > h_lim:
        blockers.append(_b(f"hysteresis {abs(h):.2f} % of full scale exceeds the declared limit "
                           f"{h_lim} %", fatal=False))
    d_lim = rec.get("zero_drift_limit_N", 0.01 * min(CAMPAIGN_FORCES_N))
    zd = out["zero_drift"].get("force_N")
    if zd is not None and abs(zd) > d_lim:
        blockers.append(_b(f"zero drift {abs(zd):.4f} N exceeds the declared limit {d_lim:.4f} N "
                           f"(minimum dead load output return)", fatal=False))
    out["declared_limits"] = dict(hysteresis_percent_fs=h_lim, zero_drift_N=d_lim,
                                  note="predeclared in the record; defaults are advisory, not a campaign gate")

    unresolved = [t for t in ("mount_record", "date", "operator", "raw_sha256") if not rec.get(t)]
    if rec.get("temperature_C") is None:
        unresolved.append("temperature_C")
    out["unresolved_terms"] = unresolved
    out["verdict"] = ("CALIBRATION_INCOMPLETE" if unresolved or blockers else "CALIBRATION_USABLE")
    out["verdict_note"] = ("A usable verdict describes this force channel only. It is not campaign "
                           "readiness, which needs the full physical-readiness checklist and a reviewer.")
    return out


def hysteresis(pts, rec, b, a):
    """Loading versus unloading difference at matched nominal levels (OIML R 60-1 vocabulary)."""
    up, down = {}, {}
    for p in pts:
        (up if p.get("direction") == "up" else down).setdefault(round(p["nominal_mass_kg"], 6), []).append(
            a + b * p["counts_mean"])
    shared = sorted(set(up) & set(down))
    if not shared:
        return dict(max_abs_N=None, note="no matched ascending and descending points")
    diffs = {lv: statistics.fmean(down[lv]) - statistics.fmean(up[lv]) for lv in shared}
    worst = max(diffs.values(), key=abs)
    fs = max((p["reference_mass_kg"] * rec["g_m_s2"]) for p in pts)
    return dict(max_abs_N=abs(worst), percent_of_full_scale=(100.0 * abs(worst) / fs if fs else None),
                per_level_N={str(k): v for k, v in diffs.items()})


def zero_drift(rec, b):
    z0, z1 = rec.get("zero_start_counts"), rec.get("zero_end_counts")
    if z0 is None or z1 is None:
        return dict(counts=None, force_N=None, note="zero readings missing")
    return dict(counts=z1 - z0, force_N=b * (z1 - z0),
                note="minimum dead load output return; a large value invalidates the session")


def repeatability(pts, rec, b, a):
    by = {}
    for p in pts:
        by.setdefault((round(p["nominal_mass_kg"], 6), p.get("direction")), []).append(a + b * p["counts_mean"])
    sds = [statistics.stdev(v) for v in by.values() if len(v) >= 2]
    return dict(pooled_sd_N=(statistics.fmean(sds) if sds else None), levels_with_repeats=len(sds),
                note="standard deviation of converted force at a repeated level and direction")


def force_uncertainty(F, fit, out, rec):
    """Standard and expanded uncertainty of a force derived from counts at level F."""
    b, a = fit["slope_N_per_count"], fit["intercept_N"]
    if b == 0:
        return dict(force_N=F, u_N=None, U95_N=None, relative_U95_percent=None, in_calibrated_range=False)
    c = (F - a) / b
    var = fit["u_intercept"] ** 2 + (c * fit["u_slope"]) ** 2 + 2 * c * fit["cov_intercept_slope"]
    pe = out["fit_quality"].get("pure_error_sd_N")
    if pe:
        var += pe * pe                       # repeat-to-repeat scatter of a single reading
    u = math.sqrt(max(var, 0.0))
    k = out["coverage"]["factor_k"]
    lo, hi = out["calibrated_force_range_N"]
    return dict(force_N=F, counts=c, u_N=u, U95_N=(k * u if k else None),
                relative_U95_percent=(100.0 * k * u / F if k and F else None),
                in_calibrated_range=(lo <= F <= hi),
                note=None if lo <= F <= hi else "EXTRAPOLATION: outside the calibrated range")


# --------------------------------------------------------------------------- refusals


def _b(msg, fatal=True):
    return dict(blocker=msg, fatal=fatal)


def validate(rec: dict) -> list:
    """Fail-closed checks. Fatal blockers stop the fit; non-fatal ones make the record incomplete."""
    out = []
    pts = rec.get("points") or []
    if len(pts) < 3:
        out.append(_b(f"only {len(pts)} calibration points; need at least 3"))
    if rec.get("reviewer_state") not in REVIEW_STATES:
        out.append(_b(f"reviewer_state {rec.get('reviewer_state')!r} not one of {REVIEW_STATES}"))
    if rec.get("promoted_to_campaign_ready") and rec.get("reviewer_state") != "reviewed":
        out.append(_b("record promoted to campaign-ready while unreviewed"))
    if rec.get("mount_changed_since_calibration"):
        out.append(_b("mounting changed since calibration; a documented recheck is required"))

    cap = rec.get("cell_capacity_N")
    # Per-point faults are aggregated: one blocker naming the count and the worst level, not one per row.
    def _levels(test):
        return [p.get("nominal_mass_kg") for p in pts if test(p)]

    for names, fatal, test in (
        ("no reference-mass uncertainty", True, lambda p: p.get("u_reference_mass_kg") is None),
        ("no positive counts_sd", True, lambda p: not p.get("counts_sd") or p["counts_sd"] <= 0),
        ("saturated counts", True, lambda p: abs(p.get("counts_mean", 0)) >= FULL_SCALE_COUNTS),
        ("total cell load over capacity (tare included)", True,
         lambda p: bool(cap) and total_cell_load(p, rec) > cap),
        ("reference-mass uncertainty coarser than 1 %", False,
         lambda p: p.get("u_reference_mass_kg") is not None and p.get("reference_mass_kg")
         and p["u_reference_mass_kg"] / p["reference_mass_kg"] > 0.01),
    ):
        bad = _levels(test)
        if bad:
            out.append(_b(f"{len(bad)} of {len(pts)} points have {names}; nominal levels "
                          f"{sorted(set(bad))} kg", fatal=fatal))

    if pts and cap:
        forces = [applied_force(p, rec) for p in pts]
        need_lo, need_hi = min(CAMPAIGN_FORCES_N), max(CAMPAIGN_FORCES_N)
        if cap < need_hi:
            out.append(_b(f"cell capacity {cap} N cannot reach the {need_hi} N campaign level; "
                          f"do not substitute this cell into the full profile"))
        if min(forces) > need_lo:
            out.append(_b(f"lowest calibration force {min(forces):.2f} N is above the {need_lo} N campaign "
                          f"level; that level would be extrapolated", fatal=False))
        if max(forces) < need_hi:
            out.append(_b(f"highest calibration force {max(forces):.2f} N is below the {need_hi} N campaign "
                          f"level; that level would be extrapolated", fatal=False))
    return out


def convert(rec: dict, result: dict, counts: float) -> dict:
    """Counts to force, refusing outside what the calibration established."""
    if result["verdict"] == "REFUSED":
        raise SystemExit("REFUSED: the calibration record itself is refused; no conversion is possible")
    lo, hi = result["calibrated_counts_range"]
    if not lo <= counts <= hi:
        raise SystemExit(f"REFUSED: {counts} counts is outside the calibrated range [{lo}, {hi}]")
    fit = result["fit"]
    return dict(counts=counts, force_N=fit["intercept_N"] + fit["slope_N_per_count"] * counts,
                cell_id=rec.get("cell_id"), config_id=rec.get("config_id"),
                verdict=result["verdict"], source_kind=rec.get("source_kind"))


# --------------------------------------------------------------------------- cli


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, required=True, help="calibration record JSON")
    ap.add_argument("--output", type=Path, help="directory for analysis.json")
    ap.add_argument("--convert", type=float, help="convert this count value to force and exit")
    ap.add_argument("--expect-config", help="refuse if the record's config_id differs")
    a = ap.parse_args(argv)

    rec = load(a.input)
    if a.expect_config and rec.get("config_id") != a.expect_config:
        print(f"REFUSED: record config {rec.get('config_id')!r} != expected {a.expect_config!r}", file=sys.stderr)
        return 2
    result = analyse(rec)
    if a.convert is not None:
        print(json.dumps(convert(rec, result, a.convert), indent=1))
        return 0
    if a.output:
        a.output.mkdir(parents=True, exist_ok=True)
        (a.output / "analysis.json").write_text(json.dumps(result, indent=1) + "\n")
    else:
        print(json.dumps(result, indent=1))

    fatal = [b for b in result["blockers"] if b["fatal"]]
    print(f"{result['verdict']}: {result['n_points']} points, {len(fatal)} fatal blockers, "
          f"{len(result['blockers']) - len(fatal)} advisory, "
          f"{len(result.get('unresolved_terms', []))} unresolved terms", file=sys.stderr)
    for b in result["blockers"]:
        print(("  FATAL " if b["fatal"] else "  note  ") + b["blocker"], file=sys.stderr)
    return 0 if result["verdict"] == "CALIBRATION_USABLE" else 2


if __name__ == "__main__":
    sys.exit(main())
