"""Paquete «motion»: tipografía cinética, datos, diagramas, transformaciones de icono, rutas y partículas.

Genérico (sirve a cualquier canal): colores y fuentes salen de la marca; los textos, del storyboard.
Usa plugins de GSAP (DrawSVG, MorphSVG, MotionPath, Physics2D) declarados en `needs` (formats/vendors.py).
Reglas de determinismo (ADR 0022): el texto se parte en Python (no depende de que cargue la fuente) y el
efecto «descifrar» usa un hash del cuadro, nunca azar en tiempo de render.
Se activa en un canal con channel.json → "format_packs": [..., "motion"].
"""
import math
import re

from formats import icons
from formats.core import CTX, _rand, esc, fmt, wrap
from formats.text import KINETIC_CSS, VARIANTS, kinetic as _kinetic, kinetic_in, kinetic_out, plain as _plain, title_size as _title_size

ACCENTS = ("accent", "accent2", "accent3")

# Hash determinista por (índice, cuadro): caracteres «descifrándose» sin azar.
SCRAMBLE_JS = """
    const vvGlyphs = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#%&@$";
    const vvHash = (i, f) => { let x = (Math.imul(i + 1, 374761393) + Math.imul(f + 7, 668265263)) >>> 0;
      x = Math.imul(x ^ (x >>> 13), 1274126177) >>> 0; return x ^ (x >>> 16); };
    const vvScramble = (text, progress, frame) => [...text].map((c, i) => {
      if (c === " " || i < Math.floor(progress * text.length)) return c;
      return /[0-9]/.test(c) ? String(vvHash(i, frame) % 10) : vvGlyphs[vvHash(i, frame) % vvGlyphs.length];
    }).join("");"""


# ---------------------------------------------------------------- utilidades

def _steps(p, key):
    """Lista de pasos como [{"icon","label"}] aceptando también pares [etiqueta, icono]."""
    out = []
    for s in p.get(key, []):
        if isinstance(s, (list, tuple)):
            s = {"label": s[0], "icon": s[1] if len(s) > 1 else None}
        out.append(s if isinstance(s, dict) else {"label": str(s)})
    return out


def _check_steps(key, lo, hi, need_icon):
    def check(p):
        items, errs = p.get(key), []
        if not isinstance(items, list) or not lo <= len(items) <= hi:
            return [f"{key}: lista de {lo} a {hi} elementos"]
        for i, s in enumerate(_steps(p, key)):
            if not s.get("label"):
                errs.append(f"{key}[{i}].label: obligatorio")
            ic = s.get("icon")
            if (need_icon or ic) and not icons.exists(ic or ""):
                errs.append(f"{key}[{i}].icon: «{ic}» no existe (formats/icons/selection.txt)")
        return errs
    return check


# ---------------------------------------------------------------- formatos

def _check_variant(p):
    v = p.get("variant", "rise")
    return [] if v in VARIANTS else [f"variant: «{v}» (usa {', '.join(VARIANTS)})"]


@fmt("kinetic-title", layout="over", required=("text",), check=_check_variant,
     example={"text": "La ciencia *abierta* cambia todo", "kicker": "CAPÍTULO 01", "variant": "rise"})
