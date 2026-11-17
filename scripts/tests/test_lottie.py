"""Animaciones Lottie: biblioteca, validación, recoloreo, datos locales y créditos (ADR 0023)."""
import json
import tempfile
import unittest
from pathlib import Path

import formats
from formats import vendors
from scripts.composer import credits, data
from scripts.core import assetlib, lottielib, oslib
from scripts.tools import lottie_builtins

formats.load_packs(["lottie"])
BRAND = {"colors": {"accent": "#112233", "accent2": "#445566", "accent3": "#778899", "warn": "#aa0000",
                    "text": "#ffffff", "muted": "#888888", "surface": "#111111", "bg": "#000000"}}


def builtin(ident):
    return json.loads((oslib.ROOT / "assets" / "lottie" / f"{ident}.json").read_text())


class LottieLibTests(unittest.TestCase):
    def test_builtins_are_valid_and_regenerate_identically(self):
        for ident, (fn, _, _) in lottie_builtins.BUILTINS.items():
            anim = fn()
            self.assertEqual(lottielib.problems(anim), [], ident)
            self.assertEqual(json.loads(json.dumps(anim)), builtin(ident), f"{ident}: corre lottie_builtins.py")

    def test_external_images_and_missing_keys_are_rejected(self):
        anim = builtin("check-draw")
        bad = {**anim, "assets": [{"id": "img", "u": "images/", "p": "foto.png"}]}
        self.assertTrue(any("imagen externa" in e for e in lottielib.problems(bad)))
        self.assertTrue(lottielib.problems({"layers": []}))

    def test_palette_auto_map_and_recolor(self):
        anim = builtin("pulse-rings")
        self.assertEqual({h for h, _ in lottielib.palette(anim)}, {"#00e5ff", "#7cff4f", "#b14dff"})
        auto = lottielib.auto_map(anim)
        self.assertEqual(sorted(auto.values()), ["accent", "accent2", "accent3"])
        out = lottielib.recolor(anim, {"#00e5ff": "accent"}, BRAND["colors"])
        self.assertIn("#112233", {h for h, _ in lottielib.palette(out)})
        self.assertIn("#00e5ff", {h for h, _ in lottielib.palette(anim)})  # el original no cambia
        self.assertTrue(lottielib.map_problems({"#000000": "neon"}))

    def test_dotlottie_zip(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.lottie"
            with zipfile.ZipFile(f, "w") as z:
                z.writestr("manifest.json", "{}")
                z.writestr("animations/a.json", json.dumps(builtin("eq-bars")))
            self.assertEqual(lottielib.load(f)["nm"], "eq-bars")


class AssetLibTests(unittest.TestCase):
    def test_channel_overrides_engine_and_problems(self):
        with tempfile.TemporaryDirectory() as d:
            ch = Path(d)
            self.assertIn("check-draw", assetlib.library("lottie", ch))
            (ch / "assets" / "lottie").mkdir(parents=True)
            (ch / "assets" / "lottie" / "mia.json").write_text(json.dumps(builtin("check-draw")))
            assetlib.save("lottie", ch, {"id": "mia", "file": "mia.json", "origin": "x", "license": "", "ads": False})
            self.assertTrue(any("licencia" in e for e in assetlib.problems("lottie", "mia", ch)))
            assetlib.save("lottie", ch, {"id": "mia", "file": "mia.json", "origin": "x", "license": "CC0", "ads": False})
            self.assertEqual(assetlib.problems("lottie", "mia", ch), [])
            self.assertTrue(any("anuncios" in e for e in assetlib.problems("lottie", "mia", ch, ads=True)))
            self.assertTrue(assetlib.problems("lottie", "no-existe", ch))
            self.assertEqual(assetlib.item("lottie", "mia", ch)["scope"], "canal")


class SceneDataTests(unittest.TestCase):
    SB = {"scenes": [{"id": "s1", "format": "lottie-scene", "in": 0, "out": 3, "params": {"anim": "check-draw"}},
                     {"id": "s2", "format": "lottie-accent", "in": 4, "out": 6, "params": {"anim": "check-draw"}}]}

    def test_data_files_head_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            hf = Path(d)
            (hf / "assets" / "data").mkdir(parents=True)
            (hf / "assets" / "data" / "lottie-viejo.js").write_text("x")
            used = data.write(hf, self.SB, None, BRAND)
            self.assertEqual([u["id"] for u in used], ["check-draw"])  # sin repetir
            self.assertEqual(sorted(p.name for p in (hf / "assets" / "data").iterdir()), ["lottie-check-draw.js"])
            js = (hf / "assets" / "data" / "lottie-check-draw.js").read_text()
            self.assertTrue(js.startswith('(window.__vv = window.__vv || {})["lottie:check-draw"] = {'))
            self.assertIn("0.0667,0.1333,0.2", js)  # accent #112233 de la marca
            self.assertEqual(data.head(self.SB), '    <script src="assets/data/lottie-check-draw.js"></script>\n')
            self.assertEqual(data.head({}), "")

    def test_lottie_vendor_renames_global(self):
        h = vendors.head({"lottie"})
        self.assertIn("lottie_svg.min.js", h)
        self.assertIn("globalThis.__vvLottie = globalThis.lottie; delete globalThis.lottie;", h)

    def test_checks(self):
        chk = formats.REGISTRY["lottie-scene"]["check"]
        self.assertEqual(chk({"anim": "x", "loops": "fill", "speed": 1.5, "from": 0.2, "to": 1}), [])
        self.assertEqual(len(chk({"anim": "x", "loops": 0, "speed": 9, "from": 2, "to": 1})), 3)

    def test_credits_block_only_when_used(self):
        with tempfile.TemporaryDirectory() as d:
            P = Path(d)
            credits.update_animation_credits(P, [])
            self.assertFalse((P / "assets.md").exists())  # nada que registrar: no se crea
            it = assetlib.item("lottie", "check-draw")
            credits.update_animation_credits(P, [{"kind": "lottie", **it}])
            txt = (P / "assets.md").read_text()
            self.assertIn("Animación Lottie «check-draw»", txt)
            credits.update_animation_credits(P, [])
            self.assertNotIn("check-draw", (P / "assets.md").read_text())


if __name__ == "__main__":
    unittest.main()


class ValidationTests(unittest.TestCase):
    def test_storyboard_checks_library_license_and_ads(self):
        from scripts.tests.test_storyboard import ctx
        from scripts.pipeline import storyboard
        with tempfile.TemporaryDirectory() as d:
            ch = Path(d)
            (ch / "assets" / "lottie").mkdir(parents=True)
            (ch / "assets" / "lottie" / "mia.json").write_text(json.dumps(builtin("eq-bars")))
            assetlib.save("lottie", ch, {"id": "mia", "file": "mia.json", "origin": "x", "license": "LS", "ads": False})
            c = {**ctx(), "formats": formats.registry(("lottie",)), "channel_dir": ch}
            sb = {"scenes": [{"id": "a", "format": "lottie-scene", "in": 1, "out": 3, "params": {"anim": "mia"}},
                             {"id": "b", "format": "lottie-accent", "in": 4, "out": 6, "params": {"anim": "nada"}}],
                  "platforms": {"tiktok": {}}}
            errs, _ = storyboard.validate(sb, c)
            self.assertEqual(len(errs), 1)
            self.assertIn("«nada» no está en la biblioteca", errs[0])
            sb["scenes"].pop()
            sb["platforms"]["ads"] = {}
            errs, _ = storyboard.validate(sb, c)
            self.assertTrue(any("anuncios" in e for e in errs), errs)
