#!/usr/bin/env python3
"""使用独立的导入文件示例，检查 sdd-grill 的正反场景。"""

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name('sdd_lint.py')
MODULE_SPEC = importlib.util.spec_from_file_location('sdd_lint', MODULE_PATH)
lint = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(lint)


def documents(spec_type='new', pending_dim=None, matrix_status=None,
              status='draft', extra='—', tagged=False):
    """生成完整文档，不读取仓库里的历史 spec。"""
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
        '- [ ] **R1** 用户提交文件后，系统显示导入结果。\n'
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
            self.assertIn('PASS  10 项检查全部通过', output.getvalue())

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


if __name__ == '__main__':
    unittest.main()
