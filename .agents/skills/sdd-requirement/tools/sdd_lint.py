#!/usr/bin/env python3
"""检查 sdd-requirement 需求文档和决策日志的固定格式。

用法：
    python .agents/skills/sdd-requirement/tools/sdd_lint.py <spec 目录>

校验项：

    L01  头部六项字段齐全且取值合法，Spec 编号与目录名一致（类型 / Status / 上游）
    L02  第 1–7 节标题齐全
    L03  R 编号连续、不重复、不超过 12 条
    L04  每条 R 有「反例」与「可观察证据」，范畴取值合法
    L05  第 5 节每条「不做」带「理由：」
    L06  第 7 节每条待决问题带「维度：<ID>」与 A / B 两个选项；有待决问题不得批准
    L07  头部「附带交付」与 R 上的范畴标记互相登记
    L08  成本字段十一项齐全；预算符合需求类型；追加合法；用量不超过批准额度
    L09  覆盖矩阵恰好包含本类型必做维度；不适用有理由；待决状态与第 7 节双向对应
    L10  规范触碰清单存在；冲突项不许留在第 7 节

脚本只检查固定格式和可计算的规则。
人仍需判断需求条目（R）是否正确、取舍是否合理；脚本不能替代这些判断。

退出码：0 全过 / 1 有 FAIL / 2 用法错误或文件缺失。

脚本随本 skill 分发，纯标准库、Python 3.8+，不依赖被审项目的语言、框架或构建系统。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# ─── 格式与规则常量 ────────────────────────────────────────────────────────────────
#
# 这些规则属于本技能。维度和预算与 ../rules/dimensions.md 对应，修改时须同步。

# 每种类型必做的维度 ID。
REQUIRED_DIMS: Dict[str, List[str]] = {
    'new': ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'N1', 'N2', 'N3'],
    'extend': ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'E1', 'E2', 'E3', 'E4', 'E5'],
    'fix': ['D1', 'D6', 'F1', 'F2', 'F3', 'F4'],
}

# 阶段 1 事实收集的工具调用预算。
TOOL_BUDGET: Dict[str, int] = {'new': 8, 'extend': 12, 'fix': 8}

# 允许出现在 R 条目上的范畴标记。
SCOPE_TAGS = ('standard', 'doc', 'data', 'contract')

# 规模上限：超过就该拆需求，而不是继续压缩表述。
MAX_RS = 12

# L01–L10 的检查项总数。
TOTAL_RULES = 10

# 规范条款编号的形状：大写前缀 + 序号，如 FSD-08 / SEC-3 / PERF-12。
STANDARDS_ID = r'[A-Z][A-Z0-9]{1,5}-\d+'

BASE_HEAD_FIELDS = ('Spec', '类型', '上游', '附带交付', 'Status', '版本')
SPEC_ID_SHAPE = re.compile(r'^p\d{2}-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*$')
VERSION_SHAPE = re.compile(r'^v\d+$')
HEAD_STATUS = ('draft', 'approved', 'stale')
MATRIX_STATUS = ('已覆盖', '不适用', '已推翻并说明', '待决')
TOUCH_STATUS = ('无冲突', '冲突', '不涉及')

# 成本字段必须有十一行，顺序不限，缺一行就 FAIL。
COST_KEYS = (
    '类型',
    '问题数',
    '问题上限',
    '问题追加',
    '工具调用',
    '工具预算',
    '工具追加',
    '追加理由',
    '开始',
    '结束',
    '重问',
)

_ROW2 = re.compile(r'^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$')
_SECTION = re.compile(r'^## (\d)\. .*$', re.MULTILINE)
_R_MARK = re.compile(r'^-\s*\[[ xX]\]\s*\*\*R(\d+)\*\*', re.MULTILINE)
_PENDING_ITEM = re.compile(r'^\d+\.\s+', re.MULTILINE)
_PENDING_DIM = re.compile(r'维度[：:]\s*`?([A-Z]\d)')
_SCOPE_TAG = re.compile(r'\*\*范畴\*\*[：:]\s*([a-z]+)')
_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)


# ─── 解析 ────────────────────────────────────────────────────────────────────


def question_limit(spec_type: str) -> int:
    """问题上限 = 本型必做维度数 + 3 次派生追问（new 12 / extend 14 / fix 9）。"""
    return len(REQUIRED_DIMS.get(spec_type, ())) + 3


def clean_cell(raw: str) -> str:
    """去除反引号和两端空白，使带反引号与不带反引号的单元格取值相同。"""
    return raw.replace('`', '').strip()


def field_pairs(text: str) -> List[Tuple[str, str]]:
    """读取固定字段行或两列表格；固定字段值中的管道不分割。"""
    pairs = []
    for line in _COMMENT.sub('', text).splitlines():
        match = re.match(r'^-\s+([^：:]+)[：:]\s*(.*)$', line) or _ROW2.match(line)
        if match:
            key = clean_cell(match.group(1))
            if key.replace('-', ''):
                pairs.append((key, clean_cell(match.group(2))))
    return pairs


def key_value_rows(text: str) -> Dict[str, str]:
    """取得字段值；校验入口另行检查重复，避免静默覆盖。"""
    return dict(field_pairs(text))


def check_fields(rep: Report, code: str, text: str,
                 keys: Tuple[str, ...], label: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for key, value in field_pairs(text):
        if key in fields:
            rep.fail(code, '%s 重复字段「%s」' % (label, key))
        fields[key] = value
    for key in keys:
        if key not in fields:
            rep.fail(code, '%s 缺字段「%s」' % (label, key))
        elif not fields[key]:
            rep.fail(code, '%s 字段「%s」为空' % (label, key))
    return fields


def record_rows(rep: Report, code: str, section: str,
                keys: Tuple[str, ...]) -> List[Tuple[str, str, str]]:
    """读取四级标题记录块；每块字段独立校验。"""
    section = _COMMENT.sub('', section)
    marks = list(re.finditer(r'^####[ \t]+(.+)$', section, re.MULTILINE))
    preamble = section[:marks[0].start()] if marks else section
    if any(key in keys for key, _ in field_pairs(preamble)):
        rep.fail(code, '记录字段必须放在「#### <记录标题>」下')
    rows = []
    titles = set()
    for index, mark in enumerate(marks):
        title = mark.group(1).strip()
        if title in titles:
            rep.fail(code, '重复记录标题「%s」' % title)
        titles.add(title)
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        fields = check_fields(rep, code, section[mark.end():end], keys, title)
        rows.append(tuple(fields.get(key, '') for key in keys))
    return rows


def header_fields(text: str) -> Dict[str, str]:
    """读取 `## 1.` 之前的头部字段。"""
    cut = text.find('\n## 1.')
    return key_value_rows(text if cut < 0 else text[:cut])


def split_sections(text: str) -> Dict[int, str]:
    """按 `## <n>. ` 切出第 1–7 节。"""
    out: Dict[int, str] = {}
    marks = list(_SECTION.finditer(text))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        out[int(mark.group(1))] = text[mark.end():end]
    return out


def section_named(text: str, name: str) -> Optional[str]:
    """取 `## <name>` 到下一个 `## ` 之间的内容；不存在返回 None。"""
    start = text.find('## ' + name)
    if start < 0:
        return None
    nxt = text.find('\n## ', start + 1)
    return text[start:] if nxt < 0 else text[start:nxt]


def table_rows(section: str, first_cell: str) -> List[re.Match]:
    """解析 ID、状态、依据三列表格；首格的 ID 可以带反引号。"""
    pattern = re.compile(
        r'^\|\s*`?(%s)`?\s[^|]*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$' % first_cell,
        re.MULTILINE,
    )
    return list(pattern.finditer(section))


# ─── 结果容器 ────────────────────────────────────────────────────────────────


class Report:
    """收集校验结果，最后决定输出与退出码。"""

    def __init__(self) -> None:
        self.failures: List[str] = []
        self.checked: List[str] = []
        # spec.md 头部声明的类型，供 grill.md 核对。
        self.spec_type = ''
        # 覆盖矩阵里每个维度的状态。
        self.matrix_status: Dict[str, str] = {}
        # 第 7 节列出的待决维度。
        self.pending_dims: List[str] = []
        # 第 4 节出现过的 R 编号，按出现顺序。
        self.r_ids: List[str] = []
        # 带 `**范畴**` 标记的 R 编号。
        self.tagged_rs: List[str] = []

    def fail(self, code: str, message: str) -> None:
        self.failures.append('%s  %s' % (code, message))

    def ok(self, code: str) -> None:
        self.checked.append(code)

    def report(self, path: str) -> int:
        print('spec-lint  %s' % path)
        if not self.failures:
            print('PASS  %d 项检查全部通过' % len(self.checked))
            return 0
        for item in self.failures:
            print('FAIL  %s' % item)
        print('%d 项不通过，共 %d 项检查' % (len(self.failures), TOTAL_RULES))
        return 1


# ─── spec.md：L01–L07 ────────────────────────────────────────────────────────


def check_spec_path(rep: Report, spec_dir: str, text: str) -> None:
    """L01 Spec 头字段必须与所在目录名一致。"""
    expected = os.path.basename(os.path.normpath(spec_dir))
    actual = header_fields(text).get('Spec', '')
    if actual != expected:
        rep.fail('L01', 'Spec 字段「%s」必须与目录名「%s」一致' % (actual, expected))


def check_spec(rep: Report, text: str) -> None:
    """头部、七节结构、R 条目、不做清单、第 7 节、附带交付。"""
    head_text = re.split(r'^## 1\.', text, maxsplit=1, flags=re.MULTILINE)[0]
    head = check_fields(rep, 'L01', head_text, BASE_HEAD_FIELDS, 'spec.md 头部')
    check_head(rep, head)
    sections = split_sections(text)
    for index in range(1, 8):
        if index not in sections:
            rep.fail('L02', 'spec.md 缺第 %d 节（## %d. ...）' % (index, index))
    rep.ok('L02')
    check_rs(rep, sections.get(4, ''))
    check_scope_out(rep, sections.get(5, ''))
    pending = sections.get(7, '')
    check_pending(rep, pending)
    if head.get('Status') == 'approved' and _PENDING_ITEM.search(pending):
        rep.fail('L06', '第 7 节仍有待决问题，Status 不得为 approved；请先由用户决定')
    check_extra(rep, head.get('附带交付', '—'))


def check_head(rep: Report, head: Dict[str, str]) -> None:
    """L01 头部字段齐全且取值合法。"""
    for key in BASE_HEAD_FIELDS:
        if key not in head:
            rep.fail('L01', 'spec.md 头部缺字段「%s」' % key)
    rep.spec_type = head.get('类型', '')
    if rep.spec_type not in REQUIRED_DIMS:
        rep.fail('L01', '类型必须是 new / extend / fix，实际「%s」' % rep.spec_type)
    spec_id = head.get('Spec', '')
    status = head.get('Status', '')
    version = head.get('版本', '')
    upstream = head.get('上游', '—')
    if not SPEC_ID_SHAPE.fullmatch(spec_id):
        rep.fail('L01', 'Spec 必须形如 pNN-NNN-<小写英文短横线 slug>，实际「%s」' % spec_id)
    if not VERSION_SHAPE.fullmatch(version):
        rep.fail('L01', '版本必须形如 vN，实际「%s」' % version)
    if 'Approved' in head or 'Approved-Tag' in head:
        rep.fail('L01', 'spec.md 头部不得包含 Approved 或 Approved-Tag；用户明确确认后，只更新 Status')
    if status not in HEAD_STATUS:
        rep.fail('L01', 'Status 必须是 draft / approved / stale，实际「%s」' % status)
    if upstream != '—' and not SPEC_ID_SHAPE.fullmatch(upstream):
        rep.fail('L01', '上游必须是有效 spec 编号或「—」，实际「%s」' % upstream)
    if rep.spec_type in ('extend', 'fix') and upstream == '—':
        rep.fail('L01', '%s 型必须填写上游 spec 编号' % rep.spec_type)
    rep.ok('L01')


def check_rs(rep: Report, section: str) -> None:
    """L03 编号连续且不超规模；L04 每条有反例、证据与合法范畴。"""
    marks = list(_R_MARK.finditer(section))
    if not marks:
        rep.fail('L03', '第 4 节没有任何 R 条目')
        return
    if len(marks) > MAX_RS:
        rep.fail('L03', 'R 共 %d 条，超过上限 %d，应拆需求' % (len(marks), MAX_RS))
    blocks: List[Tuple[str, str]] = []
    for index, mark in enumerate(marks):
        rid = 'R%s' % mark.group(1)
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        if rid in rep.r_ids:
            rep.fail('L03', '%s 编号重复' % rid)
        rep.r_ids.append(rid)
        if rid != 'R%d' % (index + 1):
            rep.fail('L03', 'R 编号不连续：第 %d 条是 %s' % (index + 1, rid))
        blocks.append((rid, section[mark.end():end]))
    rep.ok('L03')

    for rid, block in blocks:
        for field in ('反例', '可观察证据'):
            hit = re.search(r'\*\*%s\*\*[：:]\s*(.*)' % field, block)
            if hit is None:
                rep.fail('L04', '%s 缺「**%s**：」' % (rid, field))
            elif len(hit.group(1).strip()) < 4:
                rep.fail('L04', '%s 的「%s」至少需要 4 个非首尾空白字符' % (rid, field))
        tag = _SCOPE_TAG.search(block)
        if tag is None:
            continue
        if tag.group(1) not in SCOPE_TAGS:
            rep.fail('L04', '%s 的范畴「%s」不在 %s 内' % (rid, tag.group(1), ' / '.join(SCOPE_TAGS)))
        rep.tagged_rs.append(rid)
    rep.ok('L04')


def check_scope_out(rep: Report, section: str) -> None:
    """L05 每条「不做」都要有理由。"""
    items = [line for line in section.split('\n') if re.match(r'^-\s+\S', line)]
    if not items:
        rep.fail('L05', '第 5 节没有任何「不做」条目')
        return
    for item in items:
        if '理由：' not in item:
            rep.fail('L05', '第 5 节条目缺「理由：」→ %s' % item.strip())
    rep.ok('L05')


def check_pending(rep: Report, section: str) -> None:
    """L06 每条待决问题带维度 ID 与 A / B 两个具体选项。"""
    items = list(_PENDING_ITEM.finditer(section))
    for index, item in enumerate(items):
        end = items[index + 1].start() if index + 1 < len(items) else len(section)
        block = section[item.end():end]
        dim = _PENDING_DIM.search(block)
        if dim is None:
            rep.fail('L06', '第 7 节第 %d 条缺「维度：<ID>」标记，无法与覆盖矩阵核对' % (index + 1))
        else:
            rep.pending_dims.append(dim.group(1))
        has_a = re.search(r'^\s*-\s*A[.、]', block, re.MULTILINE) is not None
        has_b = re.search(r'^\s*-\s*B[.、]', block, re.MULTILINE) is not None
        if not (has_a and has_b):
            rep.fail('L06', '第 7 节第 %d 条必须给出 A / B 两个具体选项' % (index + 1))
    rep.ok('L06')


def check_extra(rep: Report, raw: str) -> None:
    """L07 头部「附带交付」与第 4 节的范畴标记必须互相登记。"""
    listed = re.findall(r'R\d+', raw)
    for rid in listed:
        if rid not in rep.r_ids:
            rep.fail('L07', '附带交付引用了不存在的 %s' % rid)
        elif rid not in rep.tagged_rs:
            rep.fail('L07', '附带交付中的 %s 必须在第 4 节填写「**范畴**」' % rid)
    for rid in rep.tagged_rs:
        if rid not in listed:
            rep.fail('L07', '%s 带有范畴标记，请同时在头部「附带交付」登记' % rid)
    rep.ok('L07')


# ─── grill.md：L08–L10 ───────────────────────────────────────────────────────


def check_grill(rep: Report, text: str) -> None:
    """成本基线、覆盖矩阵、规范触碰，与 spec.md 的类型和第 7 节交叉核对。"""
    check_cost(rep, text)
    check_matrix(rep, text)
    check_touch(rep, text)


def check_cost(rep: Report, text: str) -> None:
    """L08 成本字段十一项齐全、预算与型匹配、追加合法、用量不超授权。"""
    cost_text = re.split(r'^## ', text, maxsplit=1, flags=re.MULTILINE)[0]
    cost = check_fields(rep, 'L08', cost_text, COST_KEYS, 'grill.md 成本字段')

    grill_type = cost.get('类型', '')
    if grill_type != rep.spec_type:
        rep.fail('L08', 'grill.md 的类型「%s」与 spec.md 的「%s」不一致' % (grill_type, rep.spec_type))

    asked = _int_or_none(cost.get('问题数'))
    calls = _int_or_none(cost.get('工具调用'))
    limit = _int_or_none(cost.get('问题上限'))
    budget = _int_or_none(cost.get('工具预算'))

    if rep.spec_type in REQUIRED_DIMS:
        expected_limit = question_limit(rep.spec_type)
        if limit is not None and limit != expected_limit:
            rep.fail('L08', '问题上限为 %d；按本类型必做维度数加 3，应为 %d' % (limit, expected_limit))
        expected_tool = TOOL_BUDGET.get(rep.spec_type, 0)
        if budget is not None and budget != expected_tool:
            rep.fail('L08', '工具预算写的是 %d，%s 型应为 %d' % (budget, rep.spec_type, expected_tool))
    if '问题数' in cost and asked is None:
        rep.fail('L08', '问题数「%s」不是整数' % cost['问题数'])
    if '工具调用' in cost and calls is None:
        rep.fail('L08', '工具调用「%s」不是整数' % cost['工具调用'])

    q_extra = _allowance(rep, '问题追加', cost.get('问题追加', '—'))
    t_extra = _allowance(rep, '工具追加', cost.get('工具追加', '—'))
    if asked is not None and limit is not None and asked > limit + q_extra:
        rep.fail(
            'L08',
            '问题数 %d 超过上限 %d + 追加 %d，必须停下来问人：拆，还是再加 +4' % (asked, limit, q_extra),
        )
    if calls is not None and budget is not None and calls > budget + t_extra:
        rep.fail(
            'L08',
            '工具调用 %d 超过预算 %d + 追加 %d，须追加或写「未读」清单' % (calls, budget, t_extra),
        )

    reason = cost.get('追加理由', '—')
    if (q_extra > 0 or t_extra > 0) and reason in ('', '—'):
        rep.fail('L08', '有追加额度时，必须在「追加理由」说明谁批准、为什么仍是同一件事')
    no_extra = cost.get('问题追加', '—') == '—' and cost.get('工具追加', '—') == '—'
    if no_extra and reason not in ('', '—'):
        rep.fail('L08', '没有追加额度，但「追加理由」写了内容，两者矛盾')

    for key in ('开始', '结束'):
        if cost.get(key, '') in ('', '—'):
            rep.fail('L08', 'grill.md 成本字段「%s」未填，成本基线无法比较' % key)
    start, finish = cost.get('开始', ''), cost.get('结束', '')
    if start and finish and start > finish:
        rep.fail('L08', 'grill.md 结束时间早于开始时间')
    rep.ok('L08')


def _int_or_none(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _allowance(rep: Report, label: str, raw: str) -> int:
    """解析追加额度：只接受 `—`、`+4`、`+8`。返回 0 表示没有追加。"""
    value = raw.strip()
    if value in ('', '—'):
        return 0
    match = re.fullmatch(r'\+(\d+)', value)
    if match is None:
        rep.fail('L08', '%s 只能写 `—` 或 `+4` / `+8`，实际「%s」' % (label, value))
        return 0
    extra = int(match.group(1))
    if extra % 4 or extra > 8:
        rep.fail('L08', '%s 是 %s，只允许 +4 或 +8（每次 +4，最多两次，第三次必须拆）' % (label, value))
        return 0
    return extra


def check_matrix(rep: Report, text: str) -> None:
    """L09 必做维度齐全；状态合法；不适用有理由；待决状态与问题双向对应。"""
    section = section_named(text, '覆盖矩阵')
    if section is None:
        rep.fail('L09', 'grill.md 缺「## 覆盖矩阵」一节')
        return
    rows = record_rows(rep, 'L09', section, ('维度', '状态', '依据'))
    rows.extend((row.group(1), clean_cell(row.group(2)), clean_cell(row.group(3)))
                for row in table_rows(section, r'[A-Z]\d'))
    for raw_dim, status, basis in rows:
        match = re.match(r'^([A-Z]\d)(?:\s|$)', raw_dim)
        dim = match.group(1) if match else raw_dim
        if not match:
            rep.fail('L09', '覆盖矩阵维度「%s」必须以维度 ID 开头' % raw_dim)
        if dim in rep.matrix_status:
            rep.fail('L09', '覆盖矩阵重复记录维度 %s' % dim)
        rep.matrix_status[dim] = status
        if status not in MATRIX_STATUS:
            rep.fail('L09', '%s 的状态「%s」不在 %s 内' % (dim, status, ' / '.join(MATRIX_STATUS)))
        if status == '不适用' and basis in ('', '—'):
            rep.fail('L09', '%s 标了「不适用」但没有给理由' % dim)
    if rep.spec_type in REQUIRED_DIMS:
        expected = set(REQUIRED_DIMS[rep.spec_type])
        actual = set(rep.matrix_status)
        for dim in sorted(expected - actual):
            rep.fail('L09', '覆盖矩阵缺必做维度 %s' % dim)
        for dim in sorted(actual - expected):
            rep.fail('L09', '覆盖矩阵多出 %s 型不要求的维度 %s' % (rep.spec_type, dim))
    required = set(REQUIRED_DIMS.get(rep.spec_type, ()))
    pending_required = set(rep.pending_dims) & required
    matrix_pending = {dim for dim, status in rep.matrix_status.items() if status == '待决'}
    for dim in sorted(pending_required - matrix_pending):
        rep.fail('L09', '第 7 节将必做维度 %s 列为待决，覆盖矩阵必须标为「待决」' % dim)
    for dim in sorted(matrix_pending - set(rep.pending_dims)):
        rep.fail('L09', '覆盖矩阵将 %s 标为「待决」，但第 7 节没有对应问题' % dim)
    rep.ok('L09')


def check_touch(rep: Report, text: str) -> None:
    """L10 规范触碰清单必须存在；冲突项不许留在第 7 节。"""
    section = section_named(text, '规范触碰')
    if section is None:
        rep.fail('L10', 'grill.md 缺「## 规范触碰」一节（没有触碰也要写「无」）')
        return
    rows = record_rows(rep, 'L10', section, ('条款', '状态', '依据'))
    rows.extend((row.group(1), clean_cell(row.group(2)), clean_cell(row.group(3)))
                for row in table_rows(section, STANDARDS_ID))
    placeholders = _placeholder_rows(section)
    if placeholders:
        rep.fail('L10', '「规范触碰」还有 %d 行未填写的模板占位，请填写或删除' % placeholders)
    if not rows and not placeholders and not _says_none(section):
        rep.fail('L10', '「规范触碰」清单为空，且没有写「无」')
    seen = set()
    for code, status, basis in rows:
        if not re.fullmatch(STANDARDS_ID, code):
            rep.fail('L10', '规范条款编号「%s」无效或仍是占位' % code)
        if code in seen:
            rep.fail('L10', '规范触碰重复记录条款 %s' % code)
        seen.add(code)
        if status not in TOUCH_STATUS:
            rep.fail('L10', '%s 的状态「%s」不在 %s 内' % (code, status, ' / '.join(TOUCH_STATUS)))
        if status == '冲突' and '§7' in basis:
            rep.fail('L10', '%s 存在冲突，但依据指向第 7 节；请在访谈中解决并记录决定' % code)
    rep.ok('L10')


def _placeholder_rows(section: str) -> int:
    """首格还带尖括号的表格行数，即模板占位没填。"""
    count = 0
    for line in _COMMENT.sub('', section).split('\n'):
        if not line.lstrip().startswith('|'):
            continue
        cells = line.split('|')
        if len(cells) > 2 and '<' in cells[1]:
            count += 1
    return count


def _says_none(section: str) -> bool:
    """表格之外有没有一行显式写了「无」。"""
    for line in _COMMENT.sub('', section).split('\n'):
        text = line.strip()
        if text and not text.startswith('|') and '无' in text:
            return True
    return False


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
        prog='sdd_lint.py',
        description='检查 sdd-requirement 的 spec.md 与 grill.md 是否符合固定格式和规则',
    )
    parser.add_argument('spec_dir', help='spec 目录，如 specs/pNN-NNN-<slug>')
    args = parser.parse_args(argv)
    _use_utf8_stdout()

    spec_path = os.path.join(args.spec_dir, 'spec.md')
    grill_path = os.path.join(args.spec_dir, 'grill.md')
    missing = [path for path in (spec_path, grill_path) if not os.path.isfile(path)]
    if missing:
        sys.stderr.write('缺少 %s\n' % ' 或 '.join(missing))
        return 2

    rep = Report()
    spec_text = _read(spec_path)
    check_spec(rep, spec_text)
    check_spec_path(rep, args.spec_dir, spec_text)
    check_grill(rep, _read(grill_path))
    return rep.report(args.spec_dir)


if __name__ == '__main__':
    sys.exit(main())
