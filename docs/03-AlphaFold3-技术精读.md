---
标题: AlphaFold3 技术精读
英文原题: Accurate structure prediction of biomolecular interactions with AlphaFold 3
作者/主体: Josh Abramson, Jonas Adler, Jack Dunger, Richard Evans, Tim Green, Alexander Pritzel, Olaf Ronneberger, Lindsay Willmore 等，John Jumper（通讯）；Google DeepMind 与 Isomorphic Labs
发表/来源: Nature 630, 493–500 (2024)
DOI/标识: 10.1038/s41586-024-07487-w
原文链接: https://www.nature.com/articles/s41586-024-07487-w
勘误/补充: Addendum, Nature 636 (2024-12-12), DOI 10.1038/s41586-024-08416-7
开放获取: 是（CC-BY 4.0）
整理日期: 2026-06-24
---

# AlphaFold3 技术精读

> AlphaFold3（2024）把建模对象从「单链/蛋白复合物结构」扩展为「任意生物分子复合物的联合结构」，用 Pairformer 取代 Evoformer 以弱化对 MSA 的依赖，用扩散模块（diffusion）直接在原子坐标上生成结构以取代 IPA/Structure Module，从而在单一统一框架内统一预测蛋白质、核酸、小分子配体、离子与修饰残基。
>
> 关联阅读：本知识库 AlphaFold2 篇（《Highly accurate protein structure prediction with AlphaFold》, Jumper et al., 2021, Nature 596）。本篇聚焦 AF3 相对 AF2 的范式转变、Pairformer + 扩散（diffusion）新架构、能力扩展与已知局限。
>
> **关于来源的说明**：本精读所引数据均来自整理者实际检索到的公开来源（见文末「参考来源」）。受本次运行环境的网络出口策略限制，无法对 Nature 原文与 PMC 全文做逐字抓取，关键指标均来自可访问来源（DeepMind AlphaFold3 GitHub 官方文档、公开技术综述/解读、检索摘要）交叉核对；凡无法在所抓资料中坐实的精确数字标注「待核实」。正式引用请以 Nature 原文与 Addendum 为准。

---

## 1. 背景与范式转变

### 1.1 从「单链结构预测」到「生物分子复合物联合结构预测」

AlphaFold2（2021）解决的核心问题是：给定单条蛋白质氨基酸序列，预测其三维折叠结构。它依赖深度多序列比对（MSA）所携带的共进化信号，通过 Evoformer 提炼成对（pair）表征，再由结构模块（Structure Module，基于不变点注意力 IPA）输出每个残基的骨架坐标与侧链扭转角。AF2 及其扩展 AlphaFold-Multimer 把蛋白质单体/复合物结构预测推进到接近实验精度，但其建模对象本质上仍是「氨基酸聚合物」。

AlphaFold3 的范式转变在于：把预测对象从「单一蛋白链/蛋白复合物」扩展为**任意生物分子复合物的联合结构（joint structure of complexes）**，在同一框架内统一处理蛋白质、核酸（DNA/RNA）、小分子配体（ligand）、离子（ion）与修饰残基（modified residues，如翻译后修饰 PTM、糖基化、核酸碱基修饰）。论文标题即点明主题——「biomolecular interactions（生物分子相互作用）」，强调的是分子**之间**的界面与相互作用，而不仅是分子内部的折叠。

> 官方摘要要点（交叉核对自检索结果，措辞接近原文）：
> AlphaFold3 采用「substantially updated diffusion-based architecture（大幅更新的、基于扩散的架构）」，能够「predict the joint structure of complexes including proteins, nucleic acids, small molecules, ions and modified residues（预测包含蛋白质、核酸、小分子、离子与修饰残基的复合物联合结构）」。

### 1.2 为什么需要新架构

AF2 体系存在两个结构性约束，限制了它向「全生物分子」推广：

