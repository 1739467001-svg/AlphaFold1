---
标题: AlphaFold2 技术精读
英文原题: Highly accurate protein structure prediction with AlphaFold
作者/主体: John Jumper, Richard Evans, Alexander Pritzel, Tim Green, Michael Figurnov, Olaf Ronneberger, Kathryn Tunyasuvunakool 等，DeepMind
发表/来源: Nature 596, 583–589 (2021)
DOI/标识: 10.1038/s41586-021-03819-2
原文链接: https://www.nature.com/articles/s41586-021-03819-2
开放获取: 是（CC-BY 4.0）
整理日期: 2026-06-24
---

# AlphaFold2 技术精读

> AlphaFold2 是首个能仅凭氨基酸序列、在多数情况下以接近实验精度（CASP14 域 GDT_TS 中位数约 92.4）端到端预测蛋白质三维结构的深度学习系统，标志着 50 年「蛋白质折叠问题」中单链结构预测部分取得突破。

> **关于来源的说明**：本精读所引数据均来自整理者实际检索到的公开来源（见文末「参考来源」）。受本次运行环境的网络出口策略限制，无法对 Nature 原文与 PMC 全文做逐字抓取，部分表述为基于二手综述/官方培训材料的转述；凡涉及精确数字处均标注来源，无法在所抓资料中坐实的细节标注「待核实」。正式引用请以 Nature 原文为准。

---

## 1. 背景与动机

### 蛋白质折叠问题
蛋白质的功能由其三维结构决定，而结构在很大程度上由氨基酸序列编码。「仅凭氨基酸序列预测蛋白质会折叠成的三维结构」——即「蛋白质折叠问题」中的结构预测部分——是一个已有 **50 余年** 历史的开放性科学难题（Anfinsen 假说指出序列决定结构）。

实验测定结构的主流手段（X 射线晶体学、冷冻电镜、核磁共振 NMR）昂贵、耗时，导致已知序列数量（数亿级，UniProt）与已实验解析结构数量（PDB 中约数十万条目）之间存在巨大鸿沟。

### CASP 与此前方法的局限
**CASP（Critical Assessment of protein Structure Prediction）** 是每两年举办一次的盲测竞赛：组织方在结构尚未公开前发放序列，各团队提交预测，再与随后公布的实验结构比对，是该领域公认的「黄金标准」评测。

在 AlphaFold2 之前：
- 传统方法（基于模板/同源建模、共进化耦合、物理能量函数等）在 **缺乏近缘同源结构（Free Modeling / FM 类）** 时精度远低于实验水平。
- DeepMind 的第一代 **AlphaFold（AlphaFold1）** 在 **CASP13（2018）** 已取得当时参赛者中的最高精度，但仍未达实验级；其思路更接近「先预测残基间距离分布，再用梯度下降优化结构」的两阶段范式。
- AlphaFold2 是 **完全重新设计** 的模型（在 CASP14 以队名「AlphaFold2」参赛，与 CASP13 版本是不同的系统）。

### CASP14 突破
- **CASP14 评测期约为 2020 年 5–7 月**，结果于 **2020 年 12 月** 的会议上公布。
- AlphaFold 预测的 **域 GDT_TS 中位数达到约 92.4**，这是 CASP 历史上首次达到这一平均精度水平，尤其是在更困难的 Free Modeling 目标上。
- 据报道，其精度「在多数情况下可与实验结构相媲美」（accuracy competitive with experimental structures），并大幅超越其他方法。
- CASP14 评估方按 z 分数加总排名中，AlphaFold2 得分 **244.0**，而第二名团队约为 **90.8**，差距悬殊。
- CASP 组织者 John Moult 在闭幕发言中表示「单链蛋白质的结构预测问题现在已经解决」。学界（如 Mohammed AlQuraishi）普遍认为这是范式级突破，剩余改进更偏「工程问题」而非「科学问题」；但也有声音强调「折叠问题」（含动力学、复合物、构象变化）尚未全部解决。

> 注：GDT_TS（Global Distance Test – Total Score）取值 0–100，越高越好；一般认为 **GDT_TS ≳ 90** 即可视为与实验结构相当。

