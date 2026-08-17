# 三层记忆架构

## 概述

解决长会话丢上下文问题。借鉴 Mem0 (ECAI 2025)、H-Mem (EACL 2026) 和
Zettelkasten 笔记法的分层记忆设计。

## 三层结构

| 层 | 文件 | 内容 | 大小限制 | 更新频率 |
|---|---|---|---|---|
| 核心记忆 | `memory/working_context.md` | 当前状态、活跃目标、最近决策 | ≤5000 tokens | 每阶段切换 |
| 回忆记忆 | `memory/decisions_log.md` | 时间线决策记录、中间结果 | 可增长 | 每次决策 |
| 归档记忆 | `memory/knowledge_base.md` | 压缩的模型库、反思银行、经验 | 按主题压缩 | 比赛结束 |

## 文件结构

```
runs/<workdir>/
├── decision_log.json          # 结构化状态（脚本读取）
├── memory/
│   ├── working_context.md     # 核心记忆（Agent 读取）
│   ├── decisions_log.md       # 回忆记忆（时间线）
│   └── knowledge_base.md      # 归档记忆（经验积累）
```

## 核心记忆（working_context.md）

每次会话开始时读取此文件，恢复工作状态。

```markdown
# 当前工作上下文

## 比赛信息
- 竞赛: CUMCM 2023
- 题目: C 题 蔬菜定价与补货
- 队伍: [队号]
- 截止: 2023-09-05 18:00

## 当前状态
- 阶段: Phase 2 (建模求解)
- 已完成: Q1(描述统计), Q2(弹性回归)
- 进行中: Q3(补货优化)
- 待做: Q4(数据建议), 灵敏度分析, 论文

## 关键结果
- 品类弹性: 花叶-0.48, 水生根茎-0.72, 花菜-0.31, 茄类-0.89, 葱蒜-0.55, 豆类-0.41
- 最优补货量: 花叶类 139.685 kg/日（日毛利 177.4 元）
- 预测精度: ARIMA MAPE=4.1%

## 活跃假设
- A1: 日销量近似正态分布 (Shapiro-Wilk p=0.12)
- A2: 损耗率品类内统一 (基于附件3)
- A3: 价格弹性恒定 (R²=0.87)

## 活跃风险
- 剩余 30h，Q3 优化求解可能耗时
- 附录代码块可能有 Overfull

## 最近决策
- 选 C 题：数据完整，团队有数据分析经验
- Q2 用对数线性回归而非多项式：更稳健
```

## 回忆记忆（decisions_log.md）

按时间线记录所有决策和中间结果。

```markdown
# 决策日志

## 2023-09-02 18:00 — Phase 0
- [决策] 选择 C 题
- [理由] 数据完整（4个附件），团队有数据分析经验
- [拒绝] A题（信号处理，无相关经验），B题（图像识别，无相关经验）

## 2023-09-02 21:00 — Phase 1
- [结果] 数据质量：87.8万行，0缺失，461条退货（0.05%）
- [处理] 退货记录标记为负值，不剔除
- [产出] data_contract.json

## 2023-09-03 10:00 — Phase 2 Q1
- [模型] 描述统计 + Spearman 相关分析
- [结果] 花叶-茄类 r=-0.84（强负相关）
- [决策] 品类按销量分四档，用于差异化定价

## 2023-09-03 18:00 — Phase 2 Q2
- [模型] 对数线性回归 ln(q) = a + b*ln(p)
- [结果] 弹性 b ∈ [-0.89, -0.31]
- [决策] 不用多项式回归：弹性更稳健，物理意义明确
- [拒绝] 多项式回归：过拟合风险，外推不稳定
```

## 归档记忆（knowledge_base.md）

比赛结束后压缩归档，为下次比赛积累经验。

```markdown
# 知识库

## 2023C 经验

### 模型经验
- 蔬菜类品价格弹性范围: [-0.89, -0.31]（文献值一致）
- 对数线性回归在价格-需求关系上表现好
- 模拟退火求解 0-1 选品模型收敛良好

### 代码经验
- plot_extra.py 需要从原始数据计算 P75（results_q2_summary.csv 被精简后不包含）
- 多源表（合并多个 CSV）的 verify 检查需要按列分组匹配

### 写作经验
- 附录代码块 verbatim 会导致 Overfull，考虑用 lstlisting 替代
- 表 3 移至附录后需重新编号引用

### 时间经验
- 数据预处理实际耗时 5h（超预期，87万行清洗）
- 论文写作实际耗时 22h（超预期，附录扩充）
```

## 与 decision_log.json 的关系

| 文件 | 格式 | 读取者 | 用途 |
|---|---|---|---|
| `decision_log.json` | JSON | 脚本 + Agent | 结构化状态、时间预算、stage 状态 |
| `working_context.md` | Markdown | Agent | 核心工作状态、关键结果、假设 |
| `decisions_log.md` | Markdown | Agent | 时间线决策记录 |
| `knowledge_base.md` | Markdown | Agent | 归档经验、跨比赛知识 |

**原则：** JSON 用于程序化验证，MD 用于 Agent 上下文恢复。两者信息互补，不重复。

## 工作流程

```
会话开始
    ↓
读 working_context.md（恢复核心状态）
    ↓
读 decision_log.json（恢复结构化状态）
    ↓
执行当前阶段
    ↓
每次决策 → 追加到 decisions_log.md
    ↓
阶段结束 → 更新 working_context.md + decision_log.json
    ↓
比赛结束 → 压缩 decisions_log.md → 写入 knowledge_base.md
```

## 大小控制

- `working_context.md`：严格 ≤5000 tokens，超出时压缩旧结果
- `decisions_log.md`：可增长，但每阶段结束后压缩早期记录为摘要
- `knowledge_base.md`：按比赛年份组织，每年压缩为 1-2 页
