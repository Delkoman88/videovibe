"""Librerías de animación opcionales (formats/vendors.py, ADR 0022)."""
import tempfile
import unittest
from pathlib import Path

import formats
from formats import vendors
from scripts.core import oslib

NODE = oslib.ROOT / "node_modules"


class VendorsTests(unittest.TestCase):
    def test_without_needs_only_gsap(self):
        self.assertEqual(vendors.head(set()), '    <script src="assets/vendor/gsap.min.js"></script>\n')

    def test_pixi_head_is_byte_identical_to_0_10(self):
        """El orden y el texto de 0.10.0 se conservan: las piezas aprobadas con Pixi no cambian."""
        expected = ("    <script>\n      globalThis.__videovibeSeed = 0x4d524c4e;\n"
                    "      globalThis.__videovibeRandom = () => {\n"
                    "        let x = globalThis.__videovibeSeed >>> 0;\n"
                    "        x ^= x << 13; x ^= x >>> 17; x ^= x << 5;\n"
                    "        globalThis.__videovibeSeed = x >>> 0;\n"
                    "        return globalThis.__videovibeSeed / 4294967296;\n      };\n    </script>\n"
                    '    <script src="assets/vendor/pixi.min.js"></script>\n'
                    '    <script src="assets/vendor/pixi-filters.js"></script>\n'
                    '    <script src="assets/vendor/gsap.min.js"></script>\n')
        self.assertEqual(vendors.head({"pixi"}), expected)

    def test_gsap_plugins_load_after_gsap_and_register(self):
        h = vendors.head({"gsap:SplitText", "gsap:DrawSVGPlugin"})
        self.assertLess(h.index("gsap.min.js"), h.index("SplitText.min.js"))
        self.assertIn("gsap.registerPlugin(SplitText, DrawSVGPlugin);", h)
        self.assertNotIn("__videovibeRandom", h)  # ninguno de los dos usa azar
        self.assertIn("__videovibeRandom", vendors.head({"gsap:ScrambleTextPlugin"}))

    def test_every_declared_file_exists_in_node_modules(self):
        for key in vendors.VENDORS:
            for src, _, _ in vendors.files({key}):
                self.assertTrue((NODE / src).exists(), f"{key}: falta node_modules/{src} (npm ci)")

    def test_copy_only_what_is_needed_and_cleans_leftovers(self):
        with tempfile.TemporaryDirectory() as d:
            vd = Path(d) / "vendor"
            self.assertEqual(vendors.copy({"pixi"}, NODE, vd), [])
            self.assertNotIn("Math.random()", (vd / "pixi.min.js").read_text())
            self.assertEqual(vendors.copy(set(), NODE, vd), [])
            self.assertEqual(sorted(p.name for p in vd.iterdir()), ["gsap.min.js"])
            mtime = (vd / "gsap.min.js").stat().st_mtime_ns
            vendors.copy(set(), NODE, vd)  # sin cambios no reescribe
            self.assertEqual((vd / "gsap.min.js").stat().st_mtime_ns, mtime)

    def test_unknown_library_is_rejected(self):
        with self.assertRaises(KeyError):
            formats.core.fmt("x-bad", needs=("babylon",))
        with self.assertRaises(KeyError):
            vendors.copy({"babylon"}, NODE, Path(tempfile.gettempdir()) / "vv-none")

    def test_registered_formats_only_declare_known_libraries(self):
        formats.load_packs(formats.available_packs())
        for name, meta in formats.REGISTRY.items():
            self.assertEqual(vendors.unknown(meta["needs"]), [], name)


if __name__ == "__main__":
    unittest.main()


class IconsTests(unittest.TestCase):
    def test_icons_render_and_validate(self):
        from formats import icons
        self.assertGreaterEqual(len(icons.names()), 70)
        svg = icons.icon("dna", 120, cls="ic")
        self.assertTrue(svg.startswith('<svg class="ic" width="120"'))
        self.assertIn('stroke="currentColor"', svg)
        with self.assertRaises(KeyError):
            icons.icon("no-existe")

    def test_selection_and_json_agree(self):
        from formats import icons
        sel = [line.strip() for line in (oslib.ROOT / "formats/icons/selection.txt").read_text().splitlines()
               if line.strip() and not line.startswith("#")]
        self.assertEqual(sorted(sel), icons.names())


class GalleryTests(unittest.TestCase):
    def test_gallery_project_has_one_scene_per_format(self):
        from scripts.tools import gallery
        with tempfile.TemporaryDirectory() as d:
            hf, sb = gallery.build("science-60", out=Path(d) / "hf")
            names = [s["format"] for s in sb["scenes"]]
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(sorted(p.name for p in (hf / "compositions").iterdir()),
                             sorted(f"scene-g-{n}.html" for n in names))
            index = (hf / "index.html").read_text()
            self.assertIn('data-composition-id="root"', index)
            self.assertNotIn("bubble", "".join(s["layout"] for s in sb["scenes"]))
