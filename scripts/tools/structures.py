#!/usr/bin/env python3
"""Biblioteca de estructuras moleculares de un canal: descargar (PDB, PubChem), agregar archivos, listar y ver.

Uso:
  scripts/tools/structures.py fetch --channel <id> --pdb 1HHO [--id hemoglobina]
  scripts/tools/structures.py fetch --channel <id> --pubchem aspirin|2244 [--id aspirina]
  scripts/tools/structures.py add <archivo.pdb|.cif|.sdf|.mol2> --channel <id> --id <nombre> --origin "…" --license "…" [--ads]
  scripts/tools/structures.py list --channel <id>
  scripts/tools/structures.py preview <id> --channel <id> [--style auto|cartoon|stick|sphere|surface|ballstick]

- fetch descarga una sola vez y guarda la copia en <canal>/assets/structures/ con su fuente y licencia
  (PDB: CC0 1.0; PubChem: dominio público). El render nunca usa red.
- add registra un archivo propio (p. ej. un modelo de AlphaFold o de tu laboratorio): origen y licencia
  obligatorios; si no es público, no lo marques `--ads` sin permiso.
- list muestra cadenas, rangos de residuos y ligandos: lo que acepta `focus` en molecule-focus.
- preview: hoja de contacto con la marca del canal (molecule-spin).
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import assetlib, oslib, structlib  # noqa: E402

EXT = {"pdb": "pdb", "cif": "cif", "sdf": "sdf", "mol2": "mol2"}


def _channel(cid):
    cdir = oslib.channel_path(cid)
    if not (cdir / "channel.json").exists():
        oslib.die(f"no existe el canal «{cid}»")
    return cdir


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def _register(cdir, ident, text, fmt, source, origin, license_, ads, description=""):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", ident):
        oslib.die("--id: minúsculas, números y guiones (p. ej. «hemoglobina»)")
    d = cdir / "assets" / "structures"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{ident}.{EXT[fmt]}"
    f.write_text(text, encoding="utf-8")
    s = structlib.summary(text, fmt)
    if not s["atoms"]:
        oslib.die("el archivo no tiene átomos legibles")
    entry = {"id": ident, "file": f.name, "format": fmt, "description": description, "source": source,
             "origin": origin, "license": license_, "ads": ads, **s}
    lib = assetlib.save("structures", cdir, entry)
    return entry, lib


def cmd_fetch(a):
    cdir = _channel(a.channel)
    try:
        if a.pdb:
            text, fmt, source = structlib.fetch_pdb(a.pdb)
            lic, ident = structlib.LICENSES["pdb"], a.id or _slug(a.pdb)
        else:
            q = a.pubchem
            text, fmt, source = structlib.fetch_pubchem(cid=q) if q.isdigit() else structlib.fetch_pubchem(name=q)
            lic, ident = structlib.LICENSES["pubchem"], a.id or _slug(q)
    except Exception as e:  # noqa: BLE001
        oslib.die(f"no se pudo descargar: {e}")
    entry, lib = _register(cdir, ident, text, fmt, source, source, lic, True, a.description)
    oslib.emit({"ok": True, "id": ident, "library": str(lib), "source": source, "license": lic,
                "title": entry["title"], "chains": entry["chains"], "residues": entry["residues"],
                "ligands": entry["ligands"], "atoms": entry["atoms"],
                "next": f"scripts/tools/structures.py preview {ident} --channel {a.channel}"})


def cmd_add(a):
    cdir = _channel(a.channel)
    src = Path(a.file).expanduser()
    if not src.exists():
        src = oslib.MATERIAL / a.file
    if not src.exists():
        oslib.die(f"no encuentro {a.file} (ni como ruta ni en {oslib.MATERIAL})")
    try:
        fmt = structlib.fmt_of(src)
    except ValueError as e:
        oslib.die(str(e))
    entry, lib = _register(cdir, a.id, src.read_text(encoding="utf-8", errors="replace"), fmt, a.origin, a.origin,
                           a.license, a.ads, a.description)
    oslib.emit({"ok": True, "id": a.id, "library": str(lib), "chains": entry["chains"], "ligands": entry["ligands"]})


def cmd_list(a):
    cdir = _channel(a.channel)
    items = [{k: it.get(k) for k in ("id", "scope", "title", "source", "format", "atoms", "chains", "residues",
                                     "ligands", "license", "ads")}
             for _, it in sorted(assetlib.library("structures", cdir).items())]
    oslib.emit({"ok": True, "channel": a.channel, "items": items})


def cmd_preview(a):
    from scripts.tools import gallery
    _channel(a.channel)
    it = assetlib.item("structures", a.id, oslib.channel_path(a.channel))
    if not it:
        oslib.die(f"«{a.id}» no está en la biblioteca del canal ni del motor")
    seconds = 4.0
    hf, _ = gallery.build(a.channel, ["molecule-spin"], seconds,
                          out=ROOT / "work" / "structure-preview" / a.channel / a.id / "hf",
                          params={"molecule-spin": {"structure": a.id, "style": a.style, "degrees": 300,
                                                    "kicker": a.id, "caption": it.get("source", "")}})
    times = [round(0.4 + (seconds - 0.8) * k / 3, 3) for k in range(4)]
    shots = gallery.snapshot(hf, times, hf.parent / "snapshots")
    oslib.emit({"ok": True, "id": a.id,
                "contact_sheets": [str(p) for p in sorted((hf.parent / "snapshots").glob("contact-sheet*.jpg"))],
                "frames": [str(p) for p in shots.values()]})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch")
    p.add_argument("--channel", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pdb", help="código PDB (p. ej. 1HHO)")
    g.add_argument("--pubchem", help="CID o nombre en inglés (p. ej. 2244 o aspirin)")
    p.add_argument("--id")
    p.add_argument("--description", default="")
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
    p.add_argument("--style", default="auto")
    a = ap.parse_args()
    {"fetch": cmd_fetch, "add": cmd_add, "list": cmd_list, "preview": cmd_preview}[a.cmd](a)


if __name__ == "__main__":
    main()
