#!/usr/bin/env python3
"""检查 sdd-plan 计划的格式和可直接判断的内容。

方案确认（A）：主 Agent 完成第 1–2 节、运行 lint（格式和部分规则校验），
并完成所需独立核查后，请用户决定是否接受方案。用户同意后，主 Agent 才写第 3–6 节。
开工确认（B）：主 Agent 完成整份计划并记录实际核查范围，请用户决定是否进入实现。
首轮未改正文时，主 Agent 沿用首次 lint 结果；修改后的核查通过时，主 Agent 才运行最终 lint。
到达核查上限或最终 lint 失败时，主 Agent 停止。用户明确允许后，Agent 才能进入实现。
审阅只覆盖明确列出的范围，lint 通过不保证语义正确，也不代替用户批准。
Agent 使用字段列表填写计划，并用四级标题分隔记录。

用法：
    python3 .agents/skills/sdd-plan/tools/plan_lint.py <spec 目录>

校验项：

    L01  头部两项齐全、无版本控制字段；Spec 可解析且与目录名一致；spec 版本与状态对得上 plan 的声明
    L02  第 1–6 节结构；Status=draft 时第 3–6 节必须为空（方案尚未确认）
    L03  方案摘要非空、不超过 30 行、有「需要用户决定的事项」或「无需用户决定」
    L04  第 2 节两组记录：2.1 需要用户确认的例外（三字段、去向合法、覆盖写明条款、理由及可判断的回归条件）、2.2 Agent 遵循的既有规范（每条有真实出处；
         引用了 2.1 覆盖过的条款时必须限定只沿用哪一部分）
    L05  任务：编号连续、四行齐全、验证可执行；依赖只指前面的任务；改动不越 3.3 清单
    L06  覆盖：spec 每条 R 恰好一次，且指向真实任务，与任务的「覆盖」互洽
    L07  全文没有 TBD / 待定 / 稍后 / 视情况 这类空洞词
    L08  阻断态只能 draft；design-ok / approved 时第 3–6 节及设计子节完整，
         显式决策记录字段完整，允许仅引用 2.1 而无新增取舍；风险记录与对证记录存在；不判语义通过
    L09  spec 第 7 节还有待决项时，plan 不得存在
    L10  人读区：第 1 节有「用户会看到的变化」、无裸维度 ID、拍板项是问句或指向 2.1；
         2.1 的「为什么」一句话、不超字数
    L11  可见面：第 1 节「覆盖核对」记录覆盖 spec 每条 R，落点引文能在「用户会看到的变化」里逐字找到

只检查格式和能直接判断的内容。方案与任务语义需在明确范围内独立审阅，不保证穷尽。
退出码：0 全过 / 1 有 FAIL / 2 用法错误或文件缺失。

脚本随本 skill 分发，纯标准库、Python 3.8+，不依赖被审项目的语言、框架或构建系统。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# ─── 规则常量 ────────────────────────────────────────────────────────────────
#
# 这些是本 skill 自己的规则，与 ../SKILL.md、../rules/dimensions.md 逐字对应，
# 改一处必须同步另一处。

# plan 的状态机：draft（摘要待确认）→ design-ok（摘要已确认）→ approved（可实现）→ stale（spec 变了）
PLAN_STATUS = ('draft', 'design-ok', 'approved', 'stale')

# 头部必须有的两项。故意不含 commit SHA / tag：提交前拿不到 SHA，填它会造成"改文档→再提交"的死循环。
HEAD_FIELDS = ('Spec', 'Status')

# 头部禁止出现的字段：个人项目不依赖版本控制，SHA 只会过期。
FORBIDDEN_HEAD = ('基线', 'Commit', 'commit', 'SHA', 'sha', 'Tag', 'tag')

# 第 1 节正文行数上限（不含空行与注释）。
SUMMARY_MAX_LINES = 30

# 任务块的四行，缺一行就 FAIL。
TASK_FIELDS = ('改动', '验证', '覆盖', '依赖')

# 约束的去向。`覆盖` 是正常做法，但须在 2.1 写明被覆盖条款、理由和可判断的回归条件。
# 后两个是阻断态：出现时这份 plan 不能进 approved。
# 这些去向只用于 2.1 的待确认事项；2.2 每行都按 `既有` 处理。
ALLOWED_TARGETS = ('既有', '覆盖', '回 spec', '先补约定', '仅本次')
BLOCKING_TARGETS = ('回 spec', '先补约定')

# 空洞词：出现即视为没写完。
VAGUE_WORDS = ('TBD', 'TODO', '待定', '稍后', '视情况', '酌情')

# 第 2.1 节「为什么」一格的字符上限：一句一事，写不下说明它其实是两条约束。
WHY_MAX_CHARS = 40

# 「什么时候回到标准」里不算可判断的说法。
VAGUE_DECAY = ('', '—', '-', '暂不', '永不', '长期', '以后再说', '看情况')

# 条款 ID：例如 REPORT-01 表示报告规范的第 1 条，FORM-02 表示表单规范的第 2 条。
# 2.1 覆盖了某条款的一部分时，2.2 必须说明只沿用哪一部分，不能再整体引用。
_CLAUSE_PREFIX = r'[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*'
_CLAUSE_ID = re.compile(r'(?<![A-Za-z0-9_-])(?:%s)-\d+(?![A-Za-z0-9_-])' % _CLAUSE_PREFIX)

# `RULE-02–RULE-05` 这种区间引用会把中间的条款藏起来，展开后再比对。
_CLAUSE_RANGE = re.compile(
    r'(?<![A-Za-z0-9_-])(%s)-(\d+)\s*[–—~-]\s*(?:(%s)-)?(\d+)(?![A-Za-z0-9_-])'
    % (_CLAUSE_PREFIX, _CLAUSE_PREFIX)
)

# 2.2 引用被覆盖条款时表示"只沿用其中一部分"的词。写了它，读者才看得出边界在哪。
QUALIFIERS = ('仅', '只', '其余', '以外', '之外')

# 「除」不能按单字匹配：「不排除手写源码」「删除临时文件」里都有它，
# 会把没限定的写法判成合法。要求成对出现。
QUALIFIER_PATTERNS = (re.compile(r'除[^。；]{0,24}(?:外|之外)'),)

# 「需要用户决定的事项」下的每一项，要么是问句，要么指向 2.1。
# 写成「确认……。」的结论句时，用户只有"同意"一个动作，闸门退化成确认框。
PITCH_POINTER = '见 2.1'

# 第 1 节末尾的「覆盖核对」记录：spec 每条 R 落到「用户会看到的变化」的哪一句。
# 它和第 5 节的 `R → 验证` 同构：一个核"怎么做得到"，一个核"人看不看得见"。
# 只核存在性与引文可查；引文和 R 说的是不是一回事，脚本判不了。
_SEEN_HEAD = '覆盖核对'
_SEEN_TABLE = re.compile(r'\*\*%s\*\*[^\n]*\n(?:[ \t]*\n)*((?:[ \t]*\|[^\n]*\n)+)' % _SEEN_HEAD)
# 模板使用首个名称；解析器接受本组列出的节标题。
_VISIBLE_HEADS = ('用户会看到的变化', '你会看到什么')
_PITCH_HEADS = ('需要用户决定的事项', '需要你拍板')
_NO_PITCH_HEADS = ('无需用户决定', '无需你拍板')

# 可见变化在下一个独立粗体小标题或 Markdown 标题处结束。
# 不依赖标题名称，避免「实现方式」「代价」等措辞变化把实现说明算作可见结果。
# 列表项之间允许空行和项内折行；列表中的粗体强调不算小标题。
_VISIBLE_PARA = re.compile(
    r'\*\*(?:%s)\*\*[ \t]*[：:]?[ \t]*(.*?)(?=\n(?:\*\*[^*\n]+\*\*|#{1,6}[ \t]+)|\Z)'
    % '|'.join(_VISIBLE_HEADS),
    re.DOTALL,
)

# 落点引文：太短指不到具体画面，太长说明它是整段复述，人读核对表反而更累。
SEEN_QUOTE_MIN = 6
SEEN_QUOTE_MAX = 20

# 标「无」的落点必须给出可核对的指向（「无 —— 见「代价」段」），否则等同于没写。
NO_SEEN_MARK = '无'


def clause_ids(text: str) -> List[str]:
    """取出条款 ID，区间展开成逐条。

    `RULE-02–RULE-05` 里没有 `RULE-03` 这个完整编号，但语义上包含它。
    不展开的话，把被覆盖的条款夹在区间中间就能绕过交叉核对。
    """
    out: List[str] = []
    def expand_range(match: re.Match) -> str:
        prefix, start, end_prefix, end = match.groups()
        if end_prefix is not None and end_prefix != prefix:
            return match.group(0)
        low, high = sorted((int(start), int(end)))
        width = min(len(start), len(end))
        out.extend('%s-%s' % (prefix, str(number).zfill(width)) for number in range(low, high + 1))
        return ' '

    remaining = _CLAUSE_RANGE.sub(expand_range, text)
    out.extend(_CLAUSE_ID.findall(remaining))
    return list(dict.fromkeys(out))

TOTAL_RULES = 11

SPEC_ID_SHAPE = r'p\d{2}-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*'
_HEAD_SPEC = re.compile(
    r'^(%s)\s*[（(]\s*spec\s*v(\d+)\s*/\s*([a-z]+)\s*[）)]$' % SPEC_ID_SHAPE
)
_SECTION = re.compile(r'^## (\d)\. .*$', re.MULTILINE)
_SUBSECTION = re.compile(r'^### (\d\.\d) .*$', re.MULTILINE)
_TASK_MARK = re.compile(r'^-\s*\[[ xX]\]\s*\*\*T(\d+)\*\*', re.MULTILINE)
_SPEC_R = re.compile(r'^\s*-\s*\[[ xX]\]\s*\*\*R(\d+)\*\*', re.MULTILINE)
_R_REF = re.compile(r'R(\d+)')
_T_REF = re.compile(r'T(\d+)')
_MD_PATH = re.compile(r'[A-Za-z0-9_./-]+\.md')

# 路径契约与语言、目录无关：改动及 3.3 首列用反引号逐个标注仓库相对路径。
_CHANGE_PATH = re.compile(r'`([^`\n]+)`')


def valid_change_path(path: str) -> bool:
    """拒绝绝对路径、越界、通配与非规范分隔符，保留空格、Unicode 和点文件。"""
    return bool(path) and not (
        path.startswith('/') or '\\' in path or ':' in path
        or any(char in path for char in '*?<>|')
        or any(part in ('', '.', '..') for part in path.split('/'))
    )
_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
_SEP_CELL = re.compile(r'^:?-{2,}:?$')
# Markdown 链接的尖括号目标：`[文本](<../../docs/x.md>)`。
# 判占位符前要先摘掉，否则一行链接会被当成模板里的 `<约束原文>`，整行跳过校验。
_LINK_DEST = re.compile(r'\]\(<[^>]*>\)')
_ROW2 = re.compile(r'^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$')


# ─── 解析 ────────────────────────────────────────────────────────────────────


def clean_cell(raw: str) -> str:
    """单元格取值：去空白与反引号，让模板的 `既有` 和手写的 既有 等价。"""
    return raw.replace('`', '').strip()


def key_value_rows(text: str) -> Dict[str, str]:
    """收集只有两格的表格行。"""
    out: Dict[str, str] = {}
    for line in text.split('\n'):
        match = _ROW2.match(line)
        if not match:
            continue
        key = clean_cell(match.group(1))
        if not key.replace('-', ''):
            continue
        out[key] = clean_cell(match.group(2))
    return out


def header_fields(text: str, rep=None) -> Dict[str, str]:
    """读取计划头部字段。"""
    cut = text.find('\n## 1.')
    text = _COMMENT.sub('', text if cut < 0 else text[:cut])
    out = key_value_rows(text)
    seen = set()
    for line in text.splitlines():
        match = _ROW2.match(line)
        field = re.match(r'^-\s+([^：:]+)[：:]\s*(.*)$', line)
        if field:
            key, value = clean_cell(field[1]), clean_cell(field[2])
        elif match:
            key, value = clean_cell(match[1]), clean_cell(match[2])
            if key not in HEAD_FIELDS + FORBIDDEN_HEAD:
                continue
        else:
            continue
        if key in seen and rep is not None:
            rep.fail('L01', '头部字段「%s」重复' % key)
        seen.add(key)
        out[key] = value
    return out


def split_sections(text: str) -> Dict[int, str]:
    """按 `## <n>. ` 切出各节。"""
    out: Dict[int, str] = {}
    marks = list(_SECTION.finditer(text))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        out[int(mark.group(1))] = text[mark.end():end]
    return out


def split_subsections(section: str) -> Dict[str, str]:
    """按 `### 3.2 ` 切出子节，用于单独看决策表。"""
    out: Dict[str, str] = {}
    marks = list(_SUBSECTION.finditer(section))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        out[mark.group(1)] = section[mark.end():end]
    return out


def body_lines(section: str) -> List[str]:
    """去掉注释与空行后的有效行。"""
    return [line for line in _COMMENT.sub('', section).split('\n') if line.strip()]


def substantive_lines(section: str) -> List[str]:
    """只留"真的写了内容"的行：排除标题、表格分隔行、表头行与纯占位行。

    模板原样复制过来应当能过自己的闸门；draft 阶段真正要拦的是"已经写了设计与任务"，
    而不是"还留着 `### 3.1` 与 `| 文件 | 新建/修改 | 职责 |` 这类骨架"。
    """
    lines = body_lines(section)
    kept: List[str] = []
    for index, line in enumerate(lines):
        text = line.strip()
        if text.startswith('#'):
            continue
        if re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', text):
            continue  # 分隔线不是内容
        if re.fullmatch(r'\|[\s:|-]+\|', text):
            continue  # 表格分隔行
        if '<' in text and '>' in text:
            continue  # 模板占位，没填
        if text.startswith('|'):
            following = lines[index + 1].strip() if index + 1 < len(lines) else ''
            if re.fullmatch(r'\|[\s:|-]+\|', following):
                continue  # 表头行，下一行是分隔行
        kept.append(line)
    return kept


def grid_rows(section: str) -> List[List[str]]:
    """解析表格式多条目的表格，返回数据行（去掉表头与分隔行）。"""
    rows: List[List[str]] = []
    for line in _COMMENT.sub('', section).split('\n'):
        stripped = line.strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            continue
        cells = [cell.strip() for cell in stripped.strip('|').split('|')]
        if all(_SEP_CELL.match(cell) for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else rows


def record_rows(section: str, fields: Tuple[str, ...], rep=None, code='L04') -> List[List[str]]:
    """把记录直接解析为有序值，不序列化为表格；管道和反引号均保留。"""
    section = _COMMENT.sub('', section)
    marks = list(re.finditer(r'^####[ \t]+([^\n]+)', section, re.MULTILINE))
    if not marks:
        if re.search(r'^-\s+(?:%s)[：:]' % '|'.join(map(re.escape, fields)), section, re.MULTILINE):
            if rep is not None:
                rep.fail(code, '字段记录缺少「#### 标题」')
            return []
        return grid_rows(section)
    if re.search(r'^-\s+[^：:\n]+[：:]', section[:marks[0].start()], re.MULTILINE) and rep is not None:
        rep.fail(code, '首条字段记录缺少「#### 标题」')
    if '|' in section[:marks[0].start()]:
        if grid_rows(section[:marks[0].start()]) and rep is not None:
            rep.fail(code, '同一区域不要混用表格和字段记录')
    rows: List[List[str]] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        values: Dict[str, str] = {}
        current = None
        for line in section[mark.end():end].splitlines():
            if line.startswith('**'):
                break
            match = re.match(r'^-\s+([^：:]+)[：:][ \t]*(.*)$', line)
            if match:
                key, value = match.groups()
                if key not in fields:
                    if rep is not None:
                        rep.fail(code, '记录「%s」有未知字段「%s」' % (mark[1], key))
                    current = None
                    continue
                if key in values and rep is not None:
                    rep.fail(code, '记录「%s」字段「%s」重复' % (mark[1], key))
                values[key] = value.strip()
                current = key
            elif line.startswith(('  ', '\t')) and current is not None:
                values[current] += '\n' + line.strip()
            elif line.strip() and rep is not None:
                rep.fail(code, '记录「%s」有无法解析的行：%s' % (mark[1], line.strip()))
        for field in fields:
            if not values.get(field, '').strip() and rep is not None:
                rep.fail(code, '记录「%s」缺少非空字段「%s」' % (mark[1], field))
        rows.append([values.get(field, '') for field in fields])
    return rows


def seen_block(section: str) -> Optional[str]:
    """覆盖核对由独立粗体标题引入，遇到下一个粗体标题结束。"""
    hit = re.search(r'^\*\*覆盖核对\*\*[^\n]*\n(.*?)(?=^\*\*|\Z)', section, re.MULTILINE | re.DOTALL)
    return hit[1] if hit else None


def without_seen(section: str) -> str:
    block = seen_block(section)
    return section.replace(block, '') if block is not None else section


AGREE_FIELDS = ('这次要打破什么', '为什么', '什么时候回到标准')
FOLLOW_FIELDS = ('出处', '条款', '要求')
DECISION_FIELDS = ('决策', '选择', '放弃', '理由', '来源', '何时重评')
FILE_FIELDS = ('文件', '操作', '职责')
COVERAGE_FIELDS = ('R', '任务', '自动验证', '手工步骤')
RISK_FIELDS = ('风险', '触发信号', '应对')


def task_blocks(section: str) -> List[Tuple[int, str]]:
    """按 `- [ ] **T1**` 切出任务块。模板示例写在注释里，先剥掉注释再解析。"""
    section = _COMMENT.sub('', section)
    marks = list(_TASK_MARK.finditer(section))
    out: List[Tuple[int, str]] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        out.append((int(mark.group(1)), section[mark.end():end]))
    return out


# ─── 结果容器 ────────────────────────────────────────────────────────────────


class Report:
    """收集校验结果，最后决定输出与退出码。"""

    def __init__(self) -> None:
        self.failures: List[str] = []
        self.checked: List[str] = []
        self.skipped: List[str] = []
        self.status = ''
        # 从 Spec 行解析出的 (id, 版本, spec 状态)。
        self.spec_ref: Optional[Tuple[str, str, str]] = None
        # spec.md 第 4 节的 R 编号。
        self.spec_rs: List[str] = []
        # 第 4 节的任务编号。
        self.task_ids: List[int] = []
        # 第 5 节 R → 任务号。
        self.coverage: Dict[str, List[int]] = {}
        # 约束表的去向集合。
        self.targets: List[str] = []

    def fail(self, code: str, message: str) -> None:
        self.failures.append('%s  %s' % (code, message))

    def ok(self, code: str) -> None:
        self.checked.append(code)

    def skip(self, code: str, why: str) -> None:
        self.skipped.append('%s %s' % (code, why))

    def report(self, path: str) -> int:
        print('plan-lint  %s' % path)
        if not self.failures:
            print('PASS  %d 项检查通过' % len(self.checked))
            for item in self.skipped:
                print('SKIP  %s' % item)
            return 0
        for item in self.failures:
            print('FAIL  %s' % item)
        print('%d 项不通过，共 %d 项检查' % (len(self.failures), TOTAL_RULES))
        return 1


# ─── plan.md：L01–L04、L07 ───────────────────────────────────────────────────


def check_head(rep: Report, plan_dir: str, head: Dict[str, str], spec_head: Dict[str, str]) -> None:
    """L01 头部两项、Spec 行可解析、与目录名和 spec.md 对得上。"""
    for key in HEAD_FIELDS:
        if key not in head:
            rep.fail('L01', 'plan.md 头部缺字段「%s」' % key)
    for key in FORBIDDEN_HEAD:
        if key in head:
            rep.fail(
                'L01',
                'plan.md 头部不要写「%s」；头部只记录 Spec 和 Status，回滚步骤写在风险记录的「应对」里' % key,
            )

    rep.status = head.get('Status', '')
    if rep.status not in PLAN_STATUS:
        rep.fail('L01', 'Status 必须是 %s，实际「%s」' % (' / '.join(PLAN_STATUS), rep.status))

    expected_dir = os.path.basename(os.path.normpath(plan_dir))
    raw = head.get('Spec', '')
    match = _HEAD_SPEC.match(raw)
    if match is None:
        rep.fail(
            'L01',
            'Spec 必须形如 `pNN-NNN-<slug>`（spec vN / approved），实际「%s」' % raw,
        )
    else:
        spec_id, spec_version, spec_status = match.group(1), match.group(2), match.group(3)
        rep.spec_ref = (spec_id, spec_version, spec_status)
        if spec_id != expected_dir:
            rep.fail('L01', 'Spec「%s」与目录名「%s」不一致' % (spec_id, expected_dir))
        if spec_status != 'approved':
            rep.fail('L01', 'Spec 行声明的 spec 状态是「%s」，本阶段要求 approved' % spec_status)
        actual_status = spec_head.get('Status', '')
        if actual_status != 'approved':
            rep.fail('L01', 'spec.md 的 Status 是「%s」，plan 不得启动' % actual_status)
        actual_version = spec_head.get('版本', '')
        if actual_version != 'v%s' % spec_version:
            rep.fail(
                'L01',
                'Spec 行写的是 v%s，spec.md 实际是 %s——版本对不上，plan 可能基于旧需求' % (spec_version, actual_version),
            )

    rep.ok('L01')


def check_structure(rep: Report, text: str, sections: Dict[int, str]) -> None:
    """L02 六节齐全；draft 时第 3–6 节必须为空。"""
    for index in range(1, 7):
        if index not in sections:
            rep.fail('L02', 'plan.md 缺第 %d 节（## %d. ...）' % (index, index))
    if rep.status == 'draft':
        for index in range(3, 7):
            if substantive_lines(sections.get(index, '')):
                rep.fail(
                    'L02',
                    'Status=draft 时第 %d 节必须为空——方案摘要还没经用户确认，不许先写设计与任务' % index,
                )
    rep.ok('L02')


def check_summary(rep: Report, section: str) -> None:
    """L03 方案摘要：非空、不超行、有拍板栏。

    摘要正文最多 30 行；「覆盖核对」记录用于自检，不计入。
    """
    lines = body_lines(without_seen(section))
    if not lines:
        rep.fail('L03', '第 1 节方案摘要是空的')
        return
    if len(lines) > SUMMARY_MAX_LINES:
        rep.fail('L03', '方案摘要 %d 行，超过 %d 行——请精简表述，保留用户作决定所需的内容' % (len(lines), SUMMARY_MAX_LINES))
    text = _COMMENT.sub('', section)
    if not any(label in text for label in _PITCH_HEADS + _NO_PITCH_HEADS):
        rep.fail('L03', '第 1 节缺「需要用户决定的事项」或「无需用户决定」，用户不知道是否需要作决定')
    rep.ok('L03')


def check_constraints(rep: Report, section: str, plan_dir: str) -> None:
    """L04 第 2 节两组记录：2.1 给用户（一条一个决定），2.2 给 Agent（既有规范，按主题合并）。

    分开写、分开校验，避免日常执行要求淹没需要用户决定的例外。
    """
    subs = split_subsections(section)
    agree, follow = subs.get('2.1'), subs.get('2.2')
    if agree is None:
        rep.fail('L04', '第 2 节缺「### 2.1 需要用户确认的例外」——用户只需审阅例外记录，它必须单独存在')
    if follow is None:
        rep.fail('L04', '第 2 节缺「### 2.2 Agent 遵循的既有规范」——既有规范不要和需要用户确认的例外混在一组记录里')
    if agree is None or follow is None:
        return
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(plan_dir)))
    overridden = _check_agree(rep, agree, repo_root, plan_dir)
    _check_follow(rep, follow, repo_root, plan_dir, overridden)
    rep.ok('L04')


def _is_placeholder(text: str) -> bool:
    """模板占位行（含 <...>）不参与内容校验，否则模板复制过来就过不了闸门。

    先摘掉 Markdown 链接的尖括号目标：`[规范](<../../docs/x.md>)` 是正常引用，
    不是占位符；不摘的话，整行会被静默跳过——路径写错也不会有人发现。
    """
    cleaned = _LINK_DEST.sub('](link)', text)
    return '<' in cleaned and '>' in cleaned


def _check_agree(rep: Report, section: str, repo_root: str, plan_dir: str) -> set:
    """2.1：三格；首格标去向；理由非空，覆盖写明条款，回归条件可判断。

    返回被覆盖的条款 ID 集合，交给 2.2 做交叉核对。
    """
    overridden = set()
    rows = record_rows(section, AGREE_FIELDS, rep)
    for number, cells in enumerate(rows, 1):
        if _is_placeholder('|'.join(cells)):
            continue
        if len(cells) != 3:
            rep.fail(
                'L04',
                '第 2.1 节第 %d 行有 %d 格，应为 这次要打破什么 / 为什么 / 什么时候回到标准 三格'
                % (number, len(cells)),
            )
            continue
        what, why, decay = (clean_cell(cell) for cell in cells)
        if not why:
            rep.fail('L04', '第 2.1 节第 %d 行没写「为什么」' % number)
        if not what:
            rep.fail('L04', '第 2.1 节第 %d 行没写打破的是什么' % number)
            continue
        target = next((item for item in ALLOWED_TARGETS if item in what), None)
        if target is None:
            rep.fail(
                'L04',
                '第 2.1 节第 %d 行没标去向——这里是"需要用户确认的例外"的记录，每条都要说明属于哪一种：'
                '覆盖 / 仅本次 / 回 spec / 先补约定' % number,
            )
        elif target == '既有':
            rep.fail(
                'L04',
                '第 2.1 节第 %d 行是「既有」——既有规范放 2.2，不要占用户的注意力' % number,
            )
        else:
            rep.targets.append(target)
            if target == '覆盖':
                _check_override(rep, number, what)
                overridden.update(clause_ids(what))
        for rel in _MD_PATH.findall(what):
            _check_ref(rep, '第 2.1 节第 %d 行' % number, rel, repo_root, plan_dir)
        if decay in VAGUE_DECAY:
            rep.fail(
                'L04',
                '第 2.1 节第 %d 行的「什么时候回到标准」不可判断（「%s」）——写清什么条件下回到通用规范，'
                '例如"下个需要同类控件的 spec"' % (number, decay),
            )
    return overridden


def _is_qualified(text: str) -> bool:
    """这一条有没有写明"只沿用哪一部分"。"""
    if any(word in text for word in QUALIFIERS):
        return True
    return any(pattern.search(text) is not None for pattern in QUALIFIER_PATTERNS)


def _path_tail(rel: str) -> str:
    """去掉开头的 `../` 再比，`docs/x.md` 与 `../../docs/x.md` 算同一份。"""
    parts = os.path.normpath(rel).split(os.sep)
    while parts and parts[0] == '..':
        parts.pop(0)
    return os.sep.join(parts)


def _follow_items(section: str) -> List[str]:
    """2.2 的条目：`- ` 开头的一行，或表格的数据行（表头与分隔线不算）。

    两种写法都得读。只认 `- ` 时，把内容改写成一张表就能整节跳过校验——
    路径存不存在、有没有限定词，全都不再有人看。
    """
    items: List[str] = []
    in_table = False
    for raw in _COMMENT.sub('', section).split('\n'):
        line = raw.strip()
        if not line:
            in_table = False
            continue
        if line.startswith('- '):
            items.append(line)
            in_table = False
            continue
        if line.startswith('|'):
            if not in_table:
                in_table = True        # 第一行是表头，跳过
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(_SEP_CELL.match(cell) for cell in cells if cell):
                continue               # 分隔线 `|---|---|`
            items.append('，'.join(cell for cell in cells if cell))
            continue
        in_table = False
    return items


def _check_follow(
    rep: Report, section: str, repo_root: str, plan_dir: str, overridden: set
) -> None:
    """2.2：每条一个主题，出处必须存在。用户可以跳读，但 Agent 得找得到。"""
    if re.search(r'^####[ \t]+|^-\s+(?:出处|条款|要求)[：:]', section, re.MULTILINE):
        items = ['，'.join(row) for row in record_rows(section, FOLLOW_FIELDS, rep)]
    else:
        items = _follow_items(section)
    real = [item for item in items if not _is_placeholder(item)]
    if not real:
        rep.fail('L04', '第 2.2 节没有列出任何既有规范——预研没做，或者约束被塞回了 2.1')
        return
    for number, item in enumerate(real, 1):
        # 同一条款不能既在 2.1 被覆盖、又在 2.2 被整体引用：读者对不上账，
        # Agent 也会按 2.2 把被覆盖的部分做回去。
        for clause in clause_ids(item):
            if clause in overridden and not _is_qualified(item):
                rep.fail(
                    'L04',
                    '第 2.2 节第 %d 条整体引用了 %s，而 2.1 已覆盖它的一部分——'
                    '写明只沿用哪一部分（形如「仅三条交付命令」）或「除…外」，'
                    '否则这条到底还生不生效看不出来' % (number, clause),
                )
        paths = _MD_PATH.findall(item)
        if not paths:
            rep.fail(
                'L04',
                '第 2.2 节第 %d 条没写出处（形如 `docs/standards/xxx.md` REPORT-01）：%s'
                % (number, item[:30]),
            )
            continue
        seen_paths = set()
        for rel in paths:
            tail = _path_tail(rel)
            if tail in seen_paths:
                continue          # `[docs/x.md](<../../docs/x.md>)` 指向同一份文件，只报一次
            seen_paths.add(tail)
            _check_ref(rep, '第 2.2 节第 %d 条' % number, rel, repo_root, plan_dir)


def _check_override(rep: Report, number: int, what: str) -> None:
    """标了 `覆盖` 的，必须写明覆盖了哪一条。

    允许"更具体覆盖更一般"，但覆盖必须是可核对的：写了覆盖谁，谁就得在那儿。
    路径是否存在由调用方统一查（一行只报一次），这里只管"写没写"。
    """
    hit = re.search(r'覆盖\s*[:：]?\s*(.+)$', what)
    if hit is None:
        rep.fail(
            'L04',
            '第 2.1 节第 %d 行标了「覆盖」，但没写覆盖了哪一条（形如 `覆盖 docs/standards/report.md REPORT-01`）'
            % number,
        )
        return
    target = hit.group(1).strip()
    if not _MD_PATH.findall(target) and not re.search(r'spec\s*§\s*\d+', target):
        rep.fail(
            'L04',
            '第 2.1 节第 %d 行的被覆盖对象「%s」既不是文档路径也不是 `spec §N`' % (number, target[:40]),
        )


def _check_ref(rep: Report, where: str, rel: str, repo_root: str, plan_dir: str) -> None:
    """出处必须写成仓库相对路径，且真的存在。

    绝对路径在本机能过、换机器或换目录就全断，而且会让路径校验形同虚设
    （`os.path.join` 遇到绝对路径直接丢弃前缀），所以单独拦一条。
    """
    if os.path.isabs(rel):
        rep.fail(
            'L04',
            '%s 用了绝对路径「%s」——换机器、换 clone 目录就断，写成相对路径' % (where, rel),
        )
        return
    if not _path_exists(repo_root, plan_dir, rel):
        rep.fail(
            'L04',
            '%s 的出处「%s」不存在——引用一份不存在的规范比不写更糟' % (where, rel),
        )


def _path_exists(repo_root: str, plan_dir: str, rel: str) -> bool:
    """先按仓库根解析，再按 spec 目录解析（`grill.md` 这类同目录引用）。"""
    for base in (repo_root, plan_dir):
        if os.path.isfile(os.path.join(base, rel)):
            return True
    return False


def check_vague(rep: Report, text: str) -> None:
    """L07 全文不许留空洞词。"""
    body = _COMMENT.sub('', text)
    for word in VAGUE_WORDS:
        if word in body:
            rep.fail('L07', '出现空洞词「%s」——要么写清，要么删掉' % word)
    rep.ok('L07')


# 第 1 节里只允许以「把结论写出来」的方式引用访谈，不允许用维度 ID 指代内容：
# 「S6 已选 A」写完，人还是不知道选了哪个；「大小按 1024 换算，最多一位小数」才可判断。
_DIMENSION_ID = re.compile(r'(?<![A-Za-z0-9_])[SU][1-9](?![0-9A-Za-z_])')

# 「需要用户决定的事项」里允许出现 `维度：S3`，那是标签不是内容；先摘掉再查正文。
_DIMENSION_LABEL = re.compile(r'维度\s*[:：]\s*`?[SU][1-9]`?')


def _strip_dimension_labels(text: str) -> str:
    return _DIMENSION_LABEL.sub('', text)


def _pitch_items(summary: str) -> List[str]:
    """取「需要用户决定的事项」下面的编号项，含续行，遇到下一个粗体段落为止。"""
    lines = summary.split('\n')
    start = next((index for index, line in enumerate(lines) if any(label in line for label in _PITCH_HEADS)), None)
    if start is None:
        return []
    items: List[str] = []
    current: Optional[List[str]] = None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('**'):
            break
        if re.match(r'^\d+\.\s', stripped):
            if current is not None:
                items.append(' '.join(current))
            current = [stripped]
        elif current is not None:
            current.append(stripped)
    if current is not None:
        items.append(' '.join(current))
    return items


def _is_pitch_question(item: str) -> bool:
    """问句，或指向 2.1 的指针，都算给人留了动作。"""
    return '？' in item or '?' in item or PITCH_POINTER in item


def check_human(rep: Report, sections: Dict[int, str]) -> None:
    """L10 人读区：第 1 节是人话，2.1 每条一个决定。

    这条闸门拦的是最确定的三种退化——用 ID 指代内容、一格塞几件事、摘要里没有成品画面。
    文风本身判不了，剩下的靠阶段 4 的自检与交付时的第一句话。
    """
    summary = _COMMENT.sub('', sections.get(1, ''))
    if not any(label in summary for label in _VISIBLE_HEADS):
        rep.fail(
            'L10',
            '第 1 节缺「用户会看到的变化」——人读完第一段就该知道做成什么样；'
            '请先写清用户会看到的结果，不要只写结构和术语',
        )
    hit = _DIMENSION_ID.search(_strip_dimension_labels(summary))
    if hit is not None:
        rep.fail(
            'L10',
            '第 1 节出现裸维度 ID「%s」——把访谈结论本身写出来'
            '（写「大小按 1024 换算」，不写「S6 已选 A」）；在方案摘要中，维度 ID 只用作「需要用户决定的事项」的标签'
            % hit.group(0),
        )

    rows = record_rows(split_subsections(sections.get(2, '')).get('2.1', ''), AGREE_FIELDS)
    real = [cells for cells in rows if not _is_placeholder('|'.join(cells))]
    if real and any(label in summary for label in _NO_PITCH_HEADS):
        rep.fail(
            'L10',
            '第 1 节说「无需用户决定」，但 2.1 列了 %d 条需要用户确认的例外——'
            '用户看到"无需用户决定"就会跳过，那几条等于没写' % len(real),
        )
    if any(label in summary for label in _PITCH_HEADS):
        items = _pitch_items(summary)
        if not items and PITCH_POINTER not in summary:
            rep.fail(
                'L10',
                '第 1 节写了「需要用户决定的事项」却没列问题，也没指向 2.1——'
                '要么写成问题，要么写「需要用户决定的事项：见 2.1 …」，要么写「无需用户决定」',
            )
        for number, item in enumerate(items, 1):
            if not _is_pitch_question(item):
                rep.fail(
                    'L10',
                    '第 1 节拍板第 %d 项是结论不是问题（「%s」）——结论句只给用户"同意"一个动作，'
                    '请给出两个可选动作，或直接写「需要用户决定的事项：见 2.1 …」，'
                    '不要换一套措辞把 2.1 再复述一遍' % (number, item[:28]),
                )
    for number, cells in enumerate(rows, 1):
        if _is_placeholder('|'.join(cells)) or len(cells) < 2:
            continue
        why = clean_cell(cells[1])
        if len(why) > WHY_MAX_CHARS:
            rep.fail(
                'L10',
                '第 2.1 节第 %d 行的「为什么」有 %d 字，超过 %d——一格只说一件事，超了就是两条约束'
                % (number, len(why), WHY_MAX_CHARS),
            )
        if '；' in why or ';' in why:
            rep.fail(
                'L10',
                '第 2.1 节第 %d 行的「为什么」用分号串了两件事——拆成两行，一个决定一行' % number,
            )
    rep.ok('L10')


# ─── plan.md：L11 ────────────────────────────────────────────────────────────


def check_visible_map(rep: Report, sections: Dict[int, str]) -> None:
    """L11 每条 R 在第 1 节都有落点。

    对照 spec 第 4 节的逐条需求，而不是只看第 2 节的摘要，避免漏掉验收细节。
    脚本只检查 R 编号是否对应、引文是否能在段落中逐字找到。
    引文是否准确表达需求，由独立上下文核查，见 rules/crosscheck.md。
    """
    section = _COMMENT.sub('', sections.get(1, ''))
    block = seen_block(section)
    if block is None:
        rep.fail(
            'L11',
            '第 1 节缺「**覆盖核对**」记录——spec 每条 R 都要指出落到「用户会看到的变化」的哪一句。'
            '没有这些记录，漏掉的 R 在人评审时不会显形',
        )
        return
    para = _VISIBLE_PARA.search(without_seen(section))
    if para is None or not para.group(1).strip():
        rep.fail('L11', '第 1 节找不到「用户会看到的变化」的内容，覆盖核对没有可对照的落点')
        return
    visible = para.group(1)

    rows = record_rows(block, ('R', '落点'), rep, 'L11')
    if not rows:
        rep.fail('L11', '「覆盖核对」记录没有数据行')
        return
    seen: Dict[str, int] = {}
    for number, cells in enumerate(rows, 1):
        if len(cells) < 2:
            rep.fail('L11', '覆盖核对第 %d 行只有 %d 格，应为 R / 落点 两格' % (number, len(cells)))
            continue
        rid = clean_cell(cells[0])
        if not re.fullmatch(r'R\d+', rid):
            rep.fail('L11', '覆盖核对第 %d 行首格必须是 R 编号，实际「%s」' % (number, rid[:12]))
            continue
        where = cells[1].strip()
        if _is_placeholder(where):
            continue  # 模板占位行；下面的 R 集合核对会报"没有落点"，那才是该说的话
        seen[rid] = seen.get(rid, 0) + 1
        if where.startswith(NO_SEEN_MARK):
            if len(where) < 8 or '见' not in where:
                rep.fail(
                    'L11',
                    '%s 标了「无」却没说在那一段交代——写「无 —— 见「代价」段」这种可以点过去核对的指向'
                    % rid,
                )
            continue
        quote = where.strip('「」“”"').strip()
        if len(quote) < SEEN_QUOTE_MIN:
            rep.fail('L11', '%s 的落点「%s」不足 %d 字，指不到具体画面' % (rid, quote, SEEN_QUOTE_MIN))
        elif len(quote) > SEEN_QUOTE_MAX:
            rep.fail(
                'L11',
                '%s 的落点有 %d 字，超过 %d——照抄其中一句就够，整段复述让核对变重'
                % (rid, len(quote), SEEN_QUOTE_MAX),
            )
        elif quote not in visible:
            rep.fail(
                'L11',
                '%s 的落点「%s」在「用户会看到的变化」里找不到——落点要逐字照抄，改写后核对就成了空话'
                % (rid, quote),
            )

    for rid in rep.spec_rs:
        if rid not in seen:
            rep.fail(
                'L11',
                'spec 的 %s 没有落点——第 1 节没有一句写到它，人读到的画面里这条验收要求不存在'
                % rid,
            )
        elif seen[rid] > 1:
            rep.fail('L11', '%s 在覆盖核对里出现 %d 次，每条 R 只能有一个落点' % (rid, seen[rid]))
    for rid in seen:
        if rid not in rep.spec_rs:
            rep.fail('L11', '覆盖核对列了 spec 里不存在的 %s' % rid)
    rep.ok('L11')


# ─── plan.md：L05–L06、L08–L09 ───────────────────────────────────────────────


def check_tasks(rep: Report, section: str, design: str = '') -> None:
    """L05 任务编号连续、四行齐全、验证可执行、依赖成链、改动不越 3.3 边界。"""
    blocks = task_blocks(section)
    if not blocks:
        rep.fail('L05', '第 4 节没有任何任务（`- [ ] **T1** ...`）')
        return
    inventory = record_rows(split_subsections(design).get('3.3', ''), FILE_FIELDS, rep, 'L05')
    seen_files = set()
    for row in inventory:
        paths = _CHANGE_PATH.findall(row[0]) if row else []
        for path in paths:
            if path in seen_files:
                rep.fail('L05', '第 3.3 节文件 `%s` 重复' % path)
            seen_files.add(path)
        if not paths or any(not valid_change_path(path) for path in paths):
            rep.fail('L05', '第 3.3 节每行必须用反引号逐个列出规范的仓库相对文件路径')
    files = design_files(design)
    if not files:
        rep.fail('L05', '第 3.3 节没有影响文件清单——请列出允许改动的具体文件，才能核对任务范围')
    seen: List[int] = []
    for index, (tid, block) in enumerate(blocks, 1):
        rep.task_ids.append(tid)
        seen.append(tid)
        if tid != index:
            rep.fail('L05', '任务编号不连续：第 %d 条是 T%d' % (index, tid))
        for field in TASK_FIELDS:
            matches = list(re.finditer(r'^\s*-\s*%s[：:][ \t]*(.*)$' % field, block, re.MULTILINE))
            hit = matches[0] if matches else None
            if len(matches) > 1:
                rep.fail('L05', 'T%d 的「%s」字段重复' % (tid, field))
            if hit is None:
                rep.fail('L05', 'T%d 缺「- %s：」这一行' % (tid, field))
            elif hit.group(1).strip() in ('', '—', '-'):
                # `依赖：—` 是合法写法：第一个任务没有前置。
                if field != '依赖':
                    rep.fail('L05', 'T%d 的「%s」是空的' % (tid, field))
            elif field == '验证':
                value = hit.group(1)
                if '手工' not in value and '`' not in value:
                    rep.fail('L05', 'T%d 的验证「%s」既没有命令（反引号）也没写「手工：」' % (tid, value.strip()))
            elif field == '依赖':
                _check_deps(rep, tid, hit.group(1), seen)
            elif field == '改动':
                _check_change(rep, tid, hit.group(1), files)
    rep.ok('L05')


def _check_deps(rep: Report, tid: int, value: str, seen: List[int]) -> None:
    """依赖必须指向排在它前面的任务。

    按编号检查：例如 T4 依赖 T5，说明任务顺序不成立。
    应把提供所需文件、入口或数据的任务排在前面。
    """
    refs = [int(match.group(1)) for match in re.finditer(r'T(\d+)', value)]
    if not refs:
        rep.fail('L05', 'T%d 的依赖「%s」里没有任务号' % (tid, value.strip()))
        return
    for ref in refs:
        if ref == tid:
            rep.fail('L05', 'T%d 依赖自己' % tid)
        elif ref not in seen:
            rep.fail(
                'L05',
                'T%d 依赖 T%d，但 T%d 不存在或排在 T%d 之后——依赖只能指向先做的任务'
                % (tid, ref, ref, tid),
            )


def _check_change(rep: Report, tid: int, value: str, files: set) -> None:
    """改动的路径必须在 3.3 清单内。

    3.3 列出实现阶段允许改动的文件，任务中不能增加清单外的文件。
    """
    if not files:
        return
    paths = _CHANGE_PATH.findall(value)
    if not paths:
        rep.fail('L05', 'T%d 的改动必须用反引号逐个列出仓库相对路径' % tid)
    for path in paths:
        if not valid_change_path(path):
            rep.fail('L05', 'T%d 的改动路径 `%s` 不是规范的仓库相对文件路径' % (tid, path))
            continue
        if path in files:
            continue
        rep.fail(
            'L05',
            'T%d 要改 `%s`，但它不在第 3.3 节的文件清单里——只允许修改清单内的文件' % (tid, path),
        )


def design_files(design: str) -> set:
    """第 3.3 节影响文件清单里的路径。"""
    out = set()
    for cells in record_rows(split_subsections(design).get('3.3', ''), FILE_FIELDS):
        if not cells:
            continue
        for name in _CHANGE_PATH.findall(cells[0]):
            if valid_change_path(name) and not _is_placeholder(name):
                out.add(name)
    return out



def check_coverage(rep: Report, section5: str, section4: str) -> None:
    """L06 R 覆盖完整、只出现一次、任务号真实、与任务「覆盖」互洽。"""
    rows = record_rows(section5, COVERAGE_FIELDS, rep, 'L06')
    seen: Dict[str, int] = {}
    for number, cells in enumerate(rows, 1):
        if not cells or not re.fullmatch(r'R\d+', clean_cell(cells[0])):
            rep.fail('L06', '第 5 节第 %d 行首格必须是 R 编号' % number)
            continue
        rid = clean_cell(cells[0])
        seen[rid] = seen.get(rid, 0) + 1
        if len(cells) != 4:
            rep.fail('L06', '%s 的验证记录必须有 R、任务、自动验证、手工步骤四个字段' % rid)
        auto = clean_cell(cells[2]) if len(cells) > 2 else ''
        manual = clean_cell(cells[3]) if len(cells) > 3 else ''
        absent = ('', '—', '-', '无', '不适用')
        auto_empty = auto in absent or re.fullmatch(r'<[^<>]+>', auto) is not None
        manual_empty = manual in absent or re.fullmatch(r'<[^<>]+>', manual) is not None
        if auto_empty and manual_empty:
            rep.fail('L06', '%s 的自动验证与手工步骤不能同时为空' % rid)
        task_cell = cells[1] if len(cells) > 1 else ''
        refs = [int(match.group(1)) for match in _T_REF.finditer(task_cell)]
        if not refs:
            rep.fail('L06', '%s 没有指向任何任务' % rid)
        for ref in refs:
            if ref not in rep.task_ids:
                rep.fail('L06', '%s 指向不存在的 T%d' % (rid, ref))
        rep.coverage[rid] = refs

    for rid in rep.spec_rs:
        if rid not in seen:
            rep.fail('L06', 'spec 的 %s 没有验证行——没有验证的需求等于没实现' % rid)
        elif seen[rid] > 1:
            rep.fail('L06', '%s 出现 %d 次，每条 R 只能有一行' % (rid, seen[rid]))
    for rid in seen:
        if rid not in rep.spec_rs:
            rep.fail('L06', '第 5 节列了 spec 里不存在的 %s' % rid)

    # 任务的「覆盖」列必须与第 5 节互洽：任务声称覆盖的 R，其验证行必须包含该任务。
    for tid, block in task_blocks(section4):
        hit = re.search(r'^\s*-\s*覆盖[：:]\s*(.*)$', block, re.MULTILINE)
        if hit is None:
            continue
        claimed = ['R%s' % match.group(1) for match in _R_REF.finditer(hit.group(1))]
        if not claimed:
            rep.fail('L06', 'T%d 的「覆盖」没有列任何 R 编号' % tid)
        for rid, refs in rep.coverage.items():
            if tid in refs and rid not in claimed:
                rep.fail('L06', '第 5 节 %s 指向 T%d，但任务「覆盖」没有列出 %s' % (rid, tid, rid))
        for rid in claimed:
            if tid not in rep.coverage.get(rid, []):
                rep.fail('L06', 'T%d 声称覆盖 %s，但第 5 节 %s 的验证行没指向 T%d' % (tid, rid, rid, tid))
    rep.ok('L06')


def check_blocking(rep: Report, sections: Dict[int, str]) -> None:
    """L08 定稿完整性在 design-ok 即检查，不把用户的批准当作内容检查前置。"""
    blocked = [target for target in rep.targets if target in BLOCKING_TARGETS]
    if blocked and rep.status in ('design-ok', 'approved'):
        rep.fail(
            'L08',
            '第 2 节有「%s」，这份 plan 只能停在 draft——先解决它，再定稿' % '、'.join(sorted(set(blocked))),
        )
    if rep.status in ('design-ok', 'approved'):
        for index in range(3, 7):
            if not substantive_lines(sections.get(index, '')):
                rep.fail('L08', '%s 时第 %d 节必须有实际内容' % (rep.status, index))
        design = split_subsections(sections.get(3, ''))
        for key in ('3.1', '3.2', '3.3', '3.4'):
            if not substantive_lines(design.get(key, '')):
                rep.fail('L08', '%s 时第 %s 节不能为空' % (rep.status, key))
        risks = sections.get(6, '')
        # 2.1 已校验覆盖例外；3.2 可仅引用它，但显式决策仍须字段完整。
        decisions = record_rows(design.get('3.2', ''), DECISION_FIELDS, rep, 'L08')
        for number, row in enumerate(decisions, 1):
            if len(row) != len(DECISION_FIELDS) or any(not clean_cell(cell) for cell in row):
                rep.fail('L08', '第 3.2 节第 %d 条决策必须有六个非空字段：%s'
                         % (number, ' / '.join(DECISION_FIELDS)))
        risk_rows = record_rows(risks, RISK_FIELDS, rep, 'L08')
        if not risk_rows or any(len(row) < 3 or any(clean_cell(cell) in ('', '—', '-') or re.fullmatch(r'<[^<>]+>', clean_cell(cell)) is not None for cell in row[:3]) for row in risk_rows):
            rep.fail('L08', '第 6 节必须有风险、触发信号和应对/回滚的非空数据行')
        # 只核记录存在；语义是否通过必须独立对证，不能把这行当作审查证据。
        if not re.search(r'^\*\*对证\*\*[：:]\s*\S', _COMMENT.sub('', risks), re.MULTILINE):
            rep.fail('L08', '第 6 节缺对证记录；首轮 lint 前可记未运行，交付前必须实际完成')
    rep.ok('L08')


def check_spec_pending(rep: Report, spec_text: str) -> None:
    """L09 spec 第 7 节还有待决项时，plan 不该存在。"""
    sections = split_sections(spec_text)
    section7 = sections.get(7, '')
    body = _COMMENT.sub('', section7)
    if re.search(r'^\d+\.\s+', body, re.MULTILINE):
        rep.fail('L09', 'spec.md 第 7 节还有待决问题——阶段 0 就该停下，回 sdd-grill')
    else:
        rep.ok('L09')


def check_spec_rs(rep: Report, spec_text: str) -> None:
    """从 spec 第 4 节取 R 编号，供 L06 核对覆盖。"""
    sections = split_sections(spec_text)
    rep.spec_rs = ['R%s' % match.group(1) for match in _SPEC_R.finditer(sections.get(4, ''))]
    if not rep.spec_rs:
        rep.fail('L06', 'spec.md 第 4 节没有 R 条目，无法核对覆盖')


# ─── 入口 ────────────────────────────────────────────────────────────────────


def _read(path: str) -> str:
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def _use_utf8_stdout() -> None:
    """Windows 默认按 cp936 输出，统一成 UTF-8 才能和终端、CI 日志对齐。"""
    if os.environ.get('PYTHONIOENCODING'):
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='plan_lint.py',
        description='检查 plan.md 的格式，以及它与 spec.md 的对应关系',
    )
    parser.add_argument('spec_dir', help='spec 目录，如 specs/pNN-NNN-<slug>')
    args = parser.parse_args(argv)
    _use_utf8_stdout()

    plan_path = os.path.join(args.spec_dir, 'plan.md')
    spec_path = os.path.join(args.spec_dir, 'spec.md')
    missing = [path for path in (plan_path, spec_path) if not os.path.isfile(path)]
    if missing:
        sys.stderr.write('缺少 %s\n' % ' 或 '.join(missing))
        return 2

    plan_text = _read(plan_path)
    spec_text = _read(spec_path)
    sections = split_sections(plan_text)

    rep = Report()
    check_head(rep, args.spec_dir, header_fields(plan_text, rep), header_fields(spec_text))
    check_spec_rs(rep, spec_text)
    check_structure(rep, plan_text, sections)
    check_summary(rep, sections.get(1, ''))
    check_constraints(rep, sections.get(2, ''), args.spec_dir)
    check_human(rep, sections)
    check_visible_map(rep, sections)
    check_blocking(rep, sections)
    check_spec_pending(rep, spec_text)
    check_vague(rep, plan_text)

    if rep.status == 'draft':
        rep.skip('L05', 'Status=draft：任务与覆盖在 design-ok 之后校验')
        rep.skip('L06', 'Status=draft：任务与覆盖在 design-ok 之后校验')
    else:
        check_tasks(rep, sections.get(4, ''), sections.get(3, ''))
        check_coverage(rep, sections.get(5, ''), sections.get(4, ''))

    return rep.report(args.spec_dir)


if __name__ == '__main__':
    sys.exit(main())
