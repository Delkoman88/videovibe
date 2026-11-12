#!/usr/bin/env python3
"""Genera el kit de efectos de sonido de un canal por síntesis (100 % propios: sin licencias ni reclamos).

Uso: scripts/audio/sfx.py --channel <id> [--force]          genera el kit (base + recetas del canal)
     scripts/audio/sfx.py --channel <id> --list              lista el kit con el uso de cada efecto
     scripts/audio/sfx.py --channel <id> --preview a b …     muestrario .wav (work/sfx-preview-<canal>.wav)
     scripts/audio/sfx.py add --channel <id> --file <ruta> --name centrifuga --use "…" --license "…" \
                    [--provided-by "<persona>"] [--ads] [--entrance]      efecto aportado (grabado por la persona)

Efectos aportados: el original va a audio/sfx/user/ (fuera de git) y su registro a audio/sfx/user.json
(en git). En el kit se usa una copia procesada: sin silencios al inicio/final, fundidos de 5 ms, pico a
−1 dBFS, 48 kHz estéreo, máx. 4 s. Precedencia: usuario > receta > base.

Escribe channels/<id>/audio/sfx/<nombre>.wav (48 kHz, estéreo, −1 dBFS de pico) y sfx.json con la
descripción de cada efecto. El carácter sale de brand.json → sound (opcional):
  {"root_hz": 880, "brightness": 0.6, "texture": "clean" | "glitchy"}
Entradas de escena (sfx_auto las rota): ver ENTRANCES. Texturas: whoosh, impact, bell, bubbles,
heartbeat, typing, riser, sparkle, zap.
Otros: pulse (entrada de elemento), click (tarjeta/UI), data (procesamiento), sweep (transición
suave, usar poco), rise (revelación), success (verificado), warn (error/limitación), glitch (corte digital).
Efectos propios del canal SIN programar: channels/<id>/audio/sfx/recipes.json (capas tone, noise, fm,
sub, grains + fx reverb, lowpass, highpass, bitcrush, tremolo; frecuencias en Hz o "root*1.5").
Una receta con el nombre de un efecto base lo reemplaza. Formato y ejemplos: docs/audio.md.
Determinista: misma marca y recetas → mismos archivos. Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402
from scripts.audio import sfxrecipes  # noqa: E402
from scripts.audio import audiotools  # noqa: E402

oslib.ensure_venv()
import numpy as np  # noqa: E402

SR = 48000
env = audiotools.env_decay        # primitivas comunes (scripts/audio/audiotools.py)
noise = audiotools.noise_band_frac
pan = audiotools.pan


def write_wav(path, sig, peak_db=-1.0):
    """Efecto a −1 dBFS de pico, con fundido final y en estéreo."""
    audiotools.write_wav(path, sig, SR, peak_db=peak_db, end_fade=240, stereo=True)
GEN_VERSION = 2  # súbelo si cambia la síntesis base (regenera los kits)

DESCRIPTIONS = {
    "pulse": "Pulso breve con subida de tono: entrada de un elemento o escena",
    "click": "Clic de interfaz muy corto: aparece una tarjeta o etiqueta",
    "data": "Tres destellos rápidos: datos procesándose, terminal, agentes",
    "sweep": "Barrido suave de ruido filtrado: transición de escena (usar con moderación)",
    "rise": "Subida tonal: revelación de un título o resultado",
    "success": "Dos tonos ascendentes: algo verificado o logrado",
    "warn": "Dos tonos graves descendentes: error, limitación, advertencia",
    "glitch": "Destello digital granulado: glitch breve y controlado",
    "ping": "Ping de sonar con cola larga: aparece un diagrama o red (entrada)",
    "bloom": "Acorde suave que se abre: entrada de escena tranquila o conceptual",
    "blip": "Arpegio ascendente muy rápido: entrada de escena técnica o de datos",
    "scan": "Barrido corto ascendente con tono: escaneo, análisis, molécula (entrada)",
    "drop": "Tono que cae de agudo a medio: entrada con peso, cambio de tema",
    "shimmer": "Brillo agudo con trémolo: entrada de título o revelación ligera",
    "whoosh": "Soplo de aire que cruza de izquierda a derecha: salida o transición de escena",
    "impact": "Golpe grave con cola: revelación importante, dato fuerte (usar poco)",
    "bell": "Campana metálica (FM) con cola larga: idea, red, conexión",
    "bubbles": "Burbujas ascendentes: célula, biología, laboratorio húmedo",
    "heartbeat": "Latido doble grave: salud, pulso, vida",
    "typing": "Tecleo rápido: terminal, código, agentes escribiendo",
    "riser": "Subida de ruido y tono de 1 s: anticipa una revelación",
    "sparkle": "Destellos agudos dispersos: ADN, moléculas, algo nuevo",
    "zap": "Láser descendente: acción de un agente o herramienta",
}

# Variantes que sfx_auto rota al entrar las escenas (ver docs/storyboard.md).
ENTRANCES = ["bell", "sparkle", "bubbles", "zap", "pulse", "scan", "bloom", "blip", "drop", "shimmer", "ping"]


def tone(f0, f1, dur, decay, harm=0.25):
    n = int(SR * dur)
    f = np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sig = np.sin(ph) + harm * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
    return sig * env(n, decay=decay)


def build(sound):
    root = float(sound.get("root_hz", 880))
    bright = float(sound.get("brightness", 0.6))
    glitchy = sound.get("texture") == "glitchy"
    rng = np.random.default_rng(int(root))
    h = 0.15 + 0.3 * bright
    out = {}
    out["pulse"] = tone(root, root * 1.5, 0.12, 0.05, h)
    c = noise(0.03, rng, 0.25, 0.9) * env(int(SR * 0.03), 0.001, 0.006)
    out["click"] = c + 0.3 * tone(root * 2, root * 2, 0.03, 0.008, 0)
    d = np.zeros(int(SR * 0.3))
    for k, mult in enumerate([1.0, 1.26, 1.5]):
        b = tone(root * 1.5 * mult, root * 1.5 * mult, 0.05, 0.02, h)
        s = int(SR * 0.075 * k)
        d[s:s + len(b)] += b
    out["data"] = d
    n = int(SR * 0.45)
    sw = noise(0.45, rng, 0.02, 0.35 + 0.3 * bright)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    out["sweep"] = sw * shape * 0.6
    r = tone(root / 2, root * 1.2, 0.6, 0.35, h)
    out["rise"] = r * np.linspace(0.2, 1, len(r))
    s1, s2 = tone(root, root, 0.09, 0.05, h), tone(root * 1.5, root * 1.5, 0.16, 0.08, h)
    succ = np.zeros(int(SR * 0.28))
    succ[:len(s1)] += s1
    succ[int(SR * 0.09):int(SR * 0.09) + len(s2)] += s2
    out["success"] = succ
    w1, w2 = tone(root / 2, root / 2, 0.12, 0.08, 0.4), tone(root / 2.5, root / 2.5, 0.18, 0.1, 0.4)
    warn = np.zeros(int(SR * 0.34))
    warn[:len(w1)] += w1
    warn[int(SR * 0.13):int(SR * 0.13) + len(w2)] += w2
    out["warn"] = warn
    gl = noise(0.14, rng, 0.05, 0.8)
    step = 6 if glitchy else 12
    gl = np.repeat(gl[::step], step)[:len(gl)]  # reducción de resolución (granulado)
    gl = np.round(gl * 6) / 6
    gate = (np.floor(np.arange(len(gl)) / (SR * 0.018)) % 2 == 0).astype(float)
    out["glitch"] = gl * gate * env(len(gl), 0.001, 0.07) * 0.7
    out["ping"] = tone(root * 1.25, root * 1.2, 0.5, 0.18, 0.08)
    out["bloom"] = sum(tone(root * m, root * m, 0.45, 0.2, h) * env(int(SR * 0.45), 0.04, 0.2)
                       for m in (0.5, 0.63, 0.75))
    bl = np.zeros(int(SR * 0.2))
    for k, mult in enumerate([1.0, 1.19, 1.5, 2.0]):
        b = tone(root * 2 * mult, root * 2 * mult, 0.035, 0.012, h)
        s0 = int(SR * 0.035 * k)
        bl[s0:s0 + len(b)] += b
    out["blip"] = bl
    sc = noise(0.25, rng, 0.1, 0.5 + 0.3 * bright) * np.linspace(0.1, 1, int(SR * 0.25)) * env(int(SR * 0.25), 0.15, 0.05)
    out["scan"] = 0.5 * sc + tone(root * 0.75, root * 1.5, 0.25, 0.1, h)
    out["drop"] = tone(root * 2, root * 0.75, 0.18, 0.09, h)
    t = np.arange(int(SR * 0.4)) / SR
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 18 * t)
    out["shimmer"] = (tone(root * 3, root * 3.1, 0.4, 0.15, 0) + 0.5 * tone(root * 4.5, root * 4.6, 0.4, 0.12, 0)) * trem
    out.update(textures(root, bright, rng))
    return out


def textures(root, bright, rng):
    """Familias de timbre distintas (ruido, FM, graves, granular) para que no todo suene a tono."""
    out = {}
    n = int(SR * 0.55)
    x = np.linspace(0, 1, n)
    lo, hi = noise(0.55, rng, 0.005, 0.06), noise(0.55, rng, 0.06, 0.3 + 0.3 * bright)
    r = np.sin(np.pi * x)
    out["whoosh"] = pan((lo * (1 - r) + hi * r * 0.7) * np.sin(np.pi * x) ** 1.5, -0.8 + 1.6 * x)
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    f = 38 + 80 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    hit = noise(0.7, rng, 0.0, 0.2) * np.exp(-t / 0.015)
    out["impact"] = sub + 0.5 * hit + 0.15 * noise(0.7, rng, 0.0, 0.03) * np.exp(-t / 0.3)
    n = int(SR * 1.0)
    t = np.arange(n) / SR
    fc, fm = root * 0.75, root * 0.75 * 1.4
    idx = 3.0 * np.exp(-t / 0.25)
    out["bell"] = np.sin(2 * np.pi * fc * t + idx * np.sin(2 * np.pi * fm * t)) * env(n, 0.002, 0.35)
    bub = np.zeros((int(SR * 0.7), 2))
    for k in range(6):
        d = 0.05 + 0.03 * rng.random()
        f0 = root * (0.4 + 0.5 * rng.random())
        b = tone(f0, f0 * 2.2, d, d / 2, 0)
        s0 = int(SR * (0.02 + 0.1 * k + 0.03 * rng.random()))
        bub[s0:s0 + len(b)] += pan(b, rng.uniform(-0.7, 0.7))
    out["bubbles"] = bub
    hb = np.zeros(int(SR * 0.55))
    for s0, g in ((0.0, 1.0), (0.2, 0.7)):
        n1 = int(SR * 0.25)
        t1 = np.arange(n1) / SR
        th = np.sin(2 * np.pi * np.cumsum(60 - 20 * t1 / 0.25) / SR) * np.exp(-t1 / 0.07) * g
        i = int(SR * s0)
        hb[i:i + n1] += th
    out["heartbeat"] = hb
    ty = np.zeros((int(SR * 0.7), 2))
    pos = 0.0
    while pos < 0.6:
        c = noise(0.02, rng, 0.15 + 0.3 * rng.random(), 0.9) * env(int(SR * 0.02), 0.0005, 0.004)
        i = int(SR * pos)
        ty[i:i + len(c)] += pan(c * rng.uniform(0.5, 1), rng.uniform(-0.3, 0.3))
        pos += rng.uniform(0.04, 0.09)
    out["typing"] = ty
    n = int(SR * 1.0)
    x = np.linspace(0, 1, n)
    rz = noise(1.0, rng, 0.02, 0.15 + 0.4 * bright) * x ** 2 + tone(root / 4, root, 1.0, 10, 0.3) * x ** 2 * 0.6
    rz[-int(SR * 0.02):] *= np.linspace(1, 0, int(SR * 0.02))
    out["riser"] = rz
    sp = np.zeros((int(SR * 0.6), 2))
    for k in range(9):
        f0 = root * rng.choice([2, 2.5, 3, 4, 5])
        b = tone(f0, f0, 0.12, 0.04, 0)
        i = int(SR * 0.05 * k + SR * 0.02 * rng.random())
        sp[i:i + len(b)] += pan(b * (1 - k / 12), rng.uniform(-0.9, 0.9))
    out["sparkle"] = sp
    n = int(SR * 0.3)
    t = np.arange(n) / SR
    f = root * 3 * np.exp(-t / 0.08) + root / 3
    out["zap"] = np.sin(2 * np.pi * np.cumsum(f) / SR + 2 * np.sin(2 * np.pi * root * 0.5 * t)) * env(n, 0.001, 0.12)
    return out


# ------------------------------------------------------------------ recetas (recipes.json)

def _band(x, lo, hi):
    """Filtro de banda por FFT con bordes suaves (lo/hi en Hz; None = sin ese borde)."""
    n = x.shape[0]
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * (g[:, None] if x.ndim == 2 else g), n, axis=0)


def _layer(lay, n, root, rng):
    F = lambda k, d=None: sfxrecipes.freq(lay[k], root) if k in lay else d  # noqa: E731
    t = np.arange(n) / SR
    e = env(n, lay.get("attack", 0.004), lay.get("decay", 0.15))
    typ = lay["type"]
    if typ == "tone":
        f0 = F("f0")
        f = np.linspace(f0, F("f1", f0), n)
        ph = 2 * np.pi * np.cumsum(f) / SR
        h = lay.get("harm", 0.25)
        return (np.sin(ph) + h * np.sin(2 * ph) + 0.4 * h * np.sin(3 * ph)) * e
    if typ == "noise":
        a = noise(n / SR, rng, F("lo") / 24000, min(1.0, F("hi") / 24000))
        if "lo1" in lay or "hi1" in lay:
            b = noise(n / SR, rng, F("lo1", F("lo")) / 24000, min(1.0, F("hi1", F("hi")) / 24000))
            x = np.linspace(0, 1, n)
            a = a * (1 - x) + b * x
        return a / (np.max(np.abs(a)) + 1e-9) * e
    if typ == "fm":
        fc = F("f")
        idx = lay.get("index", 3.0) * np.exp(-t / lay.get("index_decay", 0.25))
        return np.sin(2 * np.pi * fc * t + idx * np.sin(2 * np.pi * fc * lay.get("ratio", 1.4) * t)) * e
    if typ == "sub":
        f0, f1 = F("f0", 110.0), F("f1", 38.0)
        f = f1 + (f0 - f1) * np.exp(-t / 0.05)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, lay.get("attack", 0.001), lay.get("decay", 0.22))
    if typ == "grains":
        g_rng = np.random.default_rng(lay.get("seed", 1))
        out = np.zeros((n, 2))
        gl = int(lay.get("grain", 0.05) * SR)
        lo, hi = F("f_lo"), F("f_hi")
        for _ in range(lay["count"]):
            f0 = g_rng.uniform(lo, hi)
            gt = np.arange(gl) / SR
            f = np.linspace(f0, f0 * (2.0 if lay.get("rising") else 1.0), gl)
            g = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.clip(gt / 0.002, 0, 1) * np.exp(-gt / (gl / SR / 3))
            i = int(g_rng.uniform(0, max(1, n - gl)))
            out[i:i + gl] += pan(g, g_rng.uniform(-1, 1) * lay.get("spread", 0.7))
        return out * env(n, 0.001, lay.get("decay", 4.0))[:, None]
    raise ValueError(typ)


def render_recipe(r, root, seed=0):
    """Sintetiza una receta (ya validada) a estéreo float."""
    n = int(r["duration"] * SR)
    out = np.zeros((n, 2))
    rng = np.random.default_rng(seed)
    for lay in r["layers"]:
        ln = int(lay.get("length", r["duration"] - lay.get("at", 0)) * SR)
        sig = _layer(lay, max(ln, 1), root, rng) * lay.get("gain", 1.0)
        st = sig if sig.ndim == 2 else pan(sig, lay.get("pan", 0.0))
        for k in range(lay.get("repeat", 1)):
            i = int((lay.get("at", 0) + k * lay.get("every", 0)) * SR)
            if i >= n:
                break
            j = min(n, i + len(st))
            out[i:j] += st[:j - i]
    fx = r.get("fx", {})
    if fx.get("lowpass") or fx.get("highpass"):
        out = _band(out, fx.get("highpass"), fx.get("lowpass"))
    if fx.get("bitcrush"):
        q = 2 ** (fx["bitcrush"] - 1)
        out = np.round(out / (np.max(np.abs(out)) + 1e-9) * q) / q
        out = np.repeat(out[::3], 3, axis=0)[:n]
    if fx.get("tremolo"):
        d = fx.get("tremolo_depth", 0.5)
        out *= (1 - d * (0.5 + 0.5 * np.sin(2 * np.pi * fx["tremolo"] * np.arange(n) / SR)))[:, None]
    if fx.get("reverb"):
        out = audiotools.reverb_short(out, rng, fx["reverb"], SR)
    return out


def load_recipes(cdir, root):
    f = cdir / "audio" / "sfx" / "recipes.json"
    if not f.exists():
        return {}, ""
    raw = f.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        oslib.die(f"{oslib.rel(f)}: JSON inválido ({e})")
    errs = sfxrecipes.validate(data, root)
    if errs:
        print(json.dumps({"ok": False, "error": "recetas inválidas", "file": oslib.rel(f),
                          "problems": errs}, ensure_ascii=False, indent=2))
        sys.exit(2)
    return data["recipes"], hashlib.sha1(raw.encode()).hexdigest()[:12]


# ------------------------------------------------------------------ efectos aportados (user.json)

MAX_USER_S = 4.0


def load_user(out_dir):
    f = out_dir / "user.json"
    return oslib.read_json(f) if f.exists() else {"sounds": {}}


def user_hash(out_dir, user):
    h = hashlib.sha1(json.dumps(user, sort_keys=True).encode())
    for name, u in sorted(user["sounds"].items()):
        f = out_dir / "user" / u["original"]
        h.update(f"{name}:{f.stat().st_size if f.exists() else 'falta'}".encode())
    return h.hexdigest()[:12]


def render_user(out_dir, name, u):
    """Copia procesada de un efecto aportado: recorta silencios, limita a 4 s y suaviza los bordes."""
    f = out_dir / "user" / u["original"]
    if not f.exists():
        oslib.die(f"falta el original del efecto «{name}»: {oslib.rel(f)} "
                  "(cópialo ahí o vuelve a registrarlo con sfx.py add)")
    x = audiotools.trim_silence(audiotools.load(f, SR), SR, rel_db=-50.0, keep_s=0.005, fade_s=0.005)
    cut = False
    if len(x) > MAX_USER_S * SR:
        x = audiotools.fades(x[: int(MAX_USER_S * SR)], SR, 0, 0.15)
        cut = True
    if not len(x):
        oslib.die(f"el efecto «{name}» está en silencio")
    return x, cut


def add_user(argv):
    ap = argparse.ArgumentParser(prog="sfx.py add", description="Registra un efecto aportado por la persona.")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--use", required=True, help="cuándo usarlo (lo lee el agente al elegir efectos)")
    ap.add_argument("--license", default="")
    ap.add_argument("--provided-by", default="")
    ap.add_argument("--ads", action="store_true", help="la licencia permite usarlo en publicidad pagada")
    ap.add_argument("--entrance", action="store_true", help="añadirlo a las entradas que rota sfx_auto")
    a = ap.parse_args(argv)
    if not a.license:
        oslib.die("--license es obligatorio: de dónde viene el derecho de uso (regla universal 5). "
                  "Si lo grabaste tú: --license \"Propio (grabado por <persona>)\" --ads")
    if not sfxrecipes.NAME_RE.match(a.name):
        oslib.die("--name: minúsculas, números y guiones (máx. 32)")
    src = Path(a.file).expanduser()
    if not src.exists():
        oslib.die(f"no existe {src}")
    try:
        meas, warnings, _ = audiotools.inspect(src, SR)
    except Exception as e:  # noqa: BLE001
        oslib.die(f"no se puede leer el audio de {src}: {e}")
    out_dir = oslib.channel_path(a.channel) / "audio" / "sfx"
    (out_dir / "user").mkdir(parents=True, exist_ok=True)
    orig = f"{a.name}{src.suffix.lower()}"
    import shutil
    shutil.copy(src, out_dir / "user" / orig)
    user = load_user(out_dir)
    user["sounds"][a.name] = {"original": orig, "use": a.use, "license": a.license,
                              "provided_by": a.provided_by, "ads": bool(a.ads), "entrance": bool(a.entrance)}
    oslib.write_json(out_dir / "user.json", user)
    warnings = [w for w in warnings if "silencio" not in w]  # el kit recorta los silencios solo
    if meas["duration_s"] > MAX_USER_S:
        warnings.append(f"dura {meas['duration_s']} s: en el kit se corta a {MAX_USER_S:g} s con fundido")
    return a.channel, {"added": a.name, "check": meas, "warnings": warnings}


def preview(out_dir, names, dst):
    kit = oslib.read_json(out_dir / "sfx.json")["sounds"]
    missing = [n for n in names if n not in kit]
    if missing:
        oslib.die(f"no están en el kit: {missing} (scripts/audio/sfx.py --channel … --list)")
    parts = []
    for n in names:
        with wave.open(str(out_dir / kit[n]["file"]), "rb") as f:
            x = np.frombuffer(f.readframes(f.getnframes()), "<i2").reshape(-1, 2)
        parts += [x, np.zeros((int(0.7 * SR), 2), "<i2")]
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(np.concatenate(parts).tobytes())


def main():
    added = None
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        channel, added = add_user(sys.argv[2:])
        sys.argv = [sys.argv[0], "--channel", channel]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true", help="lista el kit con el uso de cada efecto")
    ap.add_argument("--preview", nargs="+", metavar="EFECTO", help="muestrario .wav de estos efectos")
    args = ap.parse_args()
    cdir = oslib.channel_path(args.channel)
    ch = oslib.load_channel(cdir)
    sound = ch["brand"].get("sound", {})
    root = float(sound.get("root_hz", 880))
    out_dir = cdir / "audio" / "sfx"
    recipes, rhash = load_recipes(cdir, root)
    current = oslib.read_json(out_dir / "sfx.json") if (out_dir / "sfx.json").exists() else None
    user = load_user(out_dir)
    uhash = user_hash(out_dir, user) if user["sounds"] else ""
    fresh = current and current.get("sound") == sound and current.get("recipes_hash", "") == rhash \
        and current.get("generator_version") == GEN_VERSION and current.get("user_hash", "") == uhash
    if not fresh or args.force:
        sounds = build(sound)
        meta = {}
        for name, sig in sounds.items():
            meta[name] = {"file": f"{name}.wav", "duration_s": round(len(sig) / SR, 3), "use": DESCRIPTIONS[name],
                          "source": "base", "license": "Propio (sintetizado)", "ads": True}
        entrances = list(ENTRANCES)
        for i, (name, r) in enumerate(sorted(recipes.items())):
            sounds[name] = render_recipe(r, root, seed=int(hashlib.sha1(name.encode()).hexdigest()[:6], 16))
            meta[name] = {"file": f"{name}.wav", "duration_s": round(len(sounds[name]) / SR, 3), "use": r["use"],
                          "source": "receta", "license": "Propio (receta sintetizada)", "ads": True}
            if r.get("entrance") and name not in entrances:
                entrances.append(name)
        user_notes = []
        for name, u in sorted(user["sounds"].items()):
            sounds[name], cut = render_user(out_dir, name, u)
            meta[name] = {"file": f"{name}.wav", "duration_s": round(len(sounds[name]) / SR, 3), "use": u["use"],
                          "source": "usuario", "license": u["license"], "provided_by": u.get("provided_by", ""),
                          "ads": bool(u.get("ads"))}
            if cut:
                user_notes.append(f"{name}: cortado a {MAX_USER_S:g} s")
            if u.get("entrance") and name not in entrances:
                entrances.append(name)
        for name, sig in sounds.items():
            write_wav(out_dir / f"{name}.wav", sig)
        current = {"generator": "scripts/audio/sfx.py", "generator_version": GEN_VERSION, "sound": sound,
                   "recipes_hash": rhash, "user_hash": uhash,
                   "license": "Base y recetas: propio (sintetizado). Aportados: ver cada efecto",
                   "entrances": entrances, "sounds": meta}
        oslib.write_json(out_dir / "sfx.json", current)
    if added:
        oslib.emit({"ok": True, **added, "kit": oslib.rel(out_dir),
                    "next": f"Escúchalo: scripts/audio/sfx.py --channel {args.channel} --preview {added['added']}"})
    if args.preview:
        dst = oslib.ROOT / "work" / f"sfx-preview-{args.channel}.wav"
        preview(out_dir, args.preview, dst)
        oslib.emit({"ok": True, "preview": str(dst), "order": args.preview})
    if args.list:
        oslib.emit({"ok": True, "channel": args.channel, "entrances": current["entrances"],
                    "sounds": {k: {"use": v["use"], "source": v.get("source", "base"), "duration_s": v["duration_s"],
                                   "ads": v.get("ads", True)}
                               for k, v in sorted(current["sounds"].items())}})
    oslib.emit({"ok": True, "dir": oslib.rel(out_dir), "regenerated": not fresh or args.force,
                "sounds": sorted(current["sounds"]), "recipes": sorted(recipes)})


if __name__ == "__main__":
    main()
