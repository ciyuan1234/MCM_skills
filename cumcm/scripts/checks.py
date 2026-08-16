#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CUMCM 论文检查器 (checks.py)
用法:
    python checks.py <论文.md 或 论文.tex> [工作目录]
示例:
    python checks.py 4_论文/paper.md
    python checks.py 4_论文/paper.md .
    python checks.py 4_论文/paper.tex D:\2026_国赛1234

检查项（启发式规则，阈值可自行调整）:
  1. 结构完整性  必含章节是否齐全（问题重述/问题分析/模型假设/符号说明/模型建立/
                 模型评价/参考文献，附录建议有）
  2. 摘要检查    字数区间、关键词行(3-6个)、数值结果密度、逐问覆盖
  3. 编号连续性  图/表/公式编号是否跳号
  4. 参考文献    数量与格式抽查（含年份、出版社/期刊等要素）
  5. 提交物完整性 论文PDF、代码目录、支撑材料单个zip/rar<=20MB（官方 HARD）、
                  附录豁免声明（"本论文没有用到程序"/"本论文没有支撑材料"）
  5.5 身份泄漏    论文不得含 学校/队号/手机号/邮箱 等身份信息（官方 HARD）

退出码: 0 = 无错误; 1 = 存在错误项
"""

import os
import re
import sys

PASS = "[通过]"
WARN = "[警告]"
ERR = "[错误]"

ERROR_COUNT = 0


def report(level, msg):
    print(f"{level} {msg}")
    global ERROR_COUNT
    if level == ERR:
        ERROR_COUNT += 1


# ---------- 文本读取（兼容 UTF-8 / GBK） ----------

def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# ---------- 1. 结构完整性 ----------

REQUIRED_SECTIONS = [
    ("问题重述", "问题重述（一、…）"),
    ("问题分析", "问题分析（二、…）"),
    ("模型假设", "模型假设（三、…）"),
    ("符号说明", "符号说明（四、…）"),
    ("模型建立", "模型建立与求解（五、…）"),
    ("评价", "模型的评价、改进与推广（六、…）"),
    ("参考文献", "参考文献（七、…）"),
]
OPTIONAL_SECTIONS = [
    ("附录", "附录（代码清单，建议保留）"),
    ("模型检验", "模型检验（可内嵌在求解节，独立小节更佳）"),
    ("灵敏度", "灵敏度/稳定性分析（建议每个模型都做）"),
]


def heading_lines(text):
    """匹配 markdown (# 开头) 与 LaTeX (\\section) 标题行。"""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^#{1,6}\s", s):
            lines.append(s.lstrip("#").strip())
        elif re.match(r"^\\section", s):
            lines.append(s.replace("\\", "").strip())
        elif re.match(r"^[一二三四五六七八九十]、", s):
            lines.append(s)
    return lines


def check_structure(text):
    print("== 1. 结构完整性 ==")
    headings = "\n".join(heading_lines(text))
    for keyword, desc in REQUIRED_SECTIONS:
        if keyword in headings:
            report(PASS, f"已找到章节: {desc}")
        else:
            report(ERR, f"缺少章节: {desc}")
    for keyword, desc in OPTIONAL_SECTIONS:
        if keyword in headings:
            report(PASS, f"已找到章节: {desc}")
        else:
            report(WARN, f"建议补充: {desc}")


# ---------- 2. 摘要检查 ----------

def extract_abstract(text):
    """提取 摘要 与 关键词 之间的文本。"""
    m = re.search(r"(摘要|摘\s*要)\s*\n(.*?)(\n\s*关键词|关键词)", text, re.S)
    if not m:
        return None
    return m.group(2).strip()


def extract_keywords(text):
    m = re.search(r"关键词\s*[:：]?\s*(.+?)(\n|$)", text)
    if not m:
        return None
    return m.group(1).strip()


def check_abstract(text):
    print("== 2. 摘要检查 ==")
    abstract = extract_abstract(text)
    if not abstract:
        report(ERR, "未找到摘要正文（需在 摘要 与 关键词 之间）")
        return
    pure = re.sub(r"\s", "", abstract)
    n = len(pure)
    if n < 500 or n > 1500:
        report(ERR, f"摘要字数 {n}，超出一页摘要容量（官方 HARD: 摘要单独一页且不超一页）")
    elif n < 700 or n > 1300:
        report(WARN, f"摘要字数 {n}，获奖论文通常 700-1300 字，建议扩充或压缩")
    else:
        report(PASS, f"摘要字数 {n}，区间合理（获奖论文通常 700-1300 字）")

    kws = extract_keywords(text)
    if kws:
        kws_clean = re.sub(r"[*#_`]", "", kws)
        items = [w for w in re.split(r"[、,，;；\s]+", kws_clean) if w]
        if 3 <= len(items) <= 6:
            report(PASS, f"关键词 {len(items)} 个: {kws_clean}")
        else:
            report(WARN, f"关键词 {len(items)} 个，建议 3-6 个: {kws_clean}")
    else:
        report(ERR, "缺少关键词行（格式: 关键词: 词1 词2 …）")

    digits = re.findall(r"\d+(?:\.\d+)?", abstract)
    if len(digits) >= 8:
        report(PASS, f"摘要含 {len(digits)} 处数值，数字密度充足（评委看重量化结果）")
    else:
        report(WARN, f"摘要仅 {len(digits)} 处数值，建议每个问题的关键结果都写具体数值")

    qs = re.findall(r"问题[一二三四五六七八九十1-9]", abstract)
    if len(qs) >= 2:
        report(PASS, f"摘要逐问覆盖（出现 {len(qs)} 处'问题X'表述）")
    else:
        report(WARN, "摘要中'问题一/问题二…'的逐问覆盖不足，建议按问题分条写")

    for key in ("蒙特卡罗", "遗传", "模拟退火", "神经网络", "线性规划", "时间序列",
                "灰色", "聚类", "回归", "差分", "微分方程", "优化", "预测", "检验"):
        if key in abstract:
            report(PASS, f"摘要点明方法: {key}")
            break
    else:
        report(WARN, "摘要中未识别到明确的方法关键词（如'线性规划''时间序列'），需写明模型归类与算法")

    check_abstract_five(abstract)


# ---------- 2.5 摘要五要素检查（归类/思想/算法/特点/结果） ----------

ELEM_CLASS = re.compile(r"模型|建模|预测|优化|评价|分类|聚类|识别|规划|仿真|判别|估计|检测|判别")
ELEM_IDEA = re.compile(r"建立|构建|构造|设计|提出|采用|利用|引入|转化|分解|结合")
ELEM_ALGO = re.compile(r"蒙特卡罗|遗传|模拟退火|神经网络|线性规划|整数规划|动态规划|时间序列|灰色|聚类|回归|差分|微分方程|支持向量机|随机森林|决策树|ARIMA|GM\(|K-means|层次分析|图论|排队论|最小二乘|蚁群|粒子群|贝叶斯|马尔可夫|神经网络|SVM|LDA|PCA")
ELEM_FEAT = re.compile(r"可复现|可推广|通用|稳健|稳定|快速|高效|精确|简单|易于|适用于|收敛|优于|误差(?:小|低)|求解快|复杂度低|具有[^，。]{0,10}(?:性|能力)")


def check_abstract_five(abstract):
    print("== 2.5 摘要五要素 ==")
    ok = True
    if ELEM_CLASS.search(abstract):
        report(PASS, "①归类: 模型类型明确（含模型/题型关键词）")
    else:
        report(WARN, "①归类: 未见模型类型关键词，需说明属于哪类模型")
        ok = False
    if ELEM_IDEA.search(abstract):
        report(PASS, "②思想: 建模思路动词明确（建立/构建/采用…）")
    else:
        report(WARN, "②思想: 未识别到建模思路动词，需写清建模过程")
        ok = False
    if ELEM_ALGO.search(abstract):
        report(PASS, "③算法: 具体算法/方法明确（含算法关键词）")
    else:
        report(WARN, "③算法: 未见具体算法名，需点明算法（如'整数线性规划'）")
        ok = False
    if ELEM_FEAT.search(abstract):
        report(PASS, "④特点: 模型特点明确（可复现/稳健/高效…）")
    else:
        report(WARN, "④特点: 未见模型特点描述（如'可复现性强''求解效率高'），建议补充")
    # ⑤结果: 逐问覆盖（每个"问题X/第X问"后 100 字符内须有具体数值）
    q_matches = list(re.finditer(r"(?:问题|第)\s*[一二三四五六七八九十1-9]+\s*(?:问)?", abstract))
    if not q_matches:
        report(WARN, "⑤结果: 未识别到'问题X'表述，无法逐问核对（建议按问题分条给出数值结果）")
        return
    no_val = []
    for m in q_matches:
        after = abstract[m.end():m.end() + 100]
        if not re.search(r"\d+(?:\.\d+)?", after):
            no_val.append(m.group(0))
    if no_val:
        report(WARN, f"⑤结果: {len(no_val)} 处问题表述后 100 字内无具体数值: {no_val[:3]}（每个问题都应有量化结果）")
    else:
        report(PASS, f"⑤结果: {len(q_matches)} 处问题表述均带具体数值（逐问覆盖）")


# ---------- 3. 编号连续性 ----------

def check_numbering_from_list(text, label, nums_raw):
    print(f"== 3. 编号连续性: {label} ==")
    nums = [int(m) for m in nums_raw]
    if not nums:
        report(WARN, f"未发现 {label} 编号")
        return
    uniq = sorted(set(nums))
    full = list(range(1, max(uniq) + 1))
    missing = [i for i in full if i not in uniq]
    if missing:
        report(ERR, f"{label} 编号跳号，缺少: {missing}")
    else:
        report(PASS, f"{label} 编号连续 1-{max(uniq)}（共 {len(nums)} 处编号）")


def check_numbering(text, label, pattern, mode="md"):
    print(f"== 3. 编号连续性: {label} ==")
    # 编号检查只扫描正文（参考文献/附录中的数字与公式无关，先截断）
    body = re.split(r"参考文献", text)[0]
    nums = [int(m) for m in re.findall(pattern, body, re.MULTILINE)]
    if not nums:
        report(WARN, f"未发现 {label} 编号")
        return
    uniq = sorted(set(nums))
    full = list(range(1, max(uniq) + 1))
    missing = [i for i in full if i not in uniq]
    if missing:
        report(ERR, f"{label} 编号跳号，缺少: {missing}")
    else:
        report(PASS, f"{label} 编号连续 1-{max(uniq)}（共 {len(nums)} 处引用/题注）")


# ---------- 3.5 图表题注（获奖论文惯例: 图题注在图下、表题注在表上） ----------

def check_fig_captions(text):
    print("== 3.5 图表题注 ==")
    body = re.split(r"参考文献", text)[0]
    tags = []
    bad_alt = []
    for m in re.finditer(r"!\[([^\]]*)\]\([^)]+\)", body):
        alt = m.group(1).strip()
        num = re.match(r"^图\s*(\d+)", alt)
        if num:
            tags.append(int(num.group(1)))
        else:
            bad_alt.append(alt[:20] or "(空题注)")
    refs = [int(m) for m in re.findall(r"图\s*(\d+)", body)]
    if not tags:
        if refs:
            report(ERR, f"正文出现 {len(refs)} 处'图N'引用但无任何 ![图N …](图片) 标签（引用必须配插图，否则 PDF 无图）")
        else:
            report(WARN, "正文未发现图片引用与图片标签")
        return
    max_tag = max(tags)
    unref = [n for n in range(1, max_tag + 1) if n not in tags]
    if unref:
        report(ERR, f"图片标签编号不连续，缺少: {unref}")
    else:
        report(PASS, f"图片标签编号连续 1-{max_tag}（共 {len(tags)} 张图）")
    if bad_alt:
        report(WARN, f"{len(bad_alt)} 个图片标签题注未以'图N'开头（题注应写在 alt 中，如 ![图1 xxx](fig.png)）: {bad_alt[:2]}")
    else:
        report(PASS, "所有图片标签均以'图N'开头（docx 导出时自动生成图下题注）")
    if refs:
        missing = [n for n in set(refs) if n > max_tag]
        if missing:
            report(ERR, f"正文引用了未插图的编号: 图{missing}（有引用无图）")
        else:
            report(PASS, "正文'图N'引用均有对应图片标签")
    order = sorted(range(len(tags)), key=lambda i: tags[i])
    if order != list(range(len(tags))):
        report(WARN, "图片标签出现顺序与编号不一致（docx 按出现顺序排版，建议图N 按编号顺序摆放）")
    else:
        report(PASS, "图片标签按编号顺序出现")


def check_table_captions(text):
    body = re.split(r"参考文献", text)[0]
    lines = body.splitlines()
    tbl_heads = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1].strip()):
            tbl_heads.append(i)
    if not tbl_heads:
        report(WARN, "未发现 markdown 表格")
        return
    missing = []
    for i in tbl_heads:
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        # 符号说明节的表格惯例不编号，豁免
        sec = "\n".join(lines[max(0, i - 15):i])
        if re.search(r"(?m)^#{1,6}\s*[四4]、\s*符号说明|^#{1,6}\s*符号说明", sec):
            continue
        if j < 0 or not re.match(r"^表\s*\d+", lines[j].strip()):
            missing.append(tbl_heads.index(i) + 1)
    if missing:
        report(WARN, f"{len(missing)} 张表格缺少'表N …'题注行（题注须在表格正上方）: 表序 {missing[:4]}")
    else:
        report(PASS, f"{len(tbl_heads)} 张表格均有'表N'题注行（表上）")


