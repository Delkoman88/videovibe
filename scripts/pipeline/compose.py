#!/usr/bin/env python3
"""Genera el proyecto HyperFrames de una pieza a partir de su storyboard.

Uso: scripts/pipeline/compose.py --project <canal>/<pieza> --platform tiktok [--platform reels …]

Lee storyboard.json, captions/captions.json, cut/cut-map.json, la marca del canal (<canal>/brand.json),
sus paquetes de formatos (channel.json → format_packs) y presets/<plataforma>.json.
Escribe <pieza>/hf/ (un proyecto HyperFrames editable también en la app de escritorio):
  index.html                     raíz: video + cámara + escenas + CTA (texto = variable `cta_text`)
  compositions/captions.html     subtítulos palabra por palabra (track de captions)
  compositions/overlays.html     título y tarjetas HUD
  variables/<plataforma>.json    valores de variables por plataforma (para render --variables-file)
  assets/plate.mp4               el master con audio normalizado a -14 LUFS (video copiado sin recomprimir)
  assets/fonts/, assets/vendor/  fuentes de marca y GSAP local (render sin internet)

storyboard.json lo escribe el agente: formato en docs/storyboard.md; lo permitido lo valida scripts/pipeline/storyboard.py
(la fuente de verdad), que este script corre antes de componer.
El código está repartido en scripts/composer/: visual.py (HTML), audio.py (mezcla), credits.py (assets.md),
plate.py (placa de video) y context.py. Este archivo solo orquesta. Antes de componer valida el storyboard
(scripts/pipeline/storyboard.py) y se detiene con todos los problemas juntos.
Salida JSON en stdout. Exit 0 ok, 2 error.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import formats  # noqa: E402
from scripts.core import oslib  # noqa: E402
from scripts.pipeline import storyboard  # noqa: E402
from scripts.audio import voice  # noqa: E402
from scripts.composer.audio import (audio_markup, db, duck_lane, exit_cues, music_src_for,  # noqa: E402,F401
                            scene_cues, speech_intervals)
from scripts.composer.context import Ctx, font_faces  # noqa: E402
from scripts.composer.credits import (AUTO_BEGIN, AUTO_END, audio_credits_md, update_assets_md,
                              update_broll_credits)  # noqa: E402,F401
from scripts.composer.plate import build_plate  # noqa: E402
from scripts.composer.visual import captions_html, index_html, overlays_html, safe_zone  # noqa: E402


def prepare_broll(P, sb, hf, media):
    """Convierte los insertos usados a H.264 SDR sin audio; conserva raw/ intacto."""
    used = {clip["source"] for clip in sb.get("broll", [])}
    for old in (hf / "assets").glob("broll-*.mp4"):
        if old.stem.removeprefix("broll-") not in used:
            old.unlink()
    for source in used:
        m = media[source]
        raw = P / m["file"]
        out = hf / "assets" / f"broll-{source}.mp4"
        if out.exists() and out.stat().st_mtime >= raw.stat().st_mtime:
            continue
        if m.get("hdr") and not oslib.has_filter("zscale"):
            oslib.die("un inserto HDR necesita ffmpeg-full con zscale (bin/doctor)")
        vf = ((oslib.TONEMAP_SDR + "," if m.get("hdr") else "")
              + "fps=30,setsar=1,format=yuv420p,"
              "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709")
        oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-i", str(raw), "-an", "-vf", vf,
                   "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                   "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709",
                   "-movflags", "+faststart", str(out)])


def prepare_hf(P, ch, brand):
    """Carpeta hf/ con fuentes de marca, GSAP (npm) y la configuración del proyecto HyperFrames."""
    hf = P / "hf"
    (hf / "compositions").mkdir(parents=True, exist_ok=True)
    (hf / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    (hf / "assets" / "vendor").mkdir(parents=True, exist_ok=True)
    for key in ("display", "mono"):
        shutil.copy(oslib.font_file(ch, key), hf / "assets" / "fonts" / brand["fonts"][key]["file"])
    gsap = oslib.ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"  # versión fijada en package.json
    if not gsap.exists():
        oslib.die("falta GSAP: corre `npm install` en la raíz del repo (bin/setup lo hace)")
    shutil.copy(gsap, hf / "assets" / "vendor" / "gsap.min.js")
    return hf


def write_plate(P, ch, sb, hf):
    """Voz tratada (scripts/audio/voice.py) + placa a −14 LUFS + último cuadro para la cola (tail_s)."""
    voice_wav, _ = voice.ensure_voice(P, voice.config(P, ch["config"], sb))
    build_plate(P / "cut" / "master-cut.mp4", hf / "assets" / "plate.mp4", voice_wav)
    oslib.run([oslib.FFMPEG, "-y", "-v", "error", "-sseof", "-0.1", "-i", str(hf / "assets" / "plate.mp4"),
               "-frames:v", "1", "-update", "1", str(hf / "assets" / "last-frame.png")])
    if not (hf / "hyperframes.json").exists():
        oslib.write_json(hf / "hyperframes.json", {
            "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
            "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
            "media": {"autoProxy": True}})
        oslib.write_json(hf / "meta.json", {"id": P.name, "name": P.name})


def apply_grading(sb, hf, packs):
    """Corrección de color por la vía oficial de HyperFrames (media-treatment), no a mano."""
    if not sb.get("grading"):
        return
    sels = ["#plate"] + (["#hold"] if sb.get("tail_s") else [])
    sels += [f'#bv-{sc["id"]}' for sc in sb.get("scenes", [])
             if (sc.get("layout") or formats.default_layout(sc["format"], packs)) == "bubble"]
    for sel in sels:
        oslib.run([str(oslib.ROOT / "node_modules" / ".bin" / "hyperframes"), "media-treatment", "--project", str(hf),
                   "--file", "index.html", "--selector", sel,
                   "--grading", json.dumps(sb["grading"]), "--apply", "--json"])


def platform_variables(hf, sb, platforms, default_cta, music_srcs):
    """hf/variables/<plataforma>.json: CTA y pista de música de cada plataforma (render --variables-file)."""
    plats = sb.get("platforms", {})
    out = []
    (hf / "variables").mkdir(exist_ok=True)
    for plat in platforms:
        vals = {"cta_text": plats.get(plat, {}).get("cta_text") or default_cta or ""}
        if music_srcs:
            msrc = music_src_for(oslib.load_preset(plat), music_srcs)
            if not msrc:
                oslib.die(f"la plataforma {plat} es de pauta pagada y no hay pista con licencia para anuncios: "
                          "registra una con scripts/audio/music.py add … --ads (o pon audio.music.ads_track)")
            vals["music_src"] = msrc
        oslib.write_json(hf / "variables" / f"{plat}.json", vals)
        out.append(f"hf/variables/{plat}.json")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--platform", action="append", required=True)
    args = ap.parse_args()

    P = oslib.project_dir(args.project)
    sb = oslib.read_json(P / "storyboard.json")
    caps = oslib.read_json(P / "captions" / "captions.json")
    cmap = oslib.read_json(P / "cut" / "cut-map.json")
    ch = oslib.load_channel(P)
    brand = ch["brand"]
    ctx = Ctx(brand=brand, packs=tuple(ch["config"].get("format_packs", [])), font_faces=font_faces(brand),
              lang=ch["lang"]["code"])
    formats.configure(ctx.font_faces, ch["lang"]["labels"])
    problems, _ = storyboard.validate(sb, storyboard.context(P, ch))  # todos los errores juntos, antes de nada
    if problems:
        oslib.emit({"ok": False, "error": "storyboard.json tiene problemas (scripts/pipeline/storyboard.py)",
                    "problems": problems}, 2)
    sb["_lang"] = ctx.lang

    hf = prepare_hf(P, ch, brand)
    write_plate(P, ch, sb, hf)
    media = {m["id"]: m for m in oslib.read_json(P / "media.json")["items"]}
    prepare_broll(P, sb, hf, media)

    dur = round(cmap["duration_s"], 3)
    total = round(dur + sb.get("tail_s", 0), 3)
    sb["_duration"] = total
    cuts = [s["out_out"] for s in cmap["segments"]]
    # zona segura: la más estricta entre las plataformas pedidas
    safes = [safe_zone(oslib.load_preset(p)) for p in args.platform]
    safe = {"text_top": max(x["text_top"] for x in safes), "text_bottom": min(x["text_bottom"] for x in safes)}
    for old in list(hf.glob("index-*.html")) + list((hf / "compositions").glob("overlays-*.html")):
        old.unlink()
    (hf / "compositions" / "captions.html").write_text(
        captions_html(caps, sb.get("emphasis", {}), brand, safe, ctx), encoding="utf-8")
    (hf / "compositions" / "overlays.html").write_text(overlays_html(sb, brand, safe, ctx), encoding="utf-8")
    for old in (hf / "compositions").glob("scene-*.html"):
        old.unlink()
    for sc in sb.get("scenes", []):
        (hf / "compositions" / f"scene-{sc['id']}.html").write_text(formats.render(sc, ctx.packs), encoding="utf-8")
    default_cta = sb.get("platforms", {}).get(args.platform[0], {}).get("cta_text")
    shutil.rmtree(hf / "assets" / "audio", ignore_errors=True)
    plan = audio_markup(sb, ch, caps, total, hf)
    update_assets_md(P, audio_credits_md(plan.credits))
    update_broll_credits(P, sb.get("broll", []), media)
    (hf / "index.html").write_text(index_html(sb, brand, safe, dur, total, cuts, default_cta, plan.els, ctx,
                                              plan.music_srcs, media), encoding="utf-8")
    apply_grading(sb, hf, ctx.packs)
    out_files = ["hf/index.html"] + platform_variables(hf, sb, args.platform, default_cta, plan.music_srcs)
    oslib.update_status(P, "composicion", pending="revisión B (hoja + borrador)")
    oslib.emit({"ok": True, "files": out_files, "duration_s": total, "groups": len(caps["groups"]),
                "overlays": len(sb.get("overlays", [])), "scenes": len(sb.get("scenes", [])),
                "broll": len(sb.get("broll", [])), "audio": plan.used,
                "camera_moves": len(sb.get("camera", {}).get("moves", [])),
                "next": "cd hf && npx hyperframes check --json; luego snapshot --review (punto B)"})


if __name__ == "__main__":
    main()
