#!/usr/bin/env python3
"""使用独立的导入文件示例，检查 sdd-requirement 的正反场景。"""

import contextlib
import importlib.util
import io
import re
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name('sdd_lint.py')
MODULE_SPEC = importlib.util.spec_from_file_location('sdd_lint', MODULE_PATH)
lint = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(lint)


def documents(spec_type='new', pending_dim=None, matrix_status=None,
              status='draft', extra='—', tagged=False):
    """独立生成完整的测试文档。"""
    upstream = '—' if spec_type == 'new' else 'p99-900-import'
    tag = '  - **范畴**：doc\n' if tagged else ''
    pending = '本次无需你决定的事项。'
    if pending_dim:
        pending = (
            '1. 某行导入失败后，是否保留已成功的行？\n'
            '   - A. 保留已成功的行，用户可以先使用这些数据。\n'
            '   - B. 撤销整次导入，用户重新提交完整文件。\n'
            '   - 维度：`%s`\n' % pending_dim
        )
    spec = (
        '# 导入文件\n\n'
        '| 字段 | 值 |\n|---|---|\n'
        '| Spec | p99-901-import |\n'
        '| 类型 | %s |\n| 上游 | %s |\n'
        '| 附带交付 | %s |\n| Status | %s |\n| 版本 | v1 |\n'
        '\n## 1. 背景与问题\n用户需要导入文件。\n'
        '\n## 2. 目标\n用户可以看到导入结果。\n'
        '\n## 3. 用户场景\n用户选择文件并查看导入结果。\n'
        '\n## 4. 必须做到\n'
        '- **R1** 用户提交文件后，系统显示导入结果。\n'
        '%s'
        '  - **反例**：系统完成导入后仍显示空白。\n'
        '  - **可观察证据**：页面显示本次成功导入的行数。\n'
        '\n## 5. 明确不做\n'
        '- 不做报告编辑。理由：本次只处理文件导入。\n'
        '\n## 6. 风险与取舍\n用户选择手动提交文件。\n'
        '\n## 7. 审阅问题\n%s\n'
    ) % (spec_type, upstream, extra, status, tag, pending)
    matrix_status = matrix_status or {}
    matrix = '\n'.join(
        '| %s 访谈维度 | %s | %s |' % (
            dim, matrix_status.get(dim, '已覆盖'),
            '§7 第 1 题' if matrix_status.get(dim) == '待决' else 'R1 与 §5',
        )
        for dim in lint.REQUIRED_DIMS[spec_type]
    )
    grill = (
        '# 导入文件决策日志\n\n'
        '| 成本 | 值 |\n|---|---|\n'
        '| 类型 | %s |\n| 问题数 | 1 |\n| 问题上限 | %d |\n'
        '| 问题追加 | — |\n| 工具调用 | 1 |\n| 工具预算 | %d |\n'
        '| 工具追加 | — |\n| 追加理由 | — |\n'
        '| 开始 | 2026-01-01 10:00 |\n| 结束 | 2026-01-01 10:01 |\n'
        '| 重问 | 0 |\n'
        '\n## 规范触碰\n无\n'
        '\n## 覆盖矩阵\n| 维度 | 状态 | 依据 |\n|---|---|---|\n%s\n'
    ) % (spec_type, lint.question_limit(spec_type), lint.TOOL_BUDGET[spec_type], matrix)
    return spec, grill