---

## 2. 核心架构

AlphaFold2 是一个 **端到端（end-to-end）** 神经网络：输入氨基酸序列、由其检索得到的 **多序列比对（MSA）** 以及 **结构模板（templates）**，直接输出全原子三维坐标，无需传统的「先预测约束、再单独优化」两阶段流程。

整体数据流可分为三段：**输入特征构建 → Evoformer 主干 → Structure Module（结构模块）**，并辅以 **recycling（循环迭代）** 包裹整个网络。

### 2.1 输入：MSA 与模板，两类核心表示
网络内部维护两种「富表示」并反复精炼：
- **MSA 表示（MSA representation）**：刻画目标序列与其同源序列之间的关系，承载共进化信息（哪些残基位点共同变异，暗示空间上接触）。
- **配对表示（pair representation）**：一个以残基对为单位的二维表示，描述序列中每个氨基酸与其他每个氨基酸之间的关系（可理解为「残基间关系图」的边特征）。

模板结构信息也被编码进这两类表示中。

### 2.2 Evoformer 主干
Evoformer 是 AlphaFold2 的核心模块，包含 **48 个（权重不共享的）block** 堆叠（数量据二手资料，待与原文核实）。每个 block 含两条「塔」——MSA 塔与配对（pair）塔——并设计了二者之间的 **双向通信机制**，让序列层面的共进化信息与残基对的几何关系信息不断互相更新：

- **轴向注意力（axial attention）**：在 MSA 表示这样的二维网格上，分别沿「行（row-wise）」和「列（column-wise）」做注意力，从而高效处理大矩阵。
- **MSA → pair 的信息传递**：MSA 列方向的统计（如成对相关）被汇总写入配对表示。
- **配对表示的三角更新（triangular updates）与三角自注意力（triangular self-attention）**：这是 Evoformer 的标志性设计，用以注入 **三角不等式（triangle inequality）** 这一几何先验——任意三个残基 i、j、k 的两两距离需满足三角约束。具体含两类块：
  - **三角乘法更新（triangle multiplicative update）**：分「起点（starting node）」与「终点（ending node）」两个版本，基于共享同一起点/终点的所有边来更新边 (i,j)。
  - **三角自注意力（triangle self-attention）**：同样有「环绕起点 / 环绕终点」两个版本。
- **门控、残差连接、转移（transition）层** 等标准组件。

经过 Evoformer 反复精炼后，配对表示已隐含残基间的几何关系，MSA 表示的「第一行」（对应目标序列）成为送入结构模块的 **单一表示（single representation）**。

### 2.3 Structure Module 与 Invariant Point Attention（IPA）
结构模块（Structure Module）将抽象表示「翻译」为显式三维坐标：

- **残基气体 / 刚体框架表示（residue gas / backbone frames）**：每个残基的主链被表示为一个独立的刚体局部坐标系（一个旋转 + 平移，即 3D 框架），初始时所有残基都放在原点（故称「residue gas」），随后被逐步移动、旋转到正确的相对位置。
- **结构模块约含 8 个权重共享的层**（数量据二手资料，待核实）。每一层都用 **不变点注意力（Invariant Point Attention, IPA）** 来更新单一表示与主链框架。
- **IPA 的关键性质——对全局刚体变换不变**：它是一种「几何感知」的注意力。除常规的基于内容的自注意力外，IPA 还：
  1. 将配对表示转化为逐元素的 **pair bias（配对偏置）** 加入注意力；
  2. 引入定义在三维空间中的「点」，计算残基框架之间的 **距离亲和度（distance affinities）**。由于这些点在各自残基的局部坐标系中定义，整套注意力对蛋白质整体的平移/旋转 **不变**。
- 之后结构模块预测 **主链与侧链的扭转角（torsion angles）**，结合主链框架即可重建 **全原子坐标**。
- 训练用 **FAPE 损失（Frame-Aligned Point Error，框架对齐点误差）**：在每个残基的局部框架下比较预测与真实原子位置，强调局部结构准确性，并天然对全局刚体变换不变。

