#!/usr/bin/env python
"""Draw the simulator and ROS-capture report figures from committed run outputs.

The experiment scripts call the draw_* functions after they write their run
files, so a full rerun and this redraw use the same plotting code. Run this file
alone to redraw figures without a simulation, fit or bag:

    PYTHONPATH=gym MPLBACKEND=Agg python experiments/report_figures.py
    PYTHONPATH=gym MPLBACKEND=Agg python experiments/report_figures.py --only ekf

Nothing here writes to runs/ or evidence/*/metrics; only PNG files change.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd

import figure_style as fs
from figure_style import COLORS as C

plt = fs.plt
REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS = REPO_ROOT / "runs"
FIGURES = REPO_ROOT / "reports" / "figures"
ITEM11 = REPO_ROOT / "evidence" / "item11"


def module_constant(path: Path, name: str):
    """Read a literal module constant without importing the module (and its Gym import)."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(f"{name} not found in {path}")


def metric_map(path: Path) -> dict[str, float]:
    frame = pd.read_csv(path)
    return {str(row.metric): float(row.value) for row in frame.itertuples(index=False)}


SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def sci(value: float) -> str:
    """One significant figure in a × 10ⁿ form, e.g. 9 × 10⁻¹⁰."""
    mantissa, exponent = f"{value:.0e}".split("e")
    return f"{mantissa} × 10{str(int(exponent)).translate(SUPERSCRIPT)}"


def zero_line(ax) -> None:
    ax.axhline(0.0, color=C["neutral"], linewidth=0.6, zorder=1)


def ms_ticks(ax, values_s) -> None:
    """Log timestep axis labelled in milliseconds at the tested values."""
    ax.set_xscale("log")
    ax.set_xticks(values_s, [f"{v * 1000:g}" for v in values_s])
    ax.minorticks_off()


# --- RK4 timestep convergence -------------------------------------------------

