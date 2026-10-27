#!/usr/bin/env python3
"""Plot the StaticDispatch vs Quiver static dispatch ablation.

Experiment setup:
- GPU: NVIDIA A30, 56 SMs, CUDA_VISIBLE_DEVICES=1
- Backend: SPDK
- Workload: topk=10, ef_search=30, repeat=20, data_type=uint8
- Runtime: pipe_width=1, queries_per_block=2
- I/O polling: poll_threads=6, poll_submit_batch_size=256
- Sweep: num_blocks = 56, 112, 168, 224, 280, 336, 392, 448, 504, 560
- Metric: x-axis is average query latency in ms on a log scale; y-axis is QPS

The data below is hard-coded from the terminal runs of:
- ./scripts/strawmen_static_dispatch.sh
- ./scripts/quiver_search.sh
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


OUTPUTS = [
    OUTPUT_ROOT / "latency_qps_comparison.pdf",
]
GILL_SANS_DIR = FONT_ROOT

STATIC_DISPATCH = [
    (2.302, 48295.09),
    (3.023, 73512.44),
    (4.014, 83041.00),
    (5.072, 87546.48),
    (6.023, 92165.81),
    (6.944, 95940.83),
    (7.860, 98789.78),
    (9.035, 98275.18),
    (9.880, 100948.46),
    (11.813, 93851.50),
]

QUIVER = [
    (1.978, 56517.29),
    (2.499, 89449.60),
    (3.130, 107134.12),
    (4.005, 111603.16),
    (4.632, 120635.78),
    (5.396, 124256.16),
    (6.206, 126029.42),
    (7.068, 126461.26),
    (8.526, 117873.58),
    (8.509, 131196.92),
]


def configure_fonts() -> None:
    """Use the paper's bundled Gill Sans fonts for this figure."""
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


def plot() -> None:
    configure_fonts()

    fig, ax = plt.subplots(figsize=(3.5, 1.4))
    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.30, top=0.96)

    plot_line(ax, STATIC_DISPATCH, "StaticDispatch", "#7f7f7f", "o")
    plot_line(ax, QUIVER, "Quiver", "#1f77b4", "s")

    ax.set_xscale("log")
    ax.set_xlabel("Avg latency (ms)", labelpad=1)
    ax.set_ylabel("QPS", labelpad=1)
    ax.set_xlim(1.8, 12.8)
    ax.set_ylim(40000, 140000)
    ax.set_xticks([2, 3, 4, 6, 8, 10, 12])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks([50000, 90000, 130000])
    ax.set_yticklabels(["50K", "90K", "130K"])
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.6, pad=1)
    ax.legend(
        frameon=False,
        loc="lower right",
        handlelength=1.6,
        borderpad=0.1,
        labelspacing=0.25,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output)
        print(output)
    plt.close(fig)


if __name__ == "__main__":
    plot()