def kinetic_title(sid, d, p, layout="over"):
    """Título que se arma letra por letra (variantes rise, wave, blur, mask); *palabra* va en color de acento,
    con kicker que se descifra y una barra que se dibuja."""
    variant = p.get("variant", "rise")
    y = p.get("y", 330)
    size = p.get("size") or _title_size(p["text"])
    n = len(_plain(p["text"]))
    kicker = p.get("kicker", "")
    css = KINETIC_CSS + f"""
    .kt-box {{ position: absolute; left: 60px; right: 60px; top: {y}px; text-align: center; }}
    .kt-k {{ font-family: var(--font-mono); font-weight: 600; font-size: 32px; letter-spacing: .24em;
             color: var(--accent2); margin-bottom: 26px; min-height: 40px; }}
    .kt-t {{ font-family: var(--font-display); font-weight: 700; font-size: {size}px; line-height: 1.02;
             letter-spacing: -.02em; color: var(--text);
             text-shadow: 0 6px 30px rgba(0,0,0,.65), 0 2px 6px rgba(0,0,0,.5); }}
    .kt-bar {{ width: 240px; height: 8px; margin: 34px auto 0; border-radius: 4px; transform-origin: 0 50%;
               background: linear-gradient(90deg, var(--accent), var(--accent3));
               box-shadow: 0 0 22px color-mix(in srgb, var(--accent) 60%, transparent); }}
    """
    body = (f'<div class="kt-box" id="{sid}-box"><div class="kt-k" id="{sid}-k" data-text="{esc(kicker)}">'
            f'{esc(kicker)}</div><div class="kt-t" id="{sid}-t">{_kinetic(p["text"])}</div>'
            f'<div class="kt-bar" id="{sid}-bar"></div></div>')
    out_t = max(d - 0.6, 0.9)
    js = [SCRAMBLE_JS,
          f'const kEl = document.getElementById("{sid}-k"), kTxt = kEl.dataset.text, ks = {{p: 0}};',
          f'tl.fromTo(ks, {{p: 0}}, {{p: 1, duration: .55, ease: "none", onUpdate: () => {{ '
          f'kEl.textContent = vvScramble(kTxt, ks.p, Math.round(tl.time() * 30)); }}}}, .05);',
          f'tl.fromTo("#{sid}-k", {{opacity: 0}}, {{opacity: 1, duration: .15}}, .05);',
          kinetic_in(f"#{sid}-t", variant, 0.12, n),
          f'tl.fromTo("#{sid}-bar", {{scaleX: 0}}, {{scaleX: 1, duration: .55, ease: "expo.out"}}, '
          f'{min(0.35 + n * 0.02, 0.9):.3f});',
          kinetic_out(f"#{sid}-t", variant, out_t),
          f'tl.to(["#{sid}-k", "#{sid}-bar"], {{opacity: 0, duration: .25}}, {out_t:.3f});']
    return wrap(sid, d, layout, css, body, "\n".join(js))


def _parse_value(value):
    """«87%» → ("", 87.0, "%", 0 decimales, sep. miles, sep. decimal). Acepta 3.500 / 1,2 / 12.5 M."""
    m = re.match(r"^(\D*?)(\d[\d.,\s]*\d|\d)(.*)$", str(value).strip())
    if not m:
        return None
    pre, num, suf = m.group(1), m.group(2).replace(" ", ""), m.group(3)
    seps = [c for c in num if c in ".,"]
    tsep, dsep, dec = "", ".", 0
    if seps:
        last = max(num.rfind("."), num.rfind(","))
        tail = num[last + 1:]
        if len(set(seps)) == 1 and (len(tail) == 3 and (len(seps) > 1 or len(num[:last]) <= 3)):
            tsep = seps[0]  # solo separadores de miles: 3.500 / 1,000,000
        else:
            dsep, dec = num[last], len(tail)
            tsep = next((c for c in seps if c != dsep), "")
    digits = num.replace(tsep, "") if tsep else num
    return pre, float(digits.replace(dsep, ".")), suf, dec, tsep, dsep


def _check_value(p):
    return [] if _parse_value(p.get("value", "")) else [f"value: «{p.get('value')}» no tiene un número"]


@fmt("data-reveal", required=("value", "label"), needs=("gsap:DrawSVGPlugin",), check=_check_value,
     example={"value": "87%", "label": "de los datos ya son abiertos", "kicker": "EL DATO",
              "source": "Fuente: ejemplo 2026", "illustrative": True})