# ---------- 3.6 正文引用标注与附录代码（官方 HARD） ----------

def check_citations_appendix(text, workdir):
    print("== 3.6 正文引用标注与附录代码 ==")
    head = re.split(r"参考文献", text)[0]
    cites = [int(m) for m in re.findall(r"\[(\d+)\]", head)]
    m = re.search(r"参考文献(.*?)(附录|$)", text, re.S)
    refs_n = 0
    if m:
        refs_n = len([ln for ln in m.group(1).splitlines()
                      if ln.strip() and re.match(r"^[\[(（]?\d", ln.strip())])
    if not cites:
        report(ERR, "正文没有任何 [x] 引用标注（官方 HARD: 参考文献须在正文引用处标注 [x]）")
    elif refs_n == 0:
        report(WARN, "未解析到参考文献条目数，跳过覆盖率检查")
    else:
        covered = len(set(c for c in cites if c <= refs_n))
        ratio = covered / refs_n
        if ratio >= 0.5:
            report(PASS, f"正文引用覆盖 {covered}/{refs_n} 条文献 ({ratio:.0%} >= 50%)")
        else:
            report(ERR, f"正文引用仅覆盖 {covered}/{refs_n} 条文献 ({ratio:.0%} < 50%)，官方要求引用处标 [x]")

    app = re.search(r"(附录|附\s*录)(.*)$", text, re.S)
    if not app:
        report(WARN, "未找到附录章节（建议附录附文件列表与完整可运行代码）")
        return
    content = app.group(2)
    if re.search(r"本论文没有用到程序|没有用到程序", content):
        report(PASS, "附录已声明'本论文没有用到程序'（官方豁免条款）")
        return
    has_code = bool(re.search(r"```|\\begin\{lstlisting\}|\\begin\{verbatim\}", content))
    has_list = bool(re.search(r"\.(py|m|r)\b|支撑材料文件列表|文件列表|支撑材料清单", content, re.I))
    if has_code and has_list:
        report(PASS, "附录同时含 文件列表 与 完整代码块（官方 HARD: 文件列表+全部可运行源代码）")
    elif has_code:
        report(WARN, "附录含代码块但缺'支撑材料文件列表'（官方 HARD 要求附录含文件列表，建议补充清单）")
    elif has_list:
        report(ERR, "附录仅有代码文件清单而无完整代码（官方 HARD: 附录必须含完整可运行源代码，请粘贴代码块）")
    else:
        report(ERR, "附录既无代码块也无文件列表（官方 HARD: 附录必须含完整可运行源代码）")