> 直观理解：Evoformer 负责「读懂」序列/共进化/几何关系，Structure Module 负责把这种理解「摆」成真实可见的 3D 坐标，IPA 则保证「摆」的过程不依赖于你从哪个角度看蛋白质。

---

## 3. 训练与推理技巧

### 3.1 Recycling（循环迭代精炼）
整个网络（Evoformer + Structure Module）被外层 **recycling** 包裹：把前一轮的输出作为额外输入再喂回网络，重复若干次（论文默认 **3 次**循环，对应共 4 趟前向）。被回收的内容包括：结构模块输出的 **主链原子坐标**、Evoformer 输出的 **配对表示** 以及 **MSA 表示的第一行**。
- 作用：在 **几乎不增加参数量** 的情况下让网络「更深」，对输入做多轮迭代精炼，显著提升精度。

### 3.2 Self-distillation（自蒸馏，利用未标注序列）
为突破已知实验结构（PDB）数量的限制，AlphaFold2 采用类似 **noisy-student 自蒸馏** 的半监督策略：
1. 先用 PDB 训练一个「教师」网络；
2. 用它去 **预测大量未标注序列的结构**（例如从 Uniclust30 取约 **35 万** 条多样序列），并按置信度筛出高置信子集，构成新的「预测结构数据集」；
3. 再用 **PDB + 该自蒸馏数据集** 联合训练新模型。据二手资料，训练样本中约 **25% 来自 PDB 已知结构、约 75% 来自自蒸馏预测结构**（比例待与原文核实）。
- 训练时对学生注入噪声（dropout 等）以增强泛化。
- 关联的序列数据库包括 Uniref90、Uniclust30、MGnify，以及 DeepMind 为此构建的 **BFD（Big Fantastic Database，约 22 亿条序列）**。

### 3.3 置信度预测：pLDDT 与 PAE / pTM
模型在输出结构的同时给出自我置信度估计，这是其极具实用价值的一点：
- **pLDDT（predicted LDDT，预测的局部距离差异检验）**：**逐残基** 的局部置信度（0–100），衡量该残基局部结构与真实结构吻合的把握。常用阈值参考：>90 很高、70–90 较好、50–70 较低、<50 很可能是无序/不可靠区。pLDDT 与「内在无序区」高度相关，因而也被当作无序预测工具。
- **PAE（Predicted Aligned Error，预测对齐误差）**：**残基对** 级别的 **全局** 置信度——「若以残基 Y 对齐预测与真实结构，则残基 X 的预期位置误差是多少埃（Å）」。PAE 低表示两残基（或两个结构域）的相对位置可信，常用于判断 **域间排布 / 复合物界面** 是否可靠。
- **pTM（predicted TM-score，预测的模板建模得分）**：对整体结构的 TM-score 的估计（衡量整体折叠相似度），pTM 由 PAE 相关量推导；pTM > 0.5 通常意味着整体折叠大致正确。

---

## 4. 关键结果与数据

> 下表数据均来自实际检索到的来源；标「待核实」者未能在所抓资料中坐实精确值。

| 指标 | 数值 | 说明 / 来源 |
|---|---|---|
| CASP14 域 GDT_TS 中位数 | **约 92.4** | CASP 史上首次达此平均精度（Wikipedia / 多源综述）|
| 高精度域占比（best-of-5） | **87 / 92 域 GDT_TS > 70** | 二手综述 |
| 达实验级精度域（best-of-5） | **58 域 GDT_TS > 90** | 二手综述 |
| 主链 RMSD（结构化区域） | 典型 **约 1.2–1.6 Å** | 二手综述（与原文 r.m.s.d.95 指标的精确对应关系待核实）|
| CASP14 z 分数加总排名 | AlphaFold2 **244.0** vs 次优 **90.8** | 二手综述 |
| 「实验级」阈值参考 | **GDT_TS ≳ 90** | 领域共识 |
| Evoformer block 数 | **48**（权重不共享） | 二手资料，待与原文核实 |
| Structure Module 层数 | **8**（权重共享） | 二手资料，待与原文核实 |
| Recycling 次数 | **3 次** | 二手资料，待与原文核实 |

