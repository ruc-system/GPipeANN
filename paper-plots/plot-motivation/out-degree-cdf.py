#!/usr/bin/env python3
"""Plot out-degree CDFs for the 100M datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
OUTPUT_ROOT = Path(os.environ.get("GPIPEANN_FIGURE_OUTPUT", REPO_ROOT / "build" / "paper-figures"))
FONT_ROOT = REPO_ROOT / "fonts" / "gill-sans"
if not FONT_ROOT.is_dir():
    FONT_ROOT = REPO_ROOT / "ae" / "fonts"
OUTPUT = OUTPUT_ROOT / "fig-motivation" / "degree-cdf.pdf"
GILL_SANS_DIR = FONT_ROOT
DATA_DIR = ROOT / "data" / "degree"
ACCENT = "#7a1f1f"


@dataclass(frozen=True)
class DatasetSpec:
    title: str
    panel_label: str
    csv_path: Path
    color: str
    note_x: float


@dataclass(frozen=True)
class DegreeSummary:
    degree: int
    count: int
    ratio: float


def configure_fonts() -> None:
    for font_path in (
        GILL_SANS_DIR / "GillSans.ttc",
        GILL_SANS_DIR / "GillSans-SemiBold.ttf",
    ):
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))

    plt.rcParams.update(
        {
            "font.family": "Gill Sans",
            "font.sans-serif": ["Gill Sans"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
        }
    )


def build_datasets() -> list[DatasetSpec]:
    return [
        DatasetSpec(
            title="SIFT",
            panel_label="(a)",
            csv_path=DATA_DIR / "sift100m-ann_out_degree_distribution.csv",
            color="#cf6b2d",
            note_x=149,
        ),
        DatasetSpec(
            title="DEEP",
            panel_label="(b)",
            csv_path=DATA_DIR / "deep100m-ann_out_degree_distribution.csv",
            color="#3b8a63",
            note_x=146,
        ),
    ]


def load_summary(csv_path: Path) -> DegreeSummary:
    with csv_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    if len(rows) != 1:
        raise ValueError(f"expected a single-row distribution in {csv_path}, got {len(rows)}")

    row = rows[0]
    return DegreeSummary(
        degree=int(row["degree"]),
        count=int(row["count"]),
        ratio=float(row["ratio"]),
    )


def style_axes(ax: plt.Axes) -> None:
    ax.set_xlim(0, 256)
    ax.set_ylim(0, 1.04)
    ax.set_xticks([0, 64, 128, 192, 256])
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.grid(True, which="major", axis="y", linewidth=0.35, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_dataset(ax: plt.Axes, dataset: DatasetSpec) -> None:
    summary = load_summary(dataset.csv_path)
    style_axes(ax)

    x_values = [0, summary.degree, 256]
    y_values = [0.0, summary.ratio, summary.ratio]
    ax.step(x_values, y_values, where="post", color=dataset.color, linewidth=2.0)
    ax.fill_between(x_values, y_values, 0, step="post", color=dataset.color, alpha=0.14, linewidth=0)
    ax.vlines(summary.degree, 0.0, summary.ratio, color=dataset.color, linewidth=1.0, alpha=0.75)
    ax.scatter([summary.degree], [summary.ratio], s=18, color=dataset.color, zorder=3)

    ax.text(
        0.04,
        0.93,
        f"{dataset.panel_label} {dataset.title}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="semibold",
        color=ACCENT,
    )
    ax.annotate(
        "CDF reaches 1",
        xy=(summary.degree, summary.ratio),
        xytext=(dataset.note_x, 0.72),
        textcoords="data",
        ha="left",
        va="center",
        fontsize=8,
        color="#333333",
        arrowprops={
            "arrowstyle": "->",
            "linewidth": 0.8,
            "color": "#333333",
            "shrinkA": 2,
            "shrinkB": 2,
        },
    )


def save_plot() -> None:
    configure_fonts()
    datasets = build_datasets()
    fig, axes = plt.subplots(1, len(datasets), figsize=(3.5, 1.4), sharey=True)

    for ax, dataset in zip(axes, datasets, strict=True):
        plot_dataset(ax, dataset)
        ax.set_xlabel("Out-degree", labelpad=1)

    axes[0].set_ylabel("CDF", labelpad=1)

    fig.subplots_adjust(
        left=0.5 / 3.5,
        right=1 - 0.5 / 3.5,
        bottom=0.28,
        top=0.90,
        wspace=0.20,
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT)
    plt.close(fig)
    print(f"saved: {OUTPUT}")


def main() -> None:
    save_plot()


if __name__ == "__main__":
    main()
