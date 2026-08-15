# Tier 1 迷你端到端（全自动回归测试）
# 用法: .\run-tier1.ps1 [-OutDir <目录>] [-Efficiency 8] [-Trigger 5]
# 流程: scaffold -> 黄金代码+数据 -> 运行 -> 契约 -> 黄金论文 -> verify/checks -> 导出 PDF -> auto-score
# 每次优化后重跑本脚本，auto-score 得分与基线对比（见 EVALUATION.md 验收规则）
param(
    [string]$OutDir = '',
    [double]$Efficiency = 8,
    [double]$Trigger = 5
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path $ScriptDir -Parent
$Scaffold = Join-Path $RepoRoot 'cumcm\scripts\scaffold.ps1'
$Checks = Join-Path $RepoRoot 'cumcm\scripts\checks.py'
$Verify = Join-Path $RepoRoot 'cumcm\scripts\verify.py'
$Contract = Join-Path $RepoRoot 'cumcm\scripts\make-data-contract.py'
$Export = Join-Path $RepoRoot 'cumcm\scripts\export-paper.ps1'
$AutoScore = Join-Path $ScriptDir 'auto-score.py'
$Fixture = Join-Path $ScriptDir 'fixtures\sample-vegetables.csv'
$env:PYTHONIOENCODING = 'utf-8'

if (-not $OutDir) { $OutDir = Join-Path $ScriptDir ("runs\tier1_{0:yyyyMMdd-HHmmss}" -f (Get-Date)) }
if (Test-Path -LiteralPath $OutDir) { Remove-Item -LiteralPath $OutDir -Recurse -Force }
Write-Host "== Tier 1: $OutDir =="

& $Scaffold -Dest $OutDir | Out-Null
Copy-Item -LiteralPath $Fixture -Destination (Join-Path $OutDir '1_数据') -Force

# ---- 黄金代码 ----
$solve = @'
# -*- coding: utf-8 -*-
# 问题一：蔬菜各品类销量描述统计与均值预测
# 数据来源: 1_数据/sample-vegetables.csv
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv("1_数据/sample-vegetables.csv")
g = df.groupby("品类")["销量"].mean().round(3)
g.to_csv(os.path.join(HERE, "results_q1.csv"), encoding="utf-8")
print("各品类平均销量:", dict(g))
print("整体平均单价:", round(df["单价"].mean(), 3))
'@
$plot = @'
# -*- coding: utf-8 -*-
# 图1：各品类平均销量柱状图
# 数据来源: 1_数据/data_contract.json
# 对象数: 3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("1_数据/sample-vegetables.csv")
g = df.groupby("品类")["销量"].mean().round(3)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.bar(list(g.index), g.values, color=["#4C72B0", "#DD8452", "#55A868"])
plt.xlabel("品类")
plt.ylabel("平均销量 (kg)")
plt.title("各品类平均销量")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("3_图表/fig1_品类销量.png", dpi=300)
print("图1 已生成")
'@
Set-Content -LiteralPath (Join-Path $OutDir '2_代码\01_问题1\solve.py') -Value $solve -Encoding UTF8
Set-Content -LiteralPath (Join-Path $OutDir '2_代码\01_问题1\plot_q1.py') -Value $plot -Encoding UTF8

# ---- 运行代码 ----
Push-Location $OutDir
python "2_代码\01_问题1\solve.py" | Out-Null
python "2_代码\01_问题1\plot_q1.py" | Out-Null
Pop-Location
python $Contract (Join-Path $OutDir '1_数据') -o (Join-Path $OutDir '1_数据\data_contract.json') | Out-Null

# ---- 黄金论文 ----
$paper = @'
# 摘要

针对蔬菜类商品自动定价与补货决策问题，本文以某蔬菜集散中心连续 4 天的三类蔬菜（花叶类、水生根茎类、茄类）销售流水数据为研究对象，构建品类平均销量描述统计与均值预测模型。首先对附件数据清洗与侧写，识别缺失与异常值并采用均值填充；其次按品类分组计算平均销量与平均单价，绘制柱状图直观对比各品类销售强度；再次对模型进行误差分析，并以参数扰动 10% 进行灵敏度检验验证结果稳健性。求解结果表明：花叶类平均销量 50.375kg，水生根茎类平均销量 34.475kg，茄类平均销量 30.05kg，整体平均单价 8.008 元/kg，品类间销量差异显著。综上，本文方法流程清晰、结果可复现，可直接推广至更多品类与更长销售周期，为后续定价与补货决策提供数据支撑。

**关键词**：蔬菜定价；描述统计；均值预测；灵敏度分析

## 一、问题重述

蔬菜类商品的自动定价与补货是商超运营的关键问题，需要基于历史销售数据掌握各品类的销量水平。本文基于附件提供的三类蔬菜四天销售流水，统计各品类平均销量与平均单价，为后续定价与补货提供量化依据。

## 二、问题分析

各品类销量差异明显，如图 1 所示，适合采用分组描述统计刻画品类销售水平，并对结果进行稳健性检验。

## 三、模型假设

1. 附件数据真实可靠，无系统性记录误差；
2. 销量在采样期内无明显趋势与季节成分；
3. 各品类间销量相互独立。

## 四、符号说明

| 符号 | 含义 |
|---|---|
| $Q_i$ | 第 $i$ 个品类的平均销量 |
| $P$ | 整体平均单价 |

## 五、模型建立与求解

### 5.1 描述统计模型

设品类 $i$ 的销量样本为 $y_{i1}, y_{i2}, \dots, y_{in}$，则平均销量为

式(1)：
$$ Q_i = \frac{1}{n}\sum_{j=1}^{n} y_{ij} $$

按品类分组计算平均销量与平均单价，结果见表 1。

表 1 各品类平均销量

| 品类 | 平均销量 (kg) |
|---|---|
| 花叶类 | 50.375 |
| 水生根茎类 | 34.475 |
| 茄类 | 30.05 |

### 5.2 模型检验与灵敏度

对均值估计做误差分析，并对输入数据施加 10% 扰动重算，结果变化小于 5%，模型稳健。核心代码见 `solve.py` 与 `plot_q1.py`。

## 六、模型的评价、改进与推广

模型结构简洁、可复现性强；推广到更多品类时可将均值模型升级为时间序列模型（指数平滑/ARIMA）。

## 参考文献

[1] 司守奎, 孙玺菁. 数学建模算法与应用（第二版）[M]. 北京: 国防工业出版社, 2015.
[2] 姜启源, 谢金星, 叶俊. 数学模型（第四版）[M]. 北京: 高等教育出版社, 2011.
[3] 薛毅. 数学建模基础[M]. 北京: 北京工业大学出版社, 2004.
[4] 王积建. MATLAB 与数学建模[M]. 北京: 机械工业出版社, 2013.
[5] 赵静, 但琦. 数学建模与数学实验（第三版）[M]. 北京: 高等教育出版社, 2008.

## 附录

核心代码：`solve.py`、`plot_q1.py`。
'@
Set-Content -LiteralPath (Join-Path $OutDir '4_论文\paper.md') -Value $paper -Encoding UTF8

# ---- 校验与导出 ----
Write-Host "---- verify.py ----"
python $Verify $OutDir
Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
& $Export -WorkDir $OutDir | Out-Null
Write-Host "---- checks.py ----"
python $Checks (Join-Path $OutDir '4_论文\paper.md') $OutDir
Write-Host "---- auto-score ----"
python $AutoScore $OutDir --efficiency $Efficiency --trigger $Trigger
Write-Host "[完成] Tier 1 完成。把上表 grand_total 记入 evaluation/RESULTS.md 对比基线。"