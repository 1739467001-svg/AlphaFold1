#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_digest.py — AlphaFold 每日进展摘要生成器

流程：
  1. 调用 Claude（Anthropic Messages API）+ 内置联网搜索工具，检索最近 1-2 周
     AlphaFold / 蛋白质结构预测领域的最新动态。
  2. 让模型按五大类返回结构化 JSON。
  3. 渲染为 daily/<年>/<日期>.md（按主题分节）+ 同名 PDF。
  4. 更新 daily/index.json 与 daily/INDEX.md 分类索引。

用法：
  ANTHROPIC_API_KEY=sk-... python3 scripts/daily_digest.py            # 今天(北京时区)
  python3 scripts/daily_digest.py --date 2026-06-25                   # 指定日期
  python3 scripts/daily_digest.py --dry-run                           # 不联网，用示例数据测渲染

环境变量：
  ANTHROPIC_API_KEY         必需（--dry-run 时不需要）
  ANTHROPIC_MODEL           可选，默认 claude-sonnet-4-6
  WEB_SEARCH_TOOL_VERSION   可选，默认 web_search_20250305
"""
from __future__ import annotations

import os
import sys
import re
import json
import argparse
import datetime
from datetime import timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAILY = ROOT / "daily"
TOOLS = ROOT / "tools"

# 五大归档类别（键名必须与模型返回的 JSON 一致）
CATEGORIES = ["新论文", "产业新闻", "模型发布", "综述与评论", "其他动态"]
CN_TZ = timezone(timedelta(hours=8))  # 北京时间 UTC+8


def today_str() -> str:
    return datetime.datetime.now(CN_TZ).date().isoformat()


# ----------------------------------------------------------------------------- 研究
PROMPT = """你是严谨的蛋白质结构预测领域科研情报分析助手。今天是 __DATE__（北京时间）。
请使用联网搜索（web_search 工具，可多次检索），查找**最近、尤其是过去 1–2 周内**关于
**AlphaFold 及蛋白质 / 生物大分子结构预测领域**的最新进展。建议检索关键词组合（配合时间限定）：
AlphaFold、AlphaFold3、protein structure prediction、Boltz、Chai-1、ESM/ESMFold、
RoseTTAFold、Protenix、OpenFold、Isomorphic Labs、de novo protein design、CASP 等。

严格要求：
1. 只收录**有可靠来源链接、且确为近期**的条目；宁缺毋滥。无法确认时间或来源的，不要编入。
2. 每条目给出：标题、来源出处(venue/媒体)、日期、一句话摘要、为何重要、来源 URL。
3. 按这五类归档：__CATEGORIES__。某一类没有新内容，则该类返回空数组 []。
4. 全部用**简体中文**。**绝不编造**；不确定处可在摘要里标注「待核实」。

