"""Bibliotecas de recursos visuales por tipo (`lottie`, `structures`, `models`): qué hay, de dónde viene y con
qué licencia. Igual que la música: un `library.json` con los datos y los archivos al lado.

Se buscan en dos lugares; el canal tiene prioridad sobre el motor si repite un id:
  motor:  assets/<tipo>/library.json             (recursos propios de VideoVibe, Apache-2.0)
  canal:  <canal>/assets/<tipo>/library.json     (los del canal; archivos de terceros fuera de git)

Cada elemento: {"id", "file", "origin", "license", "ads": bool, ...datos del tipo}. Sin `license` no se usa.
"""
from pathlib import Path

from scripts.core import oslib

KINDS = ("lottie", "structures", "models")


def _dirs(kind, channel_dir=None):
    out = [oslib.ROOT / "assets" / kind]
    if channel_dir:
        out.append(Path(channel_dir) / "assets" / kind)
    return out


def library(kind, channel_dir=None):
    """{id: elemento} con `path` (archivo absoluto) y `scope` («motor» o «canal»)."""
    if kind not in KINDS:
        raise KeyError(f"tipo de recurso desconocido: {kind} ({', '.join(KINDS)})")
    items = {}
    for scope, d in zip(("motor", "canal"), _dirs(kind, channel_dir)):
        lib = d / "library.json"
        if not lib.exists():
            continue
        for it in oslib.read_json(lib).get("items", []):
            items[it["id"]] = {**it, "path": str(d / it["file"]), "scope": scope}
    return items


def item(kind, ident, channel_dir=None):
    return library(kind, channel_dir).get(ident)


def problems(kind, ident, channel_dir=None, ads=False):
    """Por qué no se puede usar un recurso (lista vacía = se puede)."""
    it = item(kind, ident, channel_dir)
    if not it:
        avail = ", ".join(sorted(library(kind, channel_dir))) or "ninguno"
        return [f"«{ident}» no está en la biblioteca de {kind} (disponibles: {avail}; "
                f"agrégalo con scripts/tools/{kind}.py add)"]
    errs = []
    if not Path(it["path"]).exists():
        errs.append(f"«{ident}»: falta el archivo {it['path']}")
    if not str(it.get("license", "")).strip():
        errs.append(f"«{ident}»: sin licencia registrada")
    if ads and not it.get("ads"):
        errs.append(f"«{ident}»: su licencia no permite anuncios (plataforma ads)")
    return errs


def save(kind, channel_dir, entry):
    """Agrega o reemplaza un elemento en la biblioteca del canal."""
    d = _dirs(kind, channel_dir)[-1]
    d.mkdir(parents=True, exist_ok=True)
    lib = d / "library.json"
    data = oslib.read_json(lib) if lib.exists() else {"items": []}
    data["items"] = [it for it in data["items"] if it["id"] != entry["id"]] + [entry]
    data["items"].sort(key=lambda it: it["id"])
    oslib.write_json(lib, data)
    return lib
