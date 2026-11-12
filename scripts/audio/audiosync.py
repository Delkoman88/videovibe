from pathlib import Path
import sys
"""Sincroniza el audio de un micrófono externo con el de una toma de cámara (lógica pura, numpy).

Convención: el instante t de la cámara corresponde a t + offset(t) en el micrófono, con
offset(t) = offset_s + drift_ppm·1e-6·t (la deriva corrige relojes que no van exactamente igual).

1. Gruesa: correlación de envolventes (100 Hz) en todo el largo; funciona si el micrófono empieza antes,
   termina después o cubre varias tomas.
2. Fina: GCC-PHAT sobre la onda (16 kHz, ±60 ms) en varias ventanas con voz; precisión < 1 ms.
3. Deriva: ajuste lineal de los desfases por ventana.
4. Confianza: el emparejamiento solo se acepta si todo concuerda. Ante la duda NO se usa el micrófono
   (los labios deben quedar en sincronía).
"""
import numpy as np

SR = 16000
ENV_RATE = 100
MIN_WINDOWS = 4
SHARP_MIN = 4.5  # z robusto medio mínimo de las ventanas que coinciden
CAND_MIN = 4.0   # z mínimo para que una ventana cuente como candidata


def envelope(x, sr=SR, rate=ENV_RATE):
    hop = sr // rate
    n = len(x) // hop
    if n == 0:
        return np.zeros(1)
    e = np.log(np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-5)
    k = rate  # quita la tendencia lenta (1 s): quedan las sílabas
    trend = np.convolve(e, np.ones(k) / k, mode="same")
    d = e - trend
    return (d - d.mean()) / (d.std() + 1e-9)


