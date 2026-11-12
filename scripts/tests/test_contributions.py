"""Audios aportados por la persona: música (revisión, trim, BPM, fit), efectos (sfx.py add) y licencias."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
import numpy as np  # noqa: E402

from scripts.audio import audiotools  # noqa: E402
from scripts.pipeline import compose  # noqa: E402
from scripts.audio import musicgen  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")
SR = audiotools.SR


def clicks(bpm=100, seconds=30, lead=0.0):
    x = np.zeros((int((seconds + lead) * SR), 2))
    for k in range(int(seconds * bpm / 60)):
        i = int((lead + k * 60 / bpm) * SR)
        n = int(0.03 * SR)
        t = np.arange(n) / SR
        x[i:i + n] += (np.sin(2 * np.pi * 1000 * t) * np.exp(-t / 0.008))[:, None] * (1.0 if k % 4 == 0 else 0.6)
    return x * 0.5


def run(*args):
    r = subprocess.run([PY, *map(str, args)], capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout + r.stderr)


class TestAudioTools(unittest.TestCase):
    def test_bpm_on_clicks(self):
        bpm, conf = audiotools.estimate_bpm(clicks(100))
        self.assertAlmostEqual(bpm, 100, delta=2)
        self.assertGreater(conf, 0.5)

    def test_fit_exact_both_ways(self):
        x, _ = musicgen.compose_track(40.0, "energico", 880, 1)
        for target in (25.0, 70.0, 131.3):
            y, info = audiotools.fit_duration(x, target, 120.0)
            self.assertAlmostEqual(len(y) / SR, target, delta=0.01)
            self.assertFalse(np.isnan(y).any())
            self.assertLess(np.abs(y[-100:]).max(), 0.01, "termina con fundido")
        self.assertIn("repetir", audiotools.fit_duration(x, 70.0, 120.0)[1]["method"])

    def test_trim_silence(self):
        x = np.concatenate([np.zeros((SR, 2)), clicks(100, 3), np.zeros((2 * SR, 2))])
        y = audiotools.trim_silence(x)
        self.assertLess(len(y) / SR, 3.2)
        self.assertGreater(len(y) / SR, 2.4)


class TestChannelAudio(unittest.TestCase):
    def setUp(self):
        self.cid = "zz-test-aportes"
        self.cdir = ROOT / "channels" / self.cid
        shutil.copytree(ROOT / "channels" / "_template", self.cdir)
        self.td = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.cdir)
        shutil.rmtree(self.td)

    def test_music_add_checks_trim_bpm_fit(self):
        hot = clicks(100, 20, lead=2.0) * 4  # saturada y con 2 s de silencio al inicio
        f = self.td / "mia.wav"
        audiotools.write_wav(f, hot)
        base = [ROOT / "scripts" / "audio" / "music.py", "add", "--channel", self.cid, "--file", f, "--title", "Mia",
                "--source", "usuario", "--license", "Compuesta por Alex"]
        code, out = run(*base)
        self.assertEqual(code, 2, "falta --provided-by")
        code, out = run(*base, "--provided-by", "Alex")
        self.assertEqual(code, 0, out)
        self.assertTrue(any("saturación" in w for w in out["warnings"]), out["warnings"])
        self.assertTrue(any("silencio al inicio" in w for w in out["warnings"]), out["warnings"])
        self.assertAlmostEqual(out["added"]["bpm"], 100, delta=2)
        self.assertEqual(out["added"]["provided_by"], "Alex")
        self.assertFalse(out["added"]["ads"], "aportada sin --ads: no apta para anuncios")
        code, out = run(*base, "--provided-by", "Alex", "--title", "Mia2", "--trim")
        self.assertEqual(code, 0, out)
        self.assertLess(out["added"]["duration_s"], 20.5)
        code, out = run(ROOT / "scripts" / "audio" / "music.py", "fit", "--channel", self.cid, "--track", "mia",
                        "--duration", "45")
        self.assertEqual(code, 0, out)
        self.assertAlmostEqual(out["added"]["duration_s"], 45, delta=0.05)
        self.assertEqual(out["added"]["derived_from"], "mia")
        self.assertEqual(out["added"]["license"], "Compuesta por Alex")

    def test_sfx_add_trims_survives_regen_and_precedence(self):
        f = self.td / "pip.wav"
        snd = np.concatenate([np.zeros((SR, 2)), clicks(100, 1), np.zeros((SR, 2))])
        audiotools.write_wav(f, snd)
        sfx = ROOT / "scripts" / "audio" / "sfx.py"
        code, out = run(sfx, "add", "--channel", self.cid, "--file", f, "--name", "click", "--use", "pipeta real")
        self.assertEqual(code, 2, "sin licencia debe fallar")
        code, out = run(sfx, "add", "--channel", self.cid, "--file", f, "--name", "click", "--use", "pipeta real",
                        "--license", "Propio (grabado por Alex)", "--provided-by", "Alex")
        self.assertEqual(code, 0, out)
        code, out = run(sfx, "--channel", self.cid, "--force", "--list")
        self.assertEqual(code, 0, out)
        c = out["sounds"]["click"]
        self.assertEqual(c["source"], "usuario")          # usuario > base
        self.assertEqual(c["use"], "pipeta real")
        self.assertLess(c["duration_s"], 1.3)              # silencios recortados
        self.assertFalse(c["ads"])
        self.assertTrue((self.cdir / "audio" / "sfx" / "user.json").exists())
        from scripts.tools import check_channel
        self.assertFalse(any("user" in p for p in check_channel.check(self.cid, allow_todo=True)))
        (self.cdir / "audio" / "sfx" / "user" / "click.wav").unlink()
        self.assertTrue(any("falta el original" in p for p in check_channel.check(self.cid, allow_todo=True)))


class TestCredits(unittest.TestCase):
    def test_assets_block_lists_sources_and_is_replaced(self):
        credits = {"music": {"main": {"title": "Pista", "artist": "Autor", "source": "epidemic", "source_id": "x1",
                                      "license": "Suscripción", "ads": False},
                             "ads": {"title": "Propia", "source": "propia", "license": "Propia", "ads": True}},
                   "sfx": {"bell": {"source": "base"}, "pip": {"source": "usuario", "provided_by": "Alex",
                                                                "license": "Propio (grabado)", "ads": True}}}
        block = compose.audio_credits_md(credits)
        for frag in ("«Pista» — Autor", "Epidemic Sound, id x1", "Música (versión anuncio)", "Efecto «pip»",
                     "aportado por Alex", "bell"):
            self.assertIn(frag, block)
        with tempfile.TemporaryDirectory() as td:
            P = Path(td)
            (P / "assets.md").write_text("# Fuentes\n\n| a | b | c |\n")
            compose.update_assets_md(P, block)
            compose.update_assets_md(P, block.replace("Pista", "Otra"))
            txt = (P / "assets.md").read_text()
            self.assertEqual(txt.count(compose.AUTO_BEGIN), 1)
            self.assertIn("Otra", txt)
            self.assertIn("| a | b | c |", txt)


if __name__ == "__main__":
    unittest.main()
