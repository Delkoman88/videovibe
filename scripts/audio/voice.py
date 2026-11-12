#!/usr/bin/env python3
"""Tratamiento de voz automático: mide la grabación y aplica solo lo que haga falta.

Uso: scripts/audio/voice.py --project <canal>/<pieza> [--compare] [--force]

Cadena (en orden), cada paso decidido por medición:
  1. highpass 80 Hz                 retumbe y graves inútiles (siempre)
  2. afftdn                         ruido de fondo, según piso de ruido y SNR (se salta si la voz ya está limpia)
  3. equalizer (≤ 3 bandas, ±3/4 dB) barro 200–350 Hz, presencia 2.5–5 kHz, aire 8–12 kHz vs. curva de referencia
  4. deesser                        «s» silbantes, según energía 5–9 kHz en los picos
  5. acompressor                    emparejar volumen (umbral = nivel medio de la voz − 6 dB)
El volumen final (−14 LUFS) lo pone compose.py (build_plate). Nunca cambia tono, timbre ni duración.

Configuración (pieza > canal > motor): channel.json → voice y storyboard.json → voice:
  {"enabled": true, "strength": "natural"|"fuerte", "denoise": true, "eq": true, "deess": true, "compress": true}

Escribe cut/master-voice.wav y cut/voice-report.json (medidas y porqué de cada paso).
--compare: renders/voz-antes-despues.wav (4 pares original → tratado, igualados en volumen).
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

VERSION = 1
SR = 48000
DEFAULTS = {"enabled": True, "strength": "natural", "denoise": True, "eq": True, "deess": True, "compress": True}
LIMITS = {"natural": {"eq_db": 3.0, "nr_max": 12.0, "ratio": 2.5, "deess_max": 0.35, "expand_db": 10.0},
          "fuerte": {"eq_db": 4.0, "nr_max": 18.0, "ratio": 3.5, "deess_max": 0.5, "expand_db": 14.0}}
# Nivel típico de cada banda respecto a 500–1000 Hz en voz hablada (aprox. LTASS), en dB.
REF = {"mud": (200, 350, 1.0), "presence": (2500, 5000, -13.0), "air": (8000, 12000, -24.0)}


def config(P, ch_cfg=None, sb=None):
    """Configuración efectiva: motor < canal < pieza."""
    if ch_cfg is None:
        ch_cfg = oslib.read_json(oslib.channel_dir(P) / "channel.json") if (oslib.channel_dir(P) / "channel.json").exists() else {}
    if sb is None:
        f = P / "storyboard.json"
        sb = oslib.read_json(f) if f.exists() else {}
    cfg = dict(DEFAULTS)
    cfg.update(ch_cfg.get("voice") or {})
    cfg.update(sb.get("voice") or {})
    if cfg["strength"] not in LIMITS:
        oslib.die('voice.strength debe ser "natural" o "fuerte"')
    return cfg


def band_db(spec, freqs, lo, hi):
    import numpy as np
    m = (freqs >= lo) & (freqs < hi)
    return 10 * np.log10(np.mean(spec[m]) + 1e-20)


def analyze(audio, sr=SR):
    """Medidas de la voz: piso de ruido, nivel, SNR, espectro relativo y sibilancia."""
    import numpy as np
    hop = 0.01
    db = oslib.rms_db(audio, sr, hop)
    islands, _ = oslib.speech_islands(audio, sr, hop)
    speech = np.zeros(len(db), bool)
    for a, b in islands:
        speech[int(a / hop):int(b / hop)] = True
    quiet = ~speech
    # piso de ruido: lo más bajo de los cuadros sin voz (los demás son respiraciones y colas de voz,
    # que no son ruido y no se deben quitar); si casi no hay silencios, el percentil 2 de todo
    noise_db = float(np.percentile(db[quiet], 10)) if quiet.sum() > 50 else float(np.percentile(db, 2))
    speech_db = float(np.median(db[speech])) if speech.any() else float(np.median(db))
    # espectro promedio de los tramos con voz (ventanas de 4096 con Hann)
    n = 4096
    win = np.hanning(n)
    acc, frames, hf_ratio = None, 0, []
    for a, b in islands:
        s, e = int(a * sr), int(b * sr)
        for i in range(s, e - n, n // 2):
            X = np.abs(np.fft.rfft(audio[i:i + n] * win)) ** 2
            acc = X if acc is None else acc + X
            frames += 1
    freqs = np.fft.rfftfreq(n, 1 / sr)
    bands = {}
    if frames:
        spec = acc / frames
        ref = band_db(spec, freqs, 500, 1000)
        bands = {k: round(band_db(spec, freqs, lo, hi) - ref, 1) for k, (lo, hi, _) in REF.items()}
        # sibilancia: pico (p98) de la banda 5–9 kHz frente a la energía típica (mediana) de la voz
        m = 1024
        w = np.hanning(m)
        fr = np.fft.rfftfreq(m, 1 / sr)
        sib = (fr >= 5000) & (fr < 9000)
        tot_l = []
        for a, b in islands:
            s, e = int(a * sr), int(b * sr)
            for i in range(s, e - m, m):
                X = np.abs(np.fft.rfft(audio[i:i + m] * w)) ** 2
                hf_ratio.append(10 * np.log10(X[sib].sum() + 1e-20))
                tot_l.append(10 * np.log10(X.sum() + 1e-20))
    sib_db = float(np.percentile(hf_ratio, 98) - np.median(tot_l)) if hf_ratio else -40.0
    return {"noise_db": round(noise_db, 1), "speech_db": round(speech_db, 1),
            "snr_db": round(speech_db - noise_db, 1), "bands_rel_db": bands,
            "sibilance_p98_db": round(sib_db, 1), "speech_s": round(sum(b - a for a, b in islands), 1)}


def choose_chain(m, cfg):
    """Cadena de filtros ffmpeg y el porqué de cada paso, a partir de las medidas."""
    lim = LIMITS[cfg["strength"]]
    steps = [{"step": "highpass", "filter": "highpass=f=80:p=2", "why": "quitar retumbe < 80 Hz (siempre)"}]
    snr = m["snr_db"]
    if cfg["denoise"] and snr < 45:
        nr = max(6.0, min(lim["nr_max"], 6 + (40 - snr) * 0.4))
        nf = max(-80.0, min(-20.0, m["noise_db"]))
        steps.append({"step": "denoise", "filter": f"afftdn=nr={nr:.1f}:nf={nf:.1f}:tn=1",
                      "why": f"SNR {snr} dB, piso de ruido {m['noise_db']} dBFS → reducir {nr:.1f} dB"})
    else:
        steps.append({"step": "denoise", "filter": None,
                      "why": "desactivado" if not cfg["denoise"] else f"voz limpia (SNR {snr} dB): no se toca"})
    if cfg["eq"] and m["bands_rel_db"]:
        b, cap = m["bands_rel_db"], lim["eq_db"]
        eqs = []
        excess = b["mud"] - REF["mud"][2]
        if excess > 2:
            g = -min(cap, round(excess - 1, 1))
            eqs.append((f"equalizer=f=280:t=q:w=1.0:g={g}", f"barro +{excess:.1f} dB sobre lo típico → {g} dB a 280 Hz"))
        deficit = REF["presence"][2] - b["presence"]
        if deficit > 2:
            g = min(cap, round(deficit - 1, 1))
            eqs.append((f"equalizer=f=3500:t=q:w=0.9:g={g}", f"falta presencia ({deficit:.1f} dB) → +{g} dB a 3.5 kHz"))
        deficit = REF["air"][2] - b["air"]
        if deficit > 3 and snr > 30:
            g = min(cap * 0.6, round(deficit - 2, 1))
            eqs.append((f"treble=g={g:.1f}:f=10000:t=s:w=0.5", f"falta aire ({deficit:.1f} dB) → +{g:.1f} dB desde 10 kHz"))
        for f, why in eqs:
            steps.append({"step": "eq", "filter": f, "why": why})
        if not eqs:
            steps.append({"step": "eq", "filter": None, "why": "balance tonal dentro de lo típico: no se toca"})
    if cfg["deess"]:
        sib = m["sibilance_p98_db"]
        i = max(0.0, min(lim["deess_max"], (sib + 10) / 16))
        if i >= 0.05:
            steps.append({"step": "deess", "filter": f"deesser=i={i:.2f}:m=0.5:f=0.5:s=o",
                          "why": f"picos de «s» a {sib} dB de la voz típica → intensidad {i:.2f}"})
        else:
            steps.append({"step": "deess", "filter": None, "why": f"sin «s» excesivas ({sib} dB)"})
    if cfg["compress"]:
        thr_db = m["speech_db"] - 6
        thr = max(0.001, min(1.0, 10 ** (thr_db / 20)))
        steps.append({"step": "compress",
                      "filter": f"acompressor=threshold={thr:.5f}:ratio={lim['ratio']}:attack=10:release=150:knee=4:detection=rms",
                      "why": f"voz media {m['speech_db']} dBFS → umbral {thr_db:.1f} dBFS, ratio {lim['ratio']}"})
    return steps


def expander_step(m, cfg):
    """Expansor (agate en modo suave): baja las pausas hasta `expand_db` sin cortar palabras suaves."""
    rng_db = LIMITS[cfg["strength"]]["expand_db"]
    thr_db = max(m["speech_db"] - 24, m["noise_db"] + 10)  # pausas debajo; palabras suaves (≈ voz −15 dB) encima
    thr = max(0.0001, min(1.0, 10 ** (thr_db / 20)))
    return {"step": "expand",
            "filter": f"agate=threshold={thr:.5f}:ratio=3:range={10 ** (-rng_db / 20):.4f}:attack=5:release=80:knee=3",
            "why": f"tras comprimir, pausas a {m['noise_db']} dBFS → bajarlas hasta {rng_db:.0f} dB bajo un umbral de {thr_db:.1f} dBFS"}


def cfg_hash(cfg, src):
    st = src.stat()
    return hashlib.sha1(json.dumps([VERSION, cfg, st.st_size, int(st.st_mtime)], sort_keys=True).encode()).hexdigest()[:16]


def process(src, out, chain, channels):
    filt = ",".join(s["filter"] for s in chain if s["filter"])
    oslib.run([oslib.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn",
               "-af", filt, "-ar", str(SR), "-ac", str(channels), "-c:a", "pcm_s24le", str(out)])


def n_samples(path):
    info = oslib.ffprobe(path)
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    return float(a.get("duration") or info["format"]["duration"]), int(a.get("channels", 1))


def compare(P, src, out, dst, islands, duration):
    """4 pares original → tratado de ~6 s, igualados en volumen de voz (que no gane «el más fuerte»)."""
    import numpy as np
    a, b = oslib.load_audio(src, SR), oslib.load_audio(out, SR)
    beep_t = np.arange(int(0.12 * SR)) / SR
    beep = 0.08 * np.sin(2 * np.pi * 1000 * beep_t) * np.hanning(len(beep_t))
    gap = np.zeros(int(0.35 * SR))
    parts, pairs = [], []
    for frac in (0.15, 0.38, 0.6, 0.82):
        t0 = min(max(0.0, duration * frac), max(0.0, duration - 6.0))
        s, e = int(t0 * SR), int((t0 + 6.0) * SR)
        x, y = a[s:e], b[s:e]
        rx, ry = np.sqrt(np.mean(x ** 2) + 1e-12), np.sqrt(np.mean(y ** 2) + 1e-12)
        target = 10 ** (-23 / 20)
        parts += [x * target / rx, gap, beep, gap, y * target / ry, np.zeros(int(1.0 * SR))]
        pairs.append(round(t0, 1))
    mix = np.concatenate(parts)
    mix = mix / max(1.0, np.max(np.abs(mix)) / 0.89)
    import wave
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((mix * 32767).astype("<i2").tobytes())
    return pairs


def ensure_voice(P, cfg=None, force=False, do_compare=False):
    """Genera (o reutiliza si está al día) cut/master-voice.wav. Devuelve (ruta | None, informe)."""
    oslib.ensure_venv()
    cfg = cfg or config(P)
    src = P / "cut" / "master-cut.mp4"
    if not src.exists():
        oslib.die("falta cut/master-cut.mp4 (apply_cut.py)")
    rep_f, out = P / "cut" / "voice-report.json", P / "cut" / "master-voice.wav"
    if not cfg["enabled"]:
        rep = {"enabled": False, "config": cfg}
        oslib.write_json(rep_f, rep)
        return None, rep
    h = cfg_hash(cfg, src)
    if not force and out.exists() and rep_f.exists() and oslib.read_json(rep_f).get("hash") == h and not do_compare:
        return out, oslib.read_json(rep_f)
    dur, ch = n_samples(src)
    audio = oslib.load_audio(src, SR)
    m = analyze(audio)
    chain = choose_chain(m, cfg)
    process(src, out, chain, ch)
    after = analyze(oslib.load_audio(out, SR))
    if cfg["compress"]:  # 2.ª pasada: expansor suave para que el compresor no suba el fondo en las pausas
        chain.append(expander_step(after, cfg))
        process(src, out, chain, ch)
        after = analyze(oslib.load_audio(out, SR))
    dur_out, _ = n_samples(out)
    if abs(dur_out - dur) > 0.002:
        oslib.die(f"la voz tratada dura {dur_out} s y el master {dur} s: no se usa (sincronía de labios)")
    rep = {"enabled": True, "version": VERSION, "hash": h, "config": cfg, "before": m,
           "after": {k: after[k] for k in ("noise_db", "speech_db", "snr_db", "bands_rel_db", "sibilance_p98_db")},
           "chain": chain}
    if do_compare:
        islands, _ = oslib.speech_islands(audio, SR)
        dst = P / "renders" / "voz-antes-despues.wav"
        rep["compare"] = {"file": str(dst.relative_to(P)), "pairs_at_s": compare(P, src, out, dst, islands, dur),
                          "order": "en cada par: original → bip → tratado (mismo volumen)"}
    oslib.write_json(rep_f, rep)
    return out, rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    out, rep = ensure_voice(P, force=args.force, do_compare=args.compare)
    oslib.emit({"ok": True, "file": str(out.relative_to(P)) if out else None,
                **{k: rep.get(k) for k in ("enabled", "before", "after", "chain", "compare") if k in rep}})


if __name__ == "__main__":
    main()
