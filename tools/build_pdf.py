#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pdf.py — 把知识库的 Markdown 文档渲染成排版精良、支持中文的 PDF。

用法:
    python3 tools/build_pdf.py                 # 渲染 README.md + docs/*.md + sources/*.md 到 pdf/
    python3 tools/build_pdf.py a.md b.md       # 只渲染指定文件
    python3 tools/build_pdf.py --combined      # 额外生成合订本 pdf/AlphaFold知识库-合订本.pdf

依赖: weasyprint, markdown, pygments  (pip install weasyprint markdown pygments)
中文字体: 文泉驿正黑 (WenQuanYi Zen Hei)，系统已自带。
"""
from __future__ import annotations

import sys
import re
import glob
import html
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension
from pygments.formatters import HtmlFormatter
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdf"

# 字体优先级：拉丁文用 DejaVu，中文回落到文泉驿正黑（系统自带）。
CSS = """
@page {
    size: A4;
    margin: 1.8cm 1.7cm 2.0cm 1.7cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: 'DejaVu Sans', 'WenQuanYi Zen Hei', sans-serif;
        font-size: 8pt;
        color: #888;
    }
    @top-right {
        content: string(doc-title);
        font-family: 'DejaVu Sans', 'WenQuanYi Zen Hei', sans-serif;
        font-size: 8pt;
        color: #aaa;
    }
}
html { -weasy-hyphens: none; }
body {
    font-family: 'DejaVu Sans', 'WenQuanYi Zen Hei', sans-serif;
    font-size: 10.5pt;
    line-height: 1.62;
    color: #1f2328;
}
h1, h2, h3, h4 {
    font-family: 'DejaVu Sans', 'WenQuanYi Zen Hei', sans-serif;
    line-height: 1.3;
    margin-top: 1.1em;
    margin-bottom: 0.5em;
}
h1 {
    string-set: doc-title content();
    bookmark-level: 1;
    font-size: 20pt;
    color: #0b5394;
    border-bottom: 2.5px solid #0b5394;
    padding-bottom: 0.25em;
}
h2 { bookmark-level: 2; font-size: 15pt; color: #134f78;
     border-bottom: 1px solid #d0d7de; padding-bottom: 0.2em; }
h3 { bookmark-level: 3; font-size: 12.5pt; color: #1f2328; }
h4 { font-size: 11pt; color: #444; }
p { margin: 0.45em 0; }
a { color: #0969da; text-decoration: none; word-break: break-all; }
strong { color: #0b3d62; }
ul, ol { margin: 0.4em 0 0.4em 0; padding-left: 1.4em; }
li { margin: 0.18em 0; }
blockquote {
    margin: 0.7em 0; padding: 0.5em 0.9em;
    border-left: 4px solid #0b5394; background: #f0f6fb;
    color: #33475b; border-radius: 0 4px 4px 0;
}
blockquote p { margin: 0.2em 0; }
code {
    font-family: 'DejaVu Sans Mono', 'WenQuanYi Zen Hei Mono', monospace;
    font-size: 9pt; background: #f3f4f6; padding: 0.1em 0.35em;
    border-radius: 4px; color: #b3205e;
}
pre {
    background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
    padding: 0.8em 1em; overflow-x: auto; font-size: 8.6pt; line-height: 1.45;
    white-space: pre-wrap; word-break: break-word;
}
pre code { background: none; padding: 0; color: #1f2328; font-size: 8.6pt; }
table {
    border-collapse: collapse; width: 100%; margin: 0.8em 0;
    font-size: 9pt; -weasy-table-layout: auto;
}
th, td { border: 1px solid #c8d1da; padding: 0.4em 0.6em; text-align: left;
         vertical-align: top; }
th { background: #eaf2fa; color: #0b3d62; font-weight: bold; }
tr:nth-child(even) td { background: #f7fafc; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 1.2em 0; }
img { max-width: 100%; }

/* 文档头部的元信息卡片 */
.meta-card {
    background: #f0f6fb; border: 1px solid #cfe0ef; border-left: 5px solid #0b5394;
    border-radius: 6px; padding: 0.7em 1em; margin: 0 0 1.2em 0; font-size: 9pt;
    color: #33475b;
}
.meta-card table { margin: 0; width: 100%; font-size: 9pt; }
.meta-card th, .meta-card td { border: none; padding: 0.15em 0.5em; }
.meta-card th { background: none; color: #0b5394; white-space: nowrap;
                text-align: right; width: 7em; }
.cover {
    text-align: center; margin-top: 8cm;
}
.cover h1 { border: none; font-size: 30pt; color: #0b5394; }
.cover .sub { font-size: 13pt; color: #555; margin-top: 0.6em; }
.cover .date { font-size: 11pt; color: #888; margin-top: 3cm; }
.page-break { page-break-before: always; }
"""

PYGMENTS_CSS = HtmlFormatter(style="friendly").get_style_defs(".codehilite")

MD_EXTENSIONS = [
    "extra",            # tables, fenced_code, footnotes, attr_list, def_list...
    "codehilite",
    "sane_lists",
    "admonition",
    TocExtension(permalink=False, baselevel=1),
]
MD_CONFIG = {"codehilite": {"guess_lang": False, "noclasses": False}}


def split_front_matter(text: str):
    """拆出开头的 --- ... --- YAML 式元信息块，返回 (meta_dict, body)。"""
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if m:
            block = m.group(1)
            body = text[m.end():]
            meta = {}
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            return meta, body
    return {}, text


def meta_card_html(meta: dict) -> str:
    if not meta:
        return ""
    rows = []
    for k, v in meta.items():
        v_html = html.escape(v)
        # 链接自动可点击
        v_html = re.sub(r"(https?://[^\s]+)", r'<a href="\1">\1</a>', v_html)
        rows.append(f"<tr><th>{html.escape(k)}</th><td>{v_html}</td></tr>")
    return f'<div class="meta-card"><table>{"".join(rows)}</table></div>'


def md_to_html_fragment(md_text: str) -> tuple[str, str]:
    meta, body = split_front_matter(md_text)
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIG)
    body_html = md.convert(body)
    return meta_card_html(meta) + body_html, meta.get("标题", "")


def wrap_document(inner_html: str, title: str) -> str:
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{CSS}\n{PYGMENTS_CSS}</style></head>
<body>{inner_html}</body></html>"""


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def render_file(md_path: Path, out_path: Path):
    text = md_path.read_text(encoding="utf-8")
    fragment, title = md_to_html_fragment(text)
    doc_html = wrap_document(fragment, title or md_path.stem)
    HTML(string=doc_html, base_url=str(md_path.parent)).write_pdf(str(out_path))
    print(f"  ✓ {rel(md_path)}  ->  {rel(out_path)}")


def default_inputs():
    files = []
    readme = ROOT / "README.md"
    if readme.exists():
        files.append(readme)
    files += sorted((ROOT / "docs").glob("*.md"))
    files += sorted((ROOT / "sources").glob("*.md"))
    return files


def build_combined(inputs, out_path: Path):
    cover = (
        '<div class="cover">'
        "<h1>AlphaFold 蛋白质折叠知识库</h1>"
        '<div class="sub">最新进展 · 论文精读 · 综合分析</div>'
        '<div class="date">整理日期：2026-06-24</div>'
        "</div>"
    )
    parts = [cover]
    for p in inputs:
        if p.name == "README.md":
            continue
        fragment, _ = md_to_html_fragment(p.read_text(encoding="utf-8"))
        parts.append(f'<div class="page-break">{fragment}</div>')
    doc_html = wrap_document("".join(parts), "AlphaFold 知识库 合订本")
    HTML(string=doc_html, base_url=str(ROOT)).write_pdf(str(out_path))
    print(f"  ✓ 合订本  ->  {out_path.relative_to(ROOT)}")


def main(argv):
    PDF_DIR.mkdir(exist_ok=True)
    combined = "--combined" in argv
    argv = [a for a in argv if a != "--combined"]

    if argv:
        inputs = [Path(a).resolve() for a in argv]
    else:
        inputs = default_inputs()

    if not inputs:
        print("没有可渲染的 Markdown 文件。")
        return 1

    print(f"渲染 {len(inputs)} 个文档 -> {PDF_DIR.relative_to(ROOT)}/")
    for md_path in inputs:
        if not md_path.exists():
            print(f"  ! 跳过(不存在): {md_path}")
            continue
        out_path = PDF_DIR / (md_path.stem + ".pdf")
        render_file(md_path, out_path)

    if combined:
        build_combined(default_inputs(), PDF_DIR / "AlphaFold知识库-合订本.pdf")

    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
