#!/usr/bin/env python
"""Create a report-quality RK4 vs Euler integrator sensitivity figure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

import figure_style as fs
from figure_style import COLORS as C

REPO_ROOT = Path(__file__).resolve().parents[1]

TELEMETRY_PATH = REPO_ROOT / "runs" / "first_lap" / "telemetry.csv"
METADATA_PATH = REPO_ROOT / "runs" / "first_lap" / "metadata.json"
CONFIG_PATH = REPO_ROOT / "examples" / "config_example_map.yaml"
WAYPOINTS_PATH = REPO_ROOT / "examples" / "example_waypoints.csv"
COMBINED_PATH = REPO_ROOT / "reports" / "figures" / "first_integrator_comparison.png"
TRAJECTORY_PATH = REPO_ROOT / "reports" / "figures" / "integrator_trajectory_overlay.png"
TRACKING_ERROR_PATH = REPO_ROOT / "reports" / "figures" / "integrator_tracking_error_vs_progress.png"
SUMMARY_METRICS_PATH = REPO_ROOT / "reports" / "figures" / "integrator_summary_metrics.png"
EVIDENCE = f"{fs.SIMULATOR}, pure pursuit, first lap"


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def load_metadata(path: Path) -> dict[str, Any]:
    ensure_exists(path, "metadata file")
    with path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    if not isinstance(metadata, dict):
        raise ValueError(f"Metadata did not load as a dictionary: {path}")
    return metadata


def load_telemetry(path: Path) -> pd.DataFrame:
    ensure_exists(path, "telemetry file")
    df = pd.read_csv(path)
    required = [
        "integrator",
        "time_s",
        "x_m",
        "y_m",
        "speed_mps",
        "cte_m",
        "abs_cte_m",
        "progress_m",
        "collision",
        "termination_reason",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"Telemetry missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    for column in ["time_s", "x_m", "y_m", "speed_mps", "cte_m", "abs_cte_m", "progress_m", "collision"]:
        df[column] = pd.to_numeric(df[column], errors="raise")
    df["integrator"] = df["integrator"].astype(str)
    return df


def load_map_config(path: Path) -> dict[str, Any]:
    ensure_exists(path, "map config")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Map config did not load as a dictionary: {path}")
    return config


def config_value(config: dict[str, Any], candidates: list[str]) -> Any | None:
    lower_map = {str(key).lower(): value for key, value in config.items()}
    for key in candidates:
        if key.lower() in lower_map:
            return lower_map[key.lower()]
    return None


def normalize_delimiter(delimiter: Any | None) -> str | None:
    if delimiter is None:
        return None
    value = str(delimiter)
    if value.lower() in {"whitespace", "space", r"\s+", "regex_whitespace"}:
        return r"\s+"
    return value


def read_waypoint_csv(path: Path, delimiter_hint: Any | None) -> tuple[pd.DataFrame, bool]:
    delimiter = normalize_delimiter(delimiter_hint)
    f1tenth_style = False

    with path.open("r", encoding="utf-8") as file:
        first_data_line = ""
        for line in file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            first_data_line = stripped
            break

    if not first_data_line:
        raise ValueError(f"Waypoint file has no data rows after comments: {path}")

    if delimiter is None:
        delimiter = ";" if ";" in first_data_line else None
    if delimiter == ";":
        f1tenth_style = True

    read_kwargs: dict[str, Any] = {"comment": "#"}
    if delimiter == r"\s+":
        read_kwargs.update({"sep": delimiter, "engine": "python"})
    elif delimiter is not None:
        read_kwargs["sep"] = delimiter

    # F1TENTH waypoint examples are comment-headered and data-only; keep the
    # first numeric row as data instead of accidentally treating it as headers.
    if f1tenth_style:
        waypoint_df = pd.read_csv(path, header=None, **read_kwargs)
        waypoint_df.columns = list(range(waypoint_df.shape[1]))
        return waypoint_df, True

    waypoint_df = pd.read_csv(path, **read_kwargs)
    if waypoint_df.shape[1] >= 2:
        return waypoint_df, False

    waypoint_df = pd.read_csv(path, header=None, **read_kwargs)
    waypoint_df.columns = list(range(waypoint_df.shape[1]))
    return waypoint_df, False


def load_waypoints(path: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, bool]:
    ensure_exists(path, "waypoint file")
    delimiter_hint = config_value(
        config,
        [
            "wpt_delim",
            "waypoint_delimiter",
            "waypoints_delimiter",
            "waypoint_sep",
            "waypoints_sep",
            "csv_delimiter",
            "delimiter",
            "sep",
        ],
    )
    waypoints, f1tenth_style = read_waypoint_csv(path, delimiter_hint)
    if waypoints.shape[1] < 2:
        raise ValueError(
            f"Waypoint file has fewer than 2 columns after parsing: {path}\n"
            f"Columns found: {list(waypoints.columns)}"
        )
    return waypoints, f1tenth_style


def infer_xy_columns(waypoints: pd.DataFrame, config: dict[str, Any], f1tenth_style: bool) -> tuple[Any, Any]:
    x_hint = config_value(config, ["wpt_xind", "waypoint_x_col", "x_col", "x_column", "waypoints_x_col", "waypoints_x"])
    y_hint = config_value(config, ["wpt_yind", "waypoint_y_col", "y_col", "y_column", "waypoints_y_col", "waypoints_y"])

    if x_hint is not None and y_hint is not None:
        x_column = int(x_hint) if f1tenth_style and str(x_hint).isdigit() else x_hint
        y_column = int(y_hint) if f1tenth_style and str(y_hint).isdigit() else y_hint
        if x_column in waypoints.columns and y_column in waypoints.columns:
            return x_column, y_column
        raise ValueError(
            "Waypoint x/y columns were specified in config but were not found in CSV.\n"
            f"x_hint={x_hint}, y_hint={y_hint}, available={list(waypoints.columns)}"
        )

    possible_x = ["x", "x_m", "pos_x", "waypoint_x", "x_pos"]
    possible_y = ["y", "y_m", "pos_y", "waypoint_y", "y_pos"]
    cols_lower = {str(column).lower(): column for column in waypoints.columns}

    for x_name in possible_x:
        for y_name in possible_y:
            if x_name in cols_lower and y_name in cols_lower:
                return cols_lower[x_name], cols_lower[y_name]

    numeric_cols = list(waypoints.select_dtypes(include=[np.number]).columns)
    if f1tenth_style and len(numeric_cols) >= 3:
        # Known F1TENTH format: s, x, y, psi, kappa, vx, ax.
        return numeric_cols[1], numeric_cols[2]

    raise ValueError(
        "Could not infer waypoint x/y columns from CSV or config.\n"
        f"Available columns: {list(waypoints.columns)}"
    )


def summarize_run(telemetry: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for integrator, group in telemetry.groupby("integrator"):
        group = group.sort_values("time_s").reset_index(drop=True)
        collision = bool(pd.to_numeric(group["collision"], errors="coerce").fillna(0).max() > 0)
        termination_series = group["termination_reason"].dropna()
        termination = str(termination_series.iloc[-1]) if not termination_series.empty else "unknown"

        rows.append(
            {
                "Integrator": str(integrator).upper(),
                "Termination": termination,
                "Final time [s]": float(group["time_s"].iloc[-1]),
                "Collision": collision,
                "RMS CTE [m]": float(np.sqrt(np.mean(group["cte_m"] ** 2))),
                "Max CTE [m]": float(group["abs_cte_m"].max()),
                "Mean speed [m/s]": float(group["speed_mps"].mean()),
            }
        )

    summary = pd.DataFrame(rows)
    order = ["RK4", "EULER"]
    if not summary.empty:
        summary["order"] = summary["Integrator"].map(lambda value: order.index(value) if value in order else 999)
        summary = summary.sort_values("order").drop(columns="order").reset_index(drop=True)
    return summary


def trajectory_group(telemetry: pd.DataFrame, integrator: str) -> pd.DataFrame:
    group = telemetry[telemetry["integrator"].str.lower() == integrator].sort_values("time_s")
    if group.empty:
        raise ValueError(f"No {integrator.upper()} rows found in telemetry.")
    return group


def format_summary_for_table(summary: pd.DataFrame) -> pd.DataFrame:
    table_df = summary.copy()
    for column in ["Final time [s]", "RMS CTE [m]", "Max CTE [m]", "Mean speed [m/s]"]:
        table_df[column] = table_df[column].map(lambda value: f"{value:.3f}")
    table_df["Collision"] = table_df["Collision"].map(lambda value: "Yes" if value else "No")
    table_df["Termination"] = table_df["Termination"].map(lambda value: str(value).replace("completed_lap", "completed"))
    return table_df.rename(
        columns={
            "Integrator": "Int.",
            "Termination": "End",
            "Final time [s]": "Final\nTime [s]",
            "Collision": "Hit?",
            "RMS CTE [m]": "RMS\nCTE [m]",
            "Max CTE [m]": "Max\nCTE [m]",
            "Mean speed [m/s]": "Mean\nSpeed [m/s]",
        }
    )


def endpoint_label(group: pd.DataFrame, integrator: str) -> str:
    end = group.iloc[-1]
    collision = bool(pd.to_numeric(group["collision"], errors="coerce").fillna(0).max() > 0)
    termination = str(end["termination_reason"])
    if collision:
        return f"{integrator} collision"
    return f"{integrator} {termination.replace('_', ' ')}"


def endpoint_annotation(group: pd.DataFrame, integrator: str) -> str:
    end = group.iloc[-1]
    return (
        f"{endpoint_label(group, integrator)}\n"
        f"t = {end['time_s']:.2f} s\n"
        f"s = {end['progress_m']:.1f} m"
    )


def _endpoints(rk4: pd.DataFrame, euler: pd.DataFrame):
    return rk4.iloc[0], rk4.iloc[-1], euler.iloc[-1], endpoint_label(euler, "Euler")


def _draw_trajectory(ax, waypoints: pd.DataFrame, x_col: Any, y_col: Any, rk4: pd.DataFrame, euler: pd.DataFrame) -> None:
    start, rk4_finish, euler_end, euler_label = _endpoints(rk4, euler)
    ax.plot(waypoints[x_col], waypoints[y_col], linestyle="--", linewidth=0.9, color="#AAAAAA", label="Reference path", zorder=1)
    ax.plot(rk4["x_m"], rk4["y_m"], linewidth=1.5, color=C["rk4"], label="RK4", zorder=2)
    ax.plot(euler["x_m"], euler["y_m"], linewidth=1.5, color=C["euler"], label="Euler", zorder=2)
    ax.plot(start["x_m"], start["y_m"], "o", markerfacecolor="none", markeredgecolor=C["neutral"], markersize=11,
            markeredgewidth=1.2, label="Start", zorder=4)
    ax.plot(rk4_finish["x_m"], rk4_finish["y_m"], "s", color=C["rk4"], markersize=5, label="RK4 finish", zorder=3)
    ax.plot(euler_end["x_m"], euler_end["y_m"], "X", color=C["alarm"], markersize=8, zorder=5)
    ax.annotate(endpoint_annotation(euler, "Euler"), xy=(euler_end["x_m"], euler_end["y_m"]), xytext=(14, -6),
                textcoords="offset points", va="top", fontsize=fs.SMALL, color=C["neutral"],
                arrowprops={"arrowstyle": "-", "lw": 0.6, "color": C["neutral"]})
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.06)
    ax.legend(loc="best")


def _passes(group: pd.DataFrame) -> list[pd.DataFrame]:
    """Split a run where progress wraps back to the start of the path (the Gym stops after two passes)."""
    wraps = np.flatnonzero(np.diff(group["progress_m"].to_numpy()) < -0.5 * group["progress_m"].max()) + 1
    return [part for part in np.split(group, wraps) if not part.empty]


def _draw_tracking_error(ax, rk4: pd.DataFrame, euler: pd.DataFrame) -> None:
    _, _, euler_end, euler_label = _endpoints(rk4, euler)
    for number, part in enumerate(_passes(rk4), start=1):
        ax.plot(part["progress_m"], part["abs_cte_m"], linewidth=1.1 if number == 1 else 0.8, color=C["rk4"],
                alpha=1.0 if number == 1 else 0.5, label=f"RK4, pass {number}")
    for number, part in enumerate(_passes(euler), start=1):
        ax.plot(part["progress_m"], part["abs_cte_m"], linewidth=1.1, color=C["euler"], label=f"Euler, pass {number}")
    ax.plot(euler_end["progress_m"], euler_end["abs_cte_m"], "X", color=C["alarm"], markersize=8, zorder=4)
    ax.annotate(f"Euler {euler_label.split(' ', 1)[1]} at {euler_end['time_s']:.2f} s", (euler_end["progress_m"], euler_end["abs_cte_m"]),
                xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=fs.SMALL, color=C["euler"])
    ax.set_xlabel("Progress along path [m]")
    ax.set_ylabel("|Cross-track error| [m]")
    ax.set_xlim(left=0)
    ax.set_ylim(0, max(rk4["abs_cte_m"].max(), euler["abs_cte_m"].max()) * 1.12)
    ax.legend(loc="center right")


TABLE_COLUMNS = [  # summary column -> (header, numeric)
    ("Integrator", "Integrator", False),
    ("Termination", "End of run", False),
    ("Final time [s]", "Final\ntime [s]", True),
    ("Collision", "Collision", False),
    ("RMS CTE [m]", "RMS cross-\ntrack error [m]", True),
    ("Max CTE [m]", "Peak cross-\ntrack error [m]", True),
    ("Mean speed [m/s]", "Mean\nspeed [m/s]", True),
]


def _draw_table(ax, summary: pd.DataFrame) -> None:
    table_df = format_summary_for_table(summary)
    table_df["Int."] = table_df["Int."].map(lambda value: "Euler" if value == "EULER" else value)
    ax.axis("off")
    headers = [header for _, header, _ in TABLE_COLUMNS]
    numeric = [is_numeric for _, _, is_numeric in TABLE_COLUMNS]
    table = ax.table(cellText=table_df.values, colLabels=headers, loc="center", cellLoc="left", edges="horizontal",
                     colWidths=[0.12, 0.15, 0.12, 0.12, 0.17, 0.17, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(fs.SMALL)
    table.scale(1.0, 1.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(C["neutral"])
        cell.set_linewidth(0.6 if row <= 1 else 0.0)
        cell.get_text().set_horizontalalignment("right" if numeric[col] else "left")
        cell.PAD = 0.04
        if row == 0:
            cell.set_height(cell.get_height() * 1.6)
    for col in range(len(headers)):
        table[len(table_df), col].visible_edges = "B"
        table[len(table_df), col].set_linewidth(0.6)


def _note() -> str:
    return ("One run per integrator, same map, waypoints and pure-pursuit controller; only the integrator differs. "
            "The Gym stops a completed run after two passes of the path, so RK4 progress wraps once. "
            "This is a closed-loop integrator sensitivity check, not yet a derived bicycle-model comparison.")


def _takeaway(rk4: pd.DataFrame, euler: pd.DataFrame) -> str:
    _, rk4_finish, euler_end, euler_label = _endpoints(rk4, euler)
    euler_event = "collides" if euler_label.endswith("collision") else f"stops ({euler_label.split(' ', 1)[1]})"
    return (f"Euler {euler_event} after {euler_end['time_s']:.2f} s, {euler_end['progress_m']:.1f} m along the path; "
            f"RK4 runs to the Gym's {rk4_finish['termination_reason'].replace('_', ' ')} stop at {rk4_finish['time_s']:.1f} s")


def _summary_title(summary: pd.DataFrame) -> str:
    rows = summary.set_index("Integrator")
    rk4, euler = rows.loc["RK4"], rows.loc["EULER"]
    assert rk4["RMS CTE [m]"] < euler["RMS CTE [m]"] and rk4["Max CTE [m]"] < euler["Max CTE [m]"]
    end = "collides" if euler["Collision"] else "stops"
    return f"Euler {end} at {euler['Final time [s]']:.2f} s; RK4 finishes the run with lower RMS and peak tracking error"


def save_trajectory_overlay(waypoints: pd.DataFrame, x_col: Any, y_col: Any, rk4: pd.DataFrame, euler: pd.DataFrame,
                            output_path: Path) -> None:
    fig, ax = fs.subplots(height_in=5.0, width_in=6.0)
    _draw_trajectory(ax, waypoints, x_col, y_col, rk4, euler)
    fs.title(fig, EVIDENCE, _takeaway(rk4, euler))
    fs.footnote(fig, _note())
    fs.save(fig, output_path)


def save_tracking_error_plot(rk4: pd.DataFrame, euler: pd.DataFrame, output_path: Path) -> None:
    fig, ax = fs.subplots(height_in=3.0)
    _draw_tracking_error(ax, rk4, euler)
    fs.title(fig, EVIDENCE, _takeaway(rk4, euler))
    fs.footnote(fig, _note())
    fs.save(fig, output_path)


def save_summary_metrics_table(summary: pd.DataFrame, output_path: Path) -> None:
    fig, ax = fs.subplots(height_in=1.7)
    _draw_table(ax, summary)
    fs.title(fig, EVIDENCE, _summary_title(summary))
    fs.footnote(fig, _note())
    fs.save(fig, output_path)


def save_combined_integrator_comparison(waypoints: pd.DataFrame, x_col: Any, y_col: Any, rk4: pd.DataFrame,
                                        euler: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    fig = fs.figure(height_in=5.6)
    grid = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.15], height_ratios=[3.2, 1.0])
    ax_traj, ax_cte, ax_table = fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, :])
    _draw_trajectory(ax_traj, waypoints, x_col, y_col, rk4, euler)
    _draw_tracking_error(ax_cte, rk4, euler)
    _draw_table(ax_table, summary)
    ax_traj.set_title("Trajectories on the example map")
    ax_cte.set_title("Tracking error along the path")
    for letter, ax in zip("ABC", (ax_traj, ax_cte, ax_table)):
        fs.panel_letter(ax, letter)
    fs.title(fig, EVIDENCE, _takeaway(rk4, euler))
    fs.footnote(fig, _note())
    fs.save(fig, output_path)


def plot_integrator_comparison(
    telemetry: pd.DataFrame,
    waypoints: pd.DataFrame,
    config: dict[str, Any],
    f1tenth_style_waypoints: bool,
) -> None:
    x_col, y_col = infer_xy_columns(waypoints, config, f1tenth_style_waypoints)
    print(f"Using waypoint columns: x={x_col}, y={y_col}")

    rk4 = trajectory_group(telemetry, "rk4")
    euler = trajectory_group(telemetry, "euler")
    summary = summarize_run(telemetry)

    fs.apply()
    TRAJECTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_combined_integrator_comparison(waypoints, x_col, y_col, rk4, euler, summary, COMBINED_PATH)
    save_trajectory_overlay(waypoints, x_col, y_col, rk4, euler, TRAJECTORY_PATH)
    save_tracking_error_plot(rk4, euler, TRACKING_ERROR_PATH)
    save_summary_metrics_table(summary, SUMMARY_METRICS_PATH)


def main() -> None:
    metadata = load_metadata(METADATA_PATH)
    telemetry = load_telemetry(TELEMETRY_PATH)
    config = load_map_config(CONFIG_PATH)
    waypoints, f1tenth_style_waypoints = load_waypoints(WAYPOINTS_PATH, config)
    print(f"Loaded metadata for control={metadata.get('control', 'unknown')}")

    plot_integrator_comparison(
        telemetry=telemetry,
        waypoints=waypoints,
        config=config,
        f1tenth_style_waypoints=f1tenth_style_waypoints,
    )
    print(f"Wrote combined figure to {COMBINED_PATH}")
    print(f"Wrote trajectory figure to {TRAJECTORY_PATH}")
    print(f"Wrote tracking error figure to {TRACKING_ERROR_PATH}")
    print(f"Wrote summary metrics figure to {SUMMARY_METRICS_PATH}")


if __name__ == "__main__":
    main()
