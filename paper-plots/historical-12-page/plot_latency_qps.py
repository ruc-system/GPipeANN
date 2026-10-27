#!/usr/bin/env python3
"""Plot latency-QPS comparison for Quiver, FlashANNS, and GustANN."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures")) / "historical"
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter


FULL_OUTPUTS = [
    OUTPUT_ROOT / "quiver_latency_qps.pdf",
    OUTPUT_ROOT / "quiver_latency_qps.pdf",
]
BASELINE_OUTPUTS = [OUTPUT_ROOT / "baseline_latency_qps.pdf"]
GILL_SANS_DIR = FONT_ROOT


@dataclass(frozen=True)
class PlotSeries:
    label: str
    points: list[tuple[float, float]]
    color: str
    marker: str
    linewidth: float = 1.4


@dataclass(frozen=True)
class PlotJob:
    outputs: list[Path]
    series: list[PlotSeries]


def configure_fonts() -> None:
    """Use the paper's bundled Gill Sans fonts for this figure."""
    for font_path in (
        GILL_SANS_DIR / "GillSans.ttc",
        GILL_SANS_DIR / "GillSans-SemiBold.ttf",
    ):
        font_manager.fontManager.addfont(font_path)

    plt.rcParams.update(
        {
            "font.family": "Gill Sans",
            "font.sans-serif": ["Gill Sans"],
        }
    )


def pareto_frontier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return points that are not dominated by lower latency and higher QPS."""
    frontier: list[tuple[float, float]] = []
    for latency, qps in sorted(points):
        if not frontier or qps > max(prev_qps for _, prev_qps in frontier):
            frontier.append((latency, qps))
    return frontier


def plot_line(
    ax: plt.Axes,
    points: list[tuple[float, float]],
    label: str,
    color: str,
    marker: str,
    linewidth: float = 1.4,
) -> None:
    points = sorted(points)
    latency = [point[0] for point in points]
    qps = [point[1] for point in points]
    ax.plot(
        latency,
        qps,
        label=label,
        color=color,
        marker=marker,
        markersize=3.2,
        linewidth=linewidth,
    )


def build_plot_jobs() -> list[PlotJob]:
    quiver_q2 = [
        (1.821, 61396.25),
        (2.452, 91193.58),
        (3.149, 106455.23),
        (4.120, 108476.29),
        (4.731, 118096.23),
        (5.519, 121484.99),
        (6.159, 126974.76),
        (7.341, 121730.32),
        (7.874, 127670.95),
        (8.410, 132777.25),
    ]
    quiver_pw2 = [
        (0.956, 58420.19),
        (1.183, 92802.77),
        (1.473, 110443.85),
        (1.977, 109100.97),
        (2.342, 111107.60),
        (2.868, 109617.39),
        (3.244, 111857.20),
        (3.824, 109731.83),
        (4.116, 113132.35),
        (4.416, 117611.02),
    ]
    flashanns = [
        (1.916, 29229.99),
        (2.246, 49856.20),
        (2.663, 63069.95),
        (3.133, 71482.36),
        (3.663, 76368.81),
        (4.231, 79320.16),
        (4.633, 84470.27),
        (5.570, 80326.77),
        (6.082, 82824.35),
        (6.228, 89701.87),
    ]
    gustann = [
        (11.274, 56507.06),
        (11.712, 81475.62),
        (13.104, 68557.88),
        (18.446, 79943.79),
        (21.431, 112327.67),
        (31.558, 101881.39),
        (43.382, 96313.60),
        (63.805, 117264.84),
        (79.537, 69780.24),
        (119.617, 111097.96),
        (163.690, 119498.51),
        (253.373, 74767.44),
        (309.479, 124377.33),
        (348.800, 118008.86),
    ]

    quiver = PlotSeries(
        "Quiver",
        pareto_frontier(quiver_q2 + quiver_pw2),
        "#1f77b4",
        "o",
        linewidth=1.6,
    )
    flashanns = PlotSeries(
        "FlashANNS",
        pareto_frontier(flashanns),
        "#ff7f0e",
        "s",
    )
    gustann = PlotSeries(
        "GustANN",
        pareto_frontier(gustann),
        "#2ca02c",
        "^",
    )
    return [
        PlotJob(FULL_OUTPUTS, [quiver, flashanns, gustann]),
        PlotJob(BASELINE_OUTPUTS, [flashanns, gustann]),
    ]


def save_plot(job: PlotJob) -> None:
    configure_fonts()
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(3.5, 1.4))

    for series in job.series:
        plot_line(
            ax,
            series.points,
            series.label,
            series.color,
            series.marker,
            linewidth=series.linewidth,
        )

    ax.set_xscale("log")
    ax.set_xlabel("Average latency (ms)", labelpad=1)
    ax.set_ylabel("QPS", labelpad=1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}K"))
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="both", linewidth=0.35, alpha=0.35)
    ax.legend(
        loc="lower right",
        frameon=True,
        framealpha=0.9,
        borderpad=0.25,
        handlelength=1.3,
        handletextpad=0.4,
        labelspacing=0.25,
    )
    ax.margins(x=0.04, y=0.08)

    fig.subplots_adjust(left=0.15, right=0.99, bottom=0.32, top=0.96)
    for output in job.outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output)
    plt.close(fig)


def main() -> None:
    for job in build_plot_jobs():
        save_plot(job)


if __name__ == "__main__":
    main()
