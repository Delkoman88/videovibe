"""Huellas por contenido y evidencia de etapas/aprobaciones (ADR 0036).

Esquema 3 (actual):
- Cada archivo entra a la huella con una etiqueta relativa (`piece:`, `channel:`, `engine:`, `ext:`),
  nunca con su ruta absoluta: mover la carpeta de canales o cambiar de máquina no invalida nada.
- Las etapas editables (ingesta, transcripción, corte en papel, subtítulos) dependen solo del
  contenido de la pieza y del canal que las afecta, no del código del motor.
- La aprobación B depende del contenido de la pieza y del HTML compilado, no del código del motor:
  si el motor cambia lo que se ve, cambia el HTML y B se invalida igual.

El esquema 2 (rutas absolutas, motor en todas las huellas) se conserva solo para `restamp`, que
migra la evidencia guardada sin rehacer trabajo.
"""
import copy
import hashlib
import json
import os
from pathlib import Path

from scripts.core import oslib
from scripts.core.stages import EDITABLE, HF, STAGES

SCHEME = 3


# ------------------------------------------------------------------ huellas de archivos

def channel_dir(P):
    for d in Path(P).resolve().parents:
        if (d / "channel.json").exists():
            return d
    return None


def label(p, P=None):
    """Nombre estable de un archivo dentro de una huella (sin ruta absoluta)."""
    p = Path(p).resolve()
    bases = []
    if P is not None:
        bases.append(("piece", Path(P).resolve()))
        ch = channel_dir(P)
        if ch:
            bases.append(("channel", ch))
    bases.append(("engine", oslib.ROOT.resolve()))
    for kind, base in bases:
        if p.is_relative_to(base):
            return f"{kind}:{p.relative_to(base).as_posix()}"
    return f"ext:{p.name}"


def digest(paths, P=None):
    """SHA-256 del contenido de los archivos, cada uno con su etiqueta relativa."""
    h = hashlib.sha256()
    for name, p in sorted({label(p, P): Path(p) for p in paths}.items()):
        h.update(name.encode())
        if not p.is_file():
            h.update(b":missing")
            continue
        with p.open("rb") as f:
            for b in iter(lambda: f.read(1048576), b""):
                h.update(b)
    return h.hexdigest()


LEGACY_INTEGRITY = Path(__file__).with_name("legacy") / "integrity-0.13.1.py.txt"


def legacy_digest(paths):
    """Esquema 2 (v0.13.1): rutas absolutas. Solo para migrar evidencia guardada.

    v0.13.1 metía su propio integrity.py en cada huella: se usan sus bytes originales (guardados en
    legacy/) para que la evidencia de entonces se pueda reconocer.
    """
    me = Path(__file__).resolve()
    h = hashlib.sha256()
    for p in sorted({Path(p).resolve() for p in paths}):
        h.update(str(p).encode())
        if p == me:
            h.update(LEGACY_INTEGRITY.read_bytes())
            continue
        if not p.is_file():
            h.update(b":missing")
            continue
        with p.open("rb") as f:
            for b in iter(lambda: f.read(1048576), b""):
                h.update(b)
    return h.hexdigest()


def legacy_fingerprint(paths):
    """Esquema 1 (hasta v0.13.0, editlib.fingerprint): texto por contenido, binarios por tamaño."""
    h = hashlib.sha1()
    for p in sorted(Path(x) for x in paths):
        if not p.exists():
            h.update(f"{p}:missing".encode())
        elif p.suffix in (".html", ".json", ".md", ".srt", ".txt"):
            h.update(p.name.encode() + p.read_bytes())
        else:
            h.update(f"{p.name}:{p.stat().st_size}".encode())
    return h.hexdigest()[:16]


def hasher(P, scheme=SCHEME):
    """Función de huella de archivos para un esquema."""
    if scheme == 1:
        return legacy_fingerprint
    if scheme == 2:
        return legacy_digest
    return lambda paths: digest(paths, P)


