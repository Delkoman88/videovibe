"""Formatos de escenas animadas: paquete `core` (genérico) + paquetes temáticos en formats/packs/.

Un canal activa paquetes en channel.json → "format_packs": ["biotech", …]. compose.py llama a
`configure()` con las fuentes y etiquetas del canal y luego a `render()` por escena.
Catálogo legible: docs/formats.md (lo genera bin/format-catalog).
"""
import importlib
import pkgutil
from pathlib import Path

from formats import core
from formats.core import BUBBLE, CTX, REGISTRY  # noqa: F401  (reexportados)

PACKS_DIR = Path(__file__).resolve().parent / "packs"


def available_packs():
    return sorted(m.name for m in pkgutil.iter_modules([str(PACKS_DIR)]))


def load_packs(packs=()):
    for p in packs:
        if p not in available_packs():
            raise KeyError(f"paquete de formatos desconocido: {p} (disponibles: {available_packs()})")
        importlib.import_module(f"formats.packs.{p}")


def registry(packs=()):
    """Formatos disponibles para un canal: core + sus paquetes."""
    load_packs(packs)
    allowed = {"core", *packs}
    return {k: v for k, v in REGISTRY.items() if v["pack"] in allowed}


def configure(font_faces="", labels=None, channel=None):
    CTX["font_faces"] = font_faces
    if labels:
        CTX["labels"] = labels
    if channel:  # nombre corto del canal, para rótulos por defecto de los paquetes (p. ej. «<CANAL>–3000»)
        CTX["channel"] = channel.upper()


def default_layout(fmt, packs=()):
    return registry(packs)[fmt]["layout"]


def render(scene, packs=()):
    """scene: {id, format, in, out, layout?, params} → HTML de la sub-composición."""
    reg = registry(packs)
    meta = reg.get(scene["format"])
    if not meta:
        raise KeyError(f"formato «{scene['format']}» no disponible para este canal "
                       f"(disponibles: {sorted(reg)}; paquetes: {list(packs)})")
    params = scene.get("params", {})
    missing = [k for k in meta["required"] if k not in params]
    if missing:
        raise ValueError(f"escena {scene['id']} ({scene['format']}): faltan parámetros {missing}")
    d = round(scene["out"] - scene["in"], 3)
    return meta["fn"](scene["id"], d, params, layout=scene.get("layout") or meta["layout"])


def needs(sb):
    """Librerías opcionales que piden las escenas de un storyboard (p. ej. {"pixi"}).
    Los paquetes del canal ya están cargados cuando compose.py llama a esto."""
    out = set()
    for scene in sb.get("scenes", []):
        out.update(REGISTRY.get(scene.get("format"), {}).get("needs", ()))
    return out


def uses(sb):
    """Recursos de biblioteca que piden las escenas: [(escena, tipo, id)] en orden, sin repetir (tipo, id)."""
    out, seen = [], set()
    for scene in sb.get("scenes", []):
        fn = REGISTRY.get(scene.get("format"), {}).get("uses")
        for kind, ident in (fn(scene.get("params", {})) if fn else []):
            if (kind, ident) not in seen:
                seen.add((kind, ident))
                out.append((scene.get("id"), kind, ident))
    return out