> 说明：原文衡量主链精度常用 **r.m.s.d.95**（在 95% 残基上对齐后的 Cα RMSD）、全原子精度用侧链 RMSD 等指标。常被引用的「主链 r.m.s.d.95 中位数约 0.96 Å、全原子约 1.5 Å」未能在本次所抓资料中逐字坐实，故此处标注为 **待核实**，请以 Nature 原文 Fig.1/正文为准。

---

## 5. 意义与影响

- **范式转变**：把蛋白质结构预测从「精度远逊实验」推进到「多数情况下接近实验」，被广泛视为 AI for Science 的里程碑（John Jumper 与 Demis Hassabis 因 AlphaFold 与 David Baker 共享 **2024 年诺贝尔化学奖**——背景信息，非本论文内容）。
- **AlphaFold 蛋白质结构数据库（AlphaFold Protein Structure Database, AlphaFold DB）**：DeepMind 与 **EMBL-EBI（欧洲生物信息学研究所）** 合作建立的免费公开数据库（许可 **CC-BY 4.0**）。
  - **2021 年 7 月** 首批发布 **约 35 万（部分来源记为逾 36 万）** 个结构，覆盖人类蛋白组（约 2 万个人类基因编码蛋白）及 **20 个模式生物** 蛋白组（序列取自 UniProt 2021_02）。
  - **2022 年 7 月** 扩展至 **逾 2 亿** 个结构，几乎覆盖 UniProt 中已编目的全部蛋白序列。
  - 数据库用 **pLDDT** 给结构着色以提示可信度；已被 190 多个国家、数百万用户使用。
- **下游应用**：加速结构生物学、药物发现、酶工程、罕见病/疾病机理研究、宏基因组「暗物质」蛋白注释等；并催生 AlphaFold-Multimer、AlphaFold3、ESMFold、OpenFold、RoseTTAFold 等后续工作。
- **开源**：DeepMind 于 **2021 年夏** 开源 AlphaFold v2 代码，并随论文发布约 60 页补充材料，极大降低了复现与二次开发门槛。

---

## 6. 局限与开放问题

AlphaFold2 强大但有明确边界（部分由原作者、部分由后续研究指出）：

- **以单链/单构象为主**：默认预测 **单条多肽链（单体）** 的 **单一构象**，AlphaFold DB 提供的也是单链模型而非生物学相关的 **复合物**。原生 AF2 对 **多链复合物 / 多聚体（multimer）** 支持有限（后由 AlphaFold-Multimer 改进）。
- **构象变化 / 动力学弱**：通常只给一个静态构象，难以同时刻画 **apo/holo** 等多态、别构开关与动态过程；不直接输出系综或动力学。
- **无序区（IDR/IDP）**：对 **内在无序区域** 往往表示为「漂浮」的长延展环；不能预测本就不存在单一固定构象的区域——但 **低 pLDDT 反而是无序的良好指示**。
- **点突变效应不敏感**：由于缺乏突变-结构/能量数据，且模型偏「学模式」而非「算物理力」，AF2 对 **单点突变** 引起的结构/稳定性变化往往不敏感，预测突变效应仅部分成功。
- **依赖 MSA 深度**：对 **缺乏同源序列（浅 MSA）** 的孤儿蛋白、人工设计序列等，精度可能下降。
- **不直接给出折叠机理/通路**：预测的是终态结构，而非折叠过程；「折叠问题」的动力学与复杂体系层面仍属开放问题。
- 复杂体系（如膜蛋白）的不确定性通常会反映在 **PAE** 上，应结合置信度审慎使用。

---

## 7. 关键指标速查