class SddLintTest(unittest.TestCase):
    def check_documents(self, **kwargs):
        spec, grill = documents(**kwargs)
        rep = lint.Report()
        lint.check_spec(rep, spec)
        lint.check_grill(rep, grill)
        lint.check_route(rep, grill)
        return rep

    def assert_failure(self, rep, message):
        self.assertTrue(
            any(message in failure for failure in rep.failures), rep.failures,
        )

    def test_complete_documents_pass_for_each_type(self):
        for spec_type in lint.REQUIRED_DIMS:
            with self.subTest(spec_type=spec_type):
                rep = self.check_documents(spec_type=spec_type)
                self.assertEqual([], rep.failures)
                self.assertEqual(lint.TOTAL_RULES, len(rep.checked))

    def test_pending_question_and_matrix_pass_for_each_type(self):
        for spec_type in lint.REQUIRED_DIMS:
            with self.subTest(spec_type=spec_type):
                rep = self.check_documents(
                    spec_type=spec_type, pending_dim='D1', matrix_status={'D1': '待决'},
                )
                self.assertEqual([], rep.failures)

    def test_pending_question_requires_pending_matrix_status(self):
        for status in ('已覆盖', '不适用', '已推翻并说明'):
            with self.subTest(status=status):
                rep = self.check_documents(pending_dim='D1', matrix_status={'D1': status})
                self.assert_failure(rep, '覆盖矩阵必须标为「待决」')

    def test_pending_matrix_requires_question(self):
        rep = self.check_documents(matrix_status={'D1': '待决'})
        self.assert_failure(rep, '第 7 节没有对应问题')

    def test_different_pending_dimensions_fail_both_directions(self):
        rep = self.check_documents(pending_dim='D1', matrix_status={'D2': '待决'})
        self.assert_failure(rep, '必做维度 D1')
        self.assert_failure(rep, '覆盖矩阵将 D2')

    def test_approved_with_pending_question_fails(self):
        rep = self.check_documents(
            pending_dim='D1', matrix_status={'D1': '待决'}, status='approved',
        )
        self.assert_failure(rep, 'Status 不得为 approved')

    def test_approved_without_pending_question_passes(self):
        self.assertEqual([], self.check_documents(status='approved').failures)

    def test_pending_nonrequired_dimension_does_not_add_matrix_row(self):
        rep = self.check_documents(spec_type='fix', pending_dim='D2')
        self.assertEqual([], rep.failures)

    def test_registered_and_tagged_extra_passes(self):
        self.assertEqual([], self.check_documents(extra='R1', tagged=True).failures)

    def test_tagged_extra_requires_registration(self):
        self.assert_failure(self.check_documents(tagged=True), '请同时在头部「附带交付」登记')

    def test_registered_extra_requires_tag(self):
        self.assert_failure(self.check_documents(extra='R1'), '必须在第 4 节填写「**范畴**」')

    def test_registered_extra_must_exist(self):
        self.assert_failure(self.check_documents(extra='R2'), '引用了不存在的 R2')

    def test_entry_point_returns_zero_for_legal_pending(self):
        spec, grill = documents(pending_dim='D1', matrix_status={'D1': '待决'})
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'p99-901-import'
            folder.mkdir()
            (folder / 'spec.md').write_text(spec, encoding='utf-8')
            (folder / 'grill.md').write_text(grill, encoding='utf-8')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = lint.main([str(folder)])
            self.assertEqual(0, result)
            self.assertIn('PASS  %d 项检查全部通过' % lint.TOTAL_RULES, output.getvalue())

    def test_entry_point_returns_one_for_approved_pending(self):
        spec, grill = documents(
            pending_dim='D1', matrix_status={'D1': '待决'}, status='approved',
        )
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'p99-901-import'
            folder.mkdir()
            (folder / 'spec.md').write_text(spec, encoding='utf-8')
            (folder / 'grill.md').write_text(grill, encoding='utf-8')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = lint.main([str(folder)])
            self.assertEqual(1, result)
            self.assertIn('Status 不得为 approved', output.getvalue())


def field_documents(**kwargs):
    """根据独立测试样本生成固定字段行样本。"""
    spec, grill = documents(**kwargs)

    def fields(text):
        text = re.sub(r'^\| (?:字段|成本) \| 值 \|\n\|---\|---\|\n', '', text,
                      flags=re.MULTILINE)
        return re.sub(r'^\| ([^|]+?) \| ([^|]*?) \|$',
                      lambda m: '- %s：`%s`' % (m[1], m[2]), text, flags=re.MULTILINE)

    spec = fields(spec)
    grill = fields(grill)
    grill = grill.replace('| 维度 | 状态 | 依据 |\n|---|---|---|\n', '')
    grill = re.sub(
        r'^\| ([A-Z]\d) 访谈维度 \| ([^|]+) \| ([^|]+) \|$',
        lambda m: '#### 维度 %s\n- 维度：%s 访谈维度\n- 状态：%s\n- 依据：%s' %
        (m[1], m[1], m[2], m[3]), grill, flags=re.MULTILINE,
    )
    return spec, grill


