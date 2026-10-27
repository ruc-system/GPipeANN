#!/usr/bin/env python3
"""Plot the Quiver ablation summary."""

from __future__ import annotations

from pathlib import Path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import ConnectionPatch, Rectangle
from matplotlib.ticker import FuncFormatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures"))
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"
OUTPUT_PDF = OUTPUT_ROOT / "fig-evaluation" / "ablation.pdf"
GILL_SANS_DIR = FONT_ROOT
LATENCY_TARGET_MS = 10.0

RECALLS = {
    40: "0.88",
    45: "0.90",
    55: "0.92",
    65: "0.94",
    80: "0.96",
    120: "0.98",
}

# 移除PARETO_DATA变量，使用预计算的QPS值

# 移除STACKED_BREAKDOWN变量，使用预计算的延迟组件值
STACKED_LATENCY_MS = {
    "GustANN": 24.0,
    "FlashANNS": 10.7,
    "+S": 9.5,
    "+S+C": 5.3,
}

GROUPED_SERIES = [
    ("FlashANNS", "FlashANNS", "#fbb4ae", "\\\\\\"),
    ("+S", "Baseline", "#b3cde3", "//"),
    ("+S+C", "Quiver", "#ccebc5", "--"),
]
STACK_ORDER = ["H2D", "Launch", "D2H", "Compute", "IO"]
STACK_COLORS = {
    "Compute": "#fed9a6",
    "IO": "#ccebc5",
    "Launch": "#fbb4ae",
    "H2D": "#b3cde3",
    "D2H": "#decbe4",
}
STACK_LABELS = {
    "Compute": "Compute",
    "IO": "Resume",
    "Launch": "Launch",
    "H2D": "H2D",
    "D2H": "D2H",
}
STACK_HATCHES = {
    "H2D": "//",
    "Launch": "\\\\",
    "Compute": "--",
    "IO": "xx",
    "D2H": "..",
}
ZOOM_YMAX_MS = 2.0


def configure_fonts() -> None:
    """Use the paper's bundled Gill Sans fonts when available."""
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
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
            "hatch.linewidth": 0.35,
        }
    )


# 预计算好的QPS值（单位：K QPS）
PRE_COMPUTED_QPS = {
    "FlashANNS": [68.5295, 58.80331, 51.47912, 39.63364, 30.67468, 14.10973],
    "Baseline": [82.87613, 73.77183, 61.08722, 52.97783, 35.66908, 23.29384],
    "Quiver": [98.59007, 92.71663, 75.88163, 59.08807, 44.83481, 27.75788],
}


def draw_grouped_bars(ax: plt.Axes) -> None:
    ef_values = list(RECALLS)
    x = np.arange(len(ef_values))
    width = 0.23

    for idx, (label, source_label, color, hatch) in enumerate(GROUPED_SERIES):
        values = PRE_COMPUTED_QPS[source_label]
        ax.bar(
            x + (idx - 1) * width,
            values,
            width,
            label=label,
            color=color,
            edgecolor="black",
            linewidth=0.35,
            hatch=hatch,
        )

    title = ax.set_title(
        "(a) Throughput",
        loc="left",
        color="#8f3333",
        fontweight="semibold",
        y=0.84,
        pad=0,
    )
    title.set_zorder(20)
    ax.set_xlabel("Recall@10", labelpad=5)
    ax.set_ylabel("Throughput", labelpad=0)
    ax.set_xticks(x)
    ax.set_xticklabels([RECALLS[ef] for ef in ef_values], rotation=90)
    ax.set_ylim(0, 150)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}K"))
    ax.grid(True, axis="y", linestyle=(0, (1, 7)), linewidth=0.7, color="black", alpha=0.75)
    ax.legend(
        frameon=False,
        ncol=1,
        loc="upper right",
        bbox_to_anchor=(1.0, 0.92),
        handlelength=1.2,
        borderpad=0.1,
        labelspacing=0.15,
    )


# 预计算好的延迟组件值（单位：ms）
PRE_COMPUTED_LATENCY_COMPONENTS = {
    "GustANN": {
        "Compute": 4.56,
        "Launch": 0.48,
        "H2D": 0.24,
        "D2H": 0.24,
        "IO": 18.48,
    },
    "FlashANNS": {
        "Compute": 2.461,
        "Launch": 0.0,
        "H2D": 0.107,
        "D2H": 0.107,
        "IO": 8.025,
    },
    "+S": {
        "Compute": 1.045,
        "Launch": 0.0,
        "H2D": 0.107,
        "D2H": 0.107,
        "IO": 8.241,
    },
    "+S+C": {
        "Compute": 1.06,
        "Launch": 0.0,
        "H2D": 0.107,
        "D2H": 0.107,
        "IO": 4.026,
    },
}

