"""Shared 'better' arrow annotation in axes-fraction coordinates."""

from __future__ import annotations

MUTED_DARK_RED = "#8f3333"

# Steeper up-left arrow; axes fraction (0–1), independent of data ranges.
BETTER_ANNOTATION = {
    "arrow_head": (0.54, 0.39),
    "arrow_tail": (0.70, 0.15),
    "label": (0.68, 0.40),
}

ARROW_PROPS = {
    "arrowstyle": "->",
    "color": MUTED_DARK_RED,
    "linewidth": 2.4,
    "mutation_scale": 12,
}


def draw_better_annotation(
    ax,
    *,
    annotation: dict[str, tuple[float, float]] | None = None,
    fontproperties=None,
    fontweight: str = "semibold",
) -> None:
    coords = annotation or BETTER_ANNOTATION
    ax.annotate(
        "",
        xy=coords["arrow_head"],
        xytext=coords["arrow_tail"],
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=ARROW_PROPS,
    )
    text_kwargs = {
        "ha": "left",
        "va": "center",
        "color": MUTED_DARK_RED,
    }
    if fontproperties is not None:
        text_kwargs["fontproperties"] = fontproperties
    else:
        text_kwargs["fontweight"] = fontweight
    ax.text(
        *coords["label"],
        "better",
        transform=ax.transAxes,
        **text_kwargs,
    )
