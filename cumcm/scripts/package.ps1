# 支撑材料打包脚本（Windows / PowerShell）
# 用法:
#   .\package.ps1 -WorkDir D:\2026_国赛1234           打包整个工作区的支撑材料
#   .\package.ps1 -WorkDir D:\2026_国赛1234 -Paper 4_论文\论文.pdf   指定论文路径
# 打包后自动校验（官方规范第十一条 HARD）:
#   - 单个 ZIP 文件
#   - 大小 <= 20MB
#   - 包内不含 承诺书/编号专用页 文件
#   - 包内文本文件不含参赛者身份信息（学校/队号/手机号/邮箱）
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
# 2) 支撑材料目录内容（含自主查阅的数据资料、中间结果图表等）
if (Test-Path -LiteralPath (Join-Path $WorkDir '5_支撑材料')) {
    Copy-Item -LiteralPath (Join-Path $WorkDir '5_支撑材料') -Destination $tmpSup -Recurse -Force
} else {
    Write-Host "[提示] 5_支撑材料 目录不存在；官方要求支撑材料含自主查阅的数据资料与较大篇幅中间结果图表"
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

# ---- 打包后自校验（官方规范第十一条） ----
$err = 0
$zip = [System.IO.Compression.ZipFile]::OpenRead($OutZip)
try {
    $sizeMb = (Get-Item -LiteralPath $OutZip).Length / 1MB
    if ($sizeMb -gt 20) {
        Write-Host "[错误] 支撑材料 $([math]::Round($sizeMb,1))MB > 20MB（官方 HARD）"; $err = 1
    } else {
        Write-Host "[通过] 支撑材料 $([math]::Round($sizeMb,1))MB <= 20MB"
    }
    $names = $zip.Entries.FullName
    $badName = $names | Where-Object { $_ -match '承诺书|编号专用页' }
    if ($badName) {
        Write-Host "[错误] 包内文件含 承诺书/编号专用页: $($badName -join ', ')（官方 HARD）"; $err = 1
    } else {
        Write-Host "[通过] 包内无 承诺书/编号专用页 文件"
    }
    $txtEntries = $zip.Entries | Where-Object { $_.FullName -match '\.(md|txt|py|m|r)$' -and $_.Length -lt 2MB }
    foreach ($e in $txtEntries) {
        $sr = New-Object System.IO.StreamReader($e.Open(), [System.Text.Encoding]::UTF8)
        try { $content = $sr.ReadToEnd() } finally { $sr.Close() }
        if ($content -match '[\u4e00-\u9fa5]{2,3}(?:省|市|自治区)[\u4e00-\u9fa5]{0,8}(?:大学|学院)' -or
            $content -match '(?<!\d)1[3-9]\d{9}(?!\d)' -or
            $content -match '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -or
            $content -match '(?:队号|参赛队编号|队伍编号)\s*[:：]?\s*[A-Z]?\d{4,}' -or
            $content -match '(?<!\d)20\d{2}[A-Z]\s*\d{3,4}(?!\d)') {
            Write-Host "[错误] 包内 $($e.FullName) 含参赛者身份信息（官方 HARD）"; $err = 1
        }
    }
    if ($err -eq 0) { Write-Host "[通过] 包内文本文件无参赛者身份信息" }
} finally {
    $zip.Dispose()
}

Remove-Item -LiteralPath $tmp -Recurse -Force

if ($err -eq 1) {
    Write-Host "[失败] 支撑材料存在合规问题，请修复后重新打包。"
    exit 1
}
Write-Host "[完成] 支撑材料: $OutZip"
Write-Host "[完成] 论文:     $Paper"
Write-Host "提交时: 论文 PDF + 支撑材料.zip 一起上传。"
