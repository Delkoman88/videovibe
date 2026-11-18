"""Tabla única de etapas del pipeline: qué script corre, si se edita a mano, de qué depende y qué produce.

Solo datos. La leen `integrity` (huellas de entradas/salidas), `editlib` (orden y decisiones) y `bin/edit`
(cómo ejecutar cada etapa). Cambiar una etapa es cambiar su fila aquí (ADR 0036).

Campos:
  script     módulo de scripts/pipeline/ que la ejecuta (None: la ejecuta bin/edit con HyperFrames)
  platform   argumentos de plataforma del script: "first" (--platform de la primera), "all" o None
  editable   sus documentos se corrigen a mano: solo se rehace si cambian sus fuentes, y su huella no
             incluye código del motor
  outputs    rutas de la pieza que produce
  content    rutas de la pieza de las que depende
  drop_master  quitar de `content` los archivos master-cut* (los produce una etapa posterior)
  channel    archivos del canal de los que depende
  language   el idioma del canal (channel.json → language) entra a la huella
  lang_file  el paquete de idioma lang/<código>.json entra a la huella
  hook       dependencias que no caben en una lista: "transcripcion" (modelos y audio por toma) o
             "composicion" (música, efectos y recursos que pide el storyboard)
  engine     rutas del motor de las que depende (solo etapas no editables; el script se agrega solo)
  npm        las dependencias de npm (package-lock sin la versión de VideoVibe) entran a la huella
"""

HF = ["hf/index.html", "hf/compositions", "hf/assets", "hf/variables"]

STAGES = {
    "ingesta": {
        "script": "ingest", "platform": None, "editable": True,
        "outputs": ["media.json"],
        "content": ["raw"],
    },
    "transcripcion": {
        "script": "transcribe", "platform": None, "editable": True,
        "outputs": ["transcript"],
        "content": ["raw", "media.json"], "drop_master": True,
        "channel": ["vocabulary.txt"], "language": True, "hook": "transcripcion",
    },
    "corte-en-papel": {
        "script": "paper_cut", "platform": "first", "editable": True,
        "outputs": ["cut/cut-list.json", "cut/PAPER-CUT.md"],
        "content": ["transcript", "media.json"], "drop_master": True,
        "channel": ["vocabulary.txt"], "language": True,
    },
    "corte-aplicado": {
        "script": "apply_cut", "platform": "first", "editable": False,
        "outputs": ["cut/master-cut.mp4", "cut/cut-map.json"],
        "content": ["cut/cut-list.json", "raw", "media.json", "transcript"], "drop_master": True,
        "channel": ["channel.json"],
        "engine": ["presets", "scripts/core/cutlib.py"], "npm": False,   # ffmpeg: HyperFrames no la afecta
    },
    "subtitulos": {
        "script": "captions", "platform": None, "editable": True,
        "outputs": ["captions/captions.json", "captions/master.srt"],
        "content": ["cut/cut-map.json", "transcript"],
        "channel": ["vocabulary.txt", "brand.json"], "language": True, "lang_file": True,
    },
    "composicion": {
        "script": "compose", "platform": "all", "editable": False,
        "outputs": HF,
        "hook": "composicion",
        "engine": ["formats", "presets", "scripts/composer"], "npm": True,
    },
    "check": {
        "script": None, "platform": None, "editable": False,
        "outputs": [],
        "content": HF, "npm": True,
    },
    "revision": {
        "script": None, "platform": None, "editable": False,
        "outputs": ["snaps"],
        "content": HF, "npm": True,
    },
    "render": {
        "script": None, "platform": None, "editable": False,
        "outputs": ["renders"],
        "content": HF, "npm": True,
    },
    "entrega": {
        "script": "deliver", "platform": "all", "editable": False,
        "outputs": ["copy", "covers"],
        "content": ["renders", "copy", "covers", "captions/master.srt", "brief.md", "assets.md"],
        "engine": ["scripts/pipeline/verify.py"],
    },
}

ORDER = list(STAGES)
EDITABLE = tuple(s for s in ORDER if STAGES[s]["editable"])