def _xcorr(a, b):
    """c[L] = Σ a[i]·b[i+L] para L en [-(len(a)-1), len(b)-1], por FFT. Devuelve (c, lags)."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.conj(np.fft.rfft(a, n)) * np.fft.rfft(b, n), n)
    c = np.concatenate([c[-(len(a) - 1):], c[: len(b)]]) if len(a) > 1 else c[: len(b)]
    return c, np.arange(-(len(a) - 1), len(b))


def coarse(cam, mic, sr=SR):
    """Desfase aproximado (s) y medidas de calidad de la correlación de envolventes."""
    ec, em = envelope(cam, sr), envelope(mic, sr)
    c, lags = _xcorr(ec, em)
    # normaliza por solape: evita que los bordes ganen por tener menos muestras
    ov = np.minimum(len(ec), len(em) - lags) - np.maximum(0, -lags)
    ov = np.maximum(ov, 1)
    valid = ov >= 0.6 * len(ec) if len(em) >= len(ec) else ov >= 0.6 * len(em)
    r = np.where(valid, c / ov, -np.inf)
    i = int(np.argmax(r))
    best = r[i]
    guard = ENV_RATE // 2
    r2 = r.copy()
    r2[max(0, i - guard): i + guard + 1] = -np.inf
    second = np.max(r2) if np.isfinite(r2).any() else 0.0
    return {"offset_s": lags[i] / ENV_RATE, "corr": float(best), "peak_ratio": float(best / max(second, 1e-3))}


def gcc_phat(c, m):
    """Mejor desplazamiento k (muestras) de c dentro de m (len(m) > len(c)) y nitidez del pico."""
    n = 1 << int(np.ceil(np.log2(len(c) + len(m))))
    R = np.fft.rfft(m, n) * np.conj(np.fft.rfft(c, n))
    R /= np.abs(R) + 1e-12
    cc = np.fft.irfft(R, n)[: len(m) - len(c) + 1]
    k = int(np.argmax(cc))
    frac = 0.0
    if 0 < k < len(cc) - 1:
        y0, y1, y2 = cc[k - 1], cc[k], cc[k + 1]
        frac = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
    med = np.median(cc)
    mad = np.median(np.abs(cc - med)) * 1.4826 + 1e-12
    sharp = float((cc[k] - med) / mad)  # z robusto del pico (con eco hay picos secundarios: no usar 2.º pico)
    return k + frac, sharp


def fine(cam, mic, off0, sr=SR, n_windows=12, win_s=3.0, search_s=0.06):
    """Desfases precisos en ventanas con voz. Devuelve lista de (t_cam_centro, offset_s, nitidez)."""
    W, M = int(win_s * sr), int(search_s * sr)
    dur = len(cam) / sr
    if dur < win_s + 0.5:
        return []
    hop = int(0.1 * sr)
    energy = np.array([np.sqrt(np.mean(cam[i:i + W] ** 2)) for i in range(0, len(cam) - W, hop)])
    out = []
    for frac in np.linspace(0.05, 0.95, n_windows * 3):
        i = int(frac * (len(energy) - 1))
        j0 = max(0, i - 5)
        seg = energy[j0: j0 + 11]
        j = j0 + int(np.argmax(seg)) if len(seg) else i  # alrededor de ese punto, la ventana con más voz
        if energy[min(j, len(energy) - 1)] < 0.3 * np.percentile(energy, 90):
            continue
        s = j * hop
        ms = s + int(round(off0 * sr)) - M
        if ms < 0 or ms + W + 2 * M > len(mic):
            continue
        k, sharp = gcc_phat(cam[s:s + W], mic[ms:ms + W + 2 * M])
        out.append((round((s + W / 2) / sr, 3), off0 + (k - M) / sr, sharp))
    # sin duplicados (ventanas que cayeron en el mismo sitio)
    seen, uniq = set(), []
    for t, o, sh in sorted(out):
        if round(t, 1) not in seen:
            seen.add(round(t, 1))
            uniq.append((t, o, sh))
    if len(uniq) > n_windows:  # repartidas por toda la toma (para medir la deriva)
        idx = np.linspace(0, len(uniq) - 1, n_windows).round().astype(int)
        uniq = [uniq[i] for i in sorted(set(idx))]
    return uniq


def consensus(cand, tol=0.003, max_ppm=500):
    """Mayor grupo de ventanas que coinciden con una recta offset(t) = icpt + slope·t (±tol s).
    Los picos de reflexiones (eco) quedan fuera como puntos sueltos. None si no hay ≥ MIN_WINDOWS."""
    best = None
    n = len(cand)
    pairs = [(i, j) for i in range(n) for j in range(i, n)]
    for i, j in pairs:
        ti, oi, _ = cand[i]
        tj, oj, _ = cand[j]
        slope = 0.0 if i == j or abs(tj - ti) < 1e-6 else (oj - oi) / (tj - ti)
        if abs(slope) > max_ppm * 1e-6:
            continue
        icpt = oi - slope * ti
        inl = [k for k, (t, o, _) in enumerate(cand) if abs(o - (icpt + slope * t)) <= tol]
        score = (len(inl), sum(cand[k][2] for k in inl))
        if not best or score > best[0]:
            best = (score, inl)
    if not best or len(best[1]) < MIN_WINDOWS:
        return None
    inl = best[1]
    t = np.array([cand[k][0] for k in inl])
    o = np.array([cand[k][1] for k in inl])
    slope, icpt = np.polyfit(t, o, 1) if np.ptp(t) > 5 else (0.0, float(np.median(o)))
    return float(slope), float(icpt), inl


def sync(cam, mic, sr=SR):
    """Empareja una toma con un micrófono. Devuelve dict con paired, offset_s, drift_ppm, confidence, why."""
    res = {"paired": False}
    if len(cam) < 2 * sr or len(mic) < 2 * sr:
        return {**res, "why": "audio demasiado corto para sincronizar"}
    c = coarse(cam, mic, sr)
    res.update({"coarse_offset_s": round(c["offset_s"], 3), "coarse_corr": round(c["corr"], 3),
                "peak_ratio": round(c["peak_ratio"], 2)})
    if c["corr"] < 0.25 or c["peak_ratio"] < 1.3:
        return {**res, "why": f"no se parecen (correlación {c['corr']:.2f}, pico {c['peak_ratio']:.2f})"}
    w = fine(cam, mic, c["offset_s"], sr)
    cand = [(t, o, sh) for t, o, sh in w if sh > CAND_MIN]
    line = consensus(cand)
    if line is None:
        return {**res, "why": f"solo {len(cand)} ventanas medibles y sin acuerdo entre ellas (mínimo {MIN_WINDOWS})"}
    slope, icpt, inl = line
    t = np.array([cand[i][0] for i in inl])
    o = np.array([cand[i][1] for i in inl])
    mean_sharp = float(np.mean([cand[i][2] for i in inl]))
    if mean_sharp < SHARP_MIN:
        return {**res, "why": f"sincronía poco nítida (z medio {mean_sharp:.1f} < {SHARP_MIN})"}
    resid_ms = float(np.std(o - (icpt + slope * t)) * 1000)
    keep = np.ones(len(t), bool)
    dur = len(cam) / sr
    drift_ms = abs(slope) * dur * 1000
    if drift_ms < 1.0:
        slope, icpt = 0.0, float(np.median(o))
    # tramo de la toma que el micrófono cubre (puede haber empezado tarde o terminado antes)
    cover_a = max(0.0, -icpt / (1 + slope))
    cover_b = min(dur, (len(mic) / sr - icpt) / (1 + slope))
    if cover_b - cover_a < 0.5 * dur:
        return {**res, "offset_s": round(float(icpt), 4),
                "why": f"el micrófono solo cubre {max(0, cover_b - cover_a):.1f} de {dur:.1f} s de la toma"}
    agree = len(inl) / max(len(cand), 1)
    conf = float(np.clip(min(c["corr"] / 0.5, c["peak_ratio"] / 2.0, len(inl) / 6, 2.0 / max(resid_ms, 0.5),
                             agree / 0.5), 0, 1))
    return {**res, "paired": conf >= 0.6, "offset_s": round(float(icpt), 5),
            "drift_ppm": round(float(slope * 1e6), 1), "residual_ms": round(resid_ms, 2),
            "windows": int(keep.sum()), "confidence": round(conf, 2),
            "covers_s": [round(cover_a, 3), round(cover_b, 3)],
            "why": "sincronizado" if conf >= 0.6 else f"confianza baja ({conf:.2f})"}


def offset_at(m, t):
    """Desfase del micrófono en el instante t (s) de la cámara."""
    return m["offset_s"] + m.get("drift_ppm", 0.0) * 1e-6 * t


def align(mic, m, n_out, sr=SR):
    """Audio del micrófono llevado a la línea de tiempo de la cámara (n_out muestras)."""
    t = np.arange(n_out) / sr
    src = (t + m["offset_s"] + m.get("drift_ppm", 0.0) * 1e-6 * t) * sr
    return np.interp(src, np.arange(len(mic)), mic, left=0.0, right=0.0).astype(np.float32)


def covered(m, a, b):
    """¿El tramo [a, b] s de la cámara está dentro de lo que cubre el micrófono?"""
    ca, cb = m.get("covers_s", [0.0, float("inf")])
    return a >= ca + 0.02 and b <= cb - 0.02


def merge(cam, mic_aligned, m, sr=SR, xfade_s=0.02):
    """Pista de análisis en el tiempo de la cámara: micrófono donde cubre, cámara en el resto, con el
    mismo nivel de voz (para la transcripción y las islas de voz)."""
    import numpy as np  # noqa: F811
    out = cam.astype(np.float32).copy()
    ca, cb = m.get("covers_s", [0.0, len(cam) / sr])
    a, b = int(ca * sr), int(min(cb * sr, len(cam)))
    rc = np.sqrt(np.mean(cam[a:b] ** 2) + 1e-12)
    rm = np.sqrt(np.mean(mic_aligned[a:b] ** 2) + 1e-12)
    seg = mic_aligned[a:b] * (rc / rm)
    n = min(int(xfade_s * sr), (b - a) // 4)
    w = np.ones(b - a)
    if n:
        w[:n] = np.linspace(0, 1, n) if a > 0 else 1
        w[-n:] = np.linspace(1, 0, n) if b < len(cam) else 1
    out[a:b] = w * seg + (1 - w) * out[a:b]
    return out


def residual(cam, mic_aligned, a, b, sr=SR):
    """Desfase residual (ms) entre la cámara y el micrófono ya alineado en el tramo [a, b] s.
    None si el tramo no tiene suficiente voz para medirlo."""
    s, e = int(a * sr), int(b * sr)
    M = int(0.06 * sr)
    if e - s < int(0.5 * sr) or s - M < 0 or e + M > len(mic_aligned):
        return None
    k, sharp = gcc_phat(cam[s:e], mic_aligned[s - M:e + M])
    if sharp < SHARP_MIN:
        return None
    return round(float((k - M) / sr * 1000), 2)
