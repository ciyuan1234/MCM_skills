# 跨阶段回溯检查（L2 Backcheck）

## 概述

L2 回溯检查是**跨阶段一致性验证机制**。在关键阶段转换点，自动检查前序阶段的决策是否仍然成立，
检测假设漂移、符号不一致、数值矛盾等问题。

借鉴 mathmodel-skill 的 L2 设计，适配 CUMCM 五阶段架构。

## 检查点矩阵

| 触发时机 | 检查来源 | 检查目标 | 核心问题 |
|---|---|---|---|
| **L2-A** Phase 2→3 | Phase 2 建模结果 | Phase 0 选题 + Phase 1 数据 | 模型是否回答了所有子问题？数据处理是否充分？ |
| **L2-B** Phase 3→4 | Phase 3 论文全文 | Phase 0-2 全部 | 论文数值与代码一致？假设/符号全文一致？ |
| **L2-C** Phase 4 终检前 | 全文 | 全局 | 摘要与正文一致？图表编号连续？提交物完整？ |

## L2-A：建模完成 → 开始写作前

**目的**：确认建模结果足以支撑论文写作。

### 检查项

| ID | 检查项 | 来源 | 方法 | 严重度 |
|---|---|---|---|---|
| A-01 | 子问题覆盖 | decision_log.stages.2.sub_problems | 每个子问题都有对应的结果文件 | critical |
| A-02 | 模型选择理由 | decision_log.decisions | 选型理由记录完整，包含被拒方案 | warning |
| A-03 | 数据处理记录 | decision_log.stages.1.results | 缺失值/异常值处理方式已记录 | warning |
| A-04 | 基线模型存在 | stages.2.artifacts | 至少一个基线模型代码+结果 | critical |
| A-05 | 验证通过 | verify.py 输出 | verify.py exit code = 0 | critical |
| A-06 | 时间预算 | budget.remaining_hours | 剩余时间 >= 20h（否则建议降级） | warning |

### 判定规则

- 任何 critical 项 fail → **阻止进入 Phase 3**，必须修复
- warning 项 fail → 记录到 backcheck_logs，继续但标注风险

## L2-B：写作完成 → 检查前

**目的**：确认论文忠实反映建模结果。

### 检查项

| ID | 检查项 | 方法 | 严重度 |
|---|---|---|---|
| B-01 | 数值一致性 | 论文关键数值 vs verify.py 输出 | critical |
| B-02 | 假设全文一致 | 正文假设 vs 符号说明 vs 模型建立 | critical |
| B-03 | 符号唯一性 | 全文符号无重复定义 | warning |
| B-04 | 参考文献真实 | 每条文献有 DOI/URL/出版信息 | critical |
| B-05 | 图表引用完整 | 每张图/表在正文有引用和解读 | warning |
| B-06 | 方法关键词 | 每个问题的解法都有明确的方法名称 | warning |
| B-07 | 创新点明确 | 论文含创新点/特异性表述 | warning |

### 判定规则

- B-01/B-02/B-04 fail → **阻止进入 Phase 4**，必须修复
- 其他 warning → 记录到 backcheck_logs，继续

## L2-C：最终检查前

**目的**：全局一致性终检。

### 检查项

| ID | 检查项 | 方法 | 严重度 |
|---|---|---|---|
| C-01 | 摘要数值一致 | 摘要关键数字 vs 正文/结果文件 | critical |
| C-02 | 图表编号连续 | 正文引用编号无跳号 | warning |
| C-03 | 提交物完整 | PDF/代码/支撑材料齐全 | critical |
| C-04 | 身份无泄漏 | 无学校/队号/手机号/邮箱 | critical |
| C-05 | 页数合规 | 正文 20-30 页（CUMCM） | critical |

### 判定规则

- 任何 critical 项 fail → **阻止提交**，必须修复
- warning 项 → 尽量修复，不阻止提交

## 输出格式

每次 L2 回溯检查的结果写入 `decision_log.json` 的 `backcheck_logs` 数组：

```json
{
  "check_id": "L2-A",
  "timestamp": "2023-09-04T12:00:00+08:00",
  "trigger": "Phase 2→3",
  "checks": [
    {
      "id": "A-01",
      "description": "子问题覆盖",
      "status": "pass",
      "evidence": "4 个子问题均有对应结果文件",
      "action": "none"
    },
    {
      "id": "A-06",
      "description": "时间预算",
      "status": "warn",
      "evidence": "剩余 18h，低于推荐值 20h",
      "action": "record_risk"
    }
  ],
  "verdict": "pass",
  "risks": ["剩余时间偏紧，建议简化灵敏度分析"]
}
```

## 行动等级

| 等级 | 触发条件 | 行动 |
|---|---|---|
| `none` | 检查通过 | 继续 |
| `record_risk` | warning 项 fail | 记录到 risks，继续 |
| `patch` | critical 项有简单修复方案 | 修补后继续（如补充一个缺失数值） |
| `block` | critical 项 fail 且无简单修复 | 阻止阶段转换，必须修复 |

## 实现方式

L2 检查**不由独立 Agent 执行**，而是在阶段转换时由当前 Agent 自行执行：

1. 读取 decision_log.json
2. 按检查项清单逐项检查
3. 输出结果到 backcheck_logs
4. 如果 verdict = block，暂停并报告用户
5. 修复后重新检查

这是单 Agent 架构内的自检机制，不是多 Agent 审查。
