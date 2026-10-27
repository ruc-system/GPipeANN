# 论文实验图源码

长期维护源在 [GPipeANN-paper](https://github.com/w-pq/GPipeANN-paper) 的 `plots/`；代码仓库 [GPipeANN](https://github.com/ruc-system/GPipeANN) 的 `paper-plots/` 保存相同副本。修改论文仓库后运行 `python3 scripts/sync_paper_plots.py`，用 `--check` 核对副本。此目录使用论文保存值重画，不运行硬件实验，也不以 AE 新测值替换论文值。

## 使用

```bash
python3 -m pip install -r plots/requirements.txt
python3 plots/build.py
```

在代码仓库中将命令里的 `plots` 换成 `paper-plots`。默认输出到当前仓库的 `build/paper-figures/`，不覆盖论文中已采用的 PDF；`--out-dir` 可指定输出目录。保留数据、坐标和原有标签，不在本次资料整理中重新挑选实验点或改变图的结论。

| 论文图 | 绘图源码 | 输入 |
|---|---|---|
| `fig-motivation/latency_qps.pdf` | `plot-motivation/plot_latency_qps.py` | 脚本中的论文数据 |
| `fig-motivation/io-latency.pdf` | `plot-motivation/io-latency.py` | 脚本中的论文数据、`data/comput-cdf/cdf.csv` |
| `fig-motivation/degree-cdf.pdf` | `plot-motivation/out-degree-cdf.py` | `data/degree/*100m*.csv` |
| `fig-evaluation/e2e.pdf` | `plot-evaluation/e2e.py` | 脚本中的论文数据 |
| `fig-evaluation/e2e-small.pdf` | `plot-evaluation/e2e-small.py` | 脚本中的论文数据 |
| `fig-evaluation/fusion.pdf` | `plot-evaluation/fusion.py` | 脚本中的论文数据；`data/fusionanns/` 保留来源表 |
| `fig-evaluation/ablation.pdf` | `plot-evaluation/ablation-clean.py` | 脚本中的论文数据；`ablation.py` 保留原 Pareto 点计算版本 |
| `fig-evaluation/q_sensitivity.pdf` | `plot-evaluation/q-sens.py` | 脚本中的论文数据，包括原稿给定的 CTA 利用率 |
| `fig-evaluation/openai1m_zipf.pdf` | `plot_openai_zipf.py`、`support/` | `data/openai1m_zipf.csv` 按 panel 拆分的 `data/openai1m/metrics.csv` 与 `data/zipf/metrics.csv` |

`historical-12-page/` 保存早期稿件的 step-recall、early-exit、static ablation、GPU latency/QPS 等脚本。用 `python3 plots/build.py --include-historical` 同时重画，输出在 `historical/` 子目录；这些图不是当前正文的新增实验。恢复来源和提交记录见 `SOURCES.json`。

这些是原论文绘图代码与保存值，当前论文 PDF 中的后续手工排版和 GPipeANN 标签调整未必逐字节重现。Q 图脚本中的 `95%` 是原稿保存值，不能称为本次测量结果。所有原始已采用 PDF 保持原样。AE 动态测量与相应绘图工具仍由代码仓库的 `ae/` 维护，不是此论文版绘图入口的另一个数据模式。

## 字体与依赖

论文仓库使用 `fonts/gill-sans/`，代码副本使用 `ae/fonts/`；脚本从自身路径解析字体和 CSV，不依赖旧 harness 目录或工作目录。脚本保持已有字体设置；本次修复只包括路径、缺失依赖与 Matplotlib 3.6 的 legend API 兼容。
