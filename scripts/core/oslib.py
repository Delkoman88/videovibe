"""Utilidades compartidas por los scripts del pipeline (sin dependencias salvo numpy)."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / ".venv" / "bin" / "python"
SR = 16000  # frecuencia de análisis


def _ffmpeg_bin():
    """ffmpeg para procesar video: $VIDEOVIBE_FFMPEG (o el antiguo $OSE_FFMPEG); si no, ffmpeg-full de Homebrew
    (macOS, trae zscale para HDR); si no, el del PATH (en Linux el de la distribución suele traer zscale)."""
    env = os.environ.get("VIDEOVIBE_FFMPEG") or os.environ.get("OSE_FFMPEG")
    if env:
        return env
    for prefix in ("/opt/homebrew", "/usr/local"):
        full = Path(prefix) / "opt" / "ffmpeg-full" / "bin" / "ffmpeg"
        if full.exists():
            return str(full)
    return "ffmpeg"


FFMPEG = _ffmpeg_bin()


def ffmpeg_major(version_line):
    """Versión mayor de ffmpeg desde la primera línea de `ffmpeg -version` (p. ej. «ffmpeg version 9.0.2»,
    «ffmpeg version 6.1.1-3ubuntu5», «ffmpeg version n7.1»). None si no se reconoce (build de desarrollo)."""
    import re
    m = re.search(r"version\s+n?(\d+)\.", version_line)
    return int(m.group(1)) if m else None


_FILTER_ARGS = {}


def filter_script_args(path):
    """Argumentos para pasar un grafo de filtros desde archivo: ffmpeg ≥ 7 usa `-/filter_complex <archivo>`
    (ffmpeg 9 quitó -filter_complex_script); ffmpeg 6 (p. ej. Ubuntu 24.04) solo entiende -filter_complex_script."""
    if FFMPEG not in _FILTER_ARGS:
        r = subprocess.run([FFMPEG, "-hide_banner", "-version"], capture_output=True, text=True)
        major = ffmpeg_major((r.stdout or "").splitlines()[0] if r.stdout else "")
        _FILTER_ARGS[FFMPEG] = "-filter_complex_script" if major is not None and major < 7 else "-/filter_complex"
    return [_FILTER_ARGS[FFMPEG], str(path)]
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}  # HLG y PQ
# HDR → SDR BT.709 (curva hable: tono de piel natural; el grado de color posterior levanta la exposición)
TONEMAP_SDR = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
               "zscale=t=bt709:m=bt709:r=tv")


def has_filter(name):
    out = subprocess.run([FFMPEG, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if len(line.split()) > 1)


def ensure_venv():
    """Re-ejecuta el script con el python del .venv del repo si el actual no tiene numpy."""
    try:
        import numpy  # noqa: F401
        return
    except ImportError:
        pass
    if VENV_PY.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
    die("numpy no disponible. Corre bin/doctor y INSTALL.es.md.", 2)


def die(msg, code=2):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        die(f"falló: {' '.join(map(str, cmd[:3]))}…\n{r.stderr[-1500:]}", 2)
    return r.stdout


ENGINE_CHANNELS = ROOT / "channels"  # los del motor: _template y el canal de ejemplo


def _configured_dir(env_var, key, default):
    """Carpeta configurable: $<env_var> > local.json → <key> > default (relativas, respecto al repo)."""
    env = os.environ.get(env_var)
    if env:
        return Path(env).expanduser().resolve()
    local = ROOT / "local.json"
    if local.exists():
        d = json.loads(local.read_text(encoding="utf-8")).get(key)
        if d:
            p = Path(d).expanduser()
            return (p if p.is_absolute() else ROOT / p).resolve()
    return default


def _channels_root():
    """Carpeta de los canales de la persona: $VIDEOVIBE_CHANNELS > local.json → channels_dir > channels/ del repo.
    Así los canales personales pueden vivir en otro repo (privado) y el motor en uno público."""
    return _configured_dir("VIDEOVIBE_CHANNELS", "channels_dir", ENGINE_CHANNELS)


CHANNELS = _channels_root()
# Carpetas de la persona, fáciles de encontrar en la raíz del repo (fuera de git):
# videos originales: $VIDEOVIBE_INPUT / local.json → input_dir (los nombres anteriores VIDEOVIBE_MATERIAL y
# material_dir siguen valiendo, para configuraciones existentes)
MATERIAL = _configured_dir("VIDEOVIBE_INPUT", "input_dir",
                           _configured_dir("VIDEOVIBE_MATERIAL", "material_dir", ROOT / "input"))
DELIVERIES = _configured_dir("VIDEOVIBE_DELIVERIES", "deliveries_dir", ROOT / "deliveries")  # videos finales


def channel_roots():
    """Carpetas donde buscar canales, en orden: los de la persona y luego los del motor."""
    return [CHANNELS] + ([ENGINE_CHANNELS] if ENGINE_CHANNELS != CHANNELS else [])


def rel(path):
    """Ruta legible: relativa al repo si está dentro; si no (canales en otra carpeta), con ~."""
    path = Path(path)
    if path.is_relative_to(ROOT):
        return str(path.relative_to(ROOT))
    home = Path.home()
    return "~/" + str(path.relative_to(home)) if path.is_relative_to(home) else str(path)


def channel_path(cid):
    """Carpeta del canal `cid` (primero en los de la persona, luego en los del motor)."""
    for root in channel_roots():
        if (root / cid / "channel.json").exists():
            return root / cid
    return CHANNELS / cid
LANG_DIR = ROOT / "lang"
CHANNEL_FILES = ["channel.json", "CHANNEL.md", "style.md", "rhythm.md", "topics.md", "brand.json", "vocabulary.txt"]


def project_dir(p):
    """Carpeta de una pieza. Acepta una ruta (absoluta o relativa) o la forma corta `<canal>/<pieza>`."""
    d = Path(p)
    if not d.is_absolute():
        cands = [Path.cwd() / d, ROOT / d]
        if len(d.parts) == 2:
            cands.append(channel_path(d.parts[0]) / "projects" / d.parts[1])
        d = next((c for c in cands if c.is_dir()), cands[0])
    if not d.is_dir():
        die(f"no existe la carpeta del proyecto: {p} (usa channels/<canal>/projects/<pieza> o <canal>/<pieza>)")
    return d.resolve()


def channel_dir(start):
    """Sube desde `start` (una pieza o carpeta del canal) hasta encontrar channel.json."""
    d = Path(start).resolve()
    for cand in [d, *d.parents]:
        if (cand / "channel.json").exists():
            return cand
    die(f"{start} no está dentro de un canal (no encuentro channel.json). Ver docs/channels.md")


def load_lang(code):
    f = LANG_DIR / f"{code}.json"
    if not f.exists():
        die(f"idioma sin paquete: {code}. Crea lang/{code}.json (ver lang/es.json)")
    return read_json(f)


def load_channel(start):
    """Contexto del canal de una pieza: {dir, config, brand, vocab, lang, person}."""
    cdir = channel_dir(start)
    missing = [f for f in CHANNEL_FILES if not (cdir / f).exists()]
    if missing:
        die(f"canal incompleto {cdir.name}: faltan {missing} (bin/doctor --channel {cdir.name})")
    cfg = read_json(cdir / "channel.json")
    vocab = [l.strip() for l in (cdir / "vocabulary.txt").read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    persons = cfg.get("persons") or [{"name": "la persona en cámara", "short": "la persona en cámara"}]
    return {"dir": cdir, "id": cfg["id"], "name": cfg["name"], "config": cfg,
            "brand": read_json(cdir / "brand.json"), "vocab": vocab,
            "lang": load_lang(cfg["language"]), "person": persons[0]}


def font_file(ch, key):
    """Ruta del archivo de fuente `display`/`mono` del canal: <canal>/fonts/ y luego assets/fonts/."""
    name = ch["brand"]["fonts"][key]["file"]
    for d in (ch["dir"] / "fonts", ROOT / "assets" / "fonts"):
        if (d / name).exists():
            return d / name
    die(f"fuente {name} no encontrada en {ch['dir'] / 'fonts'} ni en assets/fonts")


def update_status(P, stage, **info):
    """Registra en <pieza>/status.json la etapa alcanzada (lo leen bin/status y cualquier agente)."""
    import datetime
    f = Path(P) / "status.json"
    st = read_json(f) if f.exists() else {"stage": None, "history": [], "approvals": {}, "renders": {}}
    now = datetime.datetime.now().isoformat(timespec="seconds")
    st["stage"] = stage
    st["updated"] = now
    st["history"].append({"stage": stage, "at": now, **({"info": info} if info else {})})
    st["history"] = st["history"][-40:]
    if "renders" in info:
        st["renders"].update(info["renders"])
    if "delivery" in info:
        st["delivery"] = info["delivery"]  # carpeta de entregas (scripts/pipeline/deliver.py)
    write_json(f, st)


def load_preset(name):
    f = ROOT / "presets" / f"{name}.json"
    if not f.exists():
        die(f"preset desconocido: {name}")
    return read_json(f)


def ffprobe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def load_audio(path, sr=SR):
    """Audio mono float32 a `sr` Hz desde cualquier archivo que lea ffmpeg."""
    import numpy as np
    raw = subprocess.run(
        [FFMPEG, "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def rms_db(audio, sr=SR, hop_s=0.01, win_s=0.03):
    """Energía en dBFS por cuadro de `hop_s` segundos."""
    import numpy as np
    hop, win = int(sr * hop_s), int(sr * win_s)
    if len(audio) < win:
        return np.full(1, -120.0)
    n = 1 + (len(audio) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = audio[idx]
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-12)


def speech_islands(audio, sr=SR, hop_s=0.01, min_silence_s=0.15, min_speech_s=0.08, margin_db=14.0):
    """Intervalos [inicio, fin] (s) con voz, por umbral de energía relativo al ruido de fondo."""
    import numpy as np
    db = rms_db(audio, sr, hop_s)
    floor = float(np.percentile(db, 10))
    peak = float(np.percentile(db, 98))
    thr = max(floor + margin_db, peak - 40.0, -60.0)
    voiced = db > thr
    islands, start = [], None
    for i, v in enumerate(voiced):
        if v and start is None:
            start = i
        elif not v and start is not None:
            islands.append([start, i]); start = None
    if start is not None:
        islands.append([start, len(voiced)])
    merged = []  # une huecos cortos
    for a, b in islands:
        if merged and (a - merged[-1][1]) * hop_s < min_silence_s:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    out = [[round(a * hop_s, 3), round(b * hop_s + 0.02, 3)] for a, b in merged if (b - a) * hop_s >= min_speech_s]
    return out, {"floor_db": round(floor, 1), "threshold_db": round(thr, 1)}


def quietest_point(db, t_lo, t_hi, hop_s=0.01):
    """Instante (s) de menor energía dentro de [t_lo, t_hi]; útil para colocar cortes."""
    import numpy as np
    a, b = max(0, int(t_lo / hop_s)), min(len(db), int(t_hi / hop_s) + 1)
    if b <= a:
        return t_lo
    return round((a + int(np.argmin(db[a:b]))) * hop_s, 3)
