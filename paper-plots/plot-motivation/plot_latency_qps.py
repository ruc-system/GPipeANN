#!/usr/bin/env python3
"""Plot SIFT-1B recall@10=0.90 P99 latency vs QPS for the motivation figure."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from matplotlib.transforms import Bbox


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures"))
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"
EVAL_DIR = ROOT / "plot-evaluation"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from better_annotation import draw_better_annotation

MOTIVATION_BETTER_ANNOTATION = {
    "arrow_head": (0.42, 0.56),
    "arrow_tail": (0.52, 0.42),
    "label": (0.498, 0.575),
}

OUTPUT_PDF = OUTPUT_ROOT / "fig-motivation" / "latency_qps.pdf"
GILL_SANS_DIR = FONT_ROOT
REGULAR_FONT_PATH = GILL_SANS_DIR / "GillSans.ttc"
SEMIBOLD_FONT_PATH = GILL_SANS_DIR / "GillSans-SemiBold.ttf"

REGULAR_PROP: FontProperties | None = None
SEMIBOLD_PROP: FontProperties | None = None


@dataclass(frozen=True)
class PlotSeries:
    label: str
    points: list[tuple[float, float]]
    color: str
    marker: str
    linewidth: float = 1.4


SERIES = [
    PlotSeries(
        "GustANN",
        [
            (20.392, 40872.69),
            (21.842, 49204.50),
            (24.088, 62879.24),
            (29.223, 76897.61),
            (37.215, 83117.43),
            (69.693, 86800.66),
            (115.580, 101530.68),
        ],
        "#2ca02c",
        "^",
    ),
    PlotSeries(
        "FlashANNS",
        [
            (4.957, 26647.76),
            (5.737, 43698.99),
            (7.029, 50869.46),
            (9.410, 58803.31),
            (10.424, 65042.49),
            (10.551, 66824.03),
            (12.260, 70274.17),
            (14.452, 71415.82),
        ],
        "#ff7f0e",
        "s",
    ),
    PlotSeries(
        "Quiver(ours)",
        [
            (3.265, 67366.17),
            (5.561, 81680.19),
            (8.235, 88400.72),
            (9.603, 92716.63),
            (11.530, 99085.98),
            (17.944, 103288.34),
        ],
        "#1f77b4",
        "o",
        linewidth=1.6,
    ),
]


def configure_fonts() -> None:
    global REGULAR_PROP, SEMIBOLD_PROP

    for font_path in (REGULAR_FONT_PATH, SEMIBOLD_FONT_PATH):
        if font_path.exists():
            font_manager.fontManager.addfont(font_path)

    regular_name = font_manager.FontProperties(fname=str(REGULAR_FONT_PATH)).get_name()
    REGULAR_PROP = FontProperties(fname=str(REGULAR_FONT_PATH), size=9)
    SEMIBOLD_PROP = FontProperties(fname=str(SEMIBOLD_FONT_PATH), size=9)

    plt.rcParams.update(
        {
            "font.family": regular_name,
            "font.sans-serif": [regular_name],
            "font.weight": "regular",
            "axes.labelweight": "regular",
            "axes.titleweight": "regular",
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def apply_axis_fonts(ax: plt.Axes) -> None:
    if REGULAR_PROP is None:
        return
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(REGULAR_PROP)


def plot_line(ax: plt.Axes, series: PlotSeries) -> None:
    xs = [point[0] for point in series.points]
    ys = [point[1] for point in series.points]
    ax.plot(
        xs,
        ys,
        label=series.label,
        color=series.color,
        marker=series.marker,
        linewidth=series.linewidth,
        markersize=3.4,
    )


def annotate_series(ax: plt.Axes) -> None:
    assert SEMIBOLD_PROP is not None

    ax.annotate(
        "Favor high QPS",
        xy=(52.0, 85950),
        xytext=(41.0, 111500),
        color="#2ca02c",
        fontproperties=SEMIBOLD_PROP,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#2ca02c"},
        ha="left",
        va="center",
    )
    ax.annotate(
        "Favor low latency",
        xy=(7.8, 54500),
        xytext=(8.2, 33500),
        color="#ff7f0e",
        fontproperties=SEMIBOLD_PROP,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#ff7f0e"},
        ha="left",
        va="center",
    )
    ax.annotate(
        "Taming tradeoff",
        xy=(8.7, 90000),
        xytext=(4.2, 117000),
        color="#1f77b4",
        fontproperties=SEMIBOLD_PROP,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#1f77b4"},
        ha="left",
        va="center",
    )


def save_plot() -> None:
    configure_fonts()

    fig, ax = plt.subplots(figsize=(3.5, 1.7))

    for series in SERIES:
        plot_line(ax, series)

    ax.set_xscale("log")
    ax.set_xlim(2.8, 140)
    ax.set_ylim(20000, 149000)
    ax.set_xlabel("P99 Latency (ms)", labelpad=1)
    ax.set_ylabel("Throughput", labelpad=1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}K"))
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(length=2.5, pad=1)
    apply_axis_fonts(ax)

    ax.text(
        0.03,
        0.96,
        "SIFT-1B, Recall@10=0.90",
        transform=ax.transAxes,
        ha="left",
        va="top",
        color="#8f3333",
        fontproperties=SEMIBOLD_PROP,
    )

    annotate_series(ax)
    draw_better_annotation(
        ax,
        annotation=MOTIVATION_BETTER_ANNOTATION,
        fontproperties=SEMIBOLD_PROP,
    )

    legend = ax.legend(
        loc="lower right",
        frameon=True,
        framealpha=0.92,
        borderpad=0.25,
        handlelength=1.3,
        handletextpad=0.4,
        labelspacing=0.25,
    )
    if REGULAR_PROP is not None:
        for text in legend.get_texts():
            text.set_fontproperties(REGULAR_PROP)

    fig.subplots_adjust(left=0.14, right=0.995, bottom=0.28, top=0.96)
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    tight_bbox = fig.get_tightbbox(fig.canvas.get_renderer()).padded(0.01)
    full_bbox = fig.bbox_inches
    vertical_tight_bbox = Bbox.from_extents(
        full_bbox.x0,
        tight_bbox.y0,
        full_bbox.x1,
        tight_bbox.y1,
    )
    fig.savefig(OUTPUT_PDF, bbox_inches=vertical_tight_bbox)
    plt.close(fig)
    print(f"saved: {OUTPUT_PDF}")


def main() -> None:
    save_plot()


if __name__ == "__main__":
    main()