# ---------- 4. 参考文献 ----------

def check_references(text):
    print("== 4. 参考文献 ==")
    m = re.search(r"参考文献(.*?)(附录|$)", text, re.S)
    if not m:
        report(ERR, "未找到参考文献章节")
        return
    body = m.group(1)
    entries = [ln for ln in body.splitlines() if ln.strip() and re.match(r"^[\[(（]?\d", ln.strip())]
    if not entries:
        entries = [ln for ln in body.splitlines() if ln.strip() and re.search(r"20\d\d|19\d\d", ln)]
    if not entries:
        report(WARN, "参考文献章节存在但未解析到条目（每行以 [1] 或序号开头）")
        return
    n = len(entries)
    if n < 4:
        report(ERR, f"参考文献仅 {n} 条，建议 5-10 条")
    elif n > 20:
        report(WARN, f"参考文献 {n} 条，偏多，控制在 5-10 条较稳妥")
    else:
        report(PASS, f"参考文献 {n} 条")

    bad = []
    for ln in entries:
        if not re.search(r"(19|20)\d\d", ln):
            bad.append(ln[:30])
        elif not re.search(r"(出版社|出版|学报|杂志|期刊|页|期|:|://|edu\.|org\.|com\.)", ln):
            bad.append(ln[:30])
    if bad:
        report(WARN, f"{len(bad)} 条文献疑似缺年份/出版要素（示例: {bad[0]}…）")
    else:
        report(PASS, "文献条目均含年份与出版要素")