最终只输出**一个 JSON 对象**，不要任何额外文字、不要 Markdown 代码围栏。schema：
{
  "date": "__DATE__",
  "headline": "一句话当日总览（30-60字）",
  "categories": {
    "新论文": [{"title":"","venue":"","date":"","summary":"","significance":"","url":""}],
    "产业新闻": [],
    "模型发布": [],
    "综述与评论": [],
    "其他动态": []
  },
  "sources": ["url1", "url2"]
}"""


def run_research(date_str: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # 读取 ANTHROPIC_API_KEY
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    tool_version = os.environ.get("WEB_SEARCH_TOOL_VERSION", "web_search_20250305")

    prompt = PROMPT.replace("__DATE__", date_str).replace("__CATEGORIES__", "、".join(CATEGORIES))
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": tool_version, "name": "web_search", "max_uses": 8}]

    # 服务端工具可能返回 pause_turn，需要回喂续跑
    for _ in range(6):
        resp = client.messages.create(
            model=model,
            max_tokens=8192,
            system="你只依据检索到的可靠来源作答，绝不编造来源或数据。",
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        break

    return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", None) == "text")


def parse_json(text: str):
    """从模型输出里抽出最外层 JSON 对象。"""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ----------------------------------------------------------------------------- 渲染
def render_markdown(data: dict, date_str: str):
    cats = data.get("categories", {}) or {}
    counts = {c: len(cats.get(c) or []) for c in CATEGORIES}
    total = sum(counts.values())
    headline = (data.get("headline") or "（今日总览）").strip()

    L = [
        "---",
        f"标题: AlphaFold 每日进展 · {date_str}",
        "类型: 每日增量摘要（自动生成）",
        "生成方式: GitHub Actions + Claude 联网搜索",
        f"整理日期: {date_str}",
        "---",
        "",
        f"# AlphaFold 每日进展 · {date_str}",
        "",
        f"> {headline}",
        "",
        f"**今日收录 {total} 条** ｜ "
        + " ｜ ".join(f"{c} {counts[c]}" for c in CATEGORIES),
        "",
    ]

    for cat in CATEGORIES:
        L.append(f"## {cat}")
        L.append("")
        items = cats.get(cat) or []
        if not items:
            L += ["（今日无新增）", ""]
            continue
        for it in items:
            title = (it.get("title") or "（无标题）").strip()
            meta = " · ".join(x for x in [it.get("venue", ""), it.get("date", "")] if x)
            L.append(f"### {title}")
            if meta:
                L += [f"*{meta}*", ""]
            if it.get("summary"):
                L.append(f"- **摘要**：{it['summary']}")
            if it.get("significance"):
                L.append(f"- **为何重要**：{it['significance']}")
            if it.get("url"):
                L.append(f"- **来源**：[{it['url']}]({it['url']})")
            L.append("")

    srcs = data.get("sources") or []
    if srcs:
        L += ["## 参考来源", ""]
        L += [f"- [{u}]({u})" for u in srcs]
        L.append("")

    L += [
        "---",
        f"> 本页由自动化流程于 {date_str} 生成（Claude 联网检索）。内容仅供快速跟踪，"
        "准确数据与正式引用请以来源原文为准；标注「待核实」者尤需核对。",
        "",
    ]
    return "\n".join(L), counts, total, headline


def render_pdf(md_path: Path, pdf_path: Path):
    sys.path.insert(0, str(TOOLS))
    import build_pdf  # 复用知识库的渲染器（含中文字体与样式）

    build_pdf.render_file(md_path, pdf_path)


# ----------------------------------------------------------------------------- 索引
def update_index(date_str, headline, counts, total, rel_link):
    DAILY.mkdir(exist_ok=True)
    idx_json = DAILY / "index.json"
    entries = []
    if idx_json.exists():
        try:
            entries = json.loads(idx_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []
    entries = [e for e in entries if e.get("date") != date_str]
    entries.append(
        {"date": date_str, "headline": headline, "counts": counts, "total": total, "path": rel_link}
    )
    entries.sort(key=lambda e: e["date"], reverse=True)
    idx_json.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# AlphaFold 每日进展索引",
        "",
        f"> 由 `scripts/daily_digest.py` 自动维护，共 **{len(entries)}** 天记录（最新在上）。",
        "",
        "| 日期 | 当日总览 | 新论文 | 产业 | 模型 | 综述 | 其他 | 条目 | 链接 |",
        "|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|",
    ]
    for e in entries:
        c = e["counts"]
        hl = (e["headline"] or "").replace("|", "／")[:40]
        md.append(
            f"| {e['date']} | {hl} | {c.get('新论文',0)} | {c.get('产业新闻',0)} | "
            f"{c.get('模型发布',0)} | {c.get('综述与评论',0)} | {c.get('其他动态',0)} | "
            f"{e['total']} | [查看]({e['path']}) |"
        )
    (DAILY / "INDEX.md").write_text("\n".join(md) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- 示例（dry-run）
SAMPLE = {
    "headline": "（示例数据）今日 AlphaFold 生态有 1 篇新论文与 1 条产业动态。",
    "categories": {
        "新论文": [
            {
                "title": "（示例）某扩散式全原子结构预测方法在 PoseBusters 上的改进",
                "venue": "bioRxiv（示例）",
                "date": "2026-06-24",
                "summary": "示例条目，用于验证渲染与归档流程。",
                "significance": "示例：说明分类与 PDF 渲染正常工作。",
                "url": "https://example.org/sample-paper",
            }
        ],
        "产业新闻": [
            {
                "title": "（示例）某公司宣布将结构预测纳入药物发现管线",
                "venue": "示例媒体",
                "date": "2026-06-24",
                "summary": "示例条目。",
                "significance": "示例。",
                "url": "https://example.org/sample-news",
            }
        ],
        "模型发布": [],
        "综述与评论": [],
        "其他动态": [],
    },
    "sources": ["https://example.org/sample-paper", "https://example.org/sample-news"],
}


# ----------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="AlphaFold 每日进展摘要生成器")
    ap.add_argument("--date", help="指定日期 YYYY-MM-DD（默认今天，北京时区）")
    ap.add_argument("--dry-run", action="store_true", help="不联网，用示例数据测试渲染")
    ap.add_argument("--no-pdf", action="store_true", help="跳过 PDF 渲染")
    args = ap.parse_args(argv)

    date_str = args.date or today_str()
    year = date_str[:4]

    print(f"[daily_digest] 日期 = {date_str}（北京时区）")

    if args.dry_run:
        print("[daily_digest] dry-run：使用示例数据，不调用 API。")
        data = dict(SAMPLE, date=date_str)
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("错误：缺少 ANTHROPIC_API_KEY。", file=sys.stderr)
            return 2
        print("[daily_digest] 调用 Claude + 联网搜索 …")
        raw = run_research(date_str)
        data = parse_json(raw)
        if data is None:
            print("[daily_digest] 警告：JSON 解析失败，写入原始输出作为兜底。", file=sys.stderr)
            data = {
                "date": date_str,
                "headline": "（自动解析失败，见「其他动态」原始输出）",
                "categories": {c: [] for c in CATEGORIES},
                "sources": [],
            }
            data["categories"]["其他动态"] = [
                {"title": "模型原始输出（未能解析为结构化数据）", "summary": (raw or "")[:1500]}
            ]

    md_text, counts, total, headline = render_markdown(data, date_str)

    out_dir = DAILY / year
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{date_str}.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"[daily_digest] 写入 {md_path.relative_to(ROOT)}（{total} 条）")

    if not args.no_pdf:
        pdf_path = out_dir / f"{date_str}.pdf"
        render_pdf(md_path, pdf_path)
        print(f"[daily_digest] 渲染 {pdf_path.relative_to(ROOT)}")

    update_index(date_str, headline, counts, total, f"{year}/{date_str}.md")
    print(f"[daily_digest] 已更新 daily/INDEX.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
