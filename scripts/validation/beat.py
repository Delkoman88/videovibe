"""`beat_fx`: efectos al ritmo de la música, y avisos de sincronía (`channel.json → beat_snap`), ADR 0026."""
from .common import _num

FX = ("pulse", "shake", "flash", "strobe")
EVERY = ("beat", "half", "bar", "2bars")


def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    items = sb.get("beat_fx", [])
    if not isinstance(items, list):
        errs.append("beat_fx: debe ser una lista")
        items = []
    spans = []
    for i, it in enumerate(items):
        p = f"beat_fx[{i}]"
        if not isinstance(it, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        state.span(p, it)
        if it.get("fx") not in FX:
            errs.append(f"{p}.fx: «{it.get('fx')}» (usa {', '.join(FX)})")
        if it.get("every", "beat") not in EVERY:
            errs.append(f"{p}.every: «{it.get('every')}» (usa {', '.join(EVERY)})")
        s = it.get("strength", 0.5)
        if not _num(s) or not 0 < s <= 1:
            errs.append(f"{p}.strength: número entre 0 y 1")
            s = 0.5
        a, b = it.get("in"), it.get("out")
        if _num(a) and _num(b):
            spans.append((a, b, p))
            talk = [w for w in ctx.get("speech") or [] if w[0] < b and w[1] > a]
            if talk and s > 0.6 and it.get("fx") in ("shake", "strobe", "pulse"):
                warns.append(f"{p}: {it.get('fx')} fuerte ({s}) mientras se habla distrae; baja `strength` o úsalo "
                             f"en tramos sin voz")
    spans.sort()
    for (a1, b1, p1), (a2, b2, p2) in zip(spans, spans[1:]):
        if a2 < b1 - 0.001:
            errs.append(f"{p2}: se solapa con {p1}")
    if items and not ((sb.get("audio") or {}).get("music") or {}).get("track"):
        warns.append("beat_fx: sin pista de música, los golpes salen del audio de la toma (beats.py --source plate)")
    beats = ctx.get("beats")
    if beats and ctx.get("beat_snap"):
        starts = [(f"scenes[{i}]", x.get("in")) for i, x in enumerate(sb.get("scenes") or []) if isinstance(x, dict)]
        starts += [(f"overlays[{i}]", x.get("in")) for i, x in enumerate(sb.get("overlays") or []) if isinstance(x, dict)]
        starts += [(f"fx[{i}]", x.get("in", x.get("at"))) for i, x in enumerate(sb.get("fx") or []) if isinstance(x, dict)]
        for p, t in starts:
            if _num(t) and beats[0] <= t <= beats[-1]:
                near = min(beats, key=lambda x: abs(x - t))
                if abs(near - t) > 0.08:
                    warns.append(f"{p}.in: {t:.2f} s está a {abs(near - t) * 1000:.0f} ms del golpe más cercano "
                                 f"({near:.2f} s); el canal pide sincronía (beat_snap)")
