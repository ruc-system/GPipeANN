#!/usr/bin/env python3
"""Plot Quiver per-query step-recall CDF.

The data is hard-coded from the pw=1, q=1, ef_search=200 run where the target
is per-query recall@10 >= 0.9.
"""

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


TOTAL_QUERIES = 10000
REACHED_QUERIES = 9983
STEP_COUNTS = {
    9: 46,
    10: 160,
    11: 330,
    12: 395,
    13: 450,
    14: 507,
    15: 506,
    16: 500,
    17: 464,
    18: 432,
    19: 436,
    20: 407,
    21: 403,
    22: 356,
    23: 308,
    24: 273,
    25: 265,
    26: 257,
    27: 239,
    28: 219,
    29: 201,
    30: 175,
    31: 148,
    32: 143,
    33: 171,
    34: 111,
    35: 142,
    36: 123,
    37: 117,
    38: 105,
    39: 96,
    40: 96,
    41: 76,
    42: 75,
    43: 77,
    44: 80,
    45: 61,
    46: 54,
    47: 51,
    48: 51,
    49: 62,
    50: 41,
    51: 29,
    52: 26,
    53: 32,
    54: 34,
    55: 28,
    56: 35,
    57: 27,
    58: 25,
    59: 26,
    60: 21,
    61: 21,
    62: 14,
    63: 22,
    64: 10,
    65: 18,
    66: 20,
    67: 21,
    68: 14,
    69: 18,
    70: 11,
    71: 14,
    72: 10,
    73: 14,
    74: 11,
    75: 12,
    76: 12,
    77: 5,
    78: 10,
    79: 5,
    80: 8,
    81: 7,
    82: 4,
    83: 10,
    84: 6,
    85: 7,
    86: 8,
    87: 6,
    88: 7,
    89: 2,
    90: 3,
    91: 3,
    92: 2,
    93: 7,
    94: 4,
    95: 6,
    96: 5,
    97: 9,
    98: 2,
    99: 4,
    100: 4,
    101: 3,
    102: 4,
    103: 8,
    104: 6,
    105: 2,
    106: 5,
    107: 9,
    108: 5,
    109: 3,
    111: 6,
    112: 2,
    113: 1,
    114: 4,
    115: 1,
    117: 4,
    118: 1,
    119: 1,
    120: 1,
    121: 2,
    122: 3,
    124: 2,
    127: 1,
    128: 3,
    132: 2,
    133: 3,
    134: 1,
    136: 1,
    137: 1,
    138: 1,
    139: 2,
    140: 1,
    141: 1,
    143: 1,
    144: 2,
    146: 2,
    148: 1,
    149: 2,
    150: 1,
    151: 1,
    152: 1,
    158: 1,
    160: 2,
    161: 1,
    164: 1,
    169: 1,
    171: 1,
    173: 1,
    176: 1,
    184: 1,
    194: 1,
    197: 1,
    198: 1,
    202: 1,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def configure_fonts(root: Path) -> None:
    font_dir = FONT_ROOT
    for font_path in sorted(font_dir.glob("*")):
        if font_path.suffix.lower() in {".ttf", ".ttc", ".otf"}:
            font_manager.fontManager.addfont(str(font_path))

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Gill Sans", "Gill Sans MT"],
            "font.size": 9,
            "pdf.fonttype": 42,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
        }
    )


def expanded_steps() -> list[int]:
    steps: list[int] = []
    for step, count in sorted(STEP_COUNTS.items()):
        steps.extend([step] * count)
    assert len(steps) == REACHED_QUERIES
    return steps


def p90_step(steps: list[int]) -> int:
    return steps[int(TOTAL_QUERIES * 0.90) - 1]


def plot() -> None:
    root = repo_root()
    configure_fonts(root)

    steps = expanded_steps()
    y_values = [(idx + 1) / TOTAL_QUERIES for idx in range(len(steps))]
    p90 = p90_step(steps)

    fig, ax = plt.subplots(figsize=(3.5, 1.6))
    ax.plot(steps, y_values, color="#0072B2", linewidth=1.5)
    ax.fill_between(steps, y_values, 0, color="#56B4E9", alpha=0.22, linewidth=0)
    ax.axhline(REACHED_QUERIES / TOTAL_QUERIES, color="#D55E00", linewidth=0.9, linestyle="--")
    ax.axhline(0.90, color="#009E73", linewidth=0.9, linestyle=":")
    ax.axvline(p90, color="#009E73", linewidth=0.9, linestyle=":")
    ax.scatter([p90], [0.90], s=14, color="#009E73", zorder=3)
    ax.annotate(
        f"90% of queries reach target\nwithin {p90} steps",
        xy=(p90, 0.90),
        xytext=(70, 0.70),
        textcoords="data",
        color="#009E73",
        fontsize=9,
        ha="left",
        va="center",
        arrowprops={
            "arrowstyle": "->",
            "color": "#009E73",
            "linewidth": 0.8,
            "shrinkA": 2,
            "shrinkB": 2,
        },
    )

    ax.set_xlim(0, 205)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Steps to reach recall@10 >= 0.9", labelpad=1)
    ax.set_ylabel("CDF", labelpad=1)
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.set_yticks([0.0, 0.5, 0.9, 1.0])
    ax.grid(True, color="#d9d9d9", linewidth=0.5, alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.98,
        0.08,
        f"{TOTAL_QUERIES:,} queries; {REACHED_QUERIES:,} reach target",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color="#D55E00",
        fontsize=9,
    )

    out_path = OUTPUT_ROOT / "quiver_step_recall_cdf.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.35)
    fig.savefig(out_path, format="pdf")
    plt.close(fig)
    print(out_path)


if __name__ == "__main__":
    plot()
