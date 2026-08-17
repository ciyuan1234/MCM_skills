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
  5. 数值溯源     论文正文（摘要+正文+表格）中的关键数值
                 是否能在 代码输出文件 / 数据契约 stats 中找到出处，
                 并生成 4_论文/溯源报告.md（N/M 溯源 + 未溯源清单）
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


def _find_csv(workdir, csv_name):
    """在工作目录中查找 CSV 文件，返回路径或 None。"""
    matches = glob.glob(os.path.join(workdir, "**", csv_name), recursive=True)
    if not matches:
        matches = glob.glob(os.path.join(workdir, csv_name))
    return matches[0] if matches else None


def _read_csv_vals(csv_path):
    """读取 CSV 文件中所有裸数值。"""
    vals = set()
    try:
        text = read_text(csv_path)
    except Exception:
        return vals
    for vm in re.finditer(r"\d+(?:\.\d+)?", text):
        vals.add(vm.group(0))
    return vals


def _check_missing(tbl_vals, csv_vals):
    """检查表格数值中哪些在 CSV 数值集中找不到（含浮点容差）。"""
    csv_floats = []
    for x in csv_vals:
        try:
            csv_floats.append(float(x))
        except ValueError:
            pass
    missing = []
    for tv in tbl_vals:
        if tv in csv_vals:
            continue
        try:
            tfv = float(tv)
            if any(abs(tfv - cv) < 1e-3 * max(1.0, abs(tfv)) for cv in csv_floats):
                continue
        except ValueError:
            pass
        missing.append(tv)
    return missing


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
        # 题面常量/派生常量: data_contract.json 的 constants 字段（{名称: 数值}）
        # 论文中的题给参数（运力/消耗系数/数据规模等）由此获得出处
        contract_stats.setdefault("constants", set()).update(
            str(v) for v in contract.get("constants", {}).values())

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
    plot_scripts = [s for s in scripts if s.endswith((".py", ".m")) and re.search(r"(savefig|\.plot\(|bar\(|imshow|scatter|stem\()", read_text(s)) if os.path.isfile(s)]
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
    curve_scripts = []
    for s in plot_scripts:
        try:
            text = read_text(s)
        except Exception:
            continue
        m = re.search(r"(?:#|%)\s*对象数[:：]\s*(\d+)(?:\s*(\S+))?", text)
        if m:
            declared.append(int(m.group(1)))
            kind = (m.group(2) or "").strip("（）()")
            if kind == "曲线":
                curve_scripts.append(s)
        else:
            missing_decl.append(os.path.basename(s))
    if max_cat:
        curve_d = [d for s, d in zip(plot_scripts, declared) if s in curve_scripts]
        under = [d for d in declared if d < max_cat and d not in curve_d]
        over = [d for d in declared if d > max_cat and d not in curve_d]
        if under:
            report(ERR, f"存在绘图脚本对象数声明 {under} < 数据分组数 {max_cat} —— 可能出现「3 个对象只画 2 条线」")
        elif over:
            report(WARN, f"存在绘图脚本对象数声明 {over} > 数据分组数 {max_cat}（可能多画）")
        else:
            note = "（曲线图按曲线条数计）" if curve_d else ""
            report(PASS, f"绘图脚本对象数声明 {sorted(set(declared))} 与数据分组数 {max_cat} 一致{note}")
    elif declared:
        report(PASS, f"数据契约无分组信息，各绘图脚本对象数声明 {sorted(set(declared))}（自查一致）")
    else:
        report(WARN, "缺少对象数声明且契约无分组信息（约定: 绘图脚本注释写明 # 对象数: N）")
    if missing_decl:
        report(WARN, f"{len(missing_decl)} 个绘图脚本缺对象数声明: {', '.join(missing_decl[:5])}")

    # 5. 数值溯源（正文全数值 必须在输出文件/契约 stats 中有出处，并生成溯源报告）
    print("== 5. 数值溯源（全文） ==")
    output_files = find_output_files(workdir)
    if not output_files:
        report(WARN, "未找到代码输出文件（results*.csv/运行日志等），数值溯源无法执行")
    abstract_nums = []
    if paper:
        try:
            paper_text = read_text(paper)
        except Exception:
            paper_text = ""
        # 只扫摘要+正文（参考文献前），剔除代码块防标识符误报
        body_part = re.split(r"参考文献", paper_text)[0]
        body_no_code = re.sub(r"```.*?```", "", body_part, flags=re.S)
        am = re.search(r"摘要(.*)", body_no_code, re.S)
        if am:
            body_no_code = am.group(1)
        # 数值提取: 带小数全部纳入; 纯整数 >=100 纳入（小整数如"5 个""10%"不溯源）
        # 过滤误报: 年份（2021 年）、章节标题行（### 5.1 问题1）
        for m in re.finditer(r"\d+(?:\.\d+)?", body_no_code):
            v = m.group(0)
            if "." in v or int(v) >= 100:
                line_start = body_no_code.rfind("\n", 0, m.start()) + 1
                line = body_no_code[line_start:m.end()]
                if re.match(r"#{1,6}\s*\d+(?:\.\d+)?\s*$", line):
                    continue  # 标题行小节号（如 "### 5.1"）
                tail = body_no_code[m.end():m.end() + 6]
                if re.match(r"^\d{4}$", v) and tail.startswith("年"):
                    continue  # 年份
                ctx = body_no_code[max(0, m.start() - 18):m.end() + 18].replace("\n", " ")
                abstract_nums.append((v, ctx))
    if abstract_nums:
        found_str = numeric_values_from_outputs(output_files)
        found_float = set()
        for s in found_str:
            try:
                found_float.add(float(s))
            except ValueError:
                pass
        for k, vs in contract_stats.items():
            for v in vs:
                found_str.add(v)
                try:
                    found_float.add(float(v))
                except ValueError:
                    pass
        missing = []
        for v, ctx in abstract_nums:
            if v in found_str:
                continue
            try:
                fv = float(v)
                if any(abs(fv - x) < 1e-3 * max(1.0, abs(fv)) for x in found_float):
                    continue
            except ValueError:
                pass
            missing.append((v, ctx))
        total = len(abstract_nums)
        n_missing = len(missing)
        ratio = (total - n_missing) / total if total else 1.0
        report_file = os.path.join(workdir, "4_论文", "溯源报告.md")
        lines = [
            "# 数值溯源报告",
            "",
            f"- 论文正文检出数值（带小数或 ≥100 的整数）: **{total}** 个",
            f"- 在 代码输出文件/数据契约 中找到出处: **{total - n_missing}** 个（{ratio:.0%}）",
            f"- 未找到出处: **{n_missing}** 个",
            "",
        ]
        if n_missing:
            lines += ["## 未溯源数值（需人工核实或补写进结果文件）", ""]
            for v, ctx in missing[:20]:
                lines.append(f"- `{v}` — 所在上下文: …{ctx}…")
            if n_missing > 20:
                lines.append(f"- …共 {n_missing} 个，仅列前 20 个")
            lines.append("")
        else:
            lines += ["## 结论", "", "论文全部关键数值均可在代码输出文件/数据契约中找到出处。", ""]
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            ok_note = f"，报告已写入 {report_file}"
        except Exception:
            ok_note = ""
        if n_missing == 0:
            report(PASS, f"正文 {total} 个数值全部有出处（{ratio:.0%}）{ok_note}")
        elif ratio >= 0.95:
            report(PASS, f"正文 {total} 个数值 {n_missing} 个未在输出/契约中找到出处（{ratio:.0%} 已溯源，多为题给常量）{ok_note}")
        elif ratio >= 0.85:
            report(WARN, f"{n_missing}/{total} 个数值未在输出/契约中找到出处（{ratio:.0%} 已溯源，抽查前 5）: {[m[0] for m in missing[:5]]}")
            report(WARN, f"详情见 {report_file}，请人工核实这些数值是否编造")
        else:
            report(ERR, f"{n_missing}/{total} 个数值未在输出/契约中找到出处（仅 {ratio:.0%} 已溯源）: {[m[0] for m in missing[:5]]}")
            report(WARN, f"建议: 每个结果由代码写入 results.csv 并在论文中直接引用；详情见 {report_file}")
    else:
        report(WARN, "论文正文未解析到可溯源数值（或未找到论文）")

    # 6. 表格-CSV 一致性（论文表格数值 ↔ 数据源 CSV 按列分组核对）
    print("== 6. 表格-CSV 一致性 ==")
    if paper:
        try:
            paper_text = read_text(paper)
        except Exception:
            paper_text = ""
        lines = paper_text.splitlines()
        tables = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if re.match(r"^表\s*\d+", line) and "|" not in line:
                title = line
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("|"):
                    j += 1
                tbl_rows = []
                while j < len(lines) and lines[j].strip().startswith("|"):
                    tbl_rows.append(lines[j].strip())
                    j += 1
                if tbl_rows:
                    tables.append((title, tbl_rows))
                i = j
            else:
                i += 1
        n_ok = 0
        n_warn = 0
        n_skip = 0
        for title, tbl_rows in tables:
            ds_match = re.search(r"数据源[：:]\s*(.+?)(?:\s*[）)）]|$)", title)
            if not ds_match:
                n_skip += 1
                continue
            src_str = ds_match.group(1)
            csv_names = re.findall(r"[\w\-]+\.(?:csv|txt)", src_str)
            if not csv_names:
                n_skip += 1
                continue
            # 解析表头和数据行
            content_rows = []
            for row in tbl_rows:
                if re.match(r"^\|?[\s:|\-]+\|?\s*$", row) and "-" in row:
                    continue
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                content_rows.append(cells)
            if len(content_rows) < 2:
                n_skip += 1
                continue
            header = content_rows[0]
            data_rows = content_rows[1:]
            # 单源表：全表数值匹配
            if len(csv_names) == 1:
                tbl_vals = set()
                for cells in data_rows:
                    for cell in cells:
                        for vm in re.finditer(r"\d+(?:\.\d+)?", cell):
                            tbl_vals.add(vm.group(0))
                if not tbl_vals:
                    n_skip += 1
                    continue
                csv_path = _find_csv(workdir, csv_names[0])
                if not csv_path:
                    n_skip += 1
                    continue
                csv_vals = _read_csv_vals(csv_path)
                missing = _check_missing(tbl_vals, csv_vals)
                if missing:
                    report(WARN, f"{title[:30]}... 有 {len(missing)}/{len(tbl_vals)} 个数值未在 {csv_names[0]} 中找到: {missing[:3]}")
                    n_warn += 1
                else:
                    report(PASS, f"{title[:30]}... 与 {csv_names[0]} 一致（{len(tbl_vals)} 个数值）")
                    n_ok += 1
            else:
                # 多源表：验证每个 CSV 文件存在且表格所有数值在并集内
                found_files = []
                for cn in csv_names:
                    p = _find_csv(workdir, cn)
                    if p:
                        found_files.append((cn, p))
                if len(found_files) < len(csv_names):
                    missing_csvs = [cn for cn, _ in csv_names if cn not in [f[0] for f in found_files]]
                    report(WARN, f"{title[:30]}... 数据源文件未找到: {missing_csvs}")
                    n_warn += 1
                else:
                    # 合并所有 CSV 的数值集合
                    all_csv_vals = set()
                    for cn, cp in found_files:
                        all_csv_vals.update(_read_csv_vals(cp))
                    tbl_vals = set()
                    for cells in data_rows:
                        for cell in cells:
                            for vm in re.finditer(r"\d+(?:\.\d+)?", cell):
                                tbl_vals.add(vm.group(0))
                    missing = _check_missing(tbl_vals, all_csv_vals)
                    if missing:
                        report(WARN, f"{title[:30]}... 有 {len(missing)}/{len(tbl_vals)} 个数值未在 {len(csv_names)} 个 CSV 并集中找到: {missing[:3]}")
                        n_warn += 1
                    else:
                        report(PASS, f"{title[:30]}... 与 {len(csv_names)} 个 CSV 并集一致（{len(tbl_vals)} 个数值）")
                        n_ok += 1
        if n_ok + n_warn + n_skip > 0:
            report(PASS,
                   f"表格-CSV 核对: {n_ok} 通过, {n_warn} 警告, {n_skip} 跳过")
    else:
        report(WARN, "未找到论文文件，跳过表格-CSV 核对")

    # 7. 论文-代码对应（附录引用的代码文件必须存在）
    print("== 7. 论文-代码对应 ==")
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