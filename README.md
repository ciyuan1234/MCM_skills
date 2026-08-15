# MCM_skills — 全国大学生数学建模竞赛 AI 参赛技能包

一套面向 **全国大学生数学建模竞赛（CUMCM）** 的高质量 AI 技能（skill），
同时适用于 **Claude Code / OpenAI Codex / opencode** 三种编程代理工具。

内容基于对 1992-2023 历年赛题、历届获奖论文、官方格式规范、36 篇经验分享、
32 种常规建模方法、28+ 份 MATLAB 现成代码、Python 建模教材的系统研读，
把"老队伍的经验"固化成 AI 可以直接执行的工作流。

## 它能干什么

- **读题选题**：提取题目四层结构，判断 A-E 题型，给出技术路线
- **数据探索**：数据侧写、缺失值处理、相关性分析
- **建模求解**：题型→模型映射、32 种方法、十大算法；复用本地现成代码（含 bug 修复版）
- **论文写作**：摘要五要素、七章结构、图表规范、GB/T 7714 参考文献
- **检查提交**：自动检查论文格式，打包支撑材料

## 目录结构

```
MCM_skills/
├── install.ps1 / install.sh   # 一键安装到三个工具
├── EVALUATION.md               # 质量评估框架（判断改动是变好还是变坏）
├── evaluation/                 # benchmark 提示词、评分表、运行器、样例数据
├── cumcm/                     # skill 本体（安装目标就是它）
│   ├── SKILL.md               # 编排层：启动协议 + 六阶段工作流 + 溯源红线
│   ├── references/            # 深度知识（按需加载）
│   │   ├── 01-competition-format.md   论文格式规范
│   │   ├── 02-scoring-and-award.md    评阅标准 + 获奖论文解剖
│   │   ├── 03-model-catalog.md        题型映射 + 32 法 + 十大算法
│   │   ├── 04-code-library.md         MATLAB/Python 代码库 + 修复版
│   │   ├── 05-abstract-and-writing.md 摘要与论文写作
│   │   ├── 06-checklists.md           阶段清单 + 交卷核对
│   │   ├── 07-local-resources.md      本地书籍/数据/网站/软件索引
│   │   ├── 08-faq-and-pitfalls.md     常见坑速查
│   │   ├── 09-timeline-and-team.md    72h 时间表 + 团队分工
│   │   └── 10-constraints-and-tools.md 防幻觉约束 + 工具用法
│   ├── scripts/
│   │   ├── scaffold.ps1/.sh    一键创建比赛工作区（预置契约/绘图模板）
│   │   ├── make-data-contract.py  数据契约生成（Phase 1 强制）
│   │   ├── checks.py/.ps1      论文自动检查器
│   │   ├── verify.py           溯源硬校验（反 AI 幻觉核心）
│   │   ├── export-paper.ps1    论文导出 PDF（md/tex → Word COM）
│   │   ├── md2docx.py          Markdown → docx 转换器
│   │   └── package.ps1/.sh     支撑材料打包
│   └── assets/
│       ├── paper-template.md   论文模板（Word 路线）
│       ├── paper-template.tex  论文模板（LaTeX 路线）
│       ├── plot-style.py       绘图规范模板（必用）
│       ├── data-contract-template.json  数据契约模板
│       ├── result-table-samples.md  图表/三线表规范样例
│       └── progress-log-template.md 进度日志模板
└── examples/2023C-workflow-demo.md  全流程输出风格演示
```

## 安装

### 方式一：一键安装脚本

Windows（PowerShell）：
```powershell
.\install.ps1
```

macOS / Linux：
```bash
./install.sh
```

脚本会把 `cumcm/` 复制到四个位置：
- Claude Code：`~/.claude/skills/cumcm`
- Codex (v1)：`~/.codex/skills/cumcm`
- Codex / AGENTS 标准：`~/.agents/skills/cumcm`
- opencode：`~/.config/opencode/skills/cumcm`

opencode 会自动加载 `~/.claude/skills` 与 `~/.agents/skills`，无需额外配置。

### 方式二：手动复制

把 `cumcm/` 整个文件夹复制到对应工具的 skills 目录即可（同上表）。
**安装/更新后请重启对应工具。**

## 使用

在任意工具中自然语言触发（skill 会自动被识别）：

- "我拿到 2026 国赛 A 题了，帮我读题并分析"
- "建立比赛工作目录"
- "帮我选模型并写代码解问题二"
- "写论文摘要"
- "检查论文格式"
- "打包支撑材料"

开赛后建议：
1. 先用 `scaffold.ps1` 建工作区
2. 让 AI 读题 → 数据探索（**跑 `make-data-contract.py` 生成数据契约**）→ 建模求解
3. 第 40 小时起进入写作，摘要优先；绘图一律套用 `plot-style.py` 模板
4. 交卷前跑 `verify.py`（溯源硬校验）+ `checks.py` + 核对 `06-checklists.md`，
   `export-paper.ps1` 导 PDF，`package.ps1` 打包支撑材料

## 防 AI 幻觉（v1.1 核心能力）

"代码结果依据真实数据"、"图与数据一致（3 组画 3 条）"不再靠 AI 自觉，而是由工具拦截：

1. **数据契约**：Phase 1 生成 `1_数据/data_contract.json`（字段/统计量/文件指纹）
2. **溯源校验**：`verify.py` 自动检查代码是否真的读数据、图与数据是否一致、数值有无出处
3. **绘图模板**：`plot-style.py` 强制声明 `数据来源` 与 `对象数`
4. **质量评估**：`EVALUATION.md` + `evaluation/` benchmark 判定每次改动是变好还是变坏

## 关联本地资料库

本 skill 深度引用本地资料库 `D:\全国大学生数学竞赛资料`（历年赛题、获奖论文、
电子书籍、MATLAB 代码、数据集）。`references/04` 与 `references/07` 记录了
具体到文件夹的检索索引。若资料库不在默认路径，告诉 AI 新路径即可。

## 使用建议（重要）

- **红线**：AI 不得编造数据/文献/结果；论文数值必须来自真实运行。
- **进度日志**：每阶段结束让 AI 写入 `进度日志.md`，换会话不丢进度。
- **代码 bug**：目录 7 部分 MATLAB 代码有已知 bug，skill 内置了修复版说明
  （见 `references/04-code-library.md`），请勿直接使用原 bug 版本。

## CHANGELOG

- **v1.1.0**（2026-08）：防幻觉硬约束 + 工具链。
  新增 `make-data-contract.py`（数据契约）、`verify.py`（溯源硬校验：代码-数据绑定/
  图表三方一致/数值溯源）、`export-paper.ps1` + `md2docx.py`（论文导出 PDF，
  Word COM 零 LaTeX 依赖）、`plot-style.py`（绘图模板）、
  `references/10-constraints-and-tools.md`；红线升级为"数据·代码·图表三方溯源协议"；
  新增 `EVALUATION.md` + `evaluation/`（benchmark 含 3 道反幻觉陷阱题 + 评分模板）。
- **v1.0.0**（2026-08）：首个完整版本。六阶段工作流、9 个 references、
  3 个脚本工具、双论文模板、示例演示。