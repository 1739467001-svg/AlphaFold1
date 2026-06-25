# 每日 AlphaFold 进展摘要（自动化）

本目录由定时任务**每天自动更新**：抓取 AlphaFold / 蛋白质结构预测领域的最新进展，
按主题分类，沉淀为 Markdown + PDF。

## 目录结构

```
daily/
├── README.md            # 本说明
├── INDEX.md             # 全部每日摘要的分类索引（自动维护，最新在上）
├── index.json           # 索引数据源（自动维护）
└── <年>/
    ├── 2026-06-25.md    # 当日摘要（按主题分节）
    └── 2026-06-25.pdf   # 当日摘要 PDF
```

每篇当日摘要内部按五类分节：**新论文 / 产业新闻 / 模型发布 / 综述与评论 / 其他动态**。

## 运行机制

- **调度**：GitHub Actions 工作流 [`.github/workflows/alphafold-daily.yml`](../.github/workflows/alphafold-daily.yml)，
  每天 **北京时间 10:11**（`cron: 11 2 * * *`，即 02:11 UTC）触发。
- **生成**：[`scripts/daily_digest.py`](../scripts/daily_digest.py) 调用 Claude（Anthropic API）+ 内置**联网搜索**工具检索最新动态，
  让模型返回结构化 JSON，再渲染为 MD/PDF 并更新索引。
- **提交**：工作流用 `GITHUB_TOKEN` 自动 `commit & push` 回仓库（仅当有新内容）。

## ⚙️ 启用前的两步设置（必做）

1. **添加 API 密钥**：仓库 `Settings → Secrets and variables → Actions → New repository secret`，
   名称 `ANTHROPIC_API_KEY`，值为你的 Anthropic API Key。
   （可选）再加一个 *Variable* `ANTHROPIC_MODEL` 覆盖默认模型（默认 `claude-sonnet-4-6`）。
2. **合并到默认分支**：GitHub 的 `schedule` 定时触发**只在默认分支（通常 `main`）上生效**。
   请把本工作流所在改动合并到默认分支后，定时任务才会每天自动跑。

## 手动触发 / 本地测试

- **手动触发**（无需等到 10 点）：仓库 `Actions → AlphaFold 每日进展摘要 → Run workflow`，
  可选填日期。
- **本地测试渲染**（不联网、不花额度）：
  ```bash
  pip install weasyprint markdown pygments
  python3 scripts/daily_digest.py --dry-run --date 2026-06-25
  ```
- **本地真实运行**：
  ```bash
  export ANTHROPIC_API_KEY=sk-...
  python3 scripts/daily_digest.py            # 今天（北京时区）
  ```

## 成本与注意事项

- 每天一次 API 调用（含联网搜索），用量很小；可通过 `ANTHROPIC_MODEL` 选更便宜/更强的模型权衡成本与质量。
- 内容由模型联网检索生成，**仅供快速跟踪**；准确数据与正式引用请以来源原文为准，
  标注「待核实」者尤需核对。
- 若某天无可靠新进展，当日摘要各类可能为「（今日无新增）」，属正常。