1. **强依赖 MSA / 共进化信号。** Evoformer 的输入与计算重心是 MSA 表征。对没有同源序列库（如小分子、离子、合成配体、许多 RNA）或共进化信号弱的对象，这条路径难以直接复用。
2. **以残基「框架（frame）+ 扭转角」为输出的几何参数化。** Structure Module/IPA 把每个残基表示为一个刚体局部坐标系并预测其位姿，这套参数化是为标准氨基酸/核苷酸量身定制的，难以自然地表达任意化学结构（任意原子连接、任意配体）。

AF3 用两处替换回应上述约束：用 **Pairformer** 弱化对 MSA 的依赖；用**扩散模块直接在原子坐标上生成结构**，摆脱残基框架/扭转角参数化，从而能对任意原子化学结构统一建模。

---

## 2. 核心架构：Pairformer + Diffusion

AF3 的整体数据流可概括为三段：**输入嵌入与表征构建 → Pairformer 主干（trunk）精炼成对/单体表征 → 扩散模块（diffusion）从噪声直接生成原子坐标**，最后由置信度头输出 pLDDT/PAE/PDE 等可靠性指标。

### 2.1 输入与 token 化（相对 AF2 的差异）

- AF3 把所有实体统一为 **token 序列**。标准氨基酸/核苷酸通常以「残基」为一个 token；而配体、离子、以及非标准/修饰化学基团则以**原子级别**展开为 token。这种「混合粒度 token 化」使框架可以容纳任意化学结构。
- MSA 与模板（template）仍然使用，但只作为**辅助信息**经一个轻量的 MSA 模块注入成对表征，整体对 MSA 的处理量与依赖显著下降（见 2.2）。

### 2.2 Pairformer 取代 Evoformer

| 维度 | AF2 Evoformer | AF3 Pairformer |
|---|---|---|
| 主要表征 | MSA 表征 + 成对（pair）表征 | **单体（single）表征 + 成对表征**，去掉了贯穿主干的 MSA 表征 |
| 对 MSA 的处理 | 主干核心，逐块更新 MSA | 仅前端轻量 MSA 模块汇总后注入 pair；主干不再携带完整 MSA |
| 块数 | 48 个 Evoformer 块 | 48 个 Pairformer 块（不共享权重） |
| 核心算子 | 行/列注意力 + 三角更新（triangle multiplication / triangle attention） | 保留三角更新/三角注意力作用于 pair；以 single 表征替代 MSA 在主干中的角色 |
| 设计意图 | 充分挖掘共进化信号 | 降低 MSA 依赖、简化主干、便于推广到非蛋白对象 |

要点：Pairformer 的关键改动是**把「MSA 表征」从主干中移除**，主干只迭代精炼「single + pair」两套表征；MSA 的信息在进入主干前由一个较小的 MSA 模块处理并写入 pair 表征。三角乘法/三角注意力这一 AF2 的核心几何一致性算子被保留，用以在 pair 表征上传播「i–j–k 三点距离约束应自洽」的几何先验。

### 2.3 扩散模块取代 Structure Module / IPA

这是 AF3 最具范式意义的改动：**不再用 IPA 预测残基框架与扭转角，而是用一个去噪扩散（denoising diffusion）模型，直接在三维空间中生成每个原子的坐标。**

工作方式（交叉核对自官方文档与公开解读）：

- **生成式去噪。** 训练时向真实结构的原子坐标加高斯噪声，扩散模块学习从带噪坐标回归/去噪出真实坐标；推理时从纯噪声出发，经多步迭代去噪「采样」出一个完整结构。这与 AF2「一次前向回归出确定结构」不同，AF3 是**生成式采样**，天然支持用不同随机种子（seed）产生多个候选构象并排序。
- **多尺度噪声分工。** 扩散在不同噪声水平上承担不同任务：**低噪声**水平主要修整局部/化学细节（键长、键角、局部堆叠），**高噪声**水平主要决定全局排布（domain 间相对取向、复合物界面）。
- **直接作用于原子、无需等变框架。** 扩散模块直接输出原子笛卡尔坐标，**不需要 AF2 那套残基局部坐标系（frame）与扭转角参数化**，也不强制使用等变（equivariant）网络；几何一致性更多依靠数据与训练（含数据增强/随机旋转平移）习得。这正是 AF3 能统一表达任意配体/离子/修饰化学结构的关键。
- **物理合理性约束。** 候选结构若出现立体冲突（clash，原子间距小于范德华半径）、不合理键长或扭转角，会在评分/训练中被惩罚，从而引导扩散学到更符合化学物理的分布。
- **手性的处理。** 模型虽然以带正确手性的参考结构作为输入特征，但扩散输出并不总是遵守手性；为此在候选模型的**排序公式中加入了手性违反（chirality violation）惩罚**项（仍未能完全消除，见第 5 节）。