def data_reveal(sid, d, p, layout="full"):
    """Un dato grande que se descifra y cuenta hasta su valor dentro de un medidor circular (lleno al % si es
    porcentaje), con etiqueta, fuente y etiqueta «ilustrativo» opcional."""
    pre, target, suf, dec, tsep, dsep = _parse_value(p["value"])
    start = float(p.get("from", 0))
    pct = suf.strip().startswith("%")
    fill = max(0.0, min(target / 100, 1.0)) if pct else 1.0
    cx, cy, r = 540, 690, 330
    circ = 2 * math.pi * r
    ticks = "".join(
        f'<line x1="{cx + (r + 34) * math.cos(a):.1f}" y1="{cy + (r + 34) * math.sin(a):.1f}" '
        f'x2="{cx + (r + (52 if k % 5 == 0 else 44)) * math.cos(a):.1f}" '
        f'y2="{cy + (r + (52 if k % 5 == 0 else 44)) * math.sin(a):.1f}"/>'
        for k in range(60) for a in [(-90 + k * 6) * math.pi / 180])
    num_size = 230 if len(str(p["value"])) <= 5 else 180 if len(str(p["value"])) <= 8 else 140
    css = f"""
    svg.dr {{ position: absolute; inset: 0; }}
    svg.dr .track {{ fill: none; stroke: var(--surface-line); stroke-width: 22; opacity: .7; }}
    svg.dr .arc {{ fill: none; stroke: url(#{sid}-g); stroke-width: 22; stroke-linecap: round;
                   filter: drop-shadow(0 0 18px color-mix(in srgb, var(--accent) 70%, transparent)); }}
    svg.dr .ticks line {{ stroke: var(--muted); stroke-width: 3; opacity: .45; }}
    .dr-k {{ position: absolute; left: 0; right: 0; top: 250px; text-align: center; font-family: var(--font-mono);
             font-weight: 600; font-size: 32px; letter-spacing: .24em; color: var(--accent2); }}
    .dr-n {{ position: absolute; left: 0; right: 0; top: {cy - num_size * 0.62:.0f}px; text-align: center;
             font-family: var(--font-display); font-weight: 700; font-size: {num_size}px; line-height: 1;
             letter-spacing: -.03em; color: var(--text); font-variant-numeric: tabular-nums;
             text-shadow: 0 0 40px color-mix(in srgb, var(--accent) 45%, transparent); }}
    .dr-l {{ position: absolute; left: 90px; right: 90px; top: 1075px; text-align: center;
             font-family: var(--font-display); font-weight: 700; font-size: 50px; line-height: 1.1; color: var(--text); }}
    .dr-s {{ position: absolute; left: 0; right: 0; top: 1150px; text-align: center; font-family: var(--font-mono);
             font-size: 28px; color: var(--muted); }}
    """
    ilus = (f'<div class="tag-ilus" style="left:70px;top:200px">{esc(CTX["labels"]["illustrative"])}</div>'
            if p.get("illustrative") else "")
    body = (f'<svg class="dr" width="1080" height="1920"><defs><linearGradient id="{sid}-g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="var(--accent)"/><stop offset="1" stop-color="var(--accent3)"/></linearGradient></defs>'
            f'<g class="ticks" id="{sid}-ticks">{ticks}</g><circle class="track" cx="{cx}" cy="{cy}" r="{r}"/>'
            f'<circle class="arc" id="{sid}-arc" cx="{cx}" cy="{cy}" r="{r}" transform="rotate(-90 {cx} {cy})"/></svg>'
            f'<div class="dr-k" id="{sid}-k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="dr-n" id="{sid}-n">{esc(p["value"])}</div>'
            f'<div class="dr-l" id="{sid}-l">{esc(p["label"])}</div>'
            f'<div class="dr-s" id="{sid}-s">{esc(p.get("source", ""))}</div>{ilus}')
    count = min(1.3, max(d * 0.45, 0.7))
    js = [SCRAMBLE_JS,
          f'const nEl = document.getElementById("{sid}-n"), ns = {{v: {start}, p: 0}};',
          f'const vvFmt = (v) => {{ let s = v.toFixed({dec}); let [i, f] = s.split("."); '
          f'i = i.replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, {repr(tsep)}); '
          f'return {repr(pre)} + i + (f ? {repr(dsep)} + f : "") + {repr(suf)}; }};',
          f'const nDraw = () => {{ nEl.textContent = vvScramble(vvFmt(ns.v), Math.min(1, ns.p * 1.6), '
          f'Math.round(tl.time() * 30)); }};',
          f'tl.fromTo(ns, {{v: {start}, p: 0}}, {{v: {target}, p: 1, duration: {count:.2f}, ease: "power3.out", '
          f'onUpdate: nDraw}}, .25);',
          f'tl.fromTo("#{sid}-n", {{opacity: 0, scale: .85}}, {{opacity: 1, scale: 1, duration: .4, ease: "expo.out"}}, .2);',
          f'tl.fromTo("#{sid}-ticks line", {{opacity: 0}}, {{opacity: .45, duration: .02, stagger: .008}}, .05);',
          f'tl.fromTo("#{sid}-arc", {{drawSVG: "0%"}}, {{drawSVG: "{fill * 100:.1f}%", duration: {count:.2f}, '
          f'ease: "power3.out"}}, .25);',
          f'tl.fromTo("#{sid}-k", {{opacity: 0, y: -14}}, {{opacity: 1, y: 0, duration: .35, ease: "power3.out"}}, .1);',
          f'tl.fromTo("#{sid}-l", {{opacity: 0, y: 24}}, {{opacity: 1, y: 0, duration: .45, ease: "expo.out"}}, '
          f'{0.25 + count * 0.6:.2f});',
          f'tl.fromTo("#{sid}-s", {{opacity: 0}}, {{opacity: 1, duration: .3}}, {0.35 + count * 0.7:.2f});']
    _ = circ
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("draw-diagram", required=("steps",), needs=("gsap:DrawSVGPlugin", "gsap:MotionPathPlugin"),
     check=_check_steps("steps", 2, 5, need_icon=True),
     example={"title": "Del dato al hallazgo", "kicker": "PROCESO",
              "steps": [{"icon": "database", "label": "Datos abiertos"}, {"icon": "bot", "label": "Análisis con IA"},
                        {"icon": "microscope", "label": "Validación"}, {"icon": "lightbulb", "label": "Hallazgo"}]})
