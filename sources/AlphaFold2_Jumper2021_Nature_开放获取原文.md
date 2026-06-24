# AlphaFold2（Jumper et al., 2021, Nature）开放获取正文提取存档

- **来源 URL（原文）**：https://www.nature.com/articles/s41586-021-03819-2
- **开放获取全文（PMC）**：https://pmc.ncbi.nlm.nih.gov/articles/PMC8371605/
- **DOI**：10.1038/s41586-021-03819-2
- **出处**：Jumper, J., Evans, R., Pritzel, A. *et al.* "Highly accurate protein structure prediction with AlphaFold." *Nature* **596**, 583–589 (2021).
- **许可**：CC-BY 4.0（Creative Commons Attribution 4.0 International）。原文为开放获取，遵循 CC-BY 4.0 许可，允许在署名前提下复制与再利用。
- **整理日期**：2026-06-24

> **存档性质与重要声明**
> 本文为基于开放获取原文的提取存档，供研究/检索用，正式引用以原文为准。
>
> **抓取限制（务必知悉）**：本次整理所在的运行环境对外网出口实施策略管控，`WebFetch` 对 nature.com、PMC（ncbi.nlm.nih.gov）、ebi.ac.uk 乃至任意主机的直接抓取均返回 HTTP 403（CONNECT 被网关拒绝），按环境规则不得绕过。因此 **无法对 CC-BY 原文做逐字（verbatim）全文抓取**。
>
> 下文是以可用的 `WebSearch` 检索结果（含 Nature/PMC 摘要片段、EMBL-EBI 官方培训材料、CASP14 综述与多篇技术解读）为依据，对原文 **摘要、引言、方法概述、主要结果、讨论** 所做的 **忠实转述与结构化整理**。除非明确标注「原文摘要片段（检索所得）」，其余文字均为 **转述/概述，并非原文逐字内容**，不应作为逐字引用使用。需要权威、可逐字引用的文本，请访问上方 URL 阅读原文。凡本整理未能坐实的精确数字，均标注「待核实」。

---

## 摘要（Abstract）

> 以下为依据检索所得摘要片段整理的转述，关键句尽量贴近原文表述，但 **非保证逐字**。

蛋白质对生命几乎一切活动都至关重要，理解其结构有助于理解其功能。「仅凭氨基酸序列预测蛋白质将采取的三维结构」——即「蛋白质折叠问题」中的结构预测部分——是一个已有 **50 余年** 历史的重要开放研究问题。尽管近年有所进展，现有方法在精度上仍远未达到原子级，**尤其是在没有可用同源结构时**。

本文给出首个能够 **常规性地以原子级精度预测蛋白质结构** 的计算方法，**即便在不存在相似已知结构的情况下也能做到**。作者在极具挑战性的 **第 14 届蛋白质结构预测关键评估（CASP14）** 中验证了一个 **完全重新设计** 的、基于神经网络的 AlphaFold 模型，结果显示其在 **多数情况下达到与实验结构相媲美的精度**，并大幅超越其他方法。

该方法的底层是一种新颖的机器学习途径：它把关于蛋白质结构的 **物理与生物学知识**、以及 **多序列比对（MSA）** 信息，融入深度学习算法的设计之中。

> （检索所得摘要片段，措辞接近原文，供对照）：
> "Predicting the three-dimensional structure that a protein will adopt based solely on its amino acid sequence ... has been an important open research problem for more than 50 years. ... AlphaFold provides the first computational method that can regularly predict protein structures with atomic accuracy even in cases in which no similar structure is known."

---

## 引言（Introduction）

> 转述/概述，非逐字。

- 实验测定结构（X 射线晶体学、冷冻电镜、NMR）耗费大量时间与精力，且并非每个蛋白都能成功解析；这导致 **已知序列数** 与 **已实验解析结构数** 之间存在巨大差距。
- 既有的计算预测方法大致分两类：（1）**基于模板 / 同源建模**，依赖已解析的近缘结构；（2）**从头（de novo / ab initio）** 方法，依据物理化学原理或共进化信号建模。两者在 **缺乏近缘同源结构** 时通常都远逊于实验精度。
- 共进化思路（从大量同源序列中识别共同变异的残基对，推断空间接触）此前推动了不少进展，但仍不足以达到原子级精度。
- DeepMind 第一代 **AlphaFold** 在 **CASP13（2018）** 已取得参赛者中最高精度。本文的 **AlphaFold2** 是 **完全重新设计的不同系统**，以端到端方式直接从序列与 MSA 预测三维结构。