def digest_bytes(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def files(P, *names):
    out = []
    for name in names:
        p = Path(P) / name
        if p.is_dir():
            out.extend(sorted(x for x in p.rglob("*") if x.is_file() and not x.name.startswith(".")
                              and "__pycache__" not in x.parts))
        else:
            out.append(p)
    return out


def _not_master(paths):
    return [x for x in paths if not x.name.startswith("master-cut")]


def _combine(h, paths, metadata=()):
    return hashlib.sha256((h(paths) + json.dumps(list(metadata), sort_keys=True)).encode()).hexdigest()


# ------------------------------------------------------------------ entradas por etapa (esquema 3)

def _language(ch):
    if not ch or not (ch / "channel.json").exists():
        return None
    cfg = oslib.read_json(ch / "channel.json")
    return cfg.get("language") or cfg.get("lang")


def _lang_file(ch):
    code = _language(ch)
    code = code.get("code") if isinstance(code, dict) else code
    return [oslib.ROOT / "lang" / f"{code}.json"] if code else []


def _composition_content(P, ch, relabel=True):
    """Contenido de la pieza y del canal que usa la composición (sin código del motor).
    `relabel=False` reproduce los metadatos del esquema 2 (con rutas absolutas)."""
    paths = files(P, "storyboard.json", "captions/captions.json", "captions/master.srt", "cut/master-cut.mp4",
                  "cut/cut-map.json", "media.json", "raw")
    metadata = []
    if not ch:
        return paths, metadata
    paths += files(ch, "channel.json", "brand.json", "fonts")
    sb = oslib.read_json(P / "storyboard.json") if (P / "storyboard.json").exists() else {}
    cfg = oslib.read_json(ch / "channel.json")
    audio = sb.get("audio", {})
    music = audio.get("music") or {}
    library = ch / "audio/music/library.json"
    if music and library.exists():
        chosen = {music.get("track"), music.get("ads_track")}
        for track in oslib.read_json(library).get("tracks", []):
            if track["id"] in chosen or (not music.get("ads_track") and track.get("ads")):
                metadata.append(track)
                paths.append(ch / "audio/music" / track["file"])
    kit = ch / "audio/sfx/sfx.json"
    if kit.exists() and (audio.get("sfx") or audio.get("sfx_auto") or sb.get("transitions")):
        data = oslib.read_json(kit)
        metadata.append(data)
        paths += [ch / "audio/sfx" / v["file"] for v in data.get("sounds", {}).values()]
    import formats
    from scripts.core import assetlib
    formats.load_packs(cfg.get("format_packs", []))
    for _, kind, ident in formats.uses(sb):
        item = assetlib.item(kind, ident, ch)
        if item:
            paths.append(Path(item["path"]))
            if relabel:
                item = {**item, "path": label(item["path"], P)}  # sin ruta absoluta en los metadatos
        metadata.append(item)
    for scene in sb.get("scenes", []):
        if scene.get("params", {}).get("file"):
            paths.append(P / scene["params"]["file"])
    return paths, metadata


def dependencies():
    """Versiones e integridad de las dependencias de npm (package-lock sin la versión del propio motor):
    publicar una versión nueva de VideoVibe no invalida nada; cambiar HyperFrames o una librería sí."""
    lock = oslib.ROOT / "package-lock.json"
    if not lock.exists():
        return {}
    packages = oslib.read_json(lock).get("packages", {})
    return {k: [v.get("version"), v.get("integrity")] for k, v in sorted(packages.items()) if k}


def _transcription_extras(P, ch):
    """Modelos de whisper y VAD, y el audio aportado de cada toma."""
    model = os.environ.get("VIDEOVIBE_WHISPER_MODEL") or oslib.ROOT / "models/ggml-large-v3-turbo-q5_0.bin"
    paths = [Path(model), oslib.ROOT / "models/ggml-silero-v5.1.2.bin"]
    if (P / "media.json").exists():
        paths += [P / i["audio"] for i in oslib.read_json(P / "media.json").get("items", []) if i.get("audio")]
    return paths, []


HOOKS = {"transcripcion": _transcription_extras, "composicion": _composition_content}


def _paths(P, stage, engine=True):
    """(archivos, metadatos) de los que depende una etapa en el esquema 3, según stages.STAGES."""
    spec = STAGES[stage]
    P = Path(P)
    ch = channel_dir(P)
    paths = files(P, *spec.get("content", []))
    if spec.get("drop_master"):
        paths = _not_master(paths)
    metadata = []
    if ch:
        paths += files(ch, *spec.get("channel", []))
        if spec.get("language"):
            metadata.append({"language": _language(ch)})
        if spec.get("lang_file"):
            paths += _lang_file(ch)
    if spec.get("hook"):
        extra, extra_meta = HOOKS[spec["hook"]](P, ch)
        paths += extra
        metadata += extra_meta
    if engine and not spec["editable"]:
        paths += files(oslib.ROOT, *spec.get("engine", []))
        if spec.get("script"):
            paths.append(oslib.ROOT / "scripts/pipeline" / f"{spec['script']}.py")
        if spec.get("npm"):
            metadata.append({"dependencies": dependencies()})
    return paths, metadata


def inputs(P, stage, scheme=SCHEME):
    if scheme < 3:
        return _inputs_v2(P, stage)
    paths, metadata = _paths(P, stage)
    return _combine(hasher(P), paths, metadata)


def outputs(P, stage, scheme=SCHEME):
    P = Path(P)
    paths = files(P, *STAGES[stage]["outputs"])
    if stage == "entrega":
        from scripts.core.state import load
        destination = load(P).get("delivery")
        if destination:
            paths += files(Path(destination), ".") + [Path(destination) / ".videovibe-delivery.json"]
    if stage == "revision":
        paths += list((P / "renders").glob("draft-*.mp4"))
    if stage == "transcripcion":
        paths = _not_master(paths)
    return (legacy_digest if scheme < 3 else hasher(P))(paths)


def approval_inputs(P, gate, scheme=SCHEME):
    P = Path(P)
    h = legacy_digest if scheme < 3 else hasher(P)
    if gate == "A":
        return h(_not_master(files(P, "cut/cut-list.json", "raw", "transcript", "media.json")))
    if scheme < 3:
        return hashlib.sha256((_inputs_v2(P, "composicion") + outputs(P, "composicion", 2)).encode()).hexdigest()
    paths, metadata = _paths(P, "composicion", engine=False)
    return hashlib.sha256((_combine(h, paths, metadata) + outputs(P, "composicion")).encode()).hexdigest()


def valid(P, gate, st):
    from scripts.core.reviewlib import fingerprint
    a = st.get("approvals", {}).get(gate, {})
    return (isinstance(a, dict) and a.get("version") == 2 and a.get("inputs") == approval_inputs(P, gate)
            and a.get("presentation") == fingerprint(P, gate))


def verification(P, plats, scheme=SCHEME):
    P = Path(P)
    paths = files(P, "storyboard.json", "cut/cut-map.json", "captions", "copy", "covers", "assets.md", "brief.md")
    paths += [P / "renders" / f"{p}.mp4" for p in plats] + [oslib.ROOT / "presets" / f"{p}.json" for p in plats]
    return (legacy_digest if scheme < 3 else hasher(P))(paths)


def stable_inputs(P, stage, protect_transcript=False):
    """Entradas externas que no puede producir la propia etapa."""
    if stage == "subtitulos":
        # La etapa escribe transcript/master-cut.json; se protege solo cuando lo reutiliza.
        paths = files(P, "cut/master-cut.mp4", "cut/cut-map.json")
        if protect_transcript:
            paths += files(P, "transcript/master-cut.json")
        ch = channel_dir(P)
        if ch:
            paths += files(ch, "channel.json", "brand.json", "vocabulary.txt")
        return digest(paths + files(oslib.ROOT, "lang", "scripts/pipeline/captions.py"), P)
    return inputs(P, stage)


# ------------------------------------------------------------------ migración de evidencia

def _inputs_v2(P, stage):
    """Entradas del esquema 2, tal como las calculaba v0.13.1. Solo para restamp."""
    P = Path(P)
    groups = {"ingesta": ["raw"], "transcripcion": ["raw", "media.json"],
              "corte-en-papel": ["transcript", "media.json"],
              "corte-aplicado": ["cut/cut-list.json", "raw", "media.json", "transcript"],
              "subtitulos": ["cut/cut-map.json", "transcript"],
              "composicion": ["storyboard.json", "captions/captions.json", "captions/master.srt",
                              "cut/master-cut.mp4", "cut/cut-map.json", "media.json", "raw"],
              "check": HF, "revision": HF, "render": HF,
              "entrega": ["renders", "copy", "covers", "captions/master.srt", "brief.md", "assets.md"]}
    paths = files(P, *groups[stage])
    if stage in ("transcripcion", "corte-en-papel", "corte-aplicado"):
        paths = _not_master(paths)
    ch = channel_dir(P)
    if ch and stage in ("transcripcion", "corte-en-papel", "corte-aplicado", "subtitulos"):
        paths += files(ch, "channel.json", "brand.json", "vocabulary.txt")
        paths += files(oslib.ROOT, "lang", "presets", "scripts/core/cutlib.py")
    if stage == "transcripcion":
        paths += [Path(os.environ.get("VIDEOVIBE_WHISPER_MODEL") or oslib.ROOT / "models/ggml-large-v3-turbo-q5_0.bin"),
                  oslib.ROOT / "models/ggml-silero-v5.1.2.bin"]
        if (P / "media.json").exists():
            paths += [P / i["audio"] for i in oslib.read_json(P / "media.json").get("items", []) if i.get("audio")]
    metadata = []
    if stage == "composicion":
        if ch:
            content, metadata = _composition_content(P, ch, relabel=False)
            paths += content
        paths += files(oslib.ROOT, "formats", "presets", "scripts/composer")
    v2_scripts = {"ingesta": "ingest", "transcripcion": "transcribe", "corte-en-papel": "paper_cut",
                  "corte-aplicado": "apply_cut", "subtitulos": "captions", "composicion": "compose"}
    paths += [oslib.ROOT / "scripts/pipeline" / (v2_scripts.get(stage, stage) + ".py")]
    paths += [oslib.ROOT / "scripts/core/integrity.py", oslib.ROOT / "package-lock.json"]
    return _combine(legacy_digest, paths, metadata)


def restamp(P, st, plats):
    """Migra la evidencia guardada al esquema 3 sin rehacer trabajo. Devuelve (estado, cambios).

    Cada huella guardada se recalcula con el algoritmo con que se escribió; si coincide, se
    reemplaza por la del esquema 3. Si no coincide, se deja: el contenido cambió de verdad y la
    etapa o aprobación quedará pendiente como antes. No escribe: quien llama guarda el estado.
    Las piezas sin recibos de etapa (anteriores a v0.13.1) reciben recibo solo en las etapas que la
    lógica anterior consideraba al día, salvo la composición, que se reconstruye (es barata y, si
    el HTML sale igual, no invalida nada).
    """
    from scripts.core import editlib
    st = copy.deepcopy(st)
    if st.get("digest_scheme") == SCHEME:
        return st, []
    P = Path(P)
    changes = []
    fp = st.setdefault("fingerprints", {})
    for key, fn in (("check", editlib.hf_fingerprint), ("revision", editlib.hf_fingerprint)):
        if fp.get(key) and fp[key] in (fn(P, scheme=1), fn(P, scheme=2)):
            fp[key] = fn(P)
            changes.append(f"fingerprints.{key}")
    if fp.get("entrega") and fp["entrega"] in (editlib.delivery_fingerprint(P, plats, scheme=1),
                                               editlib.delivery_fingerprint(P, plats, scheme=2)):
        fp["entrega"] = editlib.delivery_fingerprint(P, plats)
        changes.append("fingerprints.entrega")
    receipts = st.setdefault("stages", {})
    for stage in editlib.STAGES:
        r = receipts.get(stage)
        if r and r.get("version") == 3 and r.get("status") not in ("running", "failed"):
            same_in = r.get("inputs") == inputs(P, stage, 2)
            same_out = stage in EDITABLE or r.get("outputs") == outputs(P, stage, 2)
            if same_in and same_out:
                r.update(inputs=inputs(P, stage), outputs=outputs(P, stage))
                changes.append(f"stages.{stage}")
        elif not r and stage != "composicion" and not editlib.legacy_dirty(stage, P, st, plats)[0]:
            receipts[stage] = {"version": 3, "platforms": list(plats), "inputs": inputs(P, stage),
                               "outputs": outputs(P, stage), "migrated": True}
            changes.append(f"stages.{stage} (nuevo)")
    for gate, a in st.get("approvals", {}).items():
        if isinstance(a, dict) and a.get("version") == 2 and a.get("inputs") == approval_inputs(P, gate, 2):
            a["inputs"] = approval_inputs(P, gate)
            changes.append(f"approvals.{gate}")
    for gate, r in st.get("reviews", {}).items():
        if r.get("inputs") and r["inputs"] == approval_inputs(P, gate, 2):
            r["inputs"] = approval_inputs(P, gate)
            changes.append(f"reviews.{gate}")
    v = st.get("verification") or {}
    if v.get("fingerprint") and v["fingerprint"] == verification(P, v.get("platforms", []), 2):
        v["fingerprint"] = verification(P, v["platforms"])
        changes.append("verification")
    st["digest_scheme"] = SCHEME
    return st, changes
