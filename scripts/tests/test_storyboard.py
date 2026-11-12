"""Validación del storyboard: todos los problemas juntos, con la ruta exacta; compose.py no compone si los hay."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import formats  # noqa: E402
sys.path.insert(0, str(ROOT))
from scripts.pipeline import storyboard  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")


def ctx():
    return {"duration": 20.0, "word_ids": {"w0", "w1", "w2"}, "roles": {"keyword", "data", "punchline", "warning"},
            "formats": formats.registry(("biotech",)),
            "library": {"pista": {"id": "pista", "ads": False}, "propia": {"id": "propia", "ads": True}},
            "kit": {"click": {"ads": True}, "whoosh": {"ads": True}, "grabado": {"ads": False}},
            "presets": {"tiktok": {}, "reels": {}, "ads": {"ads": True}},
            "media": {"pantalla-1": {"id": "pantalla-1", "kind": "pantalla", "file": "raw/pantalla.mp4",
                                      "width": 1920, "height": 1080, "duration_s": 10.0}}}


GOOD = {
    "version": 1, "video": "cut/master-cut.mp4", "tail_s": 1.5,
    "camera": {"origin": "50% 30%", "moves": [{"type": "punch", "t": 2.0, "scale": 1.08, "until": 4.0}]},
    "emphasis": {"w1": "keyword"},
    "overlays": [{"id": "hook", "type": "title", "in": 0.15, "out": 3.0, "text": "Hola", "role": "keyword"},
                 {"id": "cta", "type": "cta", "in": 18.0, "out": 21.5, "text": "Sígueme", "role": "punchline"}],
    "scenes": [{"id": "s-dna", "format": "dna-helix", "in": 8.0, "out": 10.0, "params": {"label": "ADN"},
                "sfx": "click"}],
    "platforms": {"tiktok": {"cta_text": "Sígueme"}},
    "audio": {"music": {"track": "pista", "ads": "quiza"},
              "sfx_auto": {"scenes": "variado", "overlays": "click", "exits": "whoosh"},
              "sfx": [{"at": 5.0, "sound": "click", "db": -20}]},
    "voice": {"strength": "natural"},
}


class TestValidate(unittest.TestCase):
    def test_good_storyboard(self):
        errs, warns = storyboard.validate(GOOD, ctx())
        self.assertEqual(errs, [])
        self.assertEqual(warns, [])

    def test_all_problems_together_with_paths(self):
        bad = json.loads(json.dumps(GOOD))
        bad["overlays"][0]["out"] = 40.0                       # 1 fuera del video
        bad["overlays"][1]["role"] = "brillante"               # 2 rol inexistente
        bad["scenes"][0]["format"] = "volcan"                  # 3 formato inexistente
        bad["scenes"].append({"id": "s-hud", "format": "hud-frame", "in": 11, "out": 12, "params": {}})  # 4 faltan params
        bad["audio"]["music"]["track"] = "no-existe"           # 5 pista
        bad["audio"]["sfx"][0]["sound"] = "trompeta"           # 6 efecto
        bad["emphasis"]["w99"] = "keyword"                     # 7 palabra
        bad["platforms"]["myspace"] = {}                       # 8 plataforma
        errs, _ = storyboard.validate(bad, ctx())
        joined = "\n".join(errs)
        for frag in ("overlays[0].out", "overlays[1].role", "scenes[0].format", "scenes[1].params",
                     "audio.music.track", "audio.sfx[0].sound", "emphasis", "platforms.myspace"):
            self.assertIn(frag, joined)
        self.assertGreaterEqual(len(errs), 8)

    def test_ads_rules(self):
        sb = json.loads(json.dumps(GOOD))
        sb["platforms"]["ads"] = {}
        sb["scenes"][0]["sfx"] = "grabado"                     # efecto sin licencia de anuncios
        sb["audio"]["music"]["ads"] = "si"                     # pista sin licencia de anuncios
        errs, _ = storyboard.validate(sb, ctx())
        joined = "\n".join(errs)
        self.assertIn("no tiene licencia para anuncios y la pieza lleva publicidad", joined)
        self.assertIn("'grabado'", joined)

    def test_unknown_root_key_is_a_warning(self):
        errs, warns = storyboard.validate({**GOOD, "colores": {}}, ctx())
        self.assertEqual(errs, [])
        self.assertTrue(any("colores" in w for w in warns))

    def test_broll_source_timing_rights_and_ads(self):
        sb = json.loads(json.dumps(GOOD))
        clip = {"id": "screen-1", "source": "pantalla-1", "in": 4, "out": 7,
                "source_in": 2, "fit": "cover", "focus_x": 65,
                "origin": "grabación de la persona", "license": "propia", "ads": True}
        sb["broll"] = [clip]
        self.assertEqual(storyboard.validate(sb, ctx())[0], [])
        sb["platforms"]["ads"] = {}
        clip["ads"] = False
        clip["source_in"] = 9
        clip["focus_x"] = 110
        errs, _ = storyboard.validate(sb, ctx())
        self.assertIn("broll[0].ads", "\n".join(errs))
        self.assertIn("broll[0].source_in", "\n".join(errs))
        self.assertIn("broll[0].focus_x", "\n".join(errs))

    def test_region_and_phone_legibility_warning(self):
        sb = json.loads(json.dumps(GOOD))
        clip = {"id": "screen", "source": "pantalla-1", "in": 4, "out": 6,
                "fit": "region", "region": {"x": 0.02, "y": 0.1, "w": 0.30, "h": 0.8},
                "origin": "persona", "license": "propia"}
        sb["broll"] = [clip]
        self.assertEqual(storyboard.validate(sb, ctx()), ([], []))
        clip["region"]["x"] = 0.8
        self.assertIn("broll[0].region", "\n".join(storyboard.validate(sb, ctx())[0]))
        clip["region"]["x"] = 0.02
        clip["fit"] = "contain"
        del clip["region"]
        errs, warns = storyboard.validate(sb, ctx())
        self.assertEqual(errs, [])
        self.assertIn("broll[0].fit", "\n".join(warns))


class TestComposeRefuses(unittest.TestCase):
    def test_compose_reports_all_problems(self):
        with tempfile.TemporaryDirectory() as td:
            chans = Path(td)
            shutil.copytree(ROOT / "channels" / "science-60", chans / "science-60",
                            ignore=shutil.ignore_patterns("projects"))
            P = chans / "science-60" / "projects" / "pieza"
            (P / "captions").mkdir(parents=True)
            (P / "cut").mkdir()
            (P / "captions" / "captions.json").write_text(json.dumps(
                {"words": [{"id": "w0", "w": "hola", "start": 0, "end": 0.5}], "groups": []}))
            (P / "cut" / "cut-map.json").write_text(json.dumps({"duration_s": 20.0, "segments": []}))
            bad = {**GOOD, "overlays": [{"id": "x", "type": "globo", "in": 5, "out": 2}],
                   "audio": {}, "emphasis": {"w42": "keyword"}}
            (P / "storyboard.json").write_text(json.dumps(bad))
            r = subprocess.run([PY, str(ROOT / "scripts" / "pipeline" / "compose.py"), "--project", "science-60/pieza",
                                "--platform", "tiktok"], capture_output=True, text=True,
                               env={**os.environ, "VIDEOVIBE_CHANNELS": str(chans)})
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            out = json.loads(r.stdout)
            self.assertGreaterEqual(len(out["problems"]), 4, out)   # tipo, text, out<in, emphasis
            self.assertFalse((P / "hf").exists(), "no debe empezar a componer")


if __name__ == "__main__":
    unittest.main()
