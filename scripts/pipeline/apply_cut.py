#!/usr/bin/env python3
"""Aplica el corte aprobado: genera el master cortado y la transcripción re-mapeada.

Uso: scripts/pipeline/apply_cut.py --project <canal>/<pieza> [--platform tiktok] [--crf 16]

Lee cut/cut-list.json (líneas con status keep/drop) y escribe:
  cut/master-cut.mp4         las líneas conservadas, en orden, con pausas naturales y micro-fundidos
                             de audio (sin clics). Normalizado al lienzo del preset (por defecto 1080x1920@30),
                             con keyframes densos para que el render posterior pueda buscar rápido.
  cut/cut-map.json           cada segmento: fuente, tiempos en la fuente y en el master
  transcript/master-cut.remap.json  palabras de la toma re-mapeadas al master (referencia; los subtítulos
                             definitivos los hace captions.py en transcript/master-cut.json)

Tomas HDR (HLG/PQ, típico de teléfonos) se convierten a SDR BT.709 (requiere zscale: ffmpeg-full).
Micrófono externo (media.json → <toma>.mic, lo empareja ingest.py): el audio de cada segmento sale del
micrófono, con su desfase evaluado en el centro del segmento (corrige la deriva por tramos). Antes se
comprueba que ese tramo esté cubierto y que el desfase residual sea ≤ 20 ms; si no, ese segmento usa el
audio de la cámara y queda anotado en cut-map.json. --audio camara fuerza el audio de la cámara.
Verifica que la duración del archivo coincida con la suma de segmentos y que salga etiquetado BT.709.
Salida JSON en stdout. Exit 0 ok, 1 verificación fallida, 2 error.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import cutlib  # noqa: E402
from scripts.core import oslib  # noqa: E402

MAX_RESIDUAL_MS = 20.0

FADE = 0.012


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--platform", default="tiktok", help="preset del que se toma el lienzo")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--audio", choices=["auto", "camara"], default="auto",
                    help="auto: micrófono externo si la toma lo tiene (ingest.py); camara: siempre el de la cámara")
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    cut = oslib.read_json(P / "cut" / "cut-list.json")
    ch = oslib.load_channel(P)
    canvas = oslib.load_preset(args.platform)["canvas"]
    W, H, FPS = canvas["width"], canvas["height"], canvas["fps"]
    media = {m["id"]: m for m in oslib.read_json(P / "media.json")["items"]}

    transcripts = {s: oslib.read_json(P / "transcript" / f"{s}.json") for s in cut["sources"]}
    islands = {s: t["islands"] for s, t in transcripts.items()}
    segs = cutlib.build_segments(cut["lines"], islands, cut["pause_s"])
    for sg in segs:  # la pausa tras la última frase no puede pasar del final de la toma
        end = float(media[sg["src"]].get("duration_s") or 0)
        if end and sg["out"] > end - 0.01:
            sg["out"] = round(end - 0.01, 3)
    segs = [sg for sg in segs if sg["out"] - sg["in"] > 0.05]
    if not segs:
        oslib.die("ninguna línea con status=keep")

    srcs = sorted({s["src"] for s in segs}, key=cut["sources"].index)
    inputs, idx = [], {}
    for s in srcs:
        idx[s] = len(idx)
        inputs += ["-i", str(P / media[s]["file"])]
    mic_idx, analysis = {}, {}
    if args.audio == "auto":
        for s in srcs:
            mic = media[s].get("mic")
            if mic and (P / mic["file"]).exists():
                if mic["file"] not in mic_idx:
                    mic_idx[mic["file"]] = len(idx) + len(mic_idx)
                    inputs += ["-i", str(P / mic["file"])]
                oslib.ensure_venv()
                from scripts.audio import audiosync
                analysis[s] = (oslib.load_audio(P / "work" / "audio" / f"{s}.cam.wav", audiosync.SR),
                               oslib.load_audio(P / "work" / "audio" / f"{s}.wav", audiosync.SR))

    def audio_source(sg):
        """('mic', input, desfase, residual_ms) o ('camara', input, 0, motivo)."""
        m = media[sg["src"]].get("mic")
        if sg["src"] not in analysis:
            return "camara", idx[sg["src"]], 0.0, None
        from scripts.audio import audiosync
        if not audiosync.covered(m, sg["in"], sg["out"]):
            return "camara", idx[sg["src"]], 0.0, "el micrófono no cubre este tramo"
        cam16, mic16 = analysis[sg["src"]]
        r = audiosync.residual(cam16, mic16, sg["in"], sg["out"])
        if r is not None and abs(r) > MAX_RESIDUAL_MS:
            return "camara", idx[sg["src"]], 0.0, f"desfase residual {r} ms"
        return "mic", mic_idx[m["file"]], audiosync.offset_at(m, (sg["in"] + sg["out"]) / 2), r

    def is_hdr(s):
        if "hdr" in media[s]:
            return media[s]["hdr"]
        v = next(x for x in oslib.ffprobe(P / media[s]["file"])["streams"] if x["codec_type"] == "video")
        return v.get("color_transfer") in oslib.HDR_TRANSFERS

    hdr = {s for s in srcs if is_hdr(s)}
    if hdr and not oslib.has_filter("zscale"):
        oslib.die("hay tomas HDR y este ffmpeg no tiene zscale: instala ffmpeg-full (INSTALL.es.md)")

    parts, labels, t_out, cmap = [], [], 0.0, []
    for k, s in enumerate(segs):
        n, a, b = idx[s["src"]], s["in"], s["out"]
        d = b - a
        parts.append(
            f"[{n}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,fps={FPS},"
            + (oslib.TONEMAP_SDR + "," if s["src"] in hdr else "") +
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,format=yuv420p[v{k}]")
        kind, ai, off, note = audio_source(s)
        parts.append(
            f"[{ai}:a]atrim=start={a + off:.5f}:end={b + off:.5f},asetpts=PTS-STARTPTS,aresample=48000,"
            f"aformat=sample_rates=48000:channel_layouts=stereo,"
            f"afade=t=in:d={FADE},afade=t=out:st={max(d - FADE, 0):.3f}:d={FADE}[a{k}]")
        labels.append(f"[v{k}][a{k}]")
        entry = {"src": s["src"], "src_in": a, "src_out": b, "out_in": round(t_out, 3),
                 "out_out": round(t_out + d, 3), "lines": s["lines"], "audio": kind}
        if kind == "mic":
            entry.update({"mic_offset_s": round(off, 5), "residual_ms": note})
        elif note:
            entry["audio_note"] = note
        cmap.append(entry)
        t_out += d
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"

    out = P / "cut" / "master-cut.mp4"
    graph_file = P / "work" / "apply-cut.filter"
    graph_file.parent.mkdir(parents=True, exist_ok=True)
    graph_file.write_text(graph, encoding="utf-8")
    oslib.run([oslib.FFMPEG, "-y", "-v", "error", *inputs, "-/filter_complex", str(graph_file),
               "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
               "-g", str(FPS // 2), "-keyint_min", str(FPS // 2), "-pix_fmt", "yuv420p",
               "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-color_range", "tv",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)])

    # transcripción re-mapeada al master
    keep_ids = {l["id"] for l in cut["lines"] if l["status"] == "keep"}
    words_out = []
    for c in cmap:
        for w in transcripts[c["src"]]["words"]:
            if w["start"] >= c["src_in"] - 0.07 and w["end"] <= c["src_out"] + 0.02:
                words_out.append({"w": w["w"], "start": round(c["out_in"] + max(w["start"], c["src_in"]) - c["src_in"], 3),
                                  "end": round(c["out_in"] + min(w["end"], c["src_out"]) - c["src_in"], 3),
                                  "p": w.get("p", 1), "src": c["src"]})
    oslib.write_json(P / "cut" / "cut-map.json", {"platform_canvas": args.platform, "width": W, "height": H,
                                                   "fps": FPS, "duration_s": round(t_out, 3), "segments": cmap})
    # transcripción re-mapeada: archivo aparte; transcript/master-cut.json es de captions.py (puede tener correcciones a mano)
    oslib.write_json(P / "transcript" / "master-cut.remap.json",
                     {"id": "master-cut", "language": ch["lang"]["code"], "words": words_out})

    probe = oslib.ffprobe(out)
    real = float(probe["format"]["duration"])
    trc = next(s for s in probe["streams"] if s["codec_type"] == "video").get("color_transfer")
    ok = abs(real - t_out) <= max(0.1, 2 / FPS) and trc in ("bt709", None)
    if ok:
        oslib.update_status(P, "corte-aplicado")
    oslib.emit({"ok": ok, "master": str(out.relative_to(P)), "duration_s": round(real, 3), "color_transfer": trc, "tonemapped": sorted(hdr),
                "expected_s": round(t_out, 3), "segments": len(segs), "kept_lines": len(keep_ids),
                "words": len(words_out),
                "audio": {"mic": sum(c["audio"] == "mic" for c in cmap),
                          "camara": sum(c["audio"] == "camara" for c in cmap),
                          "fallbacks": [{"out_in": c["out_in"], "why": c["audio_note"]} for c in cmap if c.get("audio_note")]},
                "next": "Siguiente etapa: plan visual (storyboard.json, fase 2)" if ok else "La duración no coincide: revisa los segmentos en cut-map.json"}, 0 if ok else 1)


if __name__ == "__main__":
    main()