def draw_integrator_convergence(run_dir: Path = RUNS / "integrator_convergence", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    results = pd.read_csv(run_dir / "convergence_results.csv").sort_values("dt_s")
    source = REPO_ROOT / "experiments" / "integrator_convergence.py"
    rms_tol = module_constant(source, "RMS_REFINEMENT_TOL_M")
    max_tol = module_constant(source, "MAX_REFINEMENT_TOL_M")
    return [convergence_position_error(results, figure_dir / "integrator_convergence_position_error.png", rms_tol, max_tol),
            convergence_metrics(results, figure_dir / "integrator_convergence_metrics.png")]


def _collided(results: pd.DataFrame) -> pd.Series:
    return results["collision"].astype(bool) | ~results["completed_lap"].astype(bool)


def convergence_position_error(results: pd.DataFrame, path: Path, rms_tol: float, max_tol: float) -> Path:
    ref_dt = float(results["dt_s"].min())
    failed = _collided(results)
    fig, axes = fs.subplots(1, 2, height_in=3.1, sharey=True)
    color = C["rk4"]
    panels = [
        ("A", "vs_ref_progress_m", "position_error", "Error against the {ref} ms run"),
        ("B", "vs_next_finer_dt_progress_m", "position_change", "Change against the next finer timestep"),
    ]
    for ax, (letter, suffix, stem, panel_title) in zip(axes, panels):
        rms_col, max_col = f"rms_{stem}_{suffix}", f"max_{stem}_{suffix}"
        data = results[(results["dt_s"] > ref_dt) & results[rms_col].notna()]
        ok, bad = data[~_collided(data)], data[_collided(data)]
        ax.plot(ok["dt_s"], ok[rms_col], "-o", color=color, markersize=4)
        ax.plot(ok["dt_s"], ok[max_col], "--s", color=color, markersize=4, alpha=0.6)
        ax.plot(bad["dt_s"], bad[rms_col], "x", color=C["alarm"], markersize=7, mew=1.6)
        ax.plot(bad["dt_s"], bad[max_col], "x", color=C["alarm"], markersize=7, mew=1.6)
        if letter == "A":
            first = ok.iloc[0]
            ax.annotate("RMS", (first["dt_s"], first[rms_col]), xytext=(0, 7), textcoords="offset points",
                        ha="left", va="bottom", fontsize=fs.SMALL, color=color)
            ax.annotate("Maximum", (first["dt_s"], first[max_col]), xytext=(0, 7), textcoords="offset points",
                        ha="left", va="bottom", fontsize=fs.SMALL, color=color)
            worst = bad.iloc[0] if not bad.empty else None
            if worst is not None:
                ax.annotate("Collided", (worst["dt_s"], worst[max_col]), xytext=(0, 7), textcoords="offset points",
                            ha="center", va="bottom", fontsize=fs.SMALL, color=C["alarm"])
        ms_ticks(ax, results["dt_s"].tolist())
        ax.set_yscale("log")
        ax.set_xlabel("RK4 timestep [ms]")
        fs.panel_letter(ax, letter)
        ax.set_title(panel_title.format(ref=f"{ref_dt * 1000:g}"))
    for tol, label, va in [(rms_tol, f"RMS tolerance {rms_tol:g} m", "top"), (max_tol, f"Maximum tolerance {max_tol:g} m", "bottom")]:
        axes[1].axhline(tol, color=C["neutral"], linewidth=0.8, linestyle=":")
        axes[1].annotate(label, (1.0, tol), xycoords=("axes fraction", "data"), xytext=(-2, -2 if va == "top" else 2),
                         textcoords="offset points", ha="right", va=va, fontsize=fs.SMALL, color=C["neutral"])
    axes[0].set_ylabel("Position difference [m]")
    for ax in axes:
        ax.margins(x=0.08, y=0.12)
    change = results.dropna(subset=["rms_position_change_vs_next_finer_dt_progress_m"])
    passing = change[(~_collided(change)) & (change["rms_position_change_vs_next_finer_dt_progress_m"] < rms_tol)
                     & (change["max_position_change_vs_next_finer_dt_progress_m"] < max_tol)]["dt_s"]
    largest = float(passing.max())
    assert set(passing) == set(change[change["dt_s"] <= largest]["dt_s"]), "tolerance pass set is not contiguous"
    fs.title(fig, f"{fs.SIMULATOR}, RK4, pure pursuit",
             f"Position error shrinks with the timestep; both refinement tolerances hold from {largest * 1000:g} ms down")
    crashed = results[failed]
    note = f"n = {len(results)} timesteps, one closed-loop lap each; differences are taken at matched progress."
    if not crashed.empty:
        row = crashed.iloc[0]
        note += f"\n× The {row['dt_s'] * 1000:g} ms run collided at {row['final_time_s']:.2f} s, so its values cover a partial lap."
    fs.footnote(fig, note)
    return fs.save(fig, path)[0]


def convergence_metrics(results: pd.DataFrame, path: Path) -> Path:
    failed = _collided(results)
    ok, bad = results[~failed], results[failed]
    fig, axes = fs.subplots(1, 3, height_in=2.9, sharex=True)
    specs = [("A", "final_progress_m", "Final progress along path [m]", "Progress when the run stopped"),
             ("B", "rms_cte_m", "RMS cross-track error [m]", "Tracking error"),
             ("C", "max_abs_cte_m", "Maximum |cross-track error| [m]", "Worst tracking error")]
    for ax, (letter, column, ylabel, panel_title) in zip(axes, specs):
        ax.plot(ok["dt_s"], ok[column], "-o", color=C["rk4"], markersize=4, label="Completed lap")
        ax.plot(bad["dt_s"], bad[column], "x", color=C["alarm"], markersize=7, mew=1.6, label="Collided (partial lap)")
        ms_ticks(ax, results["dt_s"].tolist())
        ax.set_ylabel(ylabel)
        ax.set_title(panel_title)
        fs.panel_letter(ax, letter)
        ax.margins(x=0.08, y=0.15)
    axes[1].set_xlabel("RK4 timestep [ms]")
    axes[0].legend(loc="center right")
    finished = ok["dt_s"]
    takeaway = f"Every timestep from {finished.max() * 1000:g} ms down completes the lap"
    if not bad.empty:
        row = bad.iloc[0]
        takeaway += f"; {row['dt_s'] * 1000:g} ms collides at {row['final_time_s']:.2f} s"
    fs.title(fig, f"{fs.SIMULATOR}, RK4, pure pursuit", takeaway)
    fs.footnote(fig, f"n = {len(results)} timesteps, one closed-loop lap each. Collided runs are not peers of completed laps: "
                     "their errors cover a partial lap.")
    return fs.save(fig, path)[0]


# --- Known-parameter dynamic replay ------------------------------------------

def draw_dynamic_replay(run_dir: Path = RUNS / "dynamic_model_replay", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    trace = pd.read_csv(run_dir / "replay_trace.csv")
    metrics = metric_map(run_dir / "metrics.csv")
    return [dynamic_replay_yaw_rate(trace, metrics, figure_dir / "dynamic_replay_yaw_rate_overlay.png"),
            dynamic_replay_state_errors(trace, metrics, figure_dir / "dynamic_replay_state_errors.png")]


def dynamic_replay_yaw_rate(trace: pd.DataFrame, metrics: dict[str, float], path: Path) -> Path:
    fig, (ax, ax_steer) = fs.subplots(2, 1, height_in=4.4, sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    t = trace["time_s"]
    ax.plot(t, trace["kinematic_yaw_rate_radps"], color=C["kinematic"], linewidth=0.6, alpha=0.8, label="Kinematic yaw law", zorder=2)
    ax.plot(t, trace["gym_yaw_rate_radps"], color=C["reference"], linewidth=2.4, alpha=0.45, label="Gym (reference)", zorder=3)
    ax.plot(t, trace["dynamic_yaw_rate_radps"], color=C["dynamic"], linewidth=0.9, label="Dynamic replay", zorder=4)
    ax.set_ylabel("Yaw rate [rad/s]")
    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index(n) for n in ("Gym (reference)", "Dynamic replay", "Kinematic yaw law")]
    ax.legend([handles[i] for i in order], [labels[i] for i in order], loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=3, borderaxespad=0.2)
    fs.panel_letter(ax, "A")
    ax_steer.plot(t, trace["gym_steer_rad"], color=C["reference"], linewidth=1.0)
    ax_steer.set_ylabel("Achieved\nsteering [rad]")
    ax_steer.set_xlabel("Time [s]")
    fs.panel_letter(ax_steer, "B")
    for axis in (ax, ax_steer):
        axis.axvline(2.0, color=C["neutral"], linestyle=":", linewidth=0.8)
        zero_line(axis)
    ax.annotate("t = 2.0 s", (2.0, 1.0), xycoords=("data", "axes fraction"), xytext=(3, -3),
                textcoords="offset points", ha="left", va="top", fontsize=fs.SMALL, color=C["neutral"])
    fs.title(fig, f"{fs.SIMULATOR}, known parameters",
             f"Dynamic replay follows Gym yaw rate (RMSE {metrics['dynamic_yaw_rate_rmse_radps']:.3f} rad/s); "
             f"the kinematic yaw law does not ({metrics['kinematic_yaw_rate_rmse_radps']:.2f} rad/s)")
    fs.footnote(fig, f"First-lap RK4 telemetry, n = {int(metrics['num_samples']):,} samples over {metrics['duration_s']:.1f} s. "
                     "Both models replay the same inputs.")
    return fs.save(fig, path)[0]


def _state_error_rows(fig_axes, trace, rows, color):
    for ax, (letter, column, label) in zip(fig_axes, rows):
        ax.plot(trace["time_s"], trace[column], color=color, linewidth=1.0)
        zero_line(ax)
        ax.set_ylabel(label)
        fs.panel_letter(ax, letter)
        ax.margins(y=0.12)
    fig_axes[-1].set_xlabel("Time [s]")
    fig_axes[0].figure.align_ylabels(fig_axes)


def dynamic_replay_state_errors(trace: pd.DataFrame, metrics: dict[str, float], path: Path) -> Path:
    fig, axes = fs.subplots(4, 1, height_in=5.4, sharex=True)
    _state_error_rows(axes, trace, [
        ("A", "error_position_m", "Position\nerror [m]"),
        ("B", "error_yaw_rad", "Yaw\nerror [rad]"),
        ("C", "error_yaw_rate_radps", "Yaw-rate\nerror [rad/s]"),
        ("D", "error_speed_mps", "Speed\nerror [m/s]"),
    ], C["dynamic"])
    fs.title(fig, f"{fs.SIMULATOR}, known parameters",
             f"Dynamic replay stays within {metrics['max_position_error_m']:.2f} m of the Gym trajectory over {metrics['duration_s']:.1f} s")
    fs.footnote(fig, f"Error = dynamic replay minus Gym state; n = {int(metrics['num_samples']):,} RK4 samples. "
                     f"RMSE: position {metrics['rmse_position_m']:.3f} m, yaw rate {metrics['rmse_yaw_rate_radps']:.3f} rad/s.")
    return fs.save(fig, path)[0]


# --- Kinematic replay ----------------------------------------------------------

def draw_kinematic_replay(run_dir: Path = RUNS / "model_vs_gym_comparison", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    trace = pd.read_csv(run_dir / "replay_trace.csv")
    metrics = metric_map(run_dir / "metrics.csv")
    return [kinematic_trajectory(trace, metrics, figure_dir / "model_vs_gym_trajectory_error.png"),
            kinematic_state_errors(trace, metrics, figure_dir / "model_vs_gym_state_errors.png")]


def kinematic_trajectory(trace: pd.DataFrame, metrics: dict[str, float], path: Path) -> Path:
    fig, ax = fs.subplots(height_in=5.0, width_in=6.0)
    ax.plot(trace["gym_x_m"], trace["gym_y_m"], color=C["reference"], linewidth=1.6, label="Gym RK4 (reference)")
    ax.plot(trace["model_x_m"], trace["model_y_m"], color=C["kinematic"], linewidth=1.3, linestyle="--", label="Kinematic replay")
    ax.plot(trace["gym_x_m"].iloc[0], trace["gym_y_m"].iloc[0], "o", markerfacecolor="none", markeredgecolor=C["neutral"],
            markersize=11, markeredgewidth=1.2, label="Start", zorder=4)
    ax.plot(trace["gym_x_m"].iloc[-1], trace["gym_y_m"].iloc[-1], "s", color=C["reference"], markersize=6, label="Gym end")
    ax.plot(trace["model_x_m"].iloc[-1], trace["model_y_m"].iloc[-1], "X", color=C["kinematic"], markersize=7, label="Replay end")
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.05)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.legend(loc="best")
    fs.title(fig, f"{fs.SIMULATOR}, first lap",
             f"Kinematic replay leaves the Gym path: {metrics['final_position_error_m']:.1f} m apart after "
             f"{metrics['duration_replayed_s']:.1f} s (maximum {metrics['max_position_error_m']:.1f} m)")
    fs.footnote(fig, f"Same inputs replayed through a kinematic bicycle model; n = {int(metrics['num_samples']):,} samples at "
                     f"{metrics['dt_mean_s'] * 1000:g} ms.")
    return fs.save(fig, path)[0]


def kinematic_state_errors(trace: pd.DataFrame, metrics: dict[str, float], path: Path) -> Path:
    fig, axes = fs.subplots(3, 1, height_in=4.6, sharex=True)
    _state_error_rows(axes, trace, [
        ("A", "error_position_m", "Position\nerror [m]"),
        ("B", "error_yaw_rad", "Wrapped yaw\nerror [rad]"),
        ("C", "error_speed_mps", "Speed\nerror [m/s]"),
    ], C["kinematic"])
    speed_max = float(trace["error_speed_mps"].abs().max())
    fs.title(fig, f"{fs.SIMULATOR}, first lap",
             f"Kinematic replay position error reaches {metrics['max_position_error_m']:.1f} m "
             f"while speed error stays below {np.ceil(speed_max * 100) / 100:.2f} m/s")
    fs.footnote(fig, f"Error = kinematic replay minus Gym state; n = {int(metrics['num_samples']):,} samples. "
                     "Yaw error is wrapped to ±π rad.")
    return fs.save(fig, path)[0]


# --- Steering excitation -------------------------------------------------------

def draw_sysid_excitation(run_dir: Path = RUNS / "sysid_steering_excitation", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    telemetry = pd.read_csv(run_dir / "telemetry.csv")
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    quality = metric_map(run_dir / "quality_metrics.csv")
    return [sysid_steering_input(telemetry, metadata, quality, figure_dir / "sysid_steering_input.png"),
            sysid_yaw_response(telemetry, metadata, quality, figure_dir / "sysid_yaw_response.png"),
            sysid_speed_hold(telemetry, metadata, quality, figure_dir / "sysid_speed_hold.png")]


def _chirp_label(metadata: dict) -> str:
    profile = metadata["selected_profile"]
    return (f"{metadata['frequency_start_hz']:g}–{metadata['frequency_end_hz']:g} Hz chirp, "
            f"{profile['amplitude_rad']:g} rad, {profile['duration_s']:g} s at {metadata['target_speed_mps']:g} m/s")


def sysid_steering_input(df: pd.DataFrame, metadata: dict, quality: dict, path: Path) -> Path:
    fig, ax = fs.subplots(height_in=2.9)
    ax.plot(df["time_s"], df["command_steer_rad"], color=C["command"], linestyle="--", linewidth=1.0, label="Commanded", zorder=3)
    ax.plot(df["time_s"], df["steer_rad"], color=C["reference"], linewidth=1.0, label="Achieved (Gym state)")
    zero_line(ax)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Steering angle [rad]")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    peak = float(df[["command_steer_rad", "steer_rad"]].abs().max().max())
    limit = float(metadata["saturation_threshold_rad"])
    fs.title(fig, f"{fs.SIMULATOR}, open occupancy map",
             f"The steering chirp stays within ±{peak:.3f} rad, far inside the ±{limit:.2f} rad steering limit")
    saturated = quality["steering_saturation_fraction"]
    fs.footnote(fig, f"{_chirp_label(metadata)}; n = {int(quality['num_samples']):,} samples. "
                     f"The 95 % steering limit lies outside the plotted range; saturated fraction {saturated:g}.")
    return fs.save(fig, path)[0]


def sysid_yaw_response(df: pd.DataFrame, metadata: dict, quality: dict, path: Path) -> Path:
    fig, (ax_yaw, ax_slip) = fs.subplots(2, 1, height_in=3.8, sharex=True)
    ax_yaw.plot(df["time_s"], df["yaw_rate_radps"], color=C["reference"], linewidth=1.0)
    ax_yaw.set_ylabel("Yaw rate [rad/s]")
    ax_slip.plot(df["time_s"], df["slip_angle_rad"], color=C["reference"], linewidth=1.0)
    ax_slip.set_ylabel("Slip angle [rad]")
    ax_slip.set_xlabel("Time [s]")
    for letter, ax in zip("AB", (ax_yaw, ax_slip)):
        zero_line(ax)
        fs.panel_letter(ax, letter)
    fig.align_ylabels((ax_yaw, ax_slip))
    slip_range = float(df["slip_angle_rad"].max() - df["slip_angle_rad"].min())
    fs.title(fig, f"{fs.SIMULATOR}, open occupancy map",
             f"The chirp excites yaw rate over a {quality['yaw_rate_range_radps']:.2f} rad/s range "
             f"and slip angle over {slip_range:.3f} rad")
    fs.footnote(fig, f"{_chirp_label(metadata)}; n = {int(quality['num_samples']):,} Gym states.")
    return fs.save(fig, path)[0]


def sysid_speed_hold(df: pd.DataFrame, metadata: dict, quality: dict, path: Path) -> Path:
    target = float(metadata["target_speed_mps"])
    low, high = 0.85 * target, 1.15 * target
    fig, ax = fs.subplots(height_in=2.9)
    ax.axhspan(low, high, color=C["grid"], alpha=0.7, linewidth=0, label="±15 % band")
    ax.plot(df["time_s"], df["command_speed_mps"], color=C["command"], linestyle="--", linewidth=1.0, label="Commanded", zorder=3)
    ax.plot(df["time_s"], df["speed_mps"], color=C["reference"], linewidth=1.0, label="Achieved (Gym state)")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Speed [m/s]")
    ax.set_ylim(bottom=0)
    ax.legend(loc="lower right", ncol=3)
    outside = df[(df["speed_mps"] < low) | (df["speed_mps"] > high)]
    settle = float(outside["time_s"].max()) if not outside.empty else 0.0
    fs.title(fig, f"{fs.SIMULATOR}, open occupancy map",
             f"After {settle:.1f} s of start-up, speed stays inside the ±15 % band around {target:g} m/s")
    fs.footnote(fig, f"{_chirp_label(metadata)}. Mean {quality['speed_mean_mps']:.2f} m/s, "
                     f"coefficient of variation {quality['speed_cv'] * 100:.1f} %; n = {int(quality['num_samples']):,}.")
    return fs.save(fig, path)[0]


# --- Dynamic parameter identification -------------------------------------------

def draw_parameter_fit(run_dir: Path, fit_path: Path, residual_path: Path, evidence: str = fs.SIMULATOR) -> list[Path]:
    fs.apply()
    fit_trace = pd.read_csv(run_dir / "fit_trace.csv")
    validation = pd.read_csv(run_dir / "heldout_replay_trace.csv")
    return [parameter_fit(fit_trace, fit_path, evidence), parameter_residuals(validation, residual_path, evidence)]


def parameter_fit(fit_trace: pd.DataFrame, path: Path, evidence: str) -> Path:
    heldout = fit_trace[fit_trace["partition"] == "heldout"]
    start, end = float(heldout["time_s"].iloc[0]), float(fit_trace["time_s"].iloc[-1])
    fig, axes = fs.subplots(2, 1, height_in=4.0, sharex=True)
    rows = [("A", "yaw_rate_radps", "Yaw rate [rad/s]"), ("B", "slip_angle_rad", "Slip angle [rad]")]
    for ax, (letter, stem, label) in zip(axes, rows):
        ax.axvspan(start, end, color=C["grid"], alpha=0.6, linewidth=0, label="Held-out intervals")
        ax.plot(fit_trace["time_s"], fit_trace[f"measured_{stem}"], color=C["reference"], linewidth=2.4, alpha=0.45, label="Gym (measured)")
        ax.plot(fit_trace["time_s"], fit_trace[f"predicted_{stem}"], color=C["dynamic"], linewidth=0.8, label="Fitted model, one step ahead")
        zero_line(ax)
        ax.set_ylabel(label)
        fs.panel_letter(ax, letter)
    axes[0].legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    axes[-1].set_xlabel("Time [s]")
    fig.align_ylabels(axes)
    worst = float(fit_trace[["yaw_rate_residual_radps", "slip_angle_residual_rad"]].abs().max().max())
    counts = fit_trace["partition"].value_counts()
    fs.title(fig, evidence, f"The fitted single-track model matches Gym within {sci(worst)} on training and held-out intervals")
    fs.footnote(fig, f"Intervals: {counts.get('train', 0):,} training, {counts.get('heldout', 0):,} held out (final 30 %). "
                     "A simulator-recovery test with Gym internal states; not vehicle identification.")
    return fs.save(fig, path)[0]


def parameter_residuals(validation: pd.DataFrame, path: Path, evidence: str) -> Path:
    fig, axes = fs.subplots(3, 1, height_in=4.6, sharex=True)
    rows = [("A", "yaw_rate_error_radps", "Yaw-rate error\n[10⁻⁹ rad/s]"),
            ("B", "slip_angle_error_rad", "Slip-angle error\n[10⁻⁹ rad]"),
            ("C", "yaw_error_rad", "Yaw error\n[10⁻⁹ rad]")]
    for ax, (letter, column, label) in zip(axes, rows):
        ax.plot(validation["time_s"], validation[column] * 1e9, color=C["dynamic"], linewidth=0.9)
        zero_line(ax)
        ax.set_ylabel(label)
        fs.panel_letter(ax, letter)
        ax.margins(y=0.12)
    axes[-1].set_xlabel("Time [s]")
    fig.align_ylabels(axes)
    worst = float(validation[[r[1] for r in rows]].abs().max().max())
    duration = float(validation["time_s"].iloc[-1] - validation["time_s"].iloc[0])
    fs.title(fig, evidence, f"Held-out rollout residuals stay below {sci(worst)} over {duration:.1f} s")
    fs.footnote(fig, f"Independent rollout of the fitted model over the held-out {duration:.1f} s; n = {len(validation):,} samples. "
                     "Residual = fitted model minus Gym.")
    return fs.save(fig, path)[0]


# --- Pure-pursuit sweep ----------------------------------------------------------

CLASS_STYLE = {  # classification -> (label, colour, marker, filled)
    "stable": ("Stable", C["rk4"], "o", True),
    "oscillatory": ("Oscillatory", C["euler"], "^", True),
    "corner_cutting": ("Corner cutting", C["kinematic"], "D", True),
    "incomplete": ("No lap within time limit", C["neutral"], "s", False),
    "collision": ("Collision", C["alarm"], "X", True),
}


def draw_pure_pursuit(run_dir: Path = RUNS / "pure_pursuit_sweep", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    results = pd.read_csv(run_dir / "results.csv")
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    return [pp_heatmap(results, metadata, "rms_cte", figure_dir / "pure_pursuit_sweep_rms_cte_heatmap.png"),
            pp_heatmap(results, metadata, "lap_time", figure_dir / "pure_pursuit_sweep_lap_time_heatmap.png"),
            pp_regions(results, metadata, figure_dir / "pure_pursuit_sweep_regions.png")]


def _pp_note(results: pd.DataFrame, metadata: dict) -> str:
    return (f"n = {len(results)} closed-loop runs, one per setting; integration step {metadata['integration_dt_s'] * 1000:g} ms, "
            f"control {metadata['control_rate_hz']:g} Hz.")


def _baseline(results: pd.DataFrame) -> pd.Series:
    rows = results[results["selected_baseline"].astype(bool)]
    assert len(rows) == 1, "expected one selected baseline"
    return rows.iloc[0]


def pp_heatmap(results: pd.DataFrame, metadata: dict, kind: str, path: Path) -> Path:
    lookaheads = sorted(results["lookahead_m"].unique())
    gains = sorted(results["vgain"].unique(), reverse=True)
    completed = results["completed_lap"].astype(bool)
    column = "rms_cte_m" if kind == "rms_cte" else "lap_time_s"
    grid = np.full((len(gains), len(lookaheads)), np.nan)
    status = np.empty(grid.shape, dtype=object)
    for row in results.itertuples(index=False):
        i, j = gains.index(row.vgain), lookaheads.index(row.lookahead_m)
        status[i, j] = row.classification
        if kind == "rms_cte" or bool(row.completed_lap):
            grid[i, j] = getattr(row, column)
    fig, ax = fs.subplots(height_in=3.6, width_in=6.0)
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("white")
    image = ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, aspect="auto")
    norm = image.norm
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            value = grid[i, j]
            if np.isnan(value):
                text, color = ("Collision" if status[i, j] == "collision" else "No lap"), C["neutral"]
            else:
                text = f"{value:.2f}" if kind == "rms_cte" else f"{value:.1f}"
                r, g, b, _ = cmap(norm(value))
                color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) > 0.5 else "white"
            ax.text(j, i, text, ha="center", va="center", fontsize=fs.SMALL, color=color)
            if kind == "rms_cte" and status[i, j] in ("collision", "incomplete"):
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="///", edgecolor="white",
                                           linewidth=0, alpha=0.6))
    base = _baseline(results)
    bi, bj = gains.index(base["vgain"]), lookaheads.index(base["lookahead_m"])
    ax.add_patch(plt.Rectangle((bj - 0.5, bi - 0.5), 1, 1, fill=False, edgecolor="black", linewidth=1.6))
    ax.set_xticks(range(len(lookaheads)), [f"{v:g}" for v in lookaheads])
    ax.set_yticks(range(len(gains)), [f"{v:g}" for v in gains])
    ax.set_xlabel("Lookahead distance [m]")
    ax.set_ylabel("Velocity gain")
    ax.grid(False)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax, shrink=0.9)
    bar.outline.set_visible(False)
    if kind == "rms_cte":
        bar.set_label("RMS cross-track error [m]")
        done = results[completed]
        takeaway = "Among completed laps, RMS cross-track error grows with lookahead and velocity gain"
        _check_monotone(done, "rms_cte_m", increasing=True)
        note = _pp_note(results, metadata) + "\nHatched cells did not complete a lap; their RMS covers the partial run. Black box: selected baseline."
    else:
        bar.set_label("Lap time [s]")
        done = results[completed]
        _check_monotone(done, "lap_time_s", increasing=False, along="vgain")
        takeaway = (f"Completed laps get faster as velocity gain rises "
                    f"({done['lap_time_s'].min():.1f} to {done['lap_time_s'].max():.1f} s)")
        note = _pp_note(results, metadata) + f"\n{int((~completed).sum())} runs did not complete a lap and have no lap time. Black box: selected baseline."
    fs.title(fig, f"{fs.SIMULATOR}, pure pursuit", takeaway)
    fs.footnote(fig, note)
    return fs.save(fig, path)[0]


