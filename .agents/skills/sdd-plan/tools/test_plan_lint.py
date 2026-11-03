#!/usr/bin/env python3
"""合法样本与变异回归；测试在内存中修改计划，不修改磁盘文件。"""
import contextlib
import importlib.util
import io
import re
from pathlib import Path
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
MODULE = importlib.util.spec_from_file_location("plan_lint", TOOLS / "plan_lint.py")
lint = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(lint)
READY = TOOLS / "fixtures/specs/p00-901-demo-plan-ready"
DRAFT = TOOLS / "fixtures/specs/p00-900-demo-plan-readable"


class PlanLintTests(unittest.TestCase):
    def run_plan(self, text=None, directory=READY):
        original = lint._read

        def read(path):
            if text is not None and Path(path).name == "plan.md":
                return text
            return original(path)

        output = io.StringIO()
        with patch.object(lint, "_read", side_effect=read), contextlib.redirect_stdout(output):
            code = lint.main([str(directory)])
        return code, output.getvalue()

    def ready(self):
        return (READY / "plan.md").read_text(encoding="utf-8")

    def assert_rejected(self, text, rule):
        code, output = self.run_plan(text)
        self.assertEqual(code, 1, output)
        self.assertIn("FAIL  " + rule, output)

    def test_positive_states(self):
        for directory, text in ((DRAFT, None), (READY, None),
                                (READY, self.ready().replace("`design-ok`", "`approved`"))):
            with self.subTest(directory=directory, approved=text is not None):
                code, output = self.run_plan(text, directory)
                self.assertEqual(code, 0, output)

    def test_legacy_and_mixed_labels(self):
        aliases = (
            ("用户会看到的变化", "你会看到什么"),
            ("需要用户决定的事项", "需要你拍板"),
            ("需要用户确认的例外", "需要你同意"),
            ("Agent 遵循的既有规范", "我自己照做"),
        )
        for directory in (DRAFT, READY):
            original = (directory / "plan.md").read_text(encoding="utf-8")
            variants = [original.replace(new, old) for new, old in aliases]
            legacy = original
            for new, old in aliases:
                legacy = legacy.replace(new, old)
            for text in variants + [legacy]:
                with self.subTest(directory=directory, text=text):
                    code, output = self.run_plan(text, directory)
                    self.assertEqual(code, 0, output)

    def test_no_decisions_new_and_legacy(self):
        original = self.ready()
        start = original.index("| 覆盖 [docs/standards/coding.md]")
        end = original.index("\n", start)
        text = original[:start] + original[end:]
        text = text.replace("**需要用户决定的事项**：见 2.1 的 1 条。", "**无需用户决定**。")
        for label in ("无需用户决定", "无需你拍板"):
            with self.subTest(label=label):
                code, output = self.run_plan(text.replace("无需用户决定", label))
                self.assertEqual(code, 0, output)

    def test_legacy_decision_checks_remain_active(self):
        for label in ("需要用户决定的事项", "需要你拍板"):
            text = self.ready().replace("**需要用户决定的事项**：见 2.1 的 1 条。", "**%s**：\n\n1. 确认产物格式。" % label)
            self.assert_rejected(text, "L10")
        for label in ("无需用户决定", "无需你拍板"):
            text = self.ready().replace("**需要用户决定的事项**：见 2.1 的 1 条。", "**%s**。" % label)
            self.assert_rejected(text, "L10")

    def test_visible_quotes_do_not_leak_into_later_sections(self):
        for visible in ("用户会看到的变化", "你会看到什么"):
            for pitch in ("需要用户决定的事项", "需要你拍板"):
                text = self.ready().replace("用户会看到的变化", visible).replace("需要用户决定的事项", pitch)
                text = text.replace("| R1 | 同目录下多出一个 |", "| R1 | 见 2.1 的 1 条。 |")
                self.assert_rejected(text, "L11")

    def test_visible_quotes_stop_at_any_standalone_heading(self):
        for heading in ("**怎么做到**", "**实现方式**", "**这样安排的原因**",
                        "**代价**", "**代价与放弃**", "**其他说明**", "### 补充说明"):
            with self.subTest(heading=heading):
                text = self.ready().replace("**怎么做到**", heading)
                text = text.replace("同目录下多出一个 `report.tsv`", "会生成报告文件")
                text = text.replace(heading + "：", heading + "：同目录下多出一个。")
                self.assert_rejected(text, "L11")

    def test_visible_list_emphasis_and_blank_lines_are_legal(self):
        text = self.ready().replace("- 跑一次导入命令，", "- **运行结果**：跑一次导入命令，")
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_visible_continuation_emphasis_is_legal(self):
        text = self.ready().replace("- 跑一次导入命令，同目录下多出一个", "- 跑一次导入命令，\n  **运行结果**：同目录下多出一个")
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_empty_visible_section_does_not_consume_next_heading(self):
        text = self.ready()
        start = text.index("- 跑一次导入命令，")
        end = text.index("**怎么做到**")
        text = text[:start] + text[end:]
        text = text.replace("**怎么做到**：", "**实现方式**：同目录下多出一个，第一列是出错的行内容。")
        self.assert_rejected(text, "L11")

    def test_generic_clause_identifiers_and_ranges(self):
        cases = (
            ("REPORT-01 FORM-02", ["REPORT-01", "FORM-02"]),
            ("UI-98–UI-100", ["UI-98", "UI-99", "UI-100"]),
            ("REPORT-01–REPORT-03", ["REPORT-01", "REPORT-02", "REPORT-03"]),
            ("FORM-03–01", ["FORM-01", "FORM-02", "FORM-03"]),
            ("DATA-ACCESS-1–DATA-ACCESS-3", ["DATA-ACCESS-1", "DATA-ACCESS-2", "DATA-ACCESS-3"]),
            ("UI-01–FSD-03", ["UI-01", "FSD-03"]),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(lint.clause_ids(text), expected)

    def test_generic_override_conflicts_are_rejected(self):
        for prefix in ("REPORT", "FORM", "DATA-ACCESS", "UI", "FSD"):
            with self.subTest(prefix=prefix):
                text = self.ready().replace("FSD-04", prefix + "-02")
                text = text.replace("FSD-01–FSD-03", prefix + "-01–" + prefix + "-03")
                self.assert_rejected(text, "L04")
                qualified = text.replace("三行文件头、需求锚点、镜像测试。", "仅沿用文件头要求。")
                code, output = self.run_plan(qualified)
                self.assertEqual(code, 0, output)

    def test_missing_risks_in_both_delivery_states(self):
        for state in ("design-ok", "approved"):
            text = self.ready().replace("`design-ok`", "`%s`" % state)
            self.assert_rejected(text.split("## 6.")[0] + "## 6. 风险与回滚\n", "L08")

    def test_missing_crosscheck(self):
        text = self.ready()
        self.assert_rejected(text[:text.index("**对证**")], "L08")

    def test_pending_crosscheck_is_not_claimed_as_semantic_pass(self):
        text = self.ready()
        code, output = self.run_plan(text[:text.index("**对证**")] + "**对证**：未运行\n")
        self.assertEqual(code, 0, output)

    def test_empty_verification(self):
        text = self.ready()
        text = text.replace("`flutter test test/report_test.dart`：跑完同目录出现报告文件。", "—")
        self.assert_rejected(text, "L06")

    def test_placeholder_verification(self):
        text = self.ready().replace("`flutter test test/report_test.dart`：跑完同目录出现报告文件。", "<验证命令>")
        self.assert_rejected(text, "L06")

    def test_incomplete_verification_row(self):
        text = self.ready().replace("| R1 | T1 | `flutter test test/report_test.dart`：跑完同目录出现报告文件。 | — |", "| R1 | T1 |")
        self.assert_rejected(text, "L06")

    def test_unlisted_paths(self):
        for path in ("src/unlisted.py", "cmd/main.go", "package.json", ".env", "Makefile", "文档/验收 数据.txt"):
            with self.subTest(path=path):
                text = self.ready().replace("  - 改动：新建 `lib/report.dart`", "  - 改动：新建 `%s`、`lib/report.dart`" % path)
                self.assert_rejected(text, "L05")

    def test_generic_listed_paths(self):
        for path in ("src/report.py", "cmd/main.go", "package.json", ".gitignore", "Makefile", "文档/验收 数据.txt"):
            with self.subTest(path=path):
                text = self.ready().replace("lib/report.dart", path)
                code, output = self.run_plan(text)
                self.assertEqual(code, 0, output)

    def test_multiple_paths_in_one_inventory_cell(self):
        text = self.ready().replace("| `lib/report.dart` |", "| `lib/report.dart`、`src/helper.py` |")
        text = text.replace("  - 改动：新建 `lib/report.dart`", "  - 改动：新建 `src/helper.py`、`lib/report.dart`")
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_missing_backticks(self):
        self.assert_rejected(self.ready().replace("  - 改动：修改 `test/report_test.dart`", "  - 改动：修改 test/report_test.dart"), "L05")

    def test_noncanonical_paths(self):
        for path in ("../escape.py", "/tmp/code.py", "src//x.py", "src/./x.py", "src/*.py", "C:/code.py"):
            with self.subTest(path=path):
                self.assert_rejected(self.ready().replace("lib/report.dart", path), "L05")

    def test_override_decision_source_need_not_repeat_override(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                with self.subTest(fixed_fields=fixed_fields, state=state):
                    text = self.new_format() if fixed_fields else self.ready()
                    text = text.replace('`design-ok`', '`%s`' % state)
                    text = text.replace('- 来源：覆盖', '- 来源：Agent 自定') if fixed_fields else text.replace(
                        '| 覆盖 | 下一个需要表格产物的 spec |',
                        '| Agent 自定 | 下一个需要表格产物的 spec |')
                    code, output = self.run_plan(text)
                    self.assertEqual(code, 0, output)

    def reference_only_plan(self, fixed_fields, state):
        """保留 2.1 的覆盖例外，3.2 仅引用它，不重复选择与放弃。"""
        text = self.new_format() if fixed_fields else self.ready()
        text = text.replace('`design-ok`', '`%s`' % state)
        start = text.index('### 3.2')
        end = text.index('### 3.3', start)
        return text[:start] + '### 3.2 决策\n\n- 沿用第 2.1 节的报告格式例外，无新增取舍。\n\n' + text[end:]

    def test_override_reference_without_new_decision_is_legal(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                with self.subTest(fixed_fields=fixed_fields, state=state):
                    code, output = self.run_plan(self.reference_only_plan(fixed_fields, state))
                    self.assertEqual(code, 0, output)

    def test_override_reference_still_requires_exception_reason(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                with self.subTest(fixed_fields=fixed_fields, state=state):
                    text = self.reference_only_plan(fixed_fields, state)
                    self.assert_rejected(text.replace('使用方按制表符解析', ''), 'L04')

    def test_override_reference_still_requires_judgable_return_condition(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                for condition in lint.VAGUE_DECAY:
                    with self.subTest(fixed_fields=fixed_fields, state=state, condition=condition):
                        text = self.reference_only_plan(fixed_fields, state)
                        self.assert_rejected(text.replace('下一个需要表格产物的 spec', condition), 'L04')

    def test_override_reference_still_requires_valid_override_target(self):
        target = '[docs/standards/coding.md](<../../docs/standards/coding.md>) FSD-04'
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                for invalid in ('通用格式要求', 'docs/standards/missing.md REPORT-01'):
                    with self.subTest(fixed_fields=fixed_fields, state=state, invalid=invalid):
                        text = self.reference_only_plan(fixed_fields, state)
                        self.assertIn(target, text)
                        self.assert_rejected(text.replace(target, invalid, 1), 'L04')

    def test_explicit_decisions_require_all_fields(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                for index, field in enumerate(lint.DECISION_FIELDS):
                    for missing in (False, True):
                        with self.subTest(fixed_fields=fixed_fields, state=state,
                                          field=field, missing=missing):
                            text = self.new_format() if fixed_fields else self.ready()
                            text = text.replace('`design-ok`', '`%s`' % state)
                            start = text.index('### 3.2')
                            end = text.index('### 3.3', start)
                            decision = text[start:end]
                            if fixed_fields:
                                decision = re.sub(r'^- %s：[^\n]*' % field,
                                                  '' if missing else '- %s：' % field,
                                                  decision, flags=re.MULTILINE)
                            else:
                                row = next(line for line in decision.splitlines() if line.startswith('| 产物格式 |'))
                                cells = row.split('|')
                                if missing:
                                    del cells[index + 1]
                                else:
                                    cells[index + 1] = ' '
                                decision = decision.replace(row, '|'.join(cells))
                            self.assert_rejected(text[:start] + decision + text[end:], 'L08')

    def test_empty_decision_subsection_in_both_delivery_states(self):
        for fixed_fields in (False, True):
            for state in ('design-ok', 'approved'):
                with self.subTest(fixed_fields=fixed_fields, state=state):
                    text = self.reference_only_plan(fixed_fields, state)
                    text = text.replace('- 沿用第 2.1 节的报告格式例外，无新增取舍。', '')
                    self.assert_rejected(text, 'L08')

    def test_empty_design_subsection(self):
        text = self.ready().replace("不引入依赖，不改 `analysis_options.yaml`。", "")
        self.assert_rejected(text, "L08")

    def test_invalid_inventory_row(self):
        text = self.ready().replace("| `lib/report.dart` |", "| lib/report.dart |")
        self.assert_rejected(text, "L05")

    def test_manual_only_verification_is_legal(self):
        text = self.ready().replace("| `flutter test test/report_test.dart`：跑完同目录出现报告文件。 | — |", "| — | 准备三行输入，以命令入口运行，打开同目录报告确认文件存在。 |")
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def new_format(self, directory=READY):
        """在内存中将测试样本转换为固定字段记录。"""
        text = (directory / 'plan.md').read_text(encoding='utf-8')
        schemas = iter((('Spec', 'Status'), ('R', '落点'), lint.AGREE_FIELDS,
                        lint.FOLLOW_FIELDS, lint.DECISION_FIELDS, lint.FILE_FIELDS,
                        lint.COVERAGE_FIELDS, lint.RISK_FIELDS))

        def convert(match):
            fields = next(schemas)
            rows = lint.grid_rows(match[0])
            if fields == ('Spec', 'Status'):
                return '\n'.join('- %s：%s' % tuple(row) for row in rows) + '\n'
            records = []
            for index, row in enumerate(rows, 1):
                if fields == lint.FOLLOW_FIELDS:
                    row = ['[docs/standards/coding.md](<../../docs/standards/coding.md>)',
                           'FSD-01–FSD-03', '三行文件头、需求锚点、镜像测试。']
                records.append('#### 记录%d\n\n%s\n' % (index, '\n'.join(
                    '- %s：%s' % pair for pair in zip(fields, row))))
            return '\n'.join(records)

        text = re.sub(r'^- `docs/standards/coding.md`[^\n]*\n', '', text, flags=re.MULTILINE)
        return re.sub(r'(?:^\|[^\n]*\n)+', convert, text, flags=re.MULTILINE)

    def test_new_format_positive_states(self):
        for directory, status in ((DRAFT, 'draft'), (READY, 'design-ok'), (READY, 'approved')):
            with self.subTest(status=status):
                text = self.new_format(directory).replace('`design-ok`', '`%s`' % status)
                code, output = self.run_plan(text, directory)
                self.assertEqual(code, 0, output)

    def test_new_format_preserves_pipes_backticks_and_continuations(self):
        text = self.new_format().replace(
            '- 自动验证：`flutter test test/report_test.dart`：跑完同目录出现报告文件。',
            '- 自动验证：`flutter test | tee report.log`：跑完同目录出现报告文件。\n'
            '  同时检查 `report.tsv`，内容包含 a|b。')
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)
        rows = lint.record_rows('#### 测试\n- 命令：`a | b`\n  继续 `c|d`\n', ('命令',))
        self.assertEqual(rows, [['`a | b`\n继续 `c|d`']])

    def test_new_format_missing_and_duplicate_fields(self):
        for field, value, rule in (
            ('这次要打破什么', '覆盖 docs/standards/coding.md FSD-04', 'L04'),
            ('出处', 'docs/standards/coding.md', 'L04'),
            ('决策', '产物格式', 'L08'), ('文件', '`lib/report.dart`', 'L05'),
            ('自动验证', '`run | check`', 'L06'), ('风险', '报告不完整', 'L08'),
            ('落点', '同目录下多出一个', 'L11')):
            with self.subTest(field=field):
                text = self.new_format()
                self.assert_rejected(re.sub(r'^- %s：[^\n]*\n' % field, '', text,
                                            count=1, flags=re.MULTILINE), rule)
                self.assert_rejected(text.replace('- %s：' % field,
                                     '- %s：%s\n- %s：' % (field, value, field), 1), rule)

    def test_new_format_duplicate_header_and_files(self):
        text = self.new_format()
        self.assert_rejected(text.replace('- Status：', '- Status：`draft`\n- Status：'), 'L01')
        self.assert_rejected(text.replace('#### 记录2\n\n- 文件：`test/report_test.dart`',
                                         '#### 记录2\n\n- 文件：`lib/report.dart`'), 'L05')

    def test_new_format_cross_mapping_still_checked(self):
        text = self.new_format()
        self.assert_rejected(text.replace('- 任务：T1', '- 任务：T2'), 'L06')
        self.assert_rejected(text.replace('- 任务：T1', '- 任务：T1、T2'), 'L06')
        self.assert_rejected(text.replace('  - 覆盖：R1', '  - 覆盖：R2\n  - 覆盖：R1'), 'L05')
        self.assert_rejected(text.replace('FSD-01–FSD-03', 'FSD-01–FSD-04'), 'L04')
        self.assert_rejected(text.replace('- 落点：同目录下多出一个', '- 落点：与实际显示不一致'), 'L11')
        self.assert_rejected(text.replace('  - 改动：新建 `lib/report.dart`',
                                         '  - 改动：新建 `lib/unknown.dart`'), 'L05')

    def test_new_format_unknown_fields_and_missing_record_heading(self):
        text = self.new_format()
        self.assert_rejected(text.replace('- 操作：新建', '- 行为：新建', 1), 'L05')
        self.assert_rejected(text.replace('#### 记录1\n\n- 风险：', '- 风险：'), 'L08')
        self.assert_rejected(text.replace('#### 记录1\n\n- 出处：', '- 出处：'), 'L04')

    def test_new_format_manual_only_and_no_exception(self):
        text = self.new_format()
        text = re.sub(r'^- 自动验证：[^\n]*$', '- 自动验证：—', text, flags=re.MULTILINE)
        text = text.replace('- 手工步骤：—', '- 手工步骤：运行入口后打开报告，核对文件与两列内容。')
        start = text.index('#### 记录1', text.index('### 2.1'))
        end = text.index('### 2.2', start)
        text = text[:start] + '无。\n\n' + text[end:]
        text = text.replace('**需要用户决定的事项**：见 2.1 的 1 条。', '**无需用户决定**。')
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_actual_template_filled_as_draft(self):
        text = (TOOLS.parent / 'templates/plan.md').read_text(encoding='utf-8')
        text = lint._COMMENT.sub('', text)
        text = text[:text.index('## 3. 设计')] + '\n'.join(
            '## %d. %s\n' % (number, title) for number, title in (
                (3, '设计'), (4, '任务'), (5, 'R → 验证'), (6, '风险与回滚')))
        replacements = {
            '<spec slug>': 'demo-plan-ready', 'pNN-NNN-<slug>': READY.name,
            '<默认状态下的具体结果>': '跑一次导入命令，同目录下多出一个 report.tsv。',
            '<其他状态或操作产生的具体差别>': '第一列是出错的行内容，第二列是失败原因。',
            '<数据从哪来、谁处理、状态和边界在哪里>': '命令读入并解析记录，结束时写报告。',
            '<相比放弃的做法，实际减少或增加什么工作>': '全部读完再写出，避免留下半份报告。',
            '<需要付出什么、哪些只能手工判断>': '需要在内存中保留整份结果。',
            '<照抄“用户会看到的变化”中的 6–20 字>': '同目录下多出一个',
            '无 —— 见「代价」段': '第一列是出错的行内容',
            '<例外名称>': '报告格式',
            '<覆盖 docs/standards/report.md REPORT-01，或仅本次等>':
                '覆盖 docs/standards/coding.md FSD-04：使用 TSV',
            '<具体理由>': '使用方按制表符读取', '<可判断的条件>': '下一个报告需求',
            '<规范主题>': '文件头', 'docs/standards/<name>.md': 'docs/standards/coding.md',
            '<条款号>': 'FSD-01–FSD-03', '<本次适用的要求及范围>': '文件头与需求锚点。',
        }
        for before, after in replacements.items():
            text = text.replace(before, after)
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_default_decision_plain_item_is_legal(self):
        text = self.new_format()
        start = text.index('### 3.2')
        end = text.index('### 3.3', start)
        text = text[:start] + '### 3.2 决策\n\n- 默认使用现有命令入口，不增加新取舍。\n\n' + text[end:]
        exception_start = text.index('#### 记录1', text.index('### 2.1'))
        exception_end = text.index('### 2.2', exception_start)
        text = text[:exception_start] + '无。\n\n' + text[exception_end:]
        text = text.replace('**需要用户决定的事项**：见 2.1 的 1 条。', '**无需用户决定**。')
        code, output = self.run_plan(text)
        self.assertEqual(code, 0, output)

    def test_forward_dependency(self):
        self.assert_rejected(self.ready().replace("  - 依赖：—", "  - 依赖：T2"), "L05")


if __name__ == "__main__":
    unittest.main(verbosity=2)
