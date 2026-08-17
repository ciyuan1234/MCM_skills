#!/usr/bin/env python3
"""
run_golden.py — 黄金测试集自动回归脚本
用法:
  python scripts/run_golden.py <workdir> [--problem 2023_C] [--verbose]
  python scripts/run_golden.py runs/tier2_2023C
  python scripts/run_golden.py runs/tier2_2023C --problem 2023_C --verbose

读取 evaluation/golden_problems/<problem>/check_points.json，逐项检查：
  - file_exists: 文件是否存在
  - output_exists: 输出文件是否存在（支持 ** 通配）
  - value_range: CSV 列值是否在 [min, max] 范围内
  - file_count_min: 目录下文件数是否 ≥ min_count

退出码:
  0 = 全部 critical 检查通过
  1 = 存在 critical 检查失败
  2 = 参数错误
"""
import sys
import os
import json
import glob
import csv
import argparse
from pathlib import Path


def find_golden_problems_dir():
    """查找 golden_problems 目录（从脚本位置向上查找）"""
    script_dir = Path(__file__).resolve().parent
    # 尝试 cumcm/evaluation/golden_problems
    candidate = script_dir.parent / "evaluation" / "golden_problems"
    if candidate.is_dir():
        return candidate
    # 尝试顶层 evaluation/golden_problems
    candidate = script_dir.parent.parent / "evaluation" / "golden_problems"
    if candidate.is_dir():
        return candidate
    # 尝试同级 golden_problems
    candidate = script_dir / "golden_problems"
    if candidate.is_dir():
        return candidate
    return None


def resolve_path(base_dir, pattern):
    """解析路径模式（支持 ** 通配符）"""
    full = os.path.join(base_dir, pattern)
    if "**" in full:
        matches = glob.glob(full, recursive=True)
        return matches if matches else []
    else:
        return [full] if os.path.exists(full) else []


def check_file_exists(base_dir, cp):
    """检查文件是否存在"""
    matches = resolve_path(base_dir, cp["path"])
    passed = len(matches) > 0
    detail = matches[0] if matches else cp["path"]
    return passed, detail


def check_output_exists(base_dir, cp):
    """检查输出文件是否存在（同 file_exists，语义区分）"""
    return check_file_exists(base_dir, cp)


def check_value_range(base_dir, cp):
    """检查 CSV 列值是否在范围内（支持宽表和长表两种格式）"""
    matches = resolve_path(base_dir, cp["file"])
    if not matches:
        return False, f"文件不存在: {cp['file']}"

    filepath = matches[0]
    column = cp["column"]
    min_val = cp["min"]
    max_val = cp["max"]

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:  # utf-8-sig 自动剥离 BOM
            reader = csv.DictReader(f)
            fields = reader.fieldnames

            # 宽表格式：column 直接是列名
            if column in fields:
                values = []
                for row in reader:
                    try:
                        val = float(row[column])
                        values.append(val)
                    except (ValueError, TypeError):
                        continue
                if not values:
                    return False, f"列 '{column}' 无数值数据"
                out_of_range = [v for v in values if v < min_val or v > max_val]
                if out_of_range:
                    return False, f"列 '{column}' 有 {len(out_of_range)}/{len(values)} 个值超出范围 [{min_val}, {max_val}]"
                return True, f"列 '{column}' {len(values)} 个值均在 [{min_val}, {max_val}] 内"

            # 长表格式（指标/数值）：column 是"指标"列中的值
            if "指标" in fields and "数值" in fields:
                for row in reader:
                    if row.get("指标", "").strip() == column:
                        try:
                            val = float(row["数值"])
                            if min_val <= val <= max_val:
                                return True, f"指标 '{column}' = {val}，在 [{min_val}, {max_val}] 内"
                            else:
                                return False, f"指标 '{column}' = {val}，超出范围 [{min_val}, {max_val}]"
                        except (ValueError, TypeError):
                            return False, f"指标 '{column}' 值无法转换为数值: {row.get('数值')}"
                return False, f"未找到指标 '{column}'"

            return False, f"列 '{column}' 不存在于 {filepath}（可用列: {fields}）"
    except Exception as e:
        return False, f"读取失败: {e}"


