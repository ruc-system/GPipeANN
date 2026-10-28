#!/usr/bin/env python3
"""Draw the seven experimental figures used by the final paper, without hardware."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from figure_paths import BUNDLE_ROOT, REPO_ROOT

FIGURES = ['fig01-latency-qps', 'fig03-io-latency', 'fig05-e2e',
           'fig06-openai-zipf', 'fig07-fusion', 'fig08-ablation',
           'fig09-q-sensitivity']
SUPPLEMENT = ['abstract-e2e', 'appendix-a1']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('figures', nargs='*', choices=FIGURES + SUPPLEMENT)
    parser.add_argument('--out-dir', type=Path,
                        default=REPO_ROOT / 'build/paper-figures')
    parser.add_argument('--with-supplement', action='store_true',
                        help='also draw the retained abstract and appendix figures')
    args = parser.parse_args()
    selected = args.figures or FIGURES
    if args.with_supplement:
        selected = list(dict.fromkeys(selected + SUPPLEMENT))
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, MPLBACKEND='Agg', GPIPEANN_FIGURE_OUTPUT=str(out))
    for name in selected:
        subprocess.run([sys.executable,
                        str(BUNDLE_ROOT / 'figures' / name / 'plot.py')],
                       check=True, env=env)
    records = {name: hashlib.sha256((out / f'{name}.pdf').read_bytes()).hexdigest()
               for name in selected}
    (out / 'manifest.json').write_text(json.dumps({
        'source': 'saved paper values; not new AE measurements',
        'hardware_experiments_run': False, 'outputs_sha256': records,
    }, indent=2) + '\n')
    print(f'Generated {len(selected)} paper figures in {out}')


if __name__ == '__main__':
    main()