> 直观对比：AF2 的结构模块像「按残基拼装乐高骨架再装侧链」；AF3 的扩散模块更像「从一团噪声里逐步雕刻出整套原子坐标」，因此可以雕刻蛋白、核酸、配体、离子——只要它们都被表示成原子/token。

### 2.4 缓解扩散带来的「幻觉」：交叉蒸馏（cross-distillation）

生成式扩散的一个副作用是**幻觉（hallucination）**：在本应无序（disordered）或缺乏约束的区域，模型可能「编造」出看似合理、实则虚假的折叠（如杂乱二级结构、紧凑团块）。AF3 的应对手段是**交叉蒸馏**：用 AlphaFold-Multimer v2.3 / AlphaFold2 预测的结构来扩充训练数据。由于 AF2 体系在无序区通常给出「伸展长 loop（extended/ribbon-like loop）」而非紧凑结构，AF3 通过模仿这种行为，学会在无序区也倾向给出舒展、低置信度的表示，从而**降低幻觉**。该机制在原文与 Addendum 的讨论中均有体现（详见第 5 节）。

### 2.5 置信度头与排序

AF3 通过一个**扩散 rollout**（训练中模拟完整的多步去噪，公开解读称约 20 步）得到预测结构，再与真值比较，用于训练置信度头预测各类可靠性指标：

- **pLDDT**：逐原子/逐残基的局部置信度，0–100，越高越可信（>90 高置信，<50 多半不可靠）。
- **PAE（Predicted Aligned Error，预测对齐误差）**：两实体相对位置的置信度，反映 token i 相对 token j 的位置误差（埃），值越大置信越低；用于判断**界面/相对取向**是否可信。
- **PDE（Predicted Distance Error，预测距离误差）**：聚焦残基间**距离**的置信度，值越低表示距离预测越精确。
- **pTM / ipTM**：全局/界面的 TM-score 估计；ipTM 常被用作评估异源复合物界面质量的最可靠指标之一。
- **ranking_score（排序分数）**：综合 pTM、ipTM、无序比例（fraction_disordered）、是否存在 clash（has_clash）等，给出一个标量（公开文档给出取值区间约 [-100, 1.5]）用于在多个采样候选中排序选优。手性违反惩罚也并入排序逻辑。

---

## 3. 能力与适用范围

AF3 在**单一统一模型**内支持以下实体及其任意组合的联合结构预测：

| 实体类别 | 说明 | 备注 |
|---|---|---|
| 蛋白质 | 单体与多聚体（同源/异源复合物） | 取代/涵盖 AlphaFold-Multimer 场景 |
| 核酸 | DNA、RNA（单链/双链、与蛋白复合） | 较核酸专用预测器精度更高（见第 4 节） |
| 蛋白–配体（小分子） | 无需提供口袋/对接先验，端到端联合预测 | PoseBusters 基准上超越传统对接工具 |
| 离子 | 金属/无机离子及其配位 | 配位环境与化学计量泛化仍有限（见第 5 节） |
| 修饰残基 / 共价修饰 | PTM、糖基化、修饰的蛋白残基与核酸碱基、键合配体（bonded ligand） | 可作用于任意聚合物残基（蛋白/RNA/DNA） |

适用边界（重要）：
- AF3 给出的是**单一、静态**的「最可能」结构快照，不直接给出构象系综或热力学权重；多 seed 采样能给出若干候选，但**不等于**真实动态分布（见第 5 节）。
- AlphaFold **Server** 版仅支持**有限的配体与共价修饰子集**，能力小于完整代码/权重版本。

