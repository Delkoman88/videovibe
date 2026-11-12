"""Bloque automático de sonido en <pieza>/assets.md (música y efectos con su licencia)."""


AUTO_BEGIN, AUTO_END = "<!-- audio:auto -->", "<!-- /audio:auto -->"


def audio_credits_md(credits):
    """Bloque de assets.md con la música y los efectos que suenan en la pieza (lo mantiene compose.py)."""
    rows = []
    for role, label in (("main", "Música"), ("ads", "Música (versión anuncio)")):
        t = credits["music"].get(role)
        if not t or (role == "ads" and t is credits["music"].get("main")):
            continue
        who = t.get("artist") or t.get("provided_by") or ""
        origin = {"epidemic": "Epidemic Sound", "propia": "propia (`scripts/audio/musicgen.py`)",
                  "usuario": f"aportada por {t.get('provided_by', '?')}"}.get(t.get("source"), t.get("source", ""))
        sid = f", id {t['source_id']}" if t.get("source_id") else ""
        rows.append(f"| {label} | «{t['title']}»{' — ' + who if who and t.get('source') != 'usuario' else ''} "
                    f"({origin}{sid}) | {t.get('license', '?')}{' · apta para anuncios' if t.get('ads') else ''} |")
    own = sorted(n for n, m in credits["sfx"].items() if m.get("source", "base") in ("base", "receta"))
    if own:
        rows.append(f"| Efectos propios | {', '.join(own)} (`scripts/audio/sfx.py`, síntesis y recetas) | Propios, sin restricciones |")
    for n, m in sorted(credits["sfx"].items()):
        if m.get("source") == "usuario":
            rows.append(f"| Efecto «{n}» | aportado por {m.get('provided_by', '?')} | {m.get('license', '?')}"
                        f"{' · apta para anuncios' if m.get('ads') else ''} |")
    if not rows:
        return ""
    return (f"{AUTO_BEGIN}\n## Sonido (automático: lo actualiza compose.py)\n\n| Recurso | Origen | Licencia |\n"
            f"|---|---|---|\n" + "\n".join(rows) + f"\n{AUTO_END}")


def update_assets_md(P, block):
    f = P / "assets.md"
    txt = f.read_text(encoding="utf-8") if f.exists() else "# Fuentes y licencias de los recursos usados\n"
    if AUTO_BEGIN in txt and AUTO_END in txt:
        a, b = txt.index(AUTO_BEGIN), txt.index(AUTO_END) + len(AUTO_END)
        txt = txt[:a] + block + txt[b:]
    elif block:
        txt = txt.rstrip("\n") + "\n\n" + block + "\n"
    f.write_text(txt, encoding="utf-8")


def update_broll_credits(P, clips, media):
    """Registra cada archivo visual usado y sus derechos en assets.md."""
    begin, end = "<!-- broll:auto -->", "<!-- /broll:auto -->"
    f = P / "assets.md"
    txt = f.read_text(encoding="utf-8") if f.exists() else "# Fuentes y licencias de los recursos usados\n"
    rows = []
    for source in dict.fromkeys(c["source"] for c in clips):
        c = next(c for c in clips if c["source"] == source)
        rows.append(f"| {media[source]['file']} | {c['origin']} | {c['license']}"
                    f"{' · apto para anuncios' if c.get('ads') else ''} |")
    block = (f"{begin}\n## Video de apoyo (automático: lo actualiza compose.py)\n\n"
             "| Archivo | Origen | Licencia |\n|---|---|---|\n" + "\n".join(rows) + f"\n{end}") if rows else ""
    if begin in txt and end in txt:
        a, b = txt.index(begin), txt.index(end) + len(end)
        txt = txt[:a] + block + txt[b:]
    elif block:
        txt = txt.rstrip("\n") + "\n\n" + block + "\n"
    f.write_text(txt, encoding="utf-8")
