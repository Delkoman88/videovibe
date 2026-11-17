"""Fase 5: iconos científicos (Health Icons, Bioicons), paquete «sketch» (Rough.js) y «data» (d3). ADR 0029."""
import json
import re
import tempfile
import unittest
from pathlib import Path

import formats
from formats import icons, vendors
from formats.core import CTX
from formats.packs import data as chart

formats.load_packs(["sketch", "data", "motion", "biotech"])
ICONS = Path(icons.__file__).resolve().parent


def render(name, params, d=3.5):
    meta = formats.REGISTRY[name]
    return formats.render({"id": f"s-{name}", "format": name, "in": 0, "out": d, "params": params}, [meta["pack"]])


class IconSetTests(unittest.TestCase):
    def test_sets_are_cc0_clean_and_complete(self):
        for name, minimum in (("health", 60), ("bio", 40)):
            d = json.loads((ICONS / f"{name}.json").read_text())
            self.assertGreaterEqual(len(d["icons"]), minimum, name)
            sel = [ln.strip() for ln in (ICONS / f"selection-{name}.txt").read_text().splitlines()
                   if ln.strip() and not ln.startswith("#")]
            self.assertEqual(sorted(re.sub(r"[^a-z0-9]+", "-", s.split("/", 1)[1].lower()).strip("-") for s in sel),
                             sorted(d["icons"]), name)                       # la selección es la fuente de verdad
            for ident, it in d["icons"].items():
                self.assertEqual(it["license"], "CC0 1.0", ident)
                self.assertNotIn("<style", it["svg"], ident)                 # estilos de clase: se filtrarían a la página
                self.assertNotIn(" class=", it["svg"], ident)
                self.assertNotRegex(it["svg"], r"<(?:inkscape|sodipodi):", ident)
                for ref in re.findall(r'\sid="([^"]+)"', it["svg"]):
                    self.assertTrue(ref.startswith(f"{name}-{ident}-"), (ident, ref))
                if name == "health":
                    self.assertNotIn("#333", it["svg"], ident)

    def test_prefixed_icons(self):
        self.assertTrue(icons.exists("health:dna") and icons.exists("bio:mitochondria"))
        self.assertFalse(icons.exists("bio:no-existe") or icons.exists("otro:dna"))
        svg = icons.icon("health:dna", 64)
        self.assertIn('fill="currentColor"', svg)
        self.assertIn('viewBox="0 0 48 48"', svg)
        self.assertNotIn('fill="currentColor"', icons.icon("bio:mitochondria", 64))   # conserva sus colores
        self.assertTrue(icons.morphable("dna"))
        self.assertFalse(icons.morphable("health:dna"))
        with self.assertRaises(KeyError):
            icons.path_d("health:dna")
        self.assertEqual(len(icons.names()), len(json.loads((ICONS / "lucide.json").read_text())["icons"]))
        self.assertIn("bio:ribosome", icons.all_names())

    def test_used_and_credit(self):
        sb = {"scenes": [{"params": {"steps": [{"icon": "bio:ribosome"}, {"icon": "dna"}, {"icon": "health:lungs"}]}}],
              "overlays": [{"text": "health:dna es texto"}]}
        self.assertEqual(icons.used(sb), {"bio:ribosome", "health:lungs"})
        c = icons.credit("bio:ribosome")
        self.assertEqual((c["set"], c["license"]), ("Bioicons", "CC0 1.0"))
        self.assertIn("bioicons.com", c["source"])

    def test_formats_accept_new_icons(self):
        dd = formats.REGISTRY["draw-diagram"]["check"]
        self.assertEqual(dd({"steps": [{"label": "A", "icon": "health:dna"}, {"label": "B", "icon": "bio:ribosome"}]}), [])
        mi = formats.REGISTRY["morph-icon"]["check"]
        self.assertTrue(any("Lucide" in e for e in mi({"stages": [{"label": "A", "icon": "health:dna"},
                                                                  {"label": "B", "icon": "dna"}]})))
        ln = formats.REGISTRY["lab-network"]
        self.assertEqual(ln["check"](ln["example"]), [])
        self.assertIn('viewBox="0 0 48 48"', render("lab-network", {**ln["example"], "modules": [["Pulmón", "health:lungs"]]}))
        self.assertTrue(ln["check"]({"modules": [["X", "nope"]]}))


