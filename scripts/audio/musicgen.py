#!/usr/bin/env python3
"""Genera música propia para un canal por síntesis (100 % propia: sirve para anuncios, sin reclamos).

Uso:
  scripts/audio/musicgen.py --channel <id> --duration 89.5 --mood esperanzador|misterioso|energico|ambiental \\
                      [--seed 1] [--bpm 100] [--palette '{"pad":"keys"}'] [--out pista.wav] [--add --title "…"]

Electrónica por capas: pad, bajo, arpegio con eco, melodía opcional, percusión, textura y reverb.
Los INSTRUMENTOS salen de la paleta (identidad del canal): ánimo por defecto < brand.json → music <
--palette. Paleta: pad saw|keys|strings|glass · lead pluck|bell|square|none · bass sub|pluck|none ·
drums soft|electronic|halftime|breakbeat|none · melody true|false · swing 0–0.3 · brightness 0–1.
El ÁNIMO decide escala, tempo, progresión y energía. Estructura de canción ajustada a la duración exacta:
intro → desarrollo → clímax → pausa → final (el último acorde suena hasta el final, sin corte).
La tonalidad sale de brand.json → sound.root_hz; `--seed` cambia progresión, arpegio y voces.
Determinista: mismos parámetros → mismo archivo.

--add registra la pista en la biblioteca del canal (scripts/audio/music.py add, source propia → ads: true).
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import math
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
import numpy as np  # noqa: E402

from scripts.audio import audiotools  # noqa: E402

SR = 48000
adsr = audiotools.adsr            # primitivas comunes (scripts/audio/audiotools.py)
pan2 = audiotools.pan
band_noise = audiotools.noise_band_hz
reverb = audiotools.reverb_ir


def write_wav(path, st):
    audiotools.write_wav(path, st, SR)
SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10]}
# Grados (0 = tónica) de progresiones de 4 acordes por ánimo; la semilla elige una.
MOODS = {
    "esperanzador": {"scale": "major", "bpm": 100, "energy": 2, "arp": 8,
                     "progs": [[0, 4, 5, 3], [3, 0, 4, 5], [0, 5, 3, 4]],
                     "palette": {"pad": "keys", "lead": "pluck", "bass": "sub", "drums": "soft", "melody": True}},
    "misterioso": {"scale": "minor", "bpm": 84, "energy": 1, "arp": 8,
                   "progs": [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6]],
                   "palette": {"pad": "strings", "lead": "bell", "bass": "sub", "drums": "halftime", "melody": False}},
    "energico": {"scale": "minor", "bpm": 120, "energy": 3, "arp": 16,
                 "progs": [[0, 5, 2, 6], [0, 5, 3, 4], [5, 6, 0, 0]],
                 "palette": {"pad": "saw", "lead": "square", "bass": "pluck", "drums": "electronic", "melody": True}},
    "ambiental": {"scale": "major", "bpm": 76, "energy": 0, "arp": 8,
                  "progs": [[3, 0, 5, 4], [0, 3, 0, 4], [5, 3, 0, 4]],
                  "palette": {"pad": "glass", "lead": "bell", "bass": "none", "drums": "none", "melody": False}},
}
# Mezcla por energía del ánimo (dB por capa): en los tranquilos manda la atmósfera; en los enérgicos,
# ritmo y bajo. Sin esto el pad tapaba todo y los ánimos sonaban parecido.
MIX_DB = {0: {"pad": -2, "arp": 2, "bass": 0, "drums": 0, "mel": 6, "tex": 10},
          1: {"pad": -4, "arp": 1, "bass": 1, "drums": 2, "mel": 8, "tex": 8},
          2: {"pad": -6, "arp": 1, "bass": 2, "drums": 3, "mel": 9, "tex": 6},
          3: {"pad": -9, "arp": 2, "bass": 4, "drums": 5, "mel": 9, "tex": 4}}
PALETTE_OPTIONS = {"pad": ["saw", "keys", "strings", "glass"], "lead": ["pluck", "bell", "square", "none"],
                   "bass": ["sub", "pluck", "none"], "drums": ["soft", "electronic", "halftime", "breakbeat", "none"]}
PALETTE_DEFAULTS = {"melody": False, "swing": 0.0, "brightness": 0.5}


def resolve_palette(mood, channel_music=None, override=None):
    """Paleta efectiva: por defecto del ánimo < brand.json → music < --palette. Valida valores."""
    pal = dict(PALETTE_DEFAULTS)
    pal.update(MOODS[mood]["palette"])
    for src in (channel_music or {}, override or {}):
        for k, v in src.items():
            if k.startswith("_"):
                continue
            if k in PALETTE_OPTIONS:
                if v not in PALETTE_OPTIONS[k]:
                    raise ValueError(f"music.{k}: «{v}» no existe ({', '.join(PALETTE_OPTIONS[k])})")
            elif k == "melody":
                if not isinstance(v, bool):
                    raise ValueError("music.melody: true o false")
            elif k in ("swing", "brightness"):
                hi = 0.3 if k == "swing" else 1.0
                if not isinstance(v, (int, float)) or not 0 <= v <= hi:
                    raise ValueError(f"music.{k}: entre 0 y {hi}")
            else:
                raise ValueError(f"music.{k}: clave desconocida (pad, lead, bass, drums, melody, swing, brightness)")
            pal[k] = v
    return pal


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def chord(scale, key, degree, base, extra=True):
    """Notas MIDI del acorde (tríada + 7.ª + 9.ª si extra) sobre el grado, cerca de `base`."""
    sc = SCALES[scale]
    idx = [degree, degree + 2, degree + 4] + ([degree + 6, degree + 8] if extra else [])
    notes = [key + sc[i % 7] + 12 * (i // 7) for i in idx]
    while notes[0] < base:
        notes = [n + 12 for n in notes]
    while notes[0] >= base + 12:
        notes = [n - 12 for n in notes]
    return notes


def place(buf, start, st):
    i = int(start)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(st))
    buf[i:j] += st[:j - i]


def pad_note(f, dur, bright, rng, K=10):
    """Sierra limitada en banda (aditiva) con 3 voces desafinadas; `bright` 0–1 (curva o escalar)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    b = np.broadcast_to(np.asarray(bright, dtype=float), (n,)) if np.ndim(bright) else np.full(n, float(bright))
    out = np.zeros((n, 2))
    for det, p in ((-0.09, -0.6), (0.0, 0.0), (0.09, 0.6)):
        fd = f * 2 ** (det / 12)
        ph = rng.uniform(0, 2 * np.pi)
        v = np.zeros(n)
        for k in range(1, K + 1):
            if fd * k > 9000:
                break
            w = (1 / k) * np.exp(-(k - 1) / (0.6 + 5 * b))
            v += w * np.sin(2 * np.pi * fd * k * t + ph * k)
        out += pan2(v, p)
    return out / 3


