# Tier 2 往届盲测运行器（Windows / PowerShell）
# 用法:
#   .\run-tier2.ps1 -Year 2023 -Problem C -Dest <工作目录> [-Library <资料库根目录>]
# 流程:
#   1. 从资料库 1.历年国赛赛题/<Year>年赛题/ 找到 <Problem>题 的题目文件
#   2. 解压附件（rar 需 7-Zip；zip 用 Expand-Archive）
#   3. 用 scaffold 建全新工作区，题目进 0_赛题、数据进 1_数据
#   4. 写 PROMPT.txt 与 BLIND 标记 —— 获奖论文不复制、测试中禁止读取
# 说明: 解压后由 AI 按 skill 跑完整流程，最后用 auto-score.py + blind-rubric.md 评分
param(
    [int]$Year = 2023,
    [string]$Problem = 'C',
    [string]$Dest = '',
    [string]$Library = ''
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---- 定位资料库 ----
if (-not $Library) {
    $candidate = Get-Location
    $root = (Get-Item $candidate.Path).Root
    $Library = $candidate.Path
}
$yearDir = Get-ChildItem -LiteralPath $Library -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like '1.历年国赛赛题*' } | Select-Object -First 1
if (-not $yearDir) { Write-Error "资料库中未找到 1.历年国赛赛题 目录: $Library"; exit 1 }
$yearSub = Get-ChildItem -LiteralPath $yearDir.FullName -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "$Year年赛题*" } | Select-Object -First 1
if (-not $yearSub) { Write-Error "未找到 $Year 年赛题目录"; exit 1 }

$problemFile = Get-ChildItem -LiteralPath $yearSub.FullName -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "$Problem题.*" } | Select-Object -First 1
if (-not $problemFile) { Write-Error "未找到 ${Problem}题 文件（$yearSub.FullName）"; exit 1 }

# ---- 建工作区 ----
if (-not $Dest) { $Dest = Join-Path $ScriptDir ("tier2_{0}{1}_{2:yyyyMMdd}" -f $Year, $Problem, (Get-Date)) }
if (Test-Path -LiteralPath $Dest) { Remove-Item -LiteralPath $Dest -Recurse -Force }
& (Join-Path $ScriptDir '..\cumcm\scripts\scaffold.ps1') -Dest $Dest | Out-Null

# ---- 复制题目 ----
Copy-Item -LiteralPath $problemFile.FullName -Destination (Join-Path $Dest '0_赛题') -Force
Write-Host "[题目] $($problemFile.Name) -> 0_赛题"

# ---- 解压附件 ----
$ext = $problemFile.Extension.ToLower()
$dataDest = Join-Path $Dest '1_数据'
$solved = $false
if ($ext -eq '.zip') {
    Expand-Archive -LiteralPath $problemFile.FullName -DestinationPath $dataDest -Force
    $solved = $true
} else {
    $sevenZip = Get-Command 7z -ErrorAction SilentlyContinue
    if ($sevenZip) {
        & 7z x $problemFile.FullName -o"$dataDest" -y | Out-Null
        $solved = $true
    } else {
        foreach ($p in @('C:\Program Files\7-Zip\7z.exe', 'C:\Program Files (x86)\7-Zip\7z.exe')) {
            if (Test-Path -LiteralPath $p) {
                & $p x $problemFile.FullName "-o$dataDest" -y | Out-Null
                $solved = $true
                break
            }
        }
    }
}
if (-not $solved) {
    Write-Warning "无法自动解压 $ext（需要 7-Zip）。请手动把附件解压到 $dataDest"
}

# ---- 盲测标记 ----
$prompt = "【盲测】这是 $Year 年国赛 ${Problem} 题。请按 cumcm skill 全流程作答：读题→数据探索(生成数据契约)→建模求解(每个模型含灵敏度)→论文→检查(checks/verify)→导出 PDF。`n`n约束: 不允许读取任何获奖论文/参考答案；评分只认方法学与可复现性。"
Set-Content -LiteralPath (Join-Path $Dest 'PROMPT.txt') -Value $prompt -Encoding UTF8
Set-Content -LiteralPath (Join-Path $Dest 'BLIND-MODE.txt') -Value "本次为盲测：不提供参考答案，禁止读取 2.历年国赛获奖论文。" -Encoding UTF8
Write-Host "[完成] Tier2 盲测工作区: $Dest"
Write-Host "  下一步: 在工具中打开 $Dest\PROMPT.txt 触发 skill 全流程；完成后运行 auto-score.py 评分。"