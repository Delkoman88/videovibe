"""Mezcla de la pieza: música con ducking bajo la voz, efectos de sonido y pista por plataforma."""
import json
import shutil
from dataclasses import dataclass, field

from scripts.core import oslib
from scripts.composer.visual import esc


@dataclass
class AudioPlan:
    els: str = ""                                   # elementos <audio> para index.html
    used: list = field(default_factory=list)        # resumen para la salida JSON
    music_srcs: dict = field(default_factory=dict)  # {"main": ruta, "ads": ruta | None}
    credits: dict = field(default_factory=lambda: {"music": {}, "sfx": {}})  # para assets.md


def speech_intervals(caps, merge_gap=0.6):
    """Tramos con voz (desde las palabras de los subtítulos), unidos si la pausa es < merge_gap."""
    out = []
    for w in sorted(caps["words"], key=lambda x: x["start"]):
        if out and w["start"] - out[-1][1] < merge_gap:
            out[-1][1] = max(out[-1][1], w["end"])
        else:
            out.append([w["start"], w["end"]])
    return out


def duck_lane(intervals, duck, total, pre=0.25, post=0.35):
    """Envolvente de volumen de la música: 1 sin voz, `duck` mientras se habla (máx. 512 puntos)."""
    pts = [{"t": 0.0, "v": duck if intervals and intervals[0][0] - pre <= 0 else 1.0}]
    for a, b in intervals:
        pts += [{"t": round(max(a - pre, 0.0), 3), "v": 1.0 if a - pre > 0 else duck},
                {"t": round(a, 3), "v": duck}, {"t": round(b, 3), "v": duck},
                {"t": round(min(b + post, total), 3), "v": 1.0}]
    pts = sorted({p["t"]: p for p in pts}.values(), key=lambda p: p["t"])
    return pts[:512]


def db(x):
    return 10 ** (x / 20)


def scene_cues(scenes, auto, level, entrances=("pulse",)):
    """Un efecto al entrar cada escena. `auto` es un efecto, una lista que se rota (sin repetir
    seguidos) o "variado" (todas las entradas del kit). Una escena con "sfx": "<efecto>" lo fija;
    con "sfx": false no suena."""
    if auto == "variado":
        auto = list(entrances)
    pool = [auto] if isinstance(auto, str) else list(auto)
    cues, k = [], 0
    for sc in scenes:
        own = sc.get("sfx", True)
        if own is False:
            continue
        if isinstance(own, str):
            sound = own
        else:
            sound = pool[k % len(pool)]
            k += 1
        cues.append({"at": sc["in"] + 0.02, "sound": sound, "db": level})
    return cues


def exit_cues(scenes, sound, level, lead=0.25):
    """Un efecto (p. ej. whoosh) que termina al salir cada escena; "sfx_out": false lo quita."""
    return [{"at": max(0.0, sc["out"] - lead), "sound": sound, "db": level}
            for sc in scenes if sc.get("out") and sc.get("sfx_out", True) is not False]



def music_src_for(preset, srcs):
    """Pista de cada plataforma: la apta para anuncios si el preset es de pauta pagada (presets/ads.json).
    None = la plataforma necesita pista para anuncios y no hay."""
    return srcs.get("ads") if preset.get("ads") else srcs.get("main")


def copy_music(t, ch, hf, start, total):
    """Copia la pista a hf/assets/audio normalizada a −14 LUFS (así cualquier pista usa la misma ganancia)."""
    src = ch["dir"] / "audio" / "music" / t["file"]
    if not src.exists():
        oslib.die(f"falta el archivo de la pista {src}")
    if t["duration_s"] - start < total - 0.5:
        oslib.die(f"la pista {t['id']} dura {t['duration_s']} s y desde {start} s no cubre los {total} s del video: "
                  "elige otra o ajústala: Epidemic → EditRecording con targetDurationMs; otras → "
                  f"scripts/audio/music.py fit --channel {ch['id']} --track {t['id']} --duration {total + 0.5:g}")
    rel = f"assets/audio/music-{t['id']}.wav"
    oslib.run([oslib.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
               "-af", f"volume={-14 - (t.get('lufs') or -14):.2f}dB", "-ar", "48000", "-ac", "2",
               "-c:a", "pcm_s16le", str(hf / rel)])
    return rel


