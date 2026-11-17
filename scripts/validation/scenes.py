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
            else:
                if reg[fmt].get("check"):
                    errs += [f"{p}.params.{m}" for m in reg[fmt]["check"](params)]
                if reg[fmt].get("uses") and not any(e.startswith(f"{p}.params") for e in errs):
                    from scripts.core import assetlib, lottielib
                    # platforms se valida después: aquí se mira directo si alguna plataforma es de anuncios
                    ads = any(ctx.get("presets", {}).get(pl, {}).get("ads") for pl in (sb.get("platforms") or {}))
                    for kind, ident in reg[fmt]["uses"](params):
                        errs += [f"{p}.params: {m}" for m in
                                 assetlib.problems(kind, ident, ctx.get("channel_dir"), ads=ads)]
                        it = assetlib.item(kind, ident, ctx.get("channel_dir"))
                        if kind == "lottie" and it:
                            errs += [f"{p}.params: «{ident}» {m}" for m in lottielib.map_problems(it.get("recolor"))]
                    if reg[fmt].get("check_items"):
                        items = {i: assetlib.item(k, i, ctx.get("channel_dir")) for k, i in reg[fmt]["uses"](params)}
                        errs += [f"{p}.params.{m}" for m in reg[fmt]["check_items"](params, items)]
        if "layout" in sc and sc["layout"] not in LAYOUTS:
            errs.append(f"{p}.layout: «{sc['layout']}» no existe ({', '.join(sorted(LAYOUTS))})")
        for k in ("sfx", "sfx_out"):
            if isinstance(sc.get(k), str):
                sound(f"{p}.{k}", sc[k])
            elif k in sc and sc[k] is not False and sc[k] is not True:
                errs.append(f"{p}.{k}: nombre de efecto o false")

