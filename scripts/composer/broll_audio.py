"""Audio original de insertos; mismo intervalo que la imagen, sin pasar por el kit SFX."""
import hashlib
import json
import math
import os
from scripts.core import oslib
from scripts.composer.visual import esc


def settings(clip):
    a = clip.get('audio', {})
    if not isinstance(a, dict):
        raise ValueError('audio debe ser un objeto')
    if set(a) - {'enabled', 'gain_db', 'duck_db', 'fade_in', 'fade_out'}:
        raise ValueError('audio contiene claves desconocidas')
    if not isinstance(a.get('enabled', False), bool):
        raise ValueError('audio.enabled debe ser booleano')
    if any(not math.isfinite(clip[k]) for k in ('in', 'out')):
        raise ValueError('audio: tiempos finitos obligatorios')
    d = clip['out'] - clip['in']
    v = {'gain_db': -8, 'duck_db': -12, 'fade_in': .08, 'fade_out': .25, **a}
    for k in ('gain_db', 'duck_db', 'fade_in', 'fade_out'):
        if isinstance(v[k], bool) or not isinstance(v[k], (int, float)) or not math.isfinite(v[k]):
            raise ValueError(f'audio.{k}: número finito obligatorio')
    if not -60 <= v['gain_db'] <= 12 or not -60 <= v['duck_db'] <= 0:
        raise ValueError('audio: gain_db entre -60 y 12; duck_db entre -60 y 0')
    if min(v['fade_in'], v['fade_out']) < 0:
        raise ValueError('audio: fundidos no negativos')
    explicit = sum(v[k] for k in ('fade_in', 'fade_out') if k in a)
    if explicit > d:
        raise ValueError('audio: fundidos explícitos exceden el inserto')
    defaults = [k for k in ('fade_in', 'fade_out') if k not in a]
    weight = sum(v[k] for k in defaults)
    if weight:
        scale = min(1, max(0, d - explicit) / weight)
        for k in defaults:
            v[k] *= scale
    return v


def markup(P, sb, media, caps, hf):
    from scripts.composer.audio import speech_intervals, duck_lane, db
    folder = hf / 'assets' / 'broll-audio'
    elements, keep = [], set()
    for clip in sb.get('broll', []):
        cfg = settings(clip)
        if not cfg.get('enabled', False):
            continue
        src = P / media[clip['source']]['file']
        duration = clip['out'] - clip['in']
        start = clip.get('source_in', 0)
        probe = oslib.ffprobe(src)
        stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        if stream is None:
            raise ValueError(f"B-roll {clip['id']}: fuente sin audio")
        end = float(stream.get('start_time', 0)) + float(stream.get('duration', probe['format']['duration']))
        if start + duration > end + .001:
            raise ValueError(f"B-roll {clip['id']}: audio insuficiente para el intervalo")
        h = hashlib.sha256()
        with src.open('rb') as f:
            for block in iter(lambda: f.read(1048576), b''):
                h.update(block)
        h.update(json.dumps([1, start, duration, cfg], sort_keys=True).encode())
        name = f"{clip['id']}-{h.hexdigest()[:20]}.wav"
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / name
        keep.add(name)
        if not out.exists():
            temp = out.with_suffix('.tmp.wav')
            # atrim conserva silencios internos; aresample conserva el origen de flujos tardíos.
            filters = (f"aresample=48000:async=1:first_pts=0,atrim=start={start}:duration={duration},"
                       f"asetpts=PTS-STARTPTS,afade=t=in:d={cfg['fade_in']},"
                       f"afade=t=out:st={duration-cfg['fade_out']}:d={cfg['fade_out']}")
            try:
                oslib.run([oslib.FFMPEG, '-y', '-v', 'error', '-i', str(src), '-map', '0:a:0',
                           '-af', filters, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(temp)])
                if abs(float(oslib.ffprobe(temp)['format']['duration']) - duration) > 1/48000 + .000001:
                    raise ValueError(f"B-roll {clip['id']}: extracción de audio incompleta")
                os.replace(temp, out)
            finally:
                temp.unlink(missing_ok=True)
        spans = [(max(a, clip['in'])-clip['in'], min(b, clip['out'])-clip['in'])
                 for a, b in speech_intervals(caps) if a < clip['out'] and b > clip['in']]
        if len(spans) > 120:
            raise ValueError('B-roll: demasiados intervalos de voz para la automatización')
        lane = duck_lane(spans, db(cfg['duck_db']), duration)
        auto = esc(json.dumps({'version': 1, 'lanes': [{'target': 'volume', 'points': lane}]}))
        elements.append(f'<audio id="broll-audio-{clip["id"]}" class="clip" src="assets/broll-audio/{name}" '
                        f'data-start="{clip["in"]}" data-duration="{duration}" data-media-start="0" '
                        f'data-volume="{db(cfg["gain_db"]):.6f}" data-audio-group="broll" '
                        f'data-track-index="45" data-automation="{auto}"></audio>')
    if folder.exists():
        for old in folder.glob('*.wav'):
            if old.name not in keep:
                old.unlink()
    return '\n'.join(elements)
