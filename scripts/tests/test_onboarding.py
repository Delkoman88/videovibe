import sys
"""Primeros pasos: bin/welcome (etapas), bin/new-channel básico y scripts con canales fuera del repo."""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str(ROOT / ".venv" / "bin" / "python")


def run(cmd, chans):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       env={**os.environ, "VIDEOVIBE_CHANNELS": str(chans)})
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout + r.stderr)


def basic_channel(chans, cid="cocina-facil"):
    return run([ROOT / "bin" / "new-channel", cid, "--name", "Cocina Fácil", "--lang", "es",
                "--about", "Recetas rápidas y baratas para estudiantes", "--person", "Ana López:cocinera",
                "--platforms", "tiktok,reels"], chans)


class TestBienvenida(unittest.TestCase):
    def test_stages_in_order(self):
        with tempfile.TemporaryDirectory() as td:
            chans = Path(td) / "canales"
            chans.mkdir()
            stage = lambda: run([ROOT / "bin" / "welcome", "--skip-doctor"], chans)[1]["stage"]  # noqa: E731
            self.assertEqual(stage(), "crear-canal")
            run([ROOT / "bin" / "new-channel", "a-medias"], chans)          # plantilla con TODO
            self.assertEqual(stage(), "completar-canal")
            (chans / "a-medias").rename(Path(td) / "fuera")                 # lo quitamos
            self.assertEqual(basic_channel(chans)[0], 0)
            self.assertEqual(stage(), "primera-pieza")
            run([ROOT / "bin" / "new-piece", "cocina-facil", "huevo"], chans)
            out = run([ROOT / "bin" / "welcome", "--skip-doctor"], chans)[1]
            self.assertEqual(out["stage"], "listo")
            self.assertEqual(list(out["channels"][0]["pieces"].values()), ["nueva"])

    def test_engine_channels_are_not_the_persons(self):
        # sin carpeta propia, los canales del motor (plantilla y ejemplo) no cuentan como canales de la persona
        loader = importlib.machinery.SourceFileLoader("bienvenida", str(ROOT / "bin" / "welcome"))
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("bienvenida", loader))
        loader.exec_module(mod)
        self.assertEqual(mod.own_channels(ROOT / "channels"), [])
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "local.json"
            local.write_text(json.dumps({"publish": {"author": "x"}}))
            target = mod.set_channels_dir(Path(td) / "mis-canales", local)
            self.assertTrue(target.is_dir())
            data = json.loads(local.read_text())
            self.assertEqual(data["publish"], {"author": "x"}, "no borra otras claves")
            self.assertTrue(data["channels_dir"].endswith("mis-canales"))


class TestNewChannelBasic(unittest.TestCase):
    def test_basic_channel_is_complete_and_usable(self):
        with tempfile.TemporaryDirectory() as td:
            chans = Path(td) / "canales"
            code, out = basic_channel(chans)
            self.assertEqual(code, 0, out)
            self.assertEqual(out["problems"], [])
            self.assertTrue(out["sfx_kit"])
            d = chans / "cocina-facil"
            for f in d.glob("*.md"):
                self.assertNotIn("TODO", f.read_text(), f.name)
            cfg = json.loads((d / "channel.json").read_text())
            self.assertEqual(cfg["persons"][0]["short"], "Ana")
            self.assertEqual(cfg["platforms"], ["tiktok", "reels"])
            self.assertIn("Recetas rápidas", (d / "CHANNEL.md").read_text())

    def test_errors(self):
        with tempfile.TemporaryDirectory() as td:
            chans = Path(td)
            self.assertEqual(run([ROOT / "bin" / "new-channel", "Mal Id"], chans)[0], 2)
            self.assertEqual(run([ROOT / "bin" / "new-channel", "x", "--platforms", "myspace"], chans)[0], 2)
            self.assertEqual(run([ROOT / "bin" / "new-channel", "x", "--about", "algo"], chans)[0], 2)  # falta --person
            self.assertEqual(basic_channel(chans)[0], 0)
            self.assertEqual(basic_channel(chans)[0], 1)  # ya existe


class TestExternalChannelsDir(unittest.TestCase):
    """Los canales pueden vivir fuera del repo (repo privado): ningún script debe suponer lo contrario."""

    def test_scripts_with_external_channels(self):
        with tempfile.TemporaryDirectory() as td:
            chans = Path(td) / "canales"
            self.assertEqual(basic_channel(chans)[0], 0)
            for cmd in ([PY, ROOT / "scripts" / "audio" / "sfx.py", "--channel", "cocina-facil", "--force"],
                        [PY, ROOT / "scripts" / "audio" / "sfx.py", "--channel", "cocina-facil", "--list"],
                        [PY, ROOT / "scripts" / "audio" / "music.py", "list", "--channel", "cocina-facil"],
                        [PY, ROOT / "scripts" / "tools" / "check_channel.py", "cocina-facil"],
                        [ROOT / "bin" / "status"]):
                code, out = run(cmd, chans)
                self.assertEqual(code, 0, f"{cmd[-2:]}: {out}")
            code, out = run([PY, ROOT / "scripts" / "audio" / "musicgen.py", "--channel", "cocina-facil", "--duration", "12",
                             "--mood", "ambiental", "--add", "--title", "Prueba"], chans)
            self.assertEqual(code, 0, out)
            self.assertTrue((chans / "cocina-facil" / "audio" / "music" / "prueba.wav").exists())


if __name__ == "__main__":
    unittest.main()
