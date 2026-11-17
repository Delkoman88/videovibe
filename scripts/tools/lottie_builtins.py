#!/usr/bin/env python3
"""Genera las animaciones Lottie propias del motor en assets/lottie/ (Apache-2.0, aptas para anuncios).

Uso: scripts/tools/lottie_builtins.py
Son de partida para cualquier canal; usan tres colores «marcadores» que la biblioteca mapea a accent,
accent2 y accent3, de modo que cada canal las ve con su marca. Salida JSON. Exit 0 ok.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import lottielib, oslib  # noqa: E402

C1, C2, C3 = "#00e5ff", "#7cff4f", "#b14dff"
OUT = ROOT / "assets" / "lottie"
EASE_OUT = {"i": {"x": [0.2], "y": [1]}, "o": {"x": [0.33], "y": [0]}}
EASE_IO = {"i": {"x": [0.55], "y": [1]}, "o": {"x": [0.45], "y": [0]}}


def rgba(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1]


def val(v):
    return {"a": 0, "k": v}


def anim(*kfs, ease=EASE_OUT):
    """kfs: (cuadro, valor). Valores escalares o listas."""
    out = []
    for i, (t, v) in enumerate(kfs):
        k = {"t": t, "s": v if isinstance(v, list) else [v]}
        if i < len(kfs) - 1:
            k.update(ease)
        out.append(k)
    return {"a": 1, "k": out}


def tr_shape():
    return {"ty": "tr", "p": val([0, 0]), "a": val([0, 0]), "s": val([100, 100]), "r": val(0), "o": val(100),
            "sk": val(0), "sa": val(0)}


def group(*items):
    return {"ty": "gr", "nm": "g", "it": [*items, tr_shape()]}


def ellipse(d, p=(0, 0)):
    return {"ty": "el", "p": val(list(p)), "s": val([d, d]), "d": 1}


def rect(w, h, p=(0, 0), r=0):
    return {"ty": "rc", "p": val(list(p)), "s": val([w, h]), "r": val(r), "d": 1}


def path(points, closed=False):
    z = [[0, 0]] * len(points)
    return {"ty": "sh", "ks": val({"i": z, "o": z, "v": [list(p) for p in points], "c": closed}), "d": 1}


def stroke(color, w):
    return {"ty": "st", "c": val(rgba(color)), "o": val(100), "w": val(w), "lc": 2, "lj": 2, "ml": 4}


def fill(color):
    return {"ty": "fl", "c": val(rgba(color)), "o": val(100), "r": 1}


def trim(s=None, e=None):
    return {"ty": "tm", "s": s or val(0), "e": e or val(100), "o": val(0), "m": 1}


def layer(ind, nm, shapes, op, p=(300, 300), s=None, o=None, r=None, a=(0, 0)):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": nm, "sr": 1, "ao": 0, "ip": 0, "op": op, "st": 0, "bm": 0,
            "ks": {"o": o or val(100), "r": r or val(0), "p": val([*p, 0]), "a": val([*a, 0]),
                   "s": s or val([100, 100, 100])},
            "shapes": shapes}


def comp(name, op, layers, size=600, fr=30):
    return {"v": "5.7.4", "fr": fr, "ip": 0, "op": op, "w": size, "h": size, "nm": name, "ddd": 0, "assets": [],
            "layers": layers}


def check_draw():
    op = 54
    ring = layer(2, "ring", [group(ellipse(440), trim(e=anim((0, 0), (22, 100))), stroke(C1, 22))], op,
                 r=val(-90), s=anim((36, [100, 100, 100]), (42, [108, 108, 100]), (50, [100, 100, 100]), ease=EASE_IO))
    tick = layer(1, "check", [group(path([(-110, 10), (-30, 90), (120, -70)]), trim(e=anim((18, 0), (36, 100))),
                                    stroke(C2, 28))], op)
    return comp("check-draw", op, [tick, ring])


def pulse_rings():
    op, layers = 75, []
    for k, t0 in enumerate((0, 18, 36)):
        layers.append(layer(k + 2, f"ring{k}", [group(ellipse(500), stroke(C1 if k != 1 else C3, 16))], op,
                            s=anim((t0, [15, 15, 100]), (t0 + 38, [100, 100, 100])),
                            o=anim((t0, 100), (t0 + 38, 0))))
    layers.insert(0, layer(1, "dot", [group(ellipse(80), fill(C2))], op,
                           s=anim((0, [0, 0, 100]), (10, [120, 120, 100]), (16, [100, 100, 100]), ease=EASE_IO)))
    return comp("pulse-rings", op, layers)


def spark_burst():
    op, layers = 45, []
    for k in range(8):
        a = math.radians(k * 45 - 90)
        pts = [(90 * math.cos(a), 90 * math.sin(a)), (250 * math.cos(a), 250 * math.sin(a))]
        layers.append(layer(k + 1, f"ray{k}", [group(path(pts), trim(s=anim((8, 0), (30, 100)), e=anim((0, 0), (18, 100))),
                                                    stroke(C1 if k % 2 == 0 else C3, 18))], op))
        b = math.radians(k * 45 - 67.5)
        layers.append(layer(k + 9, f"dot{k}", [group(ellipse(26), fill(C2))], op,
                            p=(300 + 205 * math.cos(b), 300 + 205 * math.sin(b)),
                            s=anim((6, [0, 0, 100]), (16, [100, 100, 100]), (34, [0, 0, 100]), ease=EASE_IO)))
    return comp("spark-burst", op, layers)


def eq_bars():
    op, layers = 60, []
    levels = [30, 100, 50, 85, 30]
    for k in range(5):
        seq = levels[k % 5:] + levels[:k % 5]
        seq = seq[:4] + [seq[0]]  # bucle exacto: cuadro 60 = cuadro 0
        kfs = [(i * 15, [100, v, 100]) for i, v in enumerate(seq)]
        layers.append(layer(k + 1, f"bar{k}", [group(rect(64, 360, p=(0, -180), r=14), fill(C1 if k % 2 == 0 else C2))],
                            op, p=(120 + k * 90, 480), s=anim(*kfs, ease=EASE_IO)))
    return comp("eq-bars", op, layers)


BUILTINS = {
    "check-draw": (check_draw, "Un círculo y un check que se dibujan (logro, verificado, listo)", False),
    "pulse-rings": (pulse_rings, "Pulsos que se expanden desde un punto (señal, alerta, «aquí»)", False),
    "spark-burst": (spark_burst, "Estallido de rayos y puntos (idea, descubrimiento, remate)", False),
    "eq-bars": (eq_bars, "Ecualizador de cinco barras en bucle (música, audio, voz)", True),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for ident, (fn, desc, loop) in BUILTINS.items():
        anim_ = fn()
        assert not lottielib.problems(anim_), (ident, lottielib.problems(anim_))
        oslib.write_json(OUT / f"{ident}.json", anim_)
        items.append({"id": ident, "file": f"{ident}.json", "description": desc,
                      "origin": "propia (VideoVibe, scripts/tools/lottie_builtins.py)", "license": "Apache-2.0",
                      "ads": True, "loop": loop, "recolor": {C1: "accent", C2: "accent2", C3: "accent3"},
                      **lottielib.info(anim_)})
    oslib.write_json(OUT / "library.json", {"_note": "Animaciones propias del motor. Las de cada canal van en "
                                                     "<canal>/assets/lottie/ (scripts/tools/lottie.py add).",
                                            "items": items})
    oslib.emit({"ok": True, "dir": str(OUT), "items": [i["id"] for i in items]})


if __name__ == "__main__":
    main()
