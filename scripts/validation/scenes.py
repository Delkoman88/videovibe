from .common import LAYOUTS

def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    scenes = sb.get("scenes", [])
    if not isinstance(scenes, list):
        errs.append("scenes: debe ser una lista")
        scenes = []
    reg = ctx.get("formats") or {}
    for i, sc in enumerate(scenes):
        p = f"scenes[{i}]"
        if not isinstance(sc, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        if not sc.get("id"):
            errs.append(f"{p}.id: obligatorio")
        elif sc["id"] in ids:
            errs.append(f"{p}.id: «{sc['id']}» repetido")
        ids.add(sc.get("id"))
        span(p, sc, allow_tail=False)
        fmt = sc.get("format")
        if fmt not in reg:
            errs.append(f"{p}.format: «{fmt}» no está disponible para este canal "
                        f"(ver docs/formats.md; disponibles: {', '.join(sorted(reg))})")
        else:
            params = sc.get("params", {})
            missing = [k for k in reg[fmt]["required"] if k not in params]
            if missing:
                errs.append(f"{p}.params: faltan {missing} (obligatorios de «{fmt}», ver docs/formats.md)")
        if "layout" in sc and sc["layout"] not in LAYOUTS:
            errs.append(f"{p}.layout: «{sc['layout']}» no existe ({', '.join(sorted(LAYOUTS))})")
        for k in ("sfx", "sfx_out"):
            if isinstance(sc.get(k), str):
                sound(f"{p}.{k}", sc[k])
            elif k in sc and sc[k] is not False and sc[k] is not True:
                errs.append(f"{p}.{k}: nombre de efecto o false")

