#!/usr/bin/env python3
"""Approve a spec: set Status/Approved-Tag, commit, and create an annotated tag.

This is a human-run helper for the approval step. It does not decide whether a
spec should be approved; the human runs it after review.

Usage:
    python3 .agents/skills/sdd-grill/tools/approve_spec.py specs/pNN-NNN-<slug>
    python3 .agents/skills/sdd-grill/tools/approve_spec.py specs/pNN-NNN-<slug> --yes
    python3 .agents/skills/sdd-grill/tools/approve_spec.py specs/pNN-NNN-<slug> --push

The script:
  1. runs sdd_lint.py on the spec;
  2. checks that Status is draft and Approved-Tag is —;
  3. sets Status: approved and Approved-Tag: spec/<pNN-NNN>/approved-v<N>;
  4. commits only spec.md (and optionally grill.md);
  5. creates the matching annotated tag.

It never pushes unless --push is given.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


HEADER_ROW = re.compile(r'^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$')
SPEC_ID = re.compile(r'^(p\d{2}-\d{3})-[a-z0-9-]+$')
VERSION = re.compile(r'^v\d+$')
TAG_NAME = re.compile(r'^spec/(p\d{2}-\d{3})/approved-v\d+$')


def die(message: str) -> None:
    print('error: ' + message, file=sys.stderr)
    raise SystemExit(1)


def git(root: Path, *args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['git', *args],
        cwd=root,
        text=True,
        capture_output=capture,
        check=check,
    )


def header_values(text: str) -> dict:
    head = text.split('\n## 1.', 1)[0]
    values = {}
    for line in head.splitlines():
        match = HEADER_ROW.match(line)
        if not match:
            continue
        key = match.group(1).strip()
        values[key] = match.group(2).strip().strip('`')
    return values


def replace_header(text: str, key: str, value: str) -> str:
    pattern = re.compile(r'^(\|\s*' + re.escape(key) + r'\s*\|\s*)(.*?)(\s*\|\s*)$', re.MULTILINE)
    replaced, count = pattern.subn(lambda match: '%s`%s`%s' % (match.group(1), value, match.group(3)), text, count=1)
    if count != 1:
        die('spec.md 头部找不到字段「%s」' % key)
    return replaced


def run_lint(spec_dir: Path, root: Path) -> None:
    lint = Path(__file__).resolve().with_name('sdd_lint.py')
    if not lint.is_file():
        die('找不到 sdd_lint.py：%s' % lint)
    result = subprocess.run([sys.executable, str(lint), str(spec_dir)], cwd=root, text=True)
    if result.returncode != 0:
        die('sdd_lint.py 未通过；先修 spec，再批准')


def tag_exists(root: Path, tag: str) -> bool:
    result = git(root, 'rev-parse', '--verify', 'refs/tags/' + tag, check=False)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description='批准一个 spec：改头、commit、打 annotated tag。')
    parser.add_argument('spec_dir', help='spec 目录，例如 specs/pNN-NNN-<slug>')
    parser.add_argument('--yes', action='store_true', help='跳过交互确认')
    parser.add_argument('--dry-run', action='store_true', help='只显示计划，不修改、不提交、不打 tag')
    parser.add_argument('--push', action='store_true', help='提交并打 tag 后执行 git push --follow-tags')
    parser.add_argument('--no-grill', action='store_true', help='不把 grill.md 放进批准 commit')
    parser.add_argument('--approver', default='', help='tag 消息里的批准人；默认取 git config user.name')
    parser.add_argument('--message', default='', help='commit message；默认 docs: <spec> 审核通过 <version>')
    parser.add_argument('--tag-message', default='', help='annotated tag 的消息')
    args = parser.parse_args()

    repo_result = git(Path.cwd(), 'rev-parse', '--show-toplevel', check=False)
    if repo_result.returncode != 0:
        die('当前目录不是 git 仓库')
    root = Path(repo_result.stdout.strip())
    spec_dir = Path(args.spec_dir).resolve()
    if not spec_dir.is_dir():
        die('spec 目录不存在：%s' % spec_dir)
    try:
        spec_dir.relative_to(root)
    except ValueError:
        die('spec 目录不在当前 git 仓库内：%s' % spec_dir)
    spec_path = spec_dir / 'spec.md'
    grill_path = spec_dir / 'grill.md'
    if not spec_path.is_file():
        die('缺少 spec.md：%s' % spec_path)

    # 批准前的 lint 先跑一遍；未通过的 spec 不得进入批准。
    run_lint(spec_dir, root)

    text = spec_path.read_text(encoding='utf-8')
    values = header_values(text)
    spec_id = values.get('Spec', '')
    version = values.get('版本', '')
    status = values.get('Status', '')
    approved_tag = values.get('Approved-Tag', '')

    if not SPEC_ID.match(spec_id):
        die('Spec 必须形如 pNN-NNN-<slug>，实际「%s」' % spec_id)
    if not VERSION.match(version):
        die('版本必须形如 vN，实际「%s」' % version)
    if 'Approved' in values:
        die('头部还有旧字段 Approved；本工具只支持 Approved-Tag')
    if status != 'draft':
        die('Status 必须是 draft，实际「%s」；已批准的 spec 先升版本再改回 draft' % status)
    if approved_tag not in ('', '—'):
        die('Approved-Tag 必须是「—」，实际「%s」' % approved_tag)

    prefix = SPEC_ID.match(spec_id).group(1)
    tag = 'spec/%s/approved-%s' % (prefix, version)
    if not TAG_NAME.match(tag):
        die('生成的 tag 名不合法：%s' % tag)
    if tag_exists(root, tag):
        die('tag 已存在：%s' % tag)

    approver = args.approver.strip()
    if not approver:
        name = git(root, 'config', 'user.name', check=False).stdout.strip()
        approver = name or 'unknown'
    message = args.message.strip() or 'docs: %s 审核通过 %s' % (spec_id, version)
    tag_message = args.tag_message.strip() or 'approved %s %s by %s' % (spec_id, version, approver)

    files = [str(spec_path.relative_to(root))]
    include_grill = not args.no_grill and grill_path.is_file()
    if include_grill:
        files.append(str(grill_path.relative_to(root)))

    staged = git(root, 'diff', '--cached', '--quiet', '--', *files, check=False)
    if staged.returncode != 0:
        die('这些文件已有 staged 改动；先 commit 或 unstage，再批准')

    print('Spec:        %s' % spec_id)
    print('Version:     %s' % version)
    print('Tag:         %s' % tag)
    print('Files:       %s' % ', '.join(files))
    print('Commit:      %s' % message)
    print('Tag message: %s' % tag_message)
    print('Header:      Status draft -> approved; Approved-Tag — -> %s' % tag)

    dirty = git(root, 'status', '--porcelain', '--', *files, check=False).stdout.strip()
    if dirty:
        print('注意：这些文件有未提交改动，将一并进入批准 commit：')
        print(dirty)
    if args.dry_run:
        print('dry-run：未修改、未提交、未打 tag。')
        return 0
    if not args.yes:
        answer = input('继续？[y/N] ').strip().lower()
        if answer not in ('y', 'yes'):
            print('已取消。')
            return 1

    sys.stdout.flush()
    new_text = replace_header(text, 'Status', 'approved')
    new_text = replace_header(new_text, 'Approved-Tag', tag)
    spec_path.write_text(new_text, encoding='utf-8')

    committed = False
    staged_by_script = False
    try:
        run_lint(spec_dir, root)
        git(root, 'add', '--', *files)
        staged_by_script = True
        commit = subprocess.run(
            ['git', 'commit', '-m', message, '--only', '--', *files],
            cwd=root,
            text=True,
        )
        if commit.returncode != 0:
            die('git commit 失败')
        committed = True
        sha = git(root, 'rev-parse', 'HEAD').stdout.strip()

        tag_result = subprocess.run(
            ['git', 'tag', '-a', tag, '-m', tag_message],
            cwd=root,
            text=True,
        )
        if tag_result.returncode != 0:
            print('commit 已创建，但 tag 创建失败。', file=sys.stderr)
            print('手动补 tag：git tag -a %s -m %s' % (tag, repr(tag_message)), file=sys.stderr)
            return 1

        print('已批准：%s %s' % (spec_id, version))
        print('commit: %s' % sha[:12])
        print('tag:    %s' % tag)

        if args.push:
            push = subprocess.run(['git', 'push', '--follow-tags'], cwd=root, text=True)
            if push.returncode != 0:
                print('push 失败；commit 与 tag 已在本地。可手动执行：git push --follow-tags', file=sys.stderr)
                return 1
            print('已 push：当前分支与 annotated tag')
        else:
            print('未 push；需要时执行：git push --follow-tags')
        return 0
    finally:
        if not committed:
            if staged_by_script:
                git(root, 'reset', '--', *files, check=False)
            spec_path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
