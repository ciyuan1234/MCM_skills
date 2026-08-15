#!/usr/bin/env bash
# CUMCM 参赛 skill 安装脚本 (macOS / Linux)
# 用法: ./install.sh [--uninstall]
set -euo pipefail

SKILL_NAME="cumcm"
SOURCE="$(cd "$(dirname "$0")" && pwd)/$SKILL_NAME"
UNINSTALL="${1:-}"

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "错误: 找不到 skill 源目录: $SOURCE" >&2
  exit 1
fi

declare -A TARGETS=(
  ["Claude Code"]="$HOME/.claude/skills/$SKILL_NAME"
  ["Codex (v1)"]="$HOME/.codex/skills/$SKILL_NAME"
  ["Codex/AGENTS"]="$HOME/.agents/skills/$SKILL_NAME"
  ["opencode"]="$HOME/.config/opencode/skills/$SKILL_NAME"
)

if [[ "$UNINSTALL" == "--uninstall" ]]; then
  for dest in "${TARGETS[@]}"; do
    if [[ -e "$dest" ]]; then
      rm -rf "$dest"
      echo "[卸载] $dest"
    fi
  done
  echo "cumcm skill 已从所有工具目录卸载。"
  exit 0
fi

for name in "${!TARGETS[@]}"; do
  dest="${TARGETS[$name]}"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  cp -R "$SOURCE" "$dest"
  echo "[安装] $name -> $dest"
done

echo ""
echo "cumcm skill 安装完成。重启对应工具后生效。"
echo "提示: opencode 会自动加载 ~/.claude/skills 与 ~/.agents/skills。"