def draw_diagram(sid, d, p, layout="full"):
    """Proceso de 2 a 5 pasos en zigzag: cada nodo se dibuja con su icono, las conexiones se trazan solas y un
    pulso de luz las recorre de paso en paso."""
    steps = _steps(p, "steps")
    n = len(steps)
    y0, y1 = (520, 1080) if p.get("title") else (380, 1080)
    ys = [y0 + (y1 - y0) * i / max(n - 1, 1) for i in range(n)]
    xs = [300 if i % 2 == 0 else 780 for i in range(n)]
    R = 74 if n <= 4 else 64
    nodes, labels, conns, js = [], [], [], []
    seg = max((d - 0.9) / n, 0.32)
    for i, (s, x, y) in enumerate(zip(steps, xs, ys)):
        acc = ACCENTS[i % 3]
        nodes.append(f'<circle class="dd-bg" id="{sid}-b{i}" cx="{x}" cy="{y:.0f}" r="{R}"/>'
                     f'<circle class="dd-ring" id="{sid}-c{i}" cx="{x}" cy="{y:.0f}" r="{R}" style="stroke:var(--{acc})"/>')
        labels.append(
            f'<div class="dd-ic" id="{sid}-i{i}" style="left:{x - 40}px;top:{y - 40:.0f}px;color:var(--{acc})">'
            f'{icons.icon(s["icon"], 80, stroke=1.8)}</div>'
            f'<div class="dd-lb {"r" if x < 540 else "l"}" id="{sid}-t{i}" style="top:{y - 52:.0f}px;'
            + (f'left:{x + R + 34}px' if x < 540 else f'right:{1080 - x + R + 34}px')
            + f'"><span class="n">{i + 1:02d}</span><span class="t">{esc(s["label"])}</span></div>')
        t = 0.25 + i * seg
        js += [f'tl.fromTo("#{sid}-b{i}", {{opacity: 0}}, {{opacity: 1, duration: .3}}, {t + .12:.3f});',
               f'tl.fromTo("#{sid}-c{i}", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: .45, ease: "power2.inOut"}}, {t:.3f});',
               f'tl.fromTo("#{sid}-i{i}", {{opacity: 0, scale: .4, rotation: -30}}, {{opacity: 1, scale: 1, rotation: 0, '
               f'duration: .5, ease: "back.out(2)"}}, {t + .12:.3f});',
               f'tl.fromTo("#{sid}-t{i}", {{opacity: 0, x: {-30 if x < 540 else 30}}}, {{opacity: 1, x: 0, duration: .45, '
               f'ease: "expo.out"}}, {t + .18:.3f});']
        if i < n - 1:
            x2, y2 = xs[i + 1], ys[i + 1]
            dy = y2 - y
            path = f"M{x} {y + R:.0f} C{x} {y + R + dy * .45:.0f} {x2} {y2 - R - dy * .45:.0f} {x2} {y2 - R:.0f}"
            conns.append(f'<path class="dd-ln" id="{sid}-p{i}" d="{path}"/>')
            tc = t + 0.3
            js += [f'tl.fromTo("#{sid}-p{i}", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: {seg * .8:.3f}, '
                   f'ease: "power1.inOut"}}, {tc:.3f});',
                   f'tl.set("#{sid}-dot", {{opacity: 1}}, {tc:.3f});',
                   f'tl.to("#{sid}-dot", {{duration: {seg * .8:.3f}, ease: "power1.inOut", '
                   f'motionPath: {{path: "#{sid}-p{i}"}}}}, {tc:.3f});']
    js.append(f'tl.to("#{sid}-dot", {{opacity: 0, duration: .2}}, {0.25 + (n - 1) * seg + 0.3 + seg * .8:.3f});')
    head = ""
    if p.get("title"):
        head = (f'<div class="dd-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
                f'<div class="t">{_kinetic(p["title"])}</div></div>')
        js.insert(0, kinetic_in(f"#{sid}-h", "rise", 0.08, len(_plain(p["title"]))))
    css = KINETIC_CSS + """
    svg.dd { position: absolute; inset: 0; overflow: visible; }
    .dd-bg { fill: color-mix(in srgb, var(--bg) 75%, transparent); }
    .dd-ring { fill: none; stroke-width: 5;
               filter: drop-shadow(0 0 14px color-mix(in srgb, currentColor 40%, transparent)); }
    .dd-ln { fill: none; stroke: var(--surface-line); stroke-width: 5; stroke-linecap: round; }
    .dd-dot { opacity: 0; fill: var(--text); filter: drop-shadow(0 0 10px var(--accent)) drop-shadow(0 0 22px var(--accent)); }
    .dd-ic { position: absolute; width: 80px; height: 80px; }
    .dd-lb { position: absolute; width: 400px; display: flex; flex-direction: column; gap: 4px; }
    .dd-lb.l { text-align: right; align-items: flex-end; }
    .dd-lb .n { font-family: var(--font-mono); font-size: 28px; letter-spacing: .14em; color: var(--muted); }
    .dd-lb .t { font-family: var(--font-display); font-weight: 700; font-size: 46px; line-height: 1.05; color: var(--text); }
    .dd-h { position: absolute; left: 70px; right: 70px; top: 250px; text-align: center; }
    .dd-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
               color: var(--accent2); margin-bottom: 14px; }
    .dd-h .t { font-family: var(--font-display); font-weight: 700; font-size: 66px; line-height: 1.04; color: var(--text); }
    """
    body = (head + f'<svg class="dd" width="1080" height="1920">{"".join(conns)}{"".join(nodes)}'
            f'<circle class="dd-dot" id="{sid}-dot" cx="0" cy="0" r="13"/></svg>' + "".join(labels))
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("morph-icon", required=("stages",), needs=("gsap:MorphSVGPlugin", "gsap:DrawSVGPlugin"),
     check=_check_steps("stages", 2, 4, need_icon=True),
     example={"kicker": "DE LA IDEA AL RESULTADO",
              "stages": [{"icon": "lightbulb", "label": "Una idea"}, {"icon": "flask-conical", "label": "Un experimento"},
                         {"icon": "trophy", "label": "Un resultado"}]})
