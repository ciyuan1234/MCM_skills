# 论文导出脚本（Windows / PowerShell）—— Markdown/LaTeX -> PDF
# 用法:
#   .\export-paper.ps1 [-WorkDir 工作目录] [-OutDir 输出目录]
# 流程:
#   LaTeX 路线: paper.tex -> xelatex -> paper.pdf
#   Word 路线:  paper.md  -> (pandoc 或 md2docx.py) -> paper.docx -> Word COM -> paper.pdf
param(
    [string]$WorkDir = '.',
    [string]$OutDir = '',
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PaperDir = Join-Path $WorkDir '4_论文'
if (-not (Test-Path -LiteralPath $PaperDir)) { Write-Error "找不到 4_论文 目录: $PaperDir"; exit 1 }
if (-not $OutDir) { $OutDir = $PaperDir }

$md = Get-ChildItem -LiteralPath $PaperDir -Filter *.md -ErrorAction SilentlyContinue |
      Sort-Object @{ e = { $_.Name -eq 'paper.md' }; Descending = $true }, Name | Select-Object -First 1
$tex = Get-ChildItem -LiteralPath $PaperDir -Filter *.tex -ErrorAction SilentlyContinue |
      Sort-Object @{ e = { $_.Name -eq 'paper.tex' }; Descending = $true }, Name | Select-Object -First 1
$pdf = Get-ChildItem -LiteralPath $PaperDir -Filter *.pdf -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pdf -and -not $Force) {
    $md2tex = Join-Path $PSScriptRoot 'md2tex.py'
    $texOk = $true
    if ($md -and $tex -and $tex.LastWriteTime -lt $md.LastWriteTime) { $texOk = $false }
    if ($tex -and (Test-Path -LiteralPath $md2tex) -and $tex.LastWriteTime -lt (Get-Item -LiteralPath $md2tex).LastWriteTime) { $texOk = $false }
    if ($md -and -not $tex) { $texOk = $false }
    $pdfOk = $texOk -and $tex -and ($pdf.LastWriteTime -gt $tex.LastWriteTime) -and
            (-not $md -or $pdf.LastWriteTime -gt $md.LastWriteTime)
    if (-not $pdfOk) {
        Write-Warning "PDF 或 paper.tex 已过期，重新编译（跳过旧 PDF）"
    } else {
        Write-Host "[完成] 已有 PDF: $($pdf.FullName)"
        if ($pdf.FullName -ne (Join-Path $OutDir $pdf.Name)) { Copy-Item -LiteralPath $pdf.FullName -Destination $OutDir -Force }
        exit 0
    }
}

if (-not $md -and -not $tex) {
    Write-Error "4_论文 下没有 paper.md 或 paper.tex，请先按模板写作"
    exit 1
}

# ---- LaTeX 路线 ----
function Get-PythonRunner {
    if ($script:PythonRunner) { return $script:PythonRunner }
    $candidates = @(
        @{ Name = 'python'; Args = @() },
        @{ Name = 'python3'; Args = @() },
        @{ Name = 'py'; Args = @('-3') }
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate.Name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            $checkArgs = @()
            $checkArgs += $candidate.Args
            $checkArgs += '--version'
            & $cmd.Source @checkArgs | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $script:PythonRunner = @{ Exe = $cmd.Source; Args = $candidate.Args }
                return $script:PythonRunner
            }
        } catch {
            continue
        }
    }
    return $null
}

function Invoke-PythonScript {
    param(
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )
    $runner = Get-PythonRunner
    if (-not $runner) {
        Write-Error "找不到可用 Python。请安装 Python 3.8+，或启用可用的 python/python3/py -3 命令。"
        exit 1
    }
    $invokeArgs = @()
    $invokeArgs += $runner.Args
    $invokeArgs += $ScriptPath
    $invokeArgs += $Arguments
    & $runner.Exe @invokeArgs
}

function Find-Xelatex {
    $cmd = Get-Command xelatex -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64\xelatex.exe"),
        "C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64\miktex-xelatex.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return $null
}

