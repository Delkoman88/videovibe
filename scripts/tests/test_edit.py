"""Orquestador: lógica pura (editlib) y bin/edit de punta a punta hasta las pausas, en un canal temporal."""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import editlib  # noqa: E402
from scripts.tests.support import say_voice_available  # noqa: E402


def touch(p, t=None, text="{}"):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(text)
    if t is not None:
        os.utime(p, (t, t))
    return p


BRIEF_OK = ("- ★ **Objetivo:** probar\n- ★ **Audiencia principal:** tests\n"
            "- ★ **Material disponible:** raw/toma.mp4\n- ★ **Llamada a la acción:** sígueme\n")


def iso(ts):
    return datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


class TestEditLogic(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.P = Path(self.td.name) / "pieza"
        self.now = time.time()
        touch(self.P / "brief.md", None, BRIEF_OK)

    def tearDown(self):
        self.td.cleanup()

    def piece_until_paper_cut(self):
        P, t = self.P, self.now
        touch(P / "raw" / "toma.mp4", t - 100, "x")
        touch(P / "media.json", t - 90, json.dumps({"items": [{"id": "toma", "file": "raw/toma.mp4", "audio": "a.wav"}]}))
        touch(P / "transcript" / "toma.json", t - 80)
        touch(P / "cut" / "cut-list.json", t - 70)

    def test_first_stage_is_ingest(self):
        touch(self.P / "raw" / "toma.mp4", self.now, "x")
        self.assertEqual(editlib.next_action(self.P, {}, ["tiktok"])["run"], "ingesta")

    def test_pauses_at_A_and_invalidates_when_cut_changes(self):
        self.piece_until_paper_cut()
        self.assertEqual(editlib.next_action(self.P, {}, ["tiktok"])["pause"]["pending"], "aprobación A")
        st = {"approvals": {"A": {"at": iso(self.now - 60)}}}
        self.assertEqual(editlib.next_action(self.P, st, ["tiktok"])["run"], "corte-aplicado")
        touch(self.P / "cut" / "cut-list.json", self.now)  # editado tras aprobar
        act = editlib.next_action(self.P, st, ["tiktok"])
        self.assertIn("cambió", act["pause"]["reason"])

    def test_media_json_rewrite_does_not_retranscribe(self):
        self.piece_until_paper_cut()
        touch(self.P / "media.json", self.now)  # una ingesta reescribe media.json
        st = {"approvals": {"A": {"at": iso(self.now - 60)}}}
        self.assertEqual(editlib.next_action(self.P, st, ["tiktok"])["run"], "corte-aplicado")

    def test_storyboard_gate_and_platforms(self):
        self.assertEqual(editlib.platforms({"platforms": {"reels": {}}}, {"platforms": ["tiktok"]}), ["reels"])
        self.assertEqual(editlib.platforms({}, {"platforms": ["tiktok", "x"]}), ["tiktok", "x"])
        self.assertEqual(editlib.gate("storyboard", self.P, {})["pending"], "storyboard")

    def test_B_invalidated_by_storyboard_change(self):
        touch(self.P / "storyboard.json", self.now)
        st = {"approvals": {"B": {"at": iso(self.now - 30)}}}
        self.assertEqual(editlib.gate("B", self.P, st)["pending"], "aprobación B")
        st = {"approvals": {"B": {"at": iso(self.now + 5)}}}
        self.assertIsNone(editlib.gate("B", self.P, st))

    def test_B_invalidated_by_broll_source_change(self):
        P, t = self.P, self.now
        touch(P / "storyboard.json", t - 50, json.dumps({"broll": [{"source": "screen"}]}))
        touch(P / "media.json", t - 40, json.dumps({"items": [{"id": "screen", "file": "raw/screen.mp4"}]}))
        source = touch(P / "raw" / "screen.mp4", t - 30, "old")
        st = {"approvals": {"B": {"at": iso(t - 20)}}}
        self.assertIsNone(editlib.gate("B", P, st))
        source.write_text("new")
        os.utime(source, (t, t))
        self.assertEqual(editlib.gate("B", P, st)["pending"], "aprobación B")

    def test_broll_asset_changes_review_fingerprint_even_at_same_size(self):
        asset = self.P / "hf" / "assets" / "broll-screen.mp4"
        touch(self.P / "hf" / "index.html", text="<html></html>")
        touch(asset, text="abc")
        before = editlib.hf_fingerprint(self.P)
        asset.write_text("xyz")
        self.assertNotEqual(before, editlib.hf_fingerprint(self.P))

    def test_review_times(self):
        sb = {"overlays": [{"in": 0.15, "out": 4.0}], "scenes": [{"in": s, "out": s + 2} for s in range(5, 80, 3)]}
        ts = editlib.review_times(sb, 88.0)
        self.assertLessEqual(len(ts), 16)
        self.assertEqual(ts, sorted(ts))
        self.assertTrue(all(0 < t < 88 for t in ts))
        self.assertTrue(all(b - a >= 0.5 for a, b in zip(ts, ts[1:])))

    def test_forced_from(self):
        self.assertEqual(editlib.forced_from("render"), ["render", "entrega"])
        with self.assertRaises(KeyError):
            editlib.forced_from("inexistente")


@unittest.skipUnless(say_voice_available() and shutil.which("whisper-cli")
                     and (ROOT / "models" / "ggml-large-v3-turbo-q5_0.bin").exists(),
                     "requiere macOS say, whisper-cli y el modelo")
class TestEditEndToEnd(unittest.TestCase):
    def test_pauses_resume_idempotence_and_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            chan = Path(td) / "canal-prueba"
            shutil.copytree(ROOT / "channels" / "_template", chan)
            cfg = json.loads((chan / "channel.json").read_text())
            cfg.update({"id": "canal-prueba", "name": "Canal de prueba", "language": "es", "platforms": ["tiktok"]})
            (chan / "channel.json").write_text(json.dumps(cfg))
            P = chan / "projects" / "pieza"
            (P / "raw").mkdir(parents=True)
            (P / "brief.md").write_text(BRIEF_OK)
            aiff = Path(td) / "voz.aiff"
            subprocess.run(["say", "-v", "Paulina", "-o", str(aiff), "Hola, esto es una prueba. [[slnc 1500]] "
                            "Esto es una prueba del orquestador."], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30", "-i", str(aiff),
                            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(P / "raw" / "toma.mp4")],
                           check=True)

            def edit(*extra):
                r = subprocess.run([str(ROOT / "bin" / "edit"), str(P), "--json", *extra], capture_output=True,
                                   text=True, env={**os.environ, "VIDEOVIBE_REVIEW_NO_OPEN": "1"})
                self.assertIn(r.returncode, (0,), r.stdout + r.stderr)
                return json.loads(r.stdout)

            def approve(g):
                subprocess.run([str(ROOT / "bin" / "status"), str(P), "--approve", g], check=True, capture_output=True)

            r1 = edit()
            self.assertEqual(r1["paused"], "aprobación A")
            self.assertEqual([x["stage"] for x in r1["ran"]], ["ingesta", "transcripcion", "corte-en-papel"])
            r2 = edit()
            self.assertEqual(r2["ran"], [])  # idempotente: nada que rehacer
            self.assertEqual(r2["paused"], "aprobación A")
            time.sleep(1.1)
            approve("A")
            r3 = edit()
            self.assertEqual([x["stage"] for x in r3["ran"]], ["corte-aplicado", "subtitulos"])
            self.assertEqual(r3["paused"], "storyboard")
            time.sleep(1.1)
            os.utime(P / "cut" / "cut-list.json")  # cambio del corte tras aprobar
            r4 = edit()
            self.assertEqual(r4["paused"], "aprobación A")
            self.assertIn("cambió", r4["reason"])



