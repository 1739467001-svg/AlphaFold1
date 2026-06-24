# AlphaFold3（Abramson et al., 2024, Nature）开放获取正文提取存档

- **来源 URL（原文）**：https://www.nature.com/articles/s41586-024-07487-w
- **开放获取全文（PMC，最适合抓正文）**：https://pmc.ncbi.nlm.nih.gov/articles/PMC11168924/
- **DOI**：10.1038/s41586-024-07487-w
- **勘误/补充（Addendum）**：Nature 636 (2024-12-12)，DOI 10.1038/s41586-024-08416-7；开放获取（PMC11634763）：https://pmc.ncbi.nlm.nih.gov/articles/PMC11634763/ ；https://www.nature.com/articles/s41586-024-08416-7
- **出处**：Abramson, J., Adler, J., Dunger, J. *et al.* "Accurate structure prediction of biomolecular interactions with AlphaFold 3." *Nature* **630**, 493–500 (2024).
- **作者/主体**：Josh Abramson, Jonas Adler, Jack Dunger, Richard Evans, Tim Green, Alexander Pritzel, Olaf Ronneberger, Lindsay Willmore 等，John Jumper（通讯）；Google DeepMind 与 Isomorphic Labs。
- **在线发表**：2024-05-08。
- **许可**：CC-BY 4.0（Creative Commons Attribution 4.0 International）。原文为 PMC 开放获取，遵循 CC-BY 4.0，允许在署名前提下复制与再利用。Addendum 同为开放获取（CC-BY）。
- **整理日期**：2026-06-24

> **存档性质与重要声明**
> 本文为基于开放获取原文的提取存档，供研究/检索用，正式引用以原文为准。
>
> **抓取限制（务必知悉）**：本次整理所在的运行环境对外网出口实施策略管控，`WebFetch` 对 nature.com、PMC（ncbi.nlm.nih.gov）、europepmc.org、ebi.ac.uk 乃至大多数主机的直接抓取均返回 HTTP 403（CONNECT 被网关拒绝），按环境规则不得绕过。因此 **无法对 CC-BY 原文做逐字（verbatim）全文抓取**。
>
> 下文是以可用的 `WebSearch` 检索结果（含 Nature/PMC 摘要片段、DeepMind 官方 GitHub 文档、多篇技术综述与架构解读）为依据，对原文 **摘要、引言、方法概述、主要结果、讨论** 所做的整理：其中 **「摘要」与带引号的英文句子** 为从原文逐字核对、可信度高的逐字引用；**各章节正文** 为 **忠实转述/概述，并非原文逐字内容**，不应作为逐字引用使用，并已逐处标注性质。需要权威、可逐字引用的文本，请访问上方 URL 阅读原文。凡本整理未能坐实的精确数字，均标注「待核实」。

---

## Abstract（摘要 — 逐字引用，已核对）

> The introduction of AlphaFold 2 has spurred a revolution in modelling the structure of proteins and their interactions, enabling a huge range of applications in protein modelling and design. Here we describe our AlphaFold 3 model with a substantially updated diffusion-based architecture that is capable of predicting the joint structure of complexes including proteins, nucleic acids, small molecules, ions and modified residues. The new AlphaFold model demonstrates substantially improved accuracy over many previous specialized tools: far greater accuracy for protein–ligand interactions compared with state-of-the-art docking tools, much higher accuracy for protein–nucleic acid interactions compared with nucleic-acid-specific predictors and substantially higher antibody–antigen prediction accuracy compared with AlphaFold-Multimer v.2.3. Together, these results show that high-accuracy modelling across biomolecular space is possible within a single unified deep-learning framework.

中文译文（参考）：
> AlphaFold 2 的问世掀起了蛋白质结构及其相互作用建模的一场革命，催生了蛋白质建模与设计领域的大量应用。本文介绍 AlphaFold 3 模型，它采用大幅更新的、基于扩散（diffusion）的架构，能够预测包含蛋白质、核酸、小分子、离子与修饰残基的复合物的联合结构。这一新的 AlphaFold 模型相对许多既有专用工具显著提升了精度：在蛋白–配体相互作用上远超业界领先的对接工具，在蛋白–核酸相互作用上大幅高于核酸专用预测器，在抗体–抗原预测上显著优于 AlphaFold-Multimer v2.3。这些结果共同表明，在单一统一的深度学习框架内，对整个生物分子空间进行高精度建模是可行的。

---

## 1 Introduction（引言 — 结构化提要，含逐字句）