| 项目 | 内容 |
|---|---|
| 论文 | Jumper et al., *Nature* 596, 583–589 (2021)；DOI 10.1038/s41586-021-03819-2 |
| 任务 | 序列 + MSA + 模板 → 全原子 3D 结构（端到端） |
| 核心模块 | Evoformer（MSA + pair，轴向注意力 + 三角更新/三角自注意力） |
| 输出模块 | Structure Module + IPA（不变点注意力），残基刚体框架 → 坐标 |
| 主损失 | FAPE（框架对齐点误差） |
| 关键技巧 | recycling（约 3 次）、self-distillation（noisy-student 半监督）、pLDDT、PAE/pTM |
| CASP14 成绩 | 域 GDT_TS 中位数 **约 92.4**（实验级，史上首次） |
| 置信度 | pLDDT（逐残基局部）、PAE（残基对/全局）、pTM（整体折叠） |
| 数据库 | AlphaFold DB（与 EMBL-EBI 合作，CC-BY 4.0）：2021 约 35 万 → 2022 逾 2 亿结构 |
| 主要局限 | 单链/单构象、复合物/动力学/无序区/点突变较弱 |

---

## 参考来源

- [Highly accurate protein structure prediction with AlphaFold — Nature](https://www.nature.com/articles/s41586-021-03819-2) — 原始论文（CC-BY 4.0），本精读的主依据；本次环境无法直接抓取全文，引用以此为准。
- [PMC 全文 PMC8371605](https://pmc.ncbi.nlm.nih.gov/articles/PMC8371605/) — 论文开放获取全文（PubMed Central），含摘要与方法（本次环境出口策略限制无法直接抓取）。
- [AlphaFold — Wikipedia](https://en.wikipedia.org/wiki/AlphaFold) — CASP14 背景、GDT_TS 92.4、时间线、AlphaFold DB 规模与局限。
- [AlphaFold2 @ CASP14（M. AlQuraishi 博客）](https://moalquraishi.wordpress.com/2020/12/08/alphafold2-casp14-it-feels-like-ones-child-has-left-home/) — CASP14 现场反应与意义评述。
- [The AlphaFold2 Method Paper: A Fount of Good Ideas（M. AlQuraishi）](https://moalquraishi.wordpress.com/2021/07/25/the-alphafold2-method-paper-a-fount-of-good-ideas/) — 架构（Evoformer/IPA/recycling）深度解读。
- [How does DeepMind AlphaFold2 work?（Boris Burkov）](https://borisburkov.net/2021-12-25-1/) — Evoformer、三角注意力、IPA 技术细节。
- [AlphaFold 2 is here: what's behind the structure prediction miracle（OPIG/blopig）](https://www.blopig.com/blog/2021/07/alphafold-2-is-here-whats-behind-the-structure-prediction-miracle/) — 自蒸馏、置信度等训练细节。
- [Strengths and limitations of AlphaFold 2 — EMBL-EBI Training](https://www.ebi.ac.uk/training/online/courses/alphafold/an-introductory-guide-to-its-strengths-and-limitations/strengths-and-limitations-of-alphafold/) — 官方培训材料，局限性权威表述。
- [Glossary of terms / Confidence scores — EMBL-EBI Training](https://www.ebi.ac.uk/training/online/courses/alphafold/glossary-of-terms/) — pLDDT、PAE、pTM 定义。
- [AlphaFold Protein Structure Database — EMBL-EBI](https://alphafold.ebi.ac.uk/) 及 [About](https://alphafold.ebi.ac.uk/about) — 数据库规模、CC-BY 4.0 许可、pLDDT 着色。
- [AlphaFold DB: massively expanding structural coverage（Nucleic Acids Res, PMC8728224）](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8728224/) — 2021 年首发 36 万结构、20 个模式生物。
- [AlphaFold DB in 2024: over 214 million sequences（Nucleic Acids Res）](https://academic.oup.com/nar/article/52/D1/D368/7337620) — 逾 2 亿结构扩展。
- [Applying and improving AlphaFold at CASP14（PMC9299164）](https://pmc.ncbi.nlm.nih.gov/articles/PMC9299164/) — CASP14 应用与改进，z 分数、精度统计。
- [AlphaFold2 and its applications in biology and medicine（Signal Transduct. Target. Ther.）](https://www.nature.com/articles/s41392-023-01381-z) — Evoformer/IPA/自蒸馏/recycling 综述。
