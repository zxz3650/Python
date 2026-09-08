"""날짜·시간 교안과 노트북의 KST 변환을 검증한다.

실행: python -m unittest discover -s tests -p test_datetime_lesson.py
"""

import ast
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEARNER = ROOT / "notebooks/05-6-datetime.ipynb"
SOLUTION = ROOT / "notebooks/solutions/05-6-datetime-solution.ipynb"


def code_cells(path):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]


def solution_namespace():
    namespace = {}
    with redirect_stdout(io.StringIO()):
        for source in code_cells(SOLUTION):
            exec(compile(source, str(SOLUTION), "exec"), namespace)
    return namespace


class DatetimeLessonTests(unittest.TestCase):
    def test_solution_and_kst_roundtrip(self):
        namespace = solution_namespace()
        value = namespace["parse_utc"]("2026-08-14T18:30:00Z")
        displayed = namespace["format_kst"](value)
        self.assertEqual(displayed, "2026-08-15T03:30:00+09:00")
        restored = datetime.fromisoformat(displayed)
        self.assertEqual(restored, value)
        self.assertEqual(restored.utcoffset(), timedelta(hours=9))
        self.assertEqual(restored.astimezone(timezone.utc), value)

    def test_learner_checks_accept_reference_functions(self):
        solution = solution_namespace()
        namespace = {}
        with redirect_stdout(io.StringIO()):
            for source in code_cells(LEARNER):
                if "TODO_DONE = False" in source:
                    namespace.update(
                        TODO_DONE=True,
                        parse_utc=solution["parse_utc"],
                        format_kst=solution["format_kst"],
                    )
                else:
                    exec(compile(source, str(LEARNER), "exec"), namespace)
        self.assertEqual(len(namespace["fixture_valid"]), 2)
        self.assertEqual(len(namespace["fixture_errors"]), 2)

    def test_learner_checks_reject_relabeling_utc_as_kst(self):
        solution = solution_namespace()
        namespace = {}
        cells = code_cells(LEARNER)
        with redirect_stdout(io.StringIO()):
            exec(cells[0], namespace)
        namespace.update(
            TODO_DONE=True,
            parse_utc=solution["parse_utc"],
            format_kst=lambda value: value.replace(
                tzinfo=solution["KST"]
            ).isoformat(),
        )
        with self.assertRaises(AssertionError):
            exec(cells[-1], namespace)

    def test_lesson_examples_execute_in_order(self):
        path = ROOT / "05-text-processing/05-6-datetime.md"
        blocks = re.findall(r"```python\n(.*?)\n```", path.read_text(), re.S)
        namespace = {}
        with redirect_stdout(io.StringIO()):
            for block in blocks:
                ast.parse(block)
                exec(compile(block, str(path), "exec"), namespace)
        self.assertEqual(namespace["day_bucket_kst"].isoformat(), "2026-08-15")
        self.assertEqual(namespace["hour_bucket_kst"].utcoffset(), timedelta(hours=9))

    def test_checked_in_notebooks_have_no_execution_artifacts(self):
        for path in (LEARNER, SOLUTION):
            notebook = json.loads(path.read_text())
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    self.assertIsNone(cell["execution_count"])
                    self.assertEqual(cell["outputs"], [])


if __name__ == "__main__":
    unittest.main()