TOUCH_RECORD = (
    '#### 规范 SEC-3\n- 条款：SEC-3\n- 状态：无冲突\n'
    '- 依据：docs/standards/security.md:12，日志不含密钥\n'
)


class FieldRecordTest(SddLintTest):
    def check_documents(self, **kwargs):
        return self.validate(*field_documents(**kwargs))

    def validate(self, spec, grill):
        rep = lint.Report()
        lint.check_spec(rep, spec)
        lint.check_spec_path(rep, 'p99-901-import', spec)
        lint.check_grill(rep, grill)
        lint.check_route(rep, grill)
        return rep

    def test_new_format_has_no_tables(self):
        for spec_type in lint.REQUIRED_DIMS:
            with self.subTest(spec_type=spec_type):
                spec, grill = field_documents(spec_type=spec_type)
                self.assertNotIn('|', spec + grill)
                self.assertIn('- Spec：`p99-901-import`', spec)
                self.assertEqual([], self.validate(spec, grill).failures)

    def test_pipe_values_are_preserved(self):
        spec, grill = field_documents()
        grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + TOUCH_RECORD)
        grill = grill.replace('R1 与 §5', '`R1 | §5 | 另一个依据`')
        grill = grill.replace('日志不含密钥', '日志使用 a|<b|c，命令为 `a | b`')
        grill = grill.replace('- 问题追加：`—`', '- 问题追加：`+4`')
        grill = grill.replace('- 追加理由：`—`', '- 追加理由：用户批准 a|b，仍为同一需求')
        self.assertEqual([], self.validate(spec, grill).failures)
        self.assertEqual('用户批准 a|b，仍为同一需求',
                         lint.key_value_rows(grill)['追加理由'])

    def test_missing_and_empty_fields(self):
        cases = (
            ('spec', '- 上游：`—`', 'L01'),
            ('grill', '- 重问：`0`', 'L08'),
            ('grill', '- 依据：R1 与 §5', 'L09'),
            ('grill', '- 条款：SEC-3', 'L10'),
            ('grill', '- 状态：无冲突', 'L10'),
            ('grill', '- 依据：docs/standards/security.md:12，日志不含密钥', 'L10'),
        )
        for target, line, code in cases:
            for replacement in ('', line.split('：')[0] + '：'):
                with self.subTest(target=target, line=line, replacement=replacement):
                    spec, grill = field_documents()
                    grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + TOUCH_RECORD)
                    if target == 'spec':
                        spec = spec.replace(line, replacement, 1)
                    else:
                        grill = grill.replace(line, replacement, 1)
                    self.assert_failure(self.validate(spec, grill), code)

    def test_every_header_cost_and_record_field_is_required(self):
        spec, grill = field_documents()
        for text, keys, code in (
            (spec, lint.BASE_HEAD_FIELDS, 'L01'),
            (grill, lint.COST_KEYS, 'L08'),
            (grill, ('维度', '状态', '依据'), 'L09'),
        ):
            for key in keys:
                for empty in (False, True):
                    with self.subTest(code=code, key=key, empty=empty):
                        changed = re.sub(r'^- ' + re.escape(key) + r'：[^\n]*',
                                         '- %s：``' % key if empty else '',
                                         text, count=1, flags=re.MULTILINE)
                        rep = self.validate(changed if code == 'L01' else spec,
                                            grill if code == 'L01' else changed)
                        self.assert_failure(rep, code)

    def test_duplicate_fields_fail_even_when_values_agree(self):
        for target, line, code in (
            ('spec', '- Spec：`p99-901-import`', 'L01'),
            ('grill', '- 类型：`new`', 'L08'),
            ('grill', '- 维度：D1 访谈维度', 'L09'),
            ('grill', '- 状态：已覆盖', 'L09'),
            ('grill', '- 条款：SEC-3', 'L10'),
            ('grill', '- 依据：docs/standards/security.md:12，日志不含密钥', 'L10'),
        ):
            with self.subTest(line=line):
                spec, grill = field_documents()
                grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + TOUCH_RECORD)
                if target == 'spec':
                    spec = spec.replace(line, line + '\n' + line, 1)
                else:
                    grill = grill.replace(line, line + '\n' + line, 1)
                rep = self.validate(spec, grill)
                self.assert_failure(rep, code)
                self.assert_failure(rep, '重复字段')

    def test_duplicate_records_and_titles_fail(self):
        spec, grill = field_documents()
        block = '#### 维度 另一个标题\n- 维度：D1\n- 状态：已覆盖\n- 依据：R1\n'
        self.assert_failure(self.validate(spec, grill + block), '重复记录维度 D1')
        block = block.replace('另一个标题', 'D1').replace('- 维度：D1', '- 维度：D2')
        self.assert_failure(self.validate(spec, grill + block), '重复记录标题')
        touch = TOUCH_RECORD + TOUCH_RECORD.replace('#### 规范 SEC-3', '#### 另一条规范')
        grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + touch)
        self.assert_failure(self.validate(spec, grill), '重复记录条款 SEC-3')

    def test_touch_status_conflict_and_placeholder_fail(self):
        for record, message in (
            (TOUCH_RECORD.replace('无冲突', '未知'), '状态'),
            (TOUCH_RECORD.replace('无冲突', '冲突').replace('日志不含密钥', '§7 再决定'),
             '依据指向第 7 节'),
            (TOUCH_RECORD.replace('SEC-3', '<SEC-3>'), '无效或仍是占位'),
        ):
            with self.subTest(message=message):
                spec, grill = field_documents()
                grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + record)
                self.assert_failure(self.validate(spec, grill), message)

    def test_missing_extra_and_invalid_dimensions_fail(self):
        for old, new, message in (
            ('- 维度：D1 访谈维度', '- 维度：Z9', '缺必做维度 D1'),
            ('- 维度：D1 访谈维度', '- 维度：Z9', '多出'),
            ('- 维度：D1 访谈维度', '- 维度：不是编号', '必须以维度 ID 开头'),
            ('- 状态：已覆盖', '- 状态：未知', '状态'),
            ('- 状态：已覆盖\n- 依据：R1 与 §5', '- 状态：不适用\n- 依据：—', '没有给理由'),
        ):
            with self.subTest(message=message):
                spec, grill = field_documents()
                self.assert_failure(self.validate(spec, grill.replace(old, new, 1)), message)

    def test_cost_fields_do_not_leak_from_later_records(self):
        spec, grill = field_documents()
        grill = grill.replace('- 重问：`0`\n', '') + '\n#### 其他记录\n- 重问：0\n'
        self.assert_failure(self.validate(spec, grill), '成本字段 缺字段「重问」')

    def test_mixed_legacy_and_new_duplicate_keys_fail(self):
        spec, grill = field_documents()
        spec = spec.replace('- 类型：`new`', '- 类型：`new`\n| 类型 | new |')
        grill += '| D1 访谈维度 | 已覆盖 | R1 |\n'
        rep = self.validate(spec, grill)
        self.assert_failure(rep, '重复字段「类型」')
        self.assert_failure(rep, '重复记录维度 D1')

    def test_comments_are_not_records_or_fields(self):
        spec, grill = field_documents()
        spec = spec.replace('## 1.', '<!--\n- 类型：fix\n-->\n## 1.', 1)
        grill += '\n<!--\n#### 未填写的说明\n- 维度：D1\n-->\n'
        self.assertEqual([], self.validate(spec, grill).failures)

    def test_fields_without_record_heading_fail(self):
        spec, grill = field_documents()
        grill = grill.replace('#### 维度 D1\n', '', 1)
        self.assert_failure(self.validate(spec, grill), '记录字段必须放在')

    def test_legacy_touch_table_remains_compatible(self):
        spec, grill = documents()
        table = ('| 条款 | 状态 | 依据 / 后果 |\n|---|---|---|\n'
                 '| SEC-3 安全 | 无冲突 | docs/standards/security.md:12 |\n')
        grill = grill.replace('## 规范触碰\n无', '## 规范触碰\n' + table)
        self.assertEqual([], self.validate(spec, grill).failures)
        self.assert_failure(self.validate(spec, grill.replace('无冲突', '错误状态')), '状态')

    def test_commented_legacy_touch_placeholder_is_ignored(self):
        spec, grill = field_documents()
        grill = grill.replace('## 规范触碰\n无',
                              '## 规范触碰\n无\n<!--\n| <STD-01> | 无冲突 | <依据> |\n-->')
        self.assertEqual([], self.validate(spec, grill).failures)

    def test_cost_allowances_and_limits(self):
        for old, new, message in (
            ('- 问题数：`1`', '- 问题数：`13`', '超过上限'),
            ('- 工具调用：`1`', '- 工具调用：`9`', '超过预算'),
            ('- 问题追加：`—`', '- 问题追加：`+3`', '只允许 +4 或 +8'),
            ('- 工具追加：`—`', '- 工具追加：`+4`', '说明谁批准'),
            ('- 类型：`new`', '- 类型：`fix`', '不一致'),
        ):
            with self.subTest(message=message):
                spec, grill = field_documents()
                self.assert_failure(self.validate(spec, grill.replace(old, new, 1)), message)

    def test_field_entry_point(self):
        for spec_type in lint.REQUIRED_DIMS:
            with self.subTest(spec_type=spec_type), tempfile.TemporaryDirectory() as root:
                spec, grill = field_documents(spec_type=spec_type)
                folder = Path(root) / 'p99-901-import'
                folder.mkdir()
                (folder / 'spec.md').write_text(spec, encoding='utf-8')
                (folder / 'grill.md').write_text(grill, encoding='utf-8')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, lint.main([str(folder)]))


