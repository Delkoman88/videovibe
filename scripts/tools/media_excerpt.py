"""Extract a synchronized audiovisual excerpt with natural fades; keep the source intact."""
import argparse
import math
from pathlib import Path
from scripts.core import oslib


def extract(source, start, duration, fade_in, fade_out, video, audio):
    source, video, audio = [Path(p).expanduser().resolve() for p in (source, video, audio)]
    if len({source, video, audio}) != 3:
        raise ValueError('fuente y salidas deben ser diferentes')
    if video.exists() or audio.exists():
        raise ValueError('las salidas ya existen; usa nombres nuevos')
    if any(type(n) not in (int, float) or not math.isfinite(n) for n in (start, duration, fade_in, fade_out)):
        raise ValueError('tiempos no finitos')
    if start < 0 or duration <= 0 or min(fade_in, fade_out) < 0 or fade_in + fade_out > duration:
        raise ValueError('intervalo o fundidos inválidos')
    probe = oslib.ffprobe(source)
    if not {'audio', 'video'} <= {s['codec_type'] for s in probe['streams']}:
        raise ValueError('se requiere video con audio')
    if start + duration > float(probe['format']['duration']):
        raise ValueError('intervalo fuera de la fuente')
    if any(s.get('color_transfer') in oslib.HDR_TRANSFERS for s in probe['streams']):
        raise ValueError('convierte HDR a SDR antes de extraer')
    video.parent.mkdir(parents=True, exist_ok=True)
    audio.parent.mkdir(parents=True, exist_ok=True)
    vf = 'fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1'
    af = 'aresample=48000'
    if fade_in:
        vf += f',fade=t=in:d={fade_in}'
        af += f',afade=t=in:d={fade_in}'
    if fade_out:
        vf += f',fade=t=out:st={duration-fade_out}:d={fade_out}'
        af += f',afade=t=out:st={duration-fade_out}:d={fade_out}'
    oslib.run([oslib.FFMPEG, '-v', 'error', '-n', '-ss', str(start), '-i', str(source),
               '-map', '0:v:0', '-map', '0:a:0', '-t', str(duration), '-vf', vf, '-af', af,
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-colorspace', 'bt709', '-color_trc', 'bt709', '-color_primaries', 'bt709',
               '-c:a', 'aac', '-ar', '48000', '-ac', '2', str(video),
               '-map', '0:a:0', '-t', str(duration), '-af', af, '-c:a', 'pcm_s16le',
               '-ar', '48000', '-ac', '2', str(audio)])
    return {'ok': True, 'source': str(source), 'source_in': start, 'duration_s': duration,
            'fade_in_s': fade_in, 'fade_out_s': fade_out, 'video': str(video), 'audio': str(audio)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True); ap.add_argument('--start', type=float, required=True)
    ap.add_argument('--duration', type=float, required=True)
    ap.add_argument('--fade-in', type=float, default=.08); ap.add_argument('--fade-out', type=float, default=1.2)
    ap.add_argument('--video', required=True); ap.add_argument('--audio', required=True)
    args = ap.parse_args()
    try: oslib.emit(extract(args.source, args.start, args.duration, args.fade_in, args.fade_out, args.video, args.audio))
    except (ValueError, OSError) as error: oslib.die(str(error))


if __name__ == '__main__': main()
