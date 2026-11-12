from pathlib import Path
import sys
"""Utilidades de audio compartidas (numpy), en un solo lugar:
- E/S: load, write_wav.
- Síntesis: pan, env_decay, adsr, noise_band_frac, noise_band_hz, reverb_ir, reverb_short (sfx.py, musicgen.py).
- Análisis y edición: inspect, silence_edges, trim_silence, fades, estimate_bpm, fit_duration (music.py, sfx.py).
Pares con nombres distintos (dos ruidos, dos reverbs, dos envolventes) suenan distinto a propósito.
"""
import subprocess
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib

SR = 48000


def load(path, sr=SR, channels=2):
    """Audio float32 (n, channels) a `sr` Hz desde cualquier archivo que lea ffmpeg."""
    raw = subprocess.run([oslib.FFMPEG, "-v", "error", "-i", str(path), "-vn", "-ac", str(channels), "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).astype(np.float64)


def write_wav(path, x, sr=SR, peak_db=None, end_fade=0, stereo=False):
    """WAV de 16 bits. peak_db: normaliza el pico a ese nivel; end_fade: muestras de fundido final
    (evita clics); stereo: duplica una señal mono en dos canales. Sin opciones: recorta a ±1."""
    x = np.asarray(x, dtype=float)
    if peak_db is not None:
        x = x / (np.max(np.abs(x)) + 1e-9) * (10 ** (peak_db / 20))
    if end_fade:
        fade = min(end_fade, len(x) // 4)
        ramp = np.linspace(1, 0, fade)
        x[-fade:] *= ramp if x.ndim == 1 else ramp[:, None]
    if stereo and x.ndim == 1:
        x = np.stack([x, x], axis=1)
    x = x[:, None] if x.ndim == 1 else x
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(x.shape[1])
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ síntesis (sfx.py, musicgen.py)

def pan(sig, pos):
    """Paneo de potencia constante: pos −1 (izquierda) … 1 (derecha), escalar o curva → (n, 2)."""
    a = (np.asarray(pos) + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1)


def env_decay(n, attack=0.004, decay=0.08, sr=SR):
    """Envolvente de ataque lineal y caída exponencial (efectos cortos)."""
    t = np.arange(n) / sr
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def adsr(n, a, r, sr=SR):
    """Envolvente con subida cuadrática de `a` s y caída de `r` s al final (notas sostenidas)."""
    e = np.ones(n)
    na, nr = min(int(a * sr), n), min(int(r * sr), n)
    if na:
        e[:na] = np.linspace(0, 1, na) ** 2
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def noise_band_frac(dur, rng, lo=0.0, hi=1.0, sr=SR):
    """Ruido blanco de `dur` s filtrado por banda con FFT; lo/hi en fracción de Nyquist (sin normalizar)."""
    n = int(sr * dur)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.linspace(0, 1, len(X))
    X[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(X, n)


def noise_band_hz(n, rng, lo, hi, sr=SR):
    """n muestras de ruido blanco filtrado entre lo y hi Hz, normalizado a pico 1."""
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / sr)
    X[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(X, n)
    return x / (np.max(np.abs(x)) + 1e-9)


def reverb_ir(x, rng, seconds=2.4, decay=0.55, lp=6000, sr=SR):
    """Reverb larga (música): convolución con respuesta impulsiva sintética estéreo con predelay."""
    n_ir = int(seconds * sr)
    t = np.arange(n_ir) / sr
    out = np.zeros((len(x) + n_ir - 1, 2))
    for c in range(2):
        ir = noise_band_hz(n_ir, rng, 80, lp, sr) * np.exp(-t / decay)
        ir[: int(0.012 * sr)] = 0  # predelay
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        m = 1 << int(np.ceil(np.log2(len(x) + n_ir)))
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], m) * np.fft.rfft(ir, m), m)[: len(x) + n_ir - 1]
    return out[: len(x)]


def reverb_short(x, rng, amount, sr=SR):
    """Reverb corta (efectos): añade una cola de 0.3–1.5 s según `amount` (0–1) y la mezcla."""
    n = len(x)
    ir_n = int(sr * (0.3 + 1.2 * amount))
    tail = np.zeros((n + ir_n, 2))
    tail[:n] = x
    ir_t = np.arange(ir_n) / sr
    wet = np.zeros_like(tail)
    for c in range(2):
        ir = noise_band_frac(ir_n / sr, rng, 0.004, 0.3, sr) * np.exp(-ir_t / (0.08 + 0.35 * amount))
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        m = 1 << int(np.ceil(np.log2(len(tail) + ir_n)))
        wet[:, c] = np.fft.irfft(np.fft.rfft(tail[:, c], m) * np.fft.rfft(ir, m), m)[:len(tail)]
    out = tail + amount * 0.6 * wet
    fade = int(0.05 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out


def frame_db(x, sr=SR, hop_s=0.01):
    m = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    hop = int(sr * hop_s)
    n = max(1, len(m) // hop)
    rms = np.sqrt(np.mean((m[:n * hop].reshape(n, hop)) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-12)


def silence_edges(x, sr=SR, rel_db=-50.0, hop_s=0.01):
    """(segundos de silencio al inicio, al final), con umbral relativo al pico de energía."""
    db = frame_db(x, sr, hop_s)
    thr = db.max() + rel_db
    on = np.where(db > thr)[0]
    if not len(on):
        return len(db) * hop_s, 0.0
    return on[0] * hop_s, (len(db) - 1 - on[-1]) * hop_s


def inspect(path, sr=SR):
    """Revisión de un archivo aportado: formato, picos, saturación, silencios. Devuelve (medidas, avisos)."""
    info = oslib.ffprobe(path)
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    if not a:
        raise ValueError("el archivo no tiene audio")
    x = load(path, sr)
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    hot = np.abs(x).max(axis=1) >= 0.999
    runs = int(np.sum(hot[2:] & hot[1:-1] & hot[:-2])) if len(hot) > 2 else 0  # ≥ 3 muestras seguidas
    lead, trail = silence_edges(x, sr)
    m = {"sample_rate": int(a.get("sample_rate", 0)), "channels": int(a.get("channels", 0)),
         "codec": a.get("codec_name"), "duration_s": round(len(x) / sr, 3),
         "peak_dbfs": round(20 * np.log10(peak + 1e-12), 2), "clipped_runs": runs,
         "lead_silence_s": round(lead, 2), "trail_silence_s": round(trail, 2)}
    warn = []
    if runs > 10:
        warn.append(f"saturación: {runs} tramos recortados en 0 dBFS (pide una versión sin saturar si existe)")
    if lead > 0.5:
        warn.append(f"{lead:.1f} s de silencio al inicio (--trim lo quita)")
    if trail > 1.0:
        warn.append(f"{trail:.1f} s de silencio al final (--trim lo quita)")
    if m["sample_rate"] and m["sample_rate"] < 44100:
        warn.append(f"frecuencia de muestreo baja ({m['sample_rate']} Hz): calidad limitada")
    if m["codec"] in ("mp3", "aac", "opus", "vorbis") and int(a.get("bit_rate") or 0) and int(a["bit_rate"]) < 192000:
        warn.append(f"compresión fuerte ({int(a['bit_rate']) // 1000} kbps): mejor WAV o ≥ 256 kbps")
    return m, warn, x


def trim_silence(x, sr=SR, rel_db=-50.0, keep_s=0.02, fade_s=0.005):
    lead, trail = silence_edges(x, sr, rel_db)
    a = max(0, int((lead - keep_s) * sr))
    b = len(x) - max(0, int((trail - keep_s) * sr))
    y = x[a:b].copy()
    return fades(y, sr, fade_s, fade_s)


def fades(x, sr, fin, fout):
    y = x.copy()
    ni, no = min(len(y), int(fin * sr)), min(len(y), int(fout * sr))
    if ni:
        y[:ni] *= np.linspace(0, 1, ni)[:, None]
    if no:
        y[-no:] *= np.linspace(1, 0, no)[:, None]
    return y


def estimate_bpm(x, sr=SR, lo=60, hi=180):
    """BPM por autocorrelación de la envolvente de ataques. Devuelve (bpm, confianza 0–1)."""
    mono = x.mean(axis=1) if x.ndim == 2 else x
    hop = int(sr * 0.01)
    n = len(mono) // hop
    if n < 400:
        return None, 0.0
    e = np.log(np.sqrt(np.mean(mono[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-6)
    onset = np.maximum(0, np.diff(e))
    onset -= onset.mean()
    ac = np.correlate(onset, onset, "full")[len(onset) - 1:]
    ac /= ac[0] + 1e-12
    lags = np.arange(int(6000 / hi), int(6000 / lo) + 1)  # lag en cuadros de 10 ms
    vals = ac[lags]
    i = int(np.argmax(vals))
    lag = lags[i]
    # refinamiento parabólico
    if 0 < i < len(vals) - 1:
        y0, y1, y2 = vals[i - 1], vals[i], vals[i + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
        lag = lag + d
    bpm = 6000 / lag
    while bpm < 70:
        bpm *= 2
    while bpm > 150:
        bpm /= 2
    conf = float(np.clip((vals.max() - np.median(vals)) / (1 - np.median(vals) + 1e-9), 0, 1))
    return round(float(bpm), 1), round(conf, 2)


def _xfade(a, b, n):
    """Une a + b con fundido cruzado de igual potencia de n muestras."""
    n = min(n, len(a), len(b))
    if n <= 0:
        return np.concatenate([a, b])
    t = np.linspace(0, np.pi / 2, n)[:, None]
    mid = a[-n:] * np.cos(t) + b[:n] * np.sin(t)
    return np.concatenate([a[:-n], mid, b[n:]])


def fit_duration(x, target_s, bpm=None, sr=SR, end_fade_s=2.0):
    """Ajusta la pista a `target_s` exactos. Más larga: termina en compás con fundido. Más corta: repite
    compases del centro con fundido cruzado de 1 compás. Devuelve (audio, info)."""
    target = int(round(target_s * sr))
    bar = 4 * 60 / bpm if bpm else 2.0
    nbar = int(bar * sr)
    info = {"bar_s": round(bar, 3), "method": None, "repeats": 0}
    y = x
    if len(y) < target:
        info["method"] = "repetir"
        s = int(round(len(x) * 0.25 / nbar)) * nbar
        e = int(round(len(x) * 0.75 / nbar)) * nbar
        if e - s < 2 * nbar:
            s, e = 0, max(nbar, (len(x) // nbar) * nbar)
        region = x[s:e]
        head, tail = x[:e], x[e:]
        while len(head) + len(tail) - nbar < target:
            head = _xfade(head, region, nbar)
            info["repeats"] += 1
            if info["repeats"] > 50:
                raise ValueError("la pista es demasiado corta para alargarla")
        y = _xfade(head, tail, nbar)
    if len(y) > target:
        info["method"] = (info["method"] + "+cortar") if info["method"] else "cortar"
        start_fade = target - int(end_fade_s * sr)
        if bpm:
            start_fade = max(0, (start_fade // nbar) * nbar)  # el fundido empieza en un compás
        y = y[:target].copy()
        k = target - start_fade
        y[start_fade:] *= np.linspace(1, 0, k)[:, None] ** 1.5
    return y[:target], info
