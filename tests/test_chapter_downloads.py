"""장별 배포본의 독립성, 버전 변경 범위와 압축 해제 후 실행 경로를 검증한다."""

import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("chapter_downloads", ROOT / "scripts/build_chapter_downloads.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

# 저장소를 검색 경로에 넣지 않고 압축 해제한 노트북 폴더에서 실행한다.
RUN_NOTEBOOK = """
import json, pathlib, sys, types
notebook = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
module = types.ModuleType("packaged_notebook")
sys.modules[module.__name__] = module
cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
if len(sys.argv) > 2:
    cells = cells[:int(sys.argv[2])]
for index, cell in enumerate(cells, 1):
    exec(compile("".join(cell["source"]), f"cell-{index}", "exec"), module.__dict__)
"""


class ChapterDownloadsTests(unittest.TestCase):
    def test_manifests_match_archive_and_source(self):
        for chapter in builder.CHAPTERS:
            with self.subTest(chapter=chapter):
                data, record = builder.build_archive(chapter)
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
                source = builder.package_files(chapter)
                with ZipFile(BytesIO(data)) as archive:
                    self.assertIsNone(archive.testzip())
                    prefix = record["archive_root"] + "/"
                    manifest = json.loads(archive.read(prefix + "MANIFEST.json"))
                    self.assertEqual(set(manifest["files"]), set(source))
                    self.assertEqual(len(archive.namelist()), len(source) + 1)
                    for name, content in source.items():
                        self.assertEqual(archive.read(prefix + name), content)
                        self.assertEqual(hashlib.sha256(content).hexdigest(), manifest["files"][name]["sha256"])
                    self.assertEqual(data, builder.build_archive(chapter)[0])

    def test_required_dependencies_and_retired_materials(self):
        files05 = builder.package_files("05")
        self.assertIn("fixtures/05-text-processing/web-access.log", files05)
        self.assertIn("notebooks/solutions/05-9-web-log-analysis-solution.ipynb", files05)
        files08 = builder.package_files("08")
        self.assertIn("examples/07-local-web-security-lab/training_server.py", files08)
        for chapter in builder.CHAPTERS:
            names = "\n".join(builder.package_files(chapter))
            for excluded in ("03-9-auth-challenge", "13-python-automate/", "WhatWeb", "geoserver_test"):
                self.assertNotIn(excluded, names)

    def test_one_chapter_change_does_not_change_another(self):
        original = builder.package_files
        baseline01 = builder.build_archive("01")
        baseline02 = builder.build_archive("02")

        def changed_files(chapter):
            files = original(chapter)
            if chapter == "01":
                files["sample-note.txt"] = b"chapter 01 only"
            return files

        with patch.object(builder, "package_files", side_effect=changed_files):
            self.assertNotEqual(baseline01[1]["version"], builder.build_archive("01")[1]["version"])
            self.assertEqual(baseline02, builder.build_archive("02"))

    def test_notebooks_run_from_extracted_notebook_directory(self):
        # 05장 TODO 본문은 미완성 상태가 의도되어 있어 입력 경로를 준비하는 첫 셀만 실행한다.
        cases = {
            "04": [("04-9-file-analyzer.ipynb", None)],
            "05": [("05-1-normalization.ipynb", 1)],
            "06": [("06-8-echo-project.ipynb", None)],
            "08": [("08-4-safe-subprocess.ipynb", None)],
            "13": [("13-6-safe-file-organizer-project.ipynb", None),
                   ("13-7-spreadsheet-report-project.ipynb", None)],
        }
        for chapter, notebooks in cases.items():
            with self.subTest(chapter=chapter), tempfile.TemporaryDirectory(prefix="chapter-zip-test-") as directory:
                data, record = builder.build_archive(chapter)
                with ZipFile(BytesIO(data)) as archive:
                    archive.extractall(directory)
                notebook_dir = Path(directory) / record["archive_root"] / "notebooks"
                for filename, limit in notebooks:
                    args = [sys.executable, "-I", "-B", "-c", RUN_NOTEBOOK, filename]
                    if limit is not None:
                        args.append(str(limit))
                    result = subprocess.run(args, cwd=notebook_dir, capture_output=True, text=True, timeout=45)
                    self.assertEqual(result.returncode, 0, f"{filename}\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
