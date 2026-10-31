#!/usr/bin/env python3
"""sdd-grill 阶段闸门的机械校验。

用法：
    python .agents/skills/sdd-grill/tools/sdd_lint.py <spec 目录>

校验项：

    L01  头部六项字段齐全且取值合法，Spec 编号与目录名一致（类型 / Status / 上游）
    L02  第 1–7 节标题齐全
    L03  R 编号连续、不重复、不超过 12 条
    L04  每条 R 有「反例」与「可观察证据」，范畴取值合法
    L05  第 5 节每条「不做」带「理由：」
    L06  第 7 节每条待决问题带「维度：<ID>」与 A / B 两个选项
    L07  头部「附带交付」与 R 上的范畴标记互相登记
    L08  成本表十一项齐全、预算与型匹配、追加合法、用量不超授权
    L09  覆盖矩阵维度集合 = 本型必做集合；不适用带理由；不许自证
    L10  规范触碰清单存在；冲突项不许留在第 7 节

只校验可判定的形状。判断性内容（R 写得对不对、取舍是否成立）不在这里，
脚本也给不出。

退出码：0 全过 / 1 有 FAIL / 2 用法错误或文件缺失。

脚本随本 skill 分发，纯标准库、Python 3.8+，不依赖被审项目的语言、框架或构建系统。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# ─── 形状常量 ────────────────────────────────────────────────────────────────
#
# 这些是本 skill 自己的规则，与 ../rules/dimensions.md 逐字对应，改一处必须同步另一处。

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
MATRIX_STATUS = ('已覆盖', '不适用', '已推翻并说明')
TOUCH_STATUS = ('无冲突', '冲突', '不涉及')

# 成本表必须有十一行，顺序不限，缺一行就 FAIL。
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
    """单元格取值：去空白与反引号。

    模板习惯给取值加反引号（`` `已覆盖` ``），手写时又不加。判值前统一剥掉，
    否则「已覆盖」和 `` `已覆盖` `` 会被当成两个不同的值——模板会过不了自己的闸门。
    """
    return raw.replace('`', '').strip()


def key_value_rows(text: str) -> Dict[str, str]:
    """收集只有两格的表格行，用于 spec.md 头部表格与 grill.md 的成本表。"""
    out: Dict[str, str] = {}
    for line in text.split('\n'):
        match = _ROW2.match(line)
        if not match:
            continue
        key = clean_cell(match.group(1))
        if not key.replace('-', ''):
            continue  # |---|---| 分隔行
        out[key] = clean_cell(match.group(2))
    return out


def header_fields(text: str) -> Dict[str, str]:
    """取 `## 1.` 之前的头部表格。"""
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
    """按「首格是 ID、后两格是状态与依据」解析三列表格行。

    首格的反引号可有可无——模板里写成 `` `D1` ``，手写时常常不带，两种都必须认。
    """
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
    head = header_fields(text)
    check_head(rep, head)
    sections = split_sections(text)
    for index in range(1, 8):
        if index not in sections:
            rep.fail('L02', 'spec.md 缺第 %d 节（## %d. ...）' % (index, index))
    rep.ok('L02')
    check_rs(rep, sections.get(4, ''))
    check_scope_out(rep, sections.get(5, ''))
    check_pending(rep, sections.get(7, ''))
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
        rep.fail('L01', 'spec.md 头部已移除批准凭据字段，请删除旧字段；批准只以用户明确确认记录在 Status')
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
                rep.fail('L04', '%s 的「%s」是空的' % (rid, field))
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
    for rid in rep.tagged_rs:
        if rid not in listed:
            rep.fail('L07', '%s 标了范畴，但没登记进「附带交付」，plan 看不到它' % rid)
    rep.ok('L07')


# ─── grill.md：L08–L10 ───────────────────────────────────────────────────────


def check_grill(rep: Report, text: str) -> None:
    """成本基线、覆盖矩阵、规范触碰，与 spec.md 的类型和第 7 节交叉核对。"""
    check_cost(rep, text)
    check_matrix(rep, text)
    check_touch(rep, text)


def check_cost(rep: Report, text: str) -> None:
    """L08 成本表十一项齐全、预算与型匹配、追加合法、用量不超授权。"""
    cost = key_value_rows(text)
    for key in COST_KEYS:
        if key not in cost:
            rep.fail('L08', 'grill.md 成本表缺「%s」' % key)

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
            rep.fail('L08', '问题上限写的是 %d，按必做维度推应为 %d' % (limit, expected_limit))
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
        rep.fail('L08', '有追加额度却没写「追加理由」——没有理由的追加等于静默放宽上限')
    no_extra = cost.get('问题追加', '—') == '—' and cost.get('工具追加', '—') == '—'
    if no_extra and reason not in ('', '—'):
        rep.fail('L08', '没有追加额度，但「追加理由」写了内容，两者矛盾')

    for key in ('开始', '结束'):
        if cost.get(key, '') in ('', '—'):
            rep.fail('L08', 'grill.md 成本表「%s」未填，成本基线无法比较' % key)
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
    """L09 维度集合等于本型必做集合；状态合法；不适用带理由；不许自证。"""
    section = section_named(text, '覆盖矩阵')
    if section is None:
        rep.fail('L09', 'grill.md 缺「## 覆盖矩阵」一节')
        return
    for row in table_rows(section, r'[A-Z]\d'):
        dim, status, basis = row.group(1), clean_cell(row.group(2)), clean_cell(row.group(3))
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
    for dim in rep.pending_dims:
        if rep.matrix_status.get(dim) == '已覆盖':
            rep.fail('L09', '第 7 节把 %s 列为待决，矩阵却写「已覆盖」——覆盖矩阵在自证' % dim)
    rep.ok('L09')


def check_touch(rep: Report, text: str) -> None:
    """L10 规范触碰清单必须存在；冲突项不许留在第 7 节。"""
    section = section_named(text, '规范触碰')
    if section is None:
        rep.fail('L10', 'grill.md 缺「## 规范触碰」一节（没有触碰也要写「无」）')
        return
    rows = table_rows(section, STANDARDS_ID)
    placeholders = _placeholder_rows(section)
    if placeholders:
        rep.fail('L10', '「规范触碰」还留着 %d 行模板占位，没有真填' % placeholders)
    if not rows and not placeholders and not _says_none(section):
        rep.fail('L10', '「规范触碰」清单为空，且没有写「无」')
    for row in rows:
        code, status, basis = row.group(1), clean_cell(row.group(2)), clean_cell(row.group(3))
        if status not in TOUCH_STATUS:
            rep.fail('L10', '%s 的状态「%s」不在 %s 内' % (code, status, ' / '.join(TOUCH_STATUS)))
        if status == '冲突' and '§7' in basis:
            rep.fail('L10', '%s 标了冲突却留在第 7 节——冲突必须进访谈，不许留给审阅人' % code)
    rep.ok('L10')


def _placeholder_rows(section: str) -> int:
    """首格还带尖括号的表格行数，即模板占位没填。"""
    count = 0
    for line in section.split('\n'):
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
        description='sdd-grill 阶段闸门：机械校验 spec.md 与 grill.md',
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
