"""Transiciones (`storyboard.json → transitions`, ADR 0028): capas que cubren el cuadro un instante, con el
máximo justo en `at` (el corte), para que el cambio de toma o de escena ocurra debajo.

Viven en su propia sub-composición (`compositions/transitions.html`), encima de la toma, el B-roll y las escenas,
y debajo de tarjetas y subtítulos. Solo CSS + GSAP con los colores de la marca: nada de shaders, sin red, y cada
estado se fija desde la línea de tiempo (render determinista). Sin `transitions`, no se genera nada.
"""
import math

from formats.core import esc
from formats.text import plain

from scripts.core.transition_contract import KINDS, DEFAULT_DURATION, SFX
W, H = 1080, 1920

CSS = """
    #root { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
    .tr { position: absolute; inset: 0; opacity: 0; }
    .tr-flash { background: radial-gradient(circle at 50% 45%, #ffffff 0%,
                color-mix(in srgb, var(--tr-color) 35%, #ffffff) 70%, color-mix(in srgb, var(--tr-color) 60%, #ffffff)); }
    .tr-wash { background: color-mix(in srgb, var(--tr-color) 70%, #fff6e8); mix-blend-mode: screen; }
    .tr-blob { position: absolute; width: 1500px; height: 1500px; border-radius: 50%; mix-blend-mode: screen;
               filter: blur(60px); }
    .tr-svg { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }
    .tr-row { position: absolute; left: -400px; width: 1880px; height: 162px; white-space: nowrap; overflow: hidden;
              font-family: var(--font-display); font-weight: 700; font-size: 132px; line-height: 162px;
              letter-spacing: .02em; text-transform: uppercase; background: var(--bg); }
    .tr-bar { position: absolute; left: 0; width: 1080px; opacity: 0; }
    .tr-rays { opacity: 0; position: absolute; left: -760px; top: -340px; width: 2600px; height: 2600px; border-radius: 50%;
               background: repeating-conic-gradient(from 0deg, var(--tr-color) 0deg 1.1deg, transparent 1.1deg 5deg);
               -webkit-mask-image: radial-gradient(circle, transparent 14%, #000 46%);
               mask-image: radial-gradient(circle, transparent 14%, #000 46%); }
"""


def _h(i, salt):
    """Hash determinista en [0, 1)."""
    x = (i * 374761393 + salt * 668265263 + 1442695041) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFF) / 0x10000


def _r(x):
    return round(x, 3)


def _zigzag():
    """Trazo a mano que barre el cuadro de arriba abajo: puntos y largo exacto (para dasharray)."""
    pts, y, k = [], -180.0, 0
    while y < H + 260:
        x = -300 if k % 2 == 0 else W + 300
        pts.append((x + (_h(k, 7) - .5) * 90, y))
        y += 200 + _h(k, 8) * 30
        k += 1
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    d = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    return d, math.ceil(length)


