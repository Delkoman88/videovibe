#!/usr/bin/env python3
"""Inventaria el material crudo de una pieza y extrae su audio para análisis.

Uso: scripts/pipeline/ingest.py --project <canal>/<pieza>

Lee <pieza>/raw/ (no lo modifica) y escribe:
  media.json            inventario: orientación, duración, fps, audio y tipo de toma (kind)
  work/audio/<id>.wav   audio mono 16 kHz de cada archivo con audio (lo que transcribe whisper)

Micrófono externo: un archivo solo de audio en raw/ se prueba contra cada toma de cámara
(scripts/audio/audiosync.py). Si se sincroniza con seguridad, queda kind=mic y la toma recibe
"mic": {id, file, offset_s, drift_ppm, covers_s, confidence, source: auto}; su work/audio/<toma>.wav pasa
a ser el micrófono alineado al tiempo de la cámara (el audio original de la cámara queda en
<toma>.cam.wav). Si no, sigue como voz y la salida dice por qué. Un emparejamiento con source=manual se
respeta. apply_cut.py usa el micrófono en el corte.

`kind` se adivina (camara, pantalla, broll, voz, imagen) con kind_source="auto". Si la persona del canal o el agente
lo corrigen (kind_source="manual"), una nueva ingesta lo respeta.
Salida JSON en stdout. Exit 0 ok, 2 error.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
from scripts.audio import audiosync  # noqa: E402
from scripts.audio import audiotools  # noqa: E402
import numpy as np  # noqa: E402

VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".aiff", ".aif", ".ogg"}
IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "archivo"


def describe(path):
    info = oslib.ffprobe(path)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(info.get("format", {}).get("duration") or 0)
    d = {"duration_s": round(dur, 3), "has_audio": a is not None}
    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = rot or int((v.get("tags") or {}).get("rotate", 0) or 0)
        if abs(rot) % 180 == 90:
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        fps = round(float(num) / float(den), 3) if float(den) else 0
        d.update({"width": w, "height": h, "fps": fps, "vcodec": v.get("codec_name"),
                  "color_transfer": v.get("color_transfer"), "hdr": v.get("color_transfer") in oslib.HDR_TRANSFERS,
                  "orientation": "vertical" if h > w else ("horizontal" if w > h else "cuadrado")})
    return d


def guess_kind(ext, d):
    if ext in IMAGE:
        return "imagen"
    if ext in AUDIO or "width" not in d:
        return "voz"
    if not d["has_audio"]:
        return "broll"
    return "camara" if d["orientation"] == "vertical" else "pantalla"


def wav16(path):
    return oslib.load_audio(path, audiosync.SR)


def pair_mics(P, items):
    """Empareja micrófonos externos con tomas de cámara y escribe la pista de análisis de cada toma."""
    adir = P / "work" / "audio"
    cams = [m for m in items if m.get("kind") == "camara" and m.get("has_audio")]
    cands = [m for m in items if m.get("has_audio") and "width" not in m
             and (m.get("kind") == "mic" or m.get("kind_source") != "manual")]
    by_id = {m["id"]: m for m in items}
    report = []
    mic_audio = {m["id"]: wav16(adir / f"{m['id']}.wav") for m in cands}
    for cam in cams:
        cam_a = wav16(adir / f"{cam['id']}.cam.wav")
        best = None
        if cam.get("mic", {}).get("source") == "manual":
            best = cam["mic"]
            if best.get("id") in by_id and best["id"] not in mic_audio:
                mic_audio[best["id"]] = wav16(adir / f"{best['id']}.wav")
        else:
            cam.pop("mic", None)
            for mic in cands:
                r = audiosync.sync(cam_a, mic_audio[mic["id"]])
                report.append({"cam": cam["id"], "mic": mic["id"], **{k: r.get(k) for k in
                               ("paired", "offset_s", "drift_ppm", "confidence", "covers_s", "why")}})
                if r["paired"] and (not best or r["confidence"] > best["confidence"]):
                    best = {"id": mic["id"], "file": mic["file"], "offset_s": r["offset_s"],
                            "drift_ppm": r["drift_ppm"], "covers_s": r["covers_s"],
                            "confidence": r["confidence"], "source": "auto"}
        out = adir / f"{cam['id']}.wav"
        if best and best.get("id") in mic_audio:
            cam["mic"] = best
            aligned = audiosync.align(mic_audio[best["id"]], best, len(cam_a))
            audiotools.write_wav(out, sr=audiosync.SR, x=audiosync.merge(cam_a, aligned, best))
        else:
            audiotools.write_wav(out, sr=audiosync.SR, x=cam_a)
    paired = {c["mic"]["id"] for c in cams if c.get("mic")}
    for m in cands:
        if m["id"] in paired:
            if m.get("kind_source") != "manual":
                m["kind"], m["kind_source"] = "mic", "auto"
            m["pairs"] = [c["id"] for c in cams if c.get("mic", {}).get("id") == m["id"]]
        elif m.get("kind") == "mic" and m.get("kind_source") == "auto":
            m["kind"] = "voz"
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    raw = P / "raw"
    if not raw.is_dir():
        oslib.die(f"falta {raw}. Pon el material crudo ahí.")
    old = {}
    if (P / "media.json").exists():
        old = {m["file"]: m for m in oslib.read_json(P / "media.json").get("items", [])}

    items, used = [], set()
    for f in sorted(raw.iterdir()):
        ext = f.suffix.lower()
        if f.name.startswith(".") or ext not in VIDEO | AUDIO | IMAGE:
            continue
        mid = slug(f.stem)
        while mid in used:
            mid += "-b"
        used.add(mid)
        d = {"id": mid, "file": f"raw/{f.name}"}
        d.update(describe(f) if ext not in IMAGE else {"duration_s": 0, "has_audio": False})
        prev = old.get(d["file"], {})
        if prev.get("kind_source") == "manual":
            d["kind"], d["kind_source"] = prev["kind"], "manual"
        else:
            d["kind"], d["kind_source"] = guess_kind(ext, d), "auto"
        if prev.get("notes"):
            d["notes"] = prev["notes"]
        if prev.get("mic", {}).get("source") == "manual":
            d["mic"] = prev["mic"]
        if d["has_audio"]:
            # audio propio del archivo; en tomas de video va a <id>.cam.wav (el <id>.wav final lo decide el micro)
            own = P / "work" / "audio" / (f"{mid}.cam.wav" if "width" in d else f"{mid}.wav")
            own.parent.mkdir(parents=True, exist_ok=True)
            if not own.exists() or own.stat().st_mtime < f.stat().st_mtime:
                oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", "16000", str(own)])
            d["audio"] = f"work/audio/{mid}.wav"
        items.append(d)

    if not items:
        oslib.die("raw/ no tiene archivos de video, audio o imagen reconocidos.")
    sync_report = pair_mics(P, items)
    oslib.write_json(P / "media.json", {"items": items})
    oslib.update_status(P, "ingesta")
    oslib.emit({"ok": True, "project": str(P), "count": len(items),
                "items": [{k: m.get(k) for k in ("id", "kind", "orientation", "duration_s")} for m in items],
                "mic_sync": sync_report,
                "next": "Confirma `kind` de cada toma (kind_source=auto es una suposición) y corre scripts/pipeline/transcribe.py"})


if __name__ == "__main__":
    main()
