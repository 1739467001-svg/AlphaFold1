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
   名称 **`LLM_API_KEY`**，值为你所选模型服务的 API Key。具体提供方配置见下文「选择模型提供方」。
2. **合并到默认分支**：GitHub 的 `schedule` 定时触发**只在默认分支（通常 `main`）上生效**。
   请把本工作流所在改动合并到默认分支后，定时任务才会每天自动跑。

## 选择模型提供方（Claude / 阿里云通义千问）

脚本支持两种后端，在 `Settings → Secrets and variables → Actions` 配置：

**A. Anthropic Claude（默认）**
- Secret：`LLM_API_KEY` = 你的 Anthropic API Key
- Variable（可选）：`LLM_MODEL` = `claude-sonnet-4-6`（默认）

**B. 阿里云通义千问 Qwen / DashScope（OpenAI 兼容 + 联网搜索）**
- Secret：`LLM_API_KEY` = 你的阿里云 DashScope API Key（`sk-...`）
- Variable：`LLM_PROVIDER` = `dashscope`
- Variable（可选）：`LLM_MODEL` = `qwen-plus`（默认；也可 `qwen-max` 等）
- Variable（可选）：`LLM_BASE_URL` = `https://dashscope.aliyuncs.com/compatible-mode/v1`（默认；海外可用 `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`）
- 说明：脚本用 OpenAI 兼容接口 + `enable_search` 让 Qwen 联网检索；需开通[阿里云百炼](https://bailian.console.aliyun.com/)且所选模型支持联网搜索。

> 本地运行同理，把上述 `LLM_*` 设为环境变量即可：
> ```bash
> LLM_PROVIDER=dashscope LLM_API_KEY=sk-... python3 scripts/daily_digest.py
> ```

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