def _one(i, tr):
    """(html, js) de una transición. t0 = inicio, at = máximo (corte), t1 = final."""
    kind, at = tr["kind"], float(tr["at"])
    D = float(tr.get("duration", DEFAULT_DURATION))
    t0, t1 = _r(at - D / 2), _r(at + D / 2)
    rin, rout = _r(D / 2), _r(D / 2)
    tid = f"tr{i}"
    color = f'style="--tr-color: var(--{tr.get("role", "accent")})"'
    html, js = [], []
    if kind == "flash":
        html.append(f'<div class="tr tr-flash" id="{tid}" {color}></div>')
        js += [f'tl.fromTo("#{tid}", {{opacity: 0}}, {{opacity: 1, duration: {rin}, ease: "power3.in", immediateRender: false}}, {t0});',
               f'tl.to("#{tid}", {{opacity: 0, duration: {rout}, ease: "power2.out"}}, {_r(at)});']
    elif kind == "light-leak":
        blobs = [("accent", -380, 120), ("accent2", 260, 760), (tr.get("role", "accent3"), -120, 1260)]
        inner = "".join(
            f'<div class="tr-blob" id="{tid}-b{k}" style="opacity:0;left:{x}px;top:{y}px;'
            f'background:radial-gradient(circle, color-mix(in srgb, var(--{c}) 90%, #fff) 0%, transparent 62%)"></div>'
            for k, (c, x, y) in enumerate(blobs))
        html.append(f'<div class="tr" id="{tid}" style="opacity:1">{inner}<div class="tr tr-wash" id="{tid}-w" {color}></div></div>')
        for k in range(3):
            dx = (420 if k % 2 == 0 else -420)
            js += [f'tl.fromTo("#{tid}-b{k}", {{x: {-dx}, scale: .7, opacity: 0}}, {{x: {dx}, scale: 1.25, duration: {_r(D)}, '
                   f'ease: "sine.inOut", immediateRender: false}}, {t0});',
                   f'tl.fromTo("#{tid}-b{k}", {{opacity: 0}}, {{opacity: .95, duration: {rin}, ease: "sine.in", immediateRender: false}}, {t0});',
                   f'tl.to("#{tid}-b{k}", {{opacity: 0, duration: {rout}, ease: "sine.out"}}, {_r(at)});']
        js += [f'tl.fromTo("#{tid}-w", {{opacity: 0}}, {{opacity: .88, duration: {rin}, ease: "power2.in", immediateRender: false}}, {t0});',
               f'tl.to("#{tid}-w", {{opacity: 0, duration: {rout}, ease: "power2.out"}}, {_r(at)});']
    elif kind == "scribble":
        d, L = _zigzag()
        html.append(f'<svg class="tr-svg tr" id="{tid}" viewBox="0 0 {W} {H}" style="opacity:1">'
                    f'<path id="{tid}-a" d="{d}" fill="none" stroke="var(--{tr.get("role", "accent")})" stroke-width="470" '
                    f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L} {L}" stroke-dashoffset="{L}"/>'
                    f'<path id="{tid}-b" d="{d}" fill="none" stroke="var(--accent2)" stroke-width="70" stroke-linecap="round" '
                    f'stroke-linejoin="round" stroke-dasharray="{L} {L}" stroke-dashoffset="{L}" transform="translate(40 60)"/></svg>')
        for part, lag in (("a", 0), ("b", .06)):
            js += [f'tl.fromTo("#{tid}-{part}", {{strokeDashoffset: {L}}}, {{strokeDashoffset: 0, duration: {_r(D / 2 - lag)}, '
                   f'ease: "power1.inOut", immediateRender: false}}, {_r(t0 + lag)});',
                   f'tl.to("#{tid}-{part}", {{strokeDashoffset: {-L}, duration: {_r(D / 2 - lag)}, ease: "power1.inOut"}}, {_r(at)});']
    elif kind == "word-wall":
        word = esc(plain(tr.get("word", "")).upper())
        rows = []
        n = 12
        for k in range(n):
            c = ("accent", "text", "accent2")[k % 3]
            line = " · ".join([word] * 6)
            rows.append(f'<div class="tr-row" id="{tid}-r{k}" style="top:{k * 162}px;color:var(--{c})">{line}</div>')
        html.append(f'<div class="tr" id="{tid}" data-layout-ignore>{"".join(rows)}</div>')
        js += [f'tl.set("#{tid}-r{k}", {{x: {1900 if k % 2 == 0 else -1900}}}, {t0});' for k in range(n)]
        js += [f'tl.set("#{tid}", {{opacity: 1}}, {t0});', f'tl.set("#{tid}", {{opacity: 0}}, {t1});']
        for k in range(n):
            side = 1900 if k % 2 == 0 else -1900
            lag = _r(k * D * 0.02)
            js += [f'tl.fromTo("#{tid}-r{k}", {{x: {side}}}, {{x: {-120 if k % 2 else 0}, duration: {_r(rin - lag)}, '
                   f'ease: "power3.out", immediateRender: false}}, {_r(t0 + lag)});',
                   f'tl.to("#{tid}-r{k}", {{x: {-side}, duration: {_r(rout - lag)}, ease: "power3.in"}}, {_r(at + lag)});']
    elif kind == "glitch":
        bars = 7
        cols = ("accent", "accent2", "accent3", "text")
        inner = "".join(f'<div class="tr-bar" id="{tid}-g{k}" style="background:var(--{cols[k % 4]})"></div>'
                        for k in range(bars))
        html.append(f'<div class="tr" id="{tid}" style="opacity:1">{inner}'
                    f'<div class="tr" id="{tid}-full" style="background:var(--{tr.get("role", "accent2")})"></div></div>')
        steps = max(int(D / 0.05), 6)
        for s in range(steps):
            ts = _r(t0 + s * D / steps)
            near = abs(ts - at) <= 0.05
            for k in range(bars):
                on = near or _h(s * 31 + k, 3) < 0.55
                top = int(_h(s * 31 + k, 4) * (H - 120))
                hgt = int(30 + _h(s * 31 + k, 5) * (380 if near else 180))
                dx = int((_h(s * 31 + k, 6) - .5) * 160)
                js.append(f'tl.set("#{tid}-g{k}", {{opacity: {0.9 if on else 0}, top: {top}, height: {hgt}, x: {dx}}}, {ts});')
            js.append(f'tl.set("#{tid}-full", {{opacity: {0.92 if near else 0}}}, {ts});')
        js += [f'tl.set("#{tid}-g{k}", {{opacity: 0}}, {t1});' for k in range(bars)]
        js.append(f'tl.set("#{tid}-full", {{opacity: 0}}, {t1});')
    elif kind == "zoom-lines":
        html.append(f'<div class="tr" id="{tid}" style="opacity:1"><div class="tr-rays" id="{tid}-r" {color}></div>'
                    f'<div class="tr tr-flash" id="{tid}-f" {color}></div></div>')
        js += [f'tl.fromTo("#{tid}-r", {{scale: .35, rotation: -6}}, {{scale: 1.7, rotation: 6, '
               f'duration: {_r(D)}, ease: "power2.in", immediateRender: false}}, {t0});',
               f'tl.fromTo("#{tid}-r", {{opacity: 0}}, {{opacity: 1, duration: {rin}, ease: "power2.in", immediateRender: false}}, {t0});',
               f'tl.to("#{tid}-r", {{opacity: 0, duration: {_r(rout * .6)}, ease: "power2.out"}}, {_r(at)});',
               f'tl.fromTo("#{tid}-f", {{opacity: 0}}, {{opacity: .9, duration: {_r(rin * .5)}, ease: "power3.in", '
               f'immediateRender: false}}, {_r(at - rin * .5)});',
               f'tl.to("#{tid}-f", {{opacity: 0, duration: {_r(rout * .8)}, ease: "power2.out"}}, {_r(at)});']
    return "".join(html), js


