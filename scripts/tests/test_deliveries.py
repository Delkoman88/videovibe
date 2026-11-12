"""Carpetas fáciles de encontrar: deliveries/ (finales verificados) y input/ (originales de la persona)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pipeline import deliver  # noqa: E402
from scripts.core import editlib  # noqa: E402
from scripts.core import oslib  # noqa: E402
from scripts.core import reviewlib  # noqa: E402


def piece(td, name="2026-03-04-huevo-microondas", plats=("tiktok", "reels")):
    """Canal + pieza con renders, portadas, textos y subtítulos falsos (sin video real)."""
    chans = Path(td) / "canales"
    ch = chans / "cocina"
    shutil.copytree(ROOT / "channels" / "science-60", ch, ignore=shutil.ignore_patterns("projects"))
    cfg = json.loads((ch / "channel.json").read_text())
    cfg.update({"id": "cocina", "name": "Cocina: Fácil"})
    (ch / "channel.json").write_text(json.dumps(cfg))
    P = ch / "projects" / name
    for d in ("renders", "covers", "copy", "captions"):
        (P / d).mkdir(parents=True)
    for p in plats:
        (P / "renders" / f"{p}.mp4").write_bytes(b"video " + p.encode())
        (P / "covers" / f"{p}.jpg").write_bytes(b"jpg")
        (P / "copy" / f"{p}.md").write_text(f"Texto para {p} #receta")
    (P / "captions" / "master.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhola\n")
    (P / "brief.md").write_text("- **Título de trabajo:** Huevo en 40 segundos\n")
    (P / "assets.md").write_text("<!-- audio:auto -->\n## Sonido\n| Música | propia |\n<!-- /audio:auto -->\n")
    return chans, P


class TestDeliver(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.chans, self.P = piece(self.td.name)
        self.out = Path(self.td.name) / "deliveries"
        self.patch = mock.patch.object(oslib, "DELIVERIES", self.out)
        self.patch.start()
        self.env = mock.patch.dict(os.environ, {"VIDEOVIBE_CHANNELS": str(self.chans)})
        self.env.start()

    def tearDown(self):
        self.patch.stop()
        self.env.stop()
        self.td.cleanup()

    def test_folder_names_and_hardlinks(self):
        res = deliver.deliver(self.P, ["tiktok", "reels"])
        d = Path(res["dir"])
        # «Cocina: Fácil» → los dos puntos no valen en Windows; la fecha se separa del nombre de la pieza
        self.assertEqual(d, (self.out / "Cocina- Fácil" / "2026-03-04 huevo-microondas").resolve())
        self.assertEqual(res["method"], "enlace")
        self.assertEqual(os.stat(d / "tiktok.mp4").st_ino, os.stat(self.P / "renders" / "tiktok.mp4").st_ino)
        for f in ("tiktok - cover.jpg", "reels - copy.md", "subtitles.srt", "README.md"):
            self.assertTrue((d / f).exists(), f)
        leeme = (d / "README.md").read_text()
        self.assertIn("# Huevo en 40 segundos", leeme)
        self.assertIn("Texto para reels #receta", leeme)
        self.assertIn("| Música | propia |", leeme)

    def test_copy_when_links_are_not_possible(self):
        with mock.patch.object(os, "link", side_effect=OSError("no se permiten enlaces")):
            res = deliver.deliver(self.P, ["tiktok"])
        d = Path(res["dir"])
        self.assertEqual(res["method"], "copia")
        self.assertNotEqual(os.stat(d / "tiktok.mp4").st_ino, os.stat(self.P / "renders" / "tiktok.mp4").st_ino)
        self.assertEqual((d / "tiktok.mp4").read_bytes(), b"video tiktok")

    def test_redeliver_updates_and_drops_old_platforms(self):
        d = Path(deliver.deliver(self.P, ["tiktok", "reels"])["dir"])
        (self.P / "renders" / "tiktok.mp4").unlink()                        # un render nuevo = archivo nuevo
        (self.P / "renders" / "tiktok.mp4").write_bytes(b"video tiktok v2")
        deliver.deliver(self.P, ["tiktok"])
        self.assertEqual((d / "tiktok.mp4").read_bytes(), b"video tiktok v2")
        self.assertFalse((d / "reels.mp4").exists(), "reels ya no es parte de la pieza")

    def test_missing_render_is_an_error(self):
        (self.P / "renders" / "reels.mp4").unlink()
        r = subprocess.run([str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "scripts" / "pipeline" / "deliver.py"),
                            "--project", str(self.P), "--platform", "reels"], capture_output=True, text=True,
                           env={**os.environ, "VIDEOVIBE_DELIVERIES": str(self.out)})
        self.assertEqual(r.returncode, 2)
        self.assertIn("faltan renders", r.stdout)

    def test_edit_redelivers_when_folder_is_missing(self):
        st = {"stage": "entregable", "fingerprints": {"entrega": editlib.delivery_fingerprint(self.P, ["tiktok"])}}
        self.assertTrue(editlib.stage_dirty("entrega", self.P, st, ["tiktok"])[0])
        st["delivery"] = deliver.deliver(self.P, ["tiktok"])["dir"]
        self.assertFalse(editlib.stage_dirty("entrega", self.P, st, ["tiktok"])[0])

    def test_open_folder_reports_absolute_path(self):
        d = deliver.deliver(self.P, ["tiktok"])["dir"]
        res = reviewlib.open_files([d], no_open=True)[0]
        self.assertEqual(res["path"], str(Path(d).resolve()))
        self.assertNotEqual(res.get("reason"), "archivo inexistente")


class TestMaterialFolder(unittest.TestCase):
    def test_new_piece_finds_files_in_material(self):
        with tempfile.TemporaryDirectory() as td:
            chans, _ = piece(td)
            material = Path(td) / "input"
            (material / "sesion-lunes").mkdir(parents=True)
            (material / "toma1.mp4").write_bytes(b"x")
            (material / "sesion-lunes" / "a.mov").write_bytes(b"y")
            (material / "sesion-lunes" / "notas.txt").write_text("no es material")
            env = {**os.environ, "VIDEOVIBE_CHANNELS": str(chans), "VIDEOVIBE_INPUT": str(material)}
            cmd = [str(ROOT / "bin" / "new-piece"), "cocina", "prueba", "--date", "2026-01-01"]
            r = subprocess.run(cmd + ["--from", "toma1.mp4", "sesion-lunes"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(json.loads(r.stdout)["raw"], ["a.mov", "toma1.mp4"])
            self.assertTrue((material / "toma1.mp4").exists(), "el original se queda en input/")
            r = subprocess.run([str(ROOT / "bin" / "new-piece"), "cocina", "otra", "--from", "no-existe.mp4"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 2)
            self.assertIn("toma1.mp4", r.stdout, "lista lo que sí hay en input/")


class TestInputConfig(unittest.TestCase):
    def test_input_dir_and_legacy_names(self):
        code = "import sys; sys.path.insert(0, 'scripts/core'); import oslib; print(oslib.MATERIAL)"
        def resolved(env):
            base = {k: v for k, v in os.environ.items() if k not in ("VIDEOVIBE_INPUT", "VIDEOVIBE_MATERIAL")}
            return subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                                  env={**base, **env}).stdout.strip()
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td, "a").resolve(), Path(td, "b").resolve()
            self.assertEqual(resolved({"VIDEOVIBE_INPUT": str(a)}), str(a))
            self.assertEqual(resolved({"VIDEOVIBE_MATERIAL": str(b)}), str(b), "el nombre anterior sigue valiendo")
            self.assertEqual(resolved({"VIDEOVIBE_INPUT": str(a), "VIDEOVIBE_MATERIAL": str(b)}), str(a))


if __name__ == "__main__":
    unittest.main()
