# 多 Agent 并行子问题

## 概述

v1.8.0 引入可选的多 Agent 并行模式：当问题包含 ≥ 2 个独立子问题时，
可以为每个子问题启动独立的 Agent，各自完成 build → verify → self-approve 循环。

**仅在以下条件满足时启用：**
1. 子问题之间**数据独立**（不共享中间结果）
2. 子问题之间**模型独立**（不依赖其他子问题的模型输出）
3. 用户明确选择 AP 模式
4. 剩余时间 > 24h

如果子问题之间有依赖（如问题二依赖问题一的输出），**不得并行**。

## 架构

```
主 Agent（编排器）
├── 子 Agent 1：问题一 build + verify
├── 子 Agent 2：问题二 build + verify
├── 子 Agent 3：问题三 build + verify
└── 子 Agent 4：问题四 build + verify
    ↓
主 Agent：跨问题一致性检查 → 敏感度分析 → 论文写作
```

## 启用条件检查

在启动并行前，主 Agent 必须确认：

```json
{
  "parallel_eligible": true,
  "reason": "4 个子问题数据独立，模型独立，剩余 30h",
  "sub_problems": [
    {"id": "Q1", "data_files": ["附件1.csv"], "model_type": "统计分析"},
    {"id": "Q2", "data_files": ["附件2.csv"], "model_type": "回归"},
    {"id": "Q3", "data_files": ["附件3.csv"], "model_type": "优化"},
    {"id": "Q4", "data_files": ["附件1-3.csv"], "model_type": "建议"}
  ],
  "dependency_graph": {
    "Q1": [], "Q2": [], "Q3": [], "Q4": ["Q1", "Q2", "Q3"]
  }
}
```

**注意**：如果任何子问题依赖其他子问题（如 Q4 依赖 Q1-Q3），则 Q4 不可并行，
只有 Q1-Q3 可以并行。

## 子 Agent 任务模板

每个子 Agent 收到的 prompt 包含：

1. **问题描述**：从赛题 PDF 提取的该子问题全文
2. **数据文件路径**：该子问题所需的数据文件
3. **模型约束**：必须使用的模型类型（如有）
4. **验证要求**：必须通过的验证项
5. **输出路径**：结果文件写入位置

子 Agent **不**收到：
- 其他子问题的信息
- 论文当前状态
- 敏感度分析要求（由主 Agent 统一做）

## 执行流程

### Step 1：主 Agent 分析依赖

```
读取赛题 → 提取子问题 → 分析数据依赖 → 构建依赖图
→ 标记可并行的子问题集
```

### Step 2：启动子 Agent

主 Agent 在一条消息中同时启动 N 个子 Agent：

```
Agent(description="Q1 build+verify", prompt=<子Agent模板 Q1>)
Agent(description="Q2 build+verify", prompt=<子Agent模板 Q2>)
Agent(description="Q3 build+verify", prompt=<子Agent模板 Q3>)
```

### Step 3：等待完成

主 Agent 等待所有子 Agent 返回。每个子 Agent 输出：

```
[Q1] ✓ 全部验证通过，结果已写入 results_q1.csv
[Q2] ✓ 全部验证通过，结果已写入 results_q2.csv
[Q3] ✓ 全部验证通过，结果已写入 results_q3.csv
```

### Step 4：跨问题一致性检查

主 Agent 执行：

1. **常量一致性**：物理常量、参数在所有子问题中一致
2. **数据源一致性**：所有子问题使用相同的数据预处理结果
3. **单位一致性**：单位在所有子问题中一致
4. **术语一致性**：同一概念使用相同术语

### Step 5：依赖问题处理

对有依赖的子问题（如 Q4 依赖 Q1-Q3），主 Agent 在并行完成后串行处理：

```
读取 Q1-Q3 结果 → 作为 Q4 输入 → 运行 Q4 模型 → 验证
```

### Step 6：统一敏感度分析

主 Agent 统一做全局敏感度分析（不交给子 Agent）。

## 冲突解决

如果子 Agent 之间对共享资源（如公共函数、全局配置）有冲突：

1. 每个子 Agent 使用独立的代码目录
2. 公共函数放入 `2_代码/common/`，只读不写
3. 结果文件按子问题命名（`results_q1.csv`, `results_q2.csv`）

## 回退策略

如果任何子 Agent 失败：

1. 主 Agent 等待其他子 Agent 完成
2. 分析失败原因
3. 修复后重新启动失败的子 Agent（不重跑成功的）
4. 如果时间不足，降级为串行处理

## 与 AP/Manual 模式的关系

| 模式 | 并行行为 |
|---|---|
| AP | 自动分析依赖 + 自动启动子 Agent + 自动一致性检查 |
| Manual | 分析依赖后暂停，等用户确认再启动子 Agent |

## 与 L2 的关系

并行完成后，主 Agent 必须执行 L2-A 回溯检查（子问题覆盖 + 模型选择理由），
确保所有子问题都已完成且结果可用。
