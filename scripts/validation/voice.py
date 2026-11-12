from .common import VOICE_KEYS, STRENGTHS

def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    v = sb.get("voice", {})
    if v:
        for k in sorted(set(v) - VOICE_KEYS):
            errs.append(f"voice.{k}: clave desconocida ({', '.join(sorted(VOICE_KEYS))})")
        if "strength" in v and v["strength"] not in STRENGTHS:
            errs.append(f"voice.strength: «{v['strength']}» no válido (natural, fuerte)")
        for k in VOICE_KEYS - {"strength"}:
            if k in v and not isinstance(v[k], bool):
                errs.append(f"voice.{k}: true o false")
