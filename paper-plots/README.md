# Figure plotting scripts

This directory contains plotting scripts and saved inputs for the experimental figures. The inputs are saved paper values, not new hardware measurements.

| Figure | Directory | Inputs |
|---|---|---|
| Fig.1 | `fig01-latency-qps/` | Values embedded in `plot.py` |
| Fig.3 | `fig03-io-latency/` | `plot.py`, `compute-cdf.csv` |
| Fig.5 | `fig05-e2e/` | Values embedded in `plot.py` |
| Fig.6 | `fig06-openai-zipf/` | `plot.py`, `openai.csv`, `zipf.csv` |
| Fig.7 | `fig07-fusion/` | Values embedded in `plot.py` |
| Fig.8 | `fig08-ablation/` | Values embedded in `plot.py` |
| Fig.9 | `fig09-q-sensitivity/` | Values embedded in `plot.py` |

Run these commands from the repository root:

```bash
python3 -m pip install -r paper-plots/scripts/plot-requirements.txt
python3 paper-plots/scripts/plot_figures.py
python3 paper-plots/scripts/plot_figures.py fig06-openai-zipf
```

Outputs default to `build/paper-figures/`; use `--out-dir` to choose another destination. The output manifest records PDF hashes and identifies the inputs as saved values.

`--with-supplement` also generates the retained abstract and appendix figures. Shared plotting helpers are in `scripts/`, and fonts are loaded from `ae/fonts/`.
