"""Shared figure rules: font roles, entity colours and deterministic output.

Every generator under experiments/ that writes a report figure uses these
settings, so one entity keeps one colour in every figure and every PNG is
written at the same resolution.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Three font sizes, mapped to role: titles, axis labels and series names use
# BASE; legends and annotations use SMALL; tick labels use TICK. Panel letters
# are the one exception.
BASE, SMALL, TICK = 9, 8, 7
LETTER = 10
WIDTH_IN = 7.0
DPI = 300

# One colour per entity (Okabe-Ito based, readable with colour-vision deficiency).
# The RK4 Gym run is the reference trajectory for every replay and fit, so the
# reference state and RK4 share a colour. Groups that never share a figure may
# reuse a hue; no figure relies on red against green.
COLORS = {
    "reference": "#0072B2",  # Gym RK4 state, or measured motion
    "rk4": "#0072B2",
    "euler": "#E69F00",
    "kinematic": "#CC79A7",  # kinematic bicycle model
    "dynamic": "#009E73",  # single-track dynamic model, known or fitted parameters
    "delay_affine": "#882255",  # delay + affine command-response model
    "command": "#666666",  # commanded input
    "ekf": "#56B4E9",
    "dead_reckoning": "#999999",
    "C_Sf": "#332288",  # front cornering stiffness
    "C_Sr": "#44AA99",  # rear cornering stiffness
    "alarm": "#D55E00",  # collision, dropout, limits and other failure marks only
    "neutral": "#444444",
    "grid": "#DDDDDD",
}

# Evidence classes from docs/data-and-figures.md, shown on line 1 of each title.
SIMULATOR = "Simulator output | F1TENTH Gym"
SIMULATOR_ROS = "Simulator-backed ROS 2 capture | F1TENTH Gym"

RC = {
    "font.size": BASE,
    "axes.titlesize": BASE,
    "axes.labelsize": BASE,
    "axes.titlelocation": "left",
    "axes.titleweight": "normal",
    "figure.titlesize": BASE,
    "figure.titleweight": "normal",
    "legend.fontsize": SMALL,
    "legend.title_fontsize": SMALL,
    "legend.frameon": False,
    "xtick.labelsize": TICK,
    "ytick.labelsize": TICK,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": COLORS["grid"],
    "grid.linewidth": 0.5,
    "axes.axisbelow": True,
    "axes.edgecolor": COLORS["neutral"],
    "lines.linewidth": 1.3,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "figure.dpi": 100,
    "svg.fonttype": "none",
}


def apply(hashsalt: str = "sim-to-real-figures") -> None:
    """Set the shared rcParams for the current process."""
    plt.rcParams.update(RC)
    plt.rcParams["svg.hashsalt"] = hashsalt


def figure(height_in: float, width_in: float = WIDTH_IN, **kwargs):
    """Return a constrained-layout figure at the shared width."""
    return plt.figure(figsize=(width_in, height_in), layout="constrained", **kwargs)


def subplots(nrows: int = 1, ncols: int = 1, height_in: float = 3.2, width_in: float = WIDTH_IN, **kwargs):
    return plt.subplots(nrows, ncols, figsize=(width_in, height_in), layout="constrained", **kwargs)


def _wrap(fig, text: str, size: float) -> str:
    """Wrap each paragraph to the figure width (DejaVu Sans averages ~0.52 em per character)."""
    width = int(fig.get_figwidth() * 72 / (size * 0.52))
    return "\n".join(textwrap.fill(line, width) for line in text.split("\n"))


def title(fig, evidence: str, takeaway: str) -> None:
    """Left-aligned figure title: evidence class on the first line, then the takeaway."""
    fig.suptitle(_wrap(fig, f"{evidence}\n{takeaway}", BASE), x=0.01, ha="left", fontsize=BASE)


def footnote(fig, text: str) -> None:
    """Sample size and fixed conditions, under the figure."""
    fig.supxlabel(_wrap(fig, text, SMALL), x=0.01, ha="left", fontsize=SMALL, color=COLORS["neutral"])


def panel_letter(ax, letter: str) -> None:
    """Bold letter at the top-left corner, outside the axes box."""
    offset = matplotlib.transforms.ScaledTranslation(-4 / 72, 3 / 72, ax.figure.dpi_scale_trans)
    ax.text(0.0, 1.0, letter, transform=ax.transAxes + offset, ha="right", va="bottom",
            fontsize=LETTER, fontweight="bold")


def save(fig, path: Path, formats: tuple[str, ...] = ("png",)) -> list[Path]:
    """Write each format next to `path` with no timestamps, then close the figure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in formats:
        out = path.with_suffix(f".{fmt}")
        metadata = {"png": {"Software": None}, "svg": {"Date": None},
                    "pdf": {"CreationDate": None, "ModDate": None}}[fmt]
        fig.savefig(out, dpi=DPI, metadata=metadata)
        written.append(out)
    plt.close(fig)
    return written


def layout_problems(fig) -> list[str]:
    """Overlapping visible text, text on another axes' spine, or text outside the figure."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_box = fig.bbox
    hidden = set()
    for ax in fig.axes:
        for axis, view in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
            lo, hi = sorted(view)
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not lo - 1e-12 * abs(hi - lo) <= tick.get_loc() <= hi + 1e-12 * abs(hi - lo):
                    hidden.update((tick.label1, tick.label2))
    texts = [(t, t.get_window_extent(renderer)) for t in fig.findobj(matplotlib.text.Text)
             if t.get_visible() and t.get_text().strip() and t not in hidden]
    problems = []
    for t, box in texts:
        if box.x0 < fig_box.x0 - 1 or box.y0 < fig_box.y0 - 1 or box.x1 > fig_box.x1 + 1 or box.y1 > fig_box.y1 + 1:
            problems.append(f"outside figure: {t.get_text()!r}")
    for i, (a, box_a) in enumerate(texts):
        for b, box_b in texts[i + 1:]:
            if box_a.overlaps(box_b):
                problems.append(f"overlap: {a.get_text()!r} / {b.get_text()!r}")
    for ax in fig.axes:
        own = set(ax.get_xticklabels(which="both") + ax.get_yticklabels(which="both"))
        for spine in ax.spines.values():
            if not spine.get_visible():
                continue
            spine_box = spine.get_window_extent(renderer)
            for t, box in texts:
                if t not in own and box.overlaps(spine_box):
                    problems.append(f"on spine: {t.get_text()!r}")
    return problems
