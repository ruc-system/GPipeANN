"""Paths shared by the paper figure scripts and their code-repository copy."""
import os
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = (BUNDLE_ROOT.parent if BUNDLE_ROOT.name == 'paper-plots' else BUNDLE_ROOT)


def font_dir():
    for directory in [BUNDLE_ROOT / 'fonts/gill-sans', REPO_ROOT / 'ae/fonts']:
        if (directory / 'GillSans.ttc').is_file():
            return directory
    raise FileNotFoundError('Missing Gill Sans: expected fonts/gill-sans or ae/fonts')


def output_path(figure):
    directory = Path(os.environ.get('GPIPEANN_FIGURE_OUTPUT',
                                    REPO_ROOT / 'build/paper-figures'))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f'{figure}.pdf'
