#!/usr/bin/env python3
"""Portada de una plataforma: un cuadro del video (con su gancho en pantalla) → covers/<plataforma>.jpg.

Uso: scripts/pipeline/cover.py --project <canal>/<pieza> --platform tiktok [--platform reels …] [--at 1.8]

Toma el cuadro de renders/<plataforma>.mp4 (o del borrador si aún no hay final) en el segundo --at; sin --at,
a la mitad de la primera tarjeta de tipo título (el gancho) del storyboard, o en 1.0 s. La persona
puede pedir otro momento: vuelve a correrlo con --at. Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402


def default_time(sb):
    hook = next((o for o in sb.get("overlays", []) if o.get("type") == "title"), None)
    return round((hook["in"] + hook["out"]) / 2, 2) if hook else 1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--platform", action="append", required=True)
    ap.add_argument("--at", type=float, help="segundo del video (por defecto: la mitad del gancho)")
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    sb = oslib.read_json(P / "storyboard.json") if (P / "storyboard.json").exists() else {}
    t = args.at if args.at is not None else default_time(sb)
    drafts = sorted((P / "renders").glob("draft-*.mp4")) if (P / "renders").exists() else []
    out = []
    for plat in args.platform:
        src = P / "renders" / f"{plat}.mp4"
        if not src.exists():
            src = drafts[0] if drafts else None
        if not src:
            oslib.die(f"no hay render de {plat} ni borrador: corre bin/edit hasta la revisión B")
        dst = P / "covers" / f"{plat}.jpg"
        dst.parent.mkdir(exist_ok=True)
        oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                   "-q:v", "2", str(dst)])
        out.append({"platform": plat, "file": str(dst.relative_to(P)), "from": str(src.relative_to(P)), "at_s": t})
    oslib.emit({"ok": True, "covers": out,
                "next": "Muéstrala a la persona; si prefiere otro momento: --at <segundo>"})


if __name__ == "__main__":
    main()
