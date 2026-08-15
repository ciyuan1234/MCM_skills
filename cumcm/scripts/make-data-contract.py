#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据契约生成器 (make-data-contract.py)
用法:
    python make-data-contract.py <数据目录> [-o 输出路径]
示例:
    python make-data-contract.py 1_数据
    python make-data-contract.py 1_数据 -o 1_数据/data_contract.json

功能:
    扫描数据目录中的 csv/txt/xlsx 文件，为每个文件记录:
      - 文件指纹 sha256（证明代码若读取该文件，重算出的统计必然与契约一致）
      - 行数/列数/字段名
      - 数值列统计量 (sum/mean/max/min/count)
    输出 data_contract.json —— 后续 verify.py 用它核对"代码是否真的读了真实数据"。

规则（配合 cumcm skill）:
    Phase 1 处理完每个附件后必须运行本脚本生成契约。
    论文/代码中出现的任何统计数值，都应能在契约 stats 或代码输出文件中找到出处。
"""

import csv
import hashlib
import io
import json
import os
import re
import sys

NUMERIC_RE = re.compile(r"^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_lines_any_encoding(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").splitlines()


def sniff_delimiter(line):
    counts = {d: line.count(d) for d in [",", "\t", ";", "|"]}
    return max(counts, key=counts.get) if max(counts.values()) > 0 else ","


def is_numeric(v):
    return bool(NUMERIC_RE.match(v.strip()))


def is_category_col(name, vals):
    """是否把该列当作分组（对象数来源）。日期/时间/序号类不算。"""
    low = name.lower()
    if any(k in low for k in ("日期", "时间", "序号", "编号", "date", "time", "id")):
        return False
    if vals and all(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", str(v)) for v in vals):
        return False
    return True


def describe_csv(path, limit=200000):
    lines = read_lines_any_encoding(path)
    if not lines:
        return None
    delim = sniff_delimiter(lines[0])
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        r = next(csv.reader([ln], delimiter=delim))
        rows.append(r)
    if not rows:
        return None
    header = rows[0]
    ncols = max(len(r) for r in rows)
    data_rows = rows[1:]
    stats = {}
    categories = {}
    for c in range(ncols):
        col_vals = []
        for r in data_rows:
            if c < len(r) and r[c].strip():
                col_vals.append(r[c])
        if not col_vals:
            continue
        nums = [float(v) for v in col_vals if is_numeric(v)]
        if nums and len(nums) == len(col_vals):
            stats[header[c] if c < len(header) else f"col{c+1}"] = {
                "count": len(nums),
                "sum": round(sum(nums), 4),
                "mean": round(sum(nums) / len(nums), 4),
                "max": round(max(nums), 4),
                "min": round(min(nums), 4),
            }
        else:
            # 文本列：低基数列记为分组（对象数来源，verify.py 据此核对图表元素数量）
            distinct = {v for v in col_vals}
            colname = header[c] if c < len(header) else f"col{c+1}"
            if (len(distinct) <= 100 and 1 < len(distinct) <= len(col_vals)
                    and is_category_col(colname, col_vals)):
                categories[colname] = len(distinct)
    return {
        "delimiter": delim,
        "rows": len(rows),       # 含表头
        "data_rows": len(data_rows),
        "cols": ncols,
        "columns": header,
        "stats": stats,
        "categories": categories,
    }


def describe_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        return {"note": "缺少 openpyxl，无法解析 xlsx（pip install openpyxl 后重试）"}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    def describe_sheet(ws):
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return None
        header = [str(c) if c is not None else "" for c in rows[0]]
        stats = {}
        categories = {}
        ncols = len(header)
        for c in range(ncols):
            col_vals = [r[c] for r in rows[1:] if c < len(r) and r[c] is not None]
            nums = [float(v) for v in col_vals if isinstance(v, (int, float))]
            if nums and len(nums) == len(col_vals):
                stats[header[c]] = {
                    "count": len(nums),
                    "sum": round(sum(nums), 4),
                    "mean": round(sum(nums) / len(nums), 4),
                    "max": round(max(nums), 4),
                    "min": round(min(nums), 4),
                }
            else:
                distinct = {str(v) for v in col_vals}
                if (len(distinct) <= 100 and 1 < len(distinct) <= len(col_vals)
                        and is_category_col(header[c], col_vals)):
                    categories[header[c]] = len(distinct)
        return {"rows": len(rows), "data_rows": len(rows) - 1, "cols": ncols,
                "columns": header, "stats": stats, "categories": categories}

    sheets = {}
    active_title = wb.active.title
    for ws in wb.worksheets:
        d = describe_sheet(ws)
        if d:
            sheets[ws.title] = d
    wb.close()
    if not sheets:
        return {"note": "工作表为空"}
    # 顶层合并（兼容 verify.py 从文件条目顶层读取 stats/categories 的旧逻辑）
    merged_stats, merged_cats = {}, {}
    for d in sheets.values():
        merged_stats.update(d.get("stats", {}))
        merged_cats.update(d.get("categories", {}))
    first = next(iter(sheets.values()))
    return {"sheets": {k: v for k, v in sheets.items()}, "active_sheet": active_title,
            "rows": first["rows"], "data_rows": first["data_rows"], "cols": first["cols"],
            "columns": first["columns"], "stats": merged_stats, "categories": merged_cats}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    data_dir = sys.argv[1]
    out = "data_contract.json"
    if "-o" in sys.argv:
        i = sys.argv.index("-o")
        if i + 1 < len(sys.argv):
            out = sys.argv[i + 1]

    if not os.path.isdir(data_dir):
        print(f"[错误] 目录不存在: {data_dir}", file=sys.stderr)
        sys.exit(2)

    files = []
    for name in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, name)
        if not os.path.isfile(full):
            continue
        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        desc = None
        if ext in ("csv", "txt", "dat"):
            desc = describe_csv(full)
        elif ext == "xlsx":
            desc = describe_xlsx(full)
        else:
            continue
        entry = {"path": name, "sha256": sha256_of(full)}
        if desc:
            entry.update(desc)
        files.append(entry)

    if not files:
        print("[警告] 目录下没有可分析的 csv/txt/xlsx 数据文件", file=sys.stderr)

    contract = {
        "_说明": "数据契约。Phase 1 处理附件后生成；论文/代码中的统计数值必须在 stats 或代码输出文件中可溯源。",
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "generator": "make-data-contract.py",
        "files": files,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    print(f"[完成] 数据契约已写入: {out}")
    print(f"       分析文件数: {len(files)}")
    for e in files:
        cols = e.get("cols", "?")
        rows = e.get("rows", "?")
        print(f"       - {e['path']}  rows={rows} cols={cols}  sha256={e['sha256'][:12]}...")


if __name__ == "__main__":
    main()