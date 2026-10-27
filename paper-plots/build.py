#!/usr/bin/env python3
"""Redraw the paper figures using the preserved paper inputs, without hardware."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PAPER_SCRIPTS = [
    'plot-motivation/plot_latency_qps.py',
    'plot-motivation/io-latency.py',
    'plot-motivation/out-degree-cdf.py',
    'plot-evaluation/e2e.py',
    'plot-evaluation/e2e-small.py',
    'plot-evaluation/fusion.py',
    'plot-evaluation/ablation-clean.py',
    'plot-evaluation/q-sens.py',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path,
                        default=ROOT.parent / 'build/paper-figures')
    parser.add_argument('--include-historical', action='store_true',
                        help='also render the early paper figures into historical/')
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, MPLBACKEND='Agg', GPIPEANN_FIGURE_OUTPUT=str(out))
    for relative in PAPER_SCRIPTS:
        subprocess.run([sys.executable, str(ROOT / relative)], check=True, env=env)
    subprocess.run([sys.executable, str(ROOT / 'plot_openai_zipf.py'),
                    '-o', str(out / 'fig-evaluation/openai1m_zipf.pdf')],
                   check=True, env=env)
    if args.include_historical:
        for script in sorted((ROOT / 'historical-12-page').glob('*.py')):
            subprocess.run([sys.executable, str(script)], check=True, env=env, cwd=ROOT)
    # Inputs and sources are independent of the current working directory.
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(ROOT.rglob('*'))
              if p.is_file() and '__pycache__' not in p.parts}
    outputs = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(out.rglob('*.pdf'))}
    (out / 'manifest.json').write_text(json.dumps({
        'source': 'preserved paper plotting scripts and paper input values',
        'hardware_experiments_run': False,
        'inputs_sha256': inputs, 'outputs_sha256': outputs,
    }, indent=2) + '\n')
    print(f'Generated {len(outputs)} PDFs in {out}')


if __name__ == '__main__':
    main()