def latency_component_values(labels: list[str], component: str) -> np.ndarray:
    return np.array([
        PRE_COMPUTED_LATENCY_COMPONENTS[label][component]
        for label in labels
    ])


def draw_latency_stack(
    ax: plt.Axes,
    labels: list[str],
    x: np.ndarray,
    width: float,
    show_legend_labels: bool,
) -> None:
    bottom = np.zeros(len(labels))

    for component in STACK_ORDER:
        values = latency_component_values(labels, component)
        ax.bar(
            x,
            values,
            0.55,
            bottom=bottom,
            label=STACK_LABELS[component] if show_legend_labels else "_nolegend_",
            color=STACK_COLORS[component],
            edgecolor="black",
            linewidth=0.8,
            hatch=STACK_HATCHES[component],
        )
        bottom += values


def draw_stacked_bars(ax: plt.Axes, fig: plt.Figure) -> None:
    labels = ["GustANN", "FlashANNS", "+S", "+S+C"]
    x = np.arange(len(labels))
    draw_latency_stack(ax, labels, x, 0.55, show_legend_labels=True)

    title = ax.set_title(
        "(b) Latency",
        loc="left",
        color="#8f3333",
        fontweight="semibold",
        y=0.84,
        pad=0,
    )
    title.set_zorder(20)
    ax.set_ylabel("Latency (ms)", labelpad=14, rotation=270)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, ha="center", va="top")
    ax.set_ylim(0, 28)
    ax.set_yticks([0, 7, 14, 21, 28])
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.grid(True, axis="y", linestyle=(0, (1, 7)), linewidth=0.7, color="black", alpha=0.75)
    ax.legend(
        frameon=False,
        ncol=1,
        loc="upper left",
        bbox_to_anchor=(1.65, 0.92),
        handlelength=0.9,
        borderpad=0.1,
        labelspacing=0.15,
    )

    zoom_rect = Rectangle(
        (-0.42, -0.1),
        len(labels) + 0.5,
        ZOOM_YMAX_MS + 0,
        fill=False,
        edgecolor="black",
        linewidth=0.8,
        zorder=5,
    )
    ax.add_patch(zoom_rect)

    zoom_ax = fig.add_axes([0.76, 0.05, 0.2, 0.3])
    draw_latency_stack(zoom_ax, labels, x, 0.55, show_legend_labels=False)
    zoom_ax.set_xlim(-0.5, len(labels) - 0.5)
    zoom_ax.set_ylim(0, ZOOM_YMAX_MS)
    zoom_ax.set_xticks([])
    zoom_ax.set_yticks([0, ZOOM_YMAX_MS])
    zoom_ax.tick_params(axis="both", length=2.2, width=0.8, pad=1)
    zoom_ax.yaxis.tick_right()
    zoom_ax.grid(True, axis="y", linestyle=(0, (1, 7)), linewidth=0.6, color="black", alpha=0.75)
    for spine in zoom_ax.spines.values():
        spine.set_linewidth(0.8)

    fig.add_artist(ConnectionPatch(
        xyA=(len(labels) - 0.5, ZOOM_YMAX_MS),
        coordsA=ax.transData,
        xyB=(-0.5, ZOOM_YMAX_MS),
        coordsB=zoom_ax.transData,
        color="black",
        linewidth=0.6,
    ))
    fig.add_artist(ConnectionPatch(
        xyA=(len(labels) - 0.5, 0.0),
        coordsA=ax.transData,
        xyB=(-0.5, 0.0),
        coordsB=zoom_ax.transData,
        color="black",
        linewidth=0.6,
    ))


def plot() -> None:
    configure_fonts()
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.6), gridspec_kw={"width_ratios": [7, 3]})
    fig.subplots_adjust(left=0.17, right=0.72, bottom=0.48, top=0.96, wspace=0.20)

    draw_grouped_bars(axes[0])
    draw_stacked_bars(axes[1], fig)

    for ax in axes:
        ax.tick_params(axis="both", length=3.0, width=0.8, pad=1)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF)
    plt.close(fig)
    print(f"saved: {OUTPUT_PDF}")


if __name__ == "__main__":
    plot()
