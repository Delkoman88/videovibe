"""Composición visual reproducible y legible."""
import unittest
from types import SimpleNamespace

import formats
from formats import vendors
from scripts.composer.visual import captions_html, overlay_css, overlays_html


class ComposerTests(unittest.TestCase):
    def test_prepare_hf_removes_randomness_from_pixi_vendors(self):
        source = "const a=Math.random(); const b=Math.random()"
        result = vendors.seeded_source(source)
        self.assertNotIn("Math.random()", result)
        self.assertEqual(result.count("globalThis.__videovibeRandom()"), 2)

    def test_captions_timeline_uses_literal_colors_and_full_opacity(self):
        caps = {
            "words": [{"id": "w1", "w": "sueño", "start": 0.0, "end": 0.5}],
            "groups": [{"id": "g1", "in": 0.0, "out": 0.7, "words": ["w1"]}],
        }
        brand = {
            "colors": {"text": "#ffffff", "accent": "#00ffff", "warn": "#ff00aa"},
            "highlight_roles": {"keyword": "accent"},
            "captions": {"size_px": 76, "weight": 650, "shadow": "0 4px 18px #000", "style": "neon"},
        }
        html = captions_html(caps, {"w1": "keyword"}, brand, {"text_bottom": 240},
                             SimpleNamespace(font_faces=""))
        self.assertNotIn('color: "var(--', html)
        self.assertNotIn("opacity: 0.72", html)
        self.assertNotIn("opacity: 0.82", html)
        self.assertIn("0 0 24px #00ffff", html)

    def test_caption_zone_only_moves_overlapping_group(self):
        caps = {
            "words": [
                {"id": "w1", "w": "antes", "start": 1.0, "end": 1.4},
                {"id": "w2", "w": "sentado", "start": 3.0, "end": 3.5},
            ],
            "groups": [
                {"id": "g1", "in": 1.0, "out": 1.5, "words": ["w1"]},
                {"id": "g2", "in": 3.0, "out": 3.6, "words": ["w2"]},
            ],
        }
        brand = {
            "colors": {"text": "#ffffff", "accent": "#00ffff", "warn": "#ff00aa"},
            "highlight_roles": {},
            "captions": {"size_px": 76, "weight": 650, "shadow": "0 4px 18px #000"},
        }
        html = captions_html(
            caps, {}, brand, {"text_bottom": 240}, SimpleNamespace(font_faces=""),
            zones=[{"in": 2.8, "out": 4.0, "position": "upper-left"}],
        )
        self.assertIn("bottom: 920px", html)
        self.assertIn('id="g1" class="cap clip"', html)
        self.assertIn('id="g2" class="cap clip zone-upper-left"', html)

    def test_caption_zones_work_in_neon_style_too(self):
        caps = {"words": [{"id": "w1", "w": "sentado", "start": 3.0, "end": 3.5}],
                "groups": [{"id": "g1", "in": 3.0, "out": 3.6, "words": ["w1"]}]}
        brand = {"colors": {"text": "#fff", "accent": "#0ff", "warn": "#f0a"}, "highlight_roles": {},
                 "captions": {"size_px": 76, "weight": 650, "shadow": "none", "style": "neon"}}
        html = captions_html(caps, {}, brand, {"text_bottom": 240}, SimpleNamespace(font_faces=""),
                             zones=[{"in": 2.8, "out": 4.0, "position": "upper-center"}])
        self.assertIn('class="cap clip zone-upper-center"', html)
        self.assertIn(".zone-upper-center { bottom: 920px; }", html)


class OptInStylesTests(unittest.TestCase):
    """Lo del canal de DJ (neón, liquid, Pixi) es opcional: sin pedirlo, el HTML es el de siempre."""
    BRAND = {"colors": {"text": "#fff", "accent": "#0ff", "warn": "#f0a"},
             "highlight_roles": {"keyword": "accent"},
             "captions": {"size_px": 72, "weight": 700, "shadow": "none"}}
    CAPS = {"words": [{"id": "w1", "w": "hola", "start": 0.0, "end": 0.4}],
            "groups": [{"id": "g1", "in": 0.0, "out": 0.6, "words": ["w1"]}]}

    def test_default_captions_are_classic_without_zone_css(self):
        html = captions_html(self.CAPS, {}, self.BRAND, {"text_bottom": 240}, SimpleNamespace(font_faces=""))
        self.assertIn('tl.fromTo("#w1", {opacity: 0.62}', html)
        self.assertNotIn("zone-upper", html)
        self.assertNotIn("steps(2)", html)

    def test_default_overlays_are_panels(self):
        self.assertIn("corner", overlay_css(self.BRAND, 200))
        self.assertNotIn("liquid", overlay_css(self.BRAND, 200))
        liquid = {**self.BRAND, "overlays": {"style": "liquid"}}
        self.assertIn("liquid-main", overlay_css(liquid, 200))
        sb = {"overlays": [{"id": "t1", "type": "title", "in": 0, "out": 2, "text": "Hola"}]}
        ctx = SimpleNamespace(font_faces="")
        self.assertIn('class="corner tl"', overlays_html(sb, self.BRAND, {"text_top": 200}, ctx))
        self.assertIn("LIVE SIGNAL", overlays_html(sb, liquid, {"text_top": 200}, ctx))

    def test_pixi_only_when_a_scene_needs_it(self):
        formats.load_packs(["music"])
        head = lambda sb: vendors.head(formats.needs(sb))  # noqa: E731
        self.assertEqual(head({"scenes": [{"format": "signal-spell"}]}), head({}))
        self.assertNotIn("pixi", head({}))
        self.assertIn("pixi.min.js", head({"scenes": [{"format": "pixi-signal"}]}))
        self.assertEqual(formats.needs({"scenes": [{"format": "pixi-mixer"}]}), {"pixi"})


if __name__ == "__main__":
    unittest.main()
