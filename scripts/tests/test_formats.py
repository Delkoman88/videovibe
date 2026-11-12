"""Cada formato (core + todos los paquetes) genera HTML válido para HyperFrames con su ejemplo."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import formats  # noqa: E402


class TestFormats(unittest.TestCase):
    def test_every_format_renders_its_example(self):
        packs = formats.available_packs()
        reg = formats.registry(packs)
        self.assertIn("terminal", reg)
        self.assertIn("lab-network", reg)  # paquete biotech
        formats.configure("@font-face{}", {"illustrative": "ILLUSTRATIVE"})
        for name, meta in reg.items():
            html = formats.render({"id": f"t-{name}", "format": name, "in": 0, "out": 4.0,
                                   "params": meta["example"]}, packs)
            self.assertIn(f'window.__timelines["t-{name}"]', html, name)
            self.assertTrue(html.lstrip().startswith("<template>"), name)
            self.assertNotIn("Math.random", html, name)
            self.assertNotRegex(html, r"\{esc\(|\{p\[|\{CTX", f"{name}: f-string sin resolver")
            self.assertNotIn("Space Grotesk", html, name)  # fuentes vía variables de marca
            ids = re.findall(r'id="([^"]+)"', html)
            self.assertEqual(len(ids), len(set(ids)), f"ids repetidos en {name}")
            self.assertTrue(meta["doc"], f"{name} sin docstring (lo usa el catálogo)")

    def test_missing_required_param_fails(self):
        with self.assertRaises(ValueError):
            formats.render({"id": "x", "format": "terminal", "in": 0, "out": 2, "params": {}})

    def test_pack_not_enabled_is_unavailable(self):
        with self.assertRaises(KeyError):
            formats.render({"id": "x", "format": "dna-helix", "in": 0, "out": 2, "params": {}}, packs=())


if __name__ == "__main__":
    unittest.main()
