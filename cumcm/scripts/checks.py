#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CUMCM 论文检查器 (checks.py)
用法:
    python checks.py <论文.md 或 论文.tex> [工作目录]
示例:
    python checks.py 4_论文/paper.md
    python checks.py 4_论文/paper.md .
    python checks.py 4_论文/paper.tex D:\2026_国赛1234

检查项（启发式规则，阈值可自行调整）:
  1. 结构完整性  必含章节是否齐全（问题重述/问题分析/模型假设/符号说明/模型建立/
                 模型评价/参考文献，附录建议有）
  2. 摘要检查    字数区间、关键词行(3-6个)、数值结果密度、逐问覆盖
  3. 编号连续性  图/表/公式编号是否跳号
  4. 参考文献    数量与格式抽查（含年份、出版社/期刊等要素）
  5. 提交物完整性 论文PDF、代码目录、支撑材料是否齐备（需提供工作目录）

退出码: 0 = 无错误; 1 = 存在错误项
"""

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


# ---------- 文本读取（兼容 UTF-8 / GBK） ----------

def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# ---------- 1. 结构完整性 ----------

REQUIRED_SECTIONS = [
    ("问题重述", "问题重述（一、…）"),
    ("问题分析", "问题分析（二、…）"),
    ("模型假设", "模型假设（三、…）"),
    ("符号说明", "符号说明（四、…）"),
    ("模型建立", "模型建立与求解（五、…）"),
    ("评价", "模型的评价、改进与推广（六、…）"),
    ("参考文献", "参考文献（七、…）"),
]
OPTIONAL_SECTIONS = [
    ("附录", "附录（代码清单，建议保留）"),
    ("模型检验", "模型检验（可内嵌在求解节，独立小节更佳）"),
    ("灵敏度", "灵敏度/稳定性分析（建议每个模型都做）"),
]


def heading_lines(text):
    """匹配 markdown (# 开头) 与 LaTeX (\\section) 标题行。"""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^#{1,6}\s", s):
            lines.append(s.lstrip("#").strip())
        elif re.match(r"^\\section", s):
            lines.append(s.replace("\\", "").strip())
        elif re.match(r"^[一二三四五六七八九十]、", s):
            lines.append(s)
    return lines


def check_structure(text):
    print("== 1. 结构完整性 ==")
    headings = "\n".join(heading_lines(text))
    for keyword, desc in REQUIRED_SECTIONS:
        if keyword in headings:
            report(PASS, f"已找到章节: {desc}")
        else:
            report(ERR, f"缺少章节: {desc}")
    for keyword, desc in OPTIONAL_SECTIONS:
        if keyword in headings:
            report(PASS, f"已找到章节: {desc}")
        else:
            report(WARN, f"建议补充: {desc}")


# ---------- 2. 摘要检查 ----------

def extract_abstract(text):
    """提取 摘要 与 关键词 之间的文本。"""
    m = re.search(r"(摘要|摘\s*要)\s*\n(.*?)(\n\s*关键词|关键词)", text, re.S)
    if not m:
        return None
    return m.group(2).strip()


def extract_keywords(text):
    m = re.search(r"关键词\s*[:：]?\s*(.+?)(\n|$)", text)
    if not m:
        return None
    return m.group(1).strip()


def check_abstract(text):
    print("== 2. 摘要检查 ==")
    abstract = extract_abstract(text)
    if not abstract:
        report(ERR, "未找到摘要正文（需在 摘要 与 关键词 之间）")
        return
    pure = re.sub(r"\s", "", abstract)
    n = len(pure)
    if n < 300 or n > 1800:
        report(ERR, f"摘要字数 {n}，超出合理区间 300-1800 字")
    elif n < 500 or n > 1500:
        report(WARN, f"摘要字数 {n}，获奖论文通常 900-1200 字，建议压缩或扩充")
    else:
        report(PASS, f"摘要字数 {n}，区间合理（获奖论文通常 900-1200 字）")

    kws = extract_keywords(text)
    if kws:
        kws_clean = re.sub(r"[*#_`]", "", kws)
        items = [w for w in re.split(r"[、,，;；\s]+", kws_clean) if w]
        if 3 <= len(items) <= 6:
            report(PASS, f"关键词 {len(items)} 个: {kws_clean}")
        else:
            report(WARN, f"关键词 {len(items)} 个，建议 3-6 个: {kws_clean}")
    else:
        report(ERR, "缺少关键词行（格式: 关键词: 词1 词2 …）")

    digits = re.findall(r"\d+(?:\.\d+)?", abstract)
    if len(digits) >= 8:
        report(PASS, f"摘要含 {len(digits)} 处数值，数字密度充足（评委看重量化结果）")
    else:
        report(WARN, f"摘要仅 {len(digits)} 处数值，建议每个问题的关键结果都写具体数值")

    qs = re.findall(r"问题[一二三四五六七八九十1-9]", abstract)
    if len(qs) >= 2:
        report(PASS, f"摘要逐问覆盖（出现 {len(qs)} 处'问题X'表述）")
    else:
        report(WARN, "摘要中'问题一/问题二…'的逐问覆盖不足，建议按问题分条写")

    for key in ("蒙特卡罗", "遗传", "模拟退火", "神经网络", "线性规划", "时间序列",
                "灰色", "聚类", "回归", "差分", "微分方程", "优化", "预测", "检验"):
        if key in abstract:
            report(PASS, f"摘要点明方法: {key}")
            break
    else:
        report(WARN, "摘要中未识别到明确的方法关键词（如'线性规划''时间序列'），需写明模型归类与算法")


# ---------- 3. 编号连续性 ----------

def check_numbering_from_list(text, label, nums_raw):
    print(f"== 3. 编号连续性: {label} ==")
    nums = [int(m) for m in nums_raw]
    if not nums:
        report(WARN, f"未发现 {label} 编号")
        return
    uniq = sorted(set(nums))
    full = list(range(1, max(uniq) + 1))
    missing = [i for i in full if i not in uniq]
    if missing:
        report(ERR, f"{label} 编号跳号，缺少: {missing}")
    else:
        report(PASS, f"{label} 编号连续 1-{max(uniq)}（共 {len(nums)} 处编号）")


def check_numbering(text, label, pattern, mode="md"):
    print(f"== 3. 编号连续性: {label} ==")
    # 编号检查只扫描正文（参考文献/附录中的数字与公式无关，先截断）
    body = re.split(r"参考文献", text)[0]
    nums = [int(m) for m in re.findall(pattern, body, re.MULTILINE)]
    if not nums:
        report(WARN, f"未发现 {label} 编号")
        return
    uniq = sorted(set(nums))
    full = list(range(1, max(uniq) + 1))
    missing = [i for i in full if i not in uniq]
    if missing:
        report(ERR, f"{label} 编号跳号，缺少: {missing}")
    else:
        report(PASS, f"{label} 编号连续 1-{max(uniq)}（共 {len(nums)} 处引用/题注）")


# ---------- 4. 参考文献 ----------

def check_references(text):
    print("== 4. 参考文献 ==")
    m = re.search(r"参考文献(.*?)(附录|$)", text, re.S)
    if not m:
        report(ERR, "未找到参考文献章节")
        return
    body = m.group(1)
    entries = [ln for ln in body.splitlines() if ln.strip() and re.match(r"^[\[(（]?\d", ln.strip())]
    if not entries:
        entries = [ln for ln in body.splitlines() if ln.strip() and re.search(r"20\d\d|19\d\d", ln)]
    if not entries:
        report(WARN, "参考文献章节存在但未解析到条目（每行以 [1] 或序号开头）")
        return
    n = len(entries)
    if n < 4:
        report(ERR, f"参考文献仅 {n} 条，建议 5-10 条")
    elif n > 20:
        report(WARN, f"参考文献 {n} 条，偏多，控制在 5-10 条较稳妥")
    else:
        report(PASS, f"参考文献 {n} 条")

    bad = []
    for ln in entries:
        if not re.search(r"(19|20)\d\d", ln):
            bad.append(ln[:30])
        elif not re.search(r"(出版社|出版|学报|杂志|期刊|页|期|:|://|edu\.|org\.|com\.)", ln):
            bad.append(ln[:30])
    if bad:
        report(WARN, f"{len(bad)} 条文献疑似缺年份/出版要素（示例: {bad[0]}…）")
    else:
        report(PASS, "文献条目均含年份与出版要素")


# ---------- 5. 提交物完整性 ----------

def check_submission(workdir):
    print("== 5. 提交物完整性 ==")
    if not workdir or not os.path.isdir(workdir):
        report(WARN, "未提供工作目录，跳过提交物检查（用法: python checks.py 论文.md <工作目录>）")
        return
    paper_dir = os.path.join(workdir, "4_论文")
    pdfs = [f for f in os.listdir(paper_dir) if f.lower().endswith(".pdf")] if os.path.isdir(paper_dir) else []
    if pdfs:
        report(PASS, f"论文 PDF 已生成: {pdfs[0]}")
    else:
        report(ERR, "4_论文 下没有 PDF（最终必须提交 PDF 版论文）")

    code_dir = os.path.join(workdir, "2_代码")
    if os.path.isdir(code_dir) and os.listdir(code_dir):
        report(PASS, "2_代码 目录非空（代码已就位）")
    else:
        report(ERR, "2_代码 目录为空（支撑材料需附全部代码）")

    sup_dir = os.path.join(workdir, "5_支撑材料")
    if os.path.isdir(sup_dir) and os.listdir(sup_dir):
        report(PASS, "5_支撑材料 目录非空")
    else:
        report(WARN, "5_支撑材料 目录为空（若生成了额外数据/说明文档请放入）")


# ---------- 主流程 ----------

def check_l2_backcheck(workdir):
    """L2 跨阶段回溯检查：验证 decision_log.json 与 hand_off.md 一致性。"""
    print("== 6.5 L2 跨阶段回溯检查 ==")
    import json as _json
    dlog_path = os.path.join(workdir, "decision_log.json") if workdir else "decision_log.json"
    if not os.path.isfile(dlog_path):
        report(WARN, "未找到 decision_log.json，跳过 L2 检查")
        return
    try:
        with open(dlog_path, encoding="utf-8") as f:
            dlog = _json.load(f)
    except Exception as e:
        report(ERR, f"decision_log.json 解析失败: {e}")
        return

    stage_dirs = {
        0: "stage0_read", 1: "stage1_data",
        2: "stage2_model", 3: "stage3_write", 4: "stage4_check"
    }
    issues = []

    # 检查已完成阶段是否有 hand_off.md
    for si, sdir in stage_dirs.items():
        stage_info = dlog.get("stages", {}).get(str(si), {})
        if stage_info.get("status") == "completed":
            hpath = os.path.join(workdir, sdir, "hand_off.md") if workdir else os.path.join(sdir, "hand_off.md")
            if not os.path.isfile(hpath):
                issues.append(f"阶段 {si} 已完成但缺少 hand_off.md")
            else:
                try:
                    htext = read_text(hpath)
                    sections = re.findall(r"## What", htext)
                    if len(sections) < 3:
                        issues.append(f"阶段 {si} hand_off.md 段落不完整（需 3 个 '## What'）")
                except Exception:
                    issues.append(f"阶段 {si} hand_off.md 无法读取")

    # 检查时间预算
    budget = dlog.get("budget", {})
    remaining = budget.get("remaining_hours")
    if remaining is not None and remaining <= 6:
        issues.append(f"剩余时间 {remaining}h — 应处于锁定模式")

    # 检查 decisions 数组是否为空
    if not dlog.get("decisions"):
        issues.append("decisions 数组为空（建议记录关键决策）")

    if issues:
        for iss in issues:
            report(WARN, f"L2: {iss}")
    else:
        report(PASS, "L2 跨阶段回溯检查通过（hand_off 齐全、时间预算合理、决策已记录）")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    paper = sys.argv[1]
    workdir = sys.argv[2] if len(sys.argv) > 2 else ""
    if not os.path.isfile(paper):
        print(f"{ERR} 找不到论文文件: {paper}", file=sys.stderr)
        sys.exit(2)

    text = read_text(paper)
    check_structure(text)
    check_abstract(text)
    check_numbering(text, "图", r"图\s*(\d+)")
    check_numbering(text, "表", r"表\s*(\d+)")
    # 公式编号: 优先识别 LaTeX/Markdown 的 \tag{N}；否则回退到"行内 $$...$$ 行尾 (N)"
    tags = re.findall(r"\\tag\{(\d+)\}", text)
    if tags:
        check_numbering_from_list(text, "公式", tags)
    else:
        check_numbering(text, "公式", r"^[^$\n]*\((\d+)\)\s*$")
    check_references(text)
    check_submission(workdir)
    check_l2_backcheck(workdir)

    print()
    if ERROR_COUNT:
        print(f"检查完成: {ERROR_COUNT} 项错误，请修复后再提交。")
        sys.exit(1)
    print("检查完成: 无错误。建议仍以人工逐条核对 06-checklists.md。")
    sys.exit(0)


if __name__ == "__main__":
    main()