class TestPlatformFingerprint(unittest.TestCase):
    """Render por plataforma: solo se rehace la que cambió."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        P = Path(self.td)
        hf = P / "hf"
        (hf / "compositions").mkdir(parents=True)
        (hf / "variables").mkdir()
        (hf / "assets" / "audio" / "sfx").mkdir(parents=True)
        (hf / "assets" / "plate.mp4").write_bytes(b"video" * 100)
        (hf / "assets" / "audio" / "sfx" / "click.wav").write_bytes(b"c" * 50)
        (hf / "assets" / "audio" / "music-epi.wav").write_bytes(b"e" * 1000)
        (hf / "assets" / "audio" / "music-propia.wav").write_bytes(b"p" * 1000)
        (hf / "compositions" / "captions.html").write_text("<p>hola</p>")
        self.write_index("Sígueme")
        for plat, cta, music in (("tiktok", "Sígueme", "epi"), ("reels", "Guárdalo", "epi"), ("ads", "Sígueme", "propia")):
            (hf / "variables" / f"{plat}.json").write_text(
                json.dumps({"cta_text": cta, "music_src": f"assets/audio/music-{music}.wav"}))
        self.P = P

    def tearDown(self):
        shutil.rmtree(self.td)

    def write_index(self, default_cta, body="<div>escena</div>"):
        vars_ = json.dumps([{"id": "cta_text", "default": default_cta}])
        (Path(self.td) / "hf" / "index.html").write_text(
            f"<html data-composition-variables='{vars_}'>{body}"
            f'<audio id="music" class="clip" src="assets/audio/music-epi.wav" data-var-src="music_src"></audio></html>')

    def fps(self):
        return {p: editlib.platform_fingerprint(self.P, p) for p in ("tiktok", "reels", "ads")}

    def changed(self, before):
        after = self.fps()
        return sorted(p for p in before if before[p] != after[p])

    def test_ad_music_same_size_only_ad(self):
        b = self.fps()
        (self.P / "hf" / "assets" / "audio" / "music-propia.wav").write_bytes(b"q" * 1000)  # mismo tamaño
        self.assertEqual(self.changed(b), ["ads"])

    def test_cta_of_one_platform(self):
        b = self.fps()
        (self.P / "hf" / "variables" / "reels.json").write_text(
            json.dumps({"cta_text": "Compártelo", "music_src": "assets/audio/music-epi.wav"}))
        self.assertEqual(self.changed(b), ["reels"])

    def test_default_values_in_index_do_not_matter(self):
        b = self.fps()
        self.write_index("Otro CTA por defecto")
        self.assertEqual(self.changed(b), [])

    def test_common_change_rerenders_all(self):
        b = self.fps()
        self.write_index("Sígueme", body="<div>escena nueva</div>")
        self.assertEqual(self.changed(b), ["ads", "reels", "tiktok"])
        b = self.fps()
        (self.P / "hf" / "assets" / "audio" / "sfx" / "click.wav").write_bytes(b"d" * 50)
        self.assertEqual(self.changed(b), ["ads", "reels", "tiktok"])

    def test_main_music_change_skips_ad(self):
        b = self.fps()
        (self.P / "hf" / "assets" / "audio" / "music-epi.wav").write_bytes(b"f" * 1000)
        self.assertEqual(self.changed(b), ["reels", "tiktok"])


class TestFingerprintCompat(unittest.TestCase):
    def test_without_broll_fingerprint_is_unchanged(self):
        """Las piezas sin insertos conservan la huella anterior (no se re-verifican ni re-renderizan)."""
        with tempfile.TemporaryDirectory() as td:
            hf = Path(td) / "hf"
            (hf / "compositions").mkdir(parents=True)
            (hf / "assets").mkdir()
            (hf / "index.html").write_text("<html></html>")
            (hf / "assets" / "plate.mp4").write_bytes(b"x" * 10)
            old = editlib.fingerprint([hf / "index.html", hf / "assets" / "plate.mp4"])
            self.assertEqual(editlib.hf_fingerprint(td), old)
            (hf / "assets" / "broll-a.mp4").write_bytes(b"b")
            self.assertNotEqual(editlib.hf_fingerprint(td), old)


class TestPieceStart(unittest.TestCase):
    """Empezar una pieza: bin/new-piece y las pausas «material» y «brief»."""

    def test_brief_parser(self):
        tpl = (ROOT / "templates" / "brief.md").read_text()
        self.assertEqual(editlib.brief_missing(tpl), list(editlib.BRIEF_REQUIRED))
        self.assertEqual(editlib.brief_missing(BRIEF_OK), [])
        self.assertEqual(editlib.brief_missing("- Objetivo: x\n- Audiencia: y\n- Material: z\n- CTA: w"), [])
        self.assertEqual(editlib.brief_missing(BRIEF_OK.replace("probar", "")), ["objetivo"])

    def test_gates_material_then_brief(self):
        with tempfile.TemporaryDirectory() as td:
            P = Path(td) / "pieza"
            (P / "raw").mkdir(parents=True)
            self.assertEqual(editlib.next_action(P, {}, ["tiktok"])["pause"]["pending"], "material")
            (P / "raw" / "toma.mp4").write_text("x")
            self.assertEqual(editlib.next_action(P, {}, ["tiktok"])["pause"]["pending"], "brief")
            (P / "brief.md").write_text(BRIEF_OK)
            self.assertEqual(editlib.next_action(P, {}, ["tiktok"])["run"], "ingesta")
            (P / "brief.md").write_text("")  # una pieza ya aprobada en A no se detiene por el brief
            self.assertNotEqual(editlib.next_action(P, {"approvals": {"A": {"at": iso(time.time())}}}, ["tiktok"])
                                .get("pause", {}).get("pending"), "brief")

    def test_new_piece_goes_to_channels_dir(self):
        with tempfile.TemporaryDirectory() as td:
            chans, media = Path(td) / "canales", Path(td) / "toma.mp4"
            media.write_text("x")
            env = {**os.environ, "VIDEOVIBE_CHANNELS": str(chans)}
            r = subprocess.run([str(ROOT / "bin" / "new-channel"), "mi-canal"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(ROOT / "bin" / "new-piece"), "mi-canal", "Primera Toma!", "--from", str(media),
                                "--date", "2026-01-02"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = json.loads(r.stdout)
            P = chans / "mi-canal" / "projects" / "2026-01-02-primera-toma"
            self.assertEqual(out["piece"], "mi-canal/2026-01-02-primera-toma")
            self.assertTrue((P / "raw" / "toma.mp4").exists())
            self.assertTrue((P / "brief.md").exists())
            self.assertTrue(media.exists(), "sin --move, el original se queda")
            r = subprocess.run([str(ROOT / "bin" / "new-piece"), "no-existe", "x"], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
