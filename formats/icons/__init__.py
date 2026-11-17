"""Iconos para los formatos: `icon("dna", size=96)` → <svg> del color actual.

- Sin prefijo, Lucide (ISC, trazo de 24×24; lucide.json desde selection.txt).
- `health:<id>`: Health Icons (CC0, relleno; toman el color de la marca como Lucide).
- `bio:<id>`: Bioicons de la carpeta CC0 (ilustraciones científicas con sus propios colores).
Los genera scripts/tools/icons.py (--from para Lucide, --sets para los otros). `names()` lista Lucide (los que
puede transformar `morph-icon`); `all_names()` todos; `credit()` dice licencia y autor de cada uno.
"""
import functools
import json
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_FILE = _DIR / "lucide.json"
SETS = ("health", "bio")


@functools.lru_cache(maxsize=1)
def _data():
    return json.loads(_FILE.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _set(name):
    f = _DIR / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"icons": {}}


def _split(name):
    """«health:dna» → ("health", "dna"); «dna» → (None, "dna")."""
    if isinstance(name, str) and ":" in name:
        pre, ident = name.split(":", 1)
        return (pre, ident) if pre in SETS else ("?", ident)
    return None, name


def names():
    """Iconos de Lucide (los que acepta morph-icon)."""
    return sorted(_data()["icons"])


def all_names():
    return names() + [f"{s}:{i}" for s in SETS for i in sorted(_set(s)["icons"])]


def exists(name):
    pre, ident = _split(name)
    if pre is None:
        return ident in _data()["icons"]
    return pre in SETS and ident in _set(pre)["icons"]


def morphable(name):
    """Solo Lucide se puede transformar en otro icono (trazos de un solo color)."""
    return _split(name)[0] is None and exists(name)


def credit(name):
    """{set, license, author, source} del icono (para assets.md)."""
    pre, ident = _split(name)
    if pre is None:
        return {"set": "Lucide", "license": "ISC", "author": "Lucide Contributors", "source": "https://lucide.dev"}
    it = _set(pre)["icons"][ident]
    return {"set": {"health": "Health Icons", "bio": "Bioicons"}[pre], "license": it["license"],
            "author": it["author"], "source": it["source"]}


def icon(name, size=96, cls="", stroke=2, attrs=""):
    """SVG del icono a `size` px; el color sale de CSS (`color:` del elemento o de su padre). Los de Bioicons
    conservan sus colores."""
    if not exists(name):
        raise KeyError(f"icono desconocido: «{name}» (disponibles: formats/icons/selection*.txt)")
    c = f' class="{cls}"' if cls else ""
    pre, ident = _split(name)
    if pre:
        it = _set(pre)["icons"][ident]
        fill = ' fill="currentColor"' if _set(pre).get("mono") else ""
        return (f'<svg{c} width="{size}" height="{size}" viewBox="{it["viewBox"]}"{fill} '
                f'preserveAspectRatio="xMidYMid meet"{attrs}>{it["svg"]}</svg>')
    return (f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round"{attrs}>'
            f'{_data()["icons"][name]}</svg>')


def used(obj):
    """Iconos de los conjuntos con prefijo nombrados en cualquier parte de un storyboard (para créditos)."""
    out = set()
    if isinstance(obj, dict):
        if obj.get('kind')=='icon' and exists(obj.get('icon')): out.add(obj['icon'])
        for v in obj.values():
            out |= used(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= used(v)
    elif isinstance(obj, str) and _split(obj)[0] in SETS and exists(obj):
        out.add(obj)
    return out


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
    if not morphable(name):
        raise KeyError(f"icono «{name}»: solo los de Lucide (sin prefijo) se pueden transformar")
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
