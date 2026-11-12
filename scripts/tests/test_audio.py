"""Sonido: envolvente de ducking, tramos de voz, kit de efectos sintetizado y biblioteca de música."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pipeline import compose  # noqa: E402
from scripts.audio import sfx  # noqa: E402
from scripts.audio import musicgen  # noqa: E402
import numpy as np  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")


class TestDucking(unittest.TestCase):
    def test_speech_intervals_merge_short_pauses(self):
        caps = {"words": [{"start": 1.0, "end": 1.5}, {"start": 1.7, "end": 2.0}, {"start": 4.0, "end": 4.5}]}
        self.assertEqual(compose.speech_intervals(caps), [[1.0, 2.0], [4.0, 4.5]])

    def test_duck_lane_full_before_and_after_voice(self):
        lane = compose.duck_lane([[2.0, 5.0]], duck=0.3, total=8.0)
        vals = {p["t"]: p["v"] for p in lane}
        self.assertEqual(vals[0.0], 1.0)            # entrada a nivel completo
        self.assertEqual(vals[2.0], 0.3)            # baja al empezar la voz
        self.assertEqual(vals[5.0], 0.3)
        self.assertEqual(vals[5.35], 1.0)           # sube al terminar
        self.assertEqual([p["t"] for p in lane], sorted(p["t"] for p in lane))

    def test_duck_lane_voice_from_start(self):
        lane = compose.duck_lane([[0.1, 3.0]], duck=0.4, total=5.0)
        self.assertEqual(lane[0], {"t": 0.0, "v": 0.4})

    def test_duck_lane_point_limit(self):
        ivs = [[i * 0.5, i * 0.5 + 0.2] for i in range(400)]
        self.assertLessEqual(len(compose.duck_lane(ivs, 0.3, 300.0)), 512)


class TestSfxKit(unittest.TestCase):
    def test_kit_is_deterministic_and_sane(self):
        a, b = sfx.build({"root_hz": 660}), sfx.build({"root_hz": 660})
        self.assertEqual(sorted(a), sorted(sfx.DESCRIPTIONS))
        for name in a:
            self.assertTrue((a[name] == b[name]).all(), name)
            self.assertGreater(len(a[name]), 1000, name)
            self.assertFalse(np.isnan(a[name]).any(), f"{name}: NaN")
            self.assertIn(a[name].ndim, (1, 2), name)
            if a[name].ndim == 2:
                self.assertEqual(a[name].shape[1], 2, name)


class TestSceneCues(unittest.TestCase):
    def test_rotation_override_and_skip(self):
        scenes = [{"in": 1}, {"in": 2, "sfx": "drop"}, {"in": 3}, {"in": 4, "sfx": False}, {"in": 5}, {"in": 6}]
        cues = compose.scene_cues(scenes, "variado", -22, ["pulse", "ping"])
        self.assertEqual([c["sound"] for c in cues], ["pulse", "drop", "ping", "pulse", "ping"])
        self.assertEqual([c["sound"] for c in compose.scene_cues(scenes[:1], "click", -20)], ["click"])

    def test_entrances_exist_in_kit(self):
        self.assertTrue(set(sfx.ENTRANCES) <= set(sfx.build({})))
        self.assertTrue(set(sfx.ENTRANCES) <= set(sfx.DESCRIPTIONS))


class TestSfxCues(unittest.TestCase):
    def test_exit_cues_respect_sfx_out(self):
        scenes = [{"in": 1, "out": 3}, {"in": 4, "out": 6, "sfx_out": False}, {"in": 7, "out": 9}]
        cues = compose.exit_cues(scenes, "whoosh", -26)
        self.assertEqual([c["at"] for c in cues], [2.75, 8.75])
        self.assertTrue(all(c["sound"] == "whoosh" and c["db"] == -26 for c in cues))


class TestAdsMusic(unittest.TestCase):
    def test_platform_music_by_license(self):
        srcs = {"main": "m-epidemic.wav", "ads": "m-propia.wav"}
        self.assertEqual(compose.music_src_for({"id": "tiktok"}, srcs), "m-epidemic.wav")
        self.assertEqual(compose.music_src_for({"id": "ads", "ads": True}, srcs), "m-propia.wav")
        self.assertIsNone(compose.music_src_for({"ads": True}, {"main": "m.wav", "ads": None}))

    def test_anuncio_preset_is_ads(self):
        from scripts.core import oslib
        self.assertTrue(oslib.load_preset("ads").get("ads"))
        self.assertFalse(oslib.load_preset("tiktok").get("ads"))


class TestMusicGen(unittest.TestCase):
    def test_exact_duration_deterministic_and_headroom(self):
        a, info = musicgen.compose_track(20.0, "energico", 880, seed=3)
        b, _ = musicgen.compose_track(20.0, "energico", 880, seed=3)
        self.assertEqual(a.shape, (20 * musicgen.SR, 2))
        self.assertTrue(np.array_equal(a, b))
        self.assertLessEqual(np.max(np.abs(a)), 10 ** (-1 / 20) + 1e-6)
        self.assertFalse(np.isnan(a).any())
        self.assertEqual(info["key"], "Am")
        c, _ = musicgen.compose_track(20.0, "energico", 880, seed=4)
        self.assertFalse(np.array_equal(a, c), "otra semilla, otra pista")

    def test_all_moods_and_keys(self):
        for mood in musicgen.MOODS:
            x, info = musicgen.compose_track(12.0, mood, 660, seed=1)
            self.assertEqual(len(x), 12 * musicgen.SR, mood)
            self.assertTrue(info["key"].startswith("E"), info)


class TestSfxRecipes(unittest.TestCase):
    R = {"use": "gota", "duration": 0.4, "layers": [
        {"type": "tone", "f0": "root*2", "f1": "root*3", "decay": 0.04},
        {"type": "noise", "lo": 2000, "hi": 7000, "lo1": 4000, "hi1": 9000, "decay": 0.02, "gain": 0.4},
        {"type": "fm", "f": "root", "at": 0.05},
        {"type": "sub", "f0": 120, "repeat": 2, "every": 0.15},
        {"type": "grains", "count": 6, "f_lo": "root", "f_hi": "root*2", "rising": True}],
        "fx": {"reverb": 0.3, "lowpass": 9000, "bitcrush": 6, "tremolo": 8}}

    def test_freq_expressions(self):
        from scripts.audio import sfxrecipes
        self.assertEqual(sfxrecipes.freq("root*1.5", 880), 1320)
        self.assertEqual(sfxrecipes.freq("root/2", 880), 440)
        self.assertEqual(sfxrecipes.freq(" root ", 660), 660)
        self.assertEqual(sfxrecipes.freq(300, 880), 300)
        for bad in ("root**2", "__import__('os')", "raiz*2", True):
            with self.assertRaises(ValueError):
                sfxrecipes.freq(bad, 880)

    def test_valid_recipe_renders_all_layer_types(self):
        from scripts.audio import sfxrecipes
        self.assertEqual(sfxrecipes.validate({"recipes": {"gota": self.R}}), [])
        a = sfx.render_recipe(self.R, 880, seed=1)
        b = sfx.render_recipe(self.R, 880, seed=1)
        self.assertTrue(np.array_equal(a, b))
        self.assertEqual(a.shape[1], 2)
        self.assertGreaterEqual(len(a), int(0.4 * sfx.SR))
        self.assertFalse(np.isnan(a).any())
        c = sfx.render_recipe(self.R, 440, seed=1)
        self.assertFalse(np.array_equal(a[:len(c)], c[:len(a)]), "otra marca, otro tono")

    def test_clear_errors(self):
        from scripts.audio import sfxrecipes
        errs = sfxrecipes.validate({"recipes": {"x": {"use": "u", "duration": 9,
                                    "layers": [{"type": "tonee"}, {"type": "tone", "f0": "raiz"}], "fx": {"eco": 1}}}})
        joined = "\n".join(errs)
        for frag in ("duration", "«tonee» no existe", "layers[1].f0", "fx.eco"):
            self.assertIn(frag, joined)

    def test_recipes_in_kit_and_override_base(self):
        cid = "zz-test-recipes"
        cdir = ROOT / "channels" / cid
        shutil.copytree(ROOT / "channels" / "_template", cdir)
        try:
            (cdir / "audio" / "sfx").mkdir(parents=True, exist_ok=True)
            rec = {"recipes": {"gota": self.R, "click": dict(self.R, use="clic propio"),
                               "entra": dict(self.R, use="entrada", entrance=True)}}
            (cdir / "audio" / "sfx" / "recipes.json").write_text(json.dumps(rec))
            r = subprocess.run([PY, str(ROOT / "scripts" / "audio" / "sfx.py"), "--channel", cid, "--list"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = json.loads(r.stdout)
            self.assertEqual(out["sounds"]["gota"]["source"], "receta")
            self.assertEqual(out["sounds"]["click"]["use"], "clic propio")
            self.assertIn("entra", out["entrances"])
            self.assertTrue((cdir / "audio" / "sfx" / "gota.wav").exists())
            (cdir / "audio" / "sfx" / "recipes.json").write_text(json.dumps({"recipes": {"Mal": {}}}))
            r = subprocess.run([PY, str(ROOT / "scripts" / "audio" / "sfx.py"), "--channel", cid], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("problems", json.loads(r.stdout))
            from scripts.tools import check_channel
            self.assertTrue(any("recipes.json" in x for x in check_channel.check(cid, allow_todo=True)))
        finally:
            shutil.rmtree(cdir)


class TestMusicPalette(unittest.TestCase):
    def test_precedence_and_validation(self):
        pal = musicgen.resolve_palette("ambiental", {"pad": "keys", "drums": "soft"}, {"drums": "breakbeat"})
        self.assertEqual(pal["pad"], "keys")          # canal sobre ánimo
        self.assertEqual(pal["drums"], "breakbeat")   # --palette sobre canal
        self.assertEqual(pal["lead"], "bell")         # lo no fijado viene del ánimo
        for bad in ({"pad": "piano"}, {"swing": 0.9}, {"melody": "si"}, {"tempo": 3}):
            with self.assertRaises(ValueError):
                musicgen.resolve_palette("esperanzador", bad)

    def test_every_instrument_renders(self):
        base = musicgen.resolve_palette("energico")
        for k, opts in musicgen.PALETTE_OPTIONS.items():
            for v in opts:
                x, info = musicgen.compose_track(12.0, "energico", 880, 1, palette=dict(base, **{k: v}))
                self.assertEqual(len(x), 12 * musicgen.SR, (k, v))
                self.assertFalse(np.isnan(x).any(), (k, v))
                self.assertLessEqual(np.max(np.abs(x)), 10 ** (-1 / 20) + 1e-6)
                self.assertEqual(info["palette"][k], v)

    def test_palettes_sound_different(self):
        def centroid(x):
            X = np.abs(np.fft.rfft(x[:, 0])) ** 2
            f = np.fft.rfftfreq(len(x), 1 / musicgen.SR)
            return (X * f).sum() / X.sum()
        p1 = musicgen.resolve_palette("esperanzador", {"pad": "saw", "lead": "square"})
        p2 = musicgen.resolve_palette("esperanzador", {"pad": "glass", "lead": "bell"})
        a, _ = musicgen.compose_track(20.0, "esperanzador", 880, 1, palette=p1)
        b, _ = musicgen.compose_track(20.0, "esperanzador", 880, 1, palette=p2)
        self.assertGreater(abs(centroid(a) - centroid(b)), 30)

    def test_energetic_mix_is_not_pad_dominated(self):
        st = {}
        musicgen.compose_track(30.0, "energico", 880, 1, stems=st)
        rms = {k: np.sqrt(np.mean(v ** 2)) + 1e-12 for k, v in st.items()}
        self.assertGreater(rms["drums"] + rms["bass"], rms["pad"])

    def test_intro_not_buried(self):
        """La intro puede crecer, pero no quedar muy por debajo del cuerpo (se perdía bajo la voz)."""
        for mood in musicgen.MOODS:
            x, _ = musicgen.compose_track(60.0, mood, 880, 1)
            r = lambda a, b: 20 * np.log10(np.sqrt(np.mean(x[int(a * musicgen.SR):int(b * musicgen.SR)] ** 2)) + 1e-12)  # noqa: E731
            body = r(20, 45)
            for t in range(1, 10, 2):
                self.assertGreater(r(t, t + 2), body - 6, f"{mood}: {t}s demasiado bajo")

    def test_moods_differ_in_tempo(self):
        bpms = {m: musicgen.compose_track(20.0, m, 880, 1)[1]["bpm"] for m in musicgen.MOODS}
        self.assertEqual(len(set(round(b) for b in bpms.values())), len(bpms))


class TestMusicLibrary(unittest.TestCase):
    def test_add_requires_license_and_measures(self):
        with tempfile.TemporaryDirectory() as td:
            cid = "zz-test-audio"
            cdir = ROOT / "channels" / cid
            shutil.copytree(ROOT / "channels" / "_template", cdir)
            try:
                wav = Path(td) / "t.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                                str(wav)], check=True)
                base = [PY, str(ROOT / "scripts" / "audio" / "music.py"), "add", "--channel", cid, "--file", str(wav),
                        "--title", "Tono", "--source", "propia"]
                r = subprocess.run(base, capture_output=True, text=True)
                self.assertEqual(r.returncode, 2, "sin --license debe fallar")
                r = subprocess.run(base + ["--license", "propia", "--mood", "prueba"], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                t = json.loads(r.stdout)["added"]
                self.assertAlmostEqual(t["duration_s"], 3.0, delta=0.1)
                self.assertIsNotNone(t["lufs"])
                self.assertTrue(t["ads"], "las pistas propias sirven para anuncios")
                r = subprocess.run([PY, str(ROOT / "scripts" / "audio" / "music.py"), "add", "--channel", cid, "--file", str(wav),
                                    "--title", "Epi", "--source", "epidemic", "--license", "plan personal"],
                                   capture_output=True, text=True)
                self.assertFalse(json.loads(r.stdout)["added"]["ads"], "Epidemic sin --ads no sirve para anuncios")
                r = subprocess.run([PY, str(ROOT / "scripts" / "audio" / "music.py"), "list", "--channel", cid, "--ads"],
                                   capture_output=True, text=True)
                self.assertEqual([x["id"] for x in json.loads(r.stdout)["tracks"]], ["tono"])
                lib = json.loads((cdir / "audio" / "music" / "library.json").read_text())
                self.assertEqual(lib["tracks"][0]["id"], "tono")
            finally:
                shutil.rmtree(cdir)


if __name__ == "__main__":
    unittest.main()
