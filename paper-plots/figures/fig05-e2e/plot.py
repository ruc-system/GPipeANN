#!/usr/bin/env python3
"""Combined SIFT1B and DEEP1B pareto figure with one QPS label per recall group."""

from dataclasses import dataclass
from pathlib import Path
import sys
BUNDLE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE_ROOT / "scripts"))
from figure_paths import font_dir, output_path
import os

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from better_annotation import MUTED_DARK_RED, draw_better_annotation

Y_AXIS = {
    ("sift1b", "0.90"): {"max": 139_000, "ticks": [0, 50_000, 100_000, 139_000]},
    ("sift1b", "0.95"): {"max": 80_000, "ticks": [0, 20_000, 40_000, 60_000, 80_000]},
    ("deep1b", "0.90"): {"max": 100_000, "ticks": [0, 25_000, 50_000, 75_000, 100_000]},
    ("deep1b", "0.95"): {"max": 40_000, "ticks": [0, 10_000, 20_000, 30_000, 40_000]},
}

DATA = {
    "sift1b": {
        45: {
            "avg": {
                "flashanns": [(4.052, 26647.76), (4.942, 43698.99), (6.362, 50869.46), (7.346, 58803.31), (8.288, 65042.49), (9.686, 66824.03), (10.74, 70274.17), (13.595, 71415.82)],
                "gustann": [(15.606, 40872.69), (17.38, 49204.5), (19.213, 62879.24), (24.008, 76897.61), (30.574, 83117.43), (58.434, 86800.66), (98.584, 101530.68)],
                "quiver": [(2.602, 41313.66), (3.088, 67366.17), (3.984, 77808.23), (5.26, 81680.19), (7.289, 88400.72), (9.262, 92716.63), (10.822, 99085.98), (16.619, 103288.34)],
            },
            "p99": {
                "flashanns": [(4.957, 26647.76), (5.737, 43698.99), (7.029, 50869.46), (9.41, 58803.31), (10.424, 65042.49), (10.551, 66824.03), (12.26, 70274.17), (14.452, 71415.82)],
                "gustann": [(20.392, 40872.69), (21.842, 49204.5), (24.088, 62879.24), (29.223, 76897.61), (37.215, 83117.43), (69.693, 86800.66), (115.58, 101530.68)],
                "quiver": [(3.265, 67366.17), (5.561, 81680.19), (8.235, 88400.72), (9.603, 92716.63), (11.53, 99085.98), (17.944, 103288.34)],
            },
        },
        80: {
            "avg": {
                "flashanns": [(5.66, 19079.4), (7.041, 30674.68), (9.038, 35805.43), (11.072, 39015.17), (12.936, 41672.23), (14.293, 45285.62)],
                "gustann": [(22.786, 27973.44), (25.976, 36821.21), (30.067, 42389.49), (39.774, 45437.0), (72.625, 52456.17), (90.777, 55669.27), (151.136, 60362.87), (313.288, 62242.84), (627.955, 62619.6)],
                "quiver": [(4.212, 25509.81), (5.008, 42136.67), (6.966, 44834.81), (8.654, 49731.74), (12.19, 52965.68), (15.212, 56575.07), (21.715, 59436.92), (25.273, 59519.58), (27.888, 61732.77)],
            },
            "p99": {
                "flashanns": [(6.705, 19079.4), (8.187, 30674.68), (10.165, 35805.43), (13.731, 39015.17), (15.941, 41672.23), (17.424, 45285.62)],
                "gustann": [(27.6, 27973.44), (31.473, 36821.21), (34.524, 42389.49), (45.453, 45437.0), (82.516, 52456.17), (108.616, 55669.27), (183.409, 60362.87), (373.701, 62242.84), (724.906, 62619.6)],
                "quiver": [(4.388, 25509.81), (5.671, 42136.67), (7.518, 44834.81), (9.224, 49731.74), (13.17, 52965.68), (15.867, 56575.07), (23.602, 59436.92), (26.734, 59519.58), (31.492, 61732.77)],
            },
        },
    },
    "deep1b": {
        70: {
            "avg": {
                "flashanns": [(5.707, 18922.68), (7.289, 29629.97), (9.437, 34292.78), (11.367, 38001.21), (13.081, 41209.93), (20.817, 41412.12), (22.435, 43275.66)],
                "gustann": [(21.119, 30220.48), (25.304, 37658.67), (29.884, 42567.45), (50.998, 49896.35), (69.044, 54597.78), (86.751, 57910.08), (117.543, 64451.45)],
                "quiver": [(3.896, 27595.57), (4.895, 43198.46), (6.593, 47143.5), (8.584, 50233.59), (11.621, 55638.39), (17.171, 56490.11), (22.337, 57862.05), (28.69, 60026.47), (38.473, 67091.53)],
            },
            "p99": {
                "flashanns": [(6.91, 18922.68), (8.332, 29629.97), (10.791, 34292.78), (13.14, 38001.21), (13.971, 41209.93), (24.354, 41412.12), (24.483, 43275.66)],
                "gustann": [(25.784, 30220.48), (30.123, 37658.67), (35.26, 42567.45), (60.139, 49896.35), (81.693, 54597.78), (104.163, 57910.08), (143.546, 64451.45)],
                "quiver": [(4.731, 27595.57), (5.892, 43198.46), (8.083, 47143.5), (10.104, 50233.59), (12.647, 54134.26), (14.461, 55638.39), (18.871, 56490.11), (24.36, 57766.14), (25.538, 57862.05), (31.314, 60026.47), (39.753, 67091.53)],
            },
        },
        145: {
            "avg": {
                "flashanns": [(9.544, 11314.54), (12.313, 17540.49), (16.748, 19323.62), (20.722, 20845.43), (25.744, 20940.18), (27.816, 23269.22)],
                "gustann": [(40.047, 15950.67), (49.88, 19089.69), (58.242, 20636.91), (79.828, 23962.69), (178.234, 28485.49), (241.555, 31430.58)],
                "quiver": [(7.637, 14081.87), (10.14, 20713.13), (13.13, 23832.33), (16.225, 25153.43), (23.882, 27094.01), (29.733, 29015.0)],
            },
            "p99": {
                "flashanns": [(11.992, 11314.54), (14.65, 17540.49), (18.874, 19323.62), (23.478, 20845.43), (28.898, 20940.18), (29.716, 23269.22)],
                "gustann": [(45.656, 15950.67), (60.459, 19089.69), (66.153, 20636.91), (92.2, 23962.69), (228.076, 28485.49), (302.174, 31430.58)],
                "quiver": [(9.228, 14081.87), (12.221, 20713.13), (13.802, 23832.33), (16.41, 25153.43), (25.276, 26830.82), (28.548, 27094.01), (31.837, 29015.0), (62.613, 29772.13)],
            },
        },
    },
}

