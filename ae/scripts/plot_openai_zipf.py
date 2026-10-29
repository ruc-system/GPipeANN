#!/usr/bin/env python3
"""Plot OpenAI1M and SIFT1B-Zipf P99/QPS Pareto fronts."""

from __future__ import annotations

import argparse
import csv
import logging
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
from matplotlib.ticker import LogLocator, NullFormatter
from matplotlib.transforms import Affine2D

import paper_style as ps
from paper_contract import figure_size


logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
logging.getLogger("fontTools.ttLib.tables._p_o_s_t").setLevel(logging.ERROR)

SYSTEMS = ("FlashANNS", "GustANN", "GPipeANN")
DISPLAY = {"GPipeANN": "GPipeANN(ours)", "FlashANNS": "FlashANNS", "GustANN": "GustANN"}


def line_style(system: str) -> dict:
    style = ps.line_style(system)
    if system == "FlashANNS":
        style["marker"] = "s"
    elif system == "GustANN":
        style["marker"] = "^"
    style.update(linewidth=1.35, markersize=3,
                 markeredgecolor=style["color"], markeredgewidth=1)
    return style


def read_points(
    path: Path,
    *,
    gust_minibatch_min: int | None = None,
) -> dict[str, list[tuple[float, float]]]:
    points: dict[str, list[tuple[float, float]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            system = row.get("system", "")
            if system not in SYSTEMS:
                continue
            if system == "GustANN" and gust_minibatch_min is not None:
                try:
                    if int(row["mini_batch"]) < gust_minibatch_min:
                        continue
                except (KeyError, TypeError, ValueError):
                    continue
            try:
                latency = float(row["p99_ms"])
                qps = float(row["qps"])
            except (KeyError, TypeError, ValueError):
                continue
            if latency > 0 and qps > 0 and math.isfinite(latency) and math.isfinite(qps):
                points[system].append((latency, qps))
    return points


def pareto(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Keep points that improve QPS as P99 latency increases."""
    front = []
    best_qps = -math.inf
    for point in sorted(points, key=lambda value: (value[0], -value[1])):
        if point[1] > best_qps:
            front.append(point)
            best_qps = point[1]
    return front


def draw_panel(
    ax,
    csv_path: Path,
    panel: str,
    *,
    gust_minibatch_min: int | None = None,
    gpipeann_latency_max_ms: float | None = None,
) -> None:
    grouped = read_points(
        csv_path,
        gust_minibatch_min=gust_minibatch_min,
    )
    if gpipeann_latency_max_ms is not None:
        grouped["GPipeANN"] = [
            point for point in grouped.get("GPipeANN", [])
            if point[0] <= gpipeann_latency_max_ms
        ]
    all_latency: list[float] = []
    all_qps: list[float] = []
    for system in SYSTEMS:
        points = pareto(grouped.get(system, []))
        if not points:
            raise SystemExit(f"no valid {system} points in {csv_path}")
        latency = [point[0] for point in points]
        qps = [point[1] for point in points]
        ax.plot(latency, qps, label=DISPLAY[system], **line_style(system))
        all_latency.extend(latency)
        all_qps.extend(qps)

    ps.prepare_tradeoff(ax, all_latency, all_qps, "upper left")
    # Match fusion.pdf's two equally spaced y ticks; scale values to the data.
    ceiling = math.ceil(max(all_qps) * 1.4 / 20000) * 20000
    ax.set_ylim(0, ceiling)
    ax.set_yticks([ceiling / 2, ceiling])
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=(3, 4, 6, 7, 8, 9)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(which="major", direction="out", length=2.5, width=.8, pad=1)
    ax.tick_params(which="minor", direction="out", length=2, width=.6)
    ax.set_axisbelow(True)
    ax.grid(which="major", color="#b0b0b0", linewidth=.35, alpha=.6)
    ax.text(.03, (57.449775 - 24.192) / 41.472, panel,
            transform=ax.transAxes, ha="left", va="baseline",
            fontproperties=ps.semibold_font(), fontsize=9, color="#8F3333")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--openai",
        type=Path,
        default=root / "results/openai1m/metrics.csv",
    )
    parser.add_argument(
        "--zipf",
        type=Path,
        default=root / "results/zipf/metrics.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=root / "figures/openai1m_zipf.pdf",
    )
    args = parser.parse_args(argv)

    for path in (args.openai, args.zipf):
        if not path.is_file():
            parser.error(f"missing metrics file: {path}")
    if args.output.suffix.lower() != ".pdf":
        parser.error("output must be a PDF")

    ps.apply_style(submitted_gill=True)
    fig, axes_grid = plt.subplots(
        1, 2, figsize=figure_size("fusion"), squeeze=False
    )
    axes = axes_grid[0]
    draw_panel(
        axes[0],
        args.openai,
        "OpenAI1M",
        gust_minibatch_min=16,
        gpipeann_latency_max_ms=40,
    )
    draw_panel(
        axes[1], args.zipf, "SIFT1B-Zipf",
        gpipeann_latency_max_ms=15,
    )

    handles = [Line2D([], [], **line_style(system)) for system in SYSTEMS]
    labels = [DISPLAY[system] for system in SYSTEMS]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exact point geometry extracted from the submitted paper's fusion.pdf
    # (252 x 86.4 pt). Keep fixed margins: text widths must not move axes.
    fig.subplots_adjust(left=.15, right=.985, bottom=.28, top=.76, wspace=.32)
    point_transform = Affine2D().scale(1 / 252, 1 / 86.4) + fig.transFigure
    fig.text(112.265, 8.289875, "P99 Latency (ms)", transform=point_transform,
             ha="left", va="baseline", fontsize=9)
    fig.text(9.33125, 23.27175, "Throughput", transform=point_transform,
             ha="left", va="baseline", rotation=90, rotation_mode="anchor",
             fontsize=9)
    # Preserve fusion.pdf's annotation geometry, translated into the free
    # upper-right area so neither the curves nor the dataset labels are covered.
    for panel_offset in (0, 119.7217241379):
        dx = 10 + panel_offset
        dy = 57.449775 - 43.7183775
        fig.text(88.5910344828 + dx, 43.7183775 + dy, "better",
                 transform=point_transform, ha="left", va="baseline",
                 fontproperties=ps.semibold_font(), fontsize=9, color="#8F3333")
        vertices = [(88.757551, 36.519390), (85.019080, 39.083527),
                    (82.018213, 41.141757), (79.754949, 42.694081),
                    (82.355856, 37.999905), (79.754949, 42.694081),
                    (85.070834, 41.958300)]
        path = MplPath([(x + dx, y + dy) for x, y in vertices],
                       [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4,
                        MplPath.CURVE4, MplPath.MOVETO, MplPath.LINETO,
                        MplPath.LINETO])
        fig.add_artist(PathPatch(path, transform=point_transform, fill=False,
                                color="#8F3333", linewidth=2.4,
                                capstyle="round", joinstyle="round"))
    fig.legend(handles, labels, loc="lower center", ncol=3,
               bbox_to_anchor=(.58, 75.035875 / 86.4), borderaxespad=0,
               frameon=False, fontsize=8, handlelength=1.3, handletextpad=.35,
               columnspacing=.9, borderpad=0, labelspacing=.15)
    fig.savefig(args.output, format="pdf", dpi=300)
    plt.close(fig)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