def audio_markup(sb, ch, caps, total, hf):
    """Música (con ducking bajo la voz) y efectos de sonido del storyboard → AudioPlan (elementos <audio>,
    pistas por plataforma y créditos) + copia de archivos a hf/assets/audio."""
    au = sb.get("audio") or {}
    els, used = [], []
    music_srcs, credits = {}, {"music": {}, "sfx": {}}
    adir = hf / "assets" / "audio"
    if au.get("music"):
        m = au["music"]
        lib_f = ch["dir"] / "audio" / "music" / "library.json"
        lib = {t["id"]: t for t in (oslib.read_json(lib_f)["tracks"] if lib_f.exists() else [])}
        tr = lib.get(m["track"])
        if not tr:
            oslib.die(f"storyboard.audio.music.track «{m['track']}» no está en {oslib.rel(lib_f)} "
                      f"(scripts/audio/music.py list --channel {ch['id']})")
        start = float(m.get("start", 0))
        ads = m.get("ads", "quiza")
        if ads not in ("si", "no", "quiza"):
            oslib.die('storyboard.audio.music.ads debe ser "si", "no" o "quiza"')
        if ads == "si" and not tr.get("ads"):
            oslib.die(f"la pieza lleva publicidad pagada (ads: si) y la licencia de «{tr['id']}» no la cubre: "
                      "usa una pista con ads: true (scripts/audio/music.py list --channel … --ads)")
        ads_tr = None
        if not tr.get("ads"):
            ads_id = m.get("ads_track")
            ads_tr = lib.get(ads_id) if ads_id else next(
                (t for t in lib.values() if t.get("ads") and t["duration_s"] - start >= total - 0.5), None)
            if ads_id and not ads_tr:
                oslib.die(f"storyboard.audio.music.ads_track «{ads_id}» no está en la biblioteca")
            if ads_tr and not ads_tr.get("ads"):
                oslib.die(f"ads_track «{ads_tr['id']}» no tiene licencia para anuncios (ads: false)")
        adir.mkdir(parents=True, exist_ok=True)
        srcs = {"main": copy_music(tr, ch, hf, start, total)}
        srcs["ads"] = srcs["main"] if tr.get("ads") else (copy_music(ads_tr, ch, hf, start, total) if ads_tr else None)
        music_srcs = srcs
        ch_audio = ch["config"].get("audio", {})  # valores por defecto del canal (channel.json → audio)
        level = float(m.get("level_db", ch_audio.get("music_level_db", -20)))
        duck = float(m.get("duck_db", ch_audio.get("music_duck_db", -27)))
        gain = db(level + 14)
        if gain > 3.98:
            gain = 3.98
        lane = duck_lane(speech_intervals(caps), db(duck - level), total)
        auto = {"version": 1, "lanes": [{"target": "volume", "points": lane}]}
        els.append(f'      <audio id="music" class="clip" src="{srcs["main"]}" data-var-src="music_src" data-start="0" '
                   f'data-duration="{total}" data-media-start="{start}" data-volume="{gain:.4f}" '
                   f'data-fade-in="{m.get("fade_in", 1.0)}" data-fade-out="{m.get("fade_out", 2.0)}" '
                   f'data-audio-group="music" data-track-index="40" data-automation="{esc(json.dumps(auto))}"></audio>')
        credits["music"] = {"main": tr, "ads": tr if tr.get("ads") else ads_tr}
        used.append({"music": tr["id"], "ads": ads, "ads_music": srcs["ads"],
                     "gain_db": round(level + 14, 1), "duck_points": len(lane)})
    cues = list(au.get("sfx", []))
    auto_sfx = au.get("sfx_auto") or {}
    kit_json = ch["dir"] / "audio" / "sfx" / "sfx.json"
    entrances = oslib.read_json(kit_json).get("entrances", ["pulse"]) if kit_json.exists() else ["pulse"]
    if auto_sfx.get("scenes"):
        cues += scene_cues(sb.get("scenes", []), auto_sfx["scenes"], auto_sfx.get("db", -20), entrances)
    if auto_sfx.get("overlays"):
        cues += scene_cues(sb.get("overlays", []), auto_sfx["overlays"], auto_sfx.get("db", -20), entrances)
    if auto_sfx.get("exits"):
        cues += exit_cues(sb.get("scenes", []), auto_sfx["exits"],
                          auto_sfx.get("exits_db", auto_sfx.get("db", -20) - 4))
    if cues:
        kit_dir = ch["dir"] / "audio" / "sfx"
        if not (kit_dir / "sfx.json").exists():
            oslib.die(f"el canal no tiene kit de efectos: scripts/audio/sfx.py --channel {ch['id']}")
        kit = oslib.read_json(kit_dir / "sfx.json")["sounds"]
        (adir / "sfx").mkdir(parents=True, exist_ok=True)
        for k, c in enumerate(sorted(cues, key=lambda c: c["at"])):
            if c["sound"] not in kit:
                oslib.die(f"efecto «{c['sound']}» no existe en el kit (disponibles: {sorted(kit)})")
            meta = kit[c["sound"]]
            credits["sfx"][c["sound"]] = meta
            shutil.copy(kit_dir / meta["file"], adir / "sfx" / meta["file"])
            els.append(f'      <audio id="sfx-{k}" class="clip" src="assets/audio/sfx/{meta["file"]}" '
                       f'data-start="{round(c["at"], 3)}" data-duration="{meta["duration_s"]}" '
                       f'data-volume="{db(c.get("db", -20)):.4f}" data-audio-group="sfx" data-track-index="{50 + k}"></audio>')
        used.append({"sfx": len(cues)})
    return AudioPlan("\n".join(els), used, music_srcs, credits)
