"""La placa de video: el master copiado sin recomprimir con la voz (tratada) normalizada a −14 LUFS."""
import json
import subprocess

from scripts.core import oslib


def build_plate(master, out, voice_wav=None):
    """Copia el video sin recomprimir y pone el audio (la voz tratada si hay, si no el del master)
    normalizado a -14 LUFS / -1 dBTP (dos pasadas)."""
    audio_src = voice_wav or master
    if out.exists() and out.stat().st_mtime > max(master.stat().st_mtime, audio_src.stat().st_mtime):
        return
    r = subprocess.run([oslib.FFMPEG, "-hide_banner", "-i", str(audio_src), "-af",
                        "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(txt)
    af = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-i", str(master), "-i", str(audio_src), "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
               "-shortest", str(out)])