def morph_icon(sid, d, p, layout="full"):
    """Un icono grande que se transforma en el siguiente (2 a 4 etapas) con un anillo de progreso y la etiqueta
    de cada etapa; el color avanza por los acentos de la marca."""
    stages = _steps(p, "stages")
    n = len(stages)
    cx, cy, R = 540, 660, 300
    paths = [icons.path_d(s["icon"]) for s in stages]
    seg = max((d - 0.6) / n, 0.5)
    arcs = []
    gap = 6 if n > 1 else 0
    for i in range(n):
        a0 = -90 + i * 360 / n + gap / 2
        a1 = -90 + (i + 1) * 360 / n - gap / 2
        large = 1 if a1 - a0 > 180 else 0
        x0, y0 = cx + R * math.cos(math.radians(a0)), cy + R * math.sin(math.radians(a0))
        x1, y1 = cx + R * math.cos(math.radians(a1)), cy + R * math.sin(math.radians(a1))
        arcs.append(f'<path class="mi-arc" id="{sid}-a{i}" style="stroke:var(--{ACCENTS[i % 3]})" '
                    f'd="M{x0:.1f} {y0:.1f} A{R} {R} 0 {large} 1 {x1:.1f} {y1:.1f}"/>')
    labels = "".join(f'<div class="mi-l" id="{sid}-l{i}"><span class="n">{i + 1:02d} / {n:02d}</span>'
                     f'<span class="t">{esc(s["label"])}</span></div>' for i, s in enumerate(stages))
    css = f"""
    svg.mi {{ position: absolute; inset: 0; }}
    .mi-track {{ fill: none; stroke: var(--surface-line); stroke-width: 10; opacity: .6; }}
    .mi-arc {{ fill: none; stroke-width: 10; stroke-linecap: round; }}
    .mi-ic {{ position: absolute; left: {cx - 210}px; top: {cy - 210}px; width: 420px; height: 420px; color: var(--accent);
              filter: drop-shadow(0 0 26px color-mix(in srgb, currentColor 55%, transparent)); }}
    .mi-ic path {{ fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }}
    .mi-k {{ position: absolute; left: 0; right: 0; top: 250px; text-align: center; font-family: var(--font-mono);
             font-weight: 600; font-size: 32px; letter-spacing: .24em; color: var(--accent2); }}
    .mi-l {{ position: absolute; left: 60px; right: 60px; top: 1030px; text-align: center; display: flex;
             flex-direction: column; gap: 10px; opacity: 0; }}
    .mi-l .n {{ font-family: var(--font-mono); font-size: 28px; letter-spacing: .16em; color: var(--muted); }}
    .mi-l .t {{ font-family: var(--font-display); font-weight: 700; font-size: 72px; line-height: 1.02; color: var(--text); }}
    """
    body = (f'<div class="mi-k" id="{sid}-k">{esc(p.get("kicker", ""))}</div>'
            f'<svg class="mi" width="1080" height="1920"><circle class="mi-track" cx="{cx}" cy="{cy}" r="{R}"/>{"".join(arcs)}</svg>'
            f'<svg class="mi-ic" id="{sid}-ic" viewBox="0 0 24 24"><path id="{sid}-path" d="{paths[0]}"/></svg>{labels}')
    js = ['const vvVar = (n) => getComputedStyle(document.documentElement).getPropertyValue("--" + n).trim();',
          f'tl.fromTo("#{sid}-k", {{opacity: 0, y: -14}}, {{opacity: 1, y: 0, duration: .35, ease: "power3.out"}}, .05);',
          f'tl.fromTo("#{sid}-path", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: .55, ease: "power2.inOut"}}, .1);',
          f'tl.fromTo("#{sid}-ic", {{scale: .7, rotation: -12}}, {{scale: 1, rotation: 0, duration: .7, ease: "expo.out"}}, .1);']
    for i in range(n):
        t = 0.15 + i * seg
        js += [f'tl.fromTo("#{sid}-a{i}", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: {min(seg * .8, .7):.3f}, '
               f'ease: "power2.out"}}, {t:.3f});',
               f'tl.fromTo("#{sid}-l{i}", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: .4, ease: "expo.out"}}, {t + .1:.3f});']
        if i < n - 1:
            tm = 0.15 + (i + 1) * seg - 0.35
            js += [f'tl.to("#{sid}-l{i}", {{opacity: 0, y: -24, duration: .25, ease: "power2.in"}}, {tm:.3f});',
                   f'tl.to("#{sid}-path", {{morphSVG: {{shape: "{paths[i + 1]}"}}, duration: .6, '
                   f'ease: "power3.inOut"}}, {tm:.3f});',
                   f'tl.to("#{sid}-ic", {{color: vvVar("{ACCENTS[(i + 1) % 3]}"), duration: .6}}, {tm:.3f});',
                   f'tl.fromTo("#{sid}-ic", {{scale: 1}}, {{scale: 1.08, duration: .3, yoyo: true, repeat: 1, '
                   f'ease: "sine.inOut"}}, {tm:.3f});']
    return wrap(sid, d, layout, css, body, "\n".join(js))


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * e for a, b, c, e in zip(p0, p1, p2, p3))


