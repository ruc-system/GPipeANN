# 按论文图号维护的图源

论文仓库的 `figures/` 是正式图与源文件的唯一维护位置。正文 Fig.1–9 每图一个目录；`figure.pdf` 是已采用版本，`plot.py` 是论文值绘图脚本，`source.pptx` 是设计图源。CSV 仅在对应脚本确实读取时保留。

| 正文图号 | 目录 | 源文件与输入 |
|---|---|---|
| Fig.1 | `fig01-latency-qps/` | `plot.py`；论文数值内嵌于脚本 |
| Fig.2 | `fig02-execution-models/` | `source.pptx`，GPipeANN 原始可编辑图 |
| Fig.3 | `fig03-io-latency/` | `plot.py`、`compute-cdf.csv` |
| Fig.4 | `fig04-overview/` | `source.pptx`，从最终矢量 PDF 恢复 |
| Fig.5 | `fig05-e2e/` | `plot.py`；论文数值内嵌于脚本 |
| Fig.6 | `fig06-openai-zipf/` | `plot.py`、`openai.csv`、`zipf.csv` |
| Fig.7 | `fig07-fusion/` | `plot.py`；论文数值内嵌于脚本 |
| Fig.8 | `fig08-ablation/` | `plot.py`；仅保留最终采用的 clean 绘图版本 |
| Fig.9 | `fig09-q-sensitivity/` | `plot.py`；论文数值内嵌于脚本 |

保留的扩展摘要还引用 `abstract-execution-models/` 和 `abstract-e2e/`；保留的 AE 附录引用 `appendix-a1/`。附录图的 `input.pdf` 是改名前的必要输入，`plot.py` 只恢复当前 GPipeANN 标签并校验图形未变。其他旧名图和未采用图不再保留。

## 重画实验图

从论文仓库根目录运行：

```bash
python3 -m pip install -r scripts/plot-requirements.txt
python3 scripts/plot_figures.py
python3 scripts/plot_figures.py fig06-openai-zipf
python3 scripts/plot_figures.py --with-supplement
```

默认输出在 `build/paper-figures/`，例如 `fig06-openai-zipf.pdf`。`--out-dir` 可调整输出目录。输入是论文保存值，不运行硬件实验，不切换到 AE 新测值。绘图标签统一使用 GPipeANN；重画输出与最终采用 PDF 的排版仍可能不同，因此不自动替换正式 PDF。Q 图的原稿给定利用率仍是保存值，不是本次重测。

共享组件位于 `scripts/better_annotation.py`、`scripts/paper_style.py` 和 `scripts/paper_contract.py`。字体由 `scripts/figure_paths.py` 定位：论文仓库用 `fonts/gill-sans/`，代码副本用既有 `ae/fonts/`。代码仓库 `paper-plots/` 使用相同的 `scripts/plot_figures.py` 入口，只包含实际使用的脚本与输入；正式图 PDF 和设计 PPTX 在论文仓库中查看。

## 设计图源

Fig.2 直接编辑 `source.pptx`。Fig.4 原始 PPTX 未找到，恢复版含 125 个可编辑文字/图形对象和一个原 PDF 已有的位图标注；自由曲线路径不是自动吸附连接器。恢复版不是原始 PPTX，重新导出不保证与采用 PDF 逐像素相同。

```bash
python3 -m pip install -r scripts/design-requirements.txt
python3 scripts/recover_design_pptx.py figures/fig04-overview/figure.pdf build/overview-recovered.pptx
FONTCONFIG_FILE="$PWD/scripts/figure-fonts.conf" libreoffice --headless --convert-to pdf --outdir build/design-figures figures/fig04-overview/source.pptx
```

保留字体为 Gill Sans Regular、真实 SemiBold，以及原 overview 中 `§` 使用的 Microsoft YaHei Bold 嵌入子集。后者位于 `fonts/design-symbols/`，不是完整字体。
