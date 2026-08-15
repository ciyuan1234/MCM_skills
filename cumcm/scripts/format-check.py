#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版面格式检查器 (format-check.py) —— 检查导出的 docx/PDF 是否符合国赛版面规范
用法:
    python format-check.py <工作目录> [-o 输出.json]
示例:
    python format-check.py D:\2026_国赛1234
    python format-check.py . -o 4_论文\format-check.json

检查项（docx 版面层，官方规范 HARD + 获奖论文惯例）:
  1. 页边距      上下左右 >= 2.5cm（format2023 官方 HARD）
  2. 页脚页码    每节页脚含 PAGE 域（官方 HARD: 摘要页起、页脚中部连续编号）
  3. 首页摘要    文档第一段须含"摘要"
  4. 图片题注    每张图片后须紧跟含"图N"的题注段（获奖论文 4/4 惯例）
  5. 三线表      表格边框仅顶线/表头线/底线，无竖线（获奖论文惯例）
  6. 表题注      每个表格前须有含"表N"的题注段（获奖论文惯例）
  7. 题注字号    图/表题注字号 <= 正文字号（惯例，软检查）
  8. PDF 大小    论文 PDF <= 20MB（官方 HARD）
  9. 正文页数    PDF 总页数（正文尽量 <= 20 页，官方 HARD"尽量"，软检查）

