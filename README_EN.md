<p align="center">
  <img src="https://img.shields.io/badge/CUMCM-Mathematical%20Modeling-1f6feb?style=flat-square" alt="CUMCM">
  <img src="https://img.shields.io/badge/skills-v2.2-2ea44f?style=flat-square" alt="v2.2">
  <img src="https://img.shields.io/github/stars/ciyuan1234/MCM_skills?style=flat-square&color=e8c872" alt="Stars">
</p>

# CUMCM Skill Pack

An installable AI skill for the **China Undergraduate Mathematical Contest in Modeling**: read the problem, model, verify, write the paper, check, and package. Not a prompt dump — templates, scripts, and golden problems included.

[中文](README.md) · [2023C demo](examples/2023C-workflow-demo.md) · [2026A demo](examples/2026A-workflow-demo.md)

Worked solver for 2026 Problem A: [ciyuan1234/MCM_2026](https://github.com/ciyuan1234/MCM_2026)

## Install

```bash
git clone https://github.com/ciyuan1234/MCM_skills.git
cd MCM_skills
chmod +x install.sh && ./install.sh
```

Windows: `.\install.ps1`

Copies `cumcm/` into Claude Code, Codex, opencode, and Grok (`~/.grok/skills/cumcm`). Then ask:

```text
Create a CUMCM workspace, read the problem, classify A–E, and propose a route per question.
```

A-type (PDE / heat–mass) loads `references/22-mechanism-pde.md`. C-type starts from `data_contract.json`.

## What you get

| Type | Path |
| --- | --- |
| Data (C/E) | data contract → regression / optimization → V-REG / V-OPT |
| Mechanism (A) | unit dictionary, conservation, grid/time-step checks, V-PDE |
| Scheduling (B) | feasible baseline first, then V-OPT |

Scaffold pre-creates `1_数据/units.md`, `2_代码/0N/model.md`, and `verify_qN.py`. `verify.py` now checks those artifacts.

Full index: [`cumcm/SKILL.md`](cumcm/SKILL.md). Changelog: [`CHANGELOG.md`](CHANGELOG.md).
