# 竞赛路由框架

## 概述

v1.8.0 引入竞赛路由，支持三种竞赛模式：CUMCM（国赛）、MCM/ICM（美赛）、电工杯。
同一套工作流框架，通过参数切换模板/规则/语言/时间预算。

## 路由参数

| 参数 | CUMCM | MCM/ICM | 电工杯 |
|---|---|---|---|
| `competition` | "cumcm" | "mcm" | "diangong" |
| `duration_h` | 72 | 96 | 72 |
| `language` | "zh" | "en" | "zh" |
| `paper_format` | "pdf_or_word" | "pdf_only" | "pdf_or_word" |
| `body_page_limit` | 30 | 25 | 25 |
| `abstract_location` | page 1 | Summary Sheet (page 1) | page 2 |
| `reference_format` | GB/T 7714 | APA/numbered | GB/T 7714 |
| `anonymity_scope` | no school/id in body | no school/teacher in body | no school/teacher in body |
| `ai_disclosure` | inline + reference + PDF | "Report on Use of AI" section | recommended (no formal format) |
| `team_size` | 3 students | 3 students | 3 students |
| `plagiarism_threshold` | none stated | none stated | 40% disqualification |

## 时间预算分配

### CUMCM 72h

| 阶段 | 小时 |
|---|---|
| Phase 0 读题选题 | 5h |
| Phase 1 数据探索 | 6h |
| Phase 2 建模求解 | 30h |
| Phase 3 论文写作 | 20h |
| Phase 4 检查提交 | 9h |
| 缓冲 | 2h |

### MCM 96h

| 阶段 | 小时 |
|---|---|
| Phase 0 读题选题 | 6h |
| Phase 1 数据探索 | 6h |
| Phase 2 建模求解 | 38h |
| Phase 3 论文写作 | 29h |
| Phase 4 检查提交 | 12h |
| 缓冲 | 5h |

### 电工杯 72h

| 阶段 | 小时 |
|---|---|
| Phase 0 读题选题 | 5h |
| Phase 1 数据探索 | 6h |
| Phase 2 建模求解 | 30h |
| Phase 3 论文写作 | 20h |
| Phase 4 检查提交 | 9h |
| 缓冲 | 2h |

## 论文结构差异

### CUMCM 七章结构（默认）

1. 问题重述
2. 问题分析（配总体思路图）
3. 模型假设
4. 符号说明
5. 模型建立与求解
6. 模型评价、改进与推广
7. 参考文献
8. 附录

### MCM 十节结构

1. Summary Sheet（第一页，最重要）
2. Introduction
3. Assumptions and Justifications
4. Notation
5. Model Development
6. Sensitivity Analysis
7. Strengths and Weaknesses
8. Conclusions
9. References
10. Appendices

### 电工杯结构

1. 封面（报名号+题目）
2. 摘要（≤ 1 页）
3. 问题重述与分析
4. 模型假设与符号说明
5. 模型建立与求解
6. 模型检验与灵敏度分析
7. 模型评价与推广
8. 参考文献
9. 附录

## 语言差异

| 项目 | CUMCM/电工杯 | MCM |
|---|---|---|
| 论文语言 | 中文 | 英文 |
| 摘要语言 | 中文 | 英文 |
| 代码注释 | 中文 | 英文 |
| 图表标签 | 中文 | 英文 |
| 学术英语 | 不适用 | 被动语态优先，禁口语 |

### 英文写作规则（MCM 专用）

- "we think" → "the model suggests"
- "we ran the code" → "the algorithm was executed"
- "good results" → "an R² of 0.94"
- 方法节优先用被动语态
- 每节三遍检查：草稿 → 学术语态检查 → 润色

## 路由初始化流程

首次启动时，根据 `competition` 参数：

1. 读取 `competitions/<comp>/current_rules.md` 获取规则
2. 设置 `budget.total_hours`、`language`、`body_page_limit` 等
3. 选择论文模板：
   - CUMCM → `assets/paper-template.md` 或 `assets/paper-template.tex`
   - MCM → `assets/mcm-template.tex`（mcmthesis）
   - 电工杯 → `assets/paper-template.md`（调整结构）
4. 设置 `decision_log.json` 的 `competition` 和 `budget` 字段
5. 按对应规则执行工作流

## 文件结构

```
cumcm/
├── competitions/
│   ├── cumcm/current_rules.md      # 国赛规则
│   ├── mcm/current_rules.md        # 美赛规则
│   └── diangong/current_rules.md   # 电工杯规则
├── references/
│   └── 16-competition-routing.md   # 本文件
```
