#!/usr/bin/env python3
"""Plot GPipeANN and FusionANNS Pareto frontiers."""

from __future__ import annotations

from pathlib import Path
import sys
BUNDLE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE_ROOT / "scripts"))
from figure_paths import font_dir, output_path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from better_annotation import MUTED_DARK_RED, draw_better_annotation

FUSION_BETTER_ANNOTATION = {
    "arrow_head": (0.42, 0.51),
    "arrow_tail": (0.58, 0.27),
    "label": (0.56, 0.52),
}


GILL_SANS_DIR = font_dir()
OUTPUT_PDF = output_path("fig07-fusion")
DATASETS = [
    {
        "key": "sift1b",
        "title": "SIFT1B",
    },
    {
        "key": "deep1b",
        "title": "DEEP1B",
    },
]
SERIES = [
    ("GPipeANN(ours)", "gpipeann", "#1f77b4", "o"),
    ("FusionANNS", "fusion", "#9467bd", "D"),
]
PARETO_DATA = {
    "sift1b": {
        "gpipeann": [
            (4.188, 27305.31),
            (6.817, 33612.82),
            (9.868, 35824.91),
            (10.652, 36290.46),
            (12.663, 37025.36),

        ],
        "fusion": [
            (12.7004, 100.723),
            (12.8611, 197.96),
            (13.0055, 389.704),
            (13.1677, 765.037),
            (13.4897, 1486.15),
            (13.8264, 2177.0),
            (14.1541, 2833.03),
            (14.8621, 4051.73),
            (15.6981, 5133.98),
            (17.7043, 6881.98),
            (20.2874, 8039.43),
            (26.9709, 9192.62),
            (36.0421, 9522.11),
            (77.3726, 9560.47),
        ],
    },
    "deep1b": {
        "gpipeann": [
            (6.337, 17905.65),
            (11.036, 21944.11),
            (13.73, 23801.88),
            (18.269, 24455.97),

        ],
        "fusion": [
            (13.7539, 83.6467),
            (13.8126, 165.257),
            (13.9683, 325.474),
            (14.1295, 638.387),
            (14.5175, 1239.73),
            (14.8859, 1813.93),
            (15.2788, 2361.59),
            (16.135, 3375.22),
            (17.1342, 4276.18),
            (19.8973, 5740.08),
            (24.6752, 6597.08),
            (39.1917, 7022.94),
            (55.015, 7113.16),
        ],
    },
}


def configure_fonts() -> None:
    """Use the bundled Gill Sans fonts when available."""
    for font_path in sorted(GILL_SANS_DIR.glob("*")):
        if font_path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
            font_manager.fontManager.addfont(str(font_path))

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Gill Sans", "Gill Sans MT", "Arial", "DejaVu Sans"],
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


def format_k(value: float, _: int) -> str:
    if value == 0:
        return "0"
    return f"{value / 1000:g}K"


def draw_panel(ax: plt.Axes, dataset: dict[str, object]) -> None:
    dataset_key = str(dataset["key"])
    points_by_series = PARETO_DATA[dataset_key]

    for label, key, color, marker in SERIES:
        points = points_by_series[key]
        ax.plot(
            [latency for latency, _ in points],
            [throughput for _, throughput in points],
            label=label,
            color=color,
            marker=marker,
            linewidth=1.35,
            markersize=3.0,
        )

    ax.text(
        0.97,
        0.95,
        str(dataset["title"]),
        transform=ax.transAxes,
        ha="right",
        va="top",
        color=MUTED_DARK_RED,
        fontweight="semibold",
    )
    draw_better_annotation(ax, annotation=FUSION_BETTER_ANNOTATION)
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(0, 40_000)
    ax.set_yticks([20_000, 40_000])
    ax.yaxis.set_major_formatter(FuncFormatter(format_k))
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.8, pad=1)


def plot() -> None:
    configure_fonts()
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.2), sharey=False)
    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.28, top=0.76, wspace=0.32)

    for ax, dataset in zip(axes, DATASETS):
        draw_panel(ax, dataset)

    axes[0].set_ylabel("Throughput", labelpad=8)
    fig.text(0.57, 0.12, "P99 Latency (ms)", ha="center", va="center")

    handles, labels = axes[0].get_legend_handles_labels()
    legend_order = [1, 0]
    fig.legend(
        [handles[index] for index in legend_order],
        [labels[index] for index in legend_order],
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.58, 1.01),
        handlelength=1.3,
        handletextpad=0.35,
        columnspacing=0.9,
        borderpad=0.1,
    )

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF)
    plt.close(fig)
    print(f"saved: {OUTPUT_PDF}")


if __name__ == "__main__":
    plot()