---

## 4. 关键结果与数据

> 下表数字来自可访问来源交叉核对（DeepMind 官方仓库文档、公开技术综述、检索摘要）。凡未能二次确认者标「待核实」。原始权威数值以 Nature 原文图表为准。

### 4.1 头条性能主张

| 任务 | AF3 表现 | 对照基线 | 来源可信度 |
|---|---|---|---|
| 蛋白–配体（PoseBusters） | 约 **50% 相对提升**；不需任何结构输入信息 | 业界领先对接工具（state-of-the-art docking） | 摘要级，多来源一致 |
| 蛋白–核酸 | 「much higher accuracy（精度高得多）」 | 核酸专用预测器 | 摘要级 |
| 抗体–抗原 | 「substantially higher（显著更高）」 | AlphaFold-Multimer v2.3 | 摘要级 |

任务说明中的「至少约 50%」是原文对**分子间相互作用**精度提升的标志性表述（以蛋白–配体对接为代表场景）。

### 4.2 具体基准数字（交叉核对）

| 指标 | 数值 | 含义 | 标注 |
|---|---|---|---|
| PoseBusters V1 成功率 | **76.4%**（ligand RMSD < 2 Å） | 蛋白–配体对接位姿正确率 | 多来源一致，建议以原文复核 |
| PoseBusters 成功率（整体/V2 语境） | 约 **80%** | 同上，跨 V1/V2 提升 | 待核实（不同来源口径略有差异） |
| PoseBusters 数据集规模 | **428** 个蛋白–配体结构（2021 年后入库部分用于无泄漏评测） | 评测集 | 多来源一致 |
| 蛋白–蛋白界面成功率（DockQ > 0.23） | AF3-server **78.2%（161/206）** vs AF-Multimer **71.8%（148/206）** | 复合物界面建模成功比例 | 单一来源口径，待核实 |
| 手性违反率（PoseBusters） | **4.4%** | 输出违反手性的比例 | 见第 5 节 |
| RNA（CASP15 语境） | 优于 RoseTTAFold2NA；整体不及 CASP15 最佳的 AIchemy_RNA2 | RNA 单体结构预测对比 | 待核实（口径/子集敏感） |

### 4.3 置信度指标速览（与 4 节配合，详定义见 2.5）

| 指标 | 范围 | 用途 |
|---|---|---|
| pLDDT | 0–100（越高越好） | 局部（逐原子/残基）置信度 |
| PAE | 埃（越低越好） | 相对位置 / 界面取向置信度 |
| PDE | 埃（越低越好） | 残基间距离置信度 |
| pTM / ipTM | 0–1（越高越好） | 全局 / 界面 TM-score 估计 |
| ranking_score | 约 [-100, 1.5] | 多候选排序选优（含 clash、无序比例、手性惩罚） |

---

## 5. 局限与争议（含 Addendum）

### 5.1 手性（chirality）错误
尽管输入特征提供了正确手性的参考结构，AF3 输出**并不总是遵守手性**，在 PoseBusters 基准上手性违反率约 **4.4%**。论文以排序阶段的手性惩罚部分缓解，但未根除。对手性敏感的药物化学场景需人工复核。

### 5.2 原子重叠 / 立体冲突（clash）
对**大体系/大蛋白**，AF3 可能产生原子部分重叠（clash），即物理上不可能的相互穿插。ranking_score 中的 has_clash 项用于筛除严重冲突候选，但不能保证完全无冲突。

### 5.3 动态与化学计量比的局限
- **静态快照**：AF3 输出单一静态结构，**忽略分子相互作用的动态本质**；即便对扩散头或整体网络使用多随机种子，也**不能近似真实的动态系综**。
- **化学计量 / 配位泛化**：在金属结合等体系，AF3 对**化学计量比与独特配位环境**的泛化能力有限。

### 5.4 幻觉（hallucination）与无序区
这是生成式扩散架构最受关注的副作用，也是 **Addendum** 的核心议题之一。

