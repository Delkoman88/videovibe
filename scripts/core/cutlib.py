"""Lógica de corte compartida por paper_cut.py y apply_cut.py.

Las listas que dependen del idioma (muletillas, conectores) vienen de lang/<idioma>.json; las funciones
reciben ese paquete en `lang`. Sin `lang` se usa el español (lang/es.json).
"""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

_ES = json.loads((Path(__file__).resolve().parents[2] / "lang" / "es.json").read_text(encoding="utf-8"))

SENTENCE_END = re.compile(r"[.?!…]$")


def norm(word):
    w = unicodedata.normalize("NFD", word.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]+", "", w)


def _set(lang, key):
    return {norm(x) for x in (lang or _ES)[key]}


def split_lines(src, words, max_gap=0.6, island_gap=0.25, lang=None):
    """Divide las palabras en líneas: fin de oración, hueco largo, cambio de tramo de voz tras una
    pausa (≥ island_gap) o muletilla suelta."""
    lines, cur = [], []
    fillers = _set(lang, "fillers_drop")

    def flush():
        if cur:
            lines.append({"src": src, "words": list(cur)})
            cur.clear()

    for k, w in enumerate(words):
        n = norm(w["w"])
        if n in fillers:
            flush()
            lines.append({"src": src, "words": [w], "filler": True})
            continue
        if cur:
            gap = w["start"] - cur[-1]["end"]
            new_island = "island" in w and w.get("island") != cur[-1].get("island")
            if gap > max_gap or (new_island and gap >= island_gap):
                flush()
        cur.append(w)
        if SENTENCE_END.search(w["w"]):
            flush()
    flush()
    for ln in lines:
        ln["start"], ln["end"] = ln["words"][0]["start"], ln["words"][-1]["end"]
        ln["text"] = " ".join(w["w"] for w in ln["words"])
    return lines


def is_retake(a, b):
    """¿La línea `a` es una toma fallida o anterior de la línea `b`?"""
    ta = [norm(w["w"]) for w in a["words"] if norm(w["w"])]
    tb = [norm(w["w"]) for w in b["words"] if norm(w["w"])]
    if len(ta) < 2 or len(tb) < 2:
        return False
    head = min(3, len(ta))
    if ta[:head] != tb[:head]:
        return False
    sim = SequenceMatcher(None, ta, tb[:len(ta) + 2]).ratio()
    return sim >= 0.7


def mark_lone_connectors(lines, max_words=3, lang=None):
    """Línea aislada formada solo por conectores («y», «y y», «pues»): tropiezo, se quita."""
    connectors = _set(lang, "connectors_lone")
    for ln in lines:
        ws = ln.get("words", [])
        if ln.get("status") != "keep" or not ws or len(ws) > max_words:
            continue
        if all(norm(w["w"]) in connectors for w in ws):
            ln["status"], ln["reason"] = "drop", "conector suelto"


def mark_short_fragments(lines, max_s=0.3, max_words=2):
    """Fragmentos muy cortos y aislados (≤ 0.3 s, ≤ 2 palabras): tropiezos, «¿no?», ruidos."""
    for ln in lines:
        if ln.get("status") == "keep" and ln.get("words") and len(ln["words"]) <= max_words \
                and ln["end"] - ln["start"] <= max_s:
            ln["status"], ln["reason"] = "drop", "fragmento corto"


def mark_retakes(lines, lookahead=2):
    for i, a in enumerate(lines):
        if a.get("status") == "drop":
            continue
        for b in lines[i + 1:i + 1 + lookahead]:
            if b["src"] == a["src"] and not b.get("filler") and is_retake(a, b):
                a["status"], a["reason"], a["kept_as"] = "drop", "retoma", b["id"]
                break


def build_segments(lines, islands_by_src, pause_s, pad_in=0.06, min_gap_merge=0.05):
    """Convierte las líneas conservadas en segmentos [src, in, out] con pausas naturales.

    Al final de cada línea se conservan hasta `pause_s` de silencio (sin invadir la siguiente voz).
    """
    keep = [ln for ln in lines if ln.get("status") == "keep"]
    segs = []
    for idx, ln in enumerate(keep):
        src = ln["src"]
        nxt_voice = None
        for isl in islands_by_src.get(src, []):
            if isl[0] > ln["end"] + 0.01:
                nxt_voice = isl[0]
                break
        prev_voice_end = None
        for isl in islands_by_src.get(src, []):
            if isl[1] < ln["start"] - 0.01:
                prev_voice_end = isl[1]
        t_in = max(ln["start"] - pad_in, 0.0)
        if prev_voice_end is not None:
            t_in = max(t_in, prev_voice_end + 0.02)
        t_out = ln["end"] + pause_s
        if nxt_voice is not None:
            t_out = min(t_out, nxt_voice - 0.03)
        t_out = max(t_out, ln["end"])
        if segs and segs[-1]["src"] == src and t_in - segs[-1]["out"] <= min_gap_merge:
            segs[-1]["out"] = round(max(segs[-1]["out"], t_out), 3)
            segs[-1]["lines"].append(ln["id"])
        else:
            segs.append({"src": src, "in": round(t_in, 3), "out": round(t_out, 3), "lines": [ln["id"]]})
    return segs