if ($tex) {
    # md / md2tex.py 比 tex 新时（或 -Force）先用 md2tex.py 重新生成 tex，避免编译旧内容
    $md2tex = Join-Path $PSScriptRoot 'md2tex.py'
    $texStale = $false
    if ($md) {
        if ($md.LastWriteTime -gt $tex.LastWriteTime) { $texStale = $true }
        if ((Test-Path -LiteralPath $md2tex) -and (Get-Item -LiteralPath $md2tex).LastWriteTime -gt $tex.LastWriteTime) { $texStale = $true }
    }
    if ($Force -or $texStale) {
        if ($md) {
            if ($texStale) { Write-Warning "源文件/转换脚本比 paper.tex 新，重新执行 md2tex.py" }
            Invoke-PythonScript $md2tex @($md.FullName, $tex.FullName)
            if ($LASTEXITCODE -ne 0) { Write-Error "md2tex.py 转换失败"; exit 1 }
        }
    }
    $xelatex = Find-Xelatex
    if ($xelatex) {
        Push-Location $PaperDir
        & $xelatex -interaction=nonstopmode $tex.Name | Out-Null
        & $xelatex -interaction=nonstopmode $tex.Name | Out-Null
        Pop-Location
        $outPdf = [System.IO.Path]::ChangeExtension($tex.FullName, 'pdf')
        if (Test-Path -LiteralPath $outPdf) {
            $dest = Join-Path $OutDir ([System.IO.Path]::GetFileName($outPdf))
            if ([System.IO.Path]::GetFullPath($dest) -ne [System.IO.Path]::GetFullPath($outPdf)) {
                Copy-Item -LiteralPath $outPdf -Destination $dest -Force
            }
            Write-Host "[完成] LaTeX 编译成功: $outPdf"
            exit 0
        }
        Write-Error "xelatex 编译失败，请查看 4_论文 下的 .log"
        exit 1
    }
    Write-Warning "未安装 xelatex，跳过 LaTeX 路线；尝试 Markdown -> Word 路线"
}

# ---- Markdown -> LaTeX -> PDF 路线（公式排版最佳，xelatex + ctex） ----
if ($md -and -not $tex) {
    $xelatex = Find-Xelatex
    if ($xelatex) {
        $md2tex = Join-Path $PSScriptRoot 'md2tex.py'
        if (Test-Path -LiteralPath $md2tex) {
            $texOut = [System.IO.Path]::ChangeExtension($md.FullName, 'tex')
            Invoke-PythonScript $md2tex @($md.FullName, $texOut)
            if ($LASTEXITCODE -eq 0) {
                Push-Location $PaperDir
                & $xelatex -interaction=nonstopmode ([System.IO.Path]::GetFileName($texOut)) | Out-Null
                & $xelatex -interaction=nonstopmode ([System.IO.Path]::GetFileName($texOut)) | Out-Null
                Pop-Location
                $outPdf = [System.IO.Path]::ChangeExtension($texOut, 'pdf')
                if (Test-Path -LiteralPath $outPdf) {
                    $dest = Join-Path $OutDir ([System.IO.Path]::GetFileName($outPdf))
                    if ([System.IO.Path]::GetFullPath($dest) -ne [System.IO.Path]::GetFullPath($outPdf)) {
                        Copy-Item -LiteralPath $outPdf -Destination $dest -Force
                    }
                    Write-Host "[完成] md2tex + xelatex 编译成功: $outPdf"
                    exit 0
                }
                Write-Error "xelatex 编译失败，请查看 4_论文 下的 .log"
                exit 1
            }
            Write-Warning "md2tex.py 转换失败，回退 Word 路线"
        }
    }
}

# ---- Word 路线 ----
if ($md) {
    $docx = [System.IO.Path]::ChangeExtension($md.FullName, 'docx')
    $pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($pandoc) {
        & pandoc $md.FullName -o $docx
        Write-Host "[完成] pandoc: $($md.Name) -> $($docx.Name)"
    } else {
        Invoke-PythonScript "$PSScriptRoot\md2docx.py" @($md.FullName, '-o', $docx)
        if ($LASTEXITCODE -ne 0) {
            Write-Error "md2docx 转换失败（需要 pip install python-docx，或用 pandoc）"
            exit 1
        }
    }

    # Word COM -> PDF
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $doc = $word.Documents.Open($docx)
        $outPdf = [System.IO.Path]::ChangeExtension($docx, 'pdf')
        $doc.SaveAs2($outPdf, 17)   # wdFormatPDF = 17
        $doc.Close($false)
        $word.Quit()
        if (Test-Path -LiteralPath $outPdf) {
            $dest = Join-Path $OutDir ([System.IO.Path]::GetFileName($outPdf))
            if ([System.IO.Path]::GetFullPath($dest) -ne [System.IO.Path]::GetFullPath($outPdf)) {
                Copy-Item -LiteralPath $outPdf -Destination $dest -Force
            }
            Write-Host "[完成] 论文 PDF: $outPdf"
            exit 0
        }
        Write-Error "Word 转 PDF 失败"
        exit 1
    } catch {
        Write-Error "Word COM 不可用（需安装 Microsoft Office）: $_"
        exit 1
    }
}

Write-Error "无法导出 PDF：未安装 xelatex，且没有可用于 Word 路线的 paper.md"
exit 1
