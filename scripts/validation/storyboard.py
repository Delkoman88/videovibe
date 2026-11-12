from scripts.core import oslib
from .common import ROOT_KEYS, _num, State
from . import overlays, scenes, camera, emphasis, platforms, broll, audio, voice

def context(P, ch=None):
    """Todo lo que la validación necesita saber de la pieza y su canal."""
    import formats
    ch = ch or oslib.load_channel(P)
    cmap_f, caps_f = P / "cut" / "cut-map.json", P / "captions" / "captions.json"
    lib_f = ch["dir"] / "audio" / "music" / "library.json"
    kit_f = ch["dir"] / "audio" / "sfx" / "sfx.json"
    packs = tuple(ch["config"].get("format_packs", []))
    return {
        "duration": oslib.read_json(cmap_f)["duration_s"] if cmap_f.exists() else None,
        "word_ids": {w["id"] for w in oslib.read_json(caps_f)["words"]} if caps_f.exists() else None,
        "roles": set(ch["brand"].get("highlight_roles", {})),
        "formats": formats.registry(packs),
        "library": {t["id"]: t for t in oslib.read_json(lib_f)["tracks"]} if lib_f.exists() else {},
        "kit": oslib.read_json(kit_f)["sounds"] if kit_f.exists() else {},
        "presets": {p.stem: oslib.read_json(p) for p in (oslib.ROOT / "presets").glob("*.json")},
        "media": {m["id"]: m for m in oslib.read_json(P / "media.json")["items"]}
        if (P / "media.json").exists() else {},
    }


def validate(sb, ctx):
    """(problemas, avisos). Problemas impiden componer; avisos no."""
    errs, warns = [], []
    if not isinstance(sb, dict):
        return ["storyboard.json debe ser un objeto JSON"], []
    for k in sorted(set(sb) - ROOT_KEYS):
        if not k.startswith("_"):
            warns.append(f"{k}: clave desconocida (se ignora; válidas: {', '.join(sorted(ROOT_KEYS))})")
    tail = sb.get("tail_s", 0)
    if not _num(tail) or not 0 <= tail <= 3:
        errs.append("tail_s: número entre 0 y 3 (segundos de último cuadro congelado)")
        tail = 0
    dur = ctx.get("duration")
    end = (dur + tail) if dur is not None else None

    state = State(ctx, dur, end, errs, warns)
    overlays.validate(sb, state)
    scenes.validate(sb, state)
    camera.validate(sb, state)
    emphasis.validate(sb, state)
    platforms.validate(sb, state)
    broll.validate(sb, state)
    audio.validate(sb, state)
    voice.validate(sb, state)
    return errs, warns
