#!/usr/bin/env python3
"""Subtítulos del master: transcripción de control + grupos de palabras con tiempos exactos.

Uso: scripts/pipeline/captions.py --project <canal>/<pieza> [--max-words 4] [--max-chars 22]

Sobre cut/master-cut.mp4:
  1. Transcripción tramo por tramo (misma lógica que transcribe.py --mode islands).
  2. Limpieza de presentación: mayúscula al iniciar oración y, si el idioma lo usa (lang/<idioma>.json →
     captions), «¿» de apertura en preguntas de coletilla («¿no?»).
  3. Grupos para pantalla: se cortan en fin de oración, coma, pausa ≥ 0.15 s, `--max-words`
     o `--max-chars` (de <canal>/brand.json → captions.max_chars_per_line).
     Los términos de varias palabras de <canal>/vocabulary.txt nunca se parten entre grupos.
Escribe:
  transcript/master-cut.json   palabras definitivas del master (id w0, w1…). Corrige aquí errores de texto.
  captions/captions.json       grupos {id, in, out, words:[ids]} — los consume compose.py
  captions/master.srt          subtítulos estándar
Con --from-transcript solo rehace los grupos desde transcript/master-cut.json (tras corregir texto a mano).
Salida JSON en stdout. Exit 0 ok, 2 error.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import cutlib  # noqa: E402
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
from scripts.pipeline import transcribe  # noqa: E402

SENT_END = re.compile(r"[.?!…]$")
SOFT_END = re.compile(r"[,;:]$")


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def tidy(words, lang=None):
    """Mayúscula tras fin de oración y, en idiomas con «¿», apertura en coletillas («no?» → «¿no?»).
    Solo presentación; no cambia tiempos. Sin `lang` usa el español."""
    rules = (lang or cutlib._ES)["captions"]
    tags = {f"{t}?" for t in rules.get("tag_questions", [])}
    prev_end = True
    for w in words:
        t = w["w"]
        if rules.get("inverted_question") and t.lower().rstrip(".,") in tags:
            t = "¿" + t
        if prev_end and t[:1].isalpha():
            t = t[0].upper() + t[1:]
        elif prev_end and t[:1] in "¿¡" and t[1:2].isalpha():
            t = t[0] + t[1].upper() + t[2:]
        w["w"] = t
        prev_end = bool(SENT_END.search(t))
    return words


def protected_pairs(vocab):
    """Pares de palabras consecutivas que no se separan (términos de varias palabras del vocabulario)."""
    pairs = set()
    for term in vocab or []:
        parts = [cutlib.norm(x) for x in term.split()]
        pairs.update(zip(parts, parts[1:]))
    return pairs


def build_groups(words, max_words, max_chars, duration, vocab=None):
    groups, cur = [], []
    keep = protected_pairs(vocab)

    def text_len(ws):
        return len(" ".join(w["w"] for w in ws))

    for k, w in enumerate(words):
        if cur and (cutlib.norm(cur[-1]["w"]), cutlib.norm(w["w"])) in keep:
            cur.append(w)  # no partir términos de varias palabras del vocabulario
            continue
        if cur:
            gap = w["start"] - cur[-1]["end"]
            if (gap >= 0.15 or len(cur) >= max_words or text_len(cur + [w]) > max_chars):
                groups.append(cur)
                cur = []
        cur.append(w)
        if SENT_END.search(w["w"]) or (SOFT_END.search(w["w"]) and len(cur) >= 2):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    out = []
    for i, g in enumerate(groups):
        t_in = max(g[0]["start"] - 0.05, 0.1 if i == 0 else 0.0)
        t_out = g[-1]["end"] + 0.25
        out.append({"id": f"g{i}", "in": round(t_in, 3), "out": round(t_out, 3), "words": [w["id"] for w in g],
                    "text": " ".join(w["w"] for w in g)})
    for a, b in zip(out, out[1:]):  # nunca dos grupos a la vez
        if a["out"] > b["in"]:
            a["out"] = b["in"]
    if out:
        out[-1]["out"] = round(min(out[-1]["out"], duration), 3)
    return out


def words_from_whisper_json(data):
    """Convierte el JSON `-ojf -sow -ml 1` de whisper.cpp en palabras del master."""
    words = []
    for segment in data.get("transcription", []):
        text = segment.get("text", "").strip()
        offsets = segment.get("offsets") or {}
        if not text or "from" not in offsets or "to" not in offsets:
            continue
        tokens = [t for t in segment.get("tokens", []) if not t.get("text", "").startswith("[_")]
        probability = (sum(t.get("p", 1.0) for t in tokens) / len(tokens)) if tokens else 1.0
        words.append({"w": text, "start": offsets["from"] / 1000, "end": offsets["to"] / 1000,
                      "p": round(probability, 3)})
    return words


def regularize_zero_duration_words(words, minimum=0.04):
    """Reparte tokens simultáneos sin mover los anclajes globales que dio Whisper."""
    i = 0
    while i < len(words):
        if words[i]["end"] - words[i]["start"] >= minimum:
            i += 1
            continue
        start = words[i]["start"]
        j = i
        while (j + 1 < len(words) and abs(words[j + 1]["start"] - start) < 0.001
               and words[j]["end"] - start < minimum):
            j += 1
        if words[j]["end"] - start < minimum and j + 1 < len(words) and words[j + 1]["start"] <= start + 0.001:
            j += 1
        end = max(words[j]["end"], start + minimum * (j - i + 1))
        if j + 1 < len(words):
            end = min(end, words[j + 1]["start"])
        weights = [max(len(words[k]["w"].strip(".,;:¿?¡!")), 1) for k in range(i, j + 1)]
        total = sum(weights)
        cursor = start
        for k, weight in zip(range(i, j + 1), weights):
            duration = (end - start) * weight / total
            words[k]["start"], words[k]["end"] = round(cursor, 3), round(cursor + duration, 3)
            cursor += duration
        i = j + 1
    return words


def repair_from_remap(words, remap_words, after, duration):
    """Sustituye una cola de Whisper por las palabras aprobadas del mapa de corte.

    Conserva los tiempos observados en el master: estira la cola remapeada entre el inicio y final
    reales detectados por Whisper. Elimina una palabra duplicada en la costura (p. ej. «¿no?»).
    """
    import copy
    import re

    keep = [copy.deepcopy(w) for w in words if w["end"] <= after]
    observed = [w for w in words if w["start"] >= after]
    source = [copy.deepcopy(w) for w in remap_words if w["start"] >= after]
    if not keep or not observed or not source:
        raise ValueError("no hay palabras suficientes antes y después del punto de reparación")

    def norm(s):
        return re.sub(r"[^\wáéíóúüñ]+", "", s.casefold())

    while source and norm(source[0]["w"]) == norm(keep[-1]["w"]):
        source.pop(0)
    if not source:
        raise ValueError("la cola remapeada quedó vacía después de quitar la costura duplicada")
    actual_start, actual_end = observed[0]["start"], min(observed[-1]["end"], duration)
    source_start, source_end = source[0]["start"], source[-1]["end"]
    if source_end <= source_start or actual_end <= actual_start:
        raise ValueError("el intervalo de reparación no tiene duración positiva")
    scale = (actual_end - actual_start) / (source_end - source_start)
    for w in source:
        w["start"] = round(actual_start + (w["start"] - source_start) * scale, 3)
        w["end"] = round(actual_start + (w["end"] - source_start) * scale, 3)
    merged = keep + source
    for i, w in enumerate(merged):
        w["id"] = f"w{i}"
        w.pop("src", None)
    return merged


def repair_prefix_from_approved_cut(words, cut, cut_map, before):
    """Restaura el texto aprobado del corte al inicio y conserva el resto ya alineado.

    Los tiempos se distribuyen dentro de cada segmento aprobado; el tramo posterior (por ejemplo,
    una sección cuya sincronía ya fue revisada) queda intacto.
    """
    import copy
    import re

    lines = {line["id"]: line for line in cut["lines"]}
    prefix = []
    for segment in cut_map["segments"]:
        if segment["out_out"] > before + 0.001:
            break
        text = " ".join(lines[lid]["text"] for lid in segment["lines"]
                        if lid in lines and lines[lid]["status"] == "keep")
        tokens = text.split()
        if not tokens:
            continue
        weights = [max(len(re.sub(r"[^\wáéíóúüñ]+", "", token.casefold())), 1) for token in tokens]
        total = sum(weights)
        cursor = segment["out_in"]
        span = segment["out_out"] - segment["out_in"]
        for token, weight in zip(tokens, weights):
            end = cursor + span * weight / total
            prefix.append({"w": token, "start": round(cursor, 3), "end": round(end, 3), "p": 1.0})
            cursor = end
    suffix = [copy.deepcopy(w) for w in words if w["start"] >= before - 0.001]
    merged = prefix + suffix
    for i, w in enumerate(merged):
        w["id"] = f"w{i}"
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--max-words", type=int, default=4)
    ap.add_argument("--max-chars", type=int)
    ap.add_argument("--from-transcript", action="store_true", help="no transcribe; rehace grupos")
    ap.add_argument("--from-whisper-json", type=Path,
                    help="importa tiempos por palabra de un JSON -ojf generado sobre el master final")
    ap.add_argument("--repair-from-remap-after", type=float,
                    help="desde este segundo conserva palabras del remapeo aprobado, ajustadas a los tiempos del master")
    ap.add_argument("--repair-from-approved-cut-before", type=float,
                    help="hasta este segundo restaura el texto del corte A aprobado y conserva el resto")
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    if True:
        from scripts.core.state import hold
        hold(P)
    master = P / "cut" / "master-cut.mp4"
    if not master.exists():
        oslib.die("falta cut/master-cut.mp4: corre scripts/pipeline/apply_cut.py")
    ch = oslib.load_channel(P)
    brand = ch["brand"]
    max_chars = args.max_chars or brand["captions"]["max_chars_per_line"]
    duration = float(oslib.ffprobe(master)["format"]["duration"])
    tpath = P / "transcript" / "master-cut.json"

    added = []
    selected = sum(bool(x) for x in (args.from_transcript, args.from_whisper_json,
                                     args.repair_from_remap_after is not None,
                                     args.repair_from_approved_cut_before is not None))
    if selected > 1:
        oslib.die("usa solo --from-transcript, --from-whisper-json o --repair-from-remap-after")
    if args.from_transcript:
        words = oslib.read_json(tpath)["words"]
    elif args.from_whisper_json:
        if not args.from_whisper_json.exists():
            oslib.die(f"no encuentro {args.from_whisper_json}")
        words = words_from_whisper_json(json.loads(args.from_whisper_json.read_text(encoding="utf-8")))
        regularize_zero_duration_words(words)
        for i, w in enumerate(words):
            w["id"] = f"w{i}"
            w.pop("island", None)
        tidy(words, ch["lang"])
        oslib.write_json(tpath, {"id": "master-cut", "language": ch["lang"]["code"],
                                 "source": str(args.from_whisper_json), "words": words})
    elif args.repair_from_remap_after is not None:
        base = oslib.read_json(tpath)["words"]
        remap_path = P / "transcript" / "master-cut.remap.json"
        if not remap_path.exists():
            oslib.die("falta transcript/master-cut.remap.json: corre apply_cut.py")
        try:
            words = repair_from_remap(base, oslib.read_json(remap_path)["words"],
                                      args.repair_from_remap_after, duration)
        except ValueError as e:
            oslib.die(str(e))
        oslib.write_json(tpath, {"id": "master-cut", "language": ch["lang"]["code"],
                                 "source": "master-cut.remap.json (cola reparada)", "words": words})
    elif args.repair_from_approved_cut_before is not None:
        words = repair_prefix_from_approved_cut(
            oslib.read_json(tpath)["words"], oslib.read_json(P / "cut" / "cut-list.json"),
            oslib.read_json(P / "cut" / "cut-map.json"), args.repair_from_approved_cut_before)
        oslib.write_json(tpath, {"id": "master-cut", "language": ch["lang"]["code"],
                                 "source": "cut-list.json (prefijo aprobado)", "words": words})
    else:
        wav = P / "work" / "audio" / "master-cut.wav"
        wav.parent.mkdir(parents=True, exist_ok=True)
        oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-i", str(master), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
        audio = oslib.load_audio(wav)
        islands, _ = oslib.speech_islands(audio)
        words, _, suspects = transcribe.transcribe_islands(audio, islands, transcribe.DEFAULT_MODEL,
                                                           transcribe.vocab_prompt(ch), ch["lang"])
        added = suspects
        for i, w in enumerate(words):
            w["id"] = f"w{i}"
            w.pop("island", None)
        oslib.write_json(tpath, {"id": "master-cut", "language": ch["lang"]["code"], "islands": islands, "words": words})

    for i, w in enumerate(words):
        w.setdefault("id", f"w{i}")
    if selected == 0:
        tidy(words, ch["lang"])
        oslib.write_json(tpath, {**oslib.read_json(tpath), "words": words})
    groups = build_groups(words, args.max_words, max_chars, duration, vocab=ch["vocab"])
    from scripts.core import editlib
    oslib.write_json(P / "captions" / "captions.json",
                     {"duration_s": round(duration, 3), "cut_fingerprint": editlib.cut_fingerprint(P), "words": [{k: w[k] for k in ("id", "w", "start", "end")} for w in words],
                      "groups": groups})
    srt = []
    for n, g in enumerate(groups, 1):
        srt += [str(n), f"{srt_time(g['in'])} --> {srt_time(g['out'])}", g["text"], ""]
    (P / "captions" / "master.srt").write_text("\n".join(srt), encoding="utf-8")

    low = [f"{w['id']} «{w['w']}»" for w in words if w.get("p", 1) < 0.5]
    oslib.update_status(P, "subtitulos")
    oslib.emit({"ok": True, "words": len(words), "groups": len(groups), "suspect_islands": added,
                "low_confidence": low, "text": " ".join(w["w"] for w in words),
                "next": "Revisa el texto. Corrige en transcript/master-cut.json y corre con --from-transcript. "
                        "Luego escribe storyboard.json y corre scripts/pipeline/compose.py"})


if __name__ == "__main__":
    main()
