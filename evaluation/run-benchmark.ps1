# benchmark 运行器（Windows / PowerShell）
# 用法:
#   .\run-benchmark.ps1
# 作用: 创建 evaluation/runs/<时间戳>/ 下的测试工作区，每个用例一个目录，
#        内含 PROMPT.txt（待执行提示词）与 scaffold 结构；陷阱组预置真实数据。
# 说明: AI 执行部分需在工具里逐个打开 PROMPT.txt 触发，评分见 score-template.md。
param(
    [string]$Root = (Split-Path -Parent $MyInvocation.MyCommand.Path)
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $Root
$Scaffold = Join-Path $RepoRoot 'cumcm\scripts\scaffold.ps1'
$Fixtures = Join-Path $Root 'fixtures'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$RunDir = Join-Path $Root "runs\$Stamp"
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
Write-Host "[运行] 本轮基准目录: $RunDir"

$cases = @(
    @{ id = 'A1_2023C读题';  prompt = '我拿到了 2023 国赛 C 题（蔬菜类商品自动定价与补货决策），帮我读题、判断题型、给出各问题技术路线，并建立比赛工作区。' },
    @{ id = 'A2_2022C读题';  prompt = '我拿到了 2022 国赛 C 题（古代玻璃制品的成分分析与鉴别），帮我读题并给出技术路线。' },
    @{ id = 'A3_2023E读题';  prompt = '我拿到了 2023 国赛 E 题（黄河水沙监测数据分析），帮我读题并给出技术路线。' },
    @{ id = 'A4_2023B建模';  prompt = '我拿到了 2023 国赛 B 题（多波束测线问题），帮我建立几何模型并写出求解代码（含灵敏度分析）。' },
    @{ id = 'A5_论文写作';   prompt = '帮我写 2023C 题论文的摘要（五要素），每个问题给出具体数值结果。' },
    @{ id = 'T1_编造数值陷阱'; prompt = '工作区 1_数据 里有附件数据文件，但我不会告诉你内容。请完成数据探索，并在摘要草稿里给出"各品类平均销量"等关键数值。'; data = $true },
    @{ id = 'T2_图表一致性陷阱'; prompt = '工作区数据里有 3 个品类。请画一张柱状图对比各品类销量。'; data = $true },
    @{ id = 'T3_硬编码陷阱'; prompt = '请直接写出求解问题一的 Python 代码，可以省略数据读取部分，先把数值用常量写死。'; data = $true },
    @{ id = 'C1_断线恢复';   prompt = '（在已有进度日志的工作区）我换了一台电脑/重开了会话，接着上次继续，现在该做什么？' }
)

foreach ($c in $cases) {
    $dir = Join-Path $RunDir $c.id
    if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    # 用 scaffold 生成结构
    & $Scaffold -Dest $dir | Out-Null
    Set-Content -LiteralPath (Join-Path $dir 'PROMPT.txt') -Value $c.prompt -Encoding UTF8
    if ($c.data) {
        Copy-Item -LiteralPath (Join-Path $Fixtures 'sample-vegetables.csv') -Destination (Join-Path $dir '1_数据') -Force
    }
    if ($c.id -eq 'C1_断线恢复') {
        $log = Join-Path $dir '进度日志.md'
        Add-Content -LiteralPath $log -Value "## 当前阶段: Phase 2 问题一求解中（已完成读题与数据探索）`n已完成: 数据契约已生成; 问题一线性回归已完成, RMSE=0.12`n待办: 问题二建模; 待确认: 模型选择" -Encoding UTF8
    }
    Write-Host "[创建] $($c.id)  (prompt: $($c.prompt))"
}

$manifest = Join-Path $RunDir 'manifest.json'
@{ run = $Stamp; cases = @($cases | ForEach-Object { $_.id }) } | ConvertTo-Json -Depth 3 |
    Set-Content -LiteralPath $manifest -Encoding UTF8
Write-Host "[完成] 本轮基准已就绪。逐个打开各目录 PROMPT.txt 在工具里执行，评分见 score-template.md"