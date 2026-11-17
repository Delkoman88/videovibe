from formats.text import VARIANTS

from .common import OVERLAY_TYPES

def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    overlays = sb.get("overlays", [])
    if not isinstance(overlays, list):
        errs.append("overlays: debe ser una lista")
        overlays = []
    for i, o in enumerate(overlays):
        p = f"overlays[{i}]"
        if not isinstance(o, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        if not o.get("id"):
            errs.append(f"{p}.id: obligatorio")
        elif o["id"] in ids:
            errs.append(f"{p}.id: «{o['id']}» repetido")
        ids.add(o.get("id"))
        if o.get("type") not in OVERLAY_TYPES:
            errs.append(f"{p}.type: «{o.get('type')}» no existe ({', '.join(sorted(OVERLAY_TYPES))})")
        if not o.get("text"):
            errs.append(f"{p}.text: obligatorio")
        if "role" in o and ctx.get("roles") and o["role"] not in ctx["roles"]:
            errs.append(f"{p}.role: «{o['role']}» no existe en brand.json → highlight_roles "
                        f"({', '.join(sorted(ctx['roles']))})")
        if "text_fx" in o:
            if o.get("type") == "cta":
                errs.append(f"{p}.text_fx: la CTA no admite text_fx (su texto cambia por plataforma)")
            elif o["text_fx"] not in VARIANTS:
                errs.append(f"{p}.text_fx: «{o['text_fx']}» (usa {', '.join(VARIANTS)})")
        span(p, o)
        if isinstance(o.get("sfx"), str):
            sound(f"{p}.sfx", o["sfx"])

