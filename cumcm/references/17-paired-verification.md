# 配对验证脚本规范（Paired Verification）

## 概述

v1.8.0 引入配对验证模式：每个求解脚本 `src/models/problemN_*.py` 必须配套一个
验证脚本 `src/verifications/verify_problemN_*.py`。所有验证通过（`✓ PASS`）后，
结果才能写入论文。任何 `✗ FAIL` 强制回退到模型构建阶段修复。

借鉴 AutoMCM-Pro 的 mandatory self-verification 模式。

## 命名规范

| 求解脚本 | 验证脚本 |
|---|---|
| `2_代码/01_问题1/solve_q1.py` | `2_代码/01_问题1/verify_q1.py` |
| `2_代码/02_问题2/solve_q2_elasticity.py` | `2_代码/02_问题2/verify_q2_elasticity.py` |
| `2_代码/common/optimization.py` | `2_代码/common/verify_optimization.py` |

## 按模型类型的验证项

### 优化模型（LP/QP/MIP/NLP）

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-OPT-1 | 原始可行性 | 检查所有约束是否严格满足 | 违反量 ≤ 5% |
| V-OPT-2 | 替代求解器交叉验证 | 用不同求解器（如 SLSQP → differential_evolution） | 目标值差异 ≤ 1% |
| V-OPT-3 | 扰动测试 | 对最优解各分量 ±0.1% 随机扰动 | 扰动后目标值不优于原始 |
| V-OPT-4 | 灵敏度快检 | 关键约束 RHS ±5% | 计算目标函数变化率（影子价格估计） |

### 回归/机器学习模型

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-REG-1 | 残差正态性 | Shapiro-Wilk 检验 | p > 0.05 |
| V-REG-2 | 异方差性 | Breusch-Pagan 检验 | p > 0.05 |
| V-REG-3 | 自相关性 | Durbin-Watson 统计量 | 1.5 < DW < 2.5 |
| V-REG-4 | 泛化能力 | 5 折交叉验证 | CV-RMSE / 样本内 RMSE < 1.2 |
| V-REG-5 | Monte Carlo 稳定性 | Bootstrap 1000 次 | 参数置信区间合理 |

### ODE/动力学模型

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-ODE-1 | 守恒律验证 | 检查守恒量偏差 | 偏差 < 0.1% |
| V-ODE-2 | 边界条件检查 | t=0 和 t=T 数值解 | 误差 < 1e-6 |
| V-ODE-3 | 网格收敛 | 步长 h 和 h/2 解差异 | 差异 < 0.1% |
| V-ODE-4 | 解析解对比 | 简化情况数值 vs 解析 | 误差 < 1% |

### 图/网络模型

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-GRF-1 | 路径合法性 | 检查每条边是否在原图中存在 | 100% 存在 |
| V-GRF-2 | 流守恒 | 中间节点流入=流出 | 误差 < 1e-9 |
| V-GRF-3 | 小规模暴力 | ≤10 节点子图穷举对比 | 与穷举解一致 |

### 时序预测模型

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-TS-1 | 平稳性 | ADF/KPSS 检验 | 残差平稳 |
| V-TS-2 | 残差白噪声 | Ljung-Box 检验 | p > 0.05 |
| V-TS-3 | 预测区间覆盖 | 80%/95% 预测区间 | 覆盖率接近名义水平 |
| V-TS-4 | 多步 vs 单步 | 多步预测精度 vs 单步 | 衰减比 ≤ 2.0 |

### 统计分析模型

| ID | 检查项 | 方法 | 通过标准 |
|---|---|---|---|
| V-STAT-1 | 假设检验前提 | 正态性/方差齐性 | 满足检验前提 |
| V-STAT-2 | 效应量 | Cohen's d / η² | 报告效应量，不只报告 p 值 |
| V-STAT-3 | 置信区间 | 95% CI | CI 不包含零（或合理） |

## 验证脚本模板

每个验证脚本必须输出机器可解析的报告：

```python
#!/usr/bin/env python3
"""验证脚本模板 — 问题 N 模型名"""
import sys

def main():
    checks = []  # (check_id, passed: bool, detail: str)

    # === 在此添加验证逻辑 ===
    # checks.append(("V-OPT-1", True, "所有约束满足，最大违反 0.02%"))
    # checks.append(("V-OPT-2", True, "替代求解器目标值差异 0.3%"))

    # === 输出报告 ===
    print("=" * 60)
    print("VERIFICATION REPORT — 问题N 模型名")
    print("=" * 60)
    all_pass = True
    for check_id, passed, detail in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  [{check_id}] {status}  {detail}")
        if not passed:
            all_pass = False
    print("=" * 60)
    print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILED — SEE ABOVE'}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
```

## 执行流程

```
求解脚本运行成功
    ↓
编写验证脚本
    ↓
运行验证脚本
    ↓
┌─ 全部 ✓ PASS → 结果可写入论文
│
└─ 任何 ✗ FAIL → 回到模型构建阶段
        ↓
    修复模型/代码
        ↓
    重新运行验证
        ↓
    循环直到全部 PASS
```

## 与 verify.py 的关系

| 工具 | 检查范围 | 执行时机 |
|---|---|---|
| `verify_*.py`（配对验证） | 单个模型的数学正确性 | 每个模型完成后立即 |
| `scripts/verify.py`（全局溯源） | 论文-代码-数据三方一致性 | Phase 4 提交前 |

配对验证是**模型级**的深度检查，全局溯源是**论文级**的一致性检查。两者互补。
