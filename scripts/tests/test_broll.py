"""Contrato de los insertos: HTML, conversión de fuente y créditos."""
import sys
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402
from scripts.composer.credits import update_broll_credits  # noqa: E402
from scripts.composer.visual import broll_markup  # noqa: E402
from scripts.pipeline.compose import prepare_broll  # noqa: E402


class TestBroll(unittest.TestCase):
    def test_silent_screen_clip_keeps_master_timing(self):
        media = {"screen": {"id": "screen", "file": "raw/screen.mp4", "kind": "pantalla",
                            "duration_s": 5, "width": 1920, "height": 1080}}
        clip = {"id": "demo", "source": "screen", "in": 2, "out": 3.5, "source_in": 0.75,
                "fit": "cover", "focus_x": 70, "origin": "persona", "license": "propia"}
        markup = broll_markup({"broll": [clip]}, media)
        self.assertIn('data-start="2"', markup)
        self.assertIn('data-duration="1.5"', markup)
        self.assertIn('data-media-start="0.75"', markup)
        self.assertIn('object-position:70% 50%', markup)
        self.assertIn('muted playsinline', markup)
        detail = {**clip, "id": "detail", "in": 0.2, "out": 1.5, "source_in": 0,
                  "fit": "region", "region": {"x": 0.4, "y": 0.1, "w": 0.2, "h": 0.8}}
        detail_markup = broll_markup({"broll": [detail]}, media)
        self.assertIn('data-layout-allow-overflow', detail_markup)
        self.assertIn('left:-2160.000px', detail_markup)
        self.assertIn('width:5400.000px', detail_markup)
        with tempfile.TemporaryDirectory() as td:
            P = Path(td)
            (P / "raw").mkdir()
            (P / "hf" / "assets").mkdir(parents=True)
            oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i",
                       "testsrc2=size=640x360:rate=30", "-f", "lavfi", "-i", "sine=frequency=440",
                       "-t", "2", "-c:v", "libx264", "-c:a", "aac", str(P / "raw" / "screen.mp4")])
            prepare_broll(P, {"broll": [clip]}, P / "hf", media)
            out = P / "hf" / "assets" / "broll-screen.mp4"
            self.assertTrue(out.exists())
            probe = oslib.ffprobe(out)
            self.assertEqual([s["codec_type"] for s in probe["streams"]], ["video"])
            self.assertEqual(probe["streams"][0]["color_transfer"], "bt709")
            update_broll_credits(P, [clip], media)
            credits = (P / "assets.md").read_text()
            self.assertIn("raw/screen.mp4 | persona | propia", credits)
            # El archivo generado debe respetar el contrato real de HyperFrames.
            hf = P / "hf"
            (hf / "assets" / "vendor").mkdir()
            shutil.copy(ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js",
                        hf / "assets" / "vendor" / "gsap.min.js")
            shutil.copy(out, hf / "assets" / "plate.mp4")
            (hf / "index.html").write_text(
                '<!doctype html><html><head><script src="assets/vendor/gsap.min.js"></script>'
                '<style>html,body{margin:0;width:1080px;height:1920px}#root{position:absolute;inset:0}'
                '.broll-video,#plate{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}'
                '</style></head><body><div id="root" data-composition-id="main" data-start="0" '
                'data-duration="4" data-width="1080" data-height="1920">'
                '<video id="plate" class="clip" src="assets/plate.mp4" data-start="0" '
                'data-duration="4" muted playsinline></video>' + detail_markup + markup + '</div>'
                '<script>window.__timelines["main"]=gsap.timeline({paused:true});</script>'
                '</body></html>')
            check = subprocess.run([str(ROOT / "node_modules" / ".bin" / "hyperframes"), "check", "--json"],
                                   cwd=hf, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            (P / "storyboard.json").write_text(json.dumps({"broll": [detail]}))
            (P / "renders").mkdir()
            shutil.copy(out, P / "renders" / "draft.mp4")
            preview = subprocess.run([str(ROOT / ".venv" / "bin" / "python"),
                                      str(ROOT / "scripts" / "pipeline" / "phone_preview.py"), "--project", str(P),
                                      "--draft", "renders/draft.mp4"], capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            frame = P / "snaps" / "phone-detail.png"
            self.assertTrue(frame.exists())
            p = oslib.ffprobe(frame)["streams"][0]
            self.assertEqual((p["width"], p["height"]), (360, 640))


if __name__ == "__main__":
    unittest.main()
