"""Límites que impiden volver a crecer sin control (AGENTS.md → «Al terminar una sesión de desarrollo»).

Si una prueba falla, no se sube el límite: se reorganiza (historia al CHANGELOG, detalle al ADR,
archivo largo dividido por responsabilidad).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS_MAX = 100
CODE_MAX = 600
CHANGELOG_ENTRY_MAX = 12
CHANGELOG_SINCE = (0, 13, 0)


class Budget(unittest.TestCase):
    def test_status_is_a_snapshot(self):
        text = (ROOT / "docs/status/STATUS.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), STATUS_MAX, "STATUS.md: solo la foto de hoy")
        for phrase in ("en esta sesión", "se corrigió", "se corrigieron"):
            self.assertNotIn(phrase, text.lower(), f"STATUS.md cuenta historia: «{phrase}»")

    def test_code_files_stay_small(self):
        files = [p for d in ("scripts", "formats") for p in (ROOT / d).rglob("*.py")
                 if "tests" not in p.parts and "__pycache__" not in p.parts]
        files += [p for p in (ROOT / "bin").iterdir() if p.is_file()]
        big = [f"{p.relative_to(ROOT)}: {n}" for p in files
               if (n := len(p.read_text(encoding="utf-8", errors="ignore").splitlines())) > CODE_MAX]
        self.assertEqual(big, [], f"más de {CODE_MAX} líneas: divídelo por responsabilidad")

    def test_adr_index_is_complete_and_flat(self):
        folder = ROOT / "docs/decisions"
        index = (folder / "README.md").read_text(encoding="utf-8")
        rows = dict(re.findall(r"^\| (\d{4}) \| .*\| ([^|]+?) \|$", index, re.M))
        for adr in sorted(folder.glob("[0-9][0-9][0-9][0-9]-*.md")):
            num = adr.name[:4]
            self.assertIn(num, rows, f"{adr.name} falta en la tabla de docs/decisions/README.md")
            self.assertRegex(rows[num], r"^(vigente|reemplazada por \d{4})", adr.name)
            text = adr.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^## (Revisión|Actualización)", f"{adr.name}: reescríbelo como una sola decisión")

    def test_changelog_entries_are_short(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for m in re.finditer(r"(?ms)^## (\d+)\.(\d+)\.(\d+)\S*.*?\n(.*?)(?=^## |\Z)", text):
            version = tuple(int(x) for x in m.groups()[:3])
            if version < CHANGELOG_SINCE:
                continue
            lines = [ln for ln in m.group(4).splitlines() if ln.strip()]
            self.assertLessEqual(len(lines), CHANGELOG_ENTRY_MAX, f"CHANGELOG {'.'.join(map(str, version))}: 5–8 líneas")


if __name__ == "__main__":
    unittest.main()