# ---------- 5. 提交物完整性 ----------

def check_submission(workdir, text):
    print("== 5. 提交物完整性 ==")
    if not workdir or not os.path.isdir(workdir):
        report(WARN, "未提供工作目录，跳过提交物检查（用法: python checks.py 论文.md <工作目录>）")
        return
    paper_dir = os.path.join(workdir, "4_论文")
    pdfs = [f for f in os.listdir(paper_dir) if f.lower().endswith(".pdf")] if os.path.isdir(paper_dir) else []
    if pdfs:
        report(PASS, f"论文 PDF 已生成: {pdfs[0]}")
    else:
        report(ERR, "4_论文 下没有 PDF（最终必须提交 PDF 版论文）")

    code_dir = os.path.join(workdir, "2_代码")
    if os.path.isdir(code_dir) and os.listdir(code_dir):
        report(PASS, "2_代码 目录非空（代码已就位）")
    else:
        report(ERR, "2_代码 目录为空（支撑材料需附全部代码）")

    # 支撑材料: 必须打包为单个 zip/rar <= 20MB（官方 HARD）
    sup_zip = [f for f in os.listdir(workdir) if f.lower().endswith((".zip", ".rar")) and not f.startswith("~")]
    if not sup_zip:
        if re.search(r"本论文没有支撑材料|没有支撑材料", text):
            report(PASS, "未发现支撑材料包，但附录已声明'本论文没有支撑材料'（官方豁免条款）")
        else:
            report(ERR, "工作区根目录没有 支撑材料.zip/.rar（官方 HARD: 支撑材料压缩为单个 RAR/ZIP 文件）")
    else:
        if len(sup_zip) > 1:
            report(WARN, f"存在 {len(sup_zip)} 个压缩包，最终应只提交一个: {sup_zip}")
        pkg = sup_zip[0]
        pkg_path = os.path.join(workdir, pkg)
        size_mb = os.path.getsize(pkg_path) / 1048576.0
        if size_mb > 20:
            report(ERR, f"支撑材料 {pkg} {size_mb:.1f}MB > 20MB（官方 HARD）")
        else:
            report(PASS, f"支撑材料 {pkg} {size_mb:.1f}MB <= 20MB")
        if re.search(r"承诺书|编号专用页", pkg):
            report(ERR, "支撑材料文件名含'承诺书/编号专用页'（官方 HARD: 不得放入支撑材料）")
        if pkg.lower().endswith(".zip"):
            try:
                import zipfile
                with zipfile.ZipFile(pkg_path) as zf:
                    bad = [n for n in zf.namelist() if re.search(r"承诺书|编号专用页", n)]
                if bad:
                    report(ERR, f"压缩包内文件含承诺书/编号专用页: {bad[:2]}（官方 HARD）")
                else:
                    report(PASS, "压缩包内文件名无承诺书/编号专用页")
            except Exception as e:
                report(WARN, f"无法读取压缩包内容: {e}")

    sup_dir = os.path.join(workdir, "5_支撑材料")
    if os.path.isdir(sup_dir) and os.listdir(sup_dir) and not sup_zip:
        report(WARN, "5_支撑材料 目录非空但未打包为 zip/rar（提交前运行 package.ps1 打包）")
    elif os.path.isdir(sup_dir) and os.listdir(sup_dir):
        report(PASS, "5_支撑材料 目录非空（已打包）")
    else:
        report(WARN, "5_支撑材料 目录为空（若生成了额外数据/说明文档请放入，否则在附录声明'本论文没有支撑材料'）")