GILL_SANS_DIR = font_dir()
REGULAR_FONT_PATH = GILL_SANS_DIR / "GillSans.ttc"
SEMIBOLD_FONT_PATH = GILL_SANS_DIR / "GillSans-SemiBold.ttf"
REGULAR_PROP: FontProperties | None = None
SEMIBOLD_PROP: FontProperties | None = None
SERIES = [
    ("flashanns", "FlashANNS", "#ff7f0e", "s"),
    ("gustann", "GustANN", "#2ca02c", "^"),
    ("quiver", "GPipeANN(ours)", "#1f77b4", "o"),
]


@dataclass(frozen=True)
class Panel:
    dataset_key: str
    dataset_label: str
    ef: int
    display_recall: str
    latency_key: str

    @property
    def data(self):
        return DATA[self.dataset_key][self.ef]


PANEL_ROWS = [
    [
        Panel("sift1b", "SIFT1B", 45, "0.90", "p99"),
        Panel("sift1b", "SIFT1B", 45, "0.90", "avg"),
        Panel("sift1b", "SIFT1B", 80, "0.95", "p99"),
        Panel("sift1b", "SIFT1B", 80, "0.95", "avg"),
    ],
    [
        Panel("deep1b", "DEEP1B", 70, "0.90", "p99"),
        Panel("deep1b", "DEEP1B", 70, "0.90", "avg"),
        Panel("deep1b", "DEEP1B", 145, "0.95", "p99"),
        Panel("deep1b", "DEEP1B", 145, "0.95", "avg"),
    ],
]

QPS_LABEL_GROUPS = [
    {"columns": (0, 1, 2, 3), "recall": "all"},
]