---

## 方法概述（The AlphaFold network / Methods 概述）

> 转述/概述，非逐字。数字凡来自二手资料者标注「待核实」。

### 总体设计
AlphaFold2 是一个 **端到端神经网络**：输入目标序列、检索得到的 **多序列比对（MSA）** 与 **结构模板**，**直接输出全原子三维坐标**，取消了传统「先预测残基间约束、再独立优化结构」的两阶段范式。网络主体由 **Evoformer 主干** 和 **结构模块（Structure Module）** 组成，并由 **recycling（循环）** 包裹整个网络以做迭代精炼。

### 两类核心表示
- **MSA 表示**：刻画目标序列与同源序列的关系，承载共进化信息。
- **配对表示（pair representation）**：以残基对为单位的二维表示，编码每个残基与其他每个残基之间的关系（含模板几何信息）。

### Evoformer 主干
- 由多个 block 堆叠（二手资料：**48 个、权重不共享**，待核实）。每个 block 含 MSA 塔与配对塔，并在二者间 **双向交换信息**。
- **轴向注意力（axial attention）**：在 MSA 二维网格上分别沿行、列做注意力。
- **三角更新 / 三角自注意力**：对配对表示注入 **三角不等式** 几何先验。
  - **三角乘法更新（triangle multiplicative update）**：含「起点」与「终点」两个版本。
  - **三角自注意力（triangle self-attention）**：含「环绕起点 / 环绕终点」两个版本。
- 经精炼后，配对表示蕴含残基间几何关系；MSA 表示第一行作为 **单一表示** 送入结构模块。

### 结构模块（Structure Module）与不变点注意力（IPA）
- **残基刚体框架 / 残基气体（residue gas）**：每个残基主链用一个独立的 3D 刚体（旋转 + 平移）表示，初始全部置于原点，随后被移动旋转到正确相对位置。
- 由若干权重共享的层组成（二手资料：**8 层**，待核实）。
- **不变点注意力（Invariant Point Attention, IPA）**：一种对全局刚体变换 **不变** 的几何感知注意力；在常规注意力外，引入配对表示作为 **pair bias**，并在三维空间中定义「点」以计算残基框架间的 **距离亲和度**。
- 随后预测 **主链与侧链扭转角**，结合框架重建 **全原子坐标**。
- 训练主损失为 **FAPE（Frame-Aligned Point Error，框架对齐点误差）**：在残基局部框架下比较预测与真实原子位置。

### 训练与推理技巧
- **Recycling（循环迭代）**：将上一轮输出（主链坐标、配对表示、MSA 表示第一行）作为额外输入再喂回网络，默认 **3 次循环**（待核实），几乎不增参数即可加深迭代精炼。
- **Self-distillation（自蒸馏，noisy-student 式半监督）**：先用 PDB 训练教师网络，再用它预测大量 **未标注序列**（如从 Uniclust30 取约 **35 万** 条多样序列，待核实）的结构，按置信度筛高置信子集，与 PDB 联合训练（二手资料：约 **25% PDB + 75% 自蒸馏**，待核实）。涉及数据库包括 Uniref90、Uniclust30、MGnify 及 **BFD（约 22 亿条序列）**。
- **置信度预测**：
  - **pLDDT（predicted LDDT）**：逐残基局部置信度（0–100）。
  - **PAE（Predicted Aligned Error）**：残基对级全局置信度，单位 Å——「若以残基 Y 对齐，残基 X 的预期位置误差」。
  - **pTM（predicted TM-score）**：对整体折叠 TM-score 的估计，由 PAE 相关量推导。

---

## 主要结果（Results）

> 转述/概述，数字均注明来源；未坐实者标「待核实」。