- **现象**：在本应**无序（disordered）/无结构**的区域，AF3 可能「幻觉」出貌似合理的有序结构（如 α 螺旋等二级结构、紧凑团块），而非 AF2 那种标志性的「伸展 ribbon 状」无序表示。也就是说，**无序区可能被错误地渲染成有序结构**。
- **可识别性**：这些幻觉区域**通常**被标注为**很低的置信度**，因此置信度指标是识别它们的主要手段；但其外观可能不像 AF2 那样一眼可辨（不再是松散 ribbon），需结合 pLDDT 等指标判断。
- **缓解**：训练上用**交叉蒸馏**（模仿 AF2/AF-Multimer 在无序区的伸展 loop 行为）压低幻觉（见 2.4）。

> **Addendum（勘误/补充）**：*Addendum: Accurate structure prediction of biomolecular interactions with AlphaFold 3*，Nature 卷 636（2024 年 12 月 12 日在线），DOI **10.1038/s41586-024-08416-7**（开放获取 PMC11634763）。其要点是：在 AF3 模型基础上**引入若干新指标**，用于**识别可靠的多结构域（multi-domain）预测，以及识别可能无序（likely disordered）的区域**——即为「如何判断/标注无序、避免被幻觉误导」提供了更明确的度量与实践建议。
>
> 实践建议（综合原文/Addendum 与社区共识）：对关键预测使用**多个随机种子**采样、依据 **ranking_score / pLDDT / PAE** 排序与筛选，并对低置信度区域保持审慎，不要把幻觉出的有序结构当作真实折叠。

### 5.5 可及性争议
AF3 发布初期**未同时开源代码与权重**（仅提供受限的 AlphaFold Server），引发学术界对可复现性的批评（如《Science》报道的 backlash）。后续 DeepMind 分阶段放开代码与权重（见第 6 节），但仍限**非商业**用途。

---

## 6. 可获得性与生态（Server、开源、商用）

| 里程碑 | 时间 | 内容 | 限制 |
|---|---|---|---|
| 论文发表 + AlphaFold Server 上线 | **2024-05-08** | Google DeepMind 与 Isomorphic Labs 联合发布 AF3；同时上线 alphafoldserver.com 提供免费在线预测 | 仅**非商业**；配体/共价修饰为**有限子集** |
| 推理代码开源 | **2024-11**（约 11 月） | 在 GitHub 发布 AF3 推理流水线代码 | 代码采 **Apache-2.0**；权重需另行申请 |
| 模型权重开放 | **2025-02**（约 2 月起，需申请获批） | 向学术界开放模型参数（需填表、由 DeepMind 酌情批准） | 权重受 **AlphaFold 3 Model Parameters Terms of Use** 约束，仅非商业 |

许可与商用要点（来自官方 GitHub 文档）：
- **代码**：Apache License 2.0。
- **权重**：单独的「AlphaFold 3 Model Parameters Terms of Use」+「Prohibited Use Policy」。仅**大学、非营利组织、研究院所、教育/新闻/政府机构**可用于**非商业**目的；「**You may only use AlphaFold 3 model parameters if received directly from Google**」（不得转手分发给无资格方）。禁止用于商业活动、用输出训练同类模型、误导性用途等。
- **AlphaFold Server**：alphafoldserver.com，仅非商业；配体与共价修饰能力小于完整版本。
- **免责声明**：仅供理论建模，「not intended, validated, or approved for clinical use（不用于、未验证、未批准临床用途）」。

与 **Isomorphic Labs** 的关系：AF3 由 **Google DeepMind 与 Isomorphic Labs 共同开发**。Isomorphic Labs 是 DeepMind 的药物研发衍生公司（spin-off），将 AF3 用于其药物发现管线——这也是 AF3 权重对商业用途严格设限、而把在线服务/学术权重与商业药物研发分轨的背景原因。

---

## 7. 关键指标速查

