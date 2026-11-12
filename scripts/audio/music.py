#!/usr/bin/env python3
"""Biblioteca de música de un canal: registra pistas con su licencia y ánimo, y las lista.

Uso:
  scripts/audio/music.py add  --channel <id> --file <ruta> --title "…" --source epidemic|propia|… \\
                        [--source-id …] [--artist …] [--url …] [--mood "tenso,ambiental"] [--bpm 100] \\
                        --license "Suscripción Epidemic Sound (cuenta de …)" [--ads]
  scripts/audio/music.py list --channel <id> [--mood ambiental] [--ads]
  scripts/audio/music.py fit  --channel <id> --track <id-pista> --duration 89.5     (versión a la duración exacta)

Música aportada por la persona (comprada, compuesta, de un amigo):
  scripts/audio/music.py add --channel <id> --file <ruta> --title "…" --source usuario --provided-by "<persona>" \
                       --license "Comprada en … (licencia …)" [--ads] [--trim]
  add revisa el archivo (saturación, silencios, calidad) y avisa en "warnings"; --trim quita los silencios
  del inicio y del final; si no se da --bpm, lo estima. fit corta en compás con fundido o repite compases del
  centro con fundido cruzado (equivalente local de EditRecording de Epidemic) y registra <id>-<s>s.

--ads: la licencia permite usar la pista en publicidad pagada (anuncios, posts promocionados). Por
defecto solo las propias (--source propia) lo tienen; el plan personal de Epidemic Sound NO lo cubre
(el plan Pro/Commercial sí: entonces pasa --ads). compose.py usa estas pistas para la plataforma
`ads` (anuncio) y exige una si la pieza lleva pauta (storyboard.audio.music.ads = "si").

`add` copia el archivo a channels/<id>/audio/music/<id-pista>.<ext>, mide duración y volumen integrado
(LUFS, para que compose.py calcule la ganancia exacta) y lo registra en library.json. Los audios
no van a git (licencias); library.json sí. Las pistas de Epidemic Sound se buscan y descargan con su
conector MCP (docs/connectors.md) y luego se registran aquí.
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
from scripts.audio import audiotools  # noqa: E402


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:48] or "pista"


def measure(path):
    info = oslib.ffprobe(path)
    dur = float(info["format"]["duration"])
    r = subprocess.run([oslib.FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r.stderr[r.stderr.rfind("Summary:"):])
    return round(dur, 3), (float(m.group(1)) if m else None)


def library_path(cid):
    return oslib.channel_path(cid) / "audio" / "music" / "library.json"


def load_library(cid):
    f = library_path(cid)
    return oslib.read_json(f) if f.exists() else {"tracks": []}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--channel", required=True)
    a.add_argument("--file", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--source", required=True)
    a.add_argument("--source-id", default="")
    a.add_argument("--artist", default="")
    a.add_argument("--url", default="")
    a.add_argument("--mood", default="")
    a.add_argument("--bpm", type=float)
    a.add_argument("--license", default="")
    a.add_argument("--ads", action="store_true", help="la licencia cubre publicidad pagada")
    a.add_argument("--palette", help="JSON de instrumentos (lo pasa musicgen.py)")
    a.add_argument("--replace", action="store_true", help="reemplaza la pista si ya existe (mismo id)")
    a.add_argument("--provided-by", default="", help="quién aportó el archivo (persona, amigo, proveedor)")
    a.add_argument("--trim", action="store_true", help="quita silencios del inicio y del final")
    a.add_argument("--derived-from", default="", help=argparse.SUPPRESS)
    ft = sub.add_parser("fit")
    ft.add_argument("--channel", required=True)
    ft.add_argument("--track", required=True)
    ft.add_argument("--duration", type=float, required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--channel", required=True)
    ls.add_argument("--mood")
    ls.add_argument("--ads", action="store_true", help="solo pistas aptas para anuncios")
    args = ap.parse_args()

    if not (oslib.channel_path(args.channel) / "channel.json").exists():
        oslib.die(f"no existe el canal {args.channel}")
    lib = load_library(args.channel)

    if args.cmd == "list":
        tracks = lib["tracks"]
        if args.mood:
            tracks = [t for t in tracks if args.mood.lower() in [m.lower() for m in t.get("mood", [])]]
        if args.ads:
            tracks = [t for t in tracks if t.get("ads")]
        oslib.emit({"ok": True, "channel": args.channel, "tracks": tracks})

    if args.cmd == "fit":
        fit(args, lib)

    src = Path(args.file).expanduser()
    if not src.exists():
        oslib.die(f"no existe {src}")
    if not args.license:
        oslib.die("--license es obligatorio: de dónde viene el derecho de uso (regla universal 5)")
    if args.source == "usuario" and not args.provided_by:
        oslib.die("--provided-by es obligatorio con --source usuario (quién aportó el archivo)")
    try:
        meas, warnings, x = audiotools.inspect(src)
    except (ValueError, subprocess.CalledProcessError) as e:
        oslib.die(f"no se puede leer el audio de {src}: {e}")
    tid = slug(f"{args.title}-{args.artist}" if args.artist else args.title)
    if any(t["id"] == tid for t in lib["tracks"]):
        if not args.replace:
            oslib.die(f"ya existe la pista {tid} en la biblioteca (usa --replace para reemplazarla)")
        lib["tracks"] = [t for t in lib["tracks"] if t["id"] != tid]
    mdir = oslib.channel_path(args.channel) / "audio" / "music"
    mdir.mkdir(parents=True, exist_ok=True)
    if args.trim:
        dest = mdir / f"{tid}.wav"
        audiotools.write_wav(dest, audiotools.trim_silence(x, rel_db=-55, keep_s=0.05, fade_s=0.02))
        warnings = [w for w in warnings if "silencio" not in w]
    else:
        dest = mdir / f"{tid}{src.suffix.lower()}"
        shutil.copy(src, dest)
    dur, lufs = measure(dest)
    bpm, bpm_conf = args.bpm, None
    if not bpm:
        bpm, bpm_conf = audiotools.estimate_bpm(x)
        if bpm_conf is not None and bpm_conf < 0.15:
            warnings.append(f"BPM poco claro (≈{bpm}): `fit` cortará con fundidos largos; pasa --bpm si lo sabes")
    entry = {"id": tid, "file": dest.name, "title": args.title, "artist": args.artist, "source": args.source,
             "source_id": args.source_id, "url": args.url,
             "mood": [m.strip() for m in args.mood.split(",") if m.strip()], "bpm": bpm,
             "duration_s": dur, "lufs": lufs, "license": args.license,
             "ads": bool(args.ads or args.source == "propia")}
    if bpm_conf is not None:
        entry["bpm_confidence"] = bpm_conf
    if args.provided_by:
        entry["provided_by"] = args.provided_by
    if args.derived_from:
        entry["derived_from"] = args.derived_from
    if args.palette:
        import json
        entry["palette"] = json.loads(args.palette)
    lib["tracks"].append(entry)
    oslib.write_json(library_path(args.channel), lib)
    oslib.emit({"ok": True, "added": entry, "check": meas, "warnings": warnings})


def fit(args, lib):
    """Versión de una pista a la duración exacta, registrada como pista derivada con la misma licencia."""
    tr = next((t for t in lib["tracks"] if t["id"] == args.track), None)
    if not tr:
        oslib.die(f"no existe la pista {args.track} (scripts/audio/music.py list --channel {args.channel})")
    src = oslib.channel_path(args.channel) / "audio" / "music" / tr["file"]
    if not src.exists():
        oslib.die(f"falta el archivo {src}")
    if not 5 <= args.duration <= 600:
        oslib.die("--duration entre 5 y 600 s")
    x = audiotools.load(src)
    conf = tr.get("bpm_confidence", 1.0 if tr.get("bpm") else 0.0)
    bpm = tr.get("bpm") if conf >= 0.15 else None
    try:
        y, info = audiotools.fit_duration(x, args.duration, bpm)
    except ValueError as e:
        oslib.die(str(e))
    nid = f"{tr['id']}-{args.duration:g}s".replace(".", "-")
    lib["tracks"] = [t for t in lib["tracks"] if t["id"] != nid]
    dest = src.parent / f"{nid}.wav"
    audiotools.write_wav(dest, y)
    dur, lufs = measure(dest)
    entry = {k: v for k, v in tr.items() if k not in ("id", "file", "duration_s", "lufs", "source_id")}
    entry.update({"id": nid, "file": dest.name, "duration_s": dur, "lufs": lufs, "derived_from": tr["id"],
                  "title": f"{tr['title']} ({args.duration:g} s)"})
    lib["tracks"].append(entry)
    oslib.write_json(library_path(args.channel), lib)
    warnings = [] if bpm else ["sin BPM fiable: uniones y final con fundidos de 2 s, sin alinear a compás"]
    oslib.emit({"ok": True, "added": entry, "fit": info, "warnings": warnings})


if __name__ == "__main__":
    main()
