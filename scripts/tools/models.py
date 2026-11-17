#!/usr/bin/env python3
"""Biblioteca de modelos 3D (.glb) de un canal: agregar, listar, ver y generar los de ejemplo del motor.

Uso:
  scripts/tools/models.py add <archivo.glb> --channel <id> --id <nombre> --origin "…" --license "…" [--ads]
  scripts/tools/models.py list --channel <id>
  scripts/tools/models.py preview <id> --channel <id>
  scripts/tools/models.py builtins            (rehace los modelos de ejemplo del motor en assets/models/)

- Solo glTF binario (.glb) con todo incrustado (texturas dentro): el render no usa red ni rutas sueltas.
  Desde Blender: Archivo → Exportar → glTF 2.0, formato «glTF Binary (.glb)».
- Origen y licencia obligatorios. Fuentes recomendadas: Poly Haven (CC0), Smithsonian 3D (CC0 en los marcados),
  NIH 3D (revisa la licencia de cada modelo), modelos propios. Sin permiso de uso comercial, no lo marques --ads.
- Materiales llamados `brand-accent`, `brand-accent2` o `brand-accent3` toman el color de la marca del canal
  en model-showcase (así un mismo modelo sirve a varios canales).
- preview: hoja de contacto con la marca del canal (model-showcase).
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import assetlib, glb, oslib  # noqa: E402

ENGINE = ROOT / "assets" / "models"


def _channel(cid):
    cdir = oslib.channel_path(cid)
    if not (cdir / "channel.json").exists():
        oslib.die(f"no existe el canal «{cid}»")
    return cdir


def cmd_add(a):
    cdir = _channel(a.channel)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.id):
        oslib.die("--id: minúsculas, números y guiones (p. ej. «microscopio»)")
    src = Path(a.file).expanduser()
    if not src.exists():
        src = oslib.MATERIAL / a.file
    if not src.exists():
        oslib.die(f"no encuentro {a.file} (ni como ruta ni en {oslib.MATERIAL})")
    data = src.read_bytes()
    try:
        s = glb.summary(data)
    except ValueError as e:
        oslib.die(str(e))
    if s["mb"] > glb.MAX_MB:
        oslib.die(f"el modelo pesa {s['mb']} MB (máximo {glb.MAX_MB}); simplifícalo o reduce texturas")
    d = cdir / "assets" / "models"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d / f"{a.id}.glb")
    entry = {"id": a.id, "file": f"{a.id}.glb", "description": a.description, "origin": a.origin,
             "license": a.license, "ads": a.ads, **s}
    lib = assetlib.save("models", cdir, entry)
    oslib.emit({"ok": True, "id": a.id, "library": str(lib), **s,
                "next": f"scripts/tools/models.py preview {a.id} --channel {a.channel}"})


def cmd_list(a):
    cdir = _channel(a.channel)
    items = [{k: it.get(k) for k in ("id", "scope", "description", "triangles", "textures", "mb", "origin",
                                     "license", "ads")}
             for _, it in sorted(assetlib.library("models", cdir).items())]
    oslib.emit({"ok": True, "channel": a.channel, "items": items})


def cmd_preview(a):
    from scripts.tools import gallery
    _channel(a.channel)
    if not assetlib.item("models", a.id, oslib.channel_path(a.channel)):
        oslib.die(f"«{a.id}» no está en la biblioteca del canal ni del motor")
    seconds = 4.0
    hf, _ = gallery.build(a.channel, ["model-showcase"], seconds,
                          out=ROOT / "work" / "model-preview" / a.channel / a.id / "hf",
                          params={"model-showcase": {"model": a.id, "kicker": a.id, "degrees": 300}})
    times = [round(0.4 + (seconds - 0.8) * k / 3, 3) for k in range(4)]
    shots = gallery.snapshot(hf, times, hf.parent / "snapshots")
    oslib.emit({"ok": True, "id": a.id,
                "contact_sheets": [str(p) for p in sorted((hf.parent / "snapshots").glob("contact-sheet*.jpg"))],
                "frames": [str(p) for p in shots.values()]})


def flask():
    """Matraz Erlenmeyer: vidrio (doble cara, translúcido) + líquido del color de acento de la marca."""
    glass, gi = glb.lathe([(0.0, 0.0), (0.92, 0.0), (1.0, 0.04), (1.0, 0.14), (0.32, 1.55), (0.29, 2.22),
                           (0.36, 2.28), (0.37, 2.36), (0.30, 2.38)], segments=96)
    liquid, li = glb.lathe([(0.0, 0.035), (0.9, 0.035), (0.955, 0.1), (0.66, 0.6), (0.0, 0.6)], segments=96)
    return glb.write([
        {"name": "liquid", "positions": liquid, "indices": li,
         "material": {"name": "brand-accent", "color": (0.2, 0.8, 0.75, 1), "metallic": 0.0, "roughness": 0.25,
                      "emissive": (0.05, 0.2, 0.18), "double": True}},
        {"name": "glass", "positions": glass, "indices": gi,
         "material": {"name": "glass", "color": (0.8, 0.92, 1.0, 0.16), "metallic": 0.0, "roughness": 0.08,
                      "blend": True, "double": True}},
    ], generator="VideoVibe scripts/tools/models.py")


BUILTINS = {"flask": (flask, "Matraz Erlenmeyer con líquido del color de la marca (modelo de ejemplo del motor)")}


def cmd_builtins(_a):
    ENGINE.mkdir(parents=True, exist_ok=True)
    items = []
    for ident, (fn, desc) in BUILTINS.items():
        data = fn()
        (ENGINE / f"{ident}.glb").write_bytes(data)
        items.append({"id": ident, "file": f"{ident}.glb", "description": desc, "origin": "VideoVibe (generado)",
                      "license": "Apache-2.0 (VideoVibe)", "ads": True, **glb.summary(data)})
    oslib.write_json(ENGINE / "library.json", {
        "_note": "Modelos de ejemplo del motor (generados por scripts/tools/models.py builtins). Los de cada canal "
                 "van en <canal>/assets/models/ (scripts/tools/models.py add).", "items": items})
    oslib.emit({"ok": True, "items": [i["id"] for i in items], "library": str(ENGINE / "library.json")})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("file")
    p.add_argument("--channel", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--origin", required=True)
    p.add_argument("--license", required=True)
    p.add_argument("--ads", action="store_true")
    p.add_argument("--description", default="")
    p = sub.add_parser("list")
    p.add_argument("--channel", required=True)
    p = sub.add_parser("preview")
    p.add_argument("id")
    p.add_argument("--channel", required=True)
    sub.add_parser("builtins")
    a = ap.parse_args()
    {"add": cmd_add, "list": cmd_list, "preview": cmd_preview, "builtins": cmd_builtins}[a.cmd](a)


if __name__ == "__main__":
    main()
