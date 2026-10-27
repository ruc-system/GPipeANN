#!/usr/bin/env python3
"""Plot SIFT-1B QPS sensitivity to queries per block under a P99 target."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures"))
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"
OUTPUT_PDF = OUTPUT_ROOT / "fig-evaluation" / "q_sensitivity.pdf"
GILL_SANS_DIR = FONT_ROOT
REGULAR_FONT_PATH = GILL_SANS_DIR / "GillSans.ttc"
SEMIBOLD_FONT_PATH = GILL_SANS_DIR / "GillSans-SemiBold.ttf"

REGULAR_PROP: FontProperties | None = None
SEMIBOLD_PROP: FontProperties | None = None

Q_VALUES = [1, 2, 4, 6, 8]
Q_POSITIONS = list(range(len(Q_VALUES)))
CTA_UTILIZATION = [42.76, 81.88, 90.69, 95.00, 95.00]
MISSING_MARK_Y = {
    "0.96": 4500,
    "0.98": 8500,
}


@dataclass(frozen=True)
class RecallSeries:
    label: str
    qps: list[float | None]
    color: str
    marker: str


SERIES = [
    RecallSeries(
        "Recall@10=0.90",
        [58803.31, 80204.87, 92716.63, 89841.90, 70600.18],
        "#d95f02",
        "s",
    ),
    RecallSeries(
        "Recall@10=0.92",
        [51479.12, 70641.60, 75881.63, 63517.02, 59402.58],
        "#1f78b4",
        "^",
    ),
    RecallSeries(
        "Recall@10=0.94",
        [39633.64, 57805.21, 59088.07, 51135.83, 47736.10],
        "#33a02c",
        "D",
    ),
    RecallSeries(
        "Recall@10=0.96",
        [30674.68, 44834.81, 35450.38, None, None],
        "#6a3d9a",
        "v",
    ),
]


def configure_fonts() -> None:
    global REGULAR_PROP, SEMIBOLD_PROP

    for font_path in (REGULAR_FONT_PATH, SEMIBOLD_FONT_PATH):
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))

    if REGULAR_FONT_PATH.exists() and SEMIBOLD_FONT_PATH.exists():
        regular_name = font_manager.FontProperties(fname=str(REGULAR_FONT_PATH)).get_name()
        REGULAR_PROP = FontProperties(fname=str(REGULAR_FONT_PATH), size=9)
        SEMIBOLD_PROP = FontProperties(fname=str(SEMIBOLD_FONT_PATH), size=9)
        sans_serif = [regular_name, "DejaVu Sans"]
    else:
        regular_name = "DejaVu Sans"
        REGULAR_PROP = FontProperties(family=regular_name, size=9)
        SEMIBOLD_PROP = FontProperties(family=regular_name, weight="semibold", size=9)
        sans_serif = [regular_name]

    plt.rcParams.update(
        {
            "font.family": regular_name,
            "font.sans-serif": sans_serif,
            "font.weight": "regular",
            "axes.labelweight": "regular",
            "axes.titleweight": "regular",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
            "hatch.linewidth": 0.35,
        }
    )


def apply_axis_fonts(ax: plt.Axes) -> None:
    if REGULAR_PROP is None:
        return
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(REGULAR_PROP)


def contiguous_segments(points: list[tuple[int, int, float | None]]) -> list[list[tuple[int, float]]]:
    segments: list[list[tuple[int, float]]] = []
    current: list[tuple[int, float]] = []
    for position, _, qps in points:
        if qps is None:
            if current:
                segments.append(current)
                current = []
            continue
        current.append((position, qps))
    if current:
        segments.append(current)
    return segments


def plot_series(ax: plt.Axes, series: RecallSeries) -> None:
    points = list(zip(Q_POSITIONS, Q_VALUES, series.qps))
    first_segment = True

    for segment in contiguous_segments(points):
        xs = [q_value for q_value, _ in segment]
        ys = [qps for _, qps in segment]
        ax.plot(
            xs,
            ys,
            label=series.label.split("=")[-1] if first_segment else None,
            color=series.color,
            marker=series.marker,
            linewidth=1.35,
            markersize=3.4,
        )
        first_segment = False

    missing = [position for position, _, qps in points if qps is None]
    if missing:
        recall = series.label.split("=")[-1]
        y = MISSING_MARK_Y.get(recall, 3500)
        ax.scatter(
            missing,
            [y] * len(missing),
            marker="x",
            s=22,
            color=series.color,
            linewidths=1.0,
            zorder=4,
        )


def draw_cta_utilization(ax: plt.Axes) -> None:
    x = np.arange(len(Q_VALUES))
    ax.bar(
        x,
        CTA_UTILIZATION,
        width=0.62,
        color="#fed9a6",
        edgecolor="black",
        linewidth=0.8,
        hatch="//",
    )
    title = ax.set_title(
        "(b)",
        loc="left",
        color="#8f3333",
        fontweight="semibold",
        y=0.84,
        pad=0,
    )
    title.set_zorder(20)
    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in Q_VALUES])
    ax.set_xlabel("Q", labelpad=0)
    ax.set_ylabel("Utilization", rotation=270, labelpad=14)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}%"))
    ax.grid(True, axis="y", linestyle=(0, (1, 7)), linewidth=0.7, color="black", alpha=0.75)
    apply_axis_fonts(ax)


def draw_qps_sensitivity(ax: plt.Axes) -> None:
    for series in SERIES:
        plot_series(ax, series)

    ax.set_xlim(-0.25, len(Q_VALUES) - 0.75)
    ax.set_ylim(0, 120000)
    ax.set_yticks([0, 40000, 80000, 120000])
    ax.set_xticks(Q_POSITIONS)
    ax.set_xticklabels([str(q) for q in Q_VALUES])
    ax.set_xlabel("Q", labelpad=0)
    ax.set_ylabel("Throughput", labelpad=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}K"))
    ax.grid(True, which="major", axis="both", linestyle=(0, (1, 7)), linewidth=0.7, color="black", alpha=0.75)
    ax.tick_params(length=3.0, width=0.8, pad=1)
    apply_axis_fonts(ax)

    title = ax.set_title(
        "(a)",
        loc="left",
        color="#8f3333",
        fontweight="semibold",
        y=0.84,
        pad=0,
    )
    title.set_zorder(20)

    handles, labels = ax.get_legend_handles_labels()
    blank = Line2D([], [], linestyle="none", marker=None, color="none")
    handles = [blank] + handles
    labels = ["Recall@10="] + labels
    legend_prop = FontProperties(fname=str(REGULAR_FONT_PATH), size=9) if REGULAR_FONT_PATH.exists() else FontProperties(size=9)
    legend = ax.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.54, 1.01),
        ncol=5,
        frameon=False,
        borderpad=0.0,
        handlelength=0.45,
        handletextpad=0.12,
        columnspacing=0.25,
        labelspacing=0.0,
        markerscale=0.65,
        prop=legend_prop,
    )
    handles = getattr(legend, "legend_handles", None)
    if handles is None:
        handles = legend.legendHandles
    handles[0].set_visible(False)


def save_plot() -> None:
    configure_fonts()

    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.4), gridspec_kw={"width_ratios": [7, 3]})
    fig.subplots_adjust(left=0.14, right=0.80, bottom=0.24, top=0.78, wspace=0.32)

    draw_qps_sensitivity(axes[0])
    draw_cta_utilization(axes[1])

    for ax in axes:
        ax.tick_params(axis="both", length=3.0, width=0.8, pad=1)
        ax.spines["top"].set_linewidth(0.8)
        ax.spines["right"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)
        ax.spines["left"].set_linewidth(0.8)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF)
    plt.close(fig)
    print(f"saved: {OUTPUT_PDF}")


def main() -> None:
    save_plot()


if __name__ == "__main__":
    main()
