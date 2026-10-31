#!/usr/bin/env python3
"""sdd-plan 阶段闸门的机械校验。

用法：
    python3 .agents/skills/sdd-plan/tools/plan_lint.py <spec 目录>

校验项：

    L01  头部两项齐全、无版本控制字段；Spec 可解析且与目录名一致；spec 版本与状态对得上 plan 的声明
    L02  第 1–6 节结构；Status=draft 时第 3–6 节必须为空（闸门 A 未过）
    L03  方案摘要非空、不超过 30 行、有「需要你拍板」或「无需你拍板」
    L04  约束表：非空、四格、去向合法、来源里的路径真实存在；去向为「覆盖」时写明覆盖了哪一条
    L05  任务：编号连续、四行齐全、验证可执行
    L06  覆盖：spec 每条 R 恰好一次，且指向真实任务，与任务的「覆盖」互洽
    L07  全文没有 TBD / 待定 / 稍后 / 视情况 这类空洞词
    L08  阻断态：有「回 spec」「先补约定」时不得 approved；approved 时设计与风险非空，
         且「覆盖」必须对应一条带失效条件的决策
    L09  spec 第 7 节还有待决项时，plan 不得存在

只校验可判定的形状。方案好不好、任务拆得对不对，脚本给不出。
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

# 约束的去向。`覆盖` 是正常做法，但必须留痕：写明被覆盖的条款，并在决策表里给出失效条件。
# 后两个是阻断态：出现时这份 plan 不能进 approved。
ALLOWED_TARGETS = ('既有', '覆盖', '回 spec', '先补约定', '仅本次')
BLOCKING_TARGETS = ('回 spec', '先补约定')

# 空洞词：出现即视为没写完。
VAGUE_WORDS = ('TBD', 'TODO', '待定', '稍后', '视情况', '酌情')

TOTAL_RULES = 9

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
_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
_SEP_CELL = re.compile(r'^:?-{2,}:?$')
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


def header_fields(text: str) -> Dict[str, str]:
    """取 `## 1.` 之前的头部表格。"""
    cut = text.find('\n## 1.')
    return key_value_rows(text if cut < 0 else text[:cut])


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
                'plan.md 头部不要写「%s」——提交前拿不到 SHA，填它必然过期；回滚写在风险表的「应对」里' % key,
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
                    'Status=draft 时第 %d 节必须为空——方案摘要还没过人确认，不许先写设计与任务' % index,
                )
    rep.ok('L02')


def check_summary(rep: Report, section: str) -> None:
    """L03 方案摘要：非空、不超行、有拍板栏。"""
    lines = body_lines(section)
    if not lines:
        rep.fail('L03', '第 1 节方案摘要是空的')
        return
    if len(lines) > SUMMARY_MAX_LINES:
        rep.fail('L03', '方案摘要 %d 行，超过 %d 行——摘要是给人 2 分钟读完的' % (len(lines), SUMMARY_MAX_LINES))
    text = _COMMENT.sub('', section)
    if '需要你拍板' not in text and '无需你拍板' not in text:
        rep.fail('L03', '第 1 节缺「需要你拍板」或「无需你拍板」，人不知道要不要表态')
    rep.ok('L03')


def check_constraints(rep: Report, section: str, plan_dir: str) -> None:
    """L04 约束表：非空、四格、去向合法、来源路径存在。"""
    rows = grid_rows(section)
    if not rows:
        rep.fail('L04', '第 2 节约束表没有数据行——没有约束的 plan 说明预研没做')
        return
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(plan_dir)))
    for number, cells in enumerate(rows, 1):
        if len(cells) != 4:
            rep.fail('L04', '第 2 节第 %d 行有 %d 格，应为 约束 / 来源 / 影响 / 去向 四格' % (number, len(cells)))
            continue
        source, target = clean_cell(cells[1]), clean_cell(cells[3])
        impact = clean_cell(cells[2])
        if target not in ALLOWED_TARGETS:
            rep.fail(
                'L04',
                '第 2 节第 %d 行去向「%s」不在 %s 内' % (number, target, ' / '.join(ALLOWED_TARGETS)),
            )
        else:
            rep.targets.append(target)
            if target == '覆盖':
                _check_override(rep, number, impact, repo_root, plan_dir)
        if not clean_cell(cells[0]):
            rep.fail('L04', '第 2 节第 %d 行约束为空' % number)
        for rel in _MD_PATH.findall(source):
            if not _path_exists(repo_root, plan_dir, rel):
                rep.fail('L04', '第 2 节第 %d 行的来源「%s」不存在——引用了一份不存在的规范' % (number, rel))
    rep.ok('L04')


def _check_override(rep: Report, number: int, impact: str, repo_root: str, plan_dir: str) -> None:
    """去向为 `覆盖` 时，影响格必须写明被覆盖的条款，且该条款真的存在。

    允许"更具体覆盖更一般"，但覆盖必须是可核对的：写了覆盖谁，谁就得在那儿。
    """
    hit = re.search(r'覆盖\s*[:：]?\s*(.+)$', impact)
    if hit is None:
        rep.fail(
            'L04',
            '第 2 节第 %d 行标了「覆盖」，但「影响」格没写覆盖了哪一条（形如 `覆盖 docs/standards/ui.md UI-01`）'
            % number,
        )
        return
    target = hit.group(1).strip()
    paths = _MD_PATH.findall(target)
    if not paths and not re.search(r'spec\s*§\s*\d+', target):
        rep.fail(
            'L04',
            '第 2 节第 %d 行的被覆盖对象「%s」既不是文档路径也不是 `spec §N`' % (number, target[:40]),
        )
    for rel in paths:
        if not _path_exists(repo_root, plan_dir, rel):
            rep.fail('L04', '第 2 节第 %d 行声明的被覆盖文档「%s」不存在' % (number, rel))


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


# ─── plan.md：L05–L06、L08–L09 ───────────────────────────────────────────────


def check_tasks(rep: Report, section: str) -> None:
    """L05 任务编号连续、四行齐全、验证可执行。"""
    blocks = task_blocks(section)
    if not blocks:
        rep.fail('L05', '第 4 节没有任何任务（`- [ ] **T1** ...`）')
        return
    for index, (tid, block) in enumerate(blocks, 1):
        rep.task_ids.append(tid)
        if tid != index:
            rep.fail('L05', '任务编号不连续：第 %d 条是 T%d' % (index, tid))
        for field in TASK_FIELDS:
            hit = re.search(r'^\s*-\s*%s[：:]\s*(.*)$' % field, block, re.MULTILINE)
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
    rep.ok('L05')


def check_coverage(rep: Report, section5: str, section4: str) -> None:
    """L06 R 覆盖完整、只出现一次、任务号真实、与任务「覆盖」互洽。"""
    rows = grid_rows(section5)
    seen: Dict[str, int] = {}
    for number, cells in enumerate(rows, 1):
        if not cells or not re.fullmatch(r'R\d+', clean_cell(cells[0])):
            rep.fail('L06', '第 5 节第 %d 行首格必须是 R 编号' % number)
            continue
        rid = clean_cell(cells[0])
        seen[rid] = seen.get(rid, 0) + 1
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
        for rid in claimed:
            if tid not in rep.coverage.get(rid, []):
                rep.fail('L06', 'T%d 声称覆盖 %s，但第 5 节 %s 的验证行没指向 T%d' % (tid, rid, rid, tid))
    rep.ok('L06')


def check_blocking(rep: Report, sections: Dict[int, str]) -> None:
    """L08 阻断态：去向阻塞时不得 approved；approved 时设计、文件、风险非空；覆盖要有决策。"""
    blocked = [target for target in rep.targets if target in BLOCKING_TARGETS]
    if blocked and rep.status == 'approved':
        rep.fail(
            'L08',
            '第 2 节有「%s」，这份 plan 不能标 approved——先解决它，再定稿' % '、'.join(sorted(set(blocked))),
        )
    if rep.status == 'approved':
        for index, label in ((3, '设计'), (6, '风险与回滚')):
            if not body_lines(sections.get(index, '')):
                rep.fail('L08', 'approved 时第 %d 节（%s）不能为空' % (index, label))
        design_rows = grid_rows(sections.get(3, ''))
        if not design_rows:
            rep.fail('L08', 'approved 时第 3 节必须有决策表或影响文件表')
        if '覆盖' in rep.targets:
            _check_override_decisions(rep, sections.get(3, ''))
    rep.ok('L08')


def _check_override_decisions(rep: Report, design: str) -> None:
    """第 2 节声明了 `覆盖`，第 3.2 节就得有来源为 `覆盖` 的决策，且失效条件可判断。"""
    rows = grid_rows(split_subsections(design).get('3.2', ''))
    overrides = [row for row in rows if len(row) > 5 and clean_cell(row[4]) == '覆盖']
    if not overrides:
        rep.fail(
            'L08',
            '第 2 节有「覆盖」去向，但第 3.2 节没有来源为 `覆盖` 的决策——覆盖要写清理由与何时失效',
        )
        return
    for row in overrides:
        decay = clean_cell(row[5])
        if decay in ('', '—', '-', '暂不', '永不', '长期'):
            rep.fail(
                'L08',
                '覆盖决策「%s」的「何时重评」不可判断（「%s」）——写清什么条件下回到通用规范'
                % (clean_cell(row[0]), decay),
            )


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
        description='sdd-plan 阶段闸门：机械校验 plan.md 与它对 spec.md 的承诺',
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
    check_head(rep, args.spec_dir, header_fields(plan_text), header_fields(spec_text))
    check_spec_rs(rep, spec_text)
    check_structure(rep, plan_text, sections)
    check_summary(rep, sections.get(1, ''))
    check_constraints(rep, sections.get(2, ''), args.spec_dir)
    check_blocking(rep, sections)
    check_spec_pending(rep, spec_text)
    check_vague(rep, plan_text)

    if rep.status == 'draft':
        rep.skip('L05', 'Status=draft：任务与覆盖在 design-ok 之后校验')
        rep.skip('L06', 'Status=draft：任务与覆盖在 design-ok 之后校验')
    else:
        check_tasks(rep, sections.get(4, ''))
        check_coverage(rep, sections.get(5, ''), sections.get(4, ''))

    return rep.report(args.spec_dir)


if __name__ == '__main__':
    sys.exit(main())