def check_file_count_min(base_dir, cp):
    """检查目录下文件数是否 ≥ min_count"""
    pattern = os.path.join(base_dir, cp["path"])
    if "**" in pattern:
        files = glob.glob(pattern, recursive=True)
    else:
        # 只匹配一层
        dir_part = os.path.dirname(pattern)
        base_part = os.path.basename(pattern)
        if os.path.isdir(dir_part):
            files = [f for f in glob.glob(os.path.join(dir_part, base_part)) if os.path.isfile(f)]
        else:
            files = []

    min_count = cp.get("min_count", 1)
    passed = len(files) >= min_count
    detail = f"找到 {len(files)} 个文件，要求 ≥ {min_count}"
    return passed, detail


CHECKERS = {
    "file_exists": check_file_exists,
    "output_exists": check_output_exists,
    "value_range": check_value_range,
    "file_count_min": check_file_count_min,
}


def auto_detect_problem(workdir):
    """尝试从工作区推断 problem_id"""
    # 查看 data_contract.json
    contract_path = os.path.join(workdir, "1_数据", "data_contract.json")
    if os.path.exists(contract_path):
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                contract = json.load(f)
            # 从文件名推断
            files = contract.get("files", [])
            filenames = [os.path.basename(f.get("path", "")) for f in files]
            if any("2023" in fn for fn in filenames):
                return "2023_C"
            if any("2022" in fn or "文物" in fn for fn in filenames):
                return "2022_C"
            if any("2021" in fn or "供应商" in fn for fn in filenames):
                return "2021_C"
        except Exception:
            pass

    # 从目录名推断
    basename = os.path.basename(workdir)
    if "2023" in basename:
        return "2023_C"
    if "2022" in basename:
        return "2022_C"
    if "2021" in basename:
        return "2021_C"

    return None


def run_checks(workdir, problem_id, verbose=False):
    """运行所有检查点"""
    golden_dir = find_golden_problems_dir()
    if golden_dir is None:
        print("ERROR: 找不到 golden_problems 目录")
        return 2

    check_file = golden_dir / problem_id / "check_points.json"
    if not check_file.exists():
        print(f"ERROR: 找不到检查点文件 {check_file}")
        return 2

    with open(check_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    checks = data.get("check_points", [])
    if not checks:
        print("WARNING: check_points.json 中没有检查点")
        return 0

    print(f"=" * 60)
    print(f"Golden Test: {problem_id}")
    print(f"Workdir: {workdir}")
    print(f"Checks: {len(checks)}")
    print(f"=" * 60)

    passed_count = 0
    failed_critical = 0
    failed_warning = 0

    for cp in checks:
        cp_id = cp["id"]
        cp_type = cp["type"]
        cp_desc = cp["description"]
        cp_severity = cp.get("severity", "critical")

        checker = CHECKERS.get(cp_type)
        if checker is None:
            print(f"  [{cp_id}] SKIP  未知类型: {cp_type}")
            continue

        passed, detail = checker(workdir, cp)
        status = "PASS" if passed else "FAIL"

        if passed:
            passed_count += 1
            if verbose:
                print(f"  [{cp_id}] {status}  {cp_desc}: {detail}")
            else:
                print(f"  [{cp_id}] {status}  {cp_desc}")
        else:
            if cp_severity == "critical":
                failed_critical += 1
                print(f"  [{cp_id}] {status}  {cp_desc}: {detail}")
            else:
                failed_warning += 1
                if verbose:
                    print(f"  [{cp_id}] {status}  (warning) {cp_desc}: {detail}")
                else:
                    print(f"  [{cp_id}] {status}  (warning) {cp_desc}")

    print(f"=" * 60)
    print(f"Results: {passed_count} passed, {failed_critical} critical failed, {failed_warning} warning failed")
    if failed_critical > 0:
        print(f"OVERALL: FAILED")
        return 1
    else:
        print(f"OVERALL: PASSED")
        return 0


def main():
    parser = argparse.ArgumentParser(description="黄金测试集自动回归")
    parser.add_argument("workdir", help="工作区路径（如 runs/tier2_2023C）")
    parser.add_argument("--problem", help="问题ID（如 2023_C），不指定则自动检测")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()

    workdir = os.path.abspath(args.workdir)
    if not os.path.isdir(workdir):
        print(f"ERROR: 工作区不存在: {workdir}")
        return 2

    problem_id = args.problem
    if not problem_id:
        problem_id = auto_detect_problem(workdir)
        if not problem_id:
            print("ERROR: 无法自动检测问题ID，请用 --problem 指定")
            return 2
        print(f"Auto-detected problem: {problem_id}")

    return run_checks(workdir, problem_id, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
