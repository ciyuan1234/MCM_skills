#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2tex.py —— Markdown 论文 -> LaTeX(XeLaTeX) 转换器
用法:
    python md2tex.py <paper.md> <paper.tex>

针对本 skill 的论文模板设计，输出可直接用 xelatex 编译的 .tex:
  - ctexart + xelatex（中文、小四=12pt、1.5 倍行距、geometry 2.5cm 页边距）
  - 摘要独占第一页（摘要后分页）
  - 中文编号章节（一、问题重述 等，节标题原文保留）
  - $$..\\tag{N}$$ 公式块 -> equation 环境（\tag 覆盖自动编号）
  - markdown 表 -> 三线表（booktabs），表题注行 -> 表上方题注
  - ![图N xxx](path) -> figure + 图下题注（题注用 textbf 小号，编号与 md 一致）
  - 代码块 -> verbatim
  - 页脚页码居中、页眉空
"""
import re
import sys


def esc_plain(s):
    """转义普通文本片段，保留后续 Markdown 粗体转换能力。"""
    s = s.replace("\\", r"\textbackslash{}")
    for ch, rep in [("#", r"\#"), ("$", r"\$"), ("%", r"\%"),
                    ("&", r"\&"), ("_", r"\_"), ("{", r"\{"),
                    ("}", r"\}"), ("~", r"\textasciitilde{}"),
                    ("^", r"\textasciicircum{}")]:
        s = s.replace(ch, rep)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    return s


def esc_text(s):
    """普通文本转义（公式块/代码块/表格外），保留 $...$ 行内公式。"""
    parts = re.split(r"(?<!\\)(\$[^$\n]+\$)", s)
    out = []
    for part in parts:
        if re.fullmatch(r"\$[^$\n]+\$", part or ""):
            out.append(part)
        else:
            out.append(esc_plain(part))
    return "".join(out)


def normalize_caption_text(s):
    """兼容 **表1** 标题 / 表1 标题 两种写法。"""
    return re.sub(r"^\*\*(表\s*\d+)\*\*\s*", r"\1 ", s).strip()


def md_table_to_tex(lines):
    """把 markdown 表格行集合转成三线表（≥4 列用 tabularx 自动换行适应版心）。"""
    rows = []
    for ln in lines:
        if re.match(r"^\s*\|?[\s:|\-]+\|?\s*$", ln) and "-" in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    wide = ncol >= 4
    out = [r"\begin{center}"]
    if wide:
        out.append(r"\begin{tabularx}{\textwidth}{" + (r">{\raggedright\arraybackslash}X" * ncol) + "}")
    else:
        out.append(r"\begin{tabular}{" + "c" * ncol + "}")
    out.append(r"\toprule")
    for i, r in enumerate(rows):
        r = r + [""] * (ncol - len(r))
        cells = " & ".join(esc_text(c) for c in r)
        out.append(cells + r" \\")
        if i == 0:
            out.append(r"\midrule")
    out += [r"\bottomrule"]
    out.append(r"\end{tabularx}" if wide else r"\end{tabular}")
    out.append(r"\end{center}")
    return "\n".join(out)


def convert(md_path, tex_path):
    src = open(md_path, encoding="utf-8").read()
    lines = src.splitlines()

    header = r"""\documentclass[12pt,a4paper]{ctexart}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{fancyhdr}
\usepackage{xcolor}
\usepackage{setspace}
\graphicspath{{./}{../}}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\linespread{1.5}
\setlength{\parskip}{0.5em}
\ctexset{
  section = {beforeskip=1.0em, afterskip=0.8em},
  subsection = {beforeskip=0.6em, afterskip=0.5em}
}

