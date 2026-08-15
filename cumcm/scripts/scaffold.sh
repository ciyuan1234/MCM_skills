#!/usr/bin/env bash
# 比赛工作目录生成器 (macOS / Linux)
# 用法: ./scaffold.sh [目标目录]
set -euo pipefail

YEAR="${2:-$(date +%Y)}"
TEAMID="${3:-}"
DEST="${1:-./${YEAR}_国赛${TEAMID}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/assets"

mkdir -p "$DEST"

for d in 0_赛题 1_数据 3_图表 4_论文 5_支撑材料; do
  mkdir -p "$DEST/$d"
  echo "[创建] $DEST/$d"
done
mkdir -p "$DEST/2_代码"
for i in 1 2 3 4; do
  mkdir -p "$DEST/2_代码/0${i}_问题${i}"
  echo "[创建] $DEST/2_代码/0${i}_问题${i}"
done
mkdir -p "$DEST/2_代码/common"
echo "[创建] $DEST/2_代码/common"

for t in paper-template.md paper-template.tex; do
  if [[ -f "$ASSETS_DIR/$t" ]]; then
    cp "$ASSETS_DIR/$t" "$DEST/4_论文/"
    echo "[复制] $t -> 4_论文"
  fi
done
if [[ -f "$ASSETS_DIR/progress-log-template.md" ]]; then
  cp "$ASSETS_DIR/progress-log-template.md" "$DEST/进度日志.md"
  echo "[复制] progress-log-template.md -> 进度日志.md"
fi
if [[ -f "$ASSETS_DIR/data-contract-template.json" ]]; then
  cp "$ASSETS_DIR/data-contract-template.json" "$DEST/1_数据/"
  echo "[复制] data-contract-template.json -> 1_数据"
fi
if [[ -f "$ASSETS_DIR/plot-style.py" ]]; then
  cp "$ASSETS_DIR/plot-style.py" "$DEST/3_图表/"
  echo "[复制] plot-style.py -> 3_图表"
fi

echo ""
echo "工作区已就绪: $DEST"
