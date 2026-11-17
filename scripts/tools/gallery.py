#!/usr/bin/env python3
"""Galería de formatos de animación con la marca de un canal: ver cómo luce cada uno antes de usarlo.

Uso: bin/format-gallery --channel <id> [--formats a,b,…] [--seconds 3.2] [--check] [--determinism]

Arma un proyecto HyperFrames en work/gallery/<canal>/hf con una escena por formato (parámetros de
ejemplo del registro, mismo `formats.render` y mismas librerías que una pieza real) y captura cada una
a mitad de su duración. Las escenas `over` se ven sobre un fondo neutro que simula la toma.
- --check: corre `hyperframes check` (lint, runtime, layout) y cuenta errores.
- --determinism: vuelve a capturar en orden inverso y compara píxeles (idénticos, salvo ruido de suavizado
  de la GPU: diferencias de ≤ 8 niveles en ≤ 0.01 % de los píxeles).
Salida JSON (hojas de contacto, capturas y resultados). Exit 0 ok, 1 si --check/--determinism fallan, 2 error.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import formats  # noqa: E402
from formats import vendors  # noqa: E402
from scripts.composer import data as scene_data  # noqa: E402
from scripts.composer.context import H, W, font_faces  # noqa: E402
from scripts.composer.visual import css_vars, esc, scenes_markup  # noqa: E402
from scripts.core import oslib  # noqa: E402

HF = ROOT / "node_modules" / ".bin" / "hyperframes"


def gallery_storyboard(names, packs, seconds, params=None):
    """Una escena por formato, una tras otra. `bubble` pasa a `full`: la galería no tiene toma real.
    `params` ({formato: parámetros}) reemplaza el ejemplo del registro (vista previa de un recurso)."""
    scenes = []
    for i, name in enumerate(names):
        meta = formats.REGISTRY[name]
        layout = meta["layout"] if meta["layout"] != "bubble" else "full"
        scenes.append({"id": f"g-{name}", "format": name, "in": round(i * seconds, 3),
                       "out": round((i + 1) * seconds, 3), "layout": layout,
                       "params": dict((params or {}).get(name) or meta["example"])})
    return {"scenes": scenes}


def index_html(sb, brand, faces, total):
    hosts, _, _ = scenes_markup(sb)
    labels = "\n".join(
        f'      <div id="lbl-{esc(s["format"])}" class="clip lbl" data-start="{s["in"]}" '
        f'data-duration="{round(s["out"] - s["in"], 3)}" data-track-index="2">{esc(s["format"])}'
        f' <span>· {esc(formats.REGISTRY[s["format"]]["pack"])}</span></div>' for s in sb["scenes"])
    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
{vendors.head(formats.needs(sb))}{scene_data.head(sb)}    <style>
      {faces}
      :root {{
{css_vars(brand)}
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: var(--bg); }}
      #root {{ position: absolute; inset: 0; }}
      .toma {{ position: absolute; inset: 0; background:
          radial-gradient(420px 520px at 50% 36%, #5b5f66, transparent 70%),
          linear-gradient(170deg, #3a3d42, #1d1f23); }}
      .toma::after {{ content: "toma"; position: absolute; left: 50%; top: 640px; transform: translateX(-50%);
          font: 600 34px var(--font-mono); letter-spacing: .3em; color: rgba(255,255,255,.18); }}
      .lbl {{ position: absolute; left: 0; right: 0; top: 1760px; text-align: center;
          font: 600 40px var(--font-mono); color: var(--text); }}
      .lbl span {{ color: var(--muted); font-weight: 400; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="root" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
      <div class="toma"></div>
{hosts}
{labels}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["root"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def build(channel, names=None, seconds=3.2, out=None, params=None):
    """Escribe el proyecto de la galería y devuelve (dir hf, storyboard)."""
    ch = oslib.load_channel(oslib.channel_path(channel))
    brand = ch["brand"]
    packs = tuple(ch["config"].get("format_packs", []))
    faces = font_faces(brand)
    formats.configure(faces, ch["lang"]["labels"], ch["config"].get("name"))
    reg = formats.registry(packs)
    names = names or sorted(reg, key=lambda n: (reg[n]["pack"] != "core", reg[n]["pack"], n))
    if bad := [n for n in names if n not in reg]:
        oslib.die(f"formatos no disponibles para {channel}: {bad} (paquetes del canal: {list(packs)})")
    sb = gallery_storyboard(names, packs, seconds, params)
    hf = Path(out) if out else ROOT / "work" / "gallery" / channel / "hf"
    if hf.exists():
        shutil.rmtree(hf)
    (hf / "compositions").mkdir(parents=True)
    (hf / "assets" / "fonts").mkdir(parents=True)
    for key in ("display", "mono"):
        shutil.copy(oslib.font_file(ch, key), hf / "assets" / "fonts" / brand["fonts"][key]["file"])
    if missing := vendors.copy(formats.needs(sb), ROOT / "node_modules", hf / "assets" / "vendor"):
        oslib.die(f"faltan librerías {missing}: corre `npm ci`")
    scene_data.write(hf, sb, ch["dir"], brand)
    for sc in sb["scenes"]:
        (hf / "compositions" / f"scene-{sc['id']}.html").write_text(formats.render(sc, packs), encoding="utf-8")
    total = round(len(names) * seconds, 3)
    (hf / "index.html").write_text(index_html(sb, brand, faces, total), encoding="utf-8")
    oslib.write_json(hf / "hyperframes.json", {"paths": {"blocks": "compositions", "assets": "assets"}})
    return hf, sb


def _hf(args, cwd, timeout=900):
    return subprocess.run([str(HF), *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)


def snapshot(hf, times, out):
    r = _hf(["snapshot", "--at", ",".join(f"{t:g}" for t in times), "--no-end", "-o", str(out)], hf)
    if r.returncode:
        oslib.die(f"hyperframes snapshot falló: {(r.stderr or r.stdout)[-600:]}")
    shots = {}
    for t in times:
        hits = sorted(out.glob(f"*-at-{t:g}s.png"))
        if hits:
            shots[t] = hits[0]
    return shots


def pixel_diff(a, b):
    """(máxima diferencia por canal, fracción de píxeles distintos > 8) entre dos PNG del mismo tamaño.
    La GPU puede variar 1–2 niveles en bordes suavizados; un fallo real de determinismo es mucho mayor."""
    import numpy as np

    def load(p):
        raw = subprocess.run([oslib.FFMPEG, "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.int16)
    d = np.abs(load(a) - load(b)).max(axis=2)
    return int(d.max()), float((d > 8).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--formats", help="lista separada por comas (por defecto, todos los del canal)")
    ap.add_argument("--seconds", type=float, default=3.2, help="duración de cada escena")
    ap.add_argument("--check", action="store_true", help="correr hyperframes check")
    ap.add_argument("--determinism", action="store_true", help="capturar dos veces en distinto orden y comparar")
    args = ap.parse_args()

    names = [n.strip() for n in args.formats.split(",")] if args.formats else None
    hf, sb = build(args.channel, names, args.seconds)
    times = [round(s["in"] + (s["out"] - s["in"]) * 0.7, 3) for s in sb["scenes"]]
    shots_dir = hf.parent / "snapshots"
    shots = snapshot(hf, times, shots_dir)
    result = {"ok": True, "channel": args.channel, "formats": [s["format"] for s in sb["scenes"]],
              "project": str(hf), "contact_sheets": [str(p) for p in sorted(shots_dir.glob("contact-sheet*.jpg"))],
              "frames": {s["format"]: str(shots.get(t, "")) for s, t in zip(sb["scenes"], times)}}
    if args.check:
        r = _hf(["check", "--json", "--no-cache"], hf)
        try:
            import json
            rep = json.loads(r.stdout)
            errs = sum(rep.get(k, {}).get("errorCount", 0) for k in ("lint", "runtime", "layout", "motion", "audio"))
            result["check"] = {"errors": errs, "ok": bool(rep.get("ok")) and errs == 0}
        except ValueError:
            result["check"] = {"ok": False, "errors": None, "output": (r.stdout or r.stderr)[-600:]}
        result["ok"] &= result["check"]["ok"]
    if args.determinism:
        again = snapshot(hf, list(reversed(times)), hf.parent / "snapshots-reverse")
        diff = []
        for s, t in zip(sb["scenes"], times):
            if t not in shots or t not in again:
                continue
            same = hashlib.sha256(shots[t].read_bytes()).digest() == hashlib.sha256(again[t].read_bytes()).digest()
            if not same:
                peak, frac = pixel_diff(shots[t], again[t])
                if frac > 1e-4:
                    diff.append(f"{s['format']} (máx {peak}, {frac:.2%} píxeles)")
        result["determinism"] = {"ok": not diff, "different": diff}
        result["ok"] &= not diff
    oslib.emit(result, 0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
