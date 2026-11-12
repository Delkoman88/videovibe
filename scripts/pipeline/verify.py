#!/usr/bin/env python3
"""Verificación de entrega: ¿cada render cumple el preset de su plataforma? Exit 1 = NO entregar.

Uso: scripts/pipeline/verify.py --project <canal>/<pieza> --platform tiktok [--platform reels …]

Por plataforma comprueba renders/<plataforma>.mp4 contra presets/<plataforma>.json y el storyboard:
  resolución y fps del lienzo, H.264 + yuv420p, color BT.709 (no HDR), audio AAC 48 kHz,
  volumen integrado −14 LUFS (±1), pico ≤ −1 dBTP, duración = master + tail_s (±0.2 s),
  y que existan captions/<plat>.srt, copy/<plat>.md y covers/<plat>.jpg.
Salida JSON en stdout. Exit 0 todo bien, 1 algo falla, 2 error de uso.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402


def loudness(path):
    r = subprocess.run([oslib.FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    pk = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return (float(i.group(1)) if i else None, float(pk.group(1)) if pk else None)


def check_platform(P, plat, sb, cmap):
    preset = oslib.load_preset(plat)
    canvas, exp = preset["canvas"], preset.get("export", {})
    f = P / "renders" / f"{plat}.mp4"
    res = {"platform": plat, "file": str(f.relative_to(P)), "checks": []}

    def ok(name, cond, got, want):
        res["checks"].append({"check": name, "ok": bool(cond), "got": got, "want": want})

    if not f.exists():
        ok("archivo", False, "no existe", str(f.relative_to(P)))
        return res
    info = oslib.ffprobe(f)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), {})
    num, den = v.get("r_frame_rate", "0/1").split("/")
    fps = round(float(num) / float(den), 2)
    ok("resolución", (v["width"], v["height"]) == (canvas["width"], canvas["height"]),
       f'{v["width"]}x{v["height"]}', f'{canvas["width"]}x{canvas["height"]}')
    ok("fps", abs(fps - canvas["fps"]) < 0.05, fps, canvas["fps"])
    ok("códec", v.get("codec_name") == exp.get("vcodec", "h264"), v.get("codec_name"), exp.get("vcodec", "h264"))
    ok("pixel", v.get("pix_fmt") == exp.get("pix_fmt", "yuv420p"), v.get("pix_fmt"), exp.get("pix_fmt", "yuv420p"))
    ok("color BT.709", v.get("color_transfer") in ("bt709", None) and v.get("color_primaries") in ("bt709", None),
       f'{v.get("color_transfer")}/{v.get("color_primaries")}', "bt709/bt709")
    ok("audio", a.get("codec_name") == "aac" and int(a.get("sample_rate", 0)) == exp.get("audio_rate", 48000),
       f'{a.get("codec_name")} {a.get("sample_rate")}', f'aac {exp.get("audio_rate", 48000)}')
    lufs, peak = loudness(f)
    target = exp.get("loudness_lufs", -14)
    ok("volumen", lufs is not None and abs(lufs - target) <= 1.0, lufs, f"{target} ±1 LUFS")
    ok("pico", peak is not None and peak <= exp.get("true_peak_db", -1), peak, f'≤ {exp.get("true_peak_db", -1)} dB')
    dur = float(info["format"]["duration"])
    want = cmap["duration_s"] + sb.get("tail_s", 0)
    ok("duración", abs(dur - want) <= 0.2, round(dur, 2), round(want, 2))
    for name, path in [("subtítulos", P / "captions" / f"{plat}.srt"), ("copy", P / "copy" / f"{plat}.md"),
                       ("portada", P / "covers" / f"{plat}.jpg")]:
        ok(name, path.exists(), str(path.relative_to(P)) if path.exists() else "falta", "existe")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--platform", action="append", required=True)
    args = ap.parse_args()
    P = oslib.project_dir(args.project)
    sb = oslib.read_json(P / "storyboard.json")
    cmap = oslib.read_json(P / "cut" / "cut-map.json")
    results = [check_platform(P, plat, sb, cmap) for plat in args.platform]
    failed = [f'{r["platform"]}: {c["check"]} (tiene {c["got"]}, debe {c["want"]})'
              for r in results for c in r["checks"] if not c["ok"]]
    if not failed:
        oslib.update_status(P, "entregable", renders={r["platform"]: r["file"] for r in results})
    oslib.emit({"ok": not failed, "failed": failed, "results": results}, 0 if not failed else 1)


if __name__ == "__main__":
    main()