def configure_fonts() -> None:
    global REGULAR_PROP, SEMIBOLD_PROP

    for font_path in (REGULAR_FONT_PATH, SEMIBOLD_FONT_PATH):
        if font_path.exists():
            font_manager.fontManager.addfont(font_path)

    regular_name = font_manager.FontProperties(fname=str(REGULAR_FONT_PATH)).get_name()
    semibold_name = font_manager.FontProperties(fname=str(SEMIBOLD_FONT_PATH)).get_name()
    REGULAR_PROP = FontProperties(fname=str(REGULAR_FONT_PATH), size=9)
    SEMIBOLD_PROP = FontProperties(fname=str(SEMIBOLD_FONT_PATH), size=9)

    plt.rcParams.update({
        "font.family": regular_name,
        "font.sans-serif": [regular_name],
        "font.weight": "regular",
        "axes.labelweight": "regular",
        "axes.titleweight": "regular",
        "axes.labelsize": 9,
        "font.size": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def apply_axis_fonts(ax) -> None:
    if REGULAR_PROP is None:
        return
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(REGULAR_PROP)


def panel_label(panel: Panel) -> str:
    return f"{panel.dataset_label}, Recall={panel.display_recall}"


def y_axis_max(panel: Panel) -> int:
    return Y_AXIS[(panel.dataset_key, panel.display_recall)]["max"]


def y_axis_ticks(panel: Panel) -> list[int]:
    return Y_AXIS[(panel.dataset_key, panel.display_recall)]["ticks"]


def format_y_tick(panel: Panel, value: float) -> str:
    if panel.dataset_key == "sift1b" and value == y_axis_max(panel):
        return ""
    return f"{value/1000:g}K" if value > 0 else "0"


def plot_line(ax, points, label, color, marker):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    ax.plot(x, y, label=label, color=color, marker=marker, linewidth=1.35, markersize=3.1)


def should_show_y_ticks(col: int) -> bool:
    return col in {0, 1, 2, 3}


def plot_panel(ax, panel: Panel, col: int) -> None:
    for key, label, color, marker in SERIES:
        plot_line(ax, panel.data[panel.latency_key][key], label, color, marker)

    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(length=2.5, pad=1)
    ax.set_ylim(0, y_axis_max(panel))
    ax.set_yticks(y_axis_ticks(panel))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: format_y_tick(panel, v)))
    ax.set_xlabel("")
    ax.set_ylabel("")
    if not should_show_y_ticks(col):
        ax.tick_params(axis="y", labelleft=False)
    apply_axis_fonts(ax)

    ax.text(
        0.03,
        0.95,
        panel_label(panel),
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=MUTED_DARK_RED,
        fontproperties=SEMIBOLD_PROP,
    )
    draw_better_annotation(ax, fontproperties=SEMIBOLD_PROP)


def qps_label_x(axes, group) -> float:
    left_col = group["columns"][0]
    return axes[0, left_col].get_position().x0 - 0.055


def create_figure_axes():
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 2.3531), sharey=False)
    fig.subplots_adjust(left=0.082, right=0.970, bottom=0.164, top=0.855, wspace=0.30, hspace=0.57)
    return fig, axes


def main() -> None:
    configure_fonts()
    fig, axes = create_figure_axes()

    for row, panel_row in enumerate(PANEL_ROWS):
        for col, panel in enumerate(panel_row):
            plot_panel(axes[row, col], panel, col)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    legend = fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.01),
        handlelength=1.3,
        handletextpad=0.4,
        columnspacing=1.0,
    )
    if REGULAR_PROP is not None:
        for text in legend.get_texts():
            text.set_fontproperties(REGULAR_PROP)

    top_row_bottom = axes[0, 0].get_position().y0
    bottom_row_bottom = axes[1, 0].get_position().y0
    col_centers = [axes[0, col].get_position().x0 + axes[0, col].get_position().width / 2 for col in range(4)]
    column_labels = ["P99 Latency (ms)", "AVG Latency (ms)", "P99 Latency (ms)", "AVG Latency (ms)"]

    for center, label in zip(col_centers, column_labels):
        fig.text(center, top_row_bottom - 0.0985, label, ha="center", va="center", fontproperties=REGULAR_PROP)
        fig.text(center, bottom_row_bottom - 0.0995, label, ha="center", va="center", fontproperties=REGULAR_PROP)

    for group in QPS_LABEL_GROUPS:
        fig.text(
            qps_label_x(axes, group),
            0.5,
            "Throughput",
            ha="center",
            va="center",
            rotation=90,
            fontproperties=REGULAR_PROP,
        )

    pdf_out = output_path("fig05-e2e")
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_out)
    plt.close(fig)
    print(f"saved: {pdf_out}")


if __name__ == "__main__":
    main()
