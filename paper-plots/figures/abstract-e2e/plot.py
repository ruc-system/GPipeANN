#!/usr/bin/env python3
"""Compact SIFT1B and DEEP1B P99 latency pareto figure."""

from __future__ import annotations

from pathlib import Path
import sys
BUNDLE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE_ROOT / "scripts"))
from figure_paths import font_dir, output_path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from better_annotation import MUTED_DARK_RED, draw_better_annotation

FUSION_BETTER_ANNOTATION = {
    "arrow_head": (0.58, 0.35),
    "arrow_tail": (0.74, 0.11),
    "label": (0.72, 0.36),
}

Y_AXIS = {
    "sift1b": {"max": 139_000, "ticks": [0, 50_000, 100_000, 139_000]},
    "deep1b": {"max": 100_000, "ticks": [50_000, 100_000]},
}

DATA = {
    "sift1b": {
        "flashanns": [
            (4.957, 26647.76),
            (5.737, 43698.99),
            (7.029, 50869.46),
            (9.41, 58803.31),
            (10.424, 65042.49),
            (10.551, 66824.03),
            (12.26, 70274.17),
            (14.452, 71415.82),
        ],
        "gustann": [
            (20.392, 40872.69),
            (21.842, 49204.5),
            (24.088, 62879.24),
            (29.223, 76897.61),
            (37.215, 83117.43),
            (69.693, 86800.66),
            (115.58, 101530.68),
        ],
        "quiver": [
            (3.265, 67366.17),
            (5.561, 81680.19),
            (8.235, 88400.72),
            (9.603, 92716.63),
            (11.53, 99085.98),
            (17.944, 103288.34),
        ],
    },
    "deep1b": {
        "flashanns": [
            (6.91, 18922.68),
            (8.332, 29629.97),
            (10.791, 34292.78),
            (13.14, 38001.21),
            (13.971, 41209.93),
            (24.354, 41412.12),
            (24.483, 43275.66),
        ],
        "gustann": [
            (25.784, 30220.48),
            (30.123, 37658.67),
            (35.26, 42567.45),
            (60.139, 49896.35),
            (81.693, 54597.78),
            (104.163, 57910.08),
            (143.546, 64451.45),
        ],
        "quiver": [
            (4.731, 27595.57),
            (5.892, 43198.46),
            (8.083, 47143.5),
            (10.104, 50233.59),
            (12.647, 54134.26),
            (14.461, 55638.39),
            (18.871, 56490.11),
            (24.36, 57766.14),
            (25.538, 57862.05),
            (31.314, 60026.47),
            (39.753, 67091.53),
        ],
    },
}

PANELS = [
    ("sift1b", "SIFT1B"),
    ("deep1b", "DEEP1B"),
]

SERIES = [
    ("flashanns", "FlashANNS", "#ff7f0e", "s"),
    ("gustann", "GustANN", "#2ca02c", "^"),
    ("quiver", "GPipeANN(ours)", "#1f77b4", "o"),
]

OUTPUT_PDF = output_path("abstract-e2e")
GILL_SANS_DIR = font_dir()
REGULAR_FONT_PATH = GILL_SANS_DIR / "GillSans.ttc"
SEMIBOLD_FONT_PATH = GILL_SANS_DIR / "GillSans-SemiBold.ttf"
REGULAR_PROP: FontProperties | None = None
SEMIBOLD_PROP: FontProperties | None = None


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
            "axes.titlesize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
        }
    )


def apply_axis_fonts(ax: plt.Axes) -> None:
    if REGULAR_PROP is None:
        return
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(REGULAR_PROP)


def format_y_tick(dataset_key: str, value: float) -> str:
    if dataset_key == "sift1b" and value == Y_AXIS[dataset_key]["max"]:
        return ""
    return f"{value / 1000:g}K" if value > 0 else "0"


def plot_line(ax: plt.Axes, points: list[tuple[float, float]], label: str, color: str, marker: str) -> None:
    ax.plot(
        [point[0] for point in points],
        [point[1] for point in points],
        label=label,
        color=color,
        marker=marker,
        linewidth=1.35,
        markersize=3.0,
    )


def draw_panel(ax: plt.Axes, dataset_key: str, title: str, *, show_ylabel: bool) -> None:
    points_by_series = DATA[dataset_key]
    y_axis = Y_AXIS[dataset_key]

    for key, label, color, marker in SERIES:
        plot_line(ax, points_by_series[key], label, color, marker)

    ax.text(
        0.97,
        0.95,
        title,
        transform=ax.transAxes,
        ha="right",
        va="top",
        color=MUTED_DARK_RED,
        fontproperties=SEMIBOLD_PROP,
    )
    draw_better_annotation(
        ax,
        annotation=FUSION_BETTER_ANNOTATION,
        fontproperties=SEMIBOLD_PROP,
    )
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(0, y_axis["max"])
    ax.set_yticks(y_axis["ticks"])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: format_y_tick(dataset_key, value)))
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.8, pad=1)
    if show_ylabel:
        ax.set_ylabel("Throughput", labelpad=2, fontproperties=REGULAR_PROP)
    apply_axis_fonts(ax)


def main() -> None:
    configure_fonts()
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.2), sharey=False)
    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.28, top=0.76, wspace=0.32)

    for ax, (dataset_key, title) in zip(axes, PANELS):
        draw_panel(ax, dataset_key, title, show_ylabel=dataset_key == "sift1b")

    fig.text(0.57, 0.08, "P99 Latency (ms)", ha="center", va="center", fontproperties=REGULAR_PROP)

    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.58, 1.01),
        handlelength=1.3,
        handletextpad=0.35,
        columnspacing=0.9,
        borderpad=0.1,
    )
    if REGULAR_PROP is not None:
        for text in legend.get_texts():
            text.set_fontproperties(REGULAR_PROP)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF)
    plt.close(fig)
    print(f"saved: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
