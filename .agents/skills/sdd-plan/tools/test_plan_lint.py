#!/usr/bin/env python3
"""合法样本与变异回归；测试只在内存中修改计划，不回写磁盘。"""
import contextlib
import importlib.util
import io
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

    def test_missing_override_decision_in_design_ok(self):
        self.assert_rejected(self.ready().replace("| 覆盖 | 下一个需要表格产物的 spec |", "| Agent 自定 | 下一个需要表格产物的 spec |"), "L08")

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

    def test_forward_dependency(self):
        self.assert_rejected(self.ready().replace("  - 依赖：—", "  - 依赖：T2"), "L05")


if __name__ == "__main__":
    unittest.main(verbosity=2)
