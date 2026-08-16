# CUMCM Skill Pack: AI Workflow for Mathematical Modeling Contest

[![CUMCM](https://img.shields.io/badge/CUMCM-Mathematical%20Modeling-blue)](#)
[![AI Skill](https://img.shields.io/badge/AI-Skill-green)](#)
[![Codex](https://img.shields.io/badge/OpenAI-Codex-black)](#)
[![Claude Code](https://img.shields.io/badge/Claude-Code-orange)](#)
[![opencode](https://img.shields.io/badge/opencode-supported-purple)](#)
[![Platform](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-supported-lightgrey)](#)

This repository provides an installable AI skill pack for the **China Undergraduate Mathematical Contest in Modeling (CUMCM)**.

It turns the 72-hour contest workflow into a repeatable AI-assisted process: problem reading, data profiling, model selection, coding, paper writing, format checking, result verification, and final packaging.

This is not just a prompt collection. It includes templates, scripts, checkers, scoring rubrics, anti-hallucination constraints, and reusable modeling references.

[中文 README](README.md) · [2023C Demo](examples/2023C-workflow-demo.md) · [Evaluation Framework](EVALUATION.md)

## Why Star This Repo

- **Ready for contest day**: scaffold a complete workspace with folders for problem statements, data, code, figures, paper, and supporting materials.
- **End-to-end CUMCM workflow**: from reading the problem to exporting the final PDF.
- **Anti-hallucination by design**: paper numbers must be traceable to data files and code outputs.
- **Built-in evaluation**: scripts and rubrics help determine whether a change improves or regresses the workflow.
- **Agent-friendly**: supports Claude Code, OpenAI Codex, and opencode skill directories.

## Quick Start

Clone the repository:

```powershell
git clone https://github.com/ciyuan1234/MCM_skills.git
cd MCM_skills
```

Install on Windows:

```powershell
.\install.ps1
```

Install on macOS / Linux:

```bash
chmod +x install.sh
./install.sh
```

Restart your AI coding agent, then ask:

```text
Create a CUMCM contest workspace and start the six-phase modeling workflow.
```

The installer copies `cumcm/` into:

| Tool | Skill directory |
|---|---|
| Claude Code | `~/.claude/skills/cumcm` |
| OpenAI Codex | `~/.codex/skills/cumcm` |
| AGENTS standard | `~/.agents/skills/cumcm` |
| opencode | `~/.config/opencode/skills/cumcm` |

## What It Does

| Phase | Capability | Output |
|---|---|---|
| Phase 0 | Read the problem, classify topic type, plan solution routes | Problem structure, model roadmap |
| Phase 1 | Profile datasets, check missing values and anomalies | Data quality report, `data_contract.json` |
| Phase 2 | Select models, write code, solve and validate | Reproducible scripts, result tables, plots |
| Phase 3 | Write abstract, body, figures, tables, references | `paper.md`, `paper.tex`, `paper.docx` |
| Phase 4 | Check format, traceability, and consistency | Verification reports, final PDF |
| Phase 5 | Package supporting materials | Submission archive |

## Repository Layout

```text
MCM_skills/
├── install.ps1 / install.sh       # one-click installer
├── README.md / README_EN.md       # Chinese and English entry points
├── EVALUATION.md                  # quality evaluation framework
├── examples/                      # demo outputs
├── evaluation/                    # benchmark prompts, rubrics, prior-paper notes
└── cumcm/
    ├── SKILL.md                   # orchestration instructions
    ├── references/                # contest rules, model catalog, writing guides
    ├── scripts/                   # scaffold, checks, verification, export, packaging
    └── assets/                    # paper templates, plotting style, progress log
```

## Common Commands

Create a contest workspace:

```powershell
.\cumcm\scripts\scaffold.ps1 -WorkDir .\workspace
```

Generate a data contract:

```powershell
python .\cumcm\scripts\make-data-contract.py .\workspace\1_数据 -o .\workspace\1_数据\data_contract.json
```

Check the paper and traceability:

```powershell
python .\cumcm\scripts\checks.py .\workspace\4_论文\paper.md .\workspace
python .\cumcm\scripts\verify.py .\workspace
python .\cumcm\scripts\format-check.py .\workspace
```

Export and package:

```powershell
.\cumcm\scripts\export-paper.ps1 -WorkDir .\workspace -Force
.\cumcm\scripts\package.ps1 -WorkDir .\workspace
```

## Anti-Hallucination Rules

- Data must come from real files.
- Phase 1 must generate `1_数据/data_contract.json`.
- Code must explicitly read source data files.
- Every important number in the paper must be traceable to code output or the data contract.
- Figures and tables must be generated from data, not manually fabricated.
- References must be real and actually used.
- Each model should include error analysis, stability checks, or sensitivity analysis.

## Suggested GitHub Topics

`cumcm` `mathematical-modeling` `ai-agent` `codex` `claude-code` `opencode` `skills` `latex` `python`

## Roadmap

- Add screenshots or a GIF for the full workflow.
- Add GitHub Actions for script checks and Tier 1 smoke tests.
- Add a license and contribution guide.
- Publish more end-to-end demos for past CUMCM problems.
- Split local Chinese resource indexes into optional extension packs.
