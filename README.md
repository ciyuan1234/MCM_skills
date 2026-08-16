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

本 skill 深度引用本地资料库 `D:\全国大学生数学建模竞赛资料`（历年赛题、获奖论文、
电子书籍、MATLAB 代码、数据集）。`references/04` 与 `references/07` 记录了
具体到文件夹的检索索引。若资料库不在默认路径，告诉 AI 新路径即可。

**双模式（资料库缺失自动降级）**：
- 资料库存在 → 正常模式：直接复用现成代码与数据集
- 资料库被删除 → **自包含模式**：AI 用自身知识从零写代码（`04` 已内置 18 个核心算法
  的从零实现要点表）、用 `07` 的网站清单联网取数据；工作流/防幻觉检查完全不受影响

## 使用建议（重要）

- **红线**：AI 不得编造数据/文献/结果；论文数值必须来自真实运行。
- **进度日志**：每阶段结束让 AI 写入 `进度日志.md`，换会话不丢进度。
- **代码 bug**：目录 7 部分 MATLAB 代码有已知 bug，skill 内置了修复版说明
  （见 `references/04-code-library.md`），请勿直接使用原 bug 版本。

## CHANGELOG

- **v1.4.0**（2026-08-16）：**篇幅与创新性迭代 + LaTeX 编译路线**。① 安装 MiKTeX 并新增 `md2tex.py`（md→tex 转换器），`export-paper.ps1` 优先走 xelatex 编译（公式/表格/中文排版最佳），无 xelatex 时回退 Word 路线；② 正文页数**硬标准 ≥20 页**（format-check：<20 ERR / 20-25 PASS / 26-30 WARN / >30 ERR，依据 `evaluation/award-paper-baseline.md` 获奖论文基准 25-35 页）；③ 篇幅密度检查（公式编号 ≥10、图+表 ≥8）；④ 创新性引导：`03-model-catalog.md` §5.1 四步走（问题特异性 3 问 → 第二梯队方法库 → 组合创新三模式 → 三问自检），SKILL 强制"创新点定位"小节，`checks.py` 5.7 创新点软检查；⑤ 四工作区论文全部扩写至正文 20-25 页（16-21 表、12-14 编号公式），数值溯源 100%（368-582 个数值全可溯源）；⑥ 修复 2021C sensitivity.py 候选集 bug（Q2 31 家/Q3、Q4 全 402 家）与结果文件覆盖 bug；⑦ `make-requirements.py` 支持"附件X"（无扩展名）模式与模糊模板定位。
- **v1.3.0**（2026-08）：**格式硬检查体系**。新增 `format-check.py`（docx 版面级检查：页边距 ≥2.5cm/页脚 PAGE 页码/首页摘要页/图题注/三线表/表题注/PDF ≤20MB）；`checks.py` 升级（摘要 700-1300 字档位、图片标签必须配插图、表题注须在表上、正文 [x] 引用覆盖 ≥50% 文献、附录须含代码块）；`md2docx.py` 升级（页边距 2.5cm、页脚居中页码、三线表、题注小一号、图片路径多基准解析、UTF-8 BOM 兼容）；`verify.py` 剔除代码块防标识符误报；`blind-rubric.md` 格式硬伤一票否决（写作质量上限 3/2 分）；`auto-score.py` 增加版面合规分（10 分）与 format 硬闸门；负样本验证 5 类硬伤全部被抓；2021C/2022C/2023C/Tier1 四工作区整改后全 0/0/0 通过（基线重评 97.1）。
- **v1.2.5**（2026-08）：工具链收尾。`make-data-contract.py` 支持多 sheet xlsx（每个工作表独立统计 + 顶层合并，verify.py 向后兼容）；run-tier2 题目命名匹配扩展（`CUMCM2021-C.pdf` 等）；install.ps1 三工具安装验证通过。
- **v1.2.4**（2026-08）：2021C 第三类题型（综合评价+LP优化）盲测通过；附件A/B 按官方模板填写脚本。
- **v1.2.3**（2026-08）：评测体系升级——质量 35 扩容 + WARN 扣分 + 90 分制归一化 100；盲评闭环（blind-scores.md）；Tier1 夹具强化（基线 76.4→89.5）。
- **v1.1.0**（2026-08）：防幻觉硬约束 + 工具链。
  新增 `make-data-contract.py`（数据契约）、`verify.py`（溯源硬校验：代码-数据绑定/
  图表三方一致/数值溯源）、`export-paper.ps1` + `md2docx.py`（论文导出 PDF，
  Word COM 零 LaTeX 依赖）、`plot-style.py`（绘图模板）、
  `references/10-constraints-and-tools.md`；红线升级为"数据·代码·图表三方溯源协议"；
  新增 `EVALUATION.md` + `evaluation/`（benchmark 含 3 道反幻觉陷阱题 + 评分模板）。
- **v1.0.0**（2026-08）：首个完整版本。六阶段工作流、9 个 references、
  3 个脚本工具、双论文模板、示例演示。