def _check_monotone(done: pd.DataFrame, column: str, increasing: bool, along: str | None = None) -> None:
    """Title claims hold for every completed run: test them before rendering."""
    axes = [along] if along else ["vgain", "lookahead_m"]
    for axis in axes:
        other = "lookahead_m" if axis == "vgain" else "vgain"
        for _, group in done.groupby(other):
            values = group.sort_values(axis)[column].to_numpy()
            steps = np.diff(values)
            assert (steps > 0).all() if increasing else (steps < 0).all(), f"{column} is not monotone in {axis}"


def pp_regions(results: pd.DataFrame, metadata: dict, path: Path) -> Path:
    fig, ax = fs.subplots(height_in=3.4, width_in=6.0)
    for key, (label, color, marker, filled) in CLASS_STYLE.items():
        group = results[results["classification"] == key]
        if group.empty:
            continue
        ax.scatter(group["lookahead_m"], group["vgain"], s=70, marker=marker, label=f"{label} ({len(group)})",
                   facecolors=color if filled else "white", edgecolors=color, linewidths=1.2, zorder=3)
    base = _baseline(results)
    ax.scatter([base["lookahead_m"]], [base["vgain"]], s=230, facecolors="none", edgecolors="black", linewidths=1.2, zorder=2)
    ax.annotate("Selected baseline", (base["lookahead_m"], base["vgain"]), xytext=(12, 10), textcoords="offset points",
                fontsize=fs.SMALL, arrowprops={"arrowstyle": "-", "color": "black", "linewidth": 0.7})
    ax.set_xticks(sorted(results["lookahead_m"].unique()), [f"{v:g}" for v in sorted(results["lookahead_m"].unique())])
    ax.set_yticks(sorted(results["vgain"].unique()), [f"{v:g}" for v in sorted(results["vgain"].unique())])
    ax.set_xlabel("Lookahead distance [m]")
    ax.set_ylabel("Velocity gain")
    ax.margins(0.08)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    completed = int(results["completed_lap"].astype(bool).sum())
    assert base["classification"] == "stable"
    fs.title(fig, f"{fs.SIMULATOR}, pure pursuit",
             f"{completed} of {len(results)} settings complete a lap; the selected baseline "
             f"({base['lookahead_m']:g} m, gain {base['vgain']:g}) is stable")
    fs.footnote(fig, _pp_note(results, metadata) + " Classes follow experiments/pure_pursuit_sweep.py.")
    return fs.save(fig, path)[0]


