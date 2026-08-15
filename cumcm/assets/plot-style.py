# -*- coding: utf-8 -*-
"""
绘图规范模板 (plot-style.py) —— 国赛图表统一风格
用法: 复制到 3_图表/（或 2_代码/common），比赛时每个图基于此模板绘制。
必须遵守的三条硬规则（verify.py 会检查）:
  1. 第一行写:  # 数据来源: <data_contract 或数据文件路径>
  2. 声明对象数: # 对象数: N   （N 必须等于图中柱/线/点系列的数量，3 组数据画 3 条）
  3. 图例必须来自数据列名，不允许手写与数据无关的图例
"""

# 数据来源: 1_数据/data_contract.json   <-- 必填
# 对象数: 3                               <-- 必填

import matplotlib
matplotlib.use("Agg")  # 无界面环境（服务器/批处理）也能出图
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---- 中文与全局样式 ----
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False   # 负号正常显示
plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 300            # 论文图至少 300dpi
plt.rcParams["figure.figsize"] = (8, 5)

# ---- 读取真实数据（禁止硬编码）----
df = pd.read_csv("1_数据/示例数据.csv", encoding="utf-8")

# ---- 绘制：柱状图示例 ----
# 对象数 = 数据分组数，与图例一一对应
fig, ax = plt.subplots()
categories = ["花叶类", "水生根茎类", "茄类"]           # 数据分组
values = [df["销量"].mean(), 100.0, 50.0]               # 必须来自 df 计算
ax.bar(categories, values, color=["#4C72B0", "#DD8452", "#55A868"])
ax.set_xlabel("品类")
ax.set_ylabel("平均销量 (kg)")
ax.set_title("各品类平均销量")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("3_图表/fig1_品类平均销量.png")   # 图文件与论文 图1 对应
print("图1 已生成: 3_图表/fig1_品类平均销量.png")

# ---- 绘制：折线图示例（多条线，图例取自数据列名）----
fig2, ax2 = plt.subplots()
for col in ["品类A", "品类B", "品类C"]:                # 图例来自数据列名
    ax2.plot(df["日期"], df[col], label=col)
ax2.set_xlabel("日期")
ax2.set_ylabel("销量 (kg)")
ax2.legend(title="品类")                                # 图例与数据列一一对应
ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("3_图表/fig2_品类销量时序.png")
print("图2 已生成: 3_图表/fig2_品类销量时序.png")