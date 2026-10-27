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

PARETO_DATA: dict[int, dict[str, list[tuple[float, float]]]] = {
    40: {
        "Baseline": [(3.587, 64675.02), (7.375, 80388.27), (8.772, 82876.13), (42.919, 83596.1)],
        "FlashANNS": [(4.9, 28164.02), (5.654, 46517.11), (6.718, 55512.19), (8.476, 63099.3), (8.66, 68529.5), (10.111, 75182.57), (13.36, 75249.84), (16.702, 78543.58)],
        "Quiver": [(2.464, 45928.12), (2.886, 74331.01), (3.851, 82724.62), (5.24, 87992.03), (7.465, 98590.07), (10.13, 99234.61), (10.844, 106650.0), (11.605, 107627.75), (13.662, 108110.33), (15.205, 108716.62), (15.264, 108985.65), (17.407, 110283.13), (18.849, 112284.41), (20.833, 113609.85), (25.183, 115919.19), (28.382, 117380.4), (35.503, 118175.52), (40.167, 118701.97)],
    },
    45: {
        "Baseline": [(6.101, 73771.83), (15.875, 74868.96), (17.818, 75984.09), (53.886, 76556.83)],
        "FlashANNS": [(4.957, 26647.76), (5.737, 43698.99), (7.029, 50869.46), (9.41, 58803.31), (10.424, 65042.49), (10.551, 66824.03), (12.26, 70274.17), (14.452, 71415.82)],
        "Quiver": [(3.317, 67366.17), (5.591, 81680.19), (8.177, 89841.9), (9.783, 92716.63), (11.752, 99085.98), (20.689, 101398.86), (20.799, 103288.34), (38.231, 104152.82), (42.353, 106109.52), (47.548, 107463.28)],
    },
    55: {
        "Baseline": [(4.654, 49580.7), (7.783, 61087.22), (11.414, 63542.23), (29.389, 65135.93)],
        "FlashANNS": [(5.317, 24044.89), (6.178, 39210.24), (7.861, 44881.14), (9.825, 51479.12), (10.063, 57147.04), (11.47, 59578.11), (13.198, 61342.84)],
        "Quiver": [(3.198, 35280.08), (3.809, 56632.76), (5.009, 63991.95), (7.292, 70369.71), (9.734, 75881.63), (11.736, 80235.6), (13.045, 81429.78), (13.435, 82665.87), (17.265, 83931.38), (27.495, 87608.87), (34.974, 90164.42), (51.522, 92003.6)],
    },
    65: {
        "Baseline": [(9.181, 52977.83), (15.143, 53942.82), (26.334, 54569.1), (37.748, 54635.43)],
        "FlashANNS": [(5.743, 21693.57), (6.831, 35286.58), (8.815, 39633.64), (10.802, 47007.4), (12.805, 52664.47)],
        "Quiver": [(3.858, 29804.66), (5.631, 45845.91), (6.576, 51135.83), (6.783, 53462.51), (7.35, 57805.21), (8.684, 59088.07), (10.746, 66920.79), (13.329, 69818.8), (19.928, 71055.81), (23.739, 72929.17), (31.719, 76251.1), (32.596, 76718.24), (49.271, 77114.35)],
    },
    80: {
        "Baseline": [(6.585, 35669.08), (12.294, 42705.84), (14.631, 43344.85), (17.518, 45239.74), (68.516, 45609.19)],
        "FlashANNS": [(6.705, 19079.4), (8.187, 30674.68), (10.165, 35805.43), (13.731, 39015.17), (15.941, 41672.23), (17.424, 45285.62)],
        "Quiver": [(4.391, 25509.81), (5.744, 42136.67), (8.936, 44834.81), (10.327, 49731.74), (13.254, 52965.68), (16.382, 56575.07), (19.438, 56995.06), (23.65, 59436.92), (27.059, 59519.58), (31.708, 61972.42), (38.289, 64078.94)],
    },
    120: {
        "Baseline": [(12.126, 23293.84), (18.297, 28826.47), (25.844, 30921.91)],
        "FlashANNS": [(8.633, 14109.73), (11.879, 22757.26), (15.974, 24826.36), (17.839, 28644.41), (20.169, 30838.38), (23.314, 31217.07), (23.83, 33031.43)],
        "Quiver": [(8.516, 27757.88), (10.574, 30699.69), (13.93, 31040.71), (20.153, 32776.29), (20.259, 36325.72), (29.564, 37928.69), (35.934, 37940.8), (38.692, 38968.6), (40.024, 40738.69), (59.51, 41620.6), (81.863, 41637.9), (113.083, 42215.36), (122.135, 44204.7)],
    },
}

STACKED_BREAKDOWN = {
    "GustANN": {
        "Compute": 19.0,
        "Launch": 2.0,
        "H2D": 1.0,
        "D2H": 1.0,
    },
    "FlashANNS": {
        "Compute": 23.0,
        "Launch": 0.0,
        "H2D": 1.0,
        "D2H": 1.0,
    },
    "+S": {
        "Compute": 11.0,
        "Launch": 0.0,
        "H2D": 0.107 / 9.5 * 100.0,
        "D2H": 0.107 / 9.5 * 100.0,
    },
    "+S+C": {
        "Compute": 20.0,
        "Launch": 0.0,
        "H2D": 0.107 / 5.3 * 100.0,
        "D2H": 0.107 / 5.3 * 100.0,
    },
}
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


def qps_at_latency_target(points: list[tuple[float, float]]) -> float:
    candidates = [qps for latency, qps in points if latency < LATENCY_TARGET_MS]
    if candidates:
        return max(candidates)
    return min(points, key=lambda point: point[0])[1]


def draw_grouped_bars(ax: plt.Axes) -> None:
    ef_values = list(RECALLS)
    x = np.arange(len(ef_values))
    width = 0.23

    for idx, (label, source_label, color, hatch) in enumerate(GROUPED_SERIES):
        values = [
            qps_at_latency_target(PARETO_DATA[ef][source_label]) / 1000.0
            for ef in ef_values
        ]
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


def latency_component_values(labels: list[str], component: str) -> np.ndarray:
    if component == "IO":
        return np.array([
            STACKED_LATENCY_MS[label] *
            (100.0 - sum(STACKED_BREAKDOWN[label].values())) / 100.0
            for label in labels
        ])
    return np.array([
        STACKED_LATENCY_MS[label] *
        STACKED_BREAKDOWN[label][component] / 100.0
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
    labels = list(STACKED_BREAKDOWN)
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
