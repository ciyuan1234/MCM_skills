# CUMCM 参赛 skill 安装脚本（Windows / PowerShell 5.1+）
# 用法:
#   .\install.ps1          安装到 Claude Code / Codex / opencode 三个工具目录
#   .\install.ps1 -Uninstall  卸载
param(
    [switch]$Uninstall,
    [switch]$Quiet
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$SkillName = 'cumcm'
$Source = Join-Path $PSScriptRoot $SkillName
if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md'))) {
    Write-Error "找不到 skill 源目录: $Source"
    exit 1
}

$Targets = [ordered]@{
    'Claude Code' = Join-Path $env:USERPROFILE ".claude\skills\$SkillName"
    'Codex (v1)'  = Join-Path $env:USERPROFILE ".codex\skills\$SkillName"
    'Codex/AGENTS'= Join-Path $env:USERPROFILE ".agents\skills\$SkillName"
    'opencode'    = Join-Path $env:USERPROFILE ".config\opencode\skills\$SkillName"
}

if ($Uninstall) {
    foreach ($k in $Targets.Keys) {
        if (Test-Path -LiteralPath $Targets[$k]) {
            Remove-Item -LiteralPath $Targets[$k] -Recurse -Force
            Write-Host "[卸载] $k -> $($Targets[$k])"
        }
    }
    Write-Host "cumcm skill 已从所有工具目录卸载。"
    exit 0
}

foreach ($k in $Targets.Keys) {
    $dest = $Targets[$k]
    $parent = Split-Path $dest -Parent
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if (Test-Path -LiteralPath $dest) {
        Remove-Item -LiteralPath $dest -Recurse -Force
    }
    Copy-Item -LiteralPath $Source -Destination $dest -Recurse -Force
    if (-not $Quiet) { Write-Host "[安装] $k -> $dest" }
}

Write-Host ""
Write-Host "cumcm skill 安装完成。已装到以下工具（重启对应工具后生效）:"
foreach ($k in $Targets.Keys) {
    Write-Host ("  - {0}: {1}" -f $k, $Targets[$k])
}
Write-Host ""
Write-Host "提示: opencode 会自动加载 ~/.claude/skills 与 ~/.agents/skills，无需额外配置。"
Write-Host "更新 skill 后重新运行本脚本即可覆盖旧版本。"
