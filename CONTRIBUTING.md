# Contributing

感谢你改进这个 CUMCM skill 包。这个项目更看重“可复现、可检查、能在比赛中落地”的改动。

## 适合提交的内容

- 新的往届题端到端 demo
- `checks.py`、`verify.py`、`format-check.py` 的规则修复
- 论文模板、图表模板、导出脚本改进
- 模型目录和题型映射补充
- README、安装说明、英文文档优化

## 提交前检查

至少运行：

```powershell
git diff --check
```

如果本机有 Python：

```powershell
python -m py_compile cumcm\scripts\*.py evaluation\auto-score.py
```

如果改了论文检查、导出或打包逻辑，请尽量补充：

```powershell
python cumcm\scripts\checks.py <workspace>\4_论文\paper.md <workspace>
python cumcm\scripts\verify.py <workspace>
python cumcm\scripts\format-check.py <workspace>
```

## 质量原则

- 不编造数据、结果或参考文献。
- 新增示例必须标明数据来源和可复现步骤。
- 新增规则要说明它解决了哪类真实扣分点。
- 不把大型私有资料库直接提交到仓库。
- 评测资料可以脱敏，但不要伪造“真实运行结果”。

## Commit 建议

使用能说明版本和意图的提交信息，例如：

```text
v1.6.0: add 2024C workflow demo and verification baseline
fix: handle multi-sheet data contract categories
docs: improve quick start for Codex users
```
