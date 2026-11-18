#!/usr/bin/env python3
"""Corte en papel: propone qué conservar y qué quitar, para el punto de revisión A.

Uso: scripts/pipeline/paper_cut.py --project <canal>/<pieza> [--pause 0.35] [--platform tiktok]

Lee media.json (tomas kind=camara, en orden) y transcript/<id>.json. Escribe:
  cut/cut-list.json   líneas numeradas (L1, L2…) con status keep/drop y motivo. ES LA FUENTE DEL CORTE:
                      para cambiar el corte se edita `status` de una línea y se corre apply_cut.py.
  cut/PAPER-CUT.md    lo mismo, legible, para que la persona del canal responda en lenguaje natural.

Quita automáticamente: retomas (conserva la última toma), muletillas sueltas (eh, em, mm…),
conectores sueltos ("y", "pues" aislados entre pausas), fragmentos aislados de ≤ 0.3 s
(«¿no?», tropiezos), sonidos sin texto y silencios largos (deja `--pause` s tras cada línea). Solo SUGIERE, sin
aplicar: muletillas ambiguas ("este", "o sea", "bueno") y palabras de baja confianza.
Las listas de muletillas y conectores salen del idioma del canal (lang/<idioma>.json).
La pausa por defecto sale de presets/<platform>.json (pacing.pause_after_sentence_s) o 0.35.
Salida JSON en stdout. Exit 0 ok, 2 error.
"""
import argparse
import json
import math
import os
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import cutlib  # noqa: E402
from scripts.core import oslib  # noqa: E402


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def render_paper(P, out_lines, total_src, est, pause, sugerencias):
    md = [f"# Corte en papel — {P.name}", "",
          f"Duración original **{total_src:.1f} s** → corte estimado **{est:.1f} s** "
          f"(−{100 * (1 - est / total_src):.0f} %). Pausa tras cada línea: {pause} s.", "",
          "## Líneas", ""]
    for ln in out_lines:
        rng = f"`{ln['src']} {fmt(ln['start'])}–{fmt(ln['end'])}`"
        if ln["status"] == "keep":
            md.append(f"- **{ln['id']}** ✅ {rng} {ln['text']}")
        else:
            why = ln["reason"] + (f" (se conserva {ln['kept_as']})" if ln.get("kept_as") else "")
            md.append(f"- **{ln['id']}** ❌ {rng} ~~{ln['text']}~~ — _{why}_")
    md += ["", "## Sugerencias (no aplicadas)", ""]
    md += [f"- {s}" for s in sugerencias] or ["- Ninguna."]
    md += ["", "## Cómo responder", "",
           "En lenguaje natural, por ejemplo: «conserva L2 en vez de L3», «quita L7», «deja más pausa después de L5»,",
           "«corrige la transcripción de L4: dice BLAST». El agente edita `cut/cut-list.json` y corre `scripts/pipeline/apply_cut.py`.", ""]
    return "\n".join(md)



