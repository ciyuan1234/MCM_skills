# 比赛工作目录生成器（Windows / PowerShell）
# 用法:
#   .\scaffold.ps1                      在当前目录创建 <年份>_国赛<队号>/ 工作区
#   .\scaffold.ps1 -Year 2026 -TeamID 1234
#   .\scaffold.ps1 -Dest D:\国赛2026    指定目标位置
param(
    [int]$Year = (Get-Date).Year,
    [string]$TeamID = '',
    [string]$Dest = ''
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AssetsDir = Join-Path (Split-Path $ScriptDir -Parent) 'assets'

if (-not $Dest) { $Dest = Join-Path (Get-Location) ("{0}_国赛{1}" -f $Year, $TeamID) }
$Dest = [System.IO.Path]::GetFullPath($Dest)
New-Item -ItemType Directory -Path $Dest -Force | Out-Null

$dirs = @(
    '0_赛题',      # 题目 PDF + 附件（原件，勿改动）
    '1_数据',      # 解压/整理后的数据
    '2_代码',      # 全部代码
    '3_图表',      # 论文用图、表数据
    '4_论文',      # 论文（md/tex/pdf）
    '5_支撑材料'   # 支撑材料（自造数据、说明文档等）
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path (Join-Path $Dest $d) -Force | Out-Null
    Write-Host "[创建] $Dest\$d"
}
foreach ($i in 1..4) {
    New-Item -ItemType Directory -Path (Join-Path $Dest "2_代码\0$($i)_问题$($i)") -Force | Out-Null
    Write-Host "[创建] $Dest\2_代码\0$($i)_问题$($i)"
}
New-Item -ItemType Directory -Path (Join-Path $Dest '2_代码\common') -Force | Out-Null
Write-Host "[创建] $Dest\2_代码\common"

foreach ($t in @('paper-template.md', 'paper-template.tex')) {
    $src = Join-Path $AssetsDir $t
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $Dest '4_论文') -Force
        Write-Host "[复制] $t -> 4_论文"
    }
}
$log = Join-Path $AssetsDir 'progress-log-template.md'
if (Test-Path -LiteralPath $log) {
    Copy-Item -LiteralPath $log -Destination (Join-Path $Dest '进度日志.md') -Force
    Write-Host "[复制] progress-log-template.md -> 进度日志.md"
}

Write-Host ""
Write-Host "工作区已就绪: $Dest"
Write-Host "下一步: 把赛题 PDF 和附件放进 0_赛题/，开始比赛吧。"
