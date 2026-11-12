from .common import ADS_VALUES, _num

def _used_sounds(sb, auto):
    names = set()
    for sc in sb.get("scenes", []):
        for k in ("sfx", "sfx_out"):
            if isinstance(sc.get(k), str):
                names.add(sc[k])
    for k in ("overlays", "exits"):
        if isinstance(auto.get(k), str):
            names.add(auto[k])
    if isinstance(auto.get("scenes"), list):
        names |= set(auto["scenes"])
    elif isinstance(auto.get("scenes"), str):
        names.add(auto["scenes"])
    names |= {c.get("sound") for c in sb.get("audio", {}).get("sfx", [])}
    return names



def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    dur, end, ids = state.dur, state.end, state.ids
    span, sound, ads_plats = state.span, state.sound, state.ads_plats
    au = sb.get("audio") or {}
    m = au.get("music")
    lib = ctx.get("library", {})
    if m:
        tr = lib.get(m.get("track"))
        if not tr:
            errs.append(f"audio.music.track: «{m.get('track')}» no está en la biblioteca del canal "
                        "(scripts/audio/music.py list --channel …)")
        ads = m.get("ads", "quiza")
        if ads not in ADS_VALUES:
            errs.append(f"audio.music.ads: «{ads}» no válido (si, no, quiza)")
        if ads == "si" and tr and not tr.get("ads"):
            errs.append(f"audio.music.track: «{tr['id']}» no tiene licencia para anuncios y la pieza lleva "
                        "publicidad (ads: si)")
        if m.get("ads_track"):
            at = lib.get(m["ads_track"])
            if not at:
                errs.append(f"audio.music.ads_track: «{m['ads_track']}» no está en la biblioteca")
            elif not at.get("ads"):
                errs.append(f"audio.music.ads_track: «{at['id']}» no tiene licencia para anuncios")
        elif ads_plats and tr and not tr.get("ads") and not any(t.get("ads") for t in lib.values()):
            errs.append(f"platforms.{ads_plats[0]}: es de pauta pagada y el canal no tiene ninguna pista con "
                        "licencia para anuncios (scripts/audio/musicgen.py … --add)")
        for k in ("level_db", "duck_db", "start", "fade_in", "fade_out"):
            if k in m and not _num(m[k]):
                errs.append(f"audio.music.{k}: debe ser un número")
    auto = au.get("sfx_auto") or {}
    for k in ("overlays", "exits"):
        if isinstance(auto.get(k), str):
            sound(f"audio.sfx_auto.{k}", auto[k])
    sc_auto = auto.get("scenes")
    if isinstance(sc_auto, str) and sc_auto != "variado":
        sound("audio.sfx_auto.scenes", sc_auto)
    elif isinstance(sc_auto, list):
        for j, n in enumerate(sc_auto):
            sound(f"audio.sfx_auto.scenes[{j}]", n)
    for i, c in enumerate(au.get("sfx", [])):
        p = f"audio.sfx[{i}]"
        if not _num(c.get("at")):
            errs.append(f"{p}.at: obligatorio (segundo exacto)")
        elif end is not None and c["at"] > end:
            errs.append(f"{p}.at: {c['at']} pasa del final del video ({end:.2f} s)")
        if not c.get("sound"):
            errs.append(f"{p}.sound: obligatorio")
        else:
            sound(f"{p}.sound", c["sound"])
    if ads_plats and ctx.get("kit"):
        used = {n for n in _used_sounds(sb, auto) if n in ctx["kit"]}
        no_ads = sorted(n for n in used if ctx["kit"][n].get("ads") is False)
        if no_ads:
            errs.append(f"platforms.{ads_plats[0]}: es de pauta pagada y estos efectos no tienen licencia para "
                        f"anuncios: {no_ads}")