@fmt("path-journey", required=("stops",), needs=("gsap:DrawSVGPlugin", "gsap:MotionPathPlugin"),
     check=_check_steps("stops", 2, 5, need_icon=False),
     example={"title": "Cómo llegamos aquí", "kicker": "EL CAMINO",
              "stops": [{"label": "2024", "note": "La primera idea"}, {"label": "2025", "note": "El primer laboratorio"},
                        {"label": "2026", "note": "Ciencia abierta"}]})
def path_journey(sid, d, p, layout="full"):
    """Una ruta curva que se dibuja mientras un punto de luz viaja de parada en parada (2 a 5): cada parada
    se enciende con su etiqueta y nota al llegar el punto. Ideal para cronologías e historias."""
    stops = _steps(p, "stops")
    n = len(stops)
    y0, y1 = (500, 1100) if p.get("title") else (360, 1100)
    pts = [(250 if i % 2 == 0 else 830, y0 + (y1 - y0) * i / max(n - 1, 1)) for i in range(n)]
    segs, lengths = [], []
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        dy = yb - ya
        c = ((xa, ya), (xa, ya + dy * .55), (xb, yb - dy * .55), (xb, yb))
        segs.append(c)
        prev, L = c[0], 0.0
        for k in range(1, 65):
            q = _bezier(*c, k / 64)
            L += math.dist(prev, q)
            prev = q
        lengths.append(L)
    total = sum(lengths)
    fr = [0.0]
    for L in lengths:
        fr.append(fr[-1] + L / total)
    d_path = f"M{pts[0][0]} {pts[0][1]:.0f} " + " ".join(
        f"C{c[1][0]} {c[1][1]:.0f} {c[2][0]} {c[2][1]:.0f} {c[3][0]} {c[3][1]:.0f}" for c in segs)
    seg_t = max((d - 0.9) / n, 0.35)
    marks, labels = [], []
    js = []
    for i, ((x, y), s) in enumerate(zip(pts, stops)):
        acc = ACCENTS[i % 3]
        marks.append(f'<circle class="pj-m" id="{sid}-m{i}" cx="{x}" cy="{y:.0f}" r="22" style="stroke:var(--{acc})"/>')
        side = "r" if x < 540 else "l"
        pos = f'left:{x + 52}px' if side == "r" else f'right:{1080 - x + 52}px'
        labels.append(f'<div class="pj-l {side}" id="{sid}-l{i}" style="top:{y - 46:.0f}px;{pos}">'
                      f'<span class="t" style="color:var(--{acc})">{esc(s["label"])}</span>'
                      + (f'<span class="n">{esc(s["note"])}</span>' if s.get("note") else "") + '</div>')
        t_arrive = 0.3 + i * seg_t
        js += [f'tl.fromTo("#{sid}-m{i}", {{scale: 0, transformOrigin: "50% 50%"}}, {{scale: 1, duration: .45, '
               f'ease: "back.out(3)"}}, {t_arrive:.3f});',
               f'tl.fromTo("#{sid}-l{i}", {{opacity: 0, y: 20}}, {{opacity: 1, y: 0, duration: .45, ease: "expo.out"}}, '
               f'{t_arrive + .05:.3f});']
        if i < n - 1:
            js += [f'tl.fromTo("#{sid}-prog", {{drawSVG: "0% {fr[i] * 100:.2f}%"}}, {{drawSVG: "0% {fr[i + 1] * 100:.2f}%", '
                   f'duration: {seg_t * .85:.3f}, ease: "power1.inOut"}}, {t_arrive + .1:.3f});',
                   f'tl.to("#{sid}-dot", {{duration: {seg_t * .85:.3f}, ease: "power1.inOut", '
                   f'motionPath: {{path: "#{sid}-prog", start: {fr[i]:.4f}, end: {fr[i + 1]:.4f}}}}}, {t_arrive + .1:.3f});']
    js.insert(0, f'tl.fromTo("#{sid}-track", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: .8, ease: "power2.out"}}, .05);')
    js.insert(1, f'tl.set("#{sid}-dot", {{opacity: 1, x: {pts[0][0]}, y: {pts[0][1]:.0f}}}, .3);')
    head = ""
    if p.get("title"):
        head = (f'<div class="dd-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
                f'<div class="t">{_kinetic(p["title"])}</div></div>')
        js.insert(0, kinetic_in(f"#{sid}-h", "rise", 0.08, len(_plain(p["title"]))))
    css = KINETIC_CSS + """
    svg.pj { position: absolute; inset: 0; overflow: visible; }
    .pj-track { fill: none; stroke: var(--surface-line); stroke-width: 4; stroke-dasharray: 2 14; stroke-linecap: round; }
    .pj-prog { fill: none; stroke: var(--accent); stroke-width: 7; stroke-linecap: round;
               filter: drop-shadow(0 0 12px color-mix(in srgb, var(--accent) 70%, transparent)); }
    .pj-m { fill: var(--bg); stroke-width: 7; }
    .pj-dot { opacity: 0; fill: var(--text); filter: drop-shadow(0 0 12px var(--accent)) drop-shadow(0 0 26px var(--accent)); }
    .pj-l { position: absolute; width: 420px; display: flex; flex-direction: column; gap: 6px; }
    .pj-l.l { text-align: right; align-items: flex-end; }
    .pj-l .t { font-family: var(--font-display); font-weight: 700; font-size: 58px; line-height: 1; }
    .pj-l .n { font-family: var(--font-mono); font-size: 30px; line-height: 1.25; color: var(--text); opacity: .85; }
    .dd-h { position: absolute; left: 70px; right: 70px; top: 250px; text-align: center; }
    .dd-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
               color: var(--accent2); margin-bottom: 14px; }
    .dd-h .t { font-family: var(--font-display); font-weight: 700; font-size: 66px; line-height: 1.04; color: var(--text); }
    """
    body = (head + f'<svg class="pj" width="1080" height="1920"><path class="pj-track" id="{sid}-track" d="{d_path}"/>'
            f'<path class="pj-prog" id="{sid}-prog" d="{d_path}"/>{"".join(marks)}'
            f'<circle class="pj-dot" id="{sid}-dot" cx="0" cy="0" r="15"/></svg>' + "".join(labels))
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("particle-burst", layout="over", required=("text",), needs=("gsap:Physics2DPlugin",),
     example={"text": "¡Funcionó!", "kicker": "RESULTADO"})
