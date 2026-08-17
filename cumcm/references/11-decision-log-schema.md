# 决策日志 Schema（decision_log.json）

## 概述

`decision_log.json` 是比赛工作区的**结构化持久记忆**。替代旧版 `进度日志.md` 自然语言记录，
所有字段有明确 schema，支持程序化读取和跨阶段一致性检查。

**存放位置**：`runs/<workdir>/decision_log.json`

## 完整 Schema

```json
{
  "_schema_version": "1.0",
  "competition": "cumcm",
  "problem": "C",
  "problem_meta": {
    "year": 2023,
    "letter": "C",
    "title": "蔬菜类商品的自动定价与补货决策",
    "deadline_iso": "2023-09-05T18:00:00+08:00",
    "team_control_number": "2023xxxxx"
  },
  "mode": "manual",
  "started_at": "2023-09-02T18:00:00+08:00",
  "current_stage": 2,
  "budget": {
    "total_hours": 72,
    "started_at": "2023-09-02T18:00:00+08:00",
    "elapsed_hours": 36.5,
    "remaining_hours": 35.5,
    "stage_durations_h": { "0": 3.2, "1": 4.5 },
    "pause_offset_seconds": 0
  },
  "stages": {
    "0": {
      "_label": "读题选题",
      "status": "completed",
      "started_at": "2023-09-02T18:00:00+08:00",
      "completed_at": "2023-09-02T21:12:00+08:00",
      "artifacts": ["0_赛题/2023_C_题.pdf", "decision_log.json"],
      "results": {
        "chosen_problem": "C",
        "problem_type": "C_数据分析",
        "sub_problems": 4
      },
      "risks": ["数据量大(87万行)，预处理耗时可能超预期"]
    }
  },
  "decisions": [
    {
      "stage": 0,
      "timestamp": "2023-09-02T20:30:00+08:00",
      "decision": "选择 C 题（蔬菜定价）",
      "reason": "数据完整（4个附件），团队有数据分析经验",
      "alternatives_rejected": ["A题（信号处理，无相关经验）", "B题（图像识别，无相关经验）"]
    }
  ],
  "backcheck_logs": [],
  "events": [
    {
      "timestamp": "2023-09-02T18:00:00+08:00",
      "type": "stage_start",
      "stage": 0,
      "detail": "比赛开始，进入 Phase 0"
    }
  ]
}
```

## 字段说明

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `_schema_version` | string | 是 | Schema 版本号，当前 "1.0" |
| `competition` | enum | 是 | "cumcm" / "mcm" / "diangong" |
| `problem` | string | 否 | 选定的题目编号（如 "C"），未选题时为 null |
| `problem_meta` | object | 是 | 题目元信息 |
| `mode` | enum | 是 | "manual" / "ap" — 运行模式 |
| `started_at` | ISO8601 | 是 | 比赛开始时间（首次运行时写入） |
| `current_stage` | int | 是 | 当前所在阶段（0-4） |
| `budget` | object | 是 | 时间预算 |
| `stages` | object | 是 | 各阶段状态 |
| `decisions` | array | 是 | 关键决策记录 |
| `backcheck_logs` | array | 是 | L2 回溯检查结果 |
| `events` | array | 是 | 时间线事件 |

### budget 对象

| 字段 | 类型 | 说明 |
|---|---|---|
| `total_hours` | number | 总时间预算（CUMCM=72，MCM=96） |
| `started_at` | ISO8601 | 计时开始时间 |
| `elapsed_hours` | number | 已用时间（小时），每次阶段切换更新 |
| `remaining_hours` | number | 剩余时间（小时） |
| `stage_durations_h` | object | 各阶段实际耗时（小时） |
| `pause_offset_seconds` | number | 暂停累计时间（秒），AP 模式切换时计算 |

### stages 对象（每个阶段）

| 字段 | 类型 | 说明 |
|---|---|---|
| `_label` | string | 阶段名称（只读） |
| `status` | enum | "not_started" / "in_progress" / "completed" / "blocked" |
| `started_at` | ISO8601 | 阶段开始时间 |
| `completed_at` | ISO8601 | 阶段完成时间 |
| `artifacts` | string[] | 该阶段产出的文件路径列表 |
| `results` | object | 关键数值结果（真实数值，非描述） |
| `risks` | string[] | 该阶段发现的风险项 |
| `sub_problems` | object | 仅 stage 2：按问题编号组织的子问题状态 |

### decisions 数组元素

| 字段 | 类型 | 说明 |
|---|---|---|
| `stage` | int | 决策所在阶段 |
| `timestamp` | ISO8601 | 决策时间 |
| `decision` | string | 决策内容 |
| `reason` | string | 选择理由 |
| `alternatives_rejected` | string[] | 被拒绝的备选方案 |

### events 数组元素

| 字段 | 类型 | 说明 |
|---|---|---|
| `timestamp` | ISO8601 | 事件时间 |
| `type` | enum | "stage_start" / "stage_complete" / "mode_change" / "backcheck" / "lockdown" / "degradation" |
| `stage` | int | 相关阶段（可选） |
| `detail` | string | 事件描述 |

## 读写规则

1. **每个阶段开始时**：读取 decision_log.json，恢复 current_stage + stages[N] 状态
2. **每个阶段结束时**：更新 stages[N].status/completed_at/results/artifacts/risks
3. **每次关键决策时**：追加到 decisions 数组
4. **每次阶段切换时**：更新 budget.elapsed_hours + remaining_hours + current_stage
5. **新会话第一步**：读取 decision_log.json，无需再读进度日志.md

## 与旧版进度日志.md 的关系

- decision_log.json **完全替代** 进度日志.md
- scaffold 脚本不再生成 进度日志.md，改为生成 decision_log.json
- 如用户仍需人类可读的进度摘要，可从 decision_log.json 自动生成
