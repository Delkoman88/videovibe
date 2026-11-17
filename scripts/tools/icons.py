#!/usr/bin/env python3
"""Regenera formats/icons/lucide.json (iconos de Lucide, licencia ISC) desde formats/icons/selection.txt.

Uso: scripts/tools/icons.py --from <carpeta icons/ de lucide-static> [--version X.Y.Z]
Cómo obtener la carpeta: `npm pack lucide-static@<versión>` y descomprimir (package/icons/).
El JSON guarda solo el interior de cada SVG (24×24, trazo `currentColor`); formats/icons.py lo dibuja.
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

DIR = ROOT / "formats" / "icons"


def inner_svg(text):
    body = re.search(r"<svg[^>]*>(.*)</svg>", text, re.S)
    if not body:
        raise ValueError("no es un SVG")
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", "", body.group(1), flags=re.S)).replace(" />", "/>").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", required=True, type=Path)
    ap.add_argument("--version", default="")
    args = ap.parse_args()
    names = [line.strip() for line in (DIR / "selection.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    missing = [n for n in names if not (args.src / f"{n}.svg").exists()]
    if missing:
        oslib.die(f"no existen en {args.src}: {missing}")
    version = args.version or (re.search(r"lucide-static v([\d.]+)", (args.src / f"{names[0]}.svg").read_text())
                               or [None, ""])[1]
    icons = {n: inner_svg((args.src / f"{n}.svg").read_text()) for n in names}
    oslib.write_json(DIR / "lucide.json", {"source": "lucide-static", "version": version, "license": "ISC",
                                           "icons": icons})
    oslib.emit({"ok": True, "icons": len(icons), "version": version, "file": str(DIR / "lucide.json")})


if __name__ == "__main__":
    main()
