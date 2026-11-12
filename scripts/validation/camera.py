from .common import MOVE_TYPES, _num

def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    cam = sb.get("camera", {})
    for i, m in enumerate(cam.get("moves", []) if isinstance(cam, dict) else []):
        p = f"camera.moves[{i}]"
        if m.get("type", "punch") not in MOVE_TYPES:
            errs.append(f"{p}.type: «{m.get('type')}» no existe (punch, creep)")
        if not _num(m.get("scale")) or not 1.0 <= m["scale"] <= 1.3:
            errs.append(f"{p}.scale: entre 1.0 y 1.3")
        if not _num(m.get("t")) or not _num(m.get("until")) or m["until"] <= m["t"]:
            errs.append(f"{p}: «t» y «until» obligatorios, until > t")
        elif end is not None and m["until"] > end + 0.05:
            errs.append(f"{p}.until: {m['until']} pasa del final del video ({end:.2f} s)")

