from scripts.core import oslib
from .common import ROOT_KEYS, _num, State
from . import overlays, scenes, camera, emphasis, platforms, broll, audio, voice, captions, fx, beat, transitions

def context(P, ch=None):
    """Todo lo que la validación necesita saber de la pieza y su canal."""
    import formats
    ch = ch or oslib.load_channel(P)
    cmap_f, caps_f = P / "cut" / "cut-map.json", P / "captions" / "captions.json"
    lib_f = ch["dir"] / "audio" / "music" / "library.json"
    kit_f = ch["dir"] / "audio" / "sfx" / "sfx.json"
    packs = tuple(ch["config"].get("format_packs", []))
    formats.CTX["piece_dir"] = str(P)
    return {
        "duration": oslib.read_json(cmap_f)["duration_s"] if cmap_f.exists() else None,
        "cuts": [s["out_out"] for s in oslib.read_json(cmap_f)["segments"][:-1]] if cmap_f.exists() else None,
        "words": oslib.read_json(caps_f)["words"] if caps_f.exists() else [],
        "word_ids": {w["id"] for w in oslib.read_json(caps_f)["words"]} if caps_f.exists() else None,
        "speech": [(w["start"], w["end"]) for w in oslib.read_json(caps_f)["words"]] if caps_f.exists() else None,
        "roles": set(ch["brand"].get("highlight_roles", {})),
        "formats": formats.registry(packs),
        "channel_dir": ch["dir"],
        "beats": oslib.read_json(P / "audio" / "beats.json")["beats"] if (P / "audio" / "beats.json").exists() else None,
        "beat_snap": bool(ch["config"].get("beat_snap")),
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
    if not _num(tail) or not 0 <= tail <= 5:
        errs.append("tail_s: número entre 0 y 5 (segundos de último cuadro congelado)")
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
    captions.validate(sb, state)
    audio.validate(sb, state)
    voice.validate(sb, state)
    fx.validate(sb, state)
    beat.validate(sb, state)
    transitions.validate(sb, state)
    if "motion" in sb:
        from formats.direction import validate as validate_motion
        errs.extend(validate_motion(sb['motion']))
        if not errs:
            from scripts.core.animationanchors import resolve as resolve_anchors
            try:
                anchored = resolve_anchors(sb, ctx.get('words', []))
                if anchored != sb: errs.append('anclajes sin resolver: ejecuta animation-style --snapshot --dry-run')
            except (ValueError, TypeError) as e: errs.append(str(e))
            for i, scene in enumerate(sb.get('scenes', [])):
                duration = scene['out'] - scene['in']
                if sb['motion']['version'] == 2:
                    from formats.direction import budget
                    try: budget(scene, sb['motion'])
                    except ValueError as e: errs.append(str(e))
                if duration < sb['motion']['enter_s'] + sb['motion']['exit_s'] + .5:
                    errs.append(f'scenes[{i}]: duración insuficiente para el perfil')
                if scene.get('format') == 'narrative-sequence' and duration < len(scene['params']['steps']):
                    errs.append(f'scenes[{i}]: reserva al menos un segundo por paso')
                if scene.get('format') == 'narrative-sequence':
                    steps=scene['params']['steps']
                    times=[s.get('at',j*duration/len(steps)) for j,s in enumerate(steps)]+[duration]
                    if any(b-a<.75 for a,b in zip(times,times[1:])):
                        errs.append(f'scenes[{i}]: pasos fuera de duración o sin tiempo de lectura')
                    if sb['motion']['version']==2:
                        for j,step in enumerate(steps):
                            required=max(1,len(step['text'].split())/sb['motion']['reading_wps'])+.55
                            if times[j+1]-times[j]<required:
                                errs.append(f'scenes[{i}].steps[{j}]: necesita {required:.2f}s incluyendo lectura')
                if scene.get('anchor', {}).get('word_id') not in (ctx.get('word_ids') or set()) and scene.get('anchor'):
                    errs.append(f'scenes[{i}].anchor: palabra ausente; resuelve el anclaje de nuevo')
            from scripts.core.animationqa import inspect
            for issue in inspect(sb, ctx.get('formats', {}))['issues']:
                (errs if issue['level']=='error' else warns).append(f"{issue['path']}: {issue['message']}")
    return errs, warns
