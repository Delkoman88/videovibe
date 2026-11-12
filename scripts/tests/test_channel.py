"""Canales: plantilla y canales reales válidos, resolución de canal, idiomas y sin rutas fijas a profile/."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.tools import check_channel  # noqa: E402
from scripts.core import oslib  # noqa: E402

LANG_KEYS = {"code", "whisper", "fillers_drop", "fillers_suggest", "connectors_lone", "hallucinations",
             "captions", "vocab_label", "labels"}


class TestChannels(unittest.TestCase):
    def test_template_is_structurally_valid(self):
        self.assertEqual(check_channel.check("_template", allow_todo=True), [])

    def test_template_requires_completion(self):
        self.assertTrue(any("TODO" in p for p in check_channel.check("_template")))

    def test_engine_channels_complete(self):
        for d in sorted(oslib.ENGINE_CHANNELS.iterdir()):
            if d.is_dir() and not d.name.startswith(("_", "zz-")):
                self.assertEqual(check_channel.check(d.name), [], d.name)

    def test_load_channel_from_project_path(self):
        P = oslib.channel_path("science-60") / "projects"
        ch = oslib.load_channel(P)
        self.assertEqual(ch["id"], "science-60")
        self.assertEqual(ch["lang"]["code"], "es")
        self.assertIn("Ciencia en 60 segundos", ch["vocab"])
        self.assertIn("accent", ch["brand"]["colors"])

    def test_channels_dir_configurable(self):
        env = {**__import__("os").environ, "VIDEOVIBE_CHANNELS": "/tmp/canales-x"}
        out = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'scripts'); from scripts.core import oslib; "
                              "print(oslib.CHANNELS); print(oslib.channel_path('science-60'))"],
                             capture_output=True, text=True, env=env, cwd=ROOT).stdout.split()
        self.assertEqual(out[0], str(Path("/tmp/canales-x").resolve()))
        self.assertEqual(out[1], str(ROOT / "channels" / "science-60"), "los canales del motor siguen visibles")

    def test_language_packs_have_required_keys(self):
        for f in sorted(oslib.LANG_DIR.glob("*.json")):
            self.assertEqual(LANG_KEYS - set(json.loads(f.read_text())), set(), f.name)

    def test_engine_has_no_personal_data(self):
        """El motor es público: ni código ni documentos mencionan canales o personas reales."""
        pattern = "|".join(["Ed" + "gar", "Man" + "cilla", "Open " + "Science", "proyecto-" + "open-science",
                            "Delko" + "man", "gm" + "ail", "ROG " + "Ally", "video-" + "studio"])
        paths = [ROOT / x for x in ("scripts", "formats", "bin", "docs", "lang", "presets", "templates",
                                    "channels/_template", "channels/science-60", ".agents", "AGENTS.md",
                                    "README.md", "package.json")]
        out = subprocess.run(["grep", "-rnIiE", pattern, *map(str, paths)], capture_output=True, text=True).stdout
        repo_url = "github.com/" + "Delko" + "man88/videovibe"  # la URL pública del proyecto sí puede aparecer
        offending = [l for l in out.splitlines() if "/tests/test_channel.py" not in l
                     and re.search(pattern, l.split(":", 2)[-1].replace(repo_url, ""), re.I)]
        self.assertEqual(offending, [], "\n".join(offending))


if __name__ == "__main__":
    unittest.main()