\begin{document}
"""
    out = [header]
    i = 0
    n = len(lines)
    first_page = True
    while i < n:
        ln = lines[i]
        stripped = ln.strip()
        # 注释/分隔线
        if not stripped or stripped.startswith("<!--") or stripped == "---":
            i += 1
            continue
        # 一级标题 = 论文题目（第一行 # xxx）
        m = re.match(r"^#\s+(.+)$", ln)
        if m and not ln.startswith("##"):
            out.append(r"\begin{center}{\LARGE\heiti " + esc_text(m.group(1)) + r"}\end{center}")
            out.append(r"\vspace{0.5em}")
            i += 1
            continue
        # 章节标题（## 一、xxx / ## 摘要 / ## 参考文献 / ## 附录）
        m = re.match(r"^##\s+(.+)$", ln)
        if m:
            title = m.group(1).strip()
            out.append(r"\section*{" + esc_text(title) + "}")
            if title == "摘要":
                first_page = False
            if title in ("参考文献", "附录", "附录：支撑材料清单"):
                out.append(r"\clearpage")
            elif title != "摘要":
                first_page = False
            i += 1
            continue
        m = re.match(r"^###\s+(.+)$", ln)
        if m:
            out.append(r"\subsection*{" + esc_text(m.group(1).strip()) + "}")
            first_page = False
            i += 1
            continue
        m = re.match(r"^####\s+(.+)$", ln)
        if m:
            out.append(r"\subsubsection*{" + esc_text(m.group(1).strip()) + "}")
            first_page = False
            i += 1
            continue
        # 公式块 $$ ... $$
        if stripped.startswith("$$"):
            if stripped.endswith("$$") and len(stripped) > 4:
                body = stripped[2:-2].strip()
                j = i + 1
            else:
                block = [stripped]
                j = i + 1
                while j < n and not lines[j].strip().startswith("$$"):
                    block.append(lines[j].strip())
                    j += 1
                if j < n:
                    block.append(lines[j].strip())
                j += 1
                body = "\n".join(block[1:-1]).strip()
            if r"\tag{" in body:
                out.append(r"\begin{equation}")
            else:
                out.append(r"\begin{equation*}")
            out.append(body)
            if r"\tag{" in body:
                out.append(r"\end{equation}")
            else:
                out.append(r"\end{equation*}")
            i = j
            continue
        # 图片 ![图N xxx](path)
        m = re.match(r"^!\[(.+?)\]\((.+?)\)$", ln)
        if m:
            cap = esc_text(m.group(1))
            path = m.group(2).replace("\\", "/")
            out.append(r"\begin{center}")
            out.append(r"\includegraphics[width=0.85\textwidth]{" + path + "}")
            out.append(r"\\")
            out.append(r"{\small\heiti " + cap + "}")
            out.append(r"\end{center}")
            i += 1
            continue
        # 表题注行：表N 标题 / **表N** 标题（数据源：…）
        caption = normalize_caption_text(stripped)
        m = re.match(r"^(表\s*\d+[^\n|]*)$", caption)
        if m:
            out.append(r"\begin{center}{\small\heiti " + esc_text(m.group(1)) + r"}\end{center}")
            i += 1
            continue
        # 代码块 ``` ...
        if stripped.startswith("```"):
            j = i + 1
            code = []
            while j < n and not lines[j].strip().startswith("```"):
                code.append(lines[j])
                j += 1
            out.append(r"\begin{verbatim}")
            out.extend(code)
            out.append(r"\end{verbatim}")
            i = j + 1
            continue
        # markdown 表格
        if stripped.startswith("|") or (stripped.startswith("|---") or re.match(r"^\|?[\s:|\-]+\|?\s*$", stripped)):
            j = i
            tbl = []
            while j < n and (lines[j].strip().startswith("|")):
                tbl.append(lines[j])
                j += 1
            if tbl:
                out.append(md_table_to_tex(tbl))
                i = j
                continue
        # 有序列表 1. xxx
        m = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if m:
            out.append(r"\begin{enumerate}")
            while i < n:
                m2 = re.match(r"^(\d+)\.\s+(.+)$", lines[i].strip())
                if m2:
                    out.append(r"\item " + esc_text(m2.group(2)))
                    i += 1
                else:
                    break
            out.append(r"\end{enumerate}")
            continue
        # 无序列表
        if stripped.startswith("- ") or stripped.startswith("* "):
            out.append(r"\begin{itemize}")
            while i < n:
                m2 = re.match(r"^[-*]\s+(.+)$", lines[i].strip())
                if m2:
                    out.append(r"\item " + esc_text(m2.group(1)))
                    i += 1
                else:
                    break
            out.append(r"\end{itemize}")
            continue
        # 普通段落（"注："开头用 sloppy 宽松断行，避免表格注溢出）
        if stripped.startswith("注："):
            out.append(r"{\sloppy " + esc_text(stripped) + r"\par}")
        else:
            out.append(esc_text(stripped))
        out.append("")
        i += 1

    out.append(r"\end{document}")
    open(tex_path, "w", encoding="utf-8").write("\n".join(out))
    print(f"[完成] {md_path} -> {tex_path}（{len(out)} 行）")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    convert(sys.argv[1], sys.argv[2])
