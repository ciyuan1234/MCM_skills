# CUMCM Skill Pack: AI 数学建模国赛全流程助手

[![CUMCM](https://img.shields.io/badge/CUMCM-数学建模-blue)](#)
[![AI Skill](https://img.shields.io/badge/AI-Skill-green)](#)
[![Codex](https://img.shields.io/badge/OpenAI-Codex-black)](#)
[![Claude Code](https://img.shields.io/badge/Claude-Code-orange)](#)
[![opencode](https://img.shields.io/badge/opencode-supported-purple)](#)
[![Platform](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-supported-lightgrey)](#)

一套面向 **全国大学生数学建模竞赛（CUMCM）** 的 AI 参赛 skill 包，覆盖从读题、数据探索、建模求解、论文写作、格式检查到支撑材料打包的完整 72 小时工作流。

它不是简单提示词合集，而是一个带 **论文模板、脚本工具、评测体系、反幻觉溯源约束、反思银行、黄金测试集** 的可安装技能包。

[![workflow](cumcm/assets/workflow-overview.svg)](examples/2023C-workflow-demo.md)

[English README](README_EN.md) · [2023C Demo](examples/2023C-workflow-demo.md) · [质量评估框架](EVALUATION.md)

## 为什么值得 Star

- **开赛能直接用**：一键创建比赛工作区，预置 `0_赛题`、`1_数据`、`2_代码`、`3_图表`、`4_论文`、`5_支撑材料` + `decision_log.json` + 5 个 stage 目录。
- **覆盖国赛真实流程**：读题选题、数据契约、模型选择、代码求解、论文七章结构、交卷检查全部串起来。
- **反 AI 幻觉**：论文数值必须能从数据文件和运行结果溯源，图表必须由代码生成，文献不得编造。
- **有工程化验收**：`checks.py`、`verify.py`、`format-check.py`、`auto-score.py`、`run_golden.py` 用来判断一次优化是变好还是变坏。
- **适配主流 Agent**：支持 Claude Code、OpenAI Codex、opencode 的 skill 目录结构。
- **时间感知 + 自动降级**：72h 计时器，<6h 自动锁定模式，确保按时交卷。
- **跨阶段一致性**：L2 回溯检查 + Fresh-eyes 审查，消除假设漂移和作者盲区。
- **多竞赛支持**：同一框架支持 CUMCM 国赛、MCM/ICM 美赛、电工杯，切换参数即可。
- **配对验证**：每个模型配套独立验证脚本，按模型类型自动选择验证项。
- **并行子问题**：独立子问题可并行 build+verify，缩短建模时间。
- **写作质量升级**：摘要 90 秒规则、敏感度五步法、假设闭环协议，基于 59 篇一等奖论文分析。
- **反思银行**：30+ 常见错误+修复方案知识库，防止重蹈覆辙。
- **工具接地验证**：SymPy 验证方程数学正确性，LLM 提出 → CAS 验证 → 修复循环。
- **三层记忆架构**：核心/回忆/归档三层，解决长会话丢上下文问题。

## 30 秒看懂

你对 AI 说：

```text
我拿到 2026 国赛 C 题了。请按 cumcm skill 建立工作区，读题，判断题型，给出每问建模路线。
```

AI 应该输出：

```text
题目四层结构：背景 / 问题1-N / 数据说明 / 结果要求
题型判断：C 题，数据分析 + 预测 + 优化
技术路线：数据侧写 -> 相关性分析 -> 预测模型 -> 优化模型 -> 灵敏度分析
工作区：已创建 0_赛题、1_数据、2_代码、3_图表、4_论文、5_支撑材料
下一步：读取附件并生成 1_数据/data_contract.json
```

完整输出风格见：[examples/2023C-workflow-demo.md](examples/2023C-workflow-demo.md)。

## 快速开始

克隆项目：

```powershell
git clone https://github.com/ciyuan1234/MCM_skills.git
cd MCM_skills
```

Windows 安装：

```powershell
.\install.ps1
```

macOS / Linux 安装：

```bash
chmod +x install.sh
./install.sh
```

安装后重启你的 Agent 工具，然后用自然语言触发：

```text
建立数学建模比赛工作目录，并按 CUMCM 六阶段流程开始。
```

脚本会把 `cumcm/` 复制到这些位置：

| 工具 | 安装目录 |
|---|---|
| Claude Code | `~/.claude/skills/cumcm` |
| OpenAI Codex | `~/.codex/skills/cumcm` |
| AGENTS 标准 | `~/.agents/skills/cumcm` |
| opencode | `~/.config/opencode/skills/cumcm` |

## 核心能力

| 阶段 | 能力 | 产物 |
|---|---|---|
| Phase 0 | 读题、拆解任务、判断 A-E 题型 | 题目结构、技术路线、选题建议 |
| Phase 1 | 数据侧写、缺失/异常/重复检查 | 数据质量报告、`data_contract.json` |
| Phase 2 | 模型选择、代码求解、结果检验 | 可运行代码、结果表、图表 |
| Phase 3 | 摘要最后写、正文、图表、参考文献 | `paper.md` / `paper.tex` / `paper.docx` |
| Phase 4 | 格式检查、溯源检查、Fresh-eyes 审查、导出 PDF | 检查报告、论文 PDF |
| Phase 5 | 支撑材料整理与打包 | 提交 zip |

**架构能力：**
- 结构化决策日志（`decision_log.json`）：程序化状态恢复
- 时间感知 + 锁定模式：72h 计时器，<6h 自动切换
- 阶段交接协议（`hand_off.md`）：三段式结构化交接
- L2 跨阶段回溯检查：3 个检查点，检测假设漂移
- Fresh-eyes 审查：清空上下文以评委视角重读论文
- AP/Manual 双模式 + 信心分级介入（HITL）
- 三层记忆架构：核心/回忆/归档，跨会话不丢上下文

**写作升级：**
- 摘要 90 秒规则：评委前 90 秒决定印象的四步法
- 敏感度五步法：龙卷风图 → 边界行为 → 响应曲面 → 结论翻转 → 交互检测
- 假设闭环协议：编号 A1/A2 + 正文引用 + 敏感度检验
- 反思银行：30+ 常见错误 + 修复方案

**验证体系：**
- SymPy 工具接地验证：LLM 提出方程 → CAS 验证 → 修复循环
- 配对验证：6 类模型验证项（V-OPT/V-REG/V-ODE/V-GRF/V-TS/V-STAT）
- 黄金测试集：3 年（2021C/2022C/2023C）结构化检查点，自动回归

## 目录结构

```text
MCM_skills/
├── install.ps1 / install.sh       # 一键安装
├── README.md / README_EN.md       # 中英文入口
├── CHANGELOG.md                   # 版本记录
├── EVALUATION.md                  # 质量评估框架
├── examples/                      # Demo 输出样例
├── evaluation/                    # benchmark、评分表、黄金测试集
│   ├── golden_problems/           # 结构化测试数据（2021C/2022C/2023C）
│   ├── runs/                      # Tier1/Tier2 运行结果
│   ├── auto-score.py              # 自动评分（90分制）
│   ├── run-tier1.ps1              # Tier1 回归
│   ├── run-tier2.ps1              # Tier2 盲测
│   └── run-benchmark.ps1          # 反幻觉基准（9 工作区含 3 陷阱）
└── cumcm/
    ├── SKILL.md                   # skill 编排层（v2.0.0: 记忆/验证/HITL/布局说明）
    ├── competitions/              # 竞赛规则（CUMCM/MCM/电工杯）
    ├── references/                # 参考文档（21 个）
    │   ├── 01-10 基础参考          # 格式/评分/模型/代码/写作/检查/资源/FAQ/时间/约束
    │   ├── 11-18 扩展能力          # 决策日志/时间预算/交接/L2/Fresh-eyes/路由/验证/并行
    │   └── 19-21 研究驱动          # 反思银行/记忆架构/工具接地验证
    ├── scripts/                   # 工具脚本（9 个）
    └── assets/                    # 模板（论文/绘图/decision_log/hand_off）
```

## 常用命令

创建比赛工作区：

```powershell
.\cumcm\scripts\scaffold.ps1 -WorkDir .\workspace
```

生成数据契约：

```powershell
python .\cumcm\scripts\make-data-contract.py .\workspace\1_数据 -o .\workspace\1_数据\data_contract.json
```

检查论文：

```powershell
python .\cumcm\scripts\checks.py .\workspace\4_论文\paper.md .\workspace
python .\cumcm\scripts\verify.py .\workspace
python .\cumcm\scripts\format-check.py .\workspace
```

黄金测试集回归：

```powershell
python .\cumcm\scripts\run_golden.py .\workspace --problem 2023_C -v
```

导出论文并打包支撑材料：

```powershell
.\cumcm\scripts\export-paper.ps1 -WorkDir .\workspace -Force
.\cumcm\scripts\package.ps1 -WorkDir .\workspace
```

## 推荐依赖

- Python 3.8+
- `numpy`、`scipy`、`pandas`、`matplotlib`、`sympy`、`scikit-learn`
- 可选：MiKTeX / TeX Live，用于 `xelatex` 导出高质量 PDF
- 可选：Microsoft Office，用于 Word COM 转 PDF

Windows 安装 MiKTeX：

```powershell
winget install MiKTeX.MiKTeX
& "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\initexmf.exe" --set-config-value "[MPM]AutoInstall=1"
```

## 防幻觉红线

本项目把"不要编造"落成了可检查规则：

- 数据必须来自真实文件，Phase 1 必须生成 `1_数据/data_contract.json`。
- 代码必须显式读取数据文件，禁止把关键数据硬编码进脚本。
- 论文数值必须能在运行结果或数据契约中找到出处。
- 图表必须由代码从数据生成，图例和对象数必须与数据一致。
- 参考文献只列真实读过的资料。
- 每个模型必须用五步法做敏感度分析（龙卷风图 + 边界行为 + 结论翻转）。
- 假设必须编号（A1/A2/...），正文引用假设编号，敏感度检验假设影响。

## 质量评估

项目内置四层回归：

| 层级 | 目标 | 工具 |
|---|---|---|
| Tier 0 | 工具自检 | scaffold / checks / verify / format-check / package |
| Tier 0.5 | 黄金测试集回归 | `scripts/run_golden.py`（3 年 × 9-10 检查点） |
| Tier 1 | 小型端到端 fixture | `evaluation/run-tier1.ps1` + `auto-score.py` |
| Tier 2 | 往届真题盲测 | `evaluation/run-tier2.ps1` + 盲评量表 |

详细规则见：[EVALUATION.md](EVALUATION.md)。

## 适合谁

- 正在准备 CUMCM / 数学建模国赛的队伍
- 数学建模社团、培训营、课程助教
- 想把 AI Agent 用到严肃建模任务的人
- 想研究"AI + 可验证工作流"的开发者

## 推荐 GitHub Topics

如果你 fork 或二次开发，建议添加这些 topics，方便更多人搜到：

`cumcm` `mathematical-modeling` `ai-agent` `codex` `claude-code` `opencode` `skills` `latex` `python`

## Roadmap

- [x] 增加工作流视觉入口：README 首屏已嵌入 workflow overview
- [x] 黄金测试集自动回归：`run_golden.py` 覆盖 2021C/2022C/2023C
- [x] 结构化版本记录：`CHANGELOG.md`
- [ ] 增加 GitHub Actions：脚本语法检查和 Tier 1 冒烟测试
- [ ] 增加 `LICENSE` 和贡献指南
- [ ] 补充更多往届题的端到端公开 demo
- [ ] 将中文资料库索引拆成可选扩展包

## 分享文案

项目简介与发布文案见：[PROMOTION.md](PROMOTION.md)。

## Changelog

详见 [CHANGELOG.md](CHANGELOG.md)。主要版本：

- **v2.0.1**（2026-08-17）：`run_golden.py` 黄金测试集自动回归脚本，支持 3 年题目自动检查，全部通过。
- **v2.0.0**（2026-08-17）：结构性缺口修复。Golden problems 从 1 年扩展至 3 年（2021C+2022C+2023C）；CHANGELOG.md 统一版本记录；SKILL.md evaluation 目录布局说明。
- **v1.9.0**（2026-08-17）：研究驱动升级。摘要写作升级（90秒规则+few-shot模板+最后写原则）；敏感度五步法；假设闭环协议；反思银行（30+错误库）；黄金测试集；信心分级介入；三层记忆架构；工具接地验证（SymPy）。
- **v1.8.0**（2026-08-17）：竞赛路由（CUMCM/MCM/电工杯）；配对验证；并行子问题。
- **v1.7.0**（2026-08-17）：架构升级。决策日志/时间感知/交接/L2/Fresh-eyes/AP+Manual双模式。
- **v1.6.0**（2026-08-17）：图表质量提升；表格检查智能化；附录扩充。
- **v1.5.x**（2026-08-16）：获奖论文经验库；时序预测基线；LaTeX 稳健性。
- **v1.4.0**（2026-08-16）：LaTeX 编译路线；正文页数硬标准；篇幅密度检查。
- **v1.3.0**（2026-08-15）：格式硬检查体系；负样本验证。
- **v1.0.0**（2026-08-15）：首个完整版本。
