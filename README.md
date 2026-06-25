# AlphaFold 蛋白质折叠知识库

> 关于 **AlphaFold / 蛋白质结构预测** 的最新进展、论文精读与综合分析。
> 中文整理，配套可一键生成的 PDF。整理日期：**2026-06-24**。

本仓库是一份系统化的中文知识库，覆盖 AlphaFold 从第一代到 AlphaFold3 的技术演进、2024 年诺贝尔化学奖、2025–2026 最新动态、生态竞品对比，以及一篇综合分析与展望。每篇文档都可渲染为排版精良、支持中文的 PDF。

## 📁 目录结构

```
AlphaFold1/
├── README.md                  # 本导航页
├── docs/                      # 中文文档（精读 + 分析）
│   ├── 01-总览与时间线.md
│   ├── 02-AlphaFold2-技术精读.md
│   ├── 03-AlphaFold3-技术精读.md
│   ├── 04-2024诺贝尔化学奖.md
│   ├── 05-2025-2026最新动态与五周年.md
│   ├── 06-生态与竞品对比.md
│   └── 07-综合分析与展望.md
├── sources/                   # 开放获取原文的结构化摘录（含官方原文直链）
│   ├── AlphaFold2_Jumper2021_Nature_开放获取原文.md
│   └── AlphaFold3_Abramson2024_Nature_开放获取原文.md
├── pdf/                       # 渲染输出（每篇一个 PDF + 合订本）
├── tools/
│   └── build_pdf.py           # Markdown → PDF 渲染脚本（weasyprint，支持中文）
├── scripts/
│   └── daily_digest.py        # 每日进展摘要生成器（Claude 联网搜索）
├── daily/                     # 🔄 每日自动更新的进展摘要（MD+PDF）+ 分类索引
└── .github/workflows/
    └── alphafold-daily.yml    # 每天 10:11(北京时间) 定时任务
```

## 📖 文档导读

| # | 文档 | 一句话简介 |
|---|------|-----------|
| 01 | [总览与时间线](docs/01-总览与时间线.md) | 蛋白质折叠问题背景、AlphaFold 版本演进与完整时间线、术语速查 |
| 02 | [AlphaFold2 技术精读](docs/02-AlphaFold2-技术精读.md) | Evoformer + Structure Module（IPA）架构、CASP14 突破、训练技巧 |
| 03 | [AlphaFold3 技术精读](docs/03-AlphaFold3-技术精读.md) | Pairformer + 扩散模块、复合物/配体/核酸预测、可获得性与局限 |
| 04 | [2024 诺贝尔化学奖](docs/04-2024诺贝尔化学奖.md) | Baker / Hassabis / Jumper 获奖，颁奖理由与意义 |
| 05 | [2025–2026 最新动态与五周年](docs/05-2025-2026最新动态与五周年.md) | 五年影响量化、AF3 演进、构象系综与 de novo 设计两大新前沿、商业化 |
| 06 | [生态与竞品对比](docs/06-生态与竞品对比.md) | ESMFold/OpenFold/Boltz/Chai/Protenix 等横向对比，开源 vs 闭源之争 |
| 07 | [综合分析与展望](docs/07-综合分析与展望.md) | 跨文档的趋势提炼、影响评估、争议与未来判断 |

> 建议阅读顺序：先看 **01 总览** 建立全局，再按兴趣深入 **02/03 技术精读** 或 **05/06 动态与生态**，最后读 **07 综合分析**。

## 📄 原文（sources/）

`sources/` 收录两篇核心论文（AlphaFold2、AlphaFold3，均为开放获取 CC-BY）的**结构化要点摘录**，并在每篇开头给出官方开放获取原文的**直链**，便于一键跳转阅读逐字原文。

> ⚠️ **关于"抓取原文"的说明**：本整理环境的组织出网策略对学术出版站点（`nature.com`、PubMed Central、`arxiv.org`、Wikipedia 等）的直接抓取一律返回 **HTTP 403**，因此无法将期刊原始 PDF 逐字下载入库。`sources/` 中的内容是基于权威检索结果的**忠实转述与结构化整理**（非逐字原文），正式引用与精确数据请以官方原文为准（链接已提供）。

## 🛠️ 生成 / 重建 PDF

PDF 已生成在 `pdf/`。如需重新生成：

```bash
# 安装依赖（pypi 直连可用）
pip install weasyprint markdown pygments

# 渲染 README + docs/ + sources/ 全部文档到 pdf/
python3 tools/build_pdf.py

# 额外生成一本合订本 pdf/AlphaFold知识库-合订本.pdf
python3 tools/build_pdf.py --combined

# 只渲染指定文件
python3 tools/build_pdf.py docs/01-总览与时间线.md
```

渲染使用系统自带的**文泉驿正黑**字体，中文显示正常；PDF 含书签大纲、页码与可点击链接。

## 🔍 来源、方法与约定

- **方法**：内容由多路 Web 检索的权威来源（Nature、DeepMind、诺贝尔基金会官网、MIT Tech Review、各模型 GitHub/论文等）交叉核实后整理，并标注参考链接。
- **「待核实」约定**：凡在不同来源间存在口径差异、或无法从一手来源直接确证的精确数字/细节，文中均显式标注「**待核实**」，请勿不加核对地引用。
- **时效**：知识截至 **2026-06**。AlphaFold 与相关生态演进很快，使用时请以最新官方信息为准。
- **版权**：本知识库为研究 / 学习用途的二次整理；论文原文版权归原作者与出版方所有，请通过文中官方链接获取与引用。

## 📌 关键事实速览

- AlphaFold2 在 **CASP14（2020）** 上 GDT_TS 中位数约 **92.4**，达到实验级精度，被认为基本解决了约 50 年的"蛋白质折叠问题"。
- **AlphaFold 蛋白质结构数据库**已收录 **2 亿+** 预测结构，服务全球数百万研究者。
- **AlphaFold3（2024-05）** 用 **Pairformer + 扩散模块** 把预测从单链扩展到蛋白质–核酸–配体–离子复合物。
- **2024 诺贝尔化学奖**授予 David Baker、Demis Hassabis、John Jumper。
- 2024–2026 涌现一批**开源、商用友好**的对标模型（Boltz、Chai、Protenix、OpenFold3 等），正面回应 AF3 的非商业限制。

## 🔄 每日自动更新（daily/）

仓库内置一个**每天自动跑**的定时任务：每天**北京时间 10:11** 由 GitHub Actions 触发，用 Claude + 联网搜索抓取 AlphaFold / 蛋白质结构预测领域的**最新进展**，按【新论文 / 产业新闻 / 模型发布 / 综述与评论 / 其他动态】分类，沉淀为 `daily/<年>/<日期>.md` + PDF，并自动更新 `daily/INDEX.md` 索引、自动提交回仓库。

- 工作流：`.github/workflows/alphafold-daily.yml`　·　生成脚本：`scripts/daily_digest.py`
- **启用两步**：① 在仓库 `Settings → Secrets and variables → Actions` 添加 Secret `ANTHROPIC_API_KEY`；② 把工作流合并到**默认分支**（GitHub 定时任务仅在默认分支生效）。
- 详见 [`daily/README.md`](daily/README.md)（含手动触发、本地测试、成本说明）。
