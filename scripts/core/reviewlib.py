"""Presentación verificable de revisiones humanas y apertura portable de archivos."""

from scripts.core.state import mutating
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from scripts.core import oslib


def _is_wsl():
    """Devuelve True dentro de WSL, incluso si las variables de entorno no están disponibles."""
    if os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/sys/kernel/osrelease").read_text().lower()
    except OSError:
        return False


def _open_in_windows(path):
    """Abre una ruta WSL con la aplicación predeterminada de Windows."""
    converted = subprocess.run(
        ["wslpath", "-w", str(path)], capture_output=True, text=True, timeout=10
    )
    if converted.returncode:
        return False, (converted.stderr or converted.stdout or "wslpath falló").strip()[:240]
    windows_path = converted.stdout.strip()
    opened = subprocess.run(
        ["cmd.exe", "/c", "start", "", windows_path],
        capture_output=True, text=True, timeout=10,
    )
    if opened.returncode:
        return False, (opened.stderr or opened.stdout or "Windows no pudo abrir el archivo").strip()[:240]
    return True, None


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
    quality = P / 'work' / 'animation-quality.json'
    quality_data = oslib.read_json(quality) if sb.get('motion') and quality.exists() else {}
    frames = quality_data.get('review_frames') or quality_data.get('frames', [])[:2]
    return [draft, *sheets, *phones, *[Path(f) for f in frames]]


def fingerprint(P, gate):
    P = Path(P)
    sources = [P / "cut" / "cut-list.json", P / "cut" / "PAPER-CUT.md"] if gate == "A" else [
        P / "storyboard.json", P / "captions" / "captions.json", P / "media.json", *files_for(P, "B")]
    if gate == "B" and (P / "media.json").exists():
        media = {m["id"]: m for m in oslib.read_json(P / "media.json")["items"]}
        sb = oslib.read_json(P / "storyboard.json")
        sources += [P / media[c["source"]]["file"] for c in sb.get("broll", []) if c.get("source") in media]
    if gate == "B":
        sources += sorted((P / "hf" / "assets" / "broll-audio").glob("*.wav"))
    custom = custom_questions(P, gate)
    h = hashlib.sha256()
    if custom is not None:
        h.update(json.dumps(custom, ensure_ascii=False).encode())
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
    macOS: open · Linux: xdg-open · WSL: app predeterminada de Windows · Windows: os.startfile.
    Sin visor, la persona usa la ruta."""
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
        elif system == "Linux" and _is_wsl() and shutil.which("cmd.exe") and shutil.which("wslpath"):
            try:
                item["opened"], reason = _open_in_windows(p)
                if reason:
                    item["reason"] = reason
            except (OSError, subprocess.TimeoutExpired) as e:
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


def custom_questions(P, gate):
    path = Path(P) / 'review-questions.json'
    if not path.exists(): return None
    data = oslib.read_json(path)
    if not isinstance(data, dict) or set(data) - {'A', 'B'}:
        raise ValueError('review-questions.json: solo claves A y B')
    for prompts in data.values():
        if not isinstance(prompts, list) or not 2 <= len(prompts) <= 4 or any(not isinstance(q, str) or not q.strip() for q in prompts):
            raise ValueError('cada revisión requiere de 2 a 4 preguntas no vacías; la decisión final se añade automáticamente')
    return data.get(gate)


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
        if sb.get('motion'):
            from scripts.core.animationqa import inspect
            import formats
            ch = oslib.load_channel(P)
            qa = inspect(sb, formats.registry(ch['config'].get('format_packs', [])))
            report_path = P / 'work' / 'animation-quality.json'
            from scripts.core.quality_fingerprint import fingerprint as quality_fingerprint
            if not report_path.exists(): oslib.die('control visual pendiente: ejecuta animation_quality antes de B')
            if report_path.exists():
                report = oslib.read_json(report_path)
                if report.get('fingerprint') != quality_fingerprint(P) or not report.get('ok'):
                    oslib.die('control visual desactualizado o con errores: vuelve a componer')
                summary += [f"Control de composición: {len(report['issues'])} hallazgos; rostros y claridad requieren inspección."]
            summary += [f"{i.get('time',0):.1f} s: {i['message']}" for i in report.get('issues',[])[:5]]
            summary += [f"Movimiento: {sb['motion']['profile']}; revisión visual humana pendiente."]
            summary += [f"{i['time']:.1f} s: {i['message']}" for i in qa['issues'][:5]]
        substitutions = P/'work/cutout-review/substitutions.json'
        if substitutions.exists():
            data = oslib.read_json(substitutions)
            if data.get('storyboard_hash') == hashlib.sha256((P/'storyboard.json').read_bytes()).hexdigest():
                summary += [f"Efecto {x['id']}: {x['action']} — {x['reason']}" for x in data['changes']]
        questions = ["¿Los visuales corresponden a lo que se dice en esos momentos?",
                     "¿Se leen los subtítulos y los detalles de pantalla en el teléfono?",
                     "¿Moverías, acortarías o quitarías algún visual o sustitución de efecto? Indica el segundo.",
                     "¿Apruebas el plan visual, pides ajustes puntuales o lo rechazas?"]
    custom = custom_questions(P, gate)
    if custom is not None:
        questions = custom + [questions[-1]]
    return {"gate": gate, "fingerprint": fingerprint(P, gate), "summary": summary,
            "questions": questions, "files": [str(p.resolve()) for p in files_for(P, gate)]}


@mutating
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
    if not same:
        from scripts.core.state import invalidate
        invalidate(st,gate,'nueva presentación')
    from scripts.core.integrity import approval_inputs
    record['inputs'] = approval_inputs(P,gate)
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
