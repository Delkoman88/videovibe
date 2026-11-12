"""Lógica pura del orquestador bin/edit: qué etapa toca, cuándo pausar y por qué.

No ejecuta nada: mira archivos, fechas, huellas y status.json de una pieza. bin/edit la usa en bucle:
`next_action()` → ejecutar → volver a preguntar. Se prueba en scripts/tests/test_edit.py.
"""
import datetime
import hashlib
import json
import re
from pathlib import Path

STAGES = ["ingesta", "transcripcion", "corte-en-papel", "corte-aplicado", "subtitulos",
          "composicion", "check", "revision", "render", "entrega"]
TOL = 1.0  # s de tolerancia al comparar fechas (aprobaciones con resolución de segundos)


# ------------------------------------------------------------------ utilidades de archivos

def mtime(p):
    p = Path(p)
    if not p.exists():
        return None
    if p.is_dir():
        ts = [f.stat().st_mtime for f in p.rglob("*") if f.is_file() and not f.name.startswith(".")]
        return max(ts) if ts else None
    return p.stat().st_mtime


def newer(a, b):
    """¿`a` es más nuevo que `b`? (None = no existe; algo que existe es más nuevo que nada)."""
    ta, tb = mtime(a), mtime(b)
    if ta is None:
        return False
    return tb is None or ta > tb + 1e-6


def fingerprint(paths):
    """Huella del contenido de archivos (texto/JSON por contenido; binarios por tamaño)."""
    h = hashlib.sha1()
    for p in sorted(Path(x) for x in paths):
        if not p.exists():
            h.update(f"{p}:missing".encode())
        elif p.suffix in (".html", ".json", ".md", ".srt", ".txt"):
            h.update(p.name.encode() + p.read_bytes())
        else:
            h.update(f"{p.name}:{p.stat().st_size}".encode())
    return h.hexdigest()[:16]


def hf_fingerprint(P):
    hf = Path(P) / "hf"
    files = [hf / "index.html", hf / "assets" / "plate.mp4", *sorted((hf / "compositions").glob("*.html")),
             *sorted((hf / "variables").glob("*.json"))]
    base = fingerprint(files)
    brolls = sorted((hf / "assets").glob("broll-*.mp4"))
    if not brolls:
        return base  # sin insertos, la misma huella de siempre: las piezas ya aprobadas siguen «al día»
    h = hashlib.sha1(base.encode())
    for f in brolls:
        h.update(f.name.encode())
        _file_hash(h, f)
    return h.hexdigest()[:16]


_VARS_ATTR = re.compile(r"""\sdata-composition-variables='[^']*'""")
_VAR_SRC = re.compile(r'(<[^>]*?)\ssrc="[^"]*"([^>]*\sdata-var-src="[^"]+")')


def _file_hash(h, p):
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)


def platform_fingerprint(P, plat):
    """Huella de lo que usa el render de UNA plataforma: la composición común (sin los valores por
    defecto de las variables, que cada plataforma sobreescribe), sus variables y los archivos que esas
    variables eligen (p. ej. la pista de música). Binarios por contenido, no por tamaño."""
    hf = Path(P) / "hf"
    h = hashlib.sha1()
    idx = hf / "index.html"
    if not idx.exists():
        return None
    html = _VAR_SRC.sub(r"\1\2", _VARS_ATTR.sub("", idx.read_text(encoding="utf-8")))
    h.update(html.encode())
    var_f = hf / "variables" / f"{plat}.json"
    vals = json.loads(var_f.read_text()) if var_f.exists() else {}
    h.update(json.dumps(vals, sort_keys=True).encode())
    chosen = {str(hf / v) for v in vals.values() if isinstance(v, str) and v.startswith("assets/")}
    files = [hf / "assets" / "plate.mp4", *sorted((hf / "compositions").glob("*.html"))]
    for f in sorted((hf / "assets").rglob("*")):
        if f.is_file() and not f.name.startswith(".") and f not in files:
            if f.name.startswith("music-") and str(f) not in chosen:
                continue  # pista de otra plataforma
            files.append(f)
    for f in files:
        h.update(str(f.relative_to(hf)).encode())
        if f.exists():
            _file_hash(h, f)
    return h.hexdigest()[:16]