def refresh_from_cut(P):
    """Regenera solo la vista legible; valida todas las entradas antes de escribir."""
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def number(value):
        return type(value) in (int, float) and math.isfinite(value)

    try:
        cut = read(P / "cut/cut-list.json")
        media = read(P / "media.json")["items"]
        sources = cut["sources"]
        lines = cut["lines"]
        pause = cut["pause_s"]
        if cut.get("version") != 1 or not isinstance(sources, list) or not sources:
            raise ValueError("sources/version inválidos")
        if any(not isinstance(src, str) or Path(src).name != src or src in (".", "..") for src in sources):
            raise ValueError("id de fuente inválido")
        if len(set(sources)) != len(sources) or not number(pause) or pause < 0:
            raise ValueError("fuentes duplicadas o pausa inválida")
        if not isinstance(lines, list) or not lines:
            raise ValueError("no hay líneas")
        durations, islands = {}, {}
        for src in sources:
            matches = [m for m in media if m["id"] == src]
            if len(matches) != 1 or not number(matches[0]["duration_s"]) or matches[0]["duration_s"] <= 0:
                raise ValueError(f"fuente ausente o duración inválida: {src}")
            durations[src] = matches[0]["duration_s"]
            spans = read(P / "transcript" / f"{src}.json")["islands"]
            if not isinstance(spans, list):
                raise ValueError(f"islands inválidas: {src}")
            last = 0
            for span in spans:
                if (not isinstance(span, list) or len(span) != 2 or not all(number(n) for n in span)
                        or not 0 <= last <= span[0] < span[1] <= durations[src]):
                    raise ValueError(f"islands inválidas: {src}")
                last = span[1]
            islands[src] = spans
        ids, previous = set(), (-1, -1)
        for line in lines:
            if (not isinstance(line["id"], str) or not line["id"] or line["id"] in ids
                    or line["src"] not in sources or line["status"] not in ("keep", "drop")
                    or not all(isinstance(line[k], str) for k in ("text", "reason"))
                    or not all(number(line[k]) for k in ("start", "end"))
                    or not 0 <= line["start"] < line["end"] <= durations[line["src"]]):
                raise ValueError("línea inválida, duplicada o fuera de la fuente")
            current = (sources.index(line["src"]), line["start"])
            if current < previous:
                raise ValueError("reordenamiento de líneas no soportado")
            previous = current
            ids.add(line["id"])
        for line in lines:
            if "kept_as" in line and line["kept_as"] not in ids:
                raise ValueError("kept_as no referencia una línea existente")
        if not any(line["status"] == "keep" for line in lines):
            raise ValueError("ninguna línea conservada")
        segments = cutlib.build_segments(lines, islands, pause)
        estimate = sum(seg["out"] - seg["in"] for seg in segments)
        content = render_paper(P, lines, sum(durations.values()), estimate, pause,
                               ["Vista regenerada desde cut-list.json; no se reejecutaron heurísticas."])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"No se pudo actualizar el corte en papel: {exc}") from exc
    target = P / "cut/PAPER-CUT.md"
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".paper-cut-", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, target)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return {"ok": True, "review": str(target), "estimated_s": round(estimate, 2),
            "next": "Reanuda bin/edit para presentar la revisión A vigente."}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--pause", type=float, help="silencio conservado tras cada línea (s)")
    ap.add_argument("--platform", help="toma la pausa del preset de esta plataforma")
    ap.add_argument("--kinds", default="camara", help="tipos de toma que entran al corte (coma)")
    ap.add_argument("--refresh-from-cut", action="store_true", help="regenera PAPER-CUT.md sin alterar el JSON ni sus decisiones")
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    if args.refresh_from_cut:
        if args.pause is not None or args.platform or args.kinds != "camara":
            ap.error("--refresh-from-cut usa las opciones del JSON; no admite opciones de generación")
        try:
            result = refresh_from_cut(P)
        except ValueError as exc:
            oslib.die(str(exc))
        oslib.emit(result)
        return
    ch = oslib.load_channel(P)
    lang = ch["lang"]
    suggest = {cutlib.norm(x) for x in lang["fillers_suggest"]}
    pause = args.pause
    if pause is None and args.platform:
        pause = oslib.load_preset(args.platform).get("pacing", {}).get("pause_after_sentence_s")
    pause = 0.35 if pause is None else pause

    kinds = set(args.kinds.split(","))
    media = [m for m in oslib.read_json(P / "media.json")["items"] if m.get("kind") in kinds and m.get("audio")]
    if not media:
        oslib.die(f"no hay tomas de tipo {sorted(kinds)} con audio en media.json")

    lines, islands_by_src, total_src, sugerencias = [], {}, 0.0, []
    for m in media:
        tf = P / "transcript" / f"{m['id']}.json"
        if not tf.exists():
            oslib.die(f"falta {tf.name}: corre scripts/pipeline/transcribe.py")
        t = oslib.read_json(tf)
        islands_by_src[m["id"]] = t["islands"]
        total_src += m["duration_s"]
        src_lines = cutlib.split_lines(m["id"], t["words"], lang=lang)
        for k in t.get("untranscribed_islands", []):  # sonidos sin texto
            a, b = t["islands"][k]
            src_lines.append({"src": m["id"], "words": [], "start": a, "end": b, "text": "(sonido sin texto)", "noise": True})
        src_lines.sort(key=lambda ln: ln["start"])
        lines.extend(src_lines)
        for w in t["words"]:
            n = cutlib.norm(w["w"])
            if n in suggest:
                sugerencias.append(f"{m['id']} {fmt(w['start'])}: «{w['w']}» ¿muletilla?")
            if w.get("p", 1) < 0.5:
                sugerencias.append(f"{m['id']} {fmt(w['start'])}: «{w['w']}» baja confianza, revisar transcripción")

    for i, ln in enumerate(lines, 1):
        ln["id"] = f"L{i}"
        if ln.get("filler"):
            ln["status"], ln["reason"] = "drop", "muletilla"
        elif ln.get("noise"):
            ln["status"], ln["reason"] = "drop", "sonido sin texto"
        else:
            ln["status"], ln["reason"] = "keep", ""
    cutlib.mark_retakes(lines)
    cutlib.mark_lone_connectors(lines, lang=lang)
    cutlib.mark_short_fragments(lines)

    segs = cutlib.build_segments(lines, islands_by_src, pause)
    est = sum(s["out"] - s["in"] for s in segs)

    out_lines = [{"id": ln["id"], "src": ln["src"], "start": round(ln["start"], 3), "end": round(ln["end"], 3),
                  "text": ln["text"], "status": ln["status"], "reason": ln["reason"],
                  **({"kept_as": ln["kept_as"]} if ln.get("kept_as") else {})} for ln in lines]
    cut = {"version": 1, "pause_s": pause, "kinds": sorted(kinds), "sources": [m["id"] for m in media],
           "lines": out_lines}
    oslib.write_json(P / "cut" / "cut-list.json", cut)

    (P / "cut" / "PAPER-CUT.md").write_text(
        render_paper(P, out_lines, total_src, est, pause, sugerencias), encoding="utf-8")

    oslib.update_status(P, "corte-en-papel", pending="aprobación A")
    oslib.emit({"ok": True, "lines": len(out_lines),
                "dropped": [{"id": l["id"], "reason": l["reason"], "text": l["text"][:60]} for l in out_lines if l["status"] == "drop"],
                "source_s": round(total_src, 2), "estimated_s": round(est, 2), "suggestions": len(sugerencias),
                "review": str((P / "cut" / "PAPER-CUT.md").relative_to(P)),
                "next": f"Punto de revisión A: muestra PAPER-CUT.md a {ch['person']['short']}. Tras su aprobación: "
                        f"bin/status --approve A y scripts/pipeline/apply_cut.py"})


if __name__ == "__main__":
    main()
