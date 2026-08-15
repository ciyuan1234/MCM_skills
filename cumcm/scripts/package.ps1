# 支撑材料打包脚本（Windows / PowerShell）
# 用法:
#   .\package.ps1 -WorkDir D:\2026_国赛1234           打包整个工作区的支撑材料
#   .\package.ps1 -WorkDir D:\2026_国赛1234 -Paper 4_论文\论文.pdf   指定论文路径
param(
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [string]$Paper = '',
    [string]$OutZip = ''
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$WorkDir = [System.IO.Path]::GetFullPath($WorkDir)
if (-not (Test-Path -LiteralPath $WorkDir)) { Write-Error "工作区不存在: $WorkDir"; exit 1 }

# 默认论文: 4_论文 下第一个 pdf
if (-not $Paper) {
    $pdf = Get-ChildItem -LiteralPath (Join-Path $WorkDir '4_论文') -Filter *.pdf -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pdf) { Write-Error "4_论文 下没有 PDF，请先编译论文或指定 -Paper"; exit 1 }
    $Paper = $pdf.FullName
}
$Paper = [System.IO.Path]::GetFullPath($Paper)

$tmp = Join-Path $env:TEMP ("cumcm_pkg_{0}" -f [guid]::NewGuid().ToString('N'))
$tmpCode = Join-Path $tmp '代码'
$tmpSup  = Join-Path $tmp '支撑材料'
New-Item -ItemType Directory -Path $tmpCode, $tmpSup -Force | Out-Null

# 1) 代码
if (Test-Path -LiteralPath (Join-Path $WorkDir '2_代码')) {
    Copy-Item -LiteralPath (Join-Path $WorkDir '2_代码') -Destination $tmpCode -Recurse -Force
}
# 2) 支撑材料目录内容
if (Test-Path -LiteralPath (Join-Path $WorkDir '5_支撑材料')) {
    Copy-Item -LiteralPath (Join-Path $WorkDir '5_支撑材料') -Destination $tmpSup -Recurse -Force
}
# 3) 数据清单说明（若有）
$manifest = Join-Path $WorkDir '数据清单.md'
if (Test-Path -LiteralPath $manifest) {
    Copy-Item -LiteralPath $manifest -Destination (Join-Path $tmp '数据清单.md') -Force
}

if (-not $OutZip) { $OutZip = Join-Path $WorkDir '支撑材料.zip' }

# 用 .NET ZipFile 打包（避免中文乱码）
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $OutZip) { Remove-Item -LiteralPath $OutZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($tmp, $OutZip, [System.IO.Compression.CompressionLevel]::Optimal, $true)

Remove-Item -LiteralPath $tmp -Recurse -Force

Write-Host "[完成] 支撑材料: $OutZip"
Write-Host "[完成] 论文:     $Paper"
Write-Host "提交时: 论文 PDF + 支撑材料.zip 一起上传。"
