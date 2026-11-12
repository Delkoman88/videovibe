"""Revisión guiada: archivos, preguntas y aprobación ligada a la versión presentada."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import reviewlib  # noqa: E402


class TestReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.P = Path(self.tmp.name) / "pieza"
        (self.P / "cut").mkdir(parents=True)
        (self.P / "cut" / "PAPER-CUT.md").write_text("# Corte\n")
        (self.P / "cut" / "cut-list.json").write_text(json.dumps({"lines": [
            {"status": "keep", "text": "Hola"}, {"status": "drop", "text": "Eh"}]}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_A_opens_file_and_global_approval_is_versioned(self):
        info = reviewlib.present(self.P, "A", no_open=True)
        self.assertEqual(len(info["questions"]), 4)
        self.assertEqual(info["open_results"][0]["path"], str((self.P / "cut" / "PAPER-CUT.md").resolve()))
        self.assertFalse(info["open_results"][0]["opened"])
        cmd = [str(ROOT / "bin" / "status"), str(self.P), "--approve", "A"]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        (self.P / "cut" / "cut-list.json").write_text('{"lines": []}')
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)

    def test_reject_requires_new_version_before_approval(self):
        reviewlib.present(self.P, "A", no_open=True)
        cmd = [str(ROOT / "bin" / "review"), str(self.P), "--gate", "A", "--decision", "reject"]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        approve = [str(ROOT / "bin" / "status"), str(self.P), "--approve", "A"]
        self.assertEqual(subprocess.run(approve, capture_output=True).returncode, 1)
        (self.P / "cut" / "PAPER-CUT.md").write_text("# Corte nuevo\n")
        reviewlib.present(self.P, "A", no_open=True)
        self.assertEqual(subprocess.run(approve, capture_output=True).returncode, 0)

    def test_missing_review_file_cannot_be_approved(self):
        (self.P / "cut" / "PAPER-CUT.md").unlink()
        reviewlib.present(self.P, "A", no_open=True)
        cmd = [str(ROOT / "bin" / "status"), str(self.P), "--approve", "A"]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)

    def test_B_includes_draft_sheet_and_phone_preview(self):
        for folder in ("captions", "renders", "snaps", "raw"):
            (self.P / folder).mkdir()
        (self.P / "storyboard.json").write_text(json.dumps({"platforms": {"tiktok": {}}, "broll": [
            {"id": "s", "source": "s", "in": 1, "out": 2}]}))
        (self.P / "captions" / "captions.json").write_text("{}")
        (self.P / "media.json").write_text(json.dumps({"items": [{"id": "s", "file": "raw/s.mp4"}]}))
        for name in ("renders/draft-tiktok.mp4", "snaps/contact-sheet.jpg", "snaps/phone-s.png", "raw/s.mp4"):
            (self.P / name).write_bytes(b"video")
        info = reviewlib.present(self.P, "B", no_open=True)
        self.assertEqual(len(info["files"]), 3)
        self.assertEqual(len(info["questions"]), 4)
        self.assertTrue(all(Path(p).is_absolute() for p in info["files"]))
        approve = [str(ROOT / "bin" / "status"), str(self.P), "--approve", "B"]
        self.assertEqual(subprocess.run(approve, capture_output=True).returncode, 0)
        (self.P / "raw" / "s.mp4").write_bytes(b"other")
        self.assertNotEqual(info["fingerprint"], reviewlib.fingerprint(self.P, "B"))
        self.assertEqual(subprocess.run(approve, capture_output=True).returncode, 1)

    @mock.patch("scripts.core.reviewlib.subprocess.run")
    @mock.patch("scripts.core.reviewlib.shutil.which", return_value="/usr/bin/open")
    @mock.patch("scripts.core.reviewlib.platform.system", return_value="Darwin")
    def test_opener_deduplicates_and_reports_path(self, _system, _which, run):
        run.return_value.returncode = 0
        f = self.P / "cut" / "PAPER-CUT.md"
        opened = reviewlib.open_files([f, f])
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0]["opened"])
        run.assert_called_once()

    @mock.patch("scripts.core.reviewlib.subprocess.run")
    @mock.patch("scripts.core.reviewlib.shutil.which", return_value="/usr/bin/xdg-open")
    @mock.patch("scripts.core.reviewlib.platform.system", return_value="Linux")
    def test_linux_without_display_reports_manual_path(self, _system, _which, run):
        f = self.P / "cut" / "PAPER-CUT.md"
        with mock.patch.dict("scripts.core.reviewlib.os.environ", {"DISPLAY": "", "WAYLAND_DISPLAY": ""}):
            result = reviewlib.open_files([f])[0]
        self.assertFalse(result["opened"])
        self.assertEqual(result["reason"], "no hay interfaz gráfica")
        self.assertEqual(result["path"], str(f.resolve()))
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
