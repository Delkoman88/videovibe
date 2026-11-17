#!/usr/bin/env python3
"""Biblioteca de animaciones Lottie de un canal: agregar, listar, recolorear y ver con la marca.

Uso:
  scripts/tools/lottie.py add <archivo.json|.lottie> --channel <id> --id <nombre> --origin "…" --license "…"
                              [--ads] [--loop] [--recolor auto|none] [--description "…"]
  scripts/tools/lottie.py list --channel <id>
  scripts/tools/lottie.py recolor <id> --channel <id> (--auto | --none | --map "#ff3366=accent,#ffffff=text")
  scripts/tools/lottie.py preview <id> --channel <id> [--frames 6]

- add: valida que funcione sin red (sin imágenes externas ni fuentes), mide fps/cuadros/tamaño, copia el
  archivo a <canal>/assets/lottie/ y lo registra con su origen y licencia (obligatorios: regla 5 de AGENTS.md).
  `--ads` solo si la licencia permite publicidad pagada. Por defecto se recolorea con la marca (`auto`).
- recolor: el mapa {color original → rol de la marca} se guarda en la biblioteca y se aplica al componer;
  el archivo no cambia. `list` muestra la paleta original de cada animación.
- preview: hoja de contacto de la animación en una escena `lottie-scene` con la marca del canal.
De dónde sacar animaciones: LottieFiles (revisa la licencia de cada una), After Effects + Bodymovin, Rive o
LottieLab (exportar a Lottie JSON). Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import assetlib, lottielib, oslib  # noqa: E402


def _channel(cid):
    cdir = oslib.channel_path(cid)
    if not (cdir / "channel.json").exists():
        oslib.die(f"no existe el canal «{cid}»")
    return cdir


def cmd_add(a):
    cdir = _channel(a.channel)
    src = Path(a.file).expanduser()
    if not src.exists():
        src = oslib.MATERIAL / a.file
    if not src.exists():
        oslib.die(f"no encuentro {a.file} (ni como ruta ni en {oslib.MATERIAL})")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.id):
        oslib.die("--id: minúsculas, números y guiones (p. ej. «cohete-despega»)")
    try:
        anim = lottielib.load(src)
    except (ValueError, OSError, KeyError) as e:
        oslib.die(f"no se pudo leer la animación: {e}")
    if errs := lottielib.problems(anim):
        oslib.die("la animación no se puede usar: " + "; ".join(errs))
    dest_dir = cdir / "assets" / "lottie"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{a.id}.json"
    if src.suffix.lower() == ".lottie":
        oslib.write_json(dest, anim)
    else:
        shutil.copy(src, dest)
    entry = {"id": a.id, "file": dest.name, "description": a.description or "", "origin": a.origin,
             "license": a.license, "ads": a.ads, "loop": a.loop,
             "recolor": "auto" if a.recolor == "auto" else None, **lottielib.info(anim)}
    lib = assetlib.save("lottie", cdir, entry)
    oslib.emit({"ok": True, "id": a.id, "library": str(lib), "file": str(dest), "info": lottielib.info(anim),
                "palette": lottielib.palette(anim)[:8], "recolor": entry["recolor"],
                "next": f"scripts/tools/lottie.py preview {a.id} --channel {a.channel}"})


def cmd_list(a):
    cdir = _channel(a.channel)
    items = []
    for ident, it in sorted(assetlib.library("lottie", cdir).items()):
        row = {k: it.get(k) for k in ("id", "scope", "description", "duration_s", "loop", "license", "ads", "recolor")}
        try:
            row["palette"] = [h for h, _ in lottielib.palette(lottielib.load(it["path"]))[:6]]
        except (OSError, ValueError):
            row["palette"] = "archivo no disponible"
        items.append(row)
    oslib.emit({"ok": True, "channel": a.channel, "items": items})


def cmd_recolor(a):
    cdir = _channel(a.channel)
    lib = assetlib.library("lottie", cdir)
    it = lib.get(a.id)
    if not it:
        oslib.die(f"«{a.id}» no está en la biblioteca ({', '.join(sorted(lib))})")
    if it["scope"] != "canal":
        oslib.die(f"«{a.id}» es del motor: cópiala al canal con `add` para cambiar su mapa")
    if a.map:
        mapping = {}
        for pair in a.map.split(","):
            src, _, role = pair.partition("=")
            mapping[src.strip().lower()] = role.strip()
    else:
        mapping = "auto" if a.auto else None
    if errs := lottielib.map_problems(mapping):
        oslib.die("; ".join(errs))
    entry = {k: v for k, v in it.items() if k not in ("path", "scope")}
    entry["recolor"] = mapping
    assetlib.save("lottie", cdir, entry)
    shown = lottielib.auto_map(lottielib.load(it["path"])) if mapping == "auto" else mapping
    oslib.emit({"ok": True, "id": a.id, "recolor": mapping, "effective_map": shown})


def cmd_preview(a):
    from scripts.tools import gallery
    _channel(a.channel)
    if a.id not in assetlib.library("lottie", oslib.channel_path(a.channel)):
        oslib.die(f"«{a.id}» no está en la biblioteca del canal ni del motor")
    seconds = 4.0
    hf, sb = gallery.build(a.channel, ["lottie-scene"], seconds,
                           out=ROOT / "work" / "lottie-preview" / a.channel / a.id / "hf",
                           params={"lottie-scene": {"anim": a.id, "loops": "fill", "kicker": a.id}})
    times = [round(0.2 + (seconds - 0.5) * k / max(a.frames - 1, 1), 3) for k in range(a.frames)]
    shots = gallery.snapshot(hf, times, hf.parent / "snapshots")
    oslib.emit({"ok": True, "id": a.id, "contact_sheets": [str(p) for p in sorted((hf.parent / "snapshots").glob("contact-sheet*.jpg"))],
                "frames": [str(p) for p in shots.values()]})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("file")
    p.add_argument("--channel", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--origin", required=True, help="de dónde viene (URL de LottieFiles, autor, «propia»)")
    p.add_argument("--license", required=True, help="licencia (p. ej. «Lottie Simple License», «propia»)")
    p.add_argument("--ads", action="store_true", help="la licencia permite publicidad pagada")
    p.add_argument("--loop", action="store_true", help="la animación está hecha para repetirse")
    p.add_argument("--recolor", choices=("auto", "none"), default="auto")
    p.add_argument("--description", default="")
    p = sub.add_parser("list")
    p.add_argument("--channel", required=True)
    p = sub.add_parser("recolor")
    p.add_argument("id")
    p.add_argument("--channel", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--auto", action="store_true")
    g.add_argument("--none", action="store_true")
    g.add_argument("--map")
    p = sub.add_parser("preview")
    p.add_argument("id")
    p.add_argument("--channel", required=True)
    p.add_argument("--frames", type=int, default=6)
    a = ap.parse_args()
    {"add": cmd_add, "list": cmd_list, "recolor": cmd_recolor, "preview": cmd_preview}[a.cmd](a)


if __name__ == "__main__":
    main()
