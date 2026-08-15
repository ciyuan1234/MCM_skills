# 论文导出脚本（Windows / PowerShell）—— Markdown/LaTeX -> PDF
# 用法:
#   .\export-paper.ps1 [-WorkDir 工作目录] [-OutDir 输出目录]
# 流程:
#   LaTeX 路线: paper.tex -> xelatex -> paper.pdf
#   Word 路线:  paper.md  -> (pandoc 或 md2docx.py) -> paper.docx -> Word COM -> paper.pdf
param(
    [string]$WorkDir = '.',
    [string]$OutDir = ''
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
if ($pdf) {
    Write-Host "[完成] 已有 PDF: $($pdf.FullName)"
    if ($pdf.FullName -ne (Join-Path $OutDir $pdf.Name)) { Copy-Item -LiteralPath $pdf.FullName -Destination $OutDir -Force }
    exit 0
}

if (-not $md -and -not $tex) {
    Write-Error "4_论文 下没有 paper.md 或 paper.tex，请先按模板写作"
    exit 1
}

# ---- LaTeX 路线 ----
if ($tex) {
    $xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
    if ($xelatex) {
        Push-Location $PaperDir
        & xelatex -interaction=nonstopmode $tex.Name | Out-Null
        & xelatex -interaction=nonstopmode $tex.Name | Out-Null
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

# ---- Word 路线 ----
if ($md) {
    $docx = [System.IO.Path]::ChangeExtension($md.FullName, 'docx')
    $pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($pandoc) {
        & pandoc $md.FullName -o $docx
        Write-Host "[完成] pandoc: $($md.Name) -> $($docx.Name)"
    } else {
        python "$PSScriptRoot\md2docx.py" $md.FullName -o $docx
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