#!/usr/bin/env python3
"""Plot early-exit strawman and GPruning results.

Data is hard-coded from the A30 SIFT100M runs:
- Static strawmen: none, DARTH, GPruning
- Streaming Quiver: GPruning
- topk=10, ef_search=30, repeat=20, pipe_width=1, queries_per_block=1
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


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = FONT_ROOT
OUTPUT_DIR = OUTPUT_ROOT

STATIC_NONE = [
    (1.330, 41863.05),
    (1.638, 67883.52),
    (2.077, 80252.83),
    (3.251, 68452.20),
    (3.566, 77869.16),
    (3.838, 86786.27),
    (4.750, 81911.69),
    (5.279, 84206.42),
    (5.588, 89423.96),
    (6.416, 86616.57),
]

STATIC_DARTH = [
    (19.642, 2849.17),
    (19.930, 5612.74),
    (20.241, 8278.03),
    (20.586, 10848.35),
    (24.232, 11508.51),
    (38.084, 8793.21),
    (44.239, 8828.22),
    (46.200, 9658.39),
    (49.661, 10114.12),
    (50.504, 11037.40),
]

STATIC_GPRUNING = [
    (1.266, 43989.76),
    (1.568, 70893.10),
    (1.927, 86481.32),
    (2.814, 79012.84),
    (3.206, 86642.99),
    (3.435, 96736.40),
    (4.169, 93232.83),
    (4.705, 94313.25),
    (5.104, 97834.96),
    (5.713, 97142.03),
]

STREAMING_GPRUNING = [
    (0.999, 55814.72),
    (1.312, 84541.08),
    (1.630, 100985.52),
    (1.912, 109710.66),
    (2.355, 113732.66),
    (2.807, 115181.70),
    (3.408, 109120.27),
    (3.703, 113839.14),
    (4.006, 121299.61),
    (4.547, 115909.03),
]

AVG_STEPS = {
    "None": 31.84,
    "DARTH": 27.74,
    "GPruning": 28.44,
}


def configure_fonts() -> None:
    for font_path in sorted(FONT_DIR.glob("*")):
        if font_path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
            font_manager.fontManager.addfont(str(font_path))

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Gill Sans", "Gill Sans MT"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.6,
        }
    )


def plot_line(ax: plt.Axes, points: list[tuple[float, float]], label: str, color: str, marker: str) -> None:
    points = sorted(points)
    ax.plot(
        [latency for latency, _ in points],
        [qps for _, qps in points],
        label=label,
        color=color,
        marker=marker,
        markersize=3.0,
        linewidth=1.1,
    )


def plot_latency_qps() -> Path:
    fig, ax = plt.subplots(figsize=(3.5, 1.4))
    fig.subplots_adjust(left=0.15, right=0.99, bottom=0.30, top=0.96)

    plot_line(ax, STATIC_NONE, "Static none", "#4d4d4d", "o")
    plot_line(ax, STATIC_DARTH, "Static DARTH", "#d55e00", "^")
    plot_line(ax, STATIC_GPRUNING, "Static GPruning", "#0072b2", "s")
    plot_line(ax, STREAMING_GPRUNING, "Streaming GPruning", "#009e73", "D")

    ax.set_xscale("log")
    ax.set_xlabel("Avg latency (ms)", labelpad=1)
    ax.set_ylabel("QPS", labelpad=1)
    ax.set_xlim(0.85, 60)
    ax.set_ylim(0, 130000)
    ax.set_xticks([1, 2, 4, 8, 16, 32])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks([0, 40000, 80000, 120000])
    ax.set_yticklabels(["0", "40K", "80K", "120K"])
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.6, pad=1)
    ax.legend(frameon=False, loc="lower right", handlelength=1.2, borderpad=0.1, labelspacing=0.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = OUTPUT_DIR / "early_exit_latency_qps.pdf"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_avg_steps() -> Path:
    fig, ax = plt.subplots(figsize=(3.5, 1.4))
    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.30, top=0.94)

    labels = list(AVG_STEPS.keys())
    values = [AVG_STEPS[label] for label in labels]
    colors = ["#4d4d4d", "#d55e00", "#0072b2"]
    bars = ax.bar(labels, values, color=colors, width=0.58)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.35,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_ylabel("Avg steps/query", labelpad=1)
    ax.set_ylim(0, 36)
    ax.set_yticks([0, 12, 24, 36])
    ax.grid(True, which="major", axis="y", linewidth=0.35, alpha=0.35)
    ax.tick_params(axis="both", length=2.5, width=0.6, pad=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = OUTPUT_DIR / "early_exit_avg_steps.pdf"
    fig.savefig(out)
    plt.close(fig)
    return out


def main() -> None:
    configure_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for out in (plot_latency_qps(), plot_avg_steps()):
        print(out)


if __name__ == "__main__":
    main()
