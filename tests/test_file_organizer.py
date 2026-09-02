import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "13-python-automate"
    / "file_organizer.py"
)
SPEC = importlib.util.spec_from_file_location("file_organizer", MODULE_PATH)
assert SPEC and SPEC.loader
file_organizer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = file_organizer
SPEC.loader.exec_module(file_organizer)


class FileOrganizerTests(unittest.TestCase):
    def test_build_plan_classifies_and_ignores_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "inbox"
            source.mkdir()
            (source / "PHOTO.JPG").write_bytes(b"image")
            (source / "report.pdf").write_bytes(b"pdf")
            (source / "events.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (source / "README").write_text("text", encoding="utf-8")
            (source / "nested").mkdir()

            operations = file_organizer.build_plan(source, source / "_organized")

            self.assertEqual(
                [operation.category for operation in operations],
                ["data", "images", "other", "documents"],
            )
            self.assertTrue(
                all("nested" not in operation.source for operation in operations)
            )

    def test_collision_gets_numbered_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "inbox"
            destination = source / "_organized"
            (destination / "images").mkdir(parents=True)
            (source / "photo.jpg").write_bytes(b"new")
            (destination / "images" / "photo.jpg").write_bytes(b"existing")

            operations = file_organizer.build_plan(source, destination)

            self.assertEqual(len(operations), 1)
            self.assertEqual(Path(operations[0].destination).name, "photo_2.jpg")

    def test_destination_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "inbox"
            destination = source / "_organized"
            outside = tmp_path / "outside"
            source.mkdir()
            destination.mkdir()
            outside.mkdir()
            (source / "photo.jpg").write_bytes(b"image")
            (destination / "images").symlink_to(
                outside,
                target_is_directory=True,
            )

            with self.assertRaises(ValueError):
                file_organizer.build_plan(source, destination)

    def test_apply_then_undo_restores_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "inbox"
            destination = source / "_organized"
            source.mkdir()
            original = source / "events.csv"
            original.write_text("event,count\nlogin,2\n", encoding="utf-8")
            operations = file_organizer.build_plan(source, destination)
            manifest = tmp_path / "manifest.json"

            saved = file_organizer.apply_plan(
                source, destination, operations, manifest
            )

            moved = destination / "data" / "events.csv"
            self.assertEqual(saved, manifest.resolve())
            self.assertTrue(moved.exists())
            self.assertFalse(original.exists())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "completed")
            self.assertEqual(payload["operations"][0]["status"], "applied")

            restored = file_organizer.undo_manifest(manifest)

            self.assertEqual(restored, 1)
            self.assertTrue(original.exists())
            self.assertFalse(moved.exists())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "undone")
            self.assertEqual(payload["operations"][0]["status"], "undone")

    def test_undo_stops_before_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            tmp_path = Path(temporary)
            source = tmp_path / "inbox"
            destination = source / "_organized"
            source.mkdir()
            original = source / "report.pdf"
            original.write_bytes(b"first")
            operations = file_organizer.build_plan(source, destination)
            manifest = tmp_path / "manifest.json"
            file_organizer.apply_plan(source, destination, operations, manifest)
            original.write_bytes(b"replacement")

            with self.assertRaises(FileExistsError):
                file_organizer.undo_manifest(manifest)

            self.assertEqual(original.read_bytes(), b"replacement")
            self.assertTrue((destination / "documents" / "report.pdf").exists())