def delivery_fingerprint(P, plats):
    """Huella de lo que se entrega: renders, textos y portadas de cada plataforma."""
    P = Path(P)
    return fingerprint([P / "renders" / f"{p}.mp4" for p in plats] + [P / "copy" / f"{p}.md" for p in plats]
                       + [P / "covers" / f"{p}.jpg" for p in plats])


def cut_fingerprint(P):
    """Huella de los segmentos del corte (cut-map.json): cambia solo si cambian cortes o tiempos."""
    f = Path(P) / "cut" / "cut-map.json"
    if not f.exists():
        return None
    segs = json.loads(f.read_text())["segments"]
    key = json.dumps([[x["src"], x["src_in"], x["src_out"]] for x in segs])
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def approval_ts(st, gate):
    a = st.get("approvals", {}).get(gate)
    if not a:
        return None
    return datetime.datetime.fromisoformat(a["at"]).timestamp()


# ------------------------------------------------------------------ datos de la pieza

def platforms(sb, channel_cfg):
    """Plataformas de la pieza: claves de storyboard.platforms; si no hay, las del canal."""
    if sb and sb.get("platforms"):
        return list(sb["platforms"])
    return list(channel_cfg.get("platforms", []))


def review_times(sb, duration, max_n=16, min_gap=0.5):
    """Momentos para la hoja de revisión: 0.6 s, mitad de cada tarjeta, 70 % de cada escena y el final."""
    cands = [0.6]
    for o in (sb or {}).get("overlays", []):
        cands.append((o["in"] + o["out"]) / 2)
    for s in (sb or {}).get("scenes", []):
        cands.append(s["in"] + 0.7 * (s["out"] - s["in"]))
    for clip in (sb or {}).get("broll", []):
        cands.append((clip["in"] + clip["out"]) / 2)
    cands.append(max(duration - 0.5, 0.1))
    out = []
    for t in sorted(min(max(c, 0.1), max(duration - 0.05, 0.1)) for c in cands):
        if not out or t - out[-1] >= min_gap:
            out.append(round(t, 2))
    if len(out) > max_n:  # conservar extremos y repartir el resto
        step = (len(out) - 1) / (max_n - 1)
        out = [out[round(i * step)] for i in range(max_n)]
    return out


def media_items(P):
    f = Path(P) / "media.json"
    if not f.exists():
        return []
    return [m for m in json.loads(f.read_text())["items"] if m.get("audio") and m.get("kind") != "mic"]


def media_ids(P):
    return [m["id"] for m in media_items(P)]


# ------------------------------------------------------------------ decisión

def stage_dirty(stage, P, st, plats):
    """¿Hace falta (re)ejecutar esta etapa? Devuelve (bool, motivo)."""
    P = Path(P)
    fp = st.get("fingerprints", {})
    if stage == "ingesta":
        if not (P / "raw").is_dir() or not any((P / "raw").iterdir()):
            return False, "sin material en raw/"
        return (not (P / "media.json").exists() or newer(P / "raw", P / "media.json")), "material nuevo en raw/"
    if stage == "transcripcion":
        # se compara con el archivo crudo de cada toma (media.json se reescribe en cada ingesta)
        for m in media_items(P):
            t = P / "transcript" / f"{m['id']}.json"
            mic = m.get("mic", {}).get("file")
            if not t.exists() or newer(P / m["file"], t) or (mic and newer(P / mic, t)):
                return True, "tomas sin transcribir"
        return False, ""
    if stage == "corte-en-papel":
        ts = [P / "transcript" / f"{i}.json" for i in media_ids(P)]
        cl = P / "cut" / "cut-list.json"
        return (not cl.exists() or any(newer(t, cl) for t in ts)), "transcripción más nueva que el corte"
    if stage == "corte-aplicado":
        cl, m = P / "cut" / "cut-list.json", P / "cut" / "master-cut.mp4"
        return (not m.exists() or newer(cl, m)), "corte modificado"
    if stage == "subtitulos":
        # dependen de los segmentos del corte, no del archivo de video (un re-render de color no los invalida)
        c = P / "captions" / "captions.json"
        if not c.exists():
            return True, "sin subtítulos"
        cap = json.loads(c.read_text())
        if cap.get("cut_fingerprint"):
            if cap["cut_fingerprint"] != cut_fingerprint(P):
                return True, "el corte cambió"
        else:  # piezas anteriores a la huella: misma duración = mismo corte
            cm = P / "cut" / "cut-map.json"
            if cm.exists() and abs(json.loads(cm.read_text())["duration_s"] - cap.get("duration_s", 0)) > 0.2:
                return True, "el corte cambió"
        if newer(P / "transcript" / "master-cut.json", c):
            return True, "transcripción corregida a mano"
        return False, ""
    if stage == "composicion":
        idx = P / "hf" / "index.html"
        ins = [P / "storyboard.json", P / "captions" / "captions.json", P / "cut" / "cut-map.json",
               P / "media.json",
               *[f for d in Path(P).resolve().parents if (d / "channel.json").exists()
                 for f in (d / "channel.json", d / "brand.json", d / "audio" / "music" / "library.json",
                           d / "audio" / "sfx" / "sfx.json")][:4]]
        return (not idx.exists() or any(newer(i, idx) for i in ins)), "storyboard, subtítulos, corte o sonido del canal cambiaron"
    if stage == "check":
        return fp.get("check") != hf_fingerprint(P), "composición sin verificar"
    if stage == "revision":
        draft = P / "renders" / f"draft-{plats[0]}.mp4" if plats else None
        stale = fp.get("revision") != hf_fingerprint(P)
        return (stale or not draft or not draft.exists()), "hoja de revisión y borrador desactualizados"
    if stage == "render":
        return any(fp.get(f"render:{p}") != platform_fingerprint(P, p) or not (P / "renders" / f"{p}.mp4").exists() for p in plats), \
            "composición más nueva que el render"
    if stage == "entrega":
        d = st.get("delivery")
        missing = not d or not (Path(d) / ".videovibe-delivery.json").exists()
        return (fp.get("entrega") != delivery_fingerprint(P, plats) or st.get("stage") != "entregable" or missing), \
            "entrega sin verificar o sin carpeta de entregas"
    raise KeyError(stage)


