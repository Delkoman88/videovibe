"""Presentación verificable de revisiones humanas y apertura portable de archivos."""
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from scripts.core import oslib


def files_for(P, gate):
    P = Path(P)
    if gate == "A":
        return [P / "cut" / "PAPER-CUT.md"]
    if gate != "B":
        raise ValueError("la revisión debe ser A o B")
    sb = oslib.read_json(P / "storyboard.json")
    first = next(iter(sb.get("platforms", {})), "tiktok")
    draft = P / "renders" / f"draft-{first}.mp4"
    sheets = sorted((P / "snaps").glob("contact-sheet*.jpg"))
    if not sheets:
        sheets = sorted((P / "snaps").glob("review-beats*.jpg"))
    if not sheets:
        sheets = [P / "snaps" / "contact-sheet.jpg"]
    phones = [P / "snaps" / f"phone-{clip['id']}.png" for clip in sb.get("broll", [])]
    return [draft, *sheets, *phones]


def fingerprint(P, gate):
    P = Path(P)
    sources = [P / "cut" / "cut-list.json", P / "cut" / "PAPER-CUT.md"] if gate == "A" else [
        P / "storyboard.json", P / "captions" / "captions.json", P / "media.json", *files_for(P, "B")]
    if gate == "B" and (P / "media.json").exists():
        media = {m["id"]: m for m in oslib.read_json(P / "media.json")["items"]}
        sb = oslib.read_json(P / "storyboard.json")
        sources += [P / media[c["source"]]["file"] for c in sb.get("broll", []) if c.get("source") in media]
    h = hashlib.sha256()
    for p in sorted(set(sources)):
        h.update(str(p.relative_to(P)).encode())
        if not p.is_file():
            h.update(b":missing")
            continue
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()[:20]


def open_files(paths, *, no_open=False):
    """Abre cada archivo (o carpeta) una vez y devuelve rutas absolutas aun si el visor falla.
    macOS: open · Linux: xdg-open · Windows: os.startfile. Sin visor, la persona usa la ruta."""
    results = []
    seen = set()
    system = platform.system()
    opener = "open" if system == "Darwin" else "xdg-open" if system == "Linux" else None
    for path in paths:
        p = Path(path).expanduser().resolve()
        if p in seen:
            continue
        seen.add(p)
        item = {"path": str(p), "opened": False}
        if not p.exists():
            item["reason"] = "archivo inexistente"
        elif no_open or os.environ.get("VIDEOVIBE_REVIEW_NO_OPEN") == "1":
            item["reason"] = "apertura desactivada en este entorno"
        elif system == "Windows":
            try:
                os.startfile(str(p))  # noqa: S606 — abre con la aplicación predeterminada
                item["opened"] = True
            except OSError as e:
                item["reason"] = str(e)[:240]
        elif not opener or not shutil.which(opener):
            item["reason"] = "no hay visor disponible"
        elif system == "Linux" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            item["reason"] = "no hay interfaz gráfica"
        else:
            try:
                run = subprocess.run([opener, str(p)], capture_output=True, text=True, timeout=10)
                item["opened"] = run.returncode == 0
                if run.returncode:
                    item["reason"] = (run.stderr or run.stdout or "el visor falló").strip()[:240]
            except (OSError, subprocess.TimeoutExpired) as e:
                item["reason"] = str(e)[:240]
        results.append(item)
    return results


def packet(P, gate):
    P = Path(P)
    if gate == "A":
        cut = oslib.read_json(P / "cut" / "cut-list.json")
        lines = cut.get("lines", [])
        dropped = [x for x in lines if x.get("status") == "drop"]
        summary = [f"Corte propuesto: {len(lines) - len(dropped)} líneas conservadas, {len(dropped)} eliminadas."]
        summary += [f"Se quita: {x.get('text', '')[:110]}" for x in dropped[:3]]
        questions = ["¿Recuperarías alguna de las líneas eliminadas que aparecen en el plan?",
                     "¿Hay un corte que interrumpa una palabra o una idea? Indica la línea o segundo.",
                     "¿El inicio y el cierre tienen el ritmo que quieres?",
                     "¿Apruebas el corte, pides ajustes puntuales o lo rechazas?"]
    else:
        sb = oslib.read_json(P / "storyboard.json")
        summary = [f"Plan visual: {len(sb.get('scenes', []))} escenas, {len(sb.get('overlays', []))} tarjetas y "
                   f"{len(sb.get('broll', []))} insertos de video."]
        for x in (sb.get("broll", []) + sb.get("scenes", []))[:5]:
            summary.append(f"{x.get('in', 0):.1f}–{x.get('out', 0):.1f} s: {x.get('id', x.get('format', 'visual'))}")
        questions = ["¿Los visuales corresponden a lo que se dice en esos momentos?",
                     "¿Se leen los subtítulos y los detalles de pantalla en el teléfono?",
                     "¿Moverías, acortarías o quitarías algún visual? Indica el segundo.",
                     "¿Apruebas el plan visual, pides ajustes puntuales o lo rechazas?"]
    return {"gate": gate, "fingerprint": fingerprint(P, gate), "summary": summary,
            "questions": questions, "files": [str(p.resolve()) for p in files_for(P, gate)]}


def present(P, gate, *, no_open=False, reopen=False, simulated=False):
    P = Path(P)
    info = packet(P, gate)
    st_path = P / "status.json"
    st = oslib.read_json(st_path) if st_path.exists() else {"stage": None, "history": [], "approvals": {}, "renders": {}}
    previous = st.get("reviews", {}).get(gate, {})
    same = previous.get("fingerprint") == info["fingerprint"]
    if same and not reopen:
        opened = previous.get("open_results", [])
    else:
        opened = open_files(info["files"], no_open=no_open or simulated)
    record = {"fingerprint": info["fingerprint"], "presented_at": previous.get("presented_at") if same else
              datetime.datetime.now().isoformat(timespec="seconds"), "files": info["files"],
              "open_results": opened, "decision": previous.get("decision", "pending") if same else "pending",
              "simulated": simulated}
    st.setdefault("reviews", {})[gate] = record
    oslib.write_json(st_path, st)
    info.update({"open_results": opened, "simulated": simulated})
    return info


def format_packet(info):
    lines = [f"REVISIÓN {info['gate']} — {len(info['questions'])} preguntas", *info["summary"], "Archivos:"]
    lines += [f"  {'abierto' if x['opened'] else 'abre manualmente'}: {x['path']}"
              + (f" ({x['reason']})" if x.get("reason") else "") for x in info["open_results"]]
    lines += [f"{i}. {q}" for i, q in enumerate(info["questions"], 1)]
    return "\n".join(lines)
