"""Paquete «motion», texto cinético y text_fx de tarjetas."""
import unittest
from types import SimpleNamespace

import formats
from formats import icons
from formats.packs import motion
from scripts.composer.visual import overlays_html
from scripts.validation.overlays import validate as validate_overlays

formats.load_packs(["motion"])


class ValueParsingTests(unittest.TestCase):
    def test_numbers_in_spanish_and_english(self):
        self.assertEqual(motion._parse_value("87%"), ("", 87.0, "%", 0, "", "."))
        self.assertEqual(motion._parse_value("3.500"), ("", 3500.0, "", 0, ".", "."))
        self.assertEqual(motion._parse_value("1,2 M")[1:4], (1.2, " M", 1))
        self.assertEqual(motion._parse_value("$12.5k")[:4], ("$", 12.5, "k", 1))
        self.assertEqual(motion._parse_value("1,000,000")[1], 1000000.0)
        self.assertIsNone(motion._parse_value("muchos"))


class ChecksTests(unittest.TestCase):
    def check(self, fmt, params):
        return formats.REGISTRY[fmt]["check"](params)

    def test_steps_need_valid_icons_and_counts(self):
        self.assertEqual(self.check("draw-diagram", formats.REGISTRY["draw-diagram"]["example"]), [])
        self.assertTrue(self.check("draw-diagram", {"steps": [{"icon": "dna", "label": "solo uno"}]}))
        errs = self.check("morph-icon", {"stages": [["Idea", "no-existe"], ["Hecho", "check"]]})
        self.assertTrue(any("no-existe" in e for e in errs))
        self.assertEqual(self.check("path-journey", {"stops": [{"label": "A"}, {"label": "B"}]}), [])

    def test_variant_and_value(self):
        self.assertTrue(self.check("kinetic-title", {"text": "x", "variant": "spin"}))
        self.assertTrue(self.check("data-reveal", {"value": "muchos", "label": "x"}))

    def test_every_example_renders_and_declares_known_needs(self):
        for name, meta in formats.REGISTRY.items():
            if meta["pack"] != "motion":
                continue
            html = formats.render({"id": f"s-{name}", "format": name, "in": 0, "out": 3, "params": meta["example"]},
                                  ["motion"])
            self.assertIn(f'window.__timelines["s-{name}"]', html)
            self.assertNotIn("Math.random", html)


class IconsPathTests(unittest.TestCase):
    def test_every_icon_converts_to_one_path(self):
        for n in icons.names():
            self.assertTrue(icons.path_d(n).startswith(("M", "m")), n)


class TextFxTests(unittest.TestCase):
    BRAND = {"colors": {"text": "#fff", "accent": "#0ff", "warn": "#f0a"}, "highlight_roles": {"keyword": "accent"},
             "captions": {"size_px": 72, "weight": 700, "shadow": "none"}}

    def test_text_fx_splits_letters_only_when_asked(self):
        ctx = SimpleNamespace(font_faces="")
        plain = overlays_html({"overlays": [{"id": "t1", "type": "title", "in": 0, "out": 2, "text": "Hola"}]},
                              self.BRAND, {"text_top": 200}, ctx)
        fx = overlays_html({"overlays": [{"id": "t1", "type": "title", "in": 0, "out": 2, "text": "Hola",
                                          "text_fx": "wave"}]}, self.BRAND, {"text_top": 200}, ctx)
        self.assertNotIn('class="ch"', plain)
        self.assertNotIn(".kwi", plain)
        self.assertEqual(fx.count('class="ch"'), 4)
        self.assertIn('tl.fromTo("#t1 .t1 .ch"', fx)

    def test_validator_rejects_text_fx_on_cta_and_unknown_variant(self):
        state = SimpleNamespace(ctx={}, errs=[], warns=[], dur=10, end=10, ids=set(),
                                span=lambda *a, **k: None, sound=lambda *a: None, ads_plats=[])
        validate_overlays({"overlays": [
            {"id": "c", "type": "cta", "in": 0, "out": 2, "text": "x", "text_fx": "rise"},
            {"id": "t", "type": "title", "in": 0, "out": 2, "text": "x", "text_fx": "spin"}]}, state)
        self.assertEqual(len(state.errs), 2)


if __name__ == "__main__":
    unittest.main()