# ---------- 5.5 身份泄漏扫描（官方 HARD: 摘要页/正文/附录不得含身份信息） ----------

IDENTITY_PATTERNS = [
    (re.compile(r"[\u4e00-\u9fa5]{2,3}(?:省|市|自治区)[\u4e00-\u9fa5]{0,8}(?:大学|学院)(?:[\u4e00-\u9fa5]{0,6}(?:分校|校区))?"),
     "学校/院校名称（省市+校名）"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "手机号码"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "电子邮箱"),
    (re.compile(r"(?:队号|参赛队编号|队伍编号)\s*[:：]?\s*[A-Z]?\d{4,}"), "参赛队号"),
    (re.compile(r"(?<!\d)20\d{2}[A-Z]\s*\d{3,4}(?!\d)"), "队号（年份+题号+序号）"),
    (re.compile(r"(?:队员|参赛队员|姓名)\s*[:：]\s*[\u4e00-\u9fa5]{2,4}(?:[、，,]\s*[\u4e00-\u9fa5]{2,4}){0,2}"),
     "队员姓名列表"),
]


def check_identity(text):
    print("== 5.5 身份泄漏扫描 ==")
    hits = []
    for pat, desc in IDENTITY_PATTERNS:
        for m in pat.finditer(text):
            snippet = text[max(0, m.start() - 10):m.end() + 10].replace("\n", " ")
            hits.append(f"{desc}: …{snippet}…")
            break
    if hits:
        report(ERR, f"论文含参赛者身份信息（官方 HARD）: {hits}")
    else:
        report(PASS, "未检测到学校/队号/手机号/邮箱等身份信息")


