"""13장 보안 자동화 프로젝트의 입력·집계·원본 보존 계약."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


EXAMPLES = Path(__file__).parents[1] / "examples" / "13-python-automate"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


integrity = load_module("file_integrity")
report = load_module("security_report")


class IntegrityTests(unittest.TestCase):
    def test_cli_detects_changes_and_preserves_baseline(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            base = Path(temporary)
            root = base / "target"
            root.mkdir()
            for name in ("modified", "deleted", "unchanged"):
                (root / name).write_text("before")
            baseline = base / "baseline.json"
            args = [str(root), "--baseline", str(baseline)]
            self.assertEqual(integrity.main(["baseline", *args]), 0)
            original = baseline.read_bytes()
            self.assertEqual(integrity.main(["check", *args]), 0)
            (root / "modified").write_text("after")
            (root / "deleted").unlink()
            (root / "added").write_bytes(b"")
            output = base / "changes.json"
            self.assertEqual(integrity.main(["check", *args, "--output", str(output)]), 2)
            self.assertEqual(json.loads(output.read_text()), {
                "added": ["added"], "deleted": ["deleted"],
                "modified": ["modified"], "unchanged": ["unchanged"],
            })
            self.assertEqual(integrity.main(["baseline", *args]), 1)
            self.assertEqual(baseline.read_bytes(), original)
            self.assertEqual((root / "modified").read_text(), "after")
            result_bytes = output.read_bytes()
            self.assertEqual(integrity.main(["check", *args, "--output", str(output)]), 1)
            self.assertEqual(output.read_bytes(), result_bytes)

    def test_invalid_scope_and_baseline_fail(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary) / "target"
            root.mkdir()
            baseline = Path(temporary) / "baseline.json"
            self.assertEqual(integrity.main(["baseline", str(root), "--baseline", str(root / "self.json")]), 1)
            for text in ("broken", "[]", json.dumps({"version": 1, "root": str(root), "sha256": {"a": "bad"}})):
                baseline.write_text(text)
                self.assertEqual(integrity.main(["check", str(root), "--baseline", str(baseline)]), 1)
            self.assertEqual(integrity.main(["baseline", str(root / "missing"), "--baseline", str(baseline)]), 1)

    def test_nested_files_and_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "nested" / "empty").write_bytes(b"")
            self.assertEqual(integrity.snapshot(root), {
                "nested/empty": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            })
            try:
                (root / "link").symlink_to(root / "nested", target_is_directory=True)
            except OSError:
                self.skipTest("symlink unavailable")
            with self.assertRaises(ValueError):
                integrity.snapshot(root)


class SecurityReportTests(unittest.TestCase):
    def test_sample_counts_and_error_preservation(self):
        records, issues, digest = report.load_checks(EXAMPLES / "sample_security_checks_with_errors.csv")
        self.assertEqual(len(digest), 64)
        self.assertEqual([item[0] for item in issues], [7, 8, 9, 10])
        self.assertEqual(report.summarize(records, issues), {
            "검증 통과 행": 5, "입력 오류 행": 4, "pass": 1,
            "fail": 2, "review": 1, "na": 1, "high 미흡": 2,
        })
        self.assertIn("2026-13-01", json.loads(issues[0][2])["date"])

    def test_empty_missing_fields_and_all_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.csv"
            for content in ("", "date,asset\n"):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    report.load_checks(path)
            header = ",".join(report.COLUMNS) + "\n"
            path.write_text(header)
            records, issues, _ = report.load_checks(path)
            self.assertEqual((records, issues), ([], []))
            path.write_text(header + "2026-09-01,lab,CFG-001,high\n")
            records, issues, _ = report.load_checks(path)
            self.assertEqual((len(records), len(issues)), (0, 1))
            self.assertIn("열 수 불일치", issues[0][1])

    def test_workbook_text_counts_and_exit_codes(self):
        from openpyxl import load_workbook

        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            base = Path(temporary)
            path = base / "input.csv"
            path.write_text(",".join(report.COLUMNS) + "\n2026-09-01,=2+3,CFG-001,high,fail,@note\n")
            original = path.read_bytes()
            output = base / "report.xlsx"
            args = [str(path), "--output", str(output)]
            self.assertEqual(report.main(args), 0)  # fail is a valid result
            workbook = load_workbook(output)
            self.assertEqual(workbook["점검 결과"]["B2"].value, "=2+3")
            self.assertEqual(workbook["점검 결과"]["B2"].data_type, "s")
            self.assertEqual(workbook["점검 결과"]["F2"].value, "@note")
            workbook.close()
            original_output = output.read_bytes()
            self.assertEqual(report.main(args), 1)
            self.assertEqual(output.read_bytes(), original_output)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(report.main([
                str(EXAMPLES / "sample_security_checks_with_errors.csv"),
                "--output", str(base / "errors.xlsx"),
            ]), 2)
            records, issues, _ = report.load_checks(EXAMPLES / "sample_security_checks_with_errors.csv")
            report.verify_workbook(base / "errors.xlsx", records, issues)


if __name__ == "__main__":
    unittest.main()
