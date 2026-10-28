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

默认输出在 `build/paper-figures/`，例如 `fig06-openai-zipf.pdf`。`--out-dir` 可调整输出目录。输入是论文保存值，不运行硬件实验，不切换到 AE 新测值。绘图标签和版式与采用图对齐；`scripts/check_figures.py` 在 144、300 dpi 逐像素比较 9 份输出，不读取采用图来生成实验图，也不自动替换正式 PDF。Q 图的原稿给定利用率仍是保存值，不是本次重测。

共享组件位于 `scripts/better_annotation.py`、`scripts/paper_style.py` 和 `scripts/paper_contract.py`。字体由 `scripts/figure_paths.py` 定位：论文仓库用 `fonts/gill-sans/`，代码副本用既有 `ae/fonts/`。代码仓库 `paper-plots/` 使用相同的 `scripts/plot_figures.py` 入口，只包含实际使用的脚本与输入；正式图 PDF 和设计 PPTX 在论文仓库中查看。

## 设计图源

Fig.2 直接编辑 `source.pptx`。Fig.4 原始 PPTX 未找到，恢复版现在包含 33 个完整文本框、57 个边界贴合实际几何的矢量对象，以及一个原 PDF 已有的位图标注。`Persistent kernel`、`Q1`、`H1` 和 Slot 标签不再拆框；两个标题分别保留为一个双行文本框，框内保留 § 的原字体。自由曲线路径仍不是自动吸附连接器。

```bash
python3 -m pip install -r scripts/design-requirements.txt
python3 scripts/recover_design_pptx.py figures/fig04-overview/figure.pdf build/overview-recovered.pptx
FONTCONFIG_FILE="$PWD/scripts/figure-fonts.conf" libreoffice --headless --convert-to pdf --outdir build/design-figures figures/fig04-overview/source.pptx
```

保留字体为 Gill Sans Regular、真实 SemiBold，以及原 overview 中 `§` 使用的 Microsoft YaHei Bold 嵌入子集。后者位于 `fonts/design-symbols/`，不是完整字体。字距和位置校准保存在 `fig04-overview/text-layout.json`，恢复脚本校验对应 PDF 哈希后自动应用；标签在框内使用格式 runs 保留字距，不拆成多个文本框。当前校准使用 LibreOffice 24.2.7.2；其他软件导出时应重新检查。

## 对齐检查

先生成全部保留的实验图，再导出 Fig.4 PPTX，运行：

```bash
python3 scripts/plot_figures.py --with-supplement
FONTCONFIG_FILE="$PWD/scripts/figure-fonts.conf" libreoffice --headless --convert-to pdf --outdir build/design-figures figures/fig04-overview/source.pptx
python3 scripts/check_figures.py --design-pdf build/design-figures/source.pdf --proof build/figure-alignment.pdf
```

检查包括：9 份实验图在 144/300 dpi 的精确像素比较、完整文本框结构、图形编辑边界，以及 PPTX 导出的逐字符位置。设计图的默认位置误差阈值为 0.25 pt；实验图不使用这一容差，必须完全一致。对照 PDF 和 JSON 报告在 `build/`，采用的论文 PDF 保持原样。