MEDIA_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".aiff",
             ".aif", ".ogg", ".png", ".jpg", ".jpeg", ".webp", ".heic"}
# Campos ★ del brief (templates/brief.md) y nombres equivalentes aceptados.
BRIEF_REQUIRED = {"objetivo": ("objetivo",), "audiencia": ("audiencia", "audiencia principal"),
                  "material": ("material", "material disponible"),
                  "llamada a la acción": ("llamada a la acción", "llamada a la accion", "cta")}


def brief_missing(text):
    """Campos ★ del brief sin respuesta. Una respuesta va en la misma línea, después de los dos puntos."""
    found = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("-"):
            continue
        clean = re.sub(r"<!--.*?-->", "", line.replace("*", "").replace("★", "")).strip().lstrip("-").strip()
        m = re.match(r"^([^:(]+?)\s*(?:\([^)]*\))?\s*:\s*(.*)$", clean)
        if not m:
            continue
        key, ans = m.group(1).strip().lower(), m.group(2).strip()
        for field, names in BRIEF_REQUIRED.items():
            if key in names:
                found[field] = found.get(field) or bool(ans)
    return [f for f in BRIEF_REQUIRED if not found.get(f)]


def gate(name, P, st):
    """Pausas. Devuelve None si se puede seguir, o {pending, reason, next} si hay que parar."""
    if name == "input":
        raw = P / "raw"
        if not raw.is_dir() or not any(f.suffix.lower() in MEDIA_EXT for f in raw.iterdir() if f.is_file()):
            return {"pending": "material", "reason": "La pieza no tiene material en raw/.",
                    "next": f"Pon los archivos (tomas, audio del micrófono, B-roll…) en {raw}/ y vuelve a correr "
                            "bin/edit. Para piezas nuevas: bin/new-piece <canal> <slug> --from <archivos>."}
        return None
    if name == "brief":
        if st.get("approvals", {}).get("A"):
            return None  # piezas ya cortadas y aprobadas: el brief ya se usó
        f = P / "brief.md"
        miss = brief_missing(f.read_text(encoding="utf-8")) if f.exists() else list(BRIEF_REQUIRED)
        if miss:
            return {"pending": "brief", "reason": f"El brief está incompleto: falta {', '.join(miss)}.",
                    "next": f"Pregúntale a la persona del canal y escribe las respuestas en {f} (regla universal 1: "
                            "nada creativo sin brief; plantilla: templates/brief.md). Luego bin/edit <pieza>."}
        return None
    P = Path(P)
    if name == "A":
        cl = P / "cut" / "cut-list.json"
        ts = approval_ts(st, "A")
        if ts is None:
            return {"pending": "aprobación A", "reason": "El corte no está aprobado.",
                    "next": "Muestra cut/PAPER-CUT.md a la persona del canal. Aplica sus notas en cut/cut-list.json "
                            "y, cuando apruebe: bin/status <pieza> --approve A; luego bin/edit <pieza>."}
        if mtime(cl) and mtime(cl) > ts + TOL:
            return {"pending": "aprobación A", "reason": "cut/cut-list.json cambió después de aprobarse el corte.",
                    "next": "Vuelve a mostrar PAPER-CUT.md con los cambios y registra la nueva aprobación A."}
    if name == "storyboard":
        if not (P / "storyboard.json").exists():
            return {"pending": "storyboard", "reason": "Falta el plan visual (storyboard.json).",
                    "next": "Escribe storyboard.json según docs/storyboard.md y docs/formats.md (estilo del canal en "
                            "style.md/rhythm.md/brand.json; palabras en captions/captions.json). Valídalo con "
                            "scripts/pipeline/storyboard.py --project <pieza> (todos los errores juntos). Luego bin/edit <pieza>."}
    if name == "B":
        ts = approval_ts(st, "B")
        sources = [P / "storyboard.json", P / "captions" / "captions.json"]
        sb = json.loads((P / "storyboard.json").read_text()) if (P / "storyboard.json").exists() else {}
        if sb.get("broll"):
            sources.append(P / "media.json")
            if (P / "media.json").exists():
                media = {m["id"]: m for m in json.loads((P / "media.json").read_text())["items"]}
                sources += [P / media[c["source"]]["file"] for c in sb["broll"] if c.get("source") in media]
        if ts is None:
            return {"pending": "aprobación B", "reason": "El plan visual no está aprobado.",
                    "next": "Muestra snaps/contact-sheet*.jpg, snaps/phone-*.png y el borrador en renders/ a la persona del canal. "
                            "Aplica sus notas en storyboard.json (bin/edit vuelve a componer) y, cuando apruebe: "
                            "bin/status <pieza> --approve B; luego bin/edit <pieza>."}
        changed = [s.name for s in sources if mtime(s) and mtime(s) > ts + TOL]
        if changed:
            return {"pending": "aprobación B", "reason": f"{', '.join(changed)} cambió después de aprobarse el plan.",
                    "next": "Muestra la hoja y el borrador nuevos y registra la nueva aprobación B."}
    return None


