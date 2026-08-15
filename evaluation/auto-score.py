#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动评分器 (auto-score.py) —— 三层回归的客观打分引擎
用法:
    python auto-score.py <工作目录> [-o 输出.json] [--efficiency N] [--trigger N]
功能:
    1. 运行 cumcm/scripts/checks.py 与 verify.py 解析结果（错误数/章节/摘要指标）
    2. 检查工作区产物: 数据契约 / PDF / 图表 / 代码 / 输出文件 / 进度日志
    3. 计算客观分: 正确性40 + 质量30 + 流程15 = 85 分自动部分
       （效率10/触发5 为人工项，通过 --efficiency/--trigger 传入，默认取中值）
    4. 输出 JSON 指标 + 人类可读报告
退出码: 0 = 正常; 非 0 = 工作目录无效
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKS = os.path.join(ROOT, "cumcm", "scripts", "checks.py")
VERIFY = os.path.join(ROOT, "cumcm", "scripts", "verify.py")


def run_tool(py_script, args, cwd=None):
    try:
        r = subprocess.run(
            [sys.executable, py_script] + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300, cwd=cwd)
        return r.stdout + r.stderr
    except Exception as e:
        return f"[错误] 工具运行失败: {e}"


def count(line_text, patterns):
    return len(re.findall(patterns, line_text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--efficiency", type=float, default=7.0, help="人工效率分 0-10")
    ap.add_argument("--trigger", type=float, default=5.0, help="人工触发分 0-5")
    args = ap.parse_args()

    wd = args.workdir
    if not os.path.isdir(wd):
        print(f"[错误] 工作目录不存在: {wd}")
        sys.exit(2)

    # ---------- 1. checks.py / verify.py ----------
    paper_path = os.path.join(wd, "4_论文", "paper.md")
    checks_out = run_tool(CHECKS, [paper_path, wd], cwd=wd)
    verify_out = run_tool(VERIFY, [wd], cwd=wd)
    checks_err = count(checks_out, r"\[错误\]")
    checks_warn = count(checks_out, r"\[警告\]")
    verify_err = count(verify_out, r"\[错误\]")
    verify_warn = count(verify_out, r"\[警告\]")
    chapters_found = min(7, count(checks_out, r"已找到章节"))
    abstract_nums = 0
    m = re.search(r"摘要(?:仅|含) (\d+) 处数值", checks_out)
    if m:
        abstract_nums = int(m.group(1))

    # ---------- 2. 工作区产物 ----------
    contract = os.path.isfile(os.path.join(wd, "1_数据", "data_contract.json"))
    pdf = bool(glob.glob(os.path.join(wd, "4_论文", "*.pdf")))
    figs = glob.glob(os.path.join(wd, "3_图表", "*.*"))
    fig_files = [f for f in figs if f.lower().endswith((".png", ".jpg", ".jpeg", ".eps", ".pdf", ".svg"))]
    code_files = []
    for ext in ("*.py", "*.m", "*.r"):
        code_files += glob.glob(os.path.join(wd, "2_代码", "**", ext), recursive=True)
    out_files = glob.glob(os.path.join(wd, "2_代码", "**", "results*.*"), recursive=True) + \
                glob.glob(os.path.join(wd, "2_代码", "**", "*.out"), recursive=True) + \
                glob.glob(os.path.join(wd, "2_代码", "**", "运行日志*.*"), recursive=True)
    progress_log = os.path.isfile(os.path.join(wd, "进度日志.md"))
    dirs_ok = all(os.path.isdir(os.path.join(wd, d)) for d in
                  ("0_赛题", "1_数据", "2_代码", "3_图表", "4_论文", "5_支撑材料"))

    # ---------- 3. 打分 ----------
    correctness = max(0.0, 40 - 20 * checks_err - 20 * verify_err)
    quality = (chapters_found / 7.0 * 12
               + min(abstract_nums, 15) / 15.0 * 8
               + min(len(fig_files), 4) / 4.0 * 5
               + (3 if contract else 0)
               + (2 if pdf else 0))
    quality = round(min(30, quality), 1)
    process = (5 if progress_log else 0) + (5 if contract else 0) + (5 if dirs_ok else 0)
    efficiency = max(0.0, min(10, args.efficiency))
    trigger = max(0.0, min(5, args.trigger))

    auto_total = round(correctness + quality + process, 1)      # 85 分制自动部分
    grand_total = round(auto_total + efficiency + trigger, 1)   # 100 分制

    metrics = {
        "workdir": wd,
        "checks_errors": checks_err, "checks_warnings": checks_warn,
        "verify_errors": verify_err, "verify_warnings": verify_warn,
        "chapters_found": chapters_found, "abstract_nums": abstract_nums,
        "data_contract": contract, "pdf_exported": pdf,
        "figure_files": len(fig_files), "code_files": len(code_files),
        "output_files": len(out_files), "progress_log": progress_log,
        "scaffold_dirs": dirs_ok,
    }
    scores = {
        "correctness(40)": round(correctness, 1),
        "quality(30)": quality,
        "process(15)": process,
        "efficiency(10, manual)": efficiency,
        "trigger(5, manual)": trigger,
        "auto_total(85)": auto_total,
        "grand_total(100)": grand_total,
    }

    # ---------- 4. 报告 ----------
    print("== 自动评分报告 ==")
    print(f"  checks.py 错误 {checks_err} / 警告 {checks_warn}")
    print(f"  verify.py 错误 {verify_err} / 警告 {verify_warn}")
    print(f"  章节 {chapters_found}/7 | 摘要数值 {abstract_nums} | 图 {len(fig_files)}")
    print(f"  数据契约 {contract} | PDF {pdf} | 代码 {len(code_files)} | 输出文件 {len(out_files)} | 进度日志 {progress_log}")
    print(f"  得分: 正确性 {scores['correctness(40)']}/40  质量 {scores['quality(30)']}/30  流程 {scores['process(15)']}/15")
    print(f"  自动总分 {auto_total}/85  + 人工(效率{args.efficiency}/触发{args.trigger}) = {grand_total}/100")
    verdict = "PASS(硬闸门通过)" if (checks_err == 0 and verify_err == 0) else "FAIL(存在错误，禁止发布)"
    print(f"  硬闸门: {verdict}")

    payload = {"metrics": metrics, "scores": scores, "hard_gate": verdict,
               "auto_score": auto_total, "grand_total": grand_total}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[完成] 评分结果已写入: {args.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()