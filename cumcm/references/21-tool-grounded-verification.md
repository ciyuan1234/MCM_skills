# 工具接地验证（Tool-Grounded Verification）

## 概述

LLM 提出数学模型后，用符号计算工具（SymPy/MATLAB Symbolic Toolbox）验证方程
的数学正确性。借鉴 O-Forge (arXiv 2510.12350) 的 In-Context Symbolic Feedback 循环。

**核心循环：**
```
LLM 提出方程 → SymPy 验证 → 通过则继续 / 失败则反馈给 LLM 修复 → 最多 3 轮
```

## 验证类型

### 1. 量纲一致性

检查方程两边单位是否匹配。

```python
import sympy as sp

# 定义带单位的符号
price = sp.Symbol('price', positive=True)  # 元/kg
demand = sp.Symbol('demand', positive=True)  # kg/日
revenue = price * demand  # 元·kg/(日·kg) = 元/日

# 验证: 收入 = 价格 × 销量
# 单位: [元/kg] × [kg/日] = [元/日] ✓
```

### 2. 边界行为

代入极端值检查结果是否合理。

```python
# 需求函数: q = a * p^b (b < 0)
a, p, b = sp.symbols('a p b', positive=True)
q = a * p**b

# 验证: 价格→∞时需求→0
limit_q = sp.limit(q, p, sp.oo)
# 应该 = 0（因为 b < 0）
assert limit_q == 0, f"边界错误: p→∞ 时 q→{limit_q}"

# 验证: 价格→0时需求→∞（理论上）
limit_q0 = sp.limit(q, p, 0)
# 应该 = ∞（因为 b < 0）
```

### 3. 守恒律

检查守恒量是否守恒。

```python
# 质量守恒: d(库存)/dt = 进货 - 销售 - 损耗
t = sp.Symbol('t')
stock = sp.Function('stock')(t)
inflow = sp.Function('inflow')(t)
sales = sp.Function('sales')(t)
loss = sp.Function('loss')(t)

# 守恒方程
conservation = sp.diff(stock, t) - (inflow - sales - loss)
# 验证: 如果 inflow=sales+loss, 则 d(stock)/dt=0
solution = sp.dsolve(conservation, stock)
```

### 4. 已知解对比

简化情况下的解析解。

```python
# 线性规划: min c^T x, s.t. Ax <= b, x >= 0
# 简化情况: min x, s.t. x >= 2 → 解 = 2
c = sp.Matrix([1])
A = sp.Matrix([[-1]])
b = sp.Matrix([-2])
# 用单纯形法验证
```

### 5. 约束满足

检查所有决策变量是否满足约束。

```python
# 优化结果
x_opt = [0.5, 1.2, 0.0, 3.1]  # 最优解

# 验证非负约束
assert all(x >= 0 for x in x_opt), f"违反非负约束: {x_opt}"

# 验证等式约束
A = [[1, 2, 3, 4]]
b_eq = [10]
assert abs(A[0] @ x_opt - b_eq[0]) < 1e-6, "违反等式约束"

# 验证不等式约束
A_ub = [[1, 1, 0, 0]]
b_ub = [3]
assert A_ub[0] @ x_opt <= b_ub[0] + 1e-6, "违反不等式约束"
```

## SymPy 验证脚本模板

```python
#!/usr/bin/env python3
"""SymPy 验证模板 — 验证 LLM 提出的方程"""
import sympy as sp

def verify_equation():
    checks = []
    
    # 1. 定义符号
    x, y, z = sp.symbols('x y z', real=True)
    
    # 2. LLM 提出的方程
    equation = sp.Eq(y, x**2 + 2*x + 1)
    
    # 3. 验证: 可以因式分解为 (x+1)^2
    factored = sp.factor(x**2 + 2*x + 1)
    checks.append(("因式分解", factored == (x+1)**2, str(factored)))
    
    # 4. 验证: 导数 = 2(x+1)
    derivative = sp.diff(x**2 + 2*x + 1, x)
    checks.append(("导数", sp.simplify(derivative - 2*(x+1)) == 0, str(derivative)))
    
    # 5. 输出报告
    print("=" * 50)
    print("SYMPY VERIFICATION REPORT")
    print("=" * 50)
    all_pass = True
    for name, passed, detail in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  [{name}] {status}  {detail}")
        if not passed:
            all_pass = False
    print("=" * 50)
    print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILED'}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    exit(verify_equation())
```

## 在工作流中的位置

```
Phase 2 建模
    ↓
LLM 提出数学模型（方程+约束）
    ↓
SymPy 验证（量纲/边界/守恒/约束）
    ↓
┌─ 通过 → 继续代码实现
│
└─ 失败 → 反馈错误信息给 LLM
        ↓
    LLM 修复方程
        ↓
    重新验证（最多 3 轮）
        ↓
    3 轮仍失败 → 暂停等用户
```

## 验证项清单

| 验证项 | 适用模型 | 工具 | 通过标准 |
|---|---|---|---|
| 量纲一致 | 所有 | SymPy | 方程两边单位匹配 |
| 边界行为 | 回归/优化 | SymPy limit | 极端值结果合理 |
| 守恒律 | ODE/动力学 | SymPy diff | 守恒量偏差 < 0.1% |
| 约束满足 | 优化 | numpy | 所有约束违反 ≤ 1e-6 |
| 单调性 | 回归/优化 | SymPy diff | 导数符号符合预期 |
| 非负性 | 需求/价格 | SymPy | 结果 ≥ 0 |

## 与 verify.py 的关系

| 工具 | 检查范围 | 执行时机 |
|---|---|---|
| SymPy 验证 | 单个方程的数学正确性 | Phase 2 模型建立后 |
| verify.py | 论文-代码-数据三方一致性 | Phase 4 提交前 |
| 配对验证 verify_*.py | 单个模型的完整验证 | 每个模型完成后 |

三者互补：SymPy 验证数学，配对验证模型，verify.py 验证论文。
