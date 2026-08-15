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
# 问题一：蔬菜各品类销量描述统计、均值预测与灵敏度检验
# 数据来源: 1_数据/sample-vegetables.csv
# 对象数: 3
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv("1_数据/sample-vegetables.csv")

g = df.groupby("品类")["销量"].mean().round(3)
g.to_csv(os.path.join(HERE, "results_q1.csv"), encoding="utf-8")

stats = df.groupby("品类")["销量"].agg(count="count", mean="mean", std="std").round(3)
stats["变异系数"] = (stats["std"] / stats["mean"] * 100).round(2)
stats.to_csv(os.path.join(HERE, "results_q1_stats.csv"), encoding="utf-8")

price = df.groupby("品类")["单价"].mean().round(3)
price.to_csv(os.path.join(HERE, "results_q1_price.csv"), encoding="utf-8")

rows = []
for pct in (-0.10, 0.10):
    d2 = df.copy()
    d2["销量"] = d2["销量"] * (1 + pct)
    m = d2.groupby("品类")["销量"].mean().round(3)
    rows.append({"扰动": "{0:+.0f}%".format(pct * 100), "花叶类": m["花叶类"],
                 "水生根茎类": m["水生根茎类"], "茄类": m["茄类"], "变化率": 10.0})
pd.DataFrame(rows).to_csv(os.path.join(HERE, "results_q1_sensitivity.csv"), index=False, encoding="utf-8")

print("各品类平均销量:", dict(g))
print("整体平均单价:", round(df["单价"].mean(), 3))
'@
$plot = @'
# -*- coding: utf-8 -*-
# 图1：各品类平均销量柱状图；图2：各品类平均单价对比图
# 数据来源: 1_数据/data_contract.json
# 对象数: 3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("1_数据/sample-vegetables.csv")
g = df.groupby("品类")["销量"].mean().round(3)
p = df.groupby("品类")["单价"].mean().round(3)

plt.figure(figsize=(6, 4))
plt.bar(list(g.index), g.values, color=["#4C72B0", "#DD8452", "#55A868"])
plt.xlabel("品类")
plt.ylabel("平均销量 (kg)")
plt.title("各品类平均销量")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("3_图表/fig1_品类销量.png", dpi=300)

plt.figure(figsize=(6, 4))
plt.bar(list(p.index), p.values, color=["#55A868", "#4C72B0", "#DD8452"])
plt.xlabel("品类")
plt.ylabel("平均单价 (元/kg)")
plt.title("各品类平均单价")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("3_图表/fig2_品类单价.png", dpi=300)
print("图1/图2 已生成")
'@
Set-Content -LiteralPath (Join-Path $OutDir '2_代码\01_问题1\solve.py') -Value $solve -Encoding UTF8
Set-Content -LiteralPath (Join-Path $OutDir '2_代码\01_问题1\plot_q1.py') -Value $plot -Encoding UTF8

# ---- 运行代码 ----
Push-Location $OutDir
python "2_代码\01_问题1\solve.py" | Out-Null
python "2_代码\01_问题1\plot_q1.py" | Out-Null
Pop-Location
python $Contract (Join-Path $OutDir '1_数据') -o (Join-Path $OutDir '1_数据\data_contract.json') | Out-Null
Set-Content -LiteralPath (Join-Path $OutDir '5_支撑材料\数据说明.txt') -Value "数据来源: 附件 sample-vegetables.csv（连续4天三类蔬菜销售流水）; 全部结果数值由 solve.py 计算并写入 results*.csv, 论文与摘要数值可直接溯源。" -Encoding UTF8

# ---- 黄金论文 ----
$paper = @'
# 摘要

针对蔬菜类商品自动定价与补货决策问题，本文以某蔬菜集散中心连续4天的三类蔬菜（花叶类、水生根茎类、茄类）销售流水数据为研究对象，构建分品类描述统计模型与稳健性检验框架，依次完成数据侧写、品类刻画与模型检验三部分工作。

问题一（数据侧写）：对附件数据进行清洗与核查，共12个有效销售样本，销量最小值27.6kg、最大值55.7kg、整体均值38.3kg，单价区间6.4元/kg至9.6元/kg，样本完整、无缺失，数据质量良好。

问题二（品类刻画）：按品类分组计算平均销量、标准差与平均单价。花叶类平均销量50.375kg、标准差4.437，水生根茎类平均销量34.475kg、标准差3.134，茄类平均销量30.05kg、标准差2.533，三类销量差异显著；平均单价分别为花叶类6.65元/kg、水生根茎类8.15元/kg、茄类9.225元/kg，整体平均单价8.0083元/kg，茄类单价最高、花叶类最低。

问题三（稳健性检验）：对销量数据施加±10%扰动重算品类均值，花叶类变为45.338kg与55.413kg，水生根茎类变为31.028kg与37.922kg，茄类变为27.045kg与33.055kg，三类均值均随扰动同比例平移、线性可复现，模型结论稳健。

综上，本文方法流程清晰、结果可复现，可直接推广至更多品类与更长销售周期，为定价与补货决策提供量化数据支撑。

**关键词**：蔬菜定价；描述统计；标准差；灵敏度分析；数据侧写

## 一、问题重述

蔬菜类商品的自动定价与补货是商超运营的关键问题，需要基于历史销售数据掌握各品类的销量水平与价格水平。本文基于附件提供的三类蔬菜连续四天销售流水，统计各品类平均销量、标准差与平均单价，并进行稳健性检验，为后续定价与补货决策提供量化依据。

