# 阶段交接协议（Hand-off Protocol）

## 概述

每个阶段结束时，强制生成 `hand_off.md` 文件。该文件是前后阶段之间的**结构化交接契约**，
确保上下文不丢失、事实不矛盾、下一步行动明确。

## 文件位置

```
runs/<workdir>/
  stage0_read/      hand_off.md    # Phase 0 → Phase 1
  stage1_data/      hand_off.md    # Phase 1 → Phase 2
  stage2_model/     hand_off.md    # Phase 2 → Phase 3
  stage3_write/     hand_off.md    # Phase 3 → Phase 4
```

## 三段式格式

```markdown
## What I did
<!-- 必填：列出产出文件（含路径）和完成的关键操作 -->

## What's true now
<!-- 必填：至少 3 条事实性陈述，涵盖以下维度 -->

## What you should do next
<!-- 必填：祈使句，具体行动 -->
```

## 各阶段交接内容

### Phase 0 → Phase 1（读题选题 → 数据探索）

**What I did：**
- 读取了 N 个赛题 PDF
- 完成题型分类：X 类
- 选择了 [题目编号]，理由：[ ]

**What's true now：**
- 选定题目：[编号] - [标题]
- 题型：[类型]（如 C_数据分析）
- 子问题数量：N 个
- 数据附件：[列表]，预估行数/字段数
- 剩余时间约：[ ]h
- 已知风险：[ ]

**What you should do next：**
1. 解压附件到 1_数据/ 目录
2. 逐个读取附件，建立字段含义表
3. 运行 make-data-contract.py 生成数据契约

### Phase 1 → Phase 2（数据探索 → 建模求解）

**What I did：**
- 读取了 N 个附件，共 X 行数据
- 数据质量：缺失值 X 个，异常值 X 个，重复值 X 个
- 处理方式：[均值填充/剔除/邻近值]
- 生成了 data_contract.json
- 生成了数据侧写报告

**What's true now：**
- 数据质量：[好/一般/差]，关键问题：[ ]
- 可用字段：[列表]
- 数据时间范围：[ ]
- 品类/单品数量：[ ]
- 剩余时间约：[ ]h

**What you should do next：**
1. 对问题一建立描述性统计与相关分析模型
2. 先做基线模型，再考虑升级

### Phase 2 → Phase 3（建模求解 → 论文写作）

**What I did：**
- 完成问题一：[模型名]，关键结果：[数值]
- 完成问题二：[模型名]，关键结果：[数值]
- 完成问题三：[模型名]，关键结果：[数值]
- 完成问题四：[模型名]，关键结果：[数值]
- 所有模型通过 verify.py 检查
- 灵敏度分析完成（扰动 ±5%/±10%）

**What's true now：**
- 问题一模型：[名称]，MAPE=X%，R²=X
- 问题二模型：[名称]，弹性系数范围 X-X
- 问题三模型：[名称]，最优补货量 X kg
- 问题四：[建议内容摘要]
- 关键数值已全部溯源
- 剩余时间约：[ ]h

**What you should do next：**
1. 按七章结构撰写论文
2. 摘要优先，五要素齐全
3. 每章结论带具体数值

### Phase 3 → Phase 4（论文写作 → 检查提交）

**What I did：**
- 完成论文 paper.md，共 X 页
- 摘要 X 字，含 N 处数值
- 图 N 张，表 N 个，公式 N 个
- 参考文献 N 条

**What's true now：**
- 论文页数：X 页（正文 X 页，附录 X 页）
- 图表数量：图 X 张，表 X 个
- 参考文献：X 条
- 已知问题：[列表]
- 剩余时间约：[ ]h

**What you should do next：**
1. 运行 checks.py 自动检查
2. 运行 verify.py 溯源检查
3. 执行 Fresh-eyes 审查
4. 导出 PDF + 打包 ZIP

## 验证规则

在进入下一阶段前，**强制验证** hand_off.md：

1. **文件存在**：`hand_off.md` 在对应阶段目录下存在
2. **三段完整**：三个 `## What` 段落都存在
3. **事实充足**："What's true now" 包含至少 3 个事实条目
4. **行动具体**："What you should do next" 是祈使句（以动词开头）

如果验证失败，**不得进入下一阶段**，必须补全 hand_off.md。

## 写入时机

- **阶段完成时**：立即写入 hand_off.md
- **阶段被中断时**：如果时间不足被迫跳过阶段，也要写入当前状态的 hand_off.md
- **L2 回溯修复后**：更新 hand_off.md 的 "What's true now" 部分
