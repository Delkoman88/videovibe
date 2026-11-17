"""Iconos de Lucide (ISC) para los formatos: `icon("dna", size=96)` → <svg> con trazo del color actual.

El conjunto está en lucide.json (lo genera scripts/tools/icons.py desde selection.txt); el storyboard
nombra iconos por su id de Lucide. `names()` lista los disponibles para validar y para el catálogo.
"""
import functools
import json
from pathlib import Path

_FILE = Path(__file__).resolve().parent / "lucide.json"


@functools.lru_cache(maxsize=1)
def _data():
    return json.loads(_FILE.read_text(encoding="utf-8"))


def names():
    return sorted(_data()["icons"])


def exists(name):
    return name in _data()["icons"]


def icon(name, size=96, cls="", stroke=2, attrs=""):
    """SVG del icono a `size` px; el color sale de CSS (`color:` del elemento o de su padre)."""
    if not exists(name):
        raise KeyError(f"icono desconocido: «{name}» (disponibles: formats/icons/selection.txt)")
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round"{attrs}>'
            f'{_data()["icons"][name]}</svg>')


_ATTR = None


def _attrs(tag):
    import re
    global _ATTR
    _ATTR = _ATTR or re.compile(r'([\w-]+)="([^"]*)"')
    return {k: v for k, v in _ATTR.findall(tag)}


def _f(a, k, default=0.0):
    return float(a.get(k, default))


def path_d(name):
    """Todo el icono como UN trazo SVG (`d`): lo que necesita MorphSVG para transformar un icono en otro.
    Convierte path, circle, ellipse, rect (con esquinas redondeadas), line, polyline y polygon."""
    import re
    if not exists(name):
        raise KeyError(f"icono desconocido: «{name}»")
    parts = []
    for tag, rest in re.findall(r"<(\w+)([^>]*)/?>", _data()["icons"][name]):
        a = _attrs(rest)
        if tag == "path":
            parts.append(a["d"])
        elif tag in ("circle", "ellipse"):
            cx, cy = _f(a, "cx"), _f(a, "cy")
            rx = _f(a, "r") if tag == "circle" else _f(a, "rx")
            ry = _f(a, "r") if tag == "circle" else _f(a, "ry")
            parts.append(f"M{cx - rx:g} {cy:g}a{rx:g} {ry:g} 0 1 0 {2 * rx:g} 0a{rx:g} {ry:g} 0 1 0 {-2 * rx:g} 0")
        elif tag == "rect":
            x, y, w, h = _f(a, "x"), _f(a, "y"), _f(a, "width"), _f(a, "height")
            rx = min(_f(a, "rx", a.get("ry", 0)), w / 2)
            ry = min(_f(a, "ry", a.get("rx", 0)), h / 2)
            if rx or ry:
                parts.append(f"M{x + rx:g} {y:g}h{w - 2 * rx:g}a{rx:g} {ry:g} 0 0 1 {rx:g} {ry:g}v{h - 2 * ry:g}"
                             f"a{rx:g} {ry:g} 0 0 1 {-rx:g} {ry:g}h{-(w - 2 * rx):g}a{rx:g} {ry:g} 0 0 1 {-rx:g} {-ry:g}"
                             f"v{-(h - 2 * ry):g}a{rx:g} {ry:g} 0 0 1 {rx:g} {-ry:g}z")
            else:
                parts.append(f"M{x:g} {y:g}h{w:g}v{h:g}h{-w:g}z")
        elif tag == "line":
            parts.append(f"M{_f(a, 'x1'):g} {_f(a, 'y1'):g}L{_f(a, 'x2'):g} {_f(a, 'y2'):g}")
        elif tag in ("polyline", "polygon"):
            pts = a["points"].replace(",", " ").split()
            d = "M" + " L".join(f"{pts[i]} {pts[i + 1]}" for i in range(0, len(pts) - 1, 2))
            parts.append(d + ("z" if tag == "polygon" else ""))
    return " ".join(parts)