## 二、问题分析

各品类销量差异明显（如图1所示），适合采用分组描述统计刻画品类销售水平：先做数据侧写核查样本完整性，再按品类计算销量与单价特征，最后对均值估计做误差分析与灵敏度检验（如图2所示）。

![图1 各品类平均销量](3_图表/fig1_品类销量.png)

## 三、模型假设

1. 附件数据真实可靠，无系统性记录误差；
2. 销量在采样期内无明显趋势与季节成分；
3. 各品类间销量相互独立；
4. 采样期内单价相对稳定，可用均值代表品类价格水平。

## 四、符号说明

| 符号 | 含义 |
|---|---|
| Q_i | 第 i 个品类的平均销量 |
| s_i | 第 i 个品类销量的样本标准差 |
| P_i | 第 i 个品类的平均单价 |
| P | 整体平均单价 |
| delta | 灵敏度检验中的扰动幅度（取 ±10%） |

## 五、模型建立与求解

### 5.1 描述统计模型

设品类 i 的销量样本为 y_ij（j=1..n），则平均销量与标准差分别为

Q_i = (1/n) * sum_{j=1..n} y_ij　　(1)

s_i = sqrt( (1/(n-1)) * sum_{j=1..n} (y_ij - Q_i)^2 )　　(2)

按品类分组计算平均销量与标准差，结果见表1；样本整体统计见表2。

表1 各品类平均销量与标准差

| 品类 | 平均销量 (kg) | 标准差 (kg) | 变异系数 (%) |
|---|---|---|---|
| 花叶类 | 50.375 | 4.437 | 8.81 |
| 水生根茎类 | 34.475 | 3.134 | 9.09 |
| 茄类 | 30.05 | 2.533 | 8.43 |

表2 整体样本统计（销量与单价）

| 指标 | 销量 (kg) | 单价 (元/kg) |
|---|---|---|
| 均值 | 38.3 | 8.0083 |
| 最小值 | 27.6 | 6.4 |
| 最大值 | 55.7 | 9.6 |

各品类平均单价见表3，可见茄类单价9.225元/kg最高、花叶类6.65元/kg最低，品类间存在明显价格分层。

表3 各品类平均单价

| 品类 | 平均单价 (元/kg) |
|---|---|
| 花叶类 | 6.65 |
| 水生根茎类 | 8.15 |
| 茄类 | 9.225 |

![图2 各品类平均单价](3_图表/fig2_品类单价.png)

### 5.2 模型检验与灵敏度分析

对销量数据施加 ±10% 扰动重算品类均值，扰动后均值为

Q_i' = (1/n) * sum_{j=1..n} y_ij * (1 + delta)　　(3)

变化率 R_i = (Q_i' - Q_i) / Q_i * 100%　　(4)

结果见表4：三类均值均随扰动同比例平移，变化率10.0%与扰动幅度一致，模型线性可复现。

表4 灵敏度检验结果（±10% 扰动）

| 扰动 | 花叶类 (kg) | 水生根茎类 (kg) | 茄类 (kg) | 变化率 (%) |
|---|---|---|---|---|
| -10% | 45.338 | 31.028 | 27.045 | 10.0 |
| +10% | 55.413 | 37.922 | 33.055 | 10.0 |

误差分析方面，各品类变异系数介于8.43%~9.09%（表1），反映采样期内品类销量波动处于合理水平，均值估计的抽样误差可控。核心代码见 `solve.py` 与 `plot_q1.py`，全部结果数值由代码写入 results*.csv，可复现可溯源。

## 六、模型的评价、改进与推广

模型结构简洁、可复现性强，数据驱动、无人工调参。不足在于样本仅覆盖4天，均值估计未利用时间结构；推广到更多品类与更长周期时可将均值模型升级为时间序列模型（指数平滑/ARIMA）或加入节假日因子，并结合价格弹性做定价优化。

## 参考文献

[1] 司守奎, 孙玺菁. 数学建模算法与应用（第二版）[M]. 北京: 国防工业出版社, 2015.
[2] 姜启源, 谢金星, 叶俊. 数学模型（第四版）[M]. 北京: 高等教育出版社, 2011.
[3] 薛毅. 数学建模基础[M]. 北京: 北京工业大学出版社, 2004.
[4] 王积建. MATLAB 与数学建模[M]. 北京: 机械工业出版社, 2013.
[5] 赵静, 但琦. 数学建模与数学实验（第三版）[M]. 北京: 高等教育出版社, 2008.
[6] 张维迎. 博弈论与信息经济学[M]. 上海: 上海人民出版社, 1996.

## 附录

核心代码：`solve.py`（统计计算与灵敏度检验）、`plot_q1.py`（图1、图2），输出文件位于 `2_代码/01_问题1/results_q1*.csv`。
'@
Set-Content -LiteralPath (Join-Path $OutDir '4_论文\paper.md') -Value $paper -Encoding UTF8

# ---- 校验与导出 ----
Write-Host "---- verify.py ----"
python $Verify $OutDir
Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Push-Location $OutDir
& $Export -WorkDir $OutDir | Out-Null
Pop-Location
Write-Host "---- checks.py ----"
python $Checks (Join-Path $OutDir '4_论文\paper.md') $OutDir
Write-Host "---- auto-score ----"
python $AutoScore $OutDir --efficiency $Efficiency --trigger $Trigger
Write-Host "[完成] Tier 1 完成。把上表 grand_total 记入 evaluation/RESULTS.md 对比基线。"