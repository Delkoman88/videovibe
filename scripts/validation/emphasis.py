
def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    emph = sb.get("emphasis", {})
    if not isinstance(emph, dict):
        errs.append("emphasis: debe ser un objeto {id_de_palabra: rol}")
        emph = {}
    unknown = [w for w in emph if ctx.get("word_ids") is not None and w not in ctx["word_ids"]]
    if unknown:
        errs.append(f"emphasis: palabras que no existen en captions.json: {unknown[:10]} "
                    "(los ids cambian si se vuelve a transcribir)")
    bad_roles = sorted({r for r in emph.values() if ctx.get("roles") and r not in ctx["roles"]})
    if bad_roles:
        errs.append(f"emphasis: roles que no existen en brand.json → highlight_roles: {bad_roles}")

