"""Datos de las escenas (animaciones Lottie; después estructuras moleculares) como archivos locales del proyecto.

Cada recurso que declara un formato (`@fmt(..., uses=...)`) se sirve como `hf/assets/data/<tipo>-<id>.js`, que
define `window.__vv["<tipo>:<id>"]`. Nada se pide por red durante el render (ADR 0022). Lo que sobra de una
composición anterior se borra; un archivo igual no se reescribe.
"""
import base64
import json
import re
from pathlib import Path

import formats
from scripts.core import assetlib, lottielib

DATA_DIR = "assets/data"


def script_name(kind, ident):
    return f"{kind}-{re.sub(r'[^A-Za-z0-9_-]+', '_', ident)}.js"


def head(sb):
    """<script> de los datos que usa el storyboard (después de las librerías)."""
    return "".join(f'    <script src="{DATA_DIR}/{script_name(k, i)}"></script>\n' for _, k, i in formats.uses(sb))


def _payload(kind, it, brand):
    if kind == "lottie":
        anim = lottielib.recolor(lottielib.load(it["path"]), it.get("recolor"), brand["colors"])
        return json.dumps(anim, ensure_ascii=False, separators=(",", ":"))
    if kind == "structures":
        return json.dumps({"format": it["format"], "text": Path(it["path"]).read_text(encoding="utf-8")},
                          ensure_ascii=False)
    if kind == "models":  # .glb en base64: GLTFLoader.parse lo lee sin red
        return json.dumps({"glb": base64.b64encode(Path(it["path"]).read_bytes()).decode("ascii")})
    if kind == 'images':
        import mimetypes
        file = Path(it['path']); mime = mimetypes.guess_type(file.name)[0]
        if mime not in ('image/png', 'image/jpeg', 'image/webp'): raise ValueError('images: PNG, JPEG o WebP obligatorio')
        return json.dumps({'url': 'data:'+mime+';base64,'+base64.b64encode(file.read_bytes()).decode('ascii')})
    raise KeyError(kind)


def write(hf, sb, channel_dir, brand):
    """Escribe los datos que piden las escenas y devuelve los elementos usados (para créditos)."""
    out_dir = hf / DATA_DIR
    used, keep = [], set()
    for _, kind, ident in formats.uses(sb):
        it = assetlib.item(kind, ident, channel_dir)
        if not it:
            raise KeyError(f"{kind} «{ident}» no está en la biblioteca")
        name = script_name(kind, ident)
        text = f'(window.__vv = window.__vv || {{}})["{kind}:{ident}"] = {_payload(kind, it, brand)};\n'
        out_dir.mkdir(parents=True, exist_ok=True)
        f = out_dir / name
        if not f.exists() or f.read_text(encoding="utf-8") != text:
            f.write_text(text, encoding="utf-8")
        keep.add(name)
        used.append({"kind": kind, **it})
    if out_dir.exists():
        for old in out_dir.iterdir():
            if old.is_file() and old.name not in keep:
                old.unlink()
    return used
