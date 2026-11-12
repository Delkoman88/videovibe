#!/usr/bin/env python3
"""Transcribe localmente (whisper.cpp, español) con tiempos por palabra corregidos por energía.

Uso: scripts/pipeline/transcribe.py --project <canal>/<pieza> [--id <media-id>] [--force]

Para cada elemento de media.json con audio escribe transcript/<id>.json:
  {"id", "language", "words": [{"w", "start", "end", "p"}], "islands": [[ini, fin], ...]}
`islands` son los tramos con voz detectados por energía: la referencia para silencios y cortes.

Por defecto (--mode islands) cada tramo se transcribe por separado y sus palabras se reparten dentro
del tramo por longitud: whisper no puede omitir ni desplazar palabras entre tramos. Con --mode full
se hace una pasada al archivo completo (con VAD) y las palabras se alinean a los tramos por
programación dinámica (ver align): más rápido, pero omite muletillas y frases cortas.
Los tramos sin texto quedan en `untranscribed_islands`; los descartados por parecer alucinación
(texto imposible para su duración, frases típicas de whisper) en `suspect_islands`.
El idioma y el vocabulario salen del canal (channel.json → language, vocabulary.txt): el vocabulario se
pasa a whisper como prompt para acertar términos técnicos.
Salida JSON en stdout. Exit 0 ok, 2 error.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()

# $VIDEOVIBE_WHISPER_MODEL permite otro modelo (p. ej. uno pequeño en CI); por defecto large-v3-turbo
DEFAULT_MODEL = Path(os.environ.get("VIDEOVIBE_WHISPER_MODEL")
                     or oslib.ROOT / "models" / "ggml-large-v3-turbo-q5_0.bin")
VAD_MODEL = oslib.ROOT / "models" / "ggml-silero-v5.1.2.bin"
SEC_PER_CHAR = 0.065  # velocidad media del habla en español (s por carácter), solo para alinear


# GPU: si whisper falla al usarla (sin GPU, o sandbox de un agente que bloquea Metal/CUDA), se reintenta sin
# GPU y no se vuelve a intentar en esta ejecución. VIDEOVIBE_WHISPER_CPU=1 la desactiva desde el principio.
_CPU_ONLY = {"on": os.environ.get("VIDEOVIBE_WHISPER_CPU") == "1", "fallback": False}


def _run_whisper(cmd):
    r = subprocess.run(cmd + (["-ng"] if _CPU_ONLY["on"] else []), capture_output=True, text=True)
    if r.returncode != 0 and not _CPU_ONLY["on"]:
        _CPU_ONLY.update(on=True, fallback=True)
        print("whisper falló con GPU; reintento sin GPU (más lento). Para evitar el intento: "
              "VIDEOVIBE_WHISPER_CPU=1", file=sys.stderr)
        r = subprocess.run(cmd + ["-ng"], capture_output=True, text=True)
    if r.returncode != 0:
        last = [l for l in r.stderr.strip().splitlines() if l.strip()][-3:]
        oslib.die("whisper-cli falló también sin GPU. Revisa el modelo (bin/doctor) y el audio. Últimas líneas: "
                  + " | ".join(last))


def whisper_words(wav, model, prompt, vad=True, language="es"):
    exe = shutil.which("whisper-cli") or oslib.die("whisper-cli no está en el PATH (bin/doctor)")
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "out")
        cmd = [exe, "-m", str(model), "-l", language, "-ojf", "-sow", "-ml", "1", "-f", str(wav), "-of", base, "-np"]
        if prompt:
            cmd += ["--prompt", prompt]
        if vad and VAD_MODEL.exists():  # mejora inicios de palabra y puntuación
            cmd += ["--vad", "-vm", str(VAD_MODEL)]
        _run_whisper(cmd)
        data = oslib.read_json(base + ".json")
    words = []
    for seg in data.get("transcription", []):
        text = seg.get("text", "").strip()
        if not text:
            continue
        toks = [t for t in seg.get("tokens", []) if not t["text"].startswith("[_")]
        p = sum(t.get("p", 1) for t in toks) / len(toks) if toks else 1.0
        words.append({"w": text, "start": seg["offsets"]["from"] / 1000, "end": seg["offsets"]["to"] / 1000, "p": round(p, 3)})
    return words


def _chars(w):
    return max(len(w["w"].strip(".,;:¿?¡!\"'")), 1)


def align(words, islands):
    """Asigna palabras consecutivas a tramos de voz consecutivos (programación dinámica).

    Coste por tramo: diferencia entre su duración y la duración estimada de sus palabras, más cuánto
    se salen del tramo los intervalos que dio whisper para esas palabras. Un tramo puede quedar vacío
    (ruido, respiración o muletilla que whisper omitió), con penalización proporcional a su duración.
    Devuelve, por tramo, el rango [i, j) de palabras.
    """
    n, m = len(words), len(islands)
    INF = float("inf")
    MAXG = 60
    est = [0.0]
    for w in words:
        est.append(est[-1] + _chars(w) * SEC_PER_CHAR)
    # fuera[k][q]: suma acumulada de cuánto NO se solapa el intervalo de whisper de cada palabra con el
    # tramo k (0 = cae dentro, 1 = fuera). Con VAD, la palabra junto a un silencio lo "absorbe", así que
    # su inicio no es fiable pero su intervalo sí toca el tramo correcto.
    fuera = []
    for a, b in islands:
        acc = [0.0]
        for w in words:
            ov = max(0.0, min(w["end"], b + 0.1) - max(w["start"], a - 0.1))
            ref = max(0.05, min(w["end"] - w["start"], _chars(w) * SEC_PER_CHAR))
            acc.append(acc[-1] + 1.0 - min(1.0, ov / ref))
        fuera.append(acc)
    best = [[INF] * (n + 1) for _ in range(m + 1)]
    back = [[0] * (n + 1) for _ in range(m + 1)]
    best[0][0] = 0.0
    for k in range(1, m + 1):
        a, b = islands[k - 1]
        dur = b - a
        empty = 0.25 + 1.5 * dur
        for j in range(n + 1):
            if best[k - 1][j] + empty < best[k][j]:
                best[k][j], back[k][j] = best[k - 1][j] + empty, j
            for i in range(max(0, j - MAXG), j):
                if best[k - 1][i] == INF:
                    continue
                e = est[j] - est[i]
                c = abs(dur - e) / max(dur, e, 0.3) + 1.0 * (fuera[k - 1][j] - fuera[k - 1][i])
                if best[k - 1][i] + c < best[k][j]:
                    best[k][j], back[k][j] = best[k - 1][i] + c, i
    ranges, j = [None] * m, n
    for k in range(m, 0, -1):
        i = back[k][j]
        ranges[k - 1] = (i, j)
        j = i
    return ranges


def refine(words, islands):
    """Coloca cada palabra dentro de su tramo de voz; dentro del tramo, reparte por longitud."""
    if not islands or not words:
        return words, []
    ranges = align(words, islands)
    empty = []
    for k, (i, j) in enumerate(ranges):
        a, b = islands[k]
        if i == j:
            empty.append(k)
            continue
        total = sum(_chars(words[q]) for q in range(i, j))
        t = a
        for q in range(i, j):
            d = (b - a) * _chars(words[q]) / total
            words[q]["start"], words[q]["end"], words[q]["island"] = round(t, 3), round(t + d, 3), k
            t += d
    return words, empty


def vocab_prompt(ch):
    """Prompt para whisper: nombre del canal + términos de su vocabulario."""
    if not ch["vocab"]:
        return ch["name"] + "."
    return f'{ch["name"]}. {ch["lang"]["vocab_label"]}: ' + ", ".join(ch["vocab"]) + "."




def _wav_chunk(audio, a0, b0, path, sr=oslib.SR):
    import wave
    import numpy as np
    chunk = (np.clip(audio[int(a0 * sr):int(b0 * sr)], -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(chunk.tobytes())


def transcribe_islands(audio, islands, model, base_prompt, lang, sr=oslib.SR):
    """Transcribe cada tramo de voz por separado (sin VAD), con el texto previo como contexto.

    Más fiable que una pasada sobre el archivo completo: whisper no puede omitir ni desplazar palabras
    entre tramos (sí lo hace con muletillas y frases cortas tras una pausa). Dentro de cada tramo las
    palabras se reparten por longitud. Devuelve (words, untranscribed_islands, suspects).
    """
    words, empty, suspects, context = [], [], [], []
    total = len(audio) / sr
    with tempfile.TemporaryDirectory() as td:
        for k, (a, b) in enumerate(islands):
            path = os.path.join(td, f"i{k}.wav")
            _wav_chunk(audio, max(0.0, a - 0.15), min(total, b + 0.15), path, sr)
            prompt = base_prompt + (" " + " ".join(context[-25:]) if context else "")
            ws = [w for w in whisper_words(path, model, prompt.strip(), vad=False, language=lang["whisper"])
                  if w["w"].strip()]
            text = " ".join(w["w"] for w in ws).lower()
            chars = sum(_chars(w) for w in ws)
            if not ws:
                empty.append(k)
                continue
            if any(h in text for h in lang["hallucinations"]) or chars > (b - a) * 28 + 6:
                suspects.append({"island": k, "start": a, "end": b, "text": text})
                empty.append(k)
                continue
            t, dur = a, b - a
            for w in ws:
                d = dur * _chars(w) / chars
                words.append({"w": w["w"], "start": round(t, 3), "end": round(t + d, 3), "p": w["p"], "island": k})
                t += d
            context.extend(w["w"] for w in ws)
    return words, empty, suspects


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--id", help="solo este elemento de media.json")
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--force", action="store_true", help="re-transcribir aunque exista")
    ap.add_argument("--mode", choices=["islands", "full"], default="islands")
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    if not (P / "media.json").exists():
        oslib.die("falta media.json: corre scripts/pipeline/ingest.py primero")
    if not Path(args.model).exists():
        oslib.die(f"no encuentro el modelo {args.model} (INSTALL.es.md)")
    ch = oslib.load_channel(P)
    prompt = vocab_prompt(ch)

    done = []
    for m in oslib.read_json(P / "media.json")["items"]:
        if not m.get("audio") or m.get("kind") == "mic" or (args.id and m["id"] != args.id):
            continue
        out = P / "transcript" / f"{m['id']}.json"
        if out.exists() and not args.force:
            done.append({"id": m["id"], "skipped": True})
            continue
        wav = P / m["audio"]
        audio = oslib.load_audio(wav)
        islands, stats = oslib.speech_islands(audio)
        suspects = []
        if args.mode == "islands":
            words, empty, suspects = transcribe_islands(audio, islands, args.model, prompt, ch["lang"])
        else:
            words, empty = refine(whisper_words(wav, args.model, prompt, language=ch["lang"]["whisper"]), islands)
        oslib.write_json(out, {"id": m["id"], "source": m["file"], "language": ch["lang"]["code"], "mode": args.mode,
                               "energy": stats, "islands": islands, "untranscribed_islands": empty,
                               "suspect_islands": suspects, "words": words})
        low = [w["w"] for w in words if w["p"] < 0.5]
        done.append({"id": m["id"], "words": len(words), "islands": len(islands), "untranscribed_islands": empty,
                     "suspect_islands": suspects,
                     "text": " ".join(w["w"] for w in words)[:300], "low_confidence": low[:20]})
    if not done:
        oslib.die("ningún elemento con audio para transcribir")
    oslib.update_status(P, "transcripcion")
    oslib.emit({"ok": True, "transcripts": done, "whisper_sin_gpu": _CPU_ONLY["on"], "next": "scripts/pipeline/paper_cut.py"})


if __name__ == "__main__":
    main()
