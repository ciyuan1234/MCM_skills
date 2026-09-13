# 2026A 工作流样例（机理/PDE）

C 题样例见 [2023C-workflow-demo.md](2023C-workflow-demo.md)。A 类不要走「相关分析 → 回归 → 优化」。

你对 AI 说：

```text
我拿到 2026 国赛 A 题了。请按 cumcm skill 建立工作区，读题，按 22-mechanism-pde 给出每问建模路线。
```

期望输出（结构，不是把烘干数字抄到别的题上）：

```text
题型：A 类物理/连续。附件是烘房时序、半径收缩、物性公式，不是样本表。
已加载：references/22-mechanism-pde.md
工作区：0_赛题 … 5_支撑材料；各问已有 model.md 与 verify_qN.py
Phase 1：写 1_数据/units.md；附件只读；不平滑、不删点
四问路线（递进，禁止并行）：
  Q1 常数物性短时程 → 建立径向框架
  Q2 变物性 → 传热 vs 传质
  Q3 全周期终点 → 最慢点达标时间
  Q4 收缩几何 → 效应分解（路径缩短 vs 组织变密）
验证：V-PDE（初值、零驱动、守恒、r=0、K、网格+时间步）
下一步：填问题 1 的 model.md，用户确认后再编码
```

参考实现：https://github.com/ciyuan1234/MCM_2026
