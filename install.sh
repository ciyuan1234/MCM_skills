#!/usr/bin/env bash
# CUMCM 参赛 skill 安装脚本 (macOS / Linux)
# 用法: ./install.sh [--uninstall]
# 兼容 macOS 自带 bash 3.2（不用关联数组）。
set -euo pipefail

SKILL_NAME="cumcm"
SOURCE="$(cd "$(dirname "$0")" && pwd)/$SKILL_NAME"
UNINSTALL="${1:-}"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "错误: 找不到 skill 源目录: $SOURCE" >&2
  exit 1
fi

# name|dest  一行一个目标，避免 bash 3 没有 declare -A
TARGETS="
Claude Code|$HOME/.claude/skills/$SKILL_NAME
Codex (v1)|$HOME/.codex/skills/$SKILL_NAME
Codex/AGENTS|$HOME/.agents/skills/$SKILL_NAME
opencode|$HOME/.config/opencode/skills/$SKILL_NAME
Grok|$GROK_HOME/skills/$SKILL_NAME
"

if [[ "$UNINSTALL" == "--uninstall" ]]; then
  printf '%s\n' "$TARGETS" | while IFS='|' read -r name dest; do
    [[ -z "${dest:-}" ]] && continue
    if [[ -e "$dest" ]]; then
      rm -rf "$dest"
      echo "[卸载] $name -> $dest"
    fi
  done
  echo "cumcm skill 已从所有工具目录卸载。"
  exit 0
fi

printf '%s\n' "$TARGETS" | while IFS='|' read -r name dest; do
  [[ -z "${dest:-}" ]] && continue
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  cp -R "$SOURCE" "$dest"
  echo "[安装] $name -> $dest"
done

echo ""
echo "cumcm skill 安装完成。重启对应工具后生效。"
echo "提示: opencode 会自动加载 ~/.claude/skills 与 ~/.agents/skills。"
echo "Grok 目录: $GROK_HOME/skills/$SKILL_NAME"
