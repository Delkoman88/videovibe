#!/usr/bin/env python3
"""Recorte de la persona para los efectos sobre la toma (`storyboard.json → fx`, ADR 0025).

Uso: scripts/pipeline/cutout.py --project <canal>/<pieza>

Para cada efecto que lo necesita, recorta su tramo de `cut/master-cut.mp4` (con margen) y separa a la persona
del fondo con el modelo local de HyperFrames (`hyperframes remove-background`, u2net_human_seg; CoreML en
Mac): WebM con transparencia (o PNG para `freeze-cutout`). Solo pone a la persona en otra capa: no altera
rasgos, piel ni forma (regla 3). Caché en `work/cutout/` por huella del corte y tramo: si nada cambió, no
recalcula (≈ 6 s de cálculo por segundo de video). Con cámara fija, el recorte se estabiliza contra el fondo
reconstruido del propio tramo (`scripts/pipeline/matte.py`): sin cortinas ni sillas que aparecen y desaparecen. También mide dónde empieza la cabeza (`subject_top`)
para colocar solo el texto de `text-behind`. Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import editlib, oslib  # noqa: E402
from scripts.pipeline import matte  # noqa: E402

HF = ROOT / "node_modules" / ".bin" / "hyperframes"
MODEL = "u2net_human_seg"
MATTE = "estable-v7"  # versión del estabilizador (scripts/pipeline/matte.py): cambiarla recalcula los recortes
MARGIN = 0.2
NEEDS_CUTOUT = {"text-behind", "background-swap", "subject-glow", "freeze-cutout"}


def jobs(sb, duration):
    """[(fx, tipo de salida, inicio, fin)] de los efectos que necesitan recorte."""
    out = []
    for fx in sb.get("fx", []):
        if fx.get("type") not in NEEDS_CUTOUT:
            continue
        if fx["type"] == "freeze-cutout":
            out.append((fx, "png", fx["at"], fx["at"]))
        else:
            out.append((fx, "webm", max(0.0, fx["in"] - MARGIN), min(duration, fx["out"] + MARGIN)))
    return out


def _interior(fx):
    """El halo va encima de la misma toma: ahí se rellenan los huecos pasajeros del cuerpo (matte.fill_interior)."""
    return fx.get("type") == "subject-glow"


def _key(P, kind, a, b, interior=False):
    raw = (f"{editlib.cut_fingerprint(P)}|{kind}|{a:.3f}|{b:.3f}|{MODEL}|{MATTE if kind == 'webm' else ''}"
           f"{'|interior' if interior else ''}")
    return hashlib.sha1(raw.encode()).hexdigest()[:14]


def subject_top(path, kind):
    """Primera fila (px) con persona en la franja central del primer cuadro: dónde empieza la cabeza."""
    import subprocess

    import numpy as np
    dec = ["-c:v", "libvpx-vp9"] if kind == "webm" else []  # el decodificador nativo ignora la transparencia
    r = __import__('scripts.core.state', fromlist=['run']).run([oslib.FFMPEG, "-v", "error", *dec, "-i", str(path), "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    a = np.frombuffer(r.stdout, np.uint8).reshape(1920, 1080, 4)[:, 324:756, 3]
    rows = np.nonzero((a > 128).sum(axis=1) > 12)[0]
    return int(rows[0]) if len(rows) else None


def ensure(P, sb, duration=None):
    """Recortes de los efectos (calculados o de caché): {fx_id: {file, kind, start, subject_top}}."""
    P = Path(P)
    duration = duration or oslib.read_json(P / "cut" / "cut-map.json")["duration_s"]
    todo = jobs(sb, duration)
    if not todo:
        return {}
    master = P / "cut" / "master-cut.mp4"
    if not master.exists():
        oslib.die("falta cut/master-cut.mp4 para recortar a la persona (corre el corte primero)")
    cache = P / "work" / "cutout"
    cache.mkdir(parents=True, exist_ok=True)
    out = {}
    for fx, kind, a, b in todo:
        key = _key(P, kind, a, b, _interior(fx))
        dst = cache / f"{key}.{kind}"
        meta_f = cache / f"{key}.json"
        if not (dst.exists() and meta_f.exists()):
            src = cache / f"{key}-src.{'mp4' if kind == 'webm' else 'png'}"
            if kind == "webm":
                oslib.run([oslib.FFMPEG, "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(master),
                           "-an", "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", str(src)])
            else:
                oslib.run([oslib.FFMPEG, "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", str(master),
                           "-frames:v", "1", str(src)])
            matte_info = None
            if kind == "webm":
                raw = cache / f"{key}-raw.webm"
                oslib.run([str(HF), "remove-background", str(src), "-o", str(raw), "--json"])
                matte_info = matte.stabilize(src, raw, dst, interior=_interior(fx))
                if not matte_info.get("applied"):
                    raw.replace(dst)
                raw.unlink(missing_ok=True)
            else:
                oslib.run([str(HF), "remove-background", str(src), "-o", str(dst), "--json"])
            src.unlink(missing_ok=True)
            oslib.write_json(meta_f, {"start": round(a, 3), "end": round(b, 3), "kind": kind, "model": MODEL,
                                      "matte": matte_info, "subject_top": subject_top(dst, kind)})
        meta = oslib.read_json(meta_f)
        out[fx["id"]] = {"file": dst, **meta}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    if True:
        from scripts.core.state import hold
        hold(P)
    sb = oslib.read_json(P / "storyboard.json")
    res = ensure(P, sb)
    oslib.emit({"ok": True, "cutouts": {k: {**v, "file": str(v["file"])} for k, v in res.items()}})


if __name__ == "__main__":
    main()