def particle_burst(sid, d, p, layout="over"):
    """Remate: el texto golpea en pantalla mientras una explosión de partículas de la marca sale despedida con
    física (gravedad, ángulos y velocidades fijas por semilla) y una onda de choque se expande."""
    x, y = p.get("x", 540), p.get("y", 560)
    count = max(12, min(int(p.get("count", 56)), 120))
    r = _rand(sum(map(ord, sid)) + 17)
    parts, js = [], []
    for i in range(count):
        size = 8 + r() * 18
        shape = ["50%", "3px", "50%"][i % 3]
        w = size * (2.6 if i % 7 == 0 else 1)
        parts.append(f'<i class="pb-p" id="{sid}-p{i}" style="left:{x - w / 2:.0f}px;top:{y - size / 2:.0f}px;'
                     f'width:{w:.0f}px;height:{size:.0f}px;border-radius:{shape};'
                     f'background:var(--{ACCENTS[i % 3] if i % 5 else "text"})"></i>')
        vel = 520 + r() * 900
        ang = -180 + r() * 180 if r() < 0.8 else r() * 180  # la mayoría hacia arriba
        life = 1.0 + r() * 0.8
        t0 = 0.12 + r() * 0.06
        js += [f'tl.fromTo("#{sid}-p{i}", {{opacity: 1, scale: 1, rotation: 0}}, {{physics2D: {{velocity: {vel:.0f}, '
               f'angle: {ang:.1f}, gravity: 1100}}, rotation: {(r() - .5) * 720:.0f}, duration: {life:.2f}, ease: "none"}}, {t0:.3f});',
               f'tl.to("#{sid}-p{i}", {{opacity: 0, scale: .3, duration: .35, ease: "power2.in"}}, {t0 + life - .35:.3f});']
    size = p.get("size") or _title_size(p["text"], 150)
    css = KINETIC_CSS + f"""
    .pb-p {{ position: absolute; opacity: 0; box-shadow: 0 0 12px currentColor; }}
    .pb-w {{ position: absolute; left: {x - 120}px; top: {y - 120}px; width: 240px; height: 240px; border-radius: 50%;
             border: 6px solid var(--accent); opacity: 0;
             box-shadow: 0 0 40px var(--accent), inset 0 0 40px color-mix(in srgb, var(--accent) 50%, transparent); }}
    .pb-t {{ position: absolute; left: 50px; right: 50px; top: {y - size * 0.6:.0f}px; text-align: center;
             font-family: var(--font-display); font-weight: 700; font-size: {size}px; line-height: 1; color: var(--text);
             text-shadow: 0 0 40px color-mix(in srgb, var(--accent) 70%, transparent), 0 8px 30px rgba(0,0,0,.6); }}
    .pb-k {{ position: absolute; left: 0; right: 0; top: {y - size * 0.6 - 70:.0f}px; text-align: center;
             font-family: var(--font-mono); font-weight: 600; font-size: 32px; letter-spacing: .24em; color: var(--accent2);
             text-shadow: 0 2px 10px rgba(0,0,0,.7); }}
    """
    body = (f'<div class="pb-w" id="{sid}-w"></div>{"".join(parts)}'
            f'<div class="pb-k" id="{sid}-k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="pb-t" id="{sid}-t">{_kinetic(p["text"])}</div>')
    js = [f'tl.fromTo("#{sid}-w", {{scale: .1, opacity: 1}}, {{scale: 3.2, opacity: 0, duration: .9, ease: "expo.out"}}, .1);',
          f'tl.fromTo("#{sid}-t .ch", {{scale: 2.4, opacity: 0, filter: "blur(10px)"}}, {{scale: 1, opacity: 1, '
          f'filter: "blur(0px)", duration: .45, ease: "back.out(1.8)", stagger: .025}}, .08);',
          f'tl.fromTo("#{sid}-t", {{x: 0}}, {{x: 10, duration: .04, yoyo: true, repeat: 5, ease: "none"}}, .16);',
          f'tl.fromTo("#{sid}-k", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: .35, ease: "power3.out"}}, .3);',
          *js,
          kinetic_out(f"#{sid}-t", "blur", max(d - 0.55, 1.0))]
    return wrap(sid, d, layout, css, body, "\n".join(js))
