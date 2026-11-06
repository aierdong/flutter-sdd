#!/usr/bin/env python3
"""检查 sdd-roadmap 路线图文档的固定格式和引用关系。

用法：
    python .agents/skills/sdd-roadmap/tools/sdd_lint.py specs/pNN-<slug>-roadmap.md
    python .agents/skills/sdd-roadmap/tools/sdd_lint.py specs          # 目录下恰好一份时自动选取

校验项：

    L01  头部四项字段齐全且取值合法；路线图编号与文件名一致
    L02  第 1–7 节标题齐全
    L03  第 1 节有整体目标；「整体不做」每条带理由
    L04  第 2 节四项齐全；验证方式、验证者取值合法
    L05  第 3 节每片字段齐全；slug 唯一；编号形状合法；交付证据有对应目录与 review.md
    L06  切片编号连续，且与第 4 节推进顺序一致
    L07  前置引用存在、不指向自己、不成环
    L08  路线外增补登记块字段齐全，附属编号存在
    L09  第 5 节每条约定字段齐全；覆盖切片编号存在
    L10  第 7 节验收状态与验收记录一致
    L11  没有残留占位符和空洞词

脚本只检查固定格式和可计算的关系。
人仍需判断切片切得对不对、整体完成条件是否可观察；脚本不能替代这些判断。

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

HEAD_FIELDS = ('路线图', '名称', 'Status', '版本')
HEAD_STATUS = ('draft', 'approved')
ACCEPT_STATUS = ('未验收', '已验收')
ACCEPT_RESULT = ('通过', '未通过')
SIGN_OFF = ('是', '否')
VERIFY_WAYS = ('用户手工走一遍', 'Agent 运行端到端命令', '用户走主路径，Agent 准备数据')
VERIFIERS = ('用户', 'Agent')

SECTION_TITLES = {
    1: '整体目标与边界',
    2: '整体完成条件',
    3: '切片清单',
    4: '依赖与顺序',
    5: '跨切片约定',
    6: '决策记录',
    7: '整体验收记录',
}

SLICE_KEYS = ('编号', 'slug', '解决什么问题', '做完后用户能', '前置')
EVIDENCE_KEY = '交付证据'
EXTRA_KEYS = ('编号', '附属于', '关系', '登记', '验证')
AGREEMENT_KEYS = ('要求', '覆盖切片', '留给各切片 plan 决定')
ACCEPT_KEYS = ('时间', '执行者', '实际路径', '结果', '未通过处')

TOTAL_RULES = 11

ROUTE_ID_SHAPE = re.compile(r'^p\d{2}$')
SLICE_ID_SHAPE = re.compile(r'^p\d{2}-\d{3}$')
SLUG_SHAPE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
VERSION_SHAPE = re.compile(r'^v\d+$')
VOID_WORDS = ('TBD', '待定', '稍后', '视情况')
PLACEHOLDER = re.compile(r'<[^<>\n]{1,60}>')

_SECTION = re.compile(r'^## (\d)\. .*$', re.MULTILINE)
_BLOCK = re.compile(r'^####[ \t]+(.+)$', re.MULTILINE)
_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
_FENCE = re.compile(r'^```.*?^```', re.DOTALL | re.MULTILINE)


# ─── 解析 ────────────────────────────────────────────────────────────────────


def strip_noise(text: str) -> str:
    """去掉 HTML 注释和代码块，避免占位符与示例干扰检查。"""
    return _COMMENT.sub('', _FENCE.sub('', text))


def clean(raw: str) -> str:
    """去掉反引号与两端空白，使带反引号和不带反引号的取值相同。"""
    return raw.replace('`', '').strip()


def field_pairs(text: str) -> List[Tuple[str, str]]:
    """读取固定字段行；值里的管道和括号不参与切分。"""
    pairs = []
    for line in strip_noise(text).splitlines():
        match = re.match(r'^-\s+([^：:]+)[：:]\s*(.*)$', line)
        if match:
            key = clean(match.group(1))
            if key:
                pairs.append((key, clean(match.group(2))))
    return pairs


def key_values(text: str) -> Dict[str, str]:
    return dict(field_pairs(text))


def check_fields(rep: Report, code: str, text: str,
                 keys: Tuple[str, ...], label: str,
                 optional: Tuple[str, ...] = ()) -> Dict[str, str]:
    """字段齐全、非空、不重复；optional 里的字段可有可无。"""
    fields: Dict[str, str] = {}
    wanted = tuple(keys) + tuple(optional)
    for key, value in field_pairs(text):
        if key in wanted:
            if key in fields:
                rep.fail(code, '%s 重复字段「%s」' % (label, key))
            fields[key] = value
    for key in keys:
        if key not in fields:
            rep.fail(code, '%s 缺字段「%s」' % (label, key))
        elif not fields[key]:
            rep.fail(code, '%s 字段「%s」为空' % (label, key))
    return fields


def blocks(section: str) -> List[Tuple[str, str]]:
    """按 `#### <标题>` 切出记录块，返回标题与正文。"""
    section = strip_noise(section)
    marks = list(_BLOCK.finditer(section))
    out = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(section)
        out.append((mark.group(1).strip(), section[mark.end():end]))
    return out


def header_of(text: str) -> str:
    """`## 1.` 之前的内容。"""
    cut = text.find('\n## 1.')
    return text if cut < 0 else text[:cut]


def split_sections(text: str) -> Dict[int, str]:
    body = strip_noise(text)
    out: Dict[int, str] = {}
    marks = list(_SECTION.finditer(body))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(body)
        out[int(mark.group(1))] = body[mark.end():end]
    return out


def leading_slice_id(raw: str) -> Optional[str]:
    """从「001（提供：……）」或「001」里取出三位编号。"""
    match = re.match(r'^(\d{3})\b', raw.strip())
    return match.group(1) if match else None


# ─── 结果容器 ────────────────────────────────────────────────────────────────


class Report:
    """收集校验结果，最后决定输出与退出码。"""

    def __init__(self) -> None:
        self.failures: List[str] = []
        self.checked: List[str] = []
        self.route_id = ''
        # 切片编号，按文档出现顺序。
        self.slice_ids: List[str] = []
        # 每片的前置编号，用于成环检查。
        self.pre_edges: Dict[str, Optional[str]] = {}

    def fail(self, code: str, message: str) -> None:
        self.failures.append('%s  %s' % (code, message))

    def ok(self, code: str) -> None:
        self.checked.append(code)

    def report(self, path: str) -> int:
        print('route-lint  %s' % path)
        if not self.failures:
            print('PASS  %d 项检查全部通过' % len(self.checked))
            return 0
        for item in self.failures:
            print('FAIL  %s' % item)
        print('%d 项不通过，共 %d 项检查' % (len(self.failures), TOTAL_RULES))
        return 1


# ─── L01–L02 头部与结构 ──────────────────────────────────────────────────────


def check_head(rep: Report, text: str, path: str) -> Dict[str, str]:
    """L01 头部四项齐全且合法，编号与文件名一致。"""
    head = check_fields(rep, 'L01', header_of(text), HEAD_FIELDS, '路线图头部')
    route = head.get('路线图', '')
    rep.route_id = route
    if not ROUTE_ID_SHAPE.fullmatch(route):
        rep.fail('L01', '路线图编号必须形如 pNN，实际「%s」' % route)
    name = os.path.basename(os.path.normpath(path))
    if route and not name.startswith('%s-' % route):
        rep.fail('L01', '文件名「%s」必须以路线图编号 %s 开头' % (name, route))
    if route and not name.endswith('-roadmap.md'):
        rep.fail('L01', '文件名「%s」必须以 -roadmap.md 结尾' % name)
    status = head.get('Status', '')
    if status and status not in HEAD_STATUS:
        rep.fail('L01', 'Status 必须是 draft / approved，实际「%s」' % status)
    version = head.get('版本', '')
    if version and not VERSION_SHAPE.fullmatch(version):
        rep.fail('L01', '版本必须形如 vN，实际「%s」' % version)
    for word in ('Approved', 'Approved-Tag'):
        if word in head:
            rep.fail('L01', '头部不得包含 %s；用户确认后只改 Status' % word)
    rep.ok('L01')
    return head


def check_sections(rep: Report, sections: Dict[int, str]) -> None:
    """L02 第 1–7 节齐全。"""
    for index, title in SECTION_TITLES.items():
        if index not in sections:
            rep.fail('L02', '缺第 %d 节（## %d. %s）' % (index, index, title))
    rep.ok('L02')


# ─── L03–L04 目标与完成条件 ──────────────────────────────────────────────────


def check_goal(rep: Report, section: str) -> None:
    """L03 整体目标非空；整体不做每条带理由。"""
    match = re.search(r'\*\*整体目标\*\*[：:]\s*(.+)', strip_noise(section))
    if match is None:
        rep.fail('L03', '第 1 节缺「**整体目标**：」')
    elif len(match.group(1).strip()) < 8:
        rep.fail('L03', '整体目标太短，写不出用户完整的一段经历')

    cut = re.search(r'\*\*整体不做\*\*[：:]', strip_noise(section))
    scope = strip_noise(section)[cut.end():] if cut else ''
    items = [line.strip() for line in scope.splitlines()
             if re.match(r'^-\s+\S', line) and clean(line)[1:] != '无']
    if not items:
        if '无' not in scope:
            rep.fail('L03', '第 1 节没有「整体不做」条目，也没有写「无」')
    for item in items:
        if '理由：' not in item and '理由:' not in item:
            rep.fail('L03', '「整体不做」条目缺「理由：」→ %s' % item)
    rep.ok('L03')


def check_acceptance_criteria(rep: Report, section: str) -> None:
    """L04 完成条件、操作路径、验证方式、验证者四项齐全且取值合法。"""
    keys = ('完成条件', '操作路径', '验证方式', '验证者')
    fields = check_fields(rep, 'L04', section, keys, '第 2 节')
    way = fields.get('验证方式', '')
    who = fields.get('验证者', '')
    if way and way not in VERIFY_WAYS:
        rep.fail('L04', '验证方式只能取 %s，实际「%s」' % (' / '.join(VERIFY_WAYS), way))
    if who and who not in VERIFIERS:
        rep.fail('L04', '验证者必须是 %s，实际「%s」' % (' / '.join(VERIFIERS), who))
    path = fields.get('操作路径', '')
    if path and len(path) < 6:
        rep.fail('L04', '操作路径至少要能看出起点和终态，实际「%s」' % path)
    rep.ok('L04')


# ─── L05–L08 切片、编号、前置、增补 ─────────────────────────────────────────


def check_slices(rep: Report, section: str) -> List[Dict[str, str]]:
    """L05 每片字段齐全、slug 唯一、编号形状合法、交付证据有据可查。"""
    rows = []
    seen_slug = set()
    for title, body in blocks(section):
        if not title.startswith('切片'):
            continue
        fields = check_fields(rep, 'L05', body, SLICE_KEYS, title, optional=(EVIDENCE_KEY,))
        slug = fields.get('slug', '')
        if slug:
            if not SLUG_SHAPE.fullmatch(slug):
                rep.fail('L05', '%s 的 slug 必须是小写英文短横线，实际「%s」' % (title, slug))
            if slug in seen_slug:
                rep.fail('L05', 'slug「%s」重复，切片必须能唯一落到目录名' % slug)
            seen_slug.add(slug)
        sid = fields.get('编号', '')
        if sid:
            if not SLICE_ID_SHAPE.fullmatch(sid):
                rep.fail('L05', '%s 的编号必须形如 pNN-NNN，实际「%s」' % (title, sid))
            elif rep.route_id and not sid.startswith(rep.route_id + '-'):
                rep.fail('L05', '%s 的编号「%s」与路线图 %s 不一致' % (title, sid, rep.route_id))
            rep.slice_ids.append(sid.split('-')[-1])
        elif rep.route_id:
            rep.slice_ids.append('')
        rows.append(fields)
    if not rows:
        rep.fail('L05', '第 3 节没有任何「#### 切片：<名称>」记录')
    rep.ok('L05')
    return rows


def check_evidence(rep: Report, rows: List[Dict[str, str]], path: str) -> None:
    """L05 写了交付证据的切片，必须有对应的 spec 目录和 review.md。

    路线图不记状态，交付与否只看这份证据；证据指不回真实文件时必须失败。
    """
    base = os.path.dirname(os.path.abspath(path))
    for fields in rows:
        evidence = fields.get(EVIDENCE_KEY, '')
        sid = fields.get('编号', '')
        if not evidence or not sid:
            continue
        dirs = [name for name in os.listdir(base)
                if name.startswith(sid + '-') and os.path.isdir(os.path.join(base, name))] \
            if os.path.isdir(base) else []
        if not dirs:
            rep.fail('L05', '%s 写了交付证据，但 %s 下没有 %s-* 目录' % (sid, base, sid))
            continue
        if not any(os.path.isfile(os.path.join(base, name, 'review.md')) for name in dirs):
            rep.fail('L05', '%s 写了交付证据，但对应目录里没有 review.md' % sid)


def check_numbers(rep: Report, rows: List[Dict[str, str]], section: str) -> None:
    """L06 编号按出现顺序连续，且与第 4 节推进顺序一致。"""
    expected = ['%03d' % index for index in range(1, len(rep.slice_ids) + 1)]
    if rep.slice_ids != expected:
        rep.fail('L06', '切片编号必须按出现顺序连续为 %s，实际 %s'
                 % ('、'.join(expected), '、'.join(rep.slice_ids) or '无'))
    match = re.search(r'推进顺序[：:]\s*(.+)', strip_noise(section))
    if match is None:
        rep.fail('L06', '第 4 节缺「- 推进顺序：」')
        rep.ok('L06')
        return
    listed = re.findall(r'\d{3}', match.group(1))
    if listed != rep.slice_ids:
        rep.fail('L06', '推进顺序 %s 与切片编号 %s 不一致；编号就是顺序，两处必须相同'
                 % ('、'.join(listed) or '无', '、'.join(rep.slice_ids) or '无'))
    rep.ok('L06')


def check_requires(rep: Report, rows: List[Dict[str, str]]) -> None:
    """L07 前置存在、不自指、不成环。"""
    known = set(rep.slice_ids)
    for fields in rows:
        sid = fields.get('编号', '')
        short = sid.split('-')[-1] if sid else ''
        raw = fields.get('前置', '')
        if not raw or raw in ('无', '—'):
            rep.pre_edges[short] = None
            continue
        pre = leading_slice_id(raw)
        if pre is None:
            rep.fail('L07', '%s 的前置「%s」既不是「无」，也没有以三位编号开头' % (sid, raw))
            rep.pre_edges[short] = None
            continue
        if '提供' not in raw:
            rep.fail('L07', '%s 的前置必须写明前一片提供了什么能力' % sid)
        if pre not in known:
            rep.fail('L07', '%s 的前置 %s 不在本路线图的切片里' % (sid, pre))
        if pre == short:
            rep.fail('L07', '%s 的前置不能指向自己' % sid)
        rep.pre_edges[short] = pre
    cycle = find_cycle(rep.pre_edges)
    if cycle:
        rep.fail('L07', '依赖成环：%s；请停下，交用户在合并切片和调整范围之间选择'
                 % ' → '.join(cycle))
    rep.ok('L07')


def find_cycle(edges: Dict[str, Optional[str]]) -> Optional[List[str]]:
    """沿前置指针走一趟，发现回到起点就返回环上的节点。"""
    for start in edges:
        seen: List[str] = []
        node: Optional[str] = start
        while node:
            if node in seen:
                return seen[seen.index(node):] + [node]
            seen.append(node)
            node = edges.get(node)
    return None


def check_extra(rep: Report, section: str) -> None:
    """L08 增补登记块字段齐全，附属编号存在；没有增补时不要求任何占位行。"""
    extra_blocks = [(title, body) for title, body in blocks(section)
                    if title.startswith('增补')]
    none_line = re.search(r'^-\s*路线外增补[：:]\s*(\S*)', strip_noise(section), re.MULTILINE)
    if extra_blocks and none_line:
        rep.fail('L08', '有增补登记块时，不要再写「- 路线外增补：」那一行')
    known = set(rep.slice_ids)
    for title, body in extra_blocks:
        fields = check_fields(rep, 'L08', body, EXTRA_KEYS, title)
        sid = fields.get('编号', '')
        if sid:
            if not SLICE_ID_SHAPE.fullmatch(sid):
                rep.fail('L08', '%s 的编号必须形如 pNN-NNN，实际「%s」' % (title, sid))
            elif sid.split('-')[-1] not in known:
                rep.fail('L08', '%s 的编号 %s 没有对应的路线内切片' % (title, sid))
        owner = fields.get('附属于', '')
        if owner and owner.split('-')[-1] not in known:
            rep.fail('L08', '%s 附属于 %s，该编号不在切片清单里' % (title, owner))
        sign = fields.get('登记', '')
        if sign and sign not in SIGN_OFF:
            rep.fail('L08', '%s 的登记只能写 %s，实际「%s」'
                     % (title, ' / '.join(SIGN_OFF), sign))
    rep.ok('L08')


# ─── L09–L11 约定、验收、空洞词 ─────────────────────────────────────────────


def check_agreements(rep: Report, section: str) -> None:
    """L09 每条约定字段齐全，覆盖切片编号存在。"""
    text = strip_noise(section)
    rows = [(title, body) for title, body in blocks(text) if title.startswith('约定')]
    if not rows:
        if '没有跨切片约定' not in text:
            rep.fail('L09', '第 5 节没有约定记录，也没有写「本次没有跨切片约定」')
        rep.ok('L09')
        return
    known = set(rep.slice_ids)
    for title, body in rows:
        fields = check_fields(rep, 'L09', body, AGREEMENT_KEYS, title)
        cover = fields.get('覆盖切片', '')
        for sid in re.findall(r'\d{3}', cover):
            if sid not in known:
                rep.fail('L09', '%s 覆盖的 %s 不在切片清单里' % (title, sid))
    rep.ok('L09')


def check_sign_off(rep: Report, section: str) -> None:
    """L10 验收状态与验收记录一致。"""
    text = strip_noise(section)
    status_match = re.search(r'^-\s*状态[：:]\s*(\S*)', text, re.MULTILINE)
    status = clean(status_match.group(1)) if status_match else ''
    if not status:
        rep.fail('L10', '第 7 节缺「- 状态：」')
    elif status not in ACCEPT_STATUS:
        rep.fail('L10', '验收状态只能是 %s，实际「%s」' % (' / '.join(ACCEPT_STATUS), status))
    records = [(title, body) for title, body in blocks(text) if title.startswith('整体验收记录')]
    if status == '未验收' and records:
        rep.fail('L10', '状态是「未验收」，却已有整体验收记录')
    if status == '已验收':
        if not records:
            rep.fail('L10', '状态是「已验收」，但没有「#### 整体验收记录」块')
        for title, body in records:
            fields = check_fields(rep, 'L10', body, ACCEPT_KEYS, title)
            result = fields.get('结果', '')
            gap = fields.get('未通过处', '')
            if result and result not in ACCEPT_RESULT:
                rep.fail('L10', '结果只能是 %s，实际「%s」'
                         % (' / '.join(ACCEPT_RESULT), result))
            if result == '通过' and gap not in ('-', '—'):
                rep.fail('L10', '结果为通过时，「未通过处」写 -')
            if result == '未通过' and gap in ('-', '—', ''):
                rep.fail('L10', '结果为未通过时，必须写明断在哪一步')
    rep.ok('L10')


def check_void(rep: Report, text: str) -> None:
    """L11 没有残留占位符和空洞词。"""
    clean_text = strip_noise(text)
    for word in VOID_WORDS:
        if word in clean_text:
            rep.fail('L11', '出现空洞词「%s」，请换成具体内容' % word)
    for hit in PLACEHOLDER.finditer(clean_text):
        rep.fail('L11', '残留占位符 %s' % hit.group(0))
    rep.ok('L11')


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


def resolve_path(raw: str) -> Optional[str]:
    """接受路线图文件，也接受只含一份路线图的目录。"""
    if os.path.isfile(raw):
        return raw
    if not os.path.isdir(raw):
        return None
    found = sorted(name for name in os.listdir(raw) if name.endswith('-roadmap.md'))
    if len(found) != 1:
        return None
    return os.path.join(raw, found[0])


def check_document(rep: Report, text: str, path: str) -> None:
    check_head(rep, text, path)
    sections = split_sections(text)
    check_sections(rep, sections)
    check_goal(rep, sections.get(1, ''))
    check_acceptance_criteria(rep, sections.get(2, ''))
    rows = check_slices(rep, sections.get(3, ''))
    check_evidence(rep, rows, path)
    check_numbers(rep, rows, sections.get(4, ''))
    check_requires(rep, rows)
    check_extra(rep, sections.get(3, ''))
    check_agreements(rep, sections.get(5, ''))
    check_sign_off(rep, sections.get(7, ''))
    check_void(rep, text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='sdd_lint.py',
        description='检查 sdd-roadmap 路线图的固定格式和引用关系',
    )
    parser.add_argument('path', help='路线图文件，如 specs/pNN-<slug>-roadmap.md')
    args = parser.parse_args(argv)
    _use_utf8_stdout()

    path = resolve_path(args.path)
    if path is None:
        sys.stderr.write('找不到路线图，或目录下不是恰好一份 *-roadmap.md：%s\n' % args.path)
        return 2

    rep = Report()
    check_document(rep, _read(path), path)
    return rep.report(path)


if __name__ == '__main__':
    sys.exit(main())
