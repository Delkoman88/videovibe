"""`transitions`: capas que cubren el corte (ADR 0028). Errores juntos y con ruta."""
from formats.text import plain
from scripts.composer.transitions import DEFAULT_DURATION, KINDS, SFX
from .common import _num

ROLES = ("accent", "accent2", "accent3")
MIN_GAP = 1.5      # segundos entre transiciones: más seguido cansa
SNAP = 0.25        # distancia a un corte o borde de escena para no avisar
MAX_WORD = 14


def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    items = sb.get("transitions", [])
    if not isinstance(items, list):
        errs.append("transitions: debe ser una lista")
        return
    edges = list(ctx.get("cuts") or [])
    for key in ("scenes", "broll"):
        for x in sb.get(key) or []:
            if isinstance(x, dict):
                edges += [t for t in (x.get("in"), x.get("out")) if _num(t)]
    ats = []
    for i, tr in enumerate(items):
        p = f"transitions[{i}]"
        if not isinstance(tr, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        kind, at, d = tr.get("kind"), tr.get("at"), tr.get("duration", DEFAULT_DURATION)
        if kind not in KINDS:
            errs.append(f"{p}.kind: «{kind}» (usa {', '.join(KINDS)})")
        if not _num(d) or not 0.4 <= d <= 1.2:
            errs.append(f"{p}.duration: número entre 0.4 y 1.2 (segundos)")
            d = DEFAULT_DURATION
        if not _num(at):
            errs.append(f"{p}.at: segundo del corte (obligatorio)")
            continue
        if at - d / 2 < 0 or (state.end is not None and at + d / 2 > state.end + 0.05):
            errs.append(f"{p}.at: {at} s con duración {d} se sale del video")
        ats.append((at, p))
        if kind == "word-wall":
            w = plain(tr.get("word") or "")
            if not w:
                errs.append(f"{p}.word: obligatorio en word-wall (una palabra)")
            elif len(w) > MAX_WORD:
                errs.append(f"{p}.word: máximo {MAX_WORD} caracteres")
        elif "word" in tr:
            warns.append(f"{p}.word: solo lo usa word-wall (se ignora)")
        if tr.get("role", "accent") not in ROLES:
            errs.append(f"{p}.role: «{tr.get('role')}» (usa {', '.join(ROLES)})")
        sfx = tr.get("sfx", SFX.get(kind))
        if "sfx" in tr and sfx and ctx.get("kit") is not None and sfx not in ctx["kit"]:
            errs.append(f"{p}.sfx: «{sfx}» no está en el kit del canal (scripts/audio/sfx.py --channel <canal> --list)")
        if edges and min(abs(at - e) for e in edges) > SNAP:
            near = min(edges, key=lambda e: abs(at - e))
            warns.append(f"{p}.at: {at:.2f} s no cae en un corte ni en el borde de una escena (el más cercano: "
                         f"{near:.2f} s); la transición tapa el cambio solo si coincide")
    ats.sort()
    for (a1, p1), (a2, p2) in zip(ats, ats[1:]):
        if a2 - a1 < MIN_GAP:
            errs.append(f"{p2}: a {a2 - a1:.2f} s de {p1} (mínimo {MIN_GAP} s entre transiciones)")
