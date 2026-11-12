#!/usr/bin/env python3
"""Valida el storyboard de una pieza antes de componer: devuelve TODOS los problemas juntos, con la ruta
exacta de cada campo (p. ej. «overlays[2].out: …»).

Uso: scripts/pipeline/storyboard.py --project <canal>/<pieza>

Comprueba tiempos, ids, tarjetas (tipo, rol, texto), escenas (formato disponible para el canal y sus
parámetros obligatorios, layout, efectos), cámara, palabras resaltadas (existen en captions.json), plataformas
(preset), audio (pista en la biblioteca, licencia de anuncios, efectos en el kit) y voz.
Lo usa compose.py al empezar; el agente debería correrlo después de escribir storyboard.json.
Sin numpy. Salida JSON: {"ok", "problems", "warnings"}. Exit 0 válido, 1 con problemas, 2 error de uso.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

from scripts.validation.storyboard import context, validate

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    f = P / "storyboard.json"
    if not f.exists():
        oslib.die("falta storyboard.json (ver docs/storyboard.md)")
    try:
        sb = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        oslib.emit({"ok": False, "problems": [f"storyboard.json: JSON inválido ({e})"], "warnings": []}, 1)
    errs, warns = validate(sb, context(P))
    oslib.emit({"ok": not errs, "problems": errs, "warnings": warns}, 0 if not errs else 1)


if __name__ == "__main__":
    main()