def composition(sb, font_faces=""):
    """HTML de compositions/transitions.html, o None si la pieza no tiene transiciones."""
    items = sb.get("transitions") or []
    if not items:
        return None
    parts = [_one(i, tr) for i, tr in enumerate(sorted(items, key=lambda t: t["at"]))]
    html = "\n    ".join(h for h, _ in parts)
    js = "\n    ".join(x for _, j in parts for x in j)
    return f"""<template>
  <style>
    {font_faces}
{CSS}
  </style>
  <div id="root" data-composition-id="transitions" data-width="{W}" data-height="{H}" data-layout-allow-overlap>
    {html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {js}
    window.__timelines["transitions"] = tl;
  </script>
</template>
"""


def host(sb, total):
    """Etiqueta que monta la sub-composición en index.html (vacía sin transiciones: HTML de siempre)."""
    if not sb.get("transitions"):
        return ""
    return (f'      <div id="transitions" data-composition-id="transitions" data-composition-src="compositions/transitions.html"\n'
            f'           data-start="0" data-duration="{total}" data-track-index="3" data-track-kind="graphics"\n'
            f'           data-width="{W}" data-height="{H}"></div>\n')


def cues(sb, kit):
    """Efectos de sonido de las transiciones: empiezan al inicio para culminar en el corte. `sfx: false` lo quita;
    un nombre lo cambia. Si el sonido por defecto no está en el kit del canal, la transición va sin sonido."""
    out = []
    for tr in sb.get("transitions") or []:
        name = tr.get("sfx", SFX[tr["kind"]])
        if not name or name not in kit:
            continue
        D = float(tr.get("duration", DEFAULT_DURATION))
        lead = D / 2 if tr["kind"] in ("light-leak", "scribble", "zoom-lines") else 0.0
        out.append({"at": max(float(tr["at"]) - lead, 0), "sound": name, "db": float(tr.get("sfx_db", -18))})
    return out
