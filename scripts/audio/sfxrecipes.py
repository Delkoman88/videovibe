from pathlib import Path
import sys
"""Recetas de efectos de sonido por canal (channels/<canal>/audio/sfx/recipes.json): esquema y validación.

Sin numpy: lo usan scripts/audio/sfx.py (que las sintetiza) y scripts/tools/check_channel.py (que las valida).
Formato completo y ejemplos: docs/audio.md.
"""
import re

LAYER_TYPES = {
    "tone": "tono con barrido f0→f1 y armónicos (bleeps, pulsos, láser)",
    "noise": "ruido en una banda lo–hi, con barrido opcional a lo1–hi1 (aire, whoosh, soplo, agua)",
    "fm": "síntesis FM: campana, metal, cristal (f, ratio, index)",
    "sub": "golpe grave que cae de f0 a f1 (impacto, bombo, latido)",
    "grains": "n destellos cortos dispersos entre f_lo y f_hi (burbujas, chispas, tecleo)",
}
COMMON = {"type", "at", "gain", "pan", "attack", "decay", "repeat", "every", "length"}
FIELDS = {
    "tone": {"f0", "f1", "harm"},
    "noise": {"lo", "hi", "lo1", "hi1"},
    "fm": {"f", "ratio", "index", "index_decay"},
    "sub": {"f0", "f1"},
    "grains": {"count", "f_lo", "f_hi", "grain", "spread", "rising", "seed"},
}
REQUIRED = {"tone": {"f0"}, "noise": {"lo", "hi"}, "fm": {"f"}, "sub": set(), "grains": {"count", "f_lo", "f_hi"}}
FX = {"reverb": (0.0, 1.0), "lowpass": (200.0, 20000.0), "highpass": (20.0, 8000.0),
      "bitcrush": (2.0, 12.0), "tremolo": (0.5, 40.0), "tremolo_depth": (0.0, 1.0)}
FREQ_FIELDS = {"f0", "f1", "f", "lo", "hi", "lo1", "hi1", "f_lo", "f_hi"}
RANGES = {"at": (0.0, 4.0), "gain": (0.0, 2.0), "attack": (0.0005, 1.0), "decay": (0.002, 4.0),
          "repeat": (1, 32), "every": (0.01, 2.0), "length": (0.01, 4.0), "harm": (0.0, 1.0),
          "ratio": (0.1, 12.0), "index": (0.0, 20.0), "index_decay": (0.01, 4.0), "count": (1, 64),
          "grain": (0.005, 0.5), "spread": (0.0, 1.0), "seed": (0, 10_000)}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
ROOT_RE = re.compile(r"^\s*root\s*(?:([*/])\s*(\d+(?:\.\d+)?))?\s*$")


def freq(v, root):
    """Hz desde un número o una expresión relativa al tono del canal: "root", "root*1.5", "root/2"."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if isinstance(v, str):
        m = ROOT_RE.match(v)
        if m:
            if not m.group(1):
                return float(root)
            k = float(m.group(2))
            if k == 0:
                raise ValueError("división entre 0")
            return float(root) * k if m.group(1) == "*" else float(root) / k
    raise ValueError(f"«{v}» no es una frecuencia (usa Hz, \"root\", \"root*1.5\" o \"root/2\")")


def validate(data, root=880.0):
    """Lista de errores (vacía si todo está bien). Mensajes con la ruta exacta del campo."""
    errs = []
    if not isinstance(data, dict) or not isinstance(data.get("recipes"), dict):
        return ['recipes.json debe ser {"recipes": {"<nombre>": {...}}}']
    for name, r in data["recipes"].items():
        p = f"recipes.{name}"
        if not NAME_RE.match(name):
            errs.append(f"{p}: nombre inválido (minúsculas, números y guiones; máx. 32)")
        if not isinstance(r, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        unknown = set(r) - {"use", "duration", "layers", "fx", "entrance"}
        if unknown:
            errs.append(f"{p}: campos desconocidos {sorted(unknown)}")
        if not isinstance(r.get("use"), str) or not r.get("use").strip():
            errs.append(f"{p}.use: falta la descripción de cuándo usarlo")
        dur = r.get("duration")
        if not isinstance(dur, (int, float)) or not 0.03 <= dur <= 4.0:
            errs.append(f"{p}.duration: entre 0.03 y 4 s")
            dur = 4.0
        layers = r.get("layers")
        if not isinstance(layers, list) or not 1 <= len(layers) <= 12:
            errs.append(f"{p}.layers: lista de 1 a 12 capas")
            layers = []
        for i, lay in enumerate(layers):
            q = f"{p}.layers[{i}]"
            if not isinstance(lay, dict):
                errs.append(f"{q}: debe ser un objeto")
                continue
            t = lay.get("type")
            if t not in LAYER_TYPES:
                errs.append(f"{q}.type: «{t}» no existe ({', '.join(LAYER_TYPES)})")
                continue
            extra = set(lay) - COMMON - FIELDS[t]
            if extra:
                errs.append(f"{q}: campos no válidos para «{t}»: {sorted(extra)} (válidos: {sorted(COMMON | FIELDS[t])})")
            for k in REQUIRED[t] - set(lay):
                errs.append(f"{q}.{k}: obligatorio para «{t}»")
            for k, v in lay.items():
                if k in FREQ_FIELDS:
                    try:
                        hz = freq(v, root)
                        if not 20 <= hz <= 22000:
                            errs.append(f"{q}.{k}: {hz:.0f} Hz fuera de 20–22000")
                    except ValueError as e:
                        errs.append(f"{q}.{k}: {e}")
                elif k in RANGES:
                    lo, hi = RANGES[k]
                    if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
                        errs.append(f"{q}.{k}: entre {lo} y {hi}")
                elif k == "pan" and not (isinstance(v, (int, float)) and -1 <= v <= 1):
                    errs.append(f"{q}.pan: entre -1 (izq.) y 1 (der.)")
                elif k == "rising" and not isinstance(v, bool):
                    errs.append(f"{q}.rising: true o false")
            if isinstance(lay.get("at"), (int, float)) and lay["at"] >= dur:
                errs.append(f"{q}.at: empieza después del final ({dur} s)")
            if lay.get("repeat", 1) > 1 and "every" not in lay:
                errs.append(f"{q}.every: obligatorio con repeat > 1 (segundos entre repeticiones)")
        fx = r.get("fx", {})
        if not isinstance(fx, dict):
            errs.append(f"{p}.fx: debe ser un objeto")
            fx = {}
        for k, v in fx.items():
            if k not in FX:
                errs.append(f"{p}.fx.{k}: no existe ({', '.join(FX)})")
            elif not isinstance(v, (int, float)) or not FX[k][0] <= v <= FX[k][1]:
                errs.append(f"{p}.fx.{k}: entre {FX[k][0]} y {FX[k][1]}")
        if "entrance" in r and not isinstance(r["entrance"], bool):
            errs.append(f"{p}.entrance: true o false")
    return errs
