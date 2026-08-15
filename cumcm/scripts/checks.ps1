# checks.py 的 PowerShell 包装（Windows）
# 用法:
#   .\checks.ps1                   默认检查 4_论文\paper.md，工作目录为当前目录
#   .\checks.ps1 -Paper 4_论文\论文.md -WorkDir D:\2026_国赛1234
param(
    [string]$Paper = '4_论文\paper.md',
    [string]$WorkDir = '.'
)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "未找到 python，请先安装 Python 3.8+"
    exit 2
}
& python "$PSScriptRoot\checks.py" $Paper $WorkDir
exit $LASTEXITCODE
