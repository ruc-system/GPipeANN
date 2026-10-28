"""Update the archived AE figure's legend without changing its plotted data.

Requires PyMuPDF. Run from the repository root after installing pymupdf.
The longer system name fits the existing legend when the redundant '(ours)' is omitted.
"""

from pathlib import Path
import sys
BUNDLE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUNDLE_ROOT / "scripts"))
from figure_paths import font_dir, output_path

import pymupdf


SOURCE = Path(__file__).with_name("input.pdf")
TARGET = output_path("appendix-a1")
FONT = font_dir() / "GillSans.ttc"


def main():
    doc = pymupdf.open(SOURCE)
    page = doc[0]
    drawings = page.get_drawings()
    spans = [
        span
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"] == "Quiver(ours)"
    ]
    assert len(spans) == 1, "Expected exactly one original system label"
    span = spans[0]
    page.add_redact_annot(span["bbox"], fill=False)
    page.apply_redactions(images=0, graphics=0)
    page.insert_font(fontname="GPipeGillSans", fontfile=str(FONT))
    page.insert_text(
        span["origin"], "GPipeANN", fontsize=span["size"], fontname="GPipeGillSans"
    )
    def geometry(paths):
        return [{k: v for k, v in path.items() if k != "seqno"} for path in paths]

    assert geometry(page.get_drawings()) == geometry(drawings), "Plot geometry changed"
    doc.subset_fonts()
    doc.save(TARGET, garbage=4, deflate=True)
    doc.close()


if __name__ == "__main__":
    main()
