"""Animaciones Lottie: leer (JSON o .lottie), validar, medir, extraer la paleta y recolorear con la marca.

El recoloreo no toca el archivo: la biblioteca guarda un mapa {"#rrggbb": rol} (o "auto") y compose lo aplica
al servir la animación, con los colores de `brand.json` del canal. Así una misma animación se ve con la
identidad de cada canal.
"""
import colorsys
import copy
import json
import zipfile
from pathlib import Path

ROLES = ("accent", "accent2", "accent3", "warn", "text", "muted", "surface", "bg")
SATURATED_ROLES = ("accent", "accent2", "accent3", "warn")


def load(path):
    """Dict de la animación. Acepta .json y .lottie (dotLottie: zip con animations/*.json; toma la primera)."""
    p = Path(path)
    if p.suffix.lower() == ".lottie":
        with zipfile.ZipFile(p) as z:
            names = sorted(n for n in z.namelist() if n.startswith("animations/") and n.endswith(".json"))
            if not names:
                raise ValueError("el .lottie no trae animations/*.json")
            return json.loads(z.read(names[0]).decode("utf-8"))
    return json.loads(p.read_text(encoding="utf-8"))


def problems(anim):
    """Lo que impide usarla en un render sin red (lista vacía = válida)."""
    errs = []
    for k in ("v", "fr", "ip", "op", "w", "h", "layers"):
        if k not in anim:
            errs.append(f"falta «{k}»: no parece un JSON de Lottie (Bodymovin)")
    if errs:
        return errs
    if anim["op"] <= anim["ip"]:
        errs.append("duración cero (op ≤ ip)")
    for a in anim.get("assets", []):
        if "p" in a and not str(a.get("p", "")).startswith("data:") and not a.get("layers"):
            errs.append(f"imagen externa «{a.get('u', '')}{a['p']}»: exporta con imágenes incrustadas (base64)")
    if any(layer.get("ty") == 5 for layer in _all_layers(anim)) and anim.get("fonts", {}).get("list"):
        errs.append("usa capas de texto con fuentes: conviértelas a formas en After Effects")
    return errs


def info(anim):
    fr = anim["fr"]
    return {"fps": fr, "frames": anim["op"] - anim["ip"], "ip": anim["ip"],
            "duration_s": round((anim["op"] - anim["ip"]) / fr, 3), "w": anim["w"], "h": anim["h"]}


def _all_layers(anim):
    yield from anim.get("layers", [])
    for a in anim.get("assets", []):
        yield from a.get("layers", [])


def _color_slots(node):
    """Recorre el JSON y devuelve las listas [r, g, b(, a)] de rellenos, trazos y texto (fijos y animados)."""
    if isinstance(node, dict):
        if node.get("ty") in ("fl", "st") and isinstance(node.get("c"), dict):
            c = node["c"]
            if c.get("a"):
                for kf in c.get("k", []):
                    for key in ("s", "e"):
                        if isinstance(kf, dict) and isinstance(kf.get(key), list) and len(kf[key]) >= 3:
                            yield kf[key]
            elif isinstance(c.get("k"), list) and len(c["k"]) >= 3 and all(isinstance(v, (int, float)) for v in c["k"]):
                yield c["k"]
        if "fc" in node and isinstance(node["fc"], list) and len(node["fc"]) >= 3:
            yield node["fc"]
        for v in node.values():
            yield from _color_slots(v)
    elif isinstance(node, list):
        for v in node:
            yield from _color_slots(v)


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb[:3])


def palette(anim):
    """[(hex, usos)] de mayor a menor uso."""
    count = {}
    for slot in _color_slots(anim):
        h = _hex(slot)
        count[h] = count.get(h, 0) + 1
    return sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))


def auto_map(anim):
    """Mapa automático color → rol: los grises por luminosidad (text, muted, surface) y los colores con
    saturación, del más usado al menos usado, a accent, accent2, accent3 y warn."""
    out, k = {}, 0
    for h, _ in palette(anim):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        hue, light, sat = colorsys.rgb_to_hls(r, g, b)
        if sat < 0.18 or light > 0.92 or light < 0.08:
            out[h] = "text" if light > 0.7 else "muted" if light > 0.3 else "surface"
        else:
            out[h] = SATURATED_ROLES[k % len(SATURATED_ROLES)]
            k += 1
    return out


def _rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def recolor(anim, mapping, brand_colors):
    """Copia de la animación con cada color del mapa cambiado por el color de su rol en la marca."""
    if not mapping:
        return anim
    if mapping == "auto":
        mapping = auto_map(anim)
    out = copy.deepcopy(anim)
    targets = {src.lower(): _rgb(brand_colors[role]) for src, role in mapping.items() if role in brand_colors}
    for slot in _color_slots(out):
        new = targets.get(_hex(slot))
        if new:
            slot[:3] = [round(v, 4) for v in new]
    return out


def map_problems(mapping):
    if mapping in (None, "auto"):
        return []
    if not isinstance(mapping, dict):
        return ["recolor: «auto» o un mapa {\"#rrggbb\": rol}"]
    return [f"recolor: «{r}» no es un rol ({', '.join(ROLES)})" for r in mapping.values() if r not in ROLES]
