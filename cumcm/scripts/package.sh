#!/usr/bin/env bash
# 支撑材料打包脚本 (macOS / Linux)
# 用法: ./package.sh <工作目录> [论文pdf路径] [输出zip路径]
set -euo pipefail

WORK_DIR="$(cd "$1" && pwd)"
PAPER="${2:-}"
OUT_ZIP="${3:-$WORK_DIR/支撑材料.zip}"

if [[ -z "$PAPER" ]]; then
  PAPER="$(ls "$WORK_DIR/4_论文"/*.pdf 2>/dev/null | head -n1 || true)"
  if [[ -z "$PAPER" ]]; then
    echo "错误: 4_论文 下没有 PDF，请先编译论文或指定论文路径" >&2
    exit 1
  fi
fi

TMP="$(mktemp -d)"
mkdir -p "$TMP/代码" "$TMP/支撑材料"

[[ -d "$WORK_DIR/2_代码" ]] && cp -R "$WORK_DIR/2_代码" "$TMP/代码/"
[[ -d "$WORK_DIR/5_支撑材料" ]] && cp -R "$WORK_DIR/5_支撑材料" "$TMP/支撑材料/"
[[ -f "$WORK_DIR/数据清单.md" ]] && cp "$WORK_DIR/数据清单.md" "$TMP/"

(cd "$TMP" && zip -qr "$OUT_ZIP" . -x '*.DS_Store')
rm -rf "$TMP"

echo "[完成] 支撑材料: $OUT_ZIP"
echo "[完成] 论文:     $PAPER"