> 性质说明：以下为提要 + 逐字句混排；带引号英文为已核对的逐字片段，其余为转述。

- 动机：AF2 把单链/复合物蛋白结构预测推进到接近实验精度，但生命活动由蛋白质与**核酸、小分子、离子、修饰残基**等多类分子的相互作用构成。AF3 的目标是用**单一统一框架**预测这些异质生物分子复合物的**联合结构**。
- 核心论点（逐字）：模型「is capable of predicting the joint structure of complexes including proteins, nucleic acids, small molecules, ions and modified residues」，并实现「high-accuracy modelling across biomolecular space ... within a single unified deep-learning framework」。
- 相对 AF2 的关键架构转变在引言/方法中点明（逐字）：AF3「directly predicts the raw atom coordinates with a diffusion module, replacing the AF2 structure module that operated on amino-acid-specific frames and side-chain torsion angles」（直接用扩散模块预测原始原子坐标，取代了在「氨基酸专属框架 + 侧链扭转角」上工作的 AF2 结构模块）。
- 该扩散过程的「multiscale nature（多尺度特性）」使网络得以「eliminate stereochemical losses and most special handling of bonding patterns（免去立体化学损失项与对成键模式的大多数特殊处理）」，从而「easily accommodating arbitrary chemical components（轻松容纳任意化学组分）」。

---

## 2 Methods / Architecture（方法 / 架构 — 结构化提要）

> 性质说明：本节为基于 DeepMind 官方代码文档与公开权威解读的转述提要，非原文逐字全文。原文方法细节（含补充材料 Algorithm 伪代码）请见 PMC11168924 与论文 Supplementary Information。

**总体数据流**：输入特征构建（token 化）→ 模板/MSA 轻量注入 → Pairformer 主干精炼 single/pair 表征 → 扩散模块从噪声直接生成全原子坐标 → 置信度头输出 pLDDT/PAE/PDE 等。

**2.1 输入与 token 化**
- 所有实体统一为 token 序列；标准氨基酸/核苷酸以残基为 token，配体/离子/修饰基团以原子级 token 展开，使框架可表达任意化学结构。
- MSA 与模板仍使用，但仅作为辅助信息经轻量 MSA 模块注入成对表征，主干对 MSA 的依赖大幅下降。

**2.2 Pairformer（取代 Evoformer）**
- 主干由 **48 个 Pairformer 块**组成（不共享权重）。
- 关键改动：从主干中**移除 MSA 表征**，仅迭代精炼 **single（单体）+ pair（成对）** 两套表征；保留三角乘法 / 三角注意力（triangle multiplication / triangle attention）作用于 pair 表征以维持几何自洽。
- 设计意图：降低对 MSA / 共进化信号的依赖，简化主干，便于推广到非蛋白对象。

**2.3 Diffusion module（取代 Structure Module / IPA）**
- 用去噪扩散（denoising diffusion）模型**直接生成每个原子的笛卡尔坐标**，不再使用残基局部框架与扭转角参数化，也不强制等变网络。
- 训练时向真实坐标加高斯噪声并学习去噪；推理时从纯噪声多步迭代采样出结构，属**生成式采样**，支持多随机种子产生多候选。
- 多尺度噪声分工：低噪声水平精修局部/化学细节，高噪声水平决定全局排布与界面取向。
- 物理合理性：对立体冲突（clash）、不合理键长/扭转角施加惩罚；手性问题通过在**候选排序公式中加入手性违反惩罚**部分缓解。

**2.4 抗幻觉：交叉蒸馏（cross-distillation）**
- 用 AlphaFold-Multimer v2.3 / AlphaFold2 的预测结构扩充训练集。AF2 体系在无序区通常给出伸展长 loop（ribbon 状），AF3 借此学会在无序区也给出舒展、低置信度表示，从而**降低扩散导致的幻觉**。

**2.5 置信度头与排序**
- 训练中通过扩散 rollout（公开解读称约 **20 步**去噪）得到结构并与真值比较，训练置信度头。
- 输出：**pLDDT**（逐原子/残基局部置信度，0–100）、**PAE**（相对位置/界面误差，埃）、**PDE**（残基间距离误差，埃）、**pTM/ipTM**（全局/界面 TM-score 估计）。
- **ranking_score**：综合 pTM、ipTM、fraction_disordered、has_clash 等给出标量（公开文档区间约 [-100, 1.5]）用于多候选排序选优。

---

## 3 Results（结果 — 结构化提要，含数值；数值标注可信度）

> 性质说明：以下数值经多来源交叉核对，非原文逐字。带「待核实」者不同来源口径略有差异，请回原文图表核实。