| 项目 | 内容 |
|---|---|
| 论文 | Abramson et al., *Accurate structure prediction of biomolecular interactions with AlphaFold 3*, Nature **630**, 493–500 (2024) |
| DOI | 10.1038/s41586-024-07487-w |
| Addendum | Nature **636** (2024-12-12), DOI 10.1038/s41586-024-08416-7 |
| 开放获取 | 是（CC BY 4.0；PMC11168924） |
| 核心架构改动 | Evoformer → **Pairformer**（去 MSA 主干、48 块）；Structure Module/IPA → **扩散模块**（直接生成原子坐标） |
| 对 MSA 依赖 | 显著降低（MSA 仅前端轻量注入 pair） |
| 支持实体 | 蛋白、DNA/RNA、小分子配体、离子、修饰残基/共价修饰（统一框架） |
| 头条性能 | 蛋白–配体（PoseBusters）约 **50% 相对提升**，无需结构输入 |
| PoseBusters 成功率 | V1 **76.4%**；整体约 **80%**（待核实），数据集 428 结构 |
| 蛋白–蛋白界面 | DockQ>0.23 成功率 **78.2%** vs AF-Multimer **71.8%**（单来源，待核实） |
| 抗体–抗原 | 显著优于 AlphaFold-Multimer v2.3 |
| 置信度指标 | pLDDT、PAE、PDE、pTM/ipTM、ranking_score(约[-100,1.5]) |
| 主要局限 | 手性违反（约 4.4%）、clash、无动态/系综、化学计量与配位泛化弱、无序区**幻觉** |
| 抗幻觉机制 | 与 AF2/AF-Multimer **交叉蒸馏** + 低置信度标注 + 多 seed/排序筛选 |
| 发布 | 2024-05-08（论文 + Server）；代码 2024-11；权重 2025-02（学术、非商业、需申请） |
| 许可 | 代码 Apache-2.0；权重 Model Parameters Terms of Use（仅非商业，须直接获自 Google） |
| 开发方 | Google DeepMind + Isomorphic Labs |

---

## 参考来源

- Abramson J., et al. *Accurate structure prediction of biomolecular interactions with AlphaFold 3.* Nature 630, 493–500 (2024). DOI: 10.1038/s41586-024-07487-w. 开放获取全文：https://pmc.ncbi.nlm.nih.gov/articles/PMC11168924/ ；https://www.nature.com/articles/s41586-024-07487-w
- *Addendum: Accurate structure prediction of biomolecular interactions with AlphaFold 3.* Nature 636 (2024-12-12). DOI: 10.1038/s41586-024-08416-7. 开放获取：https://pmc.ncbi.nlm.nih.gov/articles/PMC11634763/ ；https://www.nature.com/articles/s41586-024-08416-7
- Google DeepMind, AlphaFold 3 官方代码库（README / docs / output.md / known_issues.md / WEIGHTS_TERMS_OF_USE.md / Prohibited Use Policy）：https://github.com/google-deepmind/alphafold3
- Google DeepMind / Isomorphic Labs 发布公告（2024-05-08）：https://blog.google/innovation-and-ai/products/google-deepmind-isomorphic-alphafold-3-ai-model/ ；https://www.isomorphiclabs.com/articles/alphafold-3-predicts-the-structure-and-interactions-of-all-of-lifes-molecules
- EMBL-EBI AlphaFold 在线课程（AF3 工作原理 / 局限 / 验证 / 质量评估）：https://www.ebi.ac.uk/training/online/courses/alphafold/
- Oxford Protein Informatics Group, "Architectural highlights of AlphaFold3"（架构解读）：https://www.blopig.com/blog/2024/08/architectural-highlights-of-alphafold3/
- 关于可及性争议：M. Hutson, "Limits on access to DeepMind's new protein program trigger backlash," Science (2024)：https://www.science.org/content/article/limits-access-deepmind-s-new-protein-program-trigger-backlash

> 注：撰写时上述 Nature/PMC/EBI/Wikipedia 等站点在本会话出口策略下不可直接抓取，正文数字经多来源交叉核对，建议读者对带「待核实」标记的具体数值回原文图表核实。
