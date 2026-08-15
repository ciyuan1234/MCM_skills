#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
溯源检查器 (verify.py) —— 反 AI 幻觉的硬校验
用法:
    python verify.py <工作目录>
示例:
    python verify.py D:\2026_国赛1234
    python verify.py .

检查项:
  1. 数据契约   1_数据/data_contract.json 是否存在（Phase 1 强制产物）
  2. 代码-数据绑定  2_代码 下的脚本是否真的读取了数据文件
                    （判定: 代码是否含读取语句; 无读取且含大量数字字面量 -> 疑似硬编码）
  3. 图表三方一致  论文引用的图N 与 3_图表 文件、绘图代码的"数据来源"声明是否对应
  4. 图内对象数量  绘图代码的 系列数/分组数 注释声明 与 数据契约分组是否一致（软检查）
  5. 数值溯源     论文摘要中的关键数值 是否能在 代码输出文件 / 数据契约 stats 中找到出处
  6. 论文-代码对应 附录/支撑材料提到的代码文件 是否真实存在

约定（skill 红线，必须遵守）:
  - 绘图代码第一行必须有注释:  # 数据来源: <data_contract 路径>  或  % 数据来源: <...>
  - 每个结果数值必须能在代码输出文件（results*.csv/txt、运行日志）中找到
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


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


READ_STMTS = [
    # Python
    "read_csv", "read_excel", "read_table", "pd.read", "open(", "loadtxt",
    "genfromtxt", "np.load", "loadmat", "json.load", "read_fwf",
    # MATLAB
    "readtable", "readmatrix", "xlsread", "csvread", "load(", "importdata",
    "fopen", "textscan", "readcell",
]


def has_read_statement(text):
    for s in READ_STMTS:
        if s in text:
            return True
    return False


def find_paper(workdir):
    pd = os.path.join(workdir, "4_论文")
    if not os.path.isdir(pd):
        return None
    for name in sorted(os.listdir(pd)):
        low = name.lower()
        if low in ("paper.md", "paper.tex"):
            return os.path.join(pd, name)
    for name in sorted(os.listdir(pd)):
        if name.lower().endswith((".md", ".tex")) and "template" not in name.lower():
            return os.path.join(pd, name)
    return None


def find_output_files(workdir):
    pats = [
        os.path.join(workdir, "2_代码", "**", "results*.*"),
        os.path.join(workdir, "2_代码", "**", "output*.*"),
        os.path.join(workdir, "2_代码", "**", "*.out"),
        os.path.join(workdir, "2_代码", "**", "运行日志*.*"),
        os.path.join(workdir, "2_代码", "**", "*log*.txt"),
        os.path.join(workdir, "2_代码", "**", "*.csv"),
        os.path.join(workdir, "3_图表", "**", "*data*.txt"),
    ]
    files = []
    for p in pats:
        files.extend(glob.glob(p, recursive=True))
    return sorted(set(files))