- **蛋白–配体（PoseBusters）**：相对业界领先对接工具约 **50%** 相对精度提升，且**无需输入任何结构信息**。PoseBusters V1 成功率约 **76.4%**（ligand RMSD < 2 Å）；整体/跨 V1–V2 约 **80%**（待核实）。评测集含 **428** 个蛋白–配体结构（用 2021 年后入库部分做无泄漏评测）。
- **蛋白–蛋白界面**：DockQ > 0.23 成功率，AF3-server **78.2%（161/206）** vs AlphaFold-Multimer **71.8%（148/206）**（单一来源口径，待核实）。
- **抗体–抗原**：显著优于 AlphaFold-Multimer v2.3（逐字：「substantially higher antibody–antigen prediction accuracy」）。
- **蛋白–核酸**：大幅优于核酸专用预测器（逐字：「much higher accuracy for protein–nucleic acid interactions」）。RNA 方面优于 RoseTTAFold2NA；在 CASP15 RNA 上不及当时最佳的 AIchemy_RNA2（待核实）。
- **共价修饰 / 键合配体**：可准确预测糖基化、键合配体、修饰的蛋白残基与核酸碱基等，适用于任意聚合物残基。
- **手性违反率（PoseBusters）**：约 **4.4%**。

---

## 4 Discussion / Limitations（讨论 / 局限 — 结构化提要）

> 性质说明：转述提要，非原文逐字。

- **手性**：输出不总遵守手性（PoseBusters 约 4.4% 违反），排序惩罚仅部分缓解。
- **立体冲突（clash）**：大体系可能出现原子重叠；ranking_score 的 has_clash 项用于筛除严重冲突。
- **动态与化学计量**：输出单一静态结构，忽略动态本质；多 seed 也不能近似真实动态系综；金属结合等体系对化学计量比与配位环境泛化有限。
- **幻觉（hallucination）与无序区**：生成式扩散可能在本应无序区域「编造」有序结构（如 α 螺旋/紧凑团块），而非 AF2 的 ribbon 状无序外观；幻觉区**通常**以很低置信度标注，需结合置信度指标识别。训练上以交叉蒸馏缓解。

---

## 5 Addendum（勘误/补充 — 要点摘录）

**Addendum: Accurate structure prediction of biomolecular interactions with AlphaFold 3.** Nature 636 (2024-12-12). DOI: 10.1038/s41586-024-08416-7（开放获取，PMC11634763）。

要点（转述）：在 AlphaFold 模型基础上**引入若干新指标**，用于**识别可靠的多结构域（multi-domain）预测**，以及**识别可能无序（likely disordered）的区域**——为「如何判断/标注无序、避免被扩散幻觉误导」提供更明确的度量与实践指引。配合多随机种子采样与 ranking_score / pLDDT / PAE 排序筛选使用。

---

## 数据与代码可获得性（原文 Data/Code availability 对应信息）

- **AlphaFold Server**：2024-05-08 上线，https://alphafoldserver.com ，免费、仅**非商业**，配体与共价修饰为**有限子集**。
- **代码**：2024 年 11 月在 GitHub 发布推理流水线，https://github.com/google-deepmind/alphafold3 ，许可 **Apache-2.0**。
- **模型权重**：2025 年 2 月起向学术界开放（需填表申请、由 DeepMind 酌情批准），受 **AlphaFold 3 Model Parameters Terms of Use** 与 Prohibited Use Policy 约束，仅**非商业**，且「You may only use AlphaFold 3 model parameters if received directly from Google」。
- **免责声明（逐字）**：「AlphaFold 3 and its output are for theoretical modeling only. They are not intended, validated, or approved for clinical use.」
- 注：本文（主刊）初次发表时未同步公开代码/权重，曾引发学术界对可复现性的关注（见 Nature 评论 d41586-024-01463-0 与 d41586-024-03708-4）。

---

## 引用本文（建议）

Abramson, J., Adler, J., Dunger, J. et al. Accurate structure prediction of biomolecular interactions with AlphaFold 3. *Nature* **630**, 493–500 (2024). https://doi.org/10.1038/s41586-024-07487-w

---

*存档生成：2026-06-24。本文档为研究/检索辅助用途的提取存档，因出口策略限制未能逐段抓取 PMC 全文；逐字内容已加引号标注，其余为忠实转述。任何正式用途请以 https://pmc.ncbi.nlm.nih.gov/articles/PMC11168924/ 的开放获取原文（CC BY 4.0）为准。*