# --- EKF study ---------------------------------------------------------------------

SCENARIO_NAMES = {
    "clean_measurements": "Clean measurements",
    "low_noise": "Low noise",
    "high_noise": "High noise",
    "dropout_1s": "1 s dropout",
    "dropout_3s": "3 s dropout",
}


def draw_ekf(run_dir: Path = RUNS / "ekf_study", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    trace = pd.read_csv(run_dir / "trace.csv")
    summary = pd.read_csv(run_dir / "summary.csv")
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    return [ekf_position_error(trace, metadata, figure_dir / "ekf_position_error_over_time.png"),
            ekf_rmse_summary(summary, figure_dir / "ekf_rmse_summary.png"),
            ekf_dropout_zoom(trace, metadata, figure_dir / "ekf_dropout_zoom.png")]


def _windows(metadata: dict, scenario: str) -> list[tuple[float, float]]:
    return [(w["start_s"], w["start_s"] + w["duration_s"]) for w in metadata["scenarios"][scenario]["dropout_windows"]]


def _ekf_note(metadata: dict, trace: pd.DataFrame) -> str:
    return (f"Same nominal pure-pursuit lap ({trace['time_s'].max():.1f} s) for every scenario; seed {metadata['seed']}, "
            f"{metadata['integration_dt_s'] * 1000:g} ms steps. Dead reckoning uses no measurements, so its error is the same in every scenario.")


def ekf_position_error(trace: pd.DataFrame, metadata: dict, path: Path) -> Path:
    fig, ax = fs.subplots(height_in=3.2)
    dead = trace[(trace["estimator"] == "dead_reckoning")]
    first = dead[dead["scenario"] == "low_noise"]
    for scenario, group in dead.groupby("scenario"):
        assert np.array_equal(group["position_error_m"].to_numpy(), first["position_error_m"].to_numpy()), scenario
    ax.plot(first["time_s"], first["position_error_m"], color=C["dead_reckoning"], linewidth=1.2, label="Dead reckoning")
    styles = {"low_noise": "-", "dropout_1s": "--"}
    peaks = []
    for scenario, style in styles.items():
        group = trace[(trace["scenario"] == scenario) & (trace["estimator"] == "ekf")]
        peaks.append(float(group["position_error_m"].max()))
        ax.plot(group["time_s"], group["position_error_m"], color=C["ekf"], linestyle=style, linewidth=1.0,
                label=f"EKF, {SCENARIO_NAMES[scenario].lower()}")
    for start, stop in _windows(metadata, "dropout_1s"):
        ax.axvspan(start, stop, color=C["alarm"], alpha=0.15, linewidth=0, label="1 s measurement dropout")
    ax.set_yscale("log")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Position error [m]")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, borderaxespad=0.2)
    fs.title(fig, f"{fs.SIMULATOR}, simulated sensor noise",
             f"The EKF keeps position error below {np.ceil(max(peaks) * 10) / 10:.1f} m; dead reckoning drifts to "
             f"{first['position_error_m'].max():.0f} m")
    fs.footnote(fig, _ekf_note(metadata, trace))
    return fs.save(fig, path)[0]


def ekf_rmse_summary(summary: pd.DataFrame, path: Path) -> Path:
    order = [s for s in SCENARIO_NAMES if s in set(summary["scenario"])]
    pivot = summary.pivot(index="scenario", columns="estimator", values="position_rmse_m").loc[order]
    fig, ax = fs.subplots(height_in=2.8)
    y = np.arange(len(order))[::-1]
    ax.hlines(y, pivot["ekf"], pivot["dead_reckoning"], color=C["grid"], linewidth=2.0, zorder=1)
    ax.plot(pivot["dead_reckoning"], y, "o", color=C["dead_reckoning"], markersize=6, label="Dead reckoning", zorder=3)
    ax.plot(pivot["ekf"], y, "o", color=C["ekf"], markersize=6, label="EKF", zorder=3)
    ax.set_yticks(y, [SCENARIO_NAMES[s] for s in order])
    ax.set_xscale("log")
    ax.set_xlabel("Position RMSE [m] (log scale; lower is better)")
    ax.grid(axis="y", visible=False)
    ax.margins(x=0.08, y=0.12)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    fs.title(fig, f"{fs.SIMULATOR}, simulated sensor noise",
             f"EKF position RMSE stays below {np.ceil(pivot['ekf'].max() * 100) / 100:.2f} m in every scenario; "
             f"dead reckoning reaches {pivot['dead_reckoning'].max():.1f} m")
    fs.footnote(fig, f"n = 1 seeded run per scenario and estimator ({len(order)} scenarios), whole lap.")
    return fs.save(fig, path)[0]


def ekf_dropout_zoom(trace: pd.DataFrame, metadata: dict, path: Path) -> Path:
    (start, stop), = _windows(metadata, "dropout_3s")
    lo, hi = start - 1.5, stop + 1.0
    window = trace[(trace["scenario"] == "dropout_3s") & trace["time_s"].between(lo, hi)]
    fig, ax = fs.subplots(height_in=3.0)
    ax.axvspan(start, stop, color=C["alarm"], alpha=0.15, linewidth=0, label=f"{stop - start:g} s measurement dropout")
    for estimator, label in [("dead_reckoning", "Dead reckoning"), ("ekf", "EKF")]:
        group = window[window["estimator"] == estimator]
        ax.plot(group["time_s"], group["position_error_m"], color=C[estimator], linewidth=1.2, label=label)
    ax.set_yscale("log")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Position error [m]")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    ekf = window[window["estimator"] == "ekf"]
    fs.title(fig, f"{fs.SIMULATOR}, 3 s dropout scenario",
             f"During the dropout EKF error grows to {ekf['position_error_m'].max():.1f} m, then falls to "
             f"{ekf['position_error_m'].iloc[-1]:.2f} m by {ekf['time_s'].iloc[-1]:.0f} s")
    fs.footnote(fig, f"All measurement channels are withheld from {start:g} to {stop:g} s. " + _ekf_note(metadata, trace).split("; ")[0] + ".")
    return fs.save(fig, path)[0]


# --- Failure-mode screen ----------------------------------------------------------

FMEA_NAMES = {
    "euler_instability": "Euler instability",
    "bad_lookahead_small": "Lookahead too small",
    "bad_lookahead_large": "Lookahead too large",
    "latency_100ms": "100 ms control latency",
    "steering_saturation": "Steering saturation",
    "sensor_noise_high": "High sensor noise",
    "measurement_dropout_3s": "3 s measurement dropout",
}


def draw_fmea(run_dir: Path = RUNS / "failure_mode_fmea", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    results = pd.read_csv(run_dir / "results.csv")
    return [fmea_rpn(results, figure_dir / "fmea_rpn_bar.png"),
            fmea_detection_signals(results, figure_dir / "fmea_detection_signals.png")]


def fmea_rpn(results: pd.DataFrame, path: Path) -> Path:
    ordered = results.sort_values("rpn", ascending=True)
    fig, ax = fs.subplots(height_in=3.2)
    y = np.arange(len(ordered))
    reproduced = ordered["reproduced"].astype(bool).to_numpy()
    ax.barh(y, ordered["rpn"], height=0.6, color=[C["neutral"] if r else "white" for r in reproduced],
            edgecolor=C["neutral"], hatch=None, linewidth=0.8)
    for yi, (r, row) in enumerate(zip(reproduced, ordered.itertuples(index=False))):
        if not r:
            ax.barh(yi, row.rpn, height=0.6, color="none", edgecolor=C["neutral"], hatch="////", linewidth=0)
        ax.annotate(f"{row.rpn} = {row.severity_1_to_10} × {row.occurrence_1_to_10} × {row.detectability_1_to_10}",
                    (row.rpn, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=fs.SMALL)
    ax.set_yticks(y, [FMEA_NAMES.get(s, s) for s in ordered["scenario"]])
    ax.set_xlim(0, ordered["rpn"].max() * 1.32)
    ax.set_xlabel("Risk priority number (RPN)")
    ax.grid(axis="y", visible=False)
    top = ordered.iloc[-1]
    assert (results["rpn"] < top["rpn"]).sum() == len(results) - 1, "RPN maximum is tied"
    fs.title(fig, f"{fs.SIMULATOR}, failure-mode screen",
             f"{FMEA_NAMES.get(top['scenario'], top['scenario'])} carries the highest risk priority (RPN {top['rpn']})")
    fs.footnote(fig, "RPN = severity × occurrence × detectability, each scored 1 to 10. "
                     "Hatched: failure not reproduced in simulation.")
    return fs.save(fig, path)[0]


def _signal_group(signal: str) -> str:
    text = signal.lower()
    if text.startswith("collision at"):
        return "time"
    if "steer" in text:
        return "steer"
    return "position"


def fmea_detection_signals(results: pd.DataFrame, path: Path) -> Path:
    groups = [("time", "Time to collision [s]", "Detected as a collision"),
              ("position", "Position error [m]", "Detected as tracking or estimate error"),
              ("steer", "Steering command at limit [rad]", "Detected as steering dwell at the limit")]
    data = results.assign(group=results["detection_signal"].map(_signal_group))
    sizes = [max(int((data["group"] == g).sum()), 1) for g, _, _ in groups]
    fig, axes = fs.subplots(len(groups), 1, height_in=4.6, gridspec_kw={"height_ratios": sizes})
    for letter, ax, (key, xlabel, panel_title) in zip("ABC", axes, groups):
        part = data[data["group"] == key].sort_values("detection_metric")
        y = np.arange(len(part))
        reproduced = part["reproduced"].astype(bool).to_numpy()
        ax.hlines(y, 0, part["detection_metric"], color=C["grid"], linewidth=1.5, zorder=1)
        ax.scatter(part["detection_metric"], y, s=36, zorder=3, linewidths=1.2, edgecolors=C["neutral"],
                   facecolors=[C["neutral"] if r else "white" for r in reproduced])
        for yi, value in zip(y, part["detection_metric"]):
            ax.annotate(f"{value:.3g}", (value, yi), xytext=(6, 0), textcoords="offset points", va="center", fontsize=fs.SMALL)
        ax.set_yticks(y, [FMEA_NAMES.get(s, s) for s in part["scenario"]])
        ax.set_ylim(-0.6, len(part) - 0.4)
        ax.set_xlim(0, part["detection_metric"].max() * 1.25)
        ax.set_xlabel(xlabel)
        ax.set_title(panel_title)
        ax.grid(axis="y", visible=False)
        fs.panel_letter(ax, letter)
    collisions = data[data["group"] == "time"]
    fs.title(fig, f"{fs.SIMULATOR}, failure-mode screen",
             f"Lookahead and latency faults collide within {np.ceil(collisions['detection_metric'].max() * 10) / 10:.1f} s; "
             "noise and dropout show only as EKF position error")
    fs.footnote(fig, "Each failure mode has its own detection signal, so each unit gets its own axis. "
                     "Open markers: failure not reproduced in simulation.")
    return fs.save(fig, path)[0]


# --- Parameter-identification robustness -----------------------------------------

def draw_parameter_id_robustness(run_dir: Path = RUNS / "parameter_id_robustness", figure_dir: Path = FIGURES) -> list[Path]:
    fs.apply()
    results = pd.read_csv(run_dir / "results.csv")
    return [parameter_id_degradation(results, "noise", figure_dir / "parameter_id_noise_degradation.png"),
            parameter_id_degradation(results, "latency", figure_dir / "parameter_id_latency_degradation.png"),
            parameter_id_condition(results, figure_dir / "parameter_id_condition_number.png")]


def _scenario_label(name: str) -> str:
    if name == "nominal":
        return "Nominal"
    kind, _, level = name.partition("_")
    return {"noise": f"{level.capitalize()} noise", "latency": level.replace("ms", " ms"),
            "quantization": f"{level.capitalize()} quantization", "combined": f"Combined {level}"}.get(kind, name)


def parameter_id_degradation(results: pd.DataFrame, kind: str, path: Path) -> Path:
    subset = results[results["kind"].isin(["nominal", kind])].reset_index(drop=True)
    x = np.arange(len(subset))
    passed = subset["acceptance_passed"].astype(bool).to_numpy()
    fig, ax = fs.subplots(height_in=3.3, width_in=6.0)
    for param, name in [("C_Sf", "Front (C_Sf)"), ("C_Sr", "Rear (C_Sr)")]:
        values = subset[f"{param}_oracle_relative_error"].to_numpy()
        ax.plot(x, values, color=C[param], linewidth=1.0, zorder=2)
        ax.scatter(x, values, s=34, color=C[param], zorder=3, linewidths=1.2,
                   facecolors=[C[param] if p else "white" for p in passed], label=f"{name} cornering stiffness")
        other = subset["C_Sr_oracle_relative_error" if param == "C_Sf" else "C_Sf_oracle_relative_error"].iloc[-1]
        ax.annotate(name.split()[0], (x[-1], values[-1]), xytext=(6, 5 if values[-1] >= other else -5),
                    textcoords="offset points", va="center", fontsize=fs.SMALL, color=C[param])
    ax.set_xticks(x, [_scenario_label(s) for s in subset["scenario"]])
    ax.set_yscale("log")
    ax.set_ylabel("Relative error vs Gym value")
    ax.set_xlabel("Telemetry noise level" if kind == "noise" else "Added telemetry latency")
    ax.margins(x=0.12)
    ax.grid(axis="x", visible=False)
    perturbed = subset[subset["kind"] == kind]
    front, rear = perturbed["C_Sf_oracle_relative_error"], perturbed["C_Sr_oracle_relative_error"]
    if kind == "noise":
        assert (np.diff(subset["C_Sf_oracle_relative_error"]) > 0).all() and (np.diff(subset["C_Sr_oracle_relative_error"]) > 0).all()
        takeaway = (f"Cornering-stiffness error rises with every noise step, to {front.iloc[-1]:.0%} front "
                    f"and {rear.iloc[-1]:.0%} rear")
    else:
        assert (perturbed["first_failed_gate"] == "oracle_recovery").all()
        takeaway = (f"Every tested latency fails parameter recovery: front error {front.min():.0%} to {front.max():.0%}, "
                    f"rear {rear.min():.0%} to {rear.max():.0%}")
    fs.title(fig, f"{fs.SIMULATOR}, perturbed excitation telemetry", takeaway)
    fs.footnote(fig, "One seeded fit per setting. Open markers: the fit failed at least one acceptance gate.")
    return fs.save(fig, path)[0]


def parameter_id_condition(results: pd.DataFrame, path: Path) -> Path:
    data = results.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(data))
    fig, ax = fs.subplots(height_in=3.6, width_in=5.6)
    ax.hlines(y, 1.0, data["jacobian_condition_number"], color=C["grid"], linewidth=1.5, zorder=1)
    ax.plot(data["jacobian_condition_number"], y, "o", color=C["neutral"], markersize=5, zorder=3)
    ax.axvline(1.0, color=C["neutral"], linewidth=0.6)
    ax.set_yticks(y, [_scenario_label(s) for s in data["scenario"]])
    ax.set_xlim(0.95, data["jacobian_condition_number"].max() * 1.08)
    ax.set_xlabel("Normalized Jacobian condition number (1 = ideal)")
    ax.grid(axis="y", visible=False)
    values = results["jacobian_condition_number"]
    fs.title(fig, f"{fs.SIMULATOR}, perturbed excitation telemetry",
             f"The Jacobian condition number stays between {np.floor(values.min() * 10) / 10:.1f} and "
             f"{np.ceil(values.max() * 10) / 10:.1f} under every perturbation")
    fs.footnote(fig, f"n = {len(results)} settings, one seeded fit each. Conditioning stays far from the 100 acceptance limit.")
    return fs.save(fig, path)[0]


# --- Item 11 ROS-backed capture ------------------------------------------------------

def draw_item11(evidence_dir: Path = ITEM11, figure_dir: Path | None = None) -> list[Path]:
    fs.apply()
    figure_dir = figure_dir or evidence_dir / "figures"
    enriched = pd.read_csv(evidence_dir / "telemetry" / "enriched_bridge.csv")
    preflight = json.loads((evidence_dir / "metrics" / "enriched_preflight.json").read_text(encoding="utf-8"))
    paths = [item11_steering(enriched, preflight, figure_dir / "steering_command_vs_achieved.png")]
    paths += draw_parameter_fit(evidence_dir / "metrics" / "enriched_fit", figure_dir / "enriched_ros_fit.png",
                                figure_dir / "enriched_ros_residuals.png", fs.SIMULATOR_ROS)
    return paths


def item11_steering(enriched: pd.DataFrame, preflight: dict, path: Path) -> Path:
    m = preflight["metrics"]
    fig, ax = fs.subplots(height_in=2.9)
    ax.plot(enriched["time_s"], enriched["command_steer_rad"], color=C["command"], linestyle="--", linewidth=0.9, label="Commanded", zorder=3)
    ax.plot(enriched["time_s"], enriched["steer_rad"], color=C["reference"], linewidth=0.9, label="Achieved (native state)")
    zero_line(ax)
    ax.set_xlabel("Simulator time [s]")
    ax.set_ylabel("Steering angle [rad]")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    fs.title(fig, fs.SIMULATOR_ROS,
             f"Achieved steering follows the command within {m['command_achieved_rmse_rad']:.3f} rad RMSE "
             f"(maximum {m['command_achieved_max_abs_rad']:.3f} rad)")
    fs.footnote(fig, f"Enriched bridge bag, n = {len(enriched):,} samples. Best command shift {int(m['best_command_lag_samples'])} samples "
                     f"({m['best_command_lag_s']:.3f} s). Simulator steering controller, not a physical actuator.")
    return fs.save(fig, path)[0]


GROUPS = {
    "integrator": None,  # experiments/plot_integrator_comparison.py
    "convergence": draw_integrator_convergence,
    "dynamic-replay": draw_dynamic_replay,
    "kinematic-replay": draw_kinematic_replay,
    "excitation": draw_sysid_excitation,
    "parameter-fit": lambda: draw_parameter_fit(RUNS / "dynamic_parameter_identification",
                                                FIGURES / "dynamic_parameter_fit.png",
                                                FIGURES / "dynamic_parameter_residuals.png"),
    "pure-pursuit": draw_pure_pursuit,
    "ekf": draw_ekf,
    "fmea": draw_fmea,
    "parameter-id-robustness": draw_parameter_id_robustness,
    "item11": draw_item11,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", choices=sorted(GROUPS), help="figure groups to redraw (default: all)")
    args = parser.parse_args()
    for name in args.only or list(GROUPS):
        if name == "integrator":
            import plot_integrator_comparison
            plot_integrator_comparison.main()
            continue
        for path in GROUPS[name]():
            print(f"Wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