- **CASP14 整体精度**：AlphaFold 预测的 **域 GDT_TS 中位数约 92.4**，为 CASP 史上首次达此平均精度，尤其在更难的 Free Modeling 目标上表现突出（Wikipedia / 多源综述）。
- **达实验级的比例（best-of-5）**：约 **58 个域** GDT_TS > 90（视为与实验相当）；约 **87/92 个域** GDT_TS > 70（高精度）（二手综述）。
- **主链精度**：结构化区域主链 RMSD 典型 **约 1.2–1.6 Å**（二手综述）。原文常用 **r.m.s.d.95** 衡量主链精度、用侧链 RMSD 衡量全原子精度；常被引用的「主链 r.m.s.d.95 中位数约 0.96 Å、全原子约 1.5 Å」**未能在本次所抓资料中逐字坐实，标注为待核实**，请以原文 Fig.1 与正文为准。
- **相对竞争对手**：CASP14 评估方按 z 分数（>2.0）加总排名，AlphaFold2 得 **244.0**，次优团队约 **90.8**（二手综述）。
- **置信度校准**：pLDDT 与真实 LDDT 良好相关，可作可靠性指引；PAE 反映域间/复合物相对位置可信度。

---

## 讨论与局限（Discussion / Limitations）

> 转述/概述。

- **意义**：在多数情况下达到接近实验的精度，被视为蛋白质结构预测的范式突破；为大规模、低成本地获取结构信息打开大门，催生 AlphaFold 蛋白质结构数据库及众多下游应用。
- **局限（部分由原作者、部分由后续研究指出）**：
  - 以 **单链 / 单一构象** 为主，原生模型对 **多链复合物 / 多聚体** 支持有限。
  - 通常只给静态构象，难以刻画 **构象变化 / 动力学 / 别构**（apo/holo 多态）。
  - 对 **内在无序区** 常表示为漂浮长环（但低 pLDDT 可作无序指示）。
  - 对 **单点突变** 引起的结构/稳定性变化往往不敏感。
  - 依赖 **MSA 深度**，浅 MSA / 孤儿蛋白精度可能下降。
  - 预测终态结构而非折叠 **机理/通路**。

---

## 关键事实速查（基于检索来源）

| 项目 | 数值/内容 | 备注 |
|---|---|---|
| 论文 | Nature 596, 583–589 (2021) | DOI 10.1038/s41586-021-03819-2 |
| CASP14 域 GDT_TS 中位数 | 约 92.4 | 史上首次达实验级 |
| 达实验级域（best-of-5） | 约 58/92 域 GDT_TS>90 | 二手综述 |
| 高精度域（best-of-5） | 约 87/92 域 GDT_TS>70 | 二手综述 |
| 主链 RMSD | 约 1.2–1.6 Å（结构化区） | r.m.s.d.95 精确值待核实 |
| 核心模块 | Evoformer + Structure Module(IPA) | 端到端 |
| 主损失 | FAPE | — |
| 训练技巧 | recycling、self-distillation、pLDDT、PAE/pTM | 部分数量待核实 |
| 许可 | CC-BY 4.0 | 开放获取 |

---

## 参考来源（用于本提取存档）

- [Highly accurate protein structure prediction with AlphaFold — Nature（原文，CC-BY 4.0）](https://www.nature.com/articles/s41586-021-03819-2)
- [PMC8371605 — 论文开放获取全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8371605/)
- [AlphaFold — Wikipedia](https://en.wikipedia.org/wiki/AlphaFold) — CASP14、GDT_TS 92.4、AlphaFold DB、局限。
- [Strengths and limitations of AlphaFold 2 — EMBL-EBI Training](https://www.ebi.ac.uk/training/online/courses/alphafold/an-introductory-guide-to-its-strengths-and-limitations/strengths-and-limitations-of-alphafold/)
- [Glossary of terms — EMBL-EBI Training](https://www.ebi.ac.uk/training/online/courses/alphafold/glossary-of-terms/) — pLDDT/PAE/pTM 定义。
- [AlphaFold Protein Structure Database — EMBL-EBI](https://alphafold.ebi.ac.uk/) — 规模、CC-BY 4.0、pLDDT 着色。
- [The AlphaFold2 Method Paper: A Fount of Good Ideas（M. AlQuraishi）](https://moalquraishi.wordpress.com/2021/07/25/the-alphafold2-method-paper-a-fount-of-good-ideas/)
- [How does DeepMind AlphaFold2 work?（B. Burkov）](https://borisburkov.net/2021-12-25-1/)
- [AlphaFold 2 is here（OPIG/blopig）](https://www.blopig.com/blog/2021/07/alphafold-2-is-here-whats-behind-the-structure-prediction-miracle/)
- [Applying and improving AlphaFold at CASP14（PMC9299164）](https://pmc.ncbi.nlm.nih.gov/articles/PMC9299164/)