# ---------- 5.6 篇幅/密度检查（获奖论文基准: 正文25-35页/公式42-77/图30+表11+） ----------

def check_innovation(text):
    print("== 5.7 创新点声明 ==")
    if "创新点" in text or "创新" in text:
        report(PASS, "论文含创新点相关表述")
    else:
        report(WARN, "论文无'创新点'表述——按 03-model-catalog.md §5.1 四步走补写（特异性3问→第二梯队方法→组合创新→自检；手法参照 evaluation/award-paper-experience.md §2 手法库）")
    if re.search(r"创新点定位|特异性|差异化", text):
        report(PASS, "含'创新点定位/特异性/差异化'小节或表述")
    else:
        report(WARN, "问题分析缺少'创新点定位'（每问 1-2 句: 本题特异性 + 差异化建模，模板 §2.6）")
    n_algorithm = len(re.findall(r"(鲁棒|随机规划|CVaR|Copula|NSGA|启发式|熵权|TOPSIS|灰关联|秩和比|状态空间|Kalman|变点|灵敏度|对比)", text))
    if n_algorithm >= 3:
        report(PASS, f"差异化方法/检验关键词出现 {n_algorithm} 处（鲁棒/熵权/启发式/对比等）")
    else:
        report(WARN, f"差异化方法/检验关键词仅 {n_algorithm} 处——建议引入第二梯队方法或双算法互验（参考 03-model-catalog.md §5.3 差异性自检，需≥2 处差异化维度）")


