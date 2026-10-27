#!/usr/bin/env python3
"""Plot FlashANNS vs naive block multi-query latency/QPS.

Experiment setup:
- GPU: NVIDIA A30, 56 SMs, CUDA_VISIBLE_DEVICES=1
- Backend: SPDK
- Workload: SIFT-100M, topk=10, ef_search=30, data_type=uint8
- FlashANNS: pipe_width=2
- NaiveBlockMultiQuery: pipe_width=1, queries_per_block=2
- Sweep: num_blocks = 56, 112, 168, 224, 280, 336, 392, 448, 504, 560

The data below is hard-coded from terminal runs of:
- ./scripts/flashanns_search.sh
- QUERIES_PER_BLOCK=2 ./scripts/strawmen_naive_block_multi_query.sh
"""

from __future__ import annotations

from pathlib import Path
import os
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures")) / "historical"
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter


GILL_SANS_DIR = FONT_ROOT
OUTPUT = OUTPUT_ROOT / "flashanns_vs_naive_block_multi_query_latency_qps.pdf"

FLASHANNS = [
    (3.047, 18374.04),
    (3.706, 30217.78),
    (3.941, 42614.20),
    (4.482, 49971.89),
    (5.837, 47922.79),
    (5.757, 58286.15),
    (6.934, 56443.25),
    (7.707, 58050.92),
    (8.310, 60619.76),
    (7.906, 70662.34),
]

NAIVE_BLOCK_MULTI_QUERY = [
    (4.482, 24962.04),
    (7.357, 30418.63),
    (11.759, 28548.37),
    (16.405, 27283.04),
    (21.572, 25933.46),
    (24.912, 26878.51),
    (30.191, 25934.57),
    (32.957, 27145.24),
    (34.558, 29071.58),
    (37.677, 29667.44),
]


def configure_fonts() -> None:
    for font_path in sorted(GILL_SANS_DIR.glob("*")):
        if font_path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
            font_manager.fontManager.addfont(str(font_path))

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Gill Sans", "Gill Sans MT"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.6,
        }
    )


def plot_line(
    ax: plt.Axes,
    points: list[tuple[float, float]],
    label: str,
    color: str,
    marker: str,
) -> None:
    points = sorted(points)
    latencies = [latency for latency, _ in points]
    qps_values = [qps for _, qps in points]
    ax.plot(
        latencies,
        qps_values,
        label=label,
        color=color,
        marker=marker,
        markersize=3.0,
        linewidth=1.1,
    )


def main() -> None:
    configure_fonts()

    fig, ax = plt.subplots(figsize=(3.5, 1.4))
    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.31, top=0.96)

    plot_line(ax, FLASHANNS, "FlashANNS", "#ff7f0e", "s")
    plot_line(ax, NAIVE_BLOCK_MULTI_QUERY, "NaiveBlockMQ", "#9467bd", "o")

    ax.set_xscale("log")
    ax.set_xlabel("Avg latency (ms)", labelpad=1)
    ax.set_ylabel("QPS", labelpad=1)
    ax.set_xlim(2.8, 45)
    ax.set_ylim(15000, 76000)
    ax.set_xticks([3, 5, 10, 20, 40])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks([20000, 40000, 60000])
    ax.set_yticklabels(["20K", "40K", "60K"])
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.6, pad=1)
    ax.legend(
        frameon=False,
        loc="upper left",
        handlelength=1.4,
        borderpad=0.1,
        labelspacing=0.2,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT)
    print(OUTPUT)
    plt.close(fig)


if __name__ == "__main__":
    main()
