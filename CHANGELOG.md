# Changelog

本文件记录 CUMCM Skill Pack 的版本变更。格式基于 [Keep a Changelog](https://keepachangelog.com/)。

## [Unreleased]

### TODO
- 重新运行反幻觉基准测试（run-benchmark.ps1，9 工作区含 3 陷阱）
- 创建 `scripts/run_golden.py` 黄金测试集自动回归脚本

## [v2.0.0] - 2026-08-17

### Added
- Golden problems 扩展：新增 2021_C（供应商优化）和 2022_C（文物成分分析）结构化测试数据
- `CHANGELOG.md`：统一版本记录文件

### Changed
- SKILL.md 新增 evaluation 目录布局说明
- Golden problems 覆盖率从 1/3 题提升至 3/3 题（2021C/2022C/2023C）

## [v1.9.0] - 2026-08-17

### Added
- **摘要写作升级**（§1.5-1.7）：90秒规则、few-shot获奖模板、最后写原则、五要素检查清单
- **敏感度分析五步法**（§5）：龙卷风图+边界行为+响应曲面+结论翻转+交互检测，替代±10%仪式
- **假设闭环协议**（§6）：编号规则+闭环流程+质量检查清单+撰写模板
- **反思银行** `references/19-reflection-bank.md`：5类30+常见错误+修复方案
- **黄金测试集** `evaluation/golden_problems/2023_C/`：9项检查点+期望结果+获奖摘要参考
- **信心分级介入** SKILL.md：三级自主度（高>0.95/中0.85-0.95/低<0.85）+触发条件
- **三层记忆架构** `references/20-memory-architecture.md`：核心记忆+回忆记忆+归档记忆
- **工具接地验证** `references/21-tool-grounded-verification.md`：SymPy验证方程数学正确性

### Changed
- SKILL.md 223→280行；Phase 2新增SymPy验证+反思银行+五步法；Phase 3改为"摘要最后写"
- 红线新增第10条：假设闭环
- 启动协议新增记忆层读取
- references索引 18→21

## [v1.8.0] - 2026-08-17

### Added
- 竞赛路由 `references/16-competition-routing.md` + `competitions/` 目录（CUMCM/MCM/电工杯三模式）
- 配对验证 `references/17-paired-verification.md` + `scripts/verify_template.py`
- 并行子问题 `references/18-parallel-subagents.md`

## [v1.7.0] - 2026-08-17

### Added
- 结构化决策日志 `decision_log.json`（schema v1.0）
- 时间预算与锁定模式 `references/12-time-budget.md`
- 阶段交接协议 `references/13-handoff-protocol.md` + `assets/hand_off_template.md`
- L2跨阶段回溯检查 `references/14-backcheck-l2.md`（3个检查点）
- Fresh-eyes审查 `references/15-fresh-eyes-review.md`
- AP/Manual双模式

### Changed
- verify.py 新增 check 7（decision_log集成）
- checks.py 新增 check_l2_backcheck()
- scaffold 初始化 decision_log.json + stage 目录

## [v1.6.0] - 2026-08-17

### Added
- `plot_appendix.py`：4张附录图（品类箱线图/弹性散点图/预测对比/SA收敛）

### Changed
- 图表统一配色/字号/DPI
- verify.py 表格检查按列分组消除误报（13→3警告）
- 正文精简至26页，附录扩充至10页

## [v1.5.2] - 2026-08-16

### Changed
- md2tex.py 表格渲染升级（≥4列自动tabularx）
- export-paper.ps1 支持 -Force 与源文件更新检测
- Overfull hbox 12→1（3.15pt不可见级）

## [v1.5.1] - 2026-08-16

### Added
- Q2 显式时序预测基线（乘法季节分解 + SARIMA）

## [v1.5.0] - 2026-08-16

### Added
- 获奖论文经验库（59篇一等奖分析）
- 差异化创新自检（≥2处差异化维度）
- 经验分享库 `exp-review-perspective.md`

## [v1.4.0] - 2026-08-16

### Added
- LaTeX 编译路线（md2tex.py + xelatex + MiKTeX）
- 正文页数硬标准 ≥20
- 篇幅密度检查（公式≥10、图+表≥8）
- 创新点定位强制

## [v1.3.0] - 2026-08-15

### Added
- 格式硬检查体系（format-check.py）
- 负样本验证（5类硬伤全被抓）
- BOM兼容修复

## [v1.2.0] - 2026-08-15

### Added
- Tier1/Tier2回归测试框架
- auto-score.py 自动评分
- 数据契约多sheet支持

## [v1.1.0] - 2026-08-15

### Added
- 反幻觉双向验证
- 陷阱工作区测试

## [v1.0.0] - 2026-08-15

### Added
- 首个完整版本
- 5阶段工作流
- scaffold/checks/verify/export/package 脚本
