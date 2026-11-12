#!/usr/bin/env python3
"""Cuadros de insertos a tamaño de teléfono para la revisión B.

Uso: scripts/pipeline/phone_preview.py --project <canal>/<pieza> --draft renders/draft-tiktok.mp4
Lee storyboard.json y el borrador; escribe snaps/phone-<id>.png (360×640).
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--draft", required=True, help="ruta del borrador relativa a la pieza")
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    draft = (P / args.draft).resolve()
    if not draft.is_relative_to(P.resolve()) or not draft.is_file():
        oslib.die("--draft debe ser un archivo existente dentro de la pieza")
    sb = oslib.read_json(P / "storyboard.json")
    out = []
    for clip in sb.get("broll", []):
        t = (clip["in"] + clip["out"]) / 2
        dst = P / "snaps" / f"phone-{clip['id']}.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(draft),
                   "-frames:v", "1", "-vf", "scale=360:640", str(dst)])
        out.append({"id": clip["id"], "at_s": round(t, 3), "file": str(dst.relative_to(P))})
    oslib.emit({"ok": True, "frames": out})


if __name__ == "__main__":
    main()