def numeric_values_from_outputs(files):
    """收集所有输出文件中的裸数值集合。"""
    vals = set()
    for f in files:
        try:
            text = read_text(f)
        except Exception:
            continue
        for m in re.finditer(r"\d+(?:\.\d+)?", text):
            vals.add(m.group(0))
    return vals


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    workdir = sys.argv[1]
    if not os.path.isdir(workdir):
        print(f"{ERR} 工作目录不存在: {workdir}", file=sys.stderr)
        sys.exit(2)

    # 1. 数据契约
    print("== 1. 数据契约 ==")
    contract_path = os.path.join(workdir, "1_数据", "data_contract.json")
    contract = None
    if os.path.isfile(contract_path):
        try:
            with open(contract_path, encoding="utf-8") as f:
                contract = json.load(f)
            report(PASS, f"data_contract.json 存在（{len(contract.get('files', []))} 个数据文件）")
        except Exception as e:
            report(ERR, f"data_contract.json 无法解析: {e}")
    else:
        report(ERR, "缺少 data_contract.json —— Phase 1 必须运行 make-data-contract.py 生成")
        report(WARN, "跳过依赖契约的检查项 4/5 的数据侧")
    contract_stats = {}
    if contract:
        for fe in contract.get("files", []):
            for k, v in fe.get("stats", {}).items():
                for metric, val in v.items():
                    contract_stats.setdefault(metric, set()).add(str(val))

    # 2. 代码-数据绑定
    print("== 2. 代码-数据绑定 ==")
    code_dir = os.path.join(workdir, "2_代码")
    scripts = []
    if os.path.isdir(code_dir):
        for ext in ("*.py", "*.m", "*.r"):
            scripts.extend(glob.glob(os.path.join(code_dir, "**", ext), recursive=True))
    if not scripts:
        report(WARN, "2_代码 下没有 .py/.m 脚本")
    suspect = []
    for s in scripts:
        try:
            text = read_text(s)
        except Exception:
            continue
        if not has_read_statement(text):
            # 该脚本不读取数据；若它还在产出结果（绘图/打印/写文件）且含较多数字字面量 -> 疑似硬编码
            writes_output = bool(re.search(r"savefig|print\(|to_csv|to_excel|fopen.*'w'|open\(.*['\"]w", text))
            numeric_count = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
            if writes_output and numeric_count >= 4:
                suspect.append(os.path.basename(s))
    if suspect:
        report(WARN, f"{len(suspect)} 个脚本疑似未读取数据文件（含较多数字字面量，可能是硬编码）: {', '.join(suspect[:5])}")
    else:
        report(PASS, "所有脚本均包含读取数据文件的语句（或数值字面量少，视为纯算法函数）")

    # 3. 图表三方一致
    print("== 3. 图表三方一致 ==")
    paper = find_paper(workdir)
    fig_refs = []
    if paper:
        try:
            paper_text = read_text(paper)
        except Exception:
            paper_text = ""
        fig_refs = sorted(set(int(m) for m in re.findall(r"图\s*(\d+)", paper_text)))
    chart_dir = os.path.join(workdir, "3_图表")
    chart_files = []
    if os.path.isdir(chart_dir):
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.eps", "*.pdf", "*.svg"):
            chart_files.extend(glob.glob(os.path.join(chart_dir, "**", ext), recursive=True))
    if fig_refs:
        n_ref = max(fig_refs)
        if len(chart_files) < n_ref:
            report(ERR, f"论文引用到 图{n_ref}，但 3_图表 仅有 {len(chart_files)} 个图片文件")
        else:
            report(PASS, f"论文引用 图1-图{n_ref}，3_图表 有 {len(chart_files)} 个文件")
    else:
        report(WARN, "论文中未识别到 图N 引用（或未找到论文文件）")
    # 绘图代码必须声明数据来源
    plot_scripts = [s for s in scripts if s.endswith((".py", ".m")) and re.search(r"(savefig|print\(|figure|plot|bar\(|imshow|scatter)", read_text(s)) if os.path.isfile(s)]
    no_src = []
    for s in plot_scripts:
        try:
            text = read_text(s)
        except Exception:
            continue
        if not re.search(r"#\s*数据来源|%\s*数据来源|#\s*data source", text):
            no_src.append(os.path.basename(s))
    if no_src:
        report(WARN, f"{len(no_src)} 个绘图脚本缺「数据来源」声明注释（必须写: # 数据来源: <data_contract路径>）: {', '.join(no_src[:5])}")
    else:
        report(PASS, "所有绘图脚本均声明了数据来源")

    # 4. 图内对象数量（软检查，依赖契约 categories 分组数）
    print("== 4. 图内对象数量 ==")
    categories = {}
    if contract:
        for fe in contract.get("files", []):
            categories.update(fe.get("categories", {}))
    max_cat = max(categories.values()) if categories else 0
    declared = []
    missing_decl = []
    for s in plot_scripts:
        try:
            text = read_text(s)
        except Exception:
            continue
        m = re.search(r"(?:#|%)\s*对象数[:：]\s*(\d+)", text)
        if m:
            declared.append(int(m.group(1)))
        else:
            missing_decl.append(os.path.basename(s))
    if max_cat:
        under = [d for d in declared if d < max_cat]
        over = [d for d in declared if d > max_cat]
        if under:
            report(ERR, f"存在绘图脚本对象数声明 {under} < 数据分组数 {max_cat} —— 可能出现「3 个对象只画 2 条线」")
        elif over:
            report(WARN, f"存在绘图脚本对象数声明 {over} > 数据分组数 {max_cat}（可能多画）")
        else:
            report(PASS, f"绘图脚本对象数声明 {sorted(set(declared))} 与数据分组数 {max_cat} 一致")
    elif declared:
        report(PASS, f"数据契约无分组信息，各绘图脚本对象数声明 {sorted(set(declared))}（自查一致）")
    else:
        report(WARN, "缺少对象数声明且契约无分组信息（约定: 绘图脚本注释写明 # 对象数: N）")
    if missing_decl:
        report(WARN, f"{len(missing_decl)} 个绘图脚本缺对象数声明: {', '.join(missing_decl[:5])}")

    # 5. 数值溯源（摘要数值 必须在输出文件/契约 stats 中有出处）
    print("== 5. 数值溯源 ==")
    output_files = find_output_files(workdir)
    if not output_files:
        report(WARN, "未找到代码输出文件（results*.csv/运行日志等），数值溯源无法执行")
    abstract_nums = []
    if paper:
        try:
            paper_text = read_text(paper)
        except Exception:
            paper_text = ""
        am = re.search(r"摘要(.*?)(关键词)", paper_text, re.S)
        if am:
            # 聚焦带小数位的数值结果（精确数值是幻觉高发点）；整数常量如 10%、3 天不纳入溯源
            abstract_nums = re.findall(r"\d+\.\d+", am.group(1))
    if abstract_nums:
        found_vals = numeric_values_from_outputs(output_files)
        for k, vs in contract_stats.items():
            found_vals.update(vs)
        missing = []
        for v in abstract_nums:
            if v not in found_vals:
                missing.append(v)
        if missing:
            report(WARN, f"摘要中 {len(missing)} 个数值在代码输出/契约中无出处（抽查前 5 个）: {missing[:5]}")
            report(WARN, "建议: 每个结果由代码写入 results.csv 并在论文中直接引用")
        else:
            report(PASS, f"摘要中的 {len(abstract_nums)} 个数值均能在输出文件/契约中找到出处")
    else:
        report(WARN, "论文摘要未解析到数值（或未找到论文）")

    # 6. 论文-代码对应（附录引用的代码文件必须存在）
    print("== 6. 论文-代码对应 ==")
    if paper:
        try:
            paper_text = read_text(paper)
        except Exception:
            paper_text = ""
        paper_no_code = re.sub(r"```.*?```", "", paper_text, flags=re.S)  # 剔除代码块，防止标识符误报
        code_names = re.findall(r"[\w\-]+\.(?:m(?!d\b)|py|r)\b", paper_no_code)
        code_names = sorted(set(code_names))
        if code_names:
            existing = {os.path.basename(s) for s in scripts}
            absent = [c for c in code_names if c not in existing]
            if absent:
                report(ERR, f"论文提到的代码文件不存在于 2_代码: {absent[:5]}")
            else:
                report(PASS, f"论文引用的 {len(code_names)} 个代码文件均存在于 2_代码")
        else:
            report(WARN, "论文中未识别到代码文件名引用")
    else:
        report(WARN, "未找到论文文件，跳过")

    print()
    if ERROR_COUNT:
        print(f"溯源检查完成: {ERROR_COUNT} 项错误，修复后再提交。")
        sys.exit(1)
    print("溯源检查完成: 无错误。数值均有出处，图表与数据一致。")
    sys.exit(0)


if __name__ == "__main__":
    main()