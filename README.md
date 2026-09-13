<p align="center">
  <img src="https://img.shields.io/badge/CUMCM-数学建模-1f6feb?style=flat-square" alt="CUMCM">
  <img src="https://img.shields.io/badge/skills-v2.2-2ea44f?style=flat-square" alt="v2.2">
  <img src="https://img.shields.io/badge/Claude%20%7C%20Codex%20%7C%20Grok%20%7C%20opencode-supported-lightgrey?style=flat-square" alt="agents">
  <img src="https://img.shields.io/github/stars/ciyuan1234/MCM_skills?style=flat-square&color=e8c872" alt="Stars">
</p>

# CUMCM Skill Pack · 国赛全流程助手

给 AI 用的 **全国大学生数学建模竞赛** 技能包：读题、数据、建模、验证、写论文、检查、打包。不是提示词合集，是带模板、脚本和黄金测试集的可安装包。

[English](README_EN.md) · [2023C 数据题样例](examples/2023C-workflow-demo.md) · [2026A 机理题样例](examples/2026A-workflow-demo.md) · [评测](EVALUATION.md)

配套实战仓库（2026 A 烘干，四问可复现）：[ciyuan1234/MCM_2026](https://github.com/ciyuan1234/MCM_2026)

## 它解决什么

开赛 72 小时里，AI 最容易：编数字、用错题型套路、写到一半丢上下文、交卷前对不上表。这套 skill 把这些变成可检查的规则。

| 题型 | 走哪条线 |
| --- | --- |
| C / E 数据题 | 数据契约 → 回归/优化 → V-REG / V-OPT |
| A 机理 / PDE | [`22-mechanism-pde.md`](cumcm/references/22-mechanism-pde.md) → 单位字典、守恒、网格收敛、V-PDE |
| B 调度 / 规划 | 基线可行解 → V-OPT，复杂方法要能解释 |

## 30 秒上手

```bash
git clone https://github.com/ciyuan1234/MCM_skills.git
cd MCM_skills
chmod +x install.sh && ./install.sh
```

Windows：`.\install.ps1`

装到：Claude Code、Codex、opencode、Grok（`~/.grok/skills/cumcm`）。重启 Agent 后说：

```text
按 cumcm skill 建立比赛工作区，读题，判断 A–E 题型，给出每问建模路线。
```

A 类应加载 22、写 `units.md`、每问先 `model.md` 再编码。  
C 类应生成 `1_数据/data_contract.json`，论文数字能溯源。

## 工作区长什么样

```text
0_赛题/  1_数据/  2_代码/01_问题1/  …  3_图表/  4_论文/  5_支撑材料/
decision_log.json    # 阶段、决策、剩余时间
1_数据/units.md      # 机理题：由 units-template.md 复制后填写
2_代码/0N/model.md   # 每问模型说明
2_代码/0N/verify_qN.py
```

## 常用命令

```bash
./cumcm/scripts/scaffold.sh ./workspace
python cumcm/scripts/make-data-contract.py ./workspace/1_数据 -o ./workspace/1_数据/data_contract.json
python cumcm/scripts/verify.py ./workspace
python cumcm/scripts/checks.py ./workspace/4_论文/paper.md ./workspace
python cumcm/scripts/run_golden.py ./workspace --problem 2026_A -v
```

## 里面有什么

- 72 小时五阶段 + 锁定模式（剩余 ≤ 6 h 只写不建模）
- 配对验证：V-OPT / V-REG / V-ODE / **V-PDE** / V-GRF / V-TS / V-STAT
- 黄金测试集：2021C、2022C、2023C、**2026A**
- 反幻觉：`data_contract.json` + `verify.py`；机理题再加 `run_manifest.json`
- 论文：摘要最后写、假设编号闭环、评委黑白打印用灰阶图

完整目录、脚本和 references 索引见 [`cumcm/SKILL.md`](cumcm/SKILL.md)。版本记录见 [`CHANGELOG.md`](CHANGELOG.md)。

## 许可与贡献

使用与二次开发请保留来源。问题与 PR 见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
