
def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    plats = sb.get("platforms", {})
    if not isinstance(plats, dict):
        errs.append("platforms: debe ser un objeto {plataforma: {cta_text}}")
        plats = {}
    for name in plats:
        if name not in ctx.get("presets", {}):
            errs.append(f"platforms.{name}: no hay presets/{name}.json "
                        f"(disponibles: {', '.join(sorted(ctx.get('presets', {})))})")
    ads_plats = [p for p in plats if ctx.get("presets", {}).get(p, {}).get("ads")]

    state.ads_plats = ads_plats