退出码: 0 = 无错误; 1 = 存在错误项
"""

import glob
import json
import os
import re
import sys

PASS = "[通过]"
WARN = "[警告]"
ERR = "[错误]"
ERROR_COUNT = 0


def report(level, msg):
    print(f"{level} {msg}")
    global ERROR_COUNT
    if level == ERR:
        ERROR_COUNT += 1


def find_docx(workdir):
    hits = glob.glob(os.path.join(workdir, "4_论文", "*.docx"))
    return hits[0] if hits else None


def find_pdf(workdir):
    hits = glob.glob(os.path.join(workdir, "4_论文", "*.pdf"))
    return hits[0] if hits else None


def check_margins(sections):
    print("== 1. 页边距 (>=2.5cm) ==")
    ok = True
    for i, sec in enumerate(sections):
        for name, val in (("上", sec.top_margin), ("下", sec.bottom_margin),
                          ("左", sec.left_margin), ("右", sec.right_margin)):
            cm = val.cm if val is not None else 0.0
            if cm < 2.49:
                report(ERR if i == 0 else WARN,
                       f"第{i+1}节 页边距{name} {cm:.2f}cm < 2.5cm（官方规范 HARD）")
                ok = False
    if ok:
        report(PASS, "各节页边距均 >= 2.5cm")
    return ok


def has_page_field(par):
    xml = par._element.xml
    return "PAGE" in xml and ("fldChar" in xml or "instrText" in xml or "fldSimple" in xml)


def check_page_numbers(sections):
    print("== 2. 页脚页码 (摘要页起连续编号) ==")
    ok = True
    for i, sec in enumerate(sections):
        footers = [sec.footer]
        try:
            if sec.different_first_page_header_footer and sec.first_page_footer is not None:
                footers.append(sec.first_page_footer)
        except Exception:
            pass
        found = False
        for ft in footers:
            for p in ft.paragraphs:
                if has_page_field(p):
                    found = True
                    break
            if found:
                break
        if not found:
            report(ERR if i == 0 else WARN, f"第{i+1}节 页脚无 PAGE 页码域（官方规范 HARD）")
            ok = False
    if ok:
        report(PASS, "各节页脚均含 PAGE 页码域")
    return ok


def body_sequence(doc):
    """按文档顺序返回元素: ('p', paragraph) / ('tbl', table)。"""
    seq = []
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            seq.append(("p", Paragraph(child, doc)))
        elif tag == "tbl":
            seq.append(("tbl", Table(child, doc)))
    return seq


def has_image(par):
    return par._element.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline") or \
           par._element.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}anchor")


def table_border_info(tbl):
    """返回 dict: top/bottom/left/right/insideH/insideV 是否有边框。"""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    borders = None
    tblPr = tbl._element.tblPr
    if tblPr is not None:
        borders = tblPr.find(f"{ns}tblBorders")
    try:
        style_el = tbl.style.element
        if borders is None:
            borders = style_el.find(f"{ns}tblPr/{ns}tblBorders")
    except Exception:
        pass
    out = {}
    if borders is None:
        return out  # 无边框定义（默认无边框）
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(f"{ns}{name}")
        out[name] = el is not None and el.get(f"{ns}val") not in ("nil", "none", None)
    return out


def check_figures_and_tables(seq):
    print("== 3. 图片题注 / 4. 三线表 / 5. 表题注 ==")
    n_img = 0
    fig_captioned = 0
    fig_bad = []
    tbls = 0
    tbl_captioned = 0
    three_line = 0
    tbl_bad = []
    normal_size = 12.0  # 正文小四
    cap_size_bad = []
    for idx, (kind, obj) in enumerate(seq):
        if kind == "p":
            if has_image(obj):
                n_img += 1
                nxt = None
                for j in range(idx + 1, len(seq)):
                    if seq[j][0] == "p" and seq[j][1].text.strip():
                        nxt = seq[j][1].text.strip()
                        break
                if nxt and re.match(r"^图\s*\d+", nxt):
                    fig_captioned += 1
                    for r in seq[j][1].runs:
                        if r.font.size:
                            if r.font.size.pt > normal_size:
                                cap_size_bad.append(f"图题注字号 {r.font.size.pt}pt > 正文 {normal_size}pt")
                            break
                else:
                    fig_bad.append(f"第{n_img}张图片后无'图N'题注段")
        elif kind == "tbl":
            tbls += 1
            prev = None
            prev_txt = ""
            for j in range(idx - 1, -1, -1):
                if seq[j][0] == "p" and seq[j][1].text.strip():
                    prev = seq[j][1]
                    prev_txt = prev.text.strip()
                    break
            # 符号说明节的表格惯例不编号，豁免
            near = "\n".join(o.text.strip() for k, o in seq[max(0, idx - 12):idx] if k == "p")
            if re.search(r"符号说明", near) and prev_txt and not re.match(r"^表\s*\d+", prev_txt):
                tbl_captioned += 1  # 符号说明表惯例不编号，视同合规
            elif prev_txt and re.match(r"^表\s*\d+", prev_txt):
                tbl_captioned += 1
                for r in prev.runs:
                    if r.font.size:
                        if r.font.size.pt > normal_size:
                            cap_size_bad.append(f"表题注字号 {r.font.size.pt}pt > 正文 {normal_size}pt")
                        break
            else:
                tbl_bad.append(f"第{tbls}张表格前无'表N'题注段")
            bi = table_border_info(obj)
            if bi and not bi.get("insideV") and not bi.get("left") and not bi.get("right") \
                    and (bi.get("top") or bi.get("insideH")) and bi.get("bottom"):
                three_line += 1
            elif bi and (bi.get("insideV") or bi.get("left") or bi.get("right")):
                tbl_bad.append(f"第{tbls}张表格非三线表（含竖线/左右框线）")
    if n_img == 0:
        report(ERR, "docx 中未发现任何图片（论文正文必须有图，获奖论文 4/4 带图）")
    else:
        if fig_captioned == n_img:
            report(PASS, f"{n_img} 张图片均有'图N'题注（图下）")
        else:
            report(ERR, f"{n_img - fig_captioned}/{n_img} 张图片缺题注: {fig_bad[:3]}")
    if tbls == 0:
        report(WARN, "docx 中未发现表格")
    else:
        if tbl_captioned == tbls:
            report(PASS, f"{tbls} 张表格均有'表N'题注（表上）")
        else:
            report(WARN, f"{tbls - tbl_captioned}/{tbls} 张表格缺题注: {tbl_bad[:3]}")
        three_bad = [b for b in tbl_bad if "非三线表" in b]
        if three_line == tbls:
            report(PASS, f"{tbls} 张表格均为三线表")
        else:
            report(WARN, f"{len(three_bad)} 张表格非三线表: {three_bad[:3]}（惯例：仅顶线/表头线/底线）")
    if cap_size_bad:
        report(WARN, f"题注字号大于正文: {cap_size_bad[:2]}（惯例：题注小于正文）")
    else:
        report(PASS, "题注字号均 <= 正文（惯例）")
    return n_img, tbls


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    wd = sys.argv[1]
    out = ""
    if "-o" in sys.argv:
        i = sys.argv.index("-o")
        if i + 1 < len(sys.argv):
            out = sys.argv[i + 1]
    if not os.path.isdir(wd):
        print(f"{ERR} 工作目录不存在: {wd}", file=sys.stderr)
        sys.exit(2)

    from docx import Document
    from docx.shared import Cm

    docx_path = find_docx(wd)
    if not docx_path:
        report(ERR, "4_论文 下没有 docx（先运行 export-paper.ps1 导出）")
        print(f"检查完成: {ERROR_COUNT} 项错误")
        sys.exit(1)
    doc = Document(docx_path)

    m1 = check_margins(doc.sections)
    m2 = check_page_numbers(doc.sections)

    print("== 3. 首页摘要 ==")
    first_texts = []
    for p in doc.paragraphs:
        t = p.text.strip().lstrip("\ufeff")
        if t:
            first_texts.append(t)
        if len(first_texts) >= 3:
            break
    if not first_texts:
        report(ERR, "文档没有任何段落")
    elif any(re.search(r"(^|#|\s)摘\s*要", t) for t in first_texts):
        report(PASS, "文档开头为标题+摘要页（第一页为摘要专用页）")
    else:
        report(ERR, f"文档开头未见摘要标题（实际开头: {first_texts[0][:20]}…），电子版第一页必须为摘要专用页（官方 HARD）")

    m4 = check_figures_and_tables(body_sequence(doc))

    print("== 6. PDF 大小与页数 ==")
    pdf_path = find_pdf(wd)
    n_pages = -1
    if not pdf_path:
        report(ERR, "4_论文 下没有 PDF（最终必须提交 PDF 版论文）")
    else:
        size_mb = os.path.getsize(pdf_path) / 1048576.0
        if size_mb <= 20:
            report(PASS, f"PDF {size_mb:.1f}MB <= 20MB（官方 HARD）")
        else:
            report(ERR, f"PDF {size_mb:.1f}MB > 20MB（官方 HARD）")
        try:
            from pypdf import PdfReader
            n_pages = len(PdfReader(pdf_path).pages)
            if n_pages <= 20:
                report(PASS, f"PDF 共 {n_pages} 页（正文 <= 20 页建议，符合）")
            else:
                report(WARN, f"PDF 共 {n_pages} 页（含附录则正常；正文建议 <= 20 页）")
        except Exception as e:
            report(WARN, f"无法读取 PDF 页数: {e}")

    print()
    if ERROR_COUNT:
        print(f"检查完成: {ERROR_COUNT} 项错误，请修复版面后再提交。")
        sys.exit(1)
    print("检查完成: 无错误。")
    if out:
        payload = {"margins_ok": m1, "page_number_ok": m2, "images": m4[0],
                   "tables": m4[1], "pdf_pages": n_pages}
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[完成] 版面检查结果已写入: {out}")
    sys.exit(0)


if __name__ == "__main__":
    main()