def check_density(text):
    print("== 5.6 篇幅/密度 ==")
    body = re.split(r"参考文献", text)[0]
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    formulas = re.findall(r"\\tag\{(\d+)\}|\((\d+)\)\s*$", body, re.MULTILINE)
    n_formula = len([g for g in formulas if any(g)])
    figs = len(re.findall(r"图\s*\d+", body))
    tbls = len(re.findall(r"表\s*\d+", body))
    if n_formula < 10:
        report(WARN, f"正文公式编号仅 {n_formula} 处（获奖论文 42-77 处，建议每个模型给出完整推导）")
    else:
        report(PASS, f"正文公式编号 {n_formula} 处（获奖论文 42-77 处）")
    n_chart = figs + tbls
    if n_chart < 8:
        report(WARN, f"正文图+表共 {n_chart} 个（图{figs}+表{tbls}，获奖论文 图30+表11+，建议每个结论配图/表）")
    else:
        report(PASS, f"正文图+表共 {n_chart} 个（图{figs} 表{tbls}）")
    if n_formula >= 10 and n_chart >= 8:
        report(PASS, "篇幅密度达标（正文页数由 format-check 的 PDF 层检查）")


# ---------- 主流程 ----------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    paper = sys.argv[1]
    workdir = sys.argv[2] if len(sys.argv) > 2 else ""
    if not os.path.isfile(paper):
        print(f"{ERR} 找不到论文文件: {paper}", file=sys.stderr)
        sys.exit(2)

    text = read_text(paper)
    check_structure(text)
    check_abstract(text)
    check_numbering(text, "图", r"图\s*(\d+)")
    check_numbering(text, "表", r"表\s*(\d+)")
    check_fig_captions(text)
    check_table_captions(text)
    # 公式编号: 优先识别 LaTeX/Markdown 的 \tag{N}；否则回退到"行内 $$...$$ 行尾 (N)"
    tags = re.findall(r"\\tag\{(\d+)\}", text)
    if tags:
        check_numbering_from_list(text, "公式", tags)
    else:
        check_numbering(text, "公式", r"^[^$\n]*\((\d+)\)\s*$")
    check_references(text)
    check_citations_appendix(text, workdir)
    check_identity(text)
    check_density(text)
    check_innovation(text)
    check_submission(workdir, text)

    print()
    if ERROR_COUNT:
        print(f"检查完成: {ERROR_COUNT} 项错误，请修复后再提交。")
        sys.exit(1)
    print("检查完成: 无错误。建议仍以人工逐条核对 06-checklists.md。")
    sys.exit(0)


if __name__ == "__main__":
    main()