class SketchTests(unittest.TestCase):
    def test_examples_render_with_rough(self):
        for name in ("sketch-annotate", "sketch-board", "sketch-diagram"):
            meta = formats.REGISTRY[name]
            self.assertEqual(meta["check"](meta["example"]), [], name)
            self.assertIn("rough", meta["needs"])
            html = render(name, meta["example"])
            self.assertIn("skPad(", html)
            self.assertRegex(html, r'skPad\("[^"]+", \d+\)')                # semilla fija
            self.assertNotIn("Math.random", html)
        self.assertIn("rough.js", vendors.head(formats.needs({"scenes": [{"format": "sketch-board"}]})))

    def test_checks(self):
        an = formats.REGISTRY["sketch-annotate"]["check"]
        self.assertTrue(an({"box": [900, 100, 400, 300]}))                  # se sale del cuadro
        self.assertTrue(an({"box": [100, 100, 300, 300], "shape": "star"}))
        self.assertEqual(an({"box": [100, 600, 300, 300], "shape": "arrow", "label": "Mira"}), [])
        bd = formats.REGISTRY["sketch-board"]["check"]
        self.assertTrue(bd({"items": ["solo una"]}))
        self.assertTrue(bd({"items": ["a", {"text": "b", "icon": "nope"}]}))
        sd = formats.REGISTRY["sketch-diagram"]["check"]
        self.assertTrue(sd({"steps": [{"label": "x" * 30}, {"label": "y"}]}))

    def test_every_shape_renders(self):
        for shape in ("circle", "underline", "box", "arrow", "cross"):
            html = render("sketch-annotate", {"box": [200, 600, 400, 300], "shape": shape, "label": "Aquí"})
            self.assertIn("P.draw(", html, shape)


class DataTests(unittest.TestCase):
    def tearDown(self):
        CTX.pop("piece_dir", None)

    def test_examples_render_with_d3_and_source(self):
        for name in ("chart-bars", "chart-line", "chart-compare"):
            meta = formats.REGISTRY[name]
            self.assertEqual(meta["check"](meta["example"]), [], name)
            html = render(name, meta["example"])
            self.assertIn("d3.scale", html)
            self.assertIn("Fuente: ejemplo", html)
            self.assertIn(CTX["labels"]["illustrative"], html)
            self.assertNotIn("Math.random", html)

    def test_source_and_data_are_checked(self):
        bars = formats.REGISTRY["chart-bars"]["check"]
        joined = "\n".join(bars({"data": [{"label": "A", "value": "x"}]}))
        self.assertIn("source", joined)
        self.assertIn("número", joined)
        self.assertTrue(bars({"source": "s", "data": [[str(i), i] for i in range(9)]}))   # máximo 8 barras
        self.assertTrue(bars({"source": "s", "data": [["una etiqueta larguísima", 1], ["b", 2]]}))
        self.assertTrue(formats.REGISTRY["chart-compare"]["check"]({"source": "s", "data": [["a", 1], ["b", 2], ["c", 3]]}))
        self.assertTrue(formats.REGISTRY["chart-line"]["check"]({"source": "s", "data": [[1, 2], [2, 3]]}))

    def test_files_from_the_piece(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "data").mkdir()
            (Path(tmp) / "data" / "a.csv").write_text("año,casos\n2020,3\n2021,5.5\n2022,9\n", encoding="utf-8")
            (Path(tmp) / "data" / "b.json").write_text(json.dumps([{"label": "Control", "value": 2},
                                                                    {"label": "IA", "value": 7}]), encoding="utf-8")
            CTX["piece_dir"] = tmp
            self.assertEqual(chart.rows({"file": "data/a.csv"}, "line")[1], {"x": 2021.0, "y": 5.5})
            self.assertEqual(chart.rows({"file": "data/b.json"}, "cat")[1], {"label": "IA", "value": 7.0})
            self.assertTrue(formats.REGISTRY["chart-bars"]["check"]({"source": "s", "file": "data/no.csv"}))
        CTX.pop("piece_dir")
        with self.assertRaisesRegex(ValueError, "pieza"):
            chart.rows({"file": "data/a.csv"}, "line")

    def test_compare_delta(self):
        html = render("chart-compare", {"source": "s", "unit": "%", "data": [["A", 20], ["B", 70]]})
        self.assertIn(">×3.5<", html)
        html = render("chart-compare", {"source": "s", "unit": " mg", "decimals": 1, "decimal_comma": True,
                                        "data": [["A", 20], ["B", 25.5]]})
        self.assertIn(">+5,5 mg<", html)


if __name__ == "__main__":
    unittest.main()
