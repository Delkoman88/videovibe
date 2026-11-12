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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--max-words", type=int, default=4)
    ap.add_argument("--max-chars", type=int)
    ap.add_argument("--from-transcript", action="store_true", help="no transcribe; rehace grupos")
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    master = P / "cut" / "master-cut.mp4"
    if not master.exists():
        oslib.die("falta cut/master-cut.mp4: corre scripts/pipeline/apply_cut.py")
    ch = oslib.load_channel(P)
    brand = ch["brand"]
    max_chars = args.max_chars or brand["captions"]["max_chars_per_line"]
    duration = float(oslib.ffprobe(master)["format"]["duration"])
    tpath = P / "transcript" / "master-cut.json"

    added = []
    if args.from_transcript:
        words = oslib.read_json(tpath)["words"]
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
    if not args.from_transcript:
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
