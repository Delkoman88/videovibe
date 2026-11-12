import math
import re
from .common import _num

def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    broll = sb.get("broll", [])
    if not isinstance(broll, list):
        errs.append("broll: debe ser una lista")
        broll = []
    previous_out = 0
    for i, clip in enumerate(broll):
        p = f"broll[{i}]"
        if not isinstance(clip, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        cid = clip.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", cid):
            errs.append(f"{p}.id: usa letras, números, guion o guion bajo; empieza con letra")
        elif cid in ids:
            errs.append(f"{p}.id: «{cid}» repetido")
        ids.add(cid)
        span(p, clip, allow_tail=False)
        if _num(clip.get("in")) and clip["in"] < previous_out - 0.001:
            errs.append(f"{p}.in: los insertos deben ir en orden y no solaparse")
        if _num(clip.get("out")):
            previous_out = max(previous_out, clip["out"])
        source_id = clip.get("source")
        source = ctx.get("media", {}).get(source_id) if isinstance(source_id, str) else None
        if not source or source.get("kind") not in ("broll", "pantalla") or not source.get("width"):
            errs.append(f"{p}.source: debe ser un id de video kind=broll o kind=pantalla de media.json")
        source_in = clip.get("source_in", 0)
        if not _num(source_in) or source_in < 0:
            errs.append(f"{p}.source_in: número no negativo")
        elif source and _num(clip.get("in")) and _num(clip.get("out")) and \
                source_in + clip["out"] - clip["in"] > source.get("duration_s", 0) + 0.05:
            errs.append(f"{p}.source_in: el tramo termina después del archivo fuente")
        fit = clip.get("fit", "cover")
        if fit not in ("cover", "contain", "region"):
            errs.append(f"{p}.fit: cover, contain o region")
        region = clip.get("region")
        if fit == "region":
            if not isinstance(region, dict) or set(region) != {"x", "y", "w", "h"} or \
                    any(not _num(region.get(k)) or not math.isfinite(region[k]) for k in ("x", "y", "w", "h")):
                errs.append(f"{p}.region: objeto con x, y, w, h numéricos (proporciones de 0 a 1)")
            elif not (0 <= region["x"] < 1 and 0 <= region["y"] < 1 and 0 < region["w"] <= 1
                      and 0 < region["h"] <= 1 and region["x"] + region["w"] <= 1.000001
                      and region["y"] + region["h"] <= 1.000001):
                errs.append(f"{p}.region: debe quedar dentro de la imagen y tener área positiva")
            if "focus_x" in clip or "focus_y" in clip:
                errs.append(f"{p}: focus_x/focus_y no se usan con fit=region")
        elif region is not None:
            errs.append(f"{p}.region: solo se usa con fit=region")
        if fit == "contain" and source and source.get("width", 0) > source.get("height", 0) and \
                360 / source["width"] < 0.75:
            warns.append(f"{p}.fit: la captura horizontal completa se reduce a escala de teléfono "
                         f"({360 / source['width']:.2f}×); revisa si el texto se lee en los cuadros de 360 px")
        for axis in ("x", "y"):
            v = clip.get(f"focus_{axis}", 50)
            if not _num(v) or not 0 <= v <= 100:
                errs.append(f"{p}.focus_{axis}: número entre 0 y 100")
        if not isinstance(clip.get("origin"), str) or not clip["origin"].strip():
            errs.append(f"{p}.origin: indica quién aportó el archivo")
        if not isinstance(clip.get("license"), str) or not clip["license"].strip():
            errs.append(f"{p}.license: registra los derechos de uso")
        if ads_plats and clip.get("ads") is not True:
            errs.append(f"{p}.ads: confirma true para usar este archivo en anuncios")

