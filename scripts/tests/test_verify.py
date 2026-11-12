"""Verificación de entrega (verify.py): acepta un render correcto y rechaza los que no cumplen el preset."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402
from scripts.pipeline import verify  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")


def render(path, size="1080x1920", gain_db=0.0, dur=3.0):
    """Video H.264/yuv420p BT.709 + AAC 48 kHz con un tono de 1 kHz (picos predecibles); gain_db ajusta el volumen."""
    subprocess.run([oslib.FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30:d={dur}",
                    "-f", "lavfi", "-i", f"sine=frequency=1000:duration={dur}",
                    "-af", f"volume={gain_db}dB", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709",
                    "-c:a", "aac", "-ar", "48000", "-shortest", str(path)], check=True)


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        P = self.P = Path(self.td.name) / "pieza"
        for d in ("renders", "captions", "copy", "covers", "cut"):
            (P / d).mkdir(parents=True)
        (P / "storyboard.json").write_text(json.dumps({"tail_s": 0}))
        (P / "cut" / "cut-map.json").write_text(json.dumps({"duration_s": 3.0, "segments": []}))
        (P / "captions" / "tiktok.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhola\n")
        (P / "copy" / "tiktok.md").write_text("copy")
        (P / "covers" / "tiktok.jpg").write_bytes(b"\xff\xd8")
        # calibra el volumen a −14 LUFS con una medición previa
        probe = P / "renders" / "probe.mp4"
        render(probe)
        lufs, _ = verify.loudness(probe)
        self.gain = -14.0 - lufs

    def tearDown(self):
        self.td.cleanup()

    def run_verify(self):
        r = subprocess.run([PY, str(ROOT / "scripts" / "pipeline" / "verify.py"), "--project", str(self.P), "--platform", "tiktok"],
                           capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)

    def test_good_render_passes(self):
        render(self.P / "renders" / "tiktok.mp4", gain_db=self.gain)
        code, out = self.run_verify()
        self.assertEqual(code, 0, out["failed"])
        self.assertEqual(json.loads((self.P / "status.json").read_text())["stage"], "entregable")

    def test_loud_render_fails(self):
        render(self.P / "renders" / "tiktok.mp4", gain_db=self.gain + 5)
        code, out = self.run_verify()
        self.assertEqual(code, 1)
        self.assertTrue(any("volumen" in f for f in out["failed"]), out["failed"])

    def test_wrong_size_and_missing_cover_fail(self):
        render(self.P / "renders" / "tiktok.mp4", size="1920x1080", gain_db=self.gain)
        (self.P / "covers" / "tiktok.jpg").unlink()
        code, out = self.run_verify()
        self.assertEqual(code, 1)
        joined = " ".join(out["failed"])
        self.assertIn("resolución", joined)
        self.assertIn("portada", joined)


class TestCover(unittest.TestCase):
    def test_cover_at_hook_and_custom_time(self):
        with tempfile.TemporaryDirectory() as td:
            P = Path(td) / "pieza"
            (P / "renders").mkdir(parents=True)
            render(P / "renders" / "tiktok.mp4")
            (P / "storyboard.json").write_text(json.dumps(
                {"overlays": [{"id": "hook", "type": "title", "in": 0.2, "out": 2.2, "text": "Hola"}]}))
            cmd = [PY, str(ROOT / "scripts" / "pipeline" / "cover.py"), "--project", str(P), "--platform", "tiktok"]
            out = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
            self.assertAlmostEqual(out["covers"][0]["at_s"], 1.2)
            info = oslib.ffprobe(P / "covers" / "tiktok.jpg")
            self.assertEqual((info["streams"][0]["width"], info["streams"][0]["height"]), (1080, 1920))
            out = json.loads(subprocess.run(cmd + ["--at", "2.5"], capture_output=True, text=True, check=True).stdout)
            self.assertEqual(out["covers"][0]["at_s"], 2.5)


if __name__ == "__main__":
    unittest.main()