def missing_deliverables(P, plats):
    P = Path(P)
    miss = [f"copy/{p}.md" for p in plats if not (P / "copy" / f"{p}.md").exists()]
    miss += [f"covers/{p}.jpg" for p in plats if not (P / "covers" / f"{p}.jpg").exists()]
    return miss


def next_action(P, st, plats, forced=(), has_storyboard=None):
    """Siguiente paso: {"run": etapa, "why": …} | {"pause": {...}} | {"done": True}."""
    P = Path(P)
    order = [("gate", "input"), ("gate", "brief"), ("ingesta",), ("transcripcion",), ("corte-en-papel",), ("gate", "A"), ("corte-aplicado",),
             ("subtitulos",), ("gate", "storyboard"), ("composicion",), ("check",), ("revision",),
             ("gate", "B"), ("render",), ("entrega",)]
    for item in order:
        if item[0] == "gate":
            g = gate(item[1], P, st)
            if g:
                return {"pause": g}
            continue
        stage = item[0]
        if stage in forced:
            return {"run": stage, "why": "forzado con --from-stage"}
        dirty, why = stage_dirty(stage, P, st, plats)
        if dirty:
            if stage == "entrega":
                miss = missing_deliverables(P, plats)
                if miss:
                    return {"pause": {"pending": "copy/portada", "reason": f"Faltan entregables: {', '.join(miss)}.",
                                      "next": "Redacta el copy por plataforma (copy/<plat>.md, según presets y CHANNEL.md) "
                                              "y la portada: scripts/pipeline/cover.py --project <pieza> --platform <plat>. Luego bin/edit <pieza>."}}
            return {"run": stage, "why": why}
    return {"done": True}


def forced_from(stage):
    if stage not in STAGES:
        raise KeyError(f"etapa desconocida: {stage} (etapas: {', '.join(STAGES)})")
    return STAGES[STAGES.index(stage):]
