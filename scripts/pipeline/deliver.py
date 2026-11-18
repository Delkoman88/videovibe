#!/usr/bin/env python3
"""Pone los finales verificados de una pieza en la carpeta de entregas, fácil de encontrar.

Uso: scripts/pipeline/deliver.py --project <canal>/<pieza> --platform tiktok [--platform reels …]

Crea <entregas>/<Nombre del canal>/<AAAA-MM-DD> <pieza>/versions/<huella>/ con, por plataforma:
  <plat>.mp4 · <plat> - cover.jpg · <plat> - copy.md, más subtitles.srt y README.md (qué es cada archivo,
  el texto de cada plataforma listo para copiar y la licencia del sonido).
La carpeta de entregas es deliveries/ en la raíz del repo ($VIDEOVIBE_DELIVERIES o local.json → deliveries_dir).
Los archivos son copias independientes verificadas por hash. Una versión anterior no se sobrescribe.
La preparación se promueve tras comprobar verificación y aprobaciones; current.json señala la versión
vigente. Lo llama bin/edit después de verify.py. Una ejecución directa también exige esa evidencia.
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

MANIFEST = ".videovibe-delivery.json"
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')  # caracteres no válidos en nombres de Windows/macOS/Linux


def safe(name):
    return INVALID.sub("-", name).strip(" .") or "sin-nombre"


def delivery_dir(P, ch):
    """<entregas>/<Nombre del canal>/<AAAA-MM-DD> <resto del nombre de la pieza>."""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", P.name)
    folder = f"{m.group(1)} {m.group(2)}" if m else P.name
    return oslib.DELIVERIES / safe(ch["name"]) / safe(folder)


def place(src, dst):
    """Copia independiente, comprobada por contenido."""
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    from scripts.core.integrity import digest_bytes
    expected=digest_bytes(src)
    shutil.copy2(src,dst)
    if digest_bytes(dst)!=expected:raise ValueError('fuente cambió durante la copia')
    return "copia"


def readme(P, ch, plats, files):
    brief = (P / "brief.md").read_text(encoding="utf-8") if (P / "brief.md").exists() else ""
    m = re.search(r"\*\*Título de trabajo:\*\*\s*(.+)", brief)
    title = m.group(1).strip() if m and m.group(1).strip() else P.name
    lines = [f"# {title}", "", f"Canal: **{ch['name']}** · pieza `{P.name}`", "",
             "Videos verificados por VideoVibe (resolución, códec, volumen −14 LUFS). Para publicar: sube el video de",
             "cada plataforma, usa su portada y copia su texto.", "", "## Archivos", ""]
    lines += [f"- `{f}`" for f in files]
    for p in plats:
        cp = P / "copy" / f"{p}.md"
        if cp.exists():
            lines += ["", f"## Texto para {p}", "", cp.read_text(encoding="utf-8").strip()]
    assets = (P / "assets.md").read_text(encoding="utf-8") if (P / "assets.md").exists() else ""
    m = re.search(r"<!-- audio:auto -->(.*?)<!-- /audio:auto -->", assets, re.S)
    if m:
        lines += ["", m.group(1).strip()]
    return "\n".join(lines) + "\n"


def _prepare(P, plats, out_dir):
    ch = oslib.load_channel(P)
    out_dir.mkdir(parents=True, exist_ok=True)
    old = oslib.read_json(out_dir / MANIFEST).get("files", []) if (out_dir / MANIFEST).exists() else []
    plan = []
    for p in plats:
        plan += [(P / "renders" / f"{p}.mp4", f"{p}.mp4"), (P / "covers" / f"{p}.jpg", f"{p} - cover.jpg"),
                 (P / "copy" / f"{p}.md", f"{p} - copy.md")]
    srt = next((P / "captions" / n for n in ("master.srt", *(f"{p}.srt" for p in plats))
                if (P / "captions" / n).exists()), None)
    if srt:
        plan.append((srt, "subtitles.srt"))
    missing = [str(src) for src, _ in plan if not src.exists() and src.suffix == ".mp4"]
    if missing:
        oslib.die(f"faltan renders verificados: {missing} (bin/edit hasta ENTREGABLE)")
    files, methods = [], {}
    for src, name in plan:
        if src.exists():
            methods[name] = place(src, out_dir / name)
            files.append(name)
    for name in set(old) - set(files) - {"README.md"}:  # plataformas que ya no forman parte de la pieza
        (out_dir / name).unlink(missing_ok=True)
    (out_dir / "README.md").write_text(readme(P, ch, plats, files), encoding="utf-8")
    files.append("README.md")
    oslib.write_json(out_dir / MANIFEST, {"piece": str(P), "files": files})
    return {"dir": str(out_dir.resolve()), "files": files,
            "method": "enlace" if set(methods.values()) == {"enlace"} else
                      "copia" if set(methods.values()) == {"copia"} else "mixto"}


def deliver(P, plats):
    import tempfile
    from scripts.core import integrity, state
    with state.lock(P):
        st=state.load(P)
        receipt=st.get('verification',{})
        expected=integrity.verification(P,plats)
        if receipt.get('platforms')!=plats or receipt.get('fingerprint')!=expected:
            raise ValueError('verificación ausente o desactualizada')
        if not all(integrity.valid(P,g,st) for g in ('A','B')):
            raise ValueError('aprobaciones ausentes o desactualizadas')
        base=delivery_dir(P,oslib.load_channel(P));versions=base/'versions';versions.mkdir(parents=True,exist_ok=True)
        destination=versions/expected[:24]
        if not destination.exists():
            temp=Path(tempfile.mkdtemp(prefix='.pending-',dir=versions))
            try:
                result=_prepare(P,plats,temp)
                if integrity.verification(P,plats)!=expected or not all(integrity.valid(P,g,state.load(P)) for g in ('A','B')):
                    raise ValueError('contenido cambiado durante entrega')
                hashes={f.name:integrity.digest_bytes(f) for f in temp.iterdir() if f.is_file() and f.name!=MANIFEST}
                oslib.write_json(temp/MANIFEST,{'version':2,'files':result['files'],'hashes':hashes,'verification':receipt,'approvals':st['approvals']})
                os.replace(temp,destination)
            finally:
                if temp.exists():shutil.rmtree(temp)
        manifest=oslib.read_json(destination/MANIFEST)
        if any(integrity.digest_bytes(destination/name)!=value for name,value in manifest['hashes'].items()):
            raise ValueError('entrega existente alterada; no se reutiliza')
        oslib.write_json(base/'current.json',{'version':2,'dir':str(destination),'fingerprint':expected})
        return {'dir':str(destination.resolve()),'files':manifest['files'],'method':'copia'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--platform", action="append", required=True)
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    if True:
        from scripts.core.state import hold
        hold(P)
    try: res = deliver(P, args.platform)
    except ValueError as e: oslib.die(str(e),1)
    oslib.update_status(P, "entregable", delivery=res["dir"])
    oslib.emit({"ok": True, **res, "next": f"Muéstrale a la persona la carpeta de entregas: {res['dir']}"})


if __name__ == "__main__":
    main()
