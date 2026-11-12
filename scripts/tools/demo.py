#!/usr/bin/env python3
"""Demo de punta a punta: edita un video de prueba en el canal de ejemplo science-60.

Uso: bin/demo [--quick] [--lang es|en]

1. Crea una copia del canal de ejemplo en work/demo/canales/ (no toca nada del repo).
2. Genera una «toma» con voz sintética (macOS `say`; Linux `espeak-ng`) que incluye una retoma y una
   muletilla, para que se vea cómo trabaja el corte.
3. Corre bin/edit y aprueba las revisiones A y B automáticamente (en una pieza real las aprueba la persona).
4. Escribe el plan visual (gancho, una animación, CTA, música propia y efectos), el copy y la portada.
5. Renderiza la versión TikTok y la verifica. Con --quick se detiene en el borrador (≈ la mitad de tiempo).

Salida: la ruta del video. Exit 0 ok, 1 fallo, 2 error de uso.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str(ROOT / ".venv" / "bin" / "python")
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

FF = oslib.FFMPEG
TEXTS = {
    "es": ("¿Por qué sube el pan? [[slnc 700]] Porque la levadura come azúcar [[slnc 600]] "
           "Porque la levadura come azúcar y suelta dióxido de carbono. [[slnc 900]] eh [[slnc 600]] "
           "Ese gas queda atrapado en la masa y la infla como un globo. [[slnc 800]] "
           "Sígueme para la próxima pregunta."),
    "en": ("Why does bread rise? [[slnc 700]] Because yeast eats sugar [[slnc 600]] "
           "Because yeast eats sugar and releases carbon dioxide. [[slnc 900]] um [[slnc 600]] "
           "That gas gets trapped in the dough and inflates it like a balloon. [[slnc 800]] "
           "Follow me for the next question."),
}
VOICES = {"es": ["Paulina", "Mónica", "Jorge"], "en": ["Samantha", "Alex", "Daniel"]}
UI = {
    "es": {"hook": "¿Por qué sube el pan?", "kicker": "Ciencia en 60 segundos", "cta": "Sígueme para la próxima pregunta",
           "label": "LEVADURA + AZÚCAR → CO₂"},
    "en": {"hook": "Why does bread rise?", "kicker": "Science in 60 seconds", "cta": "Follow me for the next question",
           "label": "YEAST + SUGAR → CO₂"},
}


def log(msg):
    print(f"\033[1m==> {msg}\033[0m", flush=True)


def run(cmd, env, check=True, quiet=False):
    r = subprocess.run([str(c) for c in cmd], env=env, cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode not in (0,):
        print(r.stdout[-3000:], r.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    return r


def synth_voice(text, lang, out_wav):
    """Voz sintética: macOS `say` (con pausas [[slnc]]) o espeak-ng (las pausas se vuelven comas)."""
    forced = os.environ.get("VIDEOVIBE_DEMO_TTS")  # say | espeak (por defecto: el que haya)
    if shutil.which("say") and forced != "espeak":
        voices = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        v = next((x for x in VOICES[lang] if x in voices), None)
        aiff = out_wav.with_suffix(".aiff")
        subprocess.run(["say", *(["-v", v] if v else []), "-o", str(aiff), text], check=True)
        return aiff
    if shutil.which("espeak-ng"):
        import re
        plain = re.sub(r"\[\[slnc \d+\]\]", ",", text)
        subprocess.run(["espeak-ng", "-v", lang, "-s", "150", "-w", str(out_wav), plain], check=True)
        return out_wav
    sys.exit("Para la demo hace falta una voz sintética: macOS `say` o Linux `espeak-ng` (apt install espeak-ng).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="detenerse en el borrador (sin render final)")
    ap.add_argument("--lang", choices=["es", "en"], default="es")
    args = ap.parse_args()
    if not Path(PY).exists():
        sys.exit("Falta el entorno: corre bin/setup primero.")

    base = ROOT / "work" / "demo"
    chans = base / "canales"
    if base.exists():
        shutil.rmtree(base)
    chans.mkdir(parents=True)
    shutil.copytree(ROOT / "channels" / "science-60", chans / "science-60",
                    ignore=shutil.ignore_patterns("projects"))
    cfg = json.loads((chans / "science-60" / "channel.json").read_text())
    cfg.update({"language": args.lang, "platforms": ["tiktok"]})
    (chans / "science-60" / "channel.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    env = {**os.environ, "VIDEOVIBE_CHANNELS": str(chans), "VIDEOVIBE_DEMO": "1",
           "VIDEOVIBE_DELIVERIES": str(base / "deliveries")}  # la demo no llena tus deliveries/
    piece = f"{datetime.date.today().isoformat()}-demo"
    P = chans / "science-60" / "projects" / piece
    (P / "raw").mkdir(parents=True)
    ref = f"science-60/{piece}"

    log("1/6 Toma de prueba con voz sintética")
    voice = synth_voice(TEXTS[args.lang], args.lang, base / "voz.wav")
    # imagen: la forma de onda de la voz sobre fondo oscuro (no hay cámara en una demo)
    run([FF, "-y", "-v", "error", "-i", voice, "-filter_complex",
         "[0:a]showwaves=s=1080x1920:mode=cline:colors=0xFFB000:rate=30,format=yuv420p[v]",
         "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-c:a", "aac", "-shortest", P / "raw" / "toma.mp4"], env)
    (P / "brief.md").write_text(f"# Brief (demo)\n\n- Objetivo: mostrar el flujo completo.\n- Audiencia: curiosos.\n"
                                f"- Material: raw/toma.mp4 (voz sintética).\n- CTA: {UI[args.lang]['cta']}\n"
                                f"- ¿Publicidad pagada?: no\n")

    log("2/6 Transcripción y corte en papel (bin/edit → revisión A)")
    out = run([ROOT / "bin" / "edit", ref], env, check=False)
    st = json.loads((P / "status.json").read_text())
    if st.get("pending") != "aprobación A":
        print(out.stdout[-2000:], out.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
    cut = json.loads((P / "cut" / "cut-list.json").read_text())
    dropped = [f"{l.get('reason')}: «{l['text']}»" for l in cut["lines"] if l["status"] == "drop"]
    print("   El corte quitó:", *dropped, sep="\n   - ")
    run([ROOT / "bin" / "review", ref, "--gate", "A", "--simulated", "--no-open"], env)
    run([ROOT / "bin" / "status", ref, "--approve", "A", "--note", "demo: aprobación automática"], env)

    log("3/6 Corte aplicado y subtítulos (bin/edit → falta el plan visual)")
    out = run([ROOT / "bin" / "edit", ref], env, check=False)
    if not (P / "cut" / "cut-map.json").exists():  # el paso falló: mostrar el error real de bin/edit
        print(out.stdout[-3000:], out.stderr[-3000:], file=sys.stderr)
        log_tail = P / "work" / "edit.log"
        if log_tail.exists():
            print("work/edit.log:", *log_tail.read_text().splitlines()[-5:], sep="\n", file=sys.stderr)
        sys.exit(1)
    cmap = json.loads((P / "cut" / "cut-map.json").read_text())
    dur = cmap["duration_s"]

    log("4/6 Música propia y plan visual")
    mus = run([PY, "-m", "scripts.audio.musicgen", "--channel", "science-60", "--duration", f"{dur + 2.0:.2f}",
               "--mood", "esperanzador", "--seed", "3", "--add", "--title", "Demo"], env)
    track = json.loads(mus.stdout)["added"]
    ui = UI[args.lang]
    mid = round(dur * 0.45, 2)
    sb = {
        "version": 1, "video": "cut/master-cut.mp4", "tail_s": 1.5,
        "camera": {"origin": "50% 50%", "moves": []},
        "emphasis": {},
        "overlays": [
            {"id": "hook", "type": "title", "in": 0.15, "out": min(3.0, dur * 0.25), "kicker": ui["kicker"],
             "text": ui["hook"], "role": "keyword"},
            {"id": "cta", "type": "cta", "in": round(dur - 2.5, 2), "out": round(dur + 1.5, 2), "kicker": ui["kicker"],
             "text": ui["cta"], "role": "punchline"},
        ],
        "scenes": [{"id": "s-dna", "format": "dna-helix", "in": mid, "out": round(mid + 2.5, 2), "layout": "full",
                    "params": {"label": ui["label"]}, "sfx": "sparkle"}],
        "platforms": {"tiktok": {"cta_text": ui["cta"]}},
        "audio": {"music": {"track": track, "start": 0, "fade_in": 1.0, "fade_out": 1.0, "ads": "quiza"},
                  "sfx_auto": {"scenes": "variado", "overlays": "click", "exits": "whoosh", "db": -22, "exits_db": -26}},
    }
    (P / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2))

    log("5/6 Composición, verificación y borrador (bin/edit → revisión B)")
    out = run([ROOT / "bin" / "edit", ref], env, check=False)
    draft = P / "renders" / "draft-tiktok.mp4"
    if not draft.exists():
        print(out.stdout[-3000:], out.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    if args.quick:
        log(f"Listo (rápido). Borrador: {draft}")
        return
    run([ROOT / "bin" / "review", ref, "--gate", "B", "--simulated", "--no-open"], env)
    run([ROOT / "bin" / "status", ref, "--approve", "B", "--note", "demo: aprobación automática"], env)
    (P / "copy").mkdir(exist_ok=True)
    (P / "copy" / "tiktok.md").write_text(f"# TikTok — copy (demo)\n\n{ui['hook']}\n\n#ciencia #demo\n")
    run([PY, "-m", "scripts.pipeline.cover", "--project", ref, "--platform", "tiktok"], env)

    log("6/6 Render final y verificación de entrega")
    out = run([ROOT / "bin" / "edit", ref], env, check=False)
    final = P / "renders" / "tiktok.mp4"
    st = json.loads((P / "status.json").read_text())
    if not final.exists() or st.get("stage") != "entregable":
        print(out.stdout[-3000:], out.stderr[-3000:], file=sys.stderr)
        sys.exit(1)
    log(f"Listo. Video: {final}")
    print(f"   Carpeta de la pieza: {P}\n   Siguiente paso: crea tu canal con bin/new-channel <id> y pídele a tu agente "
          "que lo complete (AGENTS.md).")


if __name__ == "__main__":
    main()