def pluck(f, dur=0.32, decay=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    v = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.03)
    return v * np.exp(-t / decay) * np.clip(t / 0.002, 0, 1)


def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    v = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
    v = np.tanh(1.6 * v) * np.exp(-t / max(dur * 0.8, 0.05)) * np.clip(t / 0.005, 0, 1)
    v[-min(240, n):] *= np.linspace(1, 0, min(240, n))
    return v


def fm_tone(f, dur, ratio, index, idx_decay, attack, decay):
    n = int(dur * SR)
    t = np.arange(n) / SR
    idx = index * np.exp(-t / idx_decay)
    v = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * ratio * t))
    return v * np.clip(t / attack, 0, 1) * np.exp(-t / decay)


def pad_voice(kind, f, dur, bright, rng):
    """Una nota del pad según el instrumento de la paleta (estéreo)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "saw":
        return pad_note(f, dur, bright, rng)
    if kind == "strings":  # sierras más oscuras, más voces y vibrato lento
        b = (np.asarray(bright) * 0.6) if np.ndim(bright) else bright * 0.6
        out = pad_note(f, dur, b, rng, K=8)
        vib = 1 + 0.12 * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6))
        return out * vib[:, None]
    if kind == "glass":  # campanas FM sostenidas + octava brillante
        b = float(np.mean(bright)) if np.ndim(bright) else float(bright)
        v = fm_tone(f, dur, 3.5, 1.2 + 1.5 * b, 0.8, 0.25, 6.0) + 0.3 * fm_tone(2 * f, dur, 2.0, 0.8, 0.5, 0.4, 3.0)
        p = rng.uniform(-0.5, 0.5)
        return pan2(v, p) * 0.9
    if kind == "keys":  # piano eléctrico FM: ataque, cuerpo que decae (se re-toca en el ritmo)
        v = fm_tone(f, dur, 1.0, 2.2, 0.35, 0.004, 1.4) + 0.15 * fm_tone(f * 4, dur, 1.0, 1.0, 0.05, 0.002, 0.15)
        trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
        return pan2(v * trem, rng.uniform(-0.3, 0.3)) * 1.1
    raise ValueError(kind)


def lead_voice(kind, f, bright=0.5):
    if kind == "pluck":
        return pluck(f)
    if kind == "bell":
        return fm_tone(f, 0.7, 1.4, 2.0, 0.2, 0.002, 0.3) * 0.9
    if kind == "square":  # cuadrada suave (armónicos impares filtrados)
        n = int(0.3 * SR)
        t = np.arange(n) / SR
        v = sum((1 / k) * np.exp(-(k - 1) / (2 + 6 * bright)) * np.sin(2 * np.pi * f * k * t) for k in (1, 3, 5, 7, 9))
        return v * np.clip(t / 0.003, 0, 1) * np.exp(-t / 0.13) * 0.8
    raise ValueError(kind)


def bass_voice(kind, f, dur):
    if kind == "sub":
        return bass_note(f, dur)
    if kind == "pluck":  # bajo con armónicos y caída rápida (más rítmico)
        n = int(dur * SR)
        t = np.arange(n) / SR
        v = sum((1 / k) * np.exp(-t * k * 6) * np.sin(2 * np.pi * f * k * t) for k in range(1, 7))
        v = np.tanh(1.4 * v) * np.exp(-t / max(dur * 0.5, 0.04)) * np.clip(t / 0.003, 0, 1)
        v[-min(240, n):] *= np.linspace(1, 0, min(240, n))
        return v
    raise ValueError(kind)


# Patrones de percusión por compás: (pulso 0–3.75, pieza, ganancia)
DRUM_PATTERNS = {
    "soft": [(0, "kick", 1), (2, "kick", 1), (1, "snare", 0.8), (3, "snare", 0.8)],
    "electronic": [(0, "kick", 1), (1, "kick", 1), (2, "kick", 1), (3, "kick", 1), (1, "clap", 1), (3, "clap", 1)],
    "halftime": [(0, "kick", 1), (2, "snare", 1), (2.75, "kick", 0.6)],
    "breakbeat": [(0, "kick", 1), (0.75, "kick", 0.7), (2.5, "kick", 0.8), (1, "snare", 1), (3, "snare", 1),
                  (3.75, "snare", 0.35)],
}


def drum_kit(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t / 0.04)) / SR) * np.exp(-t / 0.16)
    hat = band_noise(int(0.06 * SR), rng, 6000, 16000) * np.exp(-np.arange(int(0.06 * SR)) / SR / 0.015)
    ns = int(0.2 * SR)
    ts = np.arange(ns) / SR
    snare = (0.7 * band_noise(ns, rng, 1200, 8000) + 0.4 * np.sin(2 * np.pi * 190 * ts)) * np.exp(-ts / 0.07)
    clap = np.zeros(int(0.25 * SR))
    for k, d in enumerate((0.0, 0.011, 0.023)):  # tres golpes de ruido muy juntos
        bn = band_noise(int(0.2 * SR), rng, 900, 6000) * np.exp(-np.arange(int(0.2 * SR)) / SR / (0.012 if k < 2 else 0.08))
        i = int(d * SR)
        clap[i:i + len(bn)] += bn[:len(clap) - i]
    kick_e = np.sin(2 * np.pi * np.cumsum(52 + 140 * np.exp(-t / 0.025)) / SR) * np.exp(-t / 0.12)
    return {"kick": kick, "kick_e": kick_e, "hat": hat, "snare": snare, "clap": clap * 0.5}


def compose_track(duration, mood, root_hz, seed=1, bpm=None, glitchy=False, palette=None, stems=None):
    cfg = MOODS[mood]
    pal = palette or resolve_palette(mood)
    rng = np.random.default_rng(seed * 7919 + int(root_hz))
    key = (round(12 * math.log2(root_hz / 440)) + 69) % 12
    tail = 3.0
    bpm0 = bpm or cfg["bpm"]
    bar0 = 4 * 60 / bpm0
    n_bars = max(4, int(round((duration - tail) / bar0)))  # el más cercano al tempo del ánimo
    bar = (duration - tail) / n_bars  # tempo ajustado: los compases caen exactos en la duración
    beat = bar / 4
    swing = pal["swing"] * beat / 2
    prog = cfg["progs"][rng.integers(len(cfg["progs"]))]
    scale = cfg["scale"]
    energy = cfg["energy"]
    bright_k = 0.5 + pal["brightness"]
    total_n = int(duration * SR)
    pad = np.zeros((total_n, 2))
    arp = np.zeros((total_n, 2))
    bass = np.zeros((total_n, 2))
    drums = np.zeros((total_n, 2))
    tex = np.zeros((total_n, 2))
    mel = np.zeros((total_n, 2))

    # Secciones (en compases): intro, desarrollo, clímax, pausa, final
    s_build, s_main = int(n_bars * 0.15), int(n_bars * 0.35)
    s_break, s_out = int(n_bars * 0.72), int(n_bars * 0.85)

    def section(b):
        return ("intro" if b < s_build else "build" if b < s_main else "main" if b < s_break
                else "break" if b < s_out else "outro")

    def sw(t_beat_frac):  # swing: retrasa las corcheas a contratiempo
        return swing if abs((t_beat_frac * 2) % 2 - 1) < 1e-6 else 0.0

    # Pad: acorde cada 2 compases (o re-tocado en ritmo si es «keys»), brillo que sube al clímax
    for b in range(0, n_bars, 2):
        deg = prog[(b // 2) % len(prog)]
        notes = chord(scale, key, deg, 52)
        last = b + 2 >= n_bars
        sec = section(b)
        bright_target = min(1.0, {"intro": 0.15, "build": 0.35, "main": 0.65, "break": 0.3, "outro": 0.2}[sec] * bright_k)
        hits = [(0.0, 2 * bar + (tail if last else 0.9))]
        if pal["pad"] == "keys" and not last:  # el piano decae: se re-toca siempre (si no, la intro se apaga)
            if sec in ("build", "main") and energy >= 2:
                hits = [(q * beat, 2.2 * beat) for q in (0, 2.5, 4, 6.5)]
            else:
                hits = [(0, 4.5 * beat), (4 * beat, 4.5 * beat)]
        for off, dur in hits:
            nn = int(dur * SR)
            bright = np.linspace(bright_target * 0.8, bright_target, nn)
            acc = np.zeros((nn, 2))
            for k, m in enumerate(notes):
                acc += pad_voice(pal["pad"], hz(m), dur, bright, rng) * (0.9 if k < 3 else 0.55)
            atk = 0.004 if pal["pad"] == "keys" else (0.9 if b == 0 else (0.7 if pal["pad"] == "strings" else 0.35))
            acc *= adsr(nn, atk, 1.2 if last else 0.6)[:, None]
            place(pad, (b * bar + off) * SR, acc * 0.22)

    # Bajo: raíz con pulso según energía, desde el desarrollo
    if pal["bass"] != "none":
        for b in range(s_build, n_bars):
            sec = section(b)
            if sec == "outro" and b > s_out + 1:
                break
            root = chord(scale, key, prog[(b // 2) % len(prog)], 33, extra=False)[0]
            if sec == "main":
                hits = range(8) if energy >= 2 else range(0, 8, 2)
            else:
                hits = range(0, 8, 4) if energy <= 1 else range(0, 8, 2)
            for h in hits:
                note = root + (12 if pal["bass"] == "pluck" and h % 4 == 3 else 0)
                v = bass_voice(pal["bass"], hz(note), beat * (0.45 if sec == "main" else 0.9))
                place(bass, (b * bar + h * beat / 2 + sw(h / 2)) * SR, pan2(v, 0) * (0.2 if h % 2 == 0 else 0.13))

    # Arpegio con eco ping-pong: desde el desarrollo, más denso en el clímax, se va en la pausa
    if pal["lead"] != "none":
        pat = [[0, 1, 2, 3, 2, 1, 0, 1], [0, 2, 1, 3, 0, 2, 4, 2], [0, 1, 2, 4, 3, 2, 1, 2]][rng.integers(3)]
        for b in range(s_build, s_out):
            sec = section(b)
            notes = chord(scale, key, prog[(b // 2) % len(prog)], 64)
            steps = cfg["arp"] if sec == "main" else (4 if energy == 0 else 8)
            for st_i in range(steps):
                if sec == "build" and st_i % 2 and b < (s_build + s_main) // 2:
                    continue
                m = notes[pat[st_i % len(pat)] % len(notes)]
                v = lead_voice(pal["lead"], hz(m), pal["brightness"]) * (0.16 if sec != "break" else 0.12)
                st = b * bar + st_i * bar / steps + sw(st_i * 4 / steps)
                place(arp, st * SR, pan2(v, -0.3))
                for e, (g, p) in enumerate(((0.45, 0.7), (0.25, -0.7), (0.12, 0.7))):
                    place(arp, (st + (e + 1) * 0.75 * beat) * SR, pan2(v * g, p))

    # Melodía: motivo de 2 compases (semilla), en el clímax, con variación cada repetición
    if pal["melody"]:
        sc = SCALES[scale]
        mrng = np.random.default_rng(seed * 31 + 7)
        rhythms = [[0, 1, 1.5, 2, 3, 4, 5.5, 6], [0, 0.5, 1, 2, 3.5, 4, 4.5, 6], [0, 1.5, 2, 3, 4, 5, 5.5, 6]]
        rhythm = rhythms[mrng.integers(len(rhythms))]
        steps_deg = list(mrng.choice([-2, -1, 1, 2, 0, 1, -1], size=len(rhythm)))
        voice = pal["lead"] if pal["lead"] != "none" else "bell"
        for rep, b in enumerate(range(s_main, s_break - 1, 4)):
            deg0 = prog[(b // 2) % len(prog)]
            d = deg0 + 7
            for k, (pos, step) in enumerate(zip(rhythm, steps_deg)):
                d += step
                if k == len(rhythm) - 1 and rep % 2:
                    d = deg0 + 7 + 4  # cierre distinto en las repeticiones impares
                m = key + 60 + sc[d % 7] + 12 * (d // 7 - 1)
                v = lead_voice(voice, hz(m), pal["brightness"]) * 0.13
                place(mel, (b * bar + pos * beat + sw(pos)) * SR, pan2(v, 0.15))

    # Percusión: patrón de la paleta; la energía decide en qué secciones y la densidad de platillos
    kit = drum_kit(rng)
    kicks = []
    if pal["drums"] != "none" and energy >= 1:
        pattern = DRUM_PATTERNS[pal["drums"]]
        kick_name = "kick_e" if pal["drums"] in ("electronic", "breakbeat") else "kick"
        for b in range(s_build, s_break):
            sec = section(b)
            if sec == "build" and energy < 3:
                if energy == 2 and b >= (s_build + s_main) // 2:
                    place(drums, b * bar * SR, pan2(kit[kick_name], 0) * 0.42)
                    kicks.append(b * bar)
                continue
            for pos, piece, g in pattern:
                if energy == 1 and piece == "kick" and pos not in (0, 2):
                    continue
                tq = b * bar + pos * beat + sw(pos)
                name = kick_name if piece == "kick" else piece
                gain = {"kick": 0.42, "kick_e": 0.42, "snare": 0.18, "clap": 0.2}[name] * g
                place(drums, tq * SR, pan2(kit[name], 0 if "kick" in name else -0.1) * gain)
                if "kick" in name:
                    kicks.append(tq)
            hat_step = {1: 0.5, 2: 0.5, 3: 0.25}[energy]
            for i in range(int(4 / hat_step)):
                pos = i * hat_step
                if energy < 3 and pos == int(pos):
                    continue  # contratiempos
                place(drums, (b * bar + pos * beat + sw(pos)) * SR, pan2(kit["hat"], 0.3) * {1: 0.05, 2: 0.1, 3: 0.08}[energy])

    # Textura: aire filtrado con respiración lenta + destellos agudos ocasionales
    air = band_noise(total_n, rng, 300, 3500)
    tt = np.arange(total_n) / SR
    tex += pan2(air * (0.5 + 0.5 * np.sin(2 * np.pi * tt / (bar * 4))) * 0.02, 0)
    for b in range(2, n_bars - 2, 4):
        f0 = hz(key + 84 + SCALES[scale][rng.integers(7)])
        n = int(0.6 * SR)
        t = np.arange(n) / SR
        bl = np.sin(2 * np.pi * np.cumsum(np.full(n, f0) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))) / SR)
        if glitchy:
            bl = 0.8 * bl + 0.2 * np.round(bl * 4) / 4
        shape = np.clip(t / 0.015, 0, 1) * np.exp(-t / 0.18)  # ataque suave: sin chasquido
        place(tex, (b * bar + 2.5 * beat) * SR, pan2(bl * shape * 0.035, rng.uniform(-0.8, 0.8)))

    # Bombeo suave (sidechain) de pad y bajo con cada bombo
    if kicks:
        scn = np.ones(total_n)
        dk = np.exp(-np.arange(int(0.3 * SR)) / SR / 0.11)
        for tk in kicks:
            i = int(tk * SR)
            j = min(total_n, i + len(dk))
            if i < total_n:
                scn[i:j] = np.minimum(scn[i:j], 1 - 0.4 * dk[: j - i])
        pad *= scn[:, None]
        bass *= scn[:, None]

    g = {k: 10 ** (v / 20) for k, v in MIX_DB[energy].items()}
    pad, arp, bass, drums, tex, mel = (pad * g["pad"], arp * g["arp"], bass * g["bass"], drums * g["drums"],
                                       tex * g["tex"], mel * g["mel"])
    if stems is not None:  # para análisis y tests: nivel de cada capa
        stems.update({"pad": pad, "arp": arp, "bass": bass, "drums": drums, "tex": tex, "mel": mel})
    dry = pad + arp + bass + drums + tex + mel
    wet = reverb(pad * 0.5 + arp * 0.8 + mel * 0.6 + drums * 0.1 + tex * 0.6, rng)
    mix = dry + 0.45 * wet
    mix = eq(mix, VOICE_POCKET)
    mix = level_sections(mix, tail)
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.95
    mix = np.tanh(1.3 * mix) / np.tanh(1.3)  # saturación/limitador suave
    fo = int(0.4 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 10 ** (-1 / 20)
    info = {"bpm": round(4 * 60 / bar, 1), "bars": n_bars, "key": ["C", "C#", "D", "D#", "E", "F", "F#", "G",
            "G#", "A", "A#", "B"][key] + ("m" if scale == "minor" else ""), "progression": prog, "palette": pal}
    return mix, info


def level_sections(x, tail, max_dip_db=3.0, win_s=3.0):
    """Nivelación lenta: ninguna parte (salvo la cola final) queda más de `max_dip_db` por debajo del
    nivel del cuerpo de la pista. La intro puede crecer, pero no desaparecer bajo la voz."""
    n = len(x)
    hop = int(0.25 * SR)
    blocks = max(1, n // hop)
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(blocks)])
    w = max(1, int(win_s / 0.25))
    sm = np.convolve(rms, np.ones(w) / w, mode="same")
    body = float(np.percentile(sm[: max(1, blocks - int(tail / 0.25))], 70))
    floor = body * 10 ** (-max_dip_db / 20)
    gain = np.clip(floor / np.maximum(sm, 1e-9), 1.0, 10 ** (12 / 20))
    gain[blocks - int(tail / 0.25):] = gain[max(0, blocks - int(tail / 0.25) - 1)]  # la cola sigue su caída natural
    g = np.interp(np.arange(n), np.arange(blocks) * hop + hop / 2, gain)
    return x * g[:, None]


# Curva de ecualización final (Hz, dB): sin subgraves, graves y medios-bajos contenidos y un hueco
# suave donde vive la voz (1–4 kHz) para que la música vaya debajo sin taparla.
VOICE_POCKET = [(20, -40), (35, -12), (60, -1), (120, -3), (300, -4), (600, -1.5), (1000, -2.5),
                (2500, -4), (4500, -2), (8000, 0.5), (14000, 1), (24000, 0)]


def eq(x, curve):
    """Ecualizador por FFT (fase cero) con interpolación en escala logarítmica de frecuencia."""
    n = len(x)
    m = 1 << int(np.ceil(np.log2(n)))
    fr = np.fft.rfftfreq(m, 1 / SR)
    fpts, gpts = zip(*curve)
    g = 10 ** (np.interp(np.log10(np.maximum(fr, 1)), np.log10(fpts), gpts) / 20)
    out = np.empty_like(x)
    for c in range(x.shape[1]):
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], m) * g, m)[:n]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--mood", choices=sorted(MOODS), default="esperanzador")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--palette", help='JSON con instrumentos para probar sin tocar la marca, p. ej. \'{"pad":"keys"}\'')
    ap.add_argument("--out")
    ap.add_argument("--add", action="store_true", help="registrar en la biblioteca del canal")
    ap.add_argument("--title")
    ap.add_argument("--replace", action="store_true", help="con --add: reemplaza la pista del mismo título")
    args = ap.parse_args()
    if not 10 <= args.duration <= 600:
        oslib.die("--duration entre 10 y 600 s")
    cdir = oslib.channel_path(args.channel)
    ch = oslib.load_channel(cdir)
    sound = ch["brand"].get("sound", {})
    import json
    try:
        override = json.loads(args.palette) if args.palette else None
        pal = resolve_palette(args.mood, ch["brand"].get("music"), override)
    except (ValueError, json.JSONDecodeError) as e:
        oslib.die(f"paleta inválida: {e}")
    mix, info = compose_track(args.duration, args.mood, float(sound.get("root_hz", 880)), args.seed, args.bpm,
                              sound.get("texture") == "glitchy", pal)
    title = args.title or f"Propia {args.mood} {args.seed}"
    out = Path(args.out) if args.out else oslib.ROOT / "work" / "musicgen" / f"{oslib_slug(title)}.wav"
    write_wav(out, mix)
    res = {"ok": True, "file": str(out), "duration_s": round(len(mix) / SR, 3), "mood": args.mood,
           "seed": args.seed, **info}
    if args.add:
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("music.py")), "add", "--channel", args.channel,
                            "--file", str(out), "--title", title, "--source", "propia", "--mood", args.mood,
                            "--bpm", str(info["bpm"]), "--palette", json.dumps(pal),
                            "--license", f"Propia: generada con scripts/audio/musicgen.py (mood {args.mood}, seed {args.seed}); "
                                         "sin restricciones, apta para anuncios"] + (["--replace"] if args.replace else []),
                           capture_output=True, text=True)
        if r.returncode:
            oslib.die(f"music.py add falló: {r.stdout}{r.stderr}")
        res["added"] = json.loads(r.stdout)["added"]["id"]
    oslib.emit(res)


def oslib_slug(s):
    import re
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "pista"


if __name__ == "__main__":
    main()
