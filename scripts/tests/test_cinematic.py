"""3D cinematográfico: paquete «cinematic», build de Three.js, biblioteca de modelos .glb (ADR 0027)."""
import base64
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

import formats
from formats import vendors
from scripts.composer import data
from scripts.core import assetlib, glb, oslib

formats.load_packs(["cinematic"])
NAMES = ("particle-word", "logo-3d", "cell-journey", "model-showcase", "space-field")
NODE = oslib.ROOT / "node_modules"


def render(name, params, d=3):
    return formats.render({"id": f"s-{name}", "format": name, "in": 0, "out": d, "params": params}, ["cinematic"])


class CinematicFormatTests(unittest.TestCase):
    def test_examples_render_with_three_and_one_clock(self):
        for name in NAMES:
            meta = formats.REGISTRY[name]
            self.assertEqual(meta["needs"], ("three",), name)
            self.assertEqual(meta["pack"], "cinematic")
            if meta["check"]:
                self.assertEqual(meta["check"](meta["example"]), [], name)
            html = render(name, meta["example"])
            self.assertIn("vvCine(", html)
            self.assertIn("onUpdate: () => draw(st.t)", html)       # un solo reloj: la línea de tiempo dibuja
            for banned in ("requestAnimationFrame", "Date.now", "performance.now", "Math.random", "setTimeout"):
                self.assertNotIn(banned, html, f"{name}: {banned}")

    def test_checks(self):
        pw = formats.REGISTRY["particle-word"]["check"]
        self.assertTrue(pw({"text": "UNA FRASE DEMASIADO LARGA"}))
        self.assertTrue(pw({"text": "ADN", "count": 100}))
        self.assertTrue(formats.REGISTRY["logo-3d"]["check"]({"text": ""}))
        ms = formats.REGISTRY["model-showcase"]
        self.assertTrue(ms["check"]({"model": "flask", "degrees": 1000}))
        self.assertEqual(ms["uses"]({"model": "flask"}), [("models", "flask")])
        self.assertTrue(formats.REGISTRY["cell-journey"]["check"]({"density": 5}))

    def test_text_is_escaped_into_js(self):
        html = render("particle-word", {"text": 'A"B</script>'})
        self.assertNotIn('B</script>', html)
        self.assertIn('A\\"B<\\/script>', html)

    def test_needs_only_when_a_scene_uses_it(self):
        self.assertEqual(vendors.head(set()), '    <script src="assets/vendor/gsap.min.js"></script>\n')
        h = vendors.head(formats.needs({"scenes": [{"format": "logo-3d"}]}))
        self.assertIn("three-pack.min.js", h)
        self.assertIn("__videovibeRandom", h)           # Three usa Math.random (uuid): se redirige a la semilla fija
        self.assertLess(h.index("gsap.min.js"), h.index("three-pack.min.js"))


@unittest.skipUnless((NODE / "three" / "package.json").exists() and (NODE / ".bin" / "esbuild").exists(),
                     "sin node_modules (npm ci)")
class ThreeBuildTests(unittest.TestCase):
    def test_build_is_cached_and_reproducible(self):
        out = vendors.build("three", NODE)
        first = hashlib.sha256(out.read_bytes()).hexdigest()
        mtime = out.stat().st_mtime_ns
        self.assertEqual(vendors.build("three", NODE).stat().st_mtime_ns, mtime)   # huella igual: no recompila
        out.with_suffix(".stamp").unlink()
        self.assertEqual(hashlib.sha256(vendors.build("three", NODE).read_bytes()).hexdigest(), first)
        text = out.read_text(encoding="utf-8")
        for name in ("THREE", "POSTPROCESSING", "THREE_ADDONS"):
            self.assertIn(name, text)

    def test_copy_seeds_randomness(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(vendors.copy({"three"}, NODE, Path(tmp)), [])
            js = (Path(tmp) / "three-pack.min.js").read_text(encoding="utf-8")
            self.assertNotIn("Math.random()", js)
            self.assertIn("globalThis.__videovibeRandom()", js)

    def test_missing_packages_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(vendors.copy({"three"}, Path(tmp), Path(tmp) / "vendor"))


class ModelLibraryTests(unittest.TestCase):
    def test_flask_roundtrip_and_engine_library(self):
        it = assetlib.item("models", "flask")
        self.assertEqual(assetlib.problems("models", "flask", ads=True), [])
        s = glb.summary(Path(it["path"]).read_bytes())
        self.assertEqual((s["meshes"], s["textures"]), (2, 0))
        self.assertGreater(s["triangles"], 1000)

    def test_bad_files(self):
        with self.assertRaises(ValueError):
            glb.summary(b"not a glb at all, sorry")
        g = {"asset": {"version": "2.0"}, "buffers": [{"uri": "mesh.bin", "byteLength": 4}], "meshes": [{}]}
        js = json.dumps(g).encode()
        js += b" " * (-len(js) % 4)
        data_ = struct.pack("<III", glb.MAGIC, 2, 20 + len(js)) + struct.pack("<II", len(js), glb.JSON_T) + js
        with self.assertRaisesRegex(ValueError, "externos"):
            glb.summary(data_)

    def test_served_as_base64_without_network(self):
        it = assetlib.item("models", "flask")
        payload = json.loads(data._payload("models", it, {}))
        self.assertEqual(base64.b64decode(payload["glb"]), Path(it["path"]).read_bytes())
        self.assertEqual(data.script_name("models", "flask"), "models-flask.js")


if __name__ == "__main__":
    unittest.main()
