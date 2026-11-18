#!/usr/bin/env python3
"""Golpes de la música en el tiempo del video (`<pieza>/audio/beats.json`), para efectos al ritmo (ADR 0026).

Uso: scripts/pipeline/beats.py --project <canal>/<pieza> [--source music|plate]

- music (por defecto si el storyboard tiene `audio.music.track`): la pista de la biblioteca del canal. Si la
  biblioteca trae su BPM, se usa esa rejilla exacta con la fase que más ataques suma (el detector puede
  engancharse a un pulso de tresillo: 94 en vez de 140 BPM). Se resta `audio.music.start`.
- plate: el audio de la toma (`cut/master-cut.mp4`), para cuando la música suena en la cámara (un DJ en vivo).
El detector es `hyperframes beats <archivo> --json`. Los primeros tiempos de compás (`downbeats`) se eligen
por la energía de los graves. Caché por huella de la fuente. Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import editlib, oslib  # noqa: E402

from scripts.core.beat_selection import pick

HF = ROOT / "node_modules" / ".bin" / "hyperframes"
EVERY = {"beat": 1, "half": 2, "bar": 4, "2bars": 8}


def detect(path):
    """(bpm, [tiempos]) del detector de HyperFrames."""
    d = json.loads(oslib.run([str(HF), "beats", str(path), "--json"]))
    return float(d.get("bpm") or 0), [float(t) for t in d.get("beatTimes", [])]


ENV_N = 1024  # ventana del análisis de ataques (muestras a 16 kHz)
ENV_CENTER = ENV_N / 2 / oslib.SR  # el valor de cada cuadro corresponde al centro de su ventana


def onset_envelope(path):
    """Fuerza de ataque cada 10 ms (flujo espectral positivo), normalizada. El cuadro k mide la ventana que
    empieza en k·10 ms; su tiempo es el centro de esa ventana (ENV_CENTER después)."""
    import numpy as np
    x = oslib.load_audio(path)
    hop, n = oslib.SR // 100, ENV_N
    if len(x) < n:
        return np.zeros(1)
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(np.diff(mag, axis=0), 0).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    return flux / (flux.max() or 1.0)


def grid(bpm, envelope, length):
    """Rejilla exacta a `bpm` con la fase (pasos de 10 ms) que más ataques suma en todo el audio."""
    import numpy as np
    period = 60.0 / bpm
    steps = max(int(round(period * 100)), 1)
    best, phase = -1.0, 0.0
    for k in range(steps):
        idx = np.round((k / 100 + np.arange(0, length, period) - ENV_CENTER) * 100).astype(int)
        idx = idx[idx >= 0]
        idx = idx[idx < len(envelope)]
        score = float(envelope[idx].sum()) if len(idx) else 0.0
        if score > best:
            best, phase = score, k / 100
    n = int((length - phase) / period) + 1
    return [round(phase + k * period, 3) for k in range(n)]


def downbeat_phase(audio_path, beats, offset=0.0):
    """0–3: qué golpe de cada grupo de cuatro tiene más graves (≈ primer tiempo del compás)."""
    import numpy as np
    x = oslib.load_audio(audio_path)  # mono 16 kHz
    sr = oslib.SR
    win = int(0.06 * sr)
    energy = []
    for t in beats:
        i = int((t + offset) * sr)
        seg = x[max(i - win // 4, 0): i + win]
        if len(seg) < 64:
            energy.append(0.0)
            continue
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / sr)
        energy.append(float(spec[freqs < 160].sum()))
    sums = [sum(energy[p::4]) for p in range(4)]
    return int(max(range(4), key=lambda p: sums[p])) if beats else 0


def _source(P, sb, ch, source):
    m = (sb.get("audio") or {}).get("music") or {}
    source = source or ("music" if m.get("track") else "plate")
    if source == "music":
        lib_f = ch["dir"] / "audio" / "music" / "library.json"
        lib = {t["id"]: t for t in oslib.read_json(lib_f)["tracks"]} if lib_f.exists() else {}
        tr = lib.get(m.get("track"))
        if not tr:
            oslib.die("beats --source music: el storyboard no tiene una pista de la biblioteca (audio.music.track)")
        f = ch["dir"] / "audio" / "music" / tr["file"]
        return source, f, float(m.get("start", 0)), tr.get("bpm"), tr["id"]
    return source, P / "cut" / "master-cut.mp4", 0.0, None, None


def ensure(P, sb, ch=None, source=None):
    """beats.json de la pieza (calculado o de caché)."""
    P = Path(P)
    ch = ch or oslib.load_channel(P)
    src, f, start, lib_bpm, track = _source(P, sb, ch, source)
    if not f.exists():
        oslib.die(f"falta {f} para detectar los golpes")
    total = oslib.read_json(P / "cut" / "cut-map.json")["duration_s"] + float(sb.get("tail_s", 0))
    st = f.stat()
    key = hashlib.sha1(f"{src}|{f.name}|{st.st_size}|{int(st.st_mtime)}|{start}|{lib_bpm}|{total}|"
                       f"{editlib.cut_fingerprint(P) if src == 'plate' else ''}".encode()).hexdigest()[:14]
    out = P / "audio" / "beats.json"
    if out.exists() and oslib.read_json(out).get("key") == key:
        return oslib.read_json(out)
    det_bpm, det = detect(f)
    if lib_bpm:
        length = max(det[-1] if det else 0, start + total) + 1
        times, used = grid(float(lib_bpm), onset_envelope(f), length), "biblioteca"
    else:
        times, used = det, "detector"
    beats = [round(t - start, 3) for t in times if start - 0.001 <= t <= start + total]
    ph = downbeat_phase(f, beats, start) if beats else 0
    data = {"key": key, "source": src, "track": track, "bpm": round(float(lib_bpm or det_bpm), 2),
            "detector_bpm": round(det_bpm, 2), "grid": used, "beats": beats, "downbeats": beats[ph::4]}
    out.parent.mkdir(parents=True, exist_ok=True)
    oslib.write_json(out, data)
    return data




def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--source", choices=("music", "plate"))
    a = ap.parse_args()
    P = oslib.project_dir(a.project)
    d = ensure(P, oslib.read_json(P / "storyboard.json"), source=a.source)
    oslib.emit({"ok": True, "file": str(P / "audio" / "beats.json"), "source": d["source"], "bpm": d["bpm"],
                "detector_bpm": d["detector_bpm"], "grid": d["grid"], "beats": len(d["beats"]),
                "downbeats": len(d["downbeats"]), "first": d["beats"][:8]})


if __name__ == "__main__":
    main()