class RouteTest(unittest.TestCase):
    """路线图与切片两个可选字段，以及日志里的对照记录。"""

    def build(self, route='p00', slice_id='003', verdict='一致',
              record_route=None, record_slice=None, section=True,
              definition='用户打开列表页并看到全部商品'):
        spec, grill = documents()
        if route is not None:
            head = '| 路线图 | %s |\n| 切片 | %s |\n' % (route, slice_id)
            spec = spec.replace('| 附带交付 |', head + '| 附带交付 |', 1)
        if section:
            grill += (
                '\n## 路线图对照\n\n'
                '#### 对照 1：商品列表页\n'
                '- 路线图：%s\n'
                '- 切片：%s\n'
                '- 切片定义：%s\n'
                '- 结论：%s\n'
            ) % (route if record_route is None else record_route,
                 slice_id if record_slice is None else record_slice,
                 definition, verdict)
        rep = lint.Report()
        lint.check_spec(rep, spec)
        lint.check_grill(rep, grill)
        lint.check_route(rep, grill)
        return rep

    def test_no_route_passes(self):
        self.assertEqual([], self.build(route=None, slice_id=None, section=False).failures)

    def test_route_and_slice_present(self):
        self.assertEqual([], self.build().failures)

    def test_two_fields_must_appear_together(self):
        rep = self.build(slice_id='—')
        self.assertTrue(any(item.startswith('L11') for item in rep.failures))

    def test_section_is_required(self):
        rep = self.build(section=False)
        self.assertTrue(any('路线图对照' in item for item in rep.failures))

    def test_scope_overrun_stops(self):
        rep = self.build(verdict='超出')
        self.assertTrue(any('修订路线图' in item for item in rep.failures))

    def test_record_must_match_head(self):
        rep = self.build(record_slice='004')
        self.assertTrue(any('不一致' in item for item in rep.failures))

    def test_no_route_needs_not_applicable(self):
        rep = self.build(route=None, slice_id=None, verdict='一致')
        self.assertTrue(any(item.startswith('L11') for item in rep.failures))

    def test_definition_must_be_copied(self):
        rep = self.build(definition='见路线图')
        self.assertTrue(any('照抄' in item for item in rep.failures))


if __name__ == '__main__':
    unittest.main()
