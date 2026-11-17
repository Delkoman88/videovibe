"""Estructuras moleculares: resumen, selección, datos locales y formatos del paquete «molecular» (ADR 0024)."""
import json
import tempfile
import unittest
from pathlib import Path

import formats
from formats import vendors
from scripts.composer import data
from scripts.core import assetlib, oslib, structlib

formats.load_packs(["molecular"])
STRUCT = oslib.ROOT / "assets" / "structures"


class StructLibTests(unittest.TestCase):
    def test_pdb_summary_chains_ranges_ligands(self):
        s = structlib.summary((STRUCT / "hemoglobin.pdb").read_text(), "pdb")
        self.assertEqual(s["chains"], {"A": 141, "B": 146})
        self.assertEqual(s["residues"]["A"], [1, 141])
        self.assertIn("HEM", s["ligands"])
        self.assertNotIn("HOH", s["ligands"])

    def test_sdf_summary(self):
        s = structlib.summary((STRUCT / "aspirin.sdf").read_text(), "sdf")
        self.assertEqual(s["atoms"], 21)

    def test_selection_problems(self):
        it = assetlib.item("structures", "hemoglobin")
        self.assertEqual(structlib.selection_problems({"chain": "A", "resn": "HEM"}, it), [])
        self.assertTrue(structlib.selection_problems({"chain": "Z"}, it))
        self.assertTrue(structlib.selection_problems({"chain": "A", "resi": [500]}, it))

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            structlib.fetch_pdb("XX")
        with self.assertRaises(ValueError):
            structlib.fmt_of("a.xyz")

    def test_engine_library_is_valid(self):
        lib = assetlib.library("structures")
        self.assertEqual(set(lib), {"crambin", "hemoglobin", "dna-dodecamer", "aspirin", "caffeine"})
        for ident in lib:
            self.assertEqual(assetlib.problems("structures", ident, ads=True), [], ident)


class MolecularFormatTests(unittest.TestCase):
    def test_examples_render_with_3dmol_and_uses(self):
        for name in ("molecule-spin", "molecule-focus", "molecule-compare"):
            meta = formats.REGISTRY[name]
            html = formats.render({"id": f"s-{name}", "format": name, "in": 0, "out": 3, "params": meta["example"]},
                                  ["molecular"])
            self.assertIn("vvMol(", html)
            self.assertEqual(meta["needs"], ("3dmol",))
            self.assertEqual(meta["check"](meta["example"]), [], name)
        compare = formats.REGISTRY["molecule-compare"]
        self.assertEqual([i for _, i in compare["uses"](compare["example"])], ["aspirin", "caffeine"])
        self.assertNotIn(">None<", formats.render({"id": "c", "format": "molecule-compare", "in": 0, "out": 3,
                                                    "params": compare["example"]}, ["molecular"]))

    def test_checks(self):
        spin = formats.REGISTRY["molecule-spin"]["check"]
        self.assertEqual(len(spin({"structure": "x", "style": "neon", "color": "rosa", "degrees": 9999, "zoom": 9})), 4)
        focus = formats.REGISTRY["molecule-focus"]
        self.assertTrue(focus["check"]({"structure": "x", "focus": {"site": 1}, "label": "x"}))
        items = {"hemoglobin": assetlib.item("structures", "hemoglobin")}
        self.assertTrue(focus["check_items"]({"structure": "hemoglobin", "focus": {"chain": "Q"}}, items))

    def test_structure_data_and_vendor(self):
        sb = {"scenes": [{"id": "s", "format": "molecule-spin", "in": 0, "out": 3, "params": {"structure": "crambin"}}]}
        with tempfile.TemporaryDirectory() as d:
            used = data.write(Path(d), sb, None, {"colors": {}})
            js = (Path(d) / "assets" / "data" / "structures-crambin.js").read_text()
            payload = json.loads(js.split("] = ", 1)[1].rstrip(";\n"))
            self.assertEqual(payload["format"], "pdb")
            self.assertIn("ATOM", payload["text"])
            self.assertEqual(used[0]["license"], structlib.LICENSES["pdb"])
        self.assertIn("3Dmol-min.js", vendors.head({"3dmol"}))
        self.assertIn("__videovibeRandom", vendors.head({"3dmol"}))


if __name__ == "__main__":
    unittest.main()
