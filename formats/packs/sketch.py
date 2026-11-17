"""Paquete «sketch»: estilo pizarrón, trazos dibujados a mano (Rough.js, MIT) con los colores de la marca.

Rough.js genera los trazos al construir la escena con una semilla fija (siempre los mismos) y DrawSVG los
dibuja desde la línea de tiempo (un solo reloj, ADR 0022 y 0029). Los colores se leen de las variables de la
marca: los atributos SVG no aceptan `var()`.
Se activa con channel.json → "format_packs": [..., "sketch"].
"""
from formats import icons
from formats.core import esc, fmt, wrap
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain

SHAPES = ("circle", "underline", "box", "arrow", "cross")
ROLES = ("accent", "accent2", "accent3", "warn", "text")

# Lienzo a mano: `skPad(svg, semilla)` → {rc, draw(nodo, t, dur)}: agrega lo que genera Rough.js y lo dibuja.
SK_JS = """
    const skVar = (n) => getComputedStyle(document.documentElement).getPropertyValue("--" + n).trim() || "#ffffff";
    const skAlpha = (hex, a) => { const h = hex.replace("#", ""), f = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
      return "rgba(" + [0, 2, 4].map((i) => parseInt(f.slice(i, i + 2), 16)).join(",") + "," + a + ")"; };
    const skPad = (svgId, seed) => {
      const svg = document.getElementById(svgId);
      const rc = rough.svg(svg, {options: {seed: seed, roughness: 1.5, bowing: 1.3, strokeWidth: 5}});
      const draw = (node, t, dur, stagger) => {
        svg.appendChild(node);
        const parts = node.querySelectorAll("path");
        tl.fromTo(parts, {drawSVG: "0%"}, {drawSVG: "100%", duration: dur, ease: "power1.inOut",
          stagger: stagger === undefined ? {amount: Math.min(dur, .4)} : stagger}, t);
        return node;
      };
      return {svg, rc, draw};
    };"""

CSS = KINETIC_CSS + """
    .sk-svg { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }
    .sk-svg path { stroke-linecap: round; stroke-linejoin: round; }
    .sk-lab { position: absolute; font-family: var(--font-display); font-weight: 700; color: var(--text);
              text-shadow: 0 2px 14px color-mix(in srgb, var(--bg) 85%, transparent); white-space: nowrap; }
    .sk-h { position: absolute; left: 90px; right: 90px; top: 230px; text-align: center; }
    .sk-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
               color: var(--accent2); margin-bottom: 12px; }
    .sk-h .t { font-family: var(--font-display); font-weight: 700; font-size: 66px; line-height: 1.04; color: var(--text); }
    .sk-item { position: absolute; left: 230px; right: 90px; font-family: var(--font-display); font-weight: 600;
               font-size: 50px; line-height: 1.12; color: var(--text); }
    .sk-ic { position: absolute; display: flex; align-items: center; justify-content: center; }
    .sk-node { position: absolute; display: flex; flex-direction: column; align-items: center; justify-content: center;
               text-align: center; font-family: var(--font-display); font-weight: 700; font-size: 40px; line-height: 1.08;
               color: var(--text); text-shadow: 0 0 12px var(--bg), 0 0 4px var(--bg); }
    .sk-nic { color: var(--text); }
    .sk-node .n { font-family: var(--font-mono); font-size: 24px; color: var(--muted); font-weight: 500; }
"""


def _svg(sid):
    return f'<svg class="sk-svg" id="{sid}-sk" viewBox="0 0 1080 1920"></svg>'


def _role(p, key="role", default="accent"):
    return p.get(key, default)


def _check_role(p):
    return [] if _role(p) in ROLES else [f"role: «{_role(p)}» (usa {', '.join(ROLES)})"]


def _check_icon(ic, where):
    return [] if not ic or icons.exists(ic) else [f"{where}: icono «{ic}» no existe (Lucide, health:… o bio:…)"]


# ---------------------------------------------------------------- sketch-annotate

def _check_annotate(p):
    errs = _check_role(p)
    if p.get("shape", "circle") not in SHAPES:
        errs.append(f"shape: «{p.get('shape')}» (usa {', '.join(SHAPES)})")
    b = p.get("box")
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b)):
        errs.append("box: [x, y, ancho, alto] en píxeles del cuadro (1080×1920)")
    else:
        x, y, w, h = b
        if w <= 20 or h <= 20 or x < 0 or y < 0 or x + w > 1080 or y + h > 1920:
            errs.append("box: debe quedar dentro del cuadro (1080×1920) y medir más de 20 px")
        elif p.get("label") and y - 120 < 168 and y + h + 120 > 1100:
            errs.append("label: no cabe arriba ni abajo de box sin chocar con la barra superior o los subtítulos")
    if len(plain(p.get("label") or "")) > 28:
        errs.append("label: máximo 28 caracteres")
    return errs


@fmt("sketch-annotate", layout="over", required=("box",), needs=("rough", "gsap:DrawSVGPlugin"),
     check=_check_annotate,
     example={"box": [300, 560, 480, 360], "shape": "circle", "label": "¡Aquí está!", "role": "accent"})
def sketch_annotate(sid, d, p, layout="over"):
    """Señala algo de la toma con un trazo a mano: `circle` (lo rodea), `underline`, `box`, `arrow` (flecha que
    llega desde la etiqueta) o `cross` (tacha), con etiqueta corta opcional. `box` = [x, y, ancho, alto]."""
    x, y, w, h = p["box"]
    shape, role = p.get("shape", "circle"), _role(p)
    cx, cy = x + w / 2, y + h / 2
    label = p.get("label") or ""
    above = y - 120 >= 168 and not (y + h + 120 <= 1100 and y - 120 < 300)
    ly = y - 104 if above else y + h + 30
    lx = max(min(cx, 1080 - 200), 200)
    if shape == "arrow":
        sx, sy = (lx + (160 if cx < 540 else -160), ly + (70 if above else 10))
        draw = (f'P.draw(P.rc.curve([[{sx:.0f}, {sy:.0f}], [{(sx + cx) / 2 + 60:.0f}, {(sy + cy) / 2:.0f}], '
                f'[{cx:.0f}, {cy - (h / 2 if above else -h / 2) * .6:.0f}]], O), .15, .5);'
                f'const tip = [{cx:.0f}, {cy - (h / 2 if above else -h / 2) * .6:.0f}];'
                f'P.draw(P.rc.linearPath([[tip[0] - 34, tip[1] {"-" if above else "+"} 30], tip, '
                f'[tip[0] + 34, tip[1] {"-" if above else "+"} 30]], O), .6, .18);')
    elif shape == "underline":
        draw = (f'P.draw(P.rc.curve([[{x:.0f}, {y + h + 14:.0f}], [{x + w * .35:.0f}, {y + h + 4:.0f}], '
                f'[{x + w * .7:.0f}, {y + h + 20:.0f}], [{x + w:.0f}, {y + h + 8:.0f}]], O), .15, .45);')
    elif shape == "box":
        draw = f'P.draw(P.rc.rectangle({x - 14:.0f}, {y - 14:.0f}, {w + 28:.0f}, {h + 28:.0f}, O), .15, .7);'
    elif shape == "cross":
        draw = (f'P.draw(P.rc.line({x:.0f}, {y:.0f}, {x + w:.0f}, {y + h:.0f}, O), .15, .3);'
                f'P.draw(P.rc.line({x + w:.0f}, {y:.0f}, {x:.0f}, {y + h:.0f}, O), .45, .3);')
    else:  # circle: dos vueltas, como cuando se rodea algo con marcador
        draw = (f'P.draw(P.rc.ellipse({cx:.0f}, {cy:.0f}, {w * 1.18:.0f}, {h * 1.22:.0f}, O), .15, .55, 0);'
                f'P.draw(P.rc.ellipse({cx + 6:.0f}, {cy - 4:.0f}, {w * 1.24:.0f}, {h * 1.16:.0f}, {{...O, strokeWidth: 3}}), .5, .4, 0);')
    lab = (f'<div class="sk-lab" id="{sid}-l" style="left:{lx - 300:.0f}px;width:600px;text-align:center;top:{ly:.0f}px;'
           f'font-size:62px;transform:rotate(-3deg)">{esc(label)}</div>') if label else ""
    js = [SK_JS, f'const P = skPad("{sid}-sk", 17);', f'const O = {{stroke: skVar("{role}"), strokeWidth: 7}};', draw]
    if label:
        js.append(f'tl.fromTo("#{sid}-l", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: .4, ease: "back.out(2)"}}, .35);')
    return wrap(sid, d, layout, CSS, _svg(sid) + lab, "\n".join(js))


# ---------------------------------------------------------------- sketch-board

def _items(p, key):
    out = []
    for it in p.get(key) or []:
        out.append(it if isinstance(it, dict) else {"text": str(it)})
    return out


def _check_board(p):
    items = p.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 4:
        return ["items: lista de 2 a 4 ideas (texto o {text, icon})"]
    errs = []
    for i, it in enumerate(_items(p, "items")):
        t = plain(it.get("text") or "")
        if not t:
            errs.append(f"items[{i}].text: obligatorio")
        elif len(t) > 46:
            errs.append(f"items[{i}].text: máximo 46 caracteres (una idea corta)")
        errs += _check_icon(it.get("icon"), f"items[{i}].icon")
    return errs


@fmt("sketch-board", required=("title", "items"), needs=("rough", "gsap:DrawSVGPlugin"), check=_check_board,
     example={"kicker": "EN RESUMEN", "title": "Ciencia *abierta*",
              "items": [{"text": "Datos que cualquiera revisa", "icon": "health:database"},
                        {"text": "Métodos paso a paso", "icon": "bio:erlenmeyer-filled"},
                        {"text": "Resultados replicables", "icon": "check"}]})
def sketch_board(sid, d, p, layout="full"):
    """Pizarra: un título que se subraya a mano y 2–4 ideas que aparecen una por una con su viñeta dibujada
    (círculo o el icono que se indique, Lucide, Health Icons o Bioicons), dentro de un marco a mano."""
    items = _items(p, "items")
    n = len(items)
    y0, gap = 600, 170 if n <= 3 else 140
    head = (f'<div class="sk-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="t">{kinetic(p["title"])}</div></div>')
    body, js = [], [SK_JS, f'const P = skPad("{sid}-sk", 23);', 'const O = {stroke: skVar("accent"), strokeWidth: 5};',
                'P.draw(P.rc.rectangle(60, 160, 960, 1000, {...O, stroke: skVar("muted"), strokeWidth: 3}), .05, .8, 0);',
                f'tl.fromTo("#{sid}-h .k", {{opacity: 0}}, {{opacity: 1, duration: .3}}, .2);',
                kinetic_in(f"#{sid}-h .t", "rise", 0.3, len(plain(p["title"]))),
                'P.draw(P.rc.curve([[300, 418], [540, 404], [780, 422]], {...O, strokeWidth: 6}), .75, .4);']
    seg = max((d - 1.6) / n, 0.45)
    for i, it in enumerate(items):
        y = y0 + i * gap
        t = 1.0 + i * seg
        acc = ("accent", "accent2", "accent3")[i % 3]
        if it.get("icon"):
            body.append(f'<div class="sk-ic" id="{sid}-i{i}" style="left:110px;top:{y - 8}px;width:84px;height:84px;'
                        f'color:var(--{acc})">{icons.icon(it["icon"], 76)}</div>')
            js.append(f'tl.fromTo("#{sid}-i{i}", {{opacity: 0, scale: .5, rotation: -20}}, {{opacity: 1, scale: 1, rotation: 0, '
                      f'duration: .45, ease: "back.out(2)"}}, {t + .1:.2f});')
            js.append(f'P.draw(P.rc.circle(152, {y + 34}, 112, {{...O, stroke: skVar("{acc}"), strokeWidth: 3}}), {t:.2f}, .4, 0);')
        else:
            js.append(f'P.draw(P.rc.circle(152, {y + 34}, 64, {{...O, stroke: skVar("{acc}"), fill: skVar("{acc}"), '
                      f'fillStyle: "hachure", hachureGap: 9}}), {t:.2f}, .45);')
        body.append(f'<div class="sk-item" id="{sid}-t{i}" style="top:{y}px">{kinetic(it["text"])}</div>')
        js.append(f'tl.fromTo("#{sid}-t{i}", {{opacity: 0, x: -24}}, {{opacity: 1, x: 0, duration: .45, ease: "expo.out"}}, '
                  f'{t + .15:.2f});')
    return wrap(sid, d, layout, CSS, _svg(sid) + head + "".join(body), "\n".join(js))


# ---------------------------------------------------------------- sketch-diagram

def _check_diagram(p):
    steps = p.get("steps")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 5:
        return ["steps: lista de 2 a 5 pasos ({label, icon?})"]
    errs = []
    for i, s in enumerate(_items(p, "steps")):
        lab = plain(s.get("label") or s.get("text") or "")
        if not lab:
            errs.append(f"steps[{i}].label: obligatorio")
        elif len(lab) > 24:
            errs.append(f"steps[{i}].label: máximo 24 caracteres")
        errs += _check_icon(s.get("icon"), f"steps[{i}].icon")
    return errs


@fmt("sketch-diagram", required=("steps",), needs=("rough", "gsap:DrawSVGPlugin"), check=_check_diagram,
     example={"title": "Del *gen* a la proteína",
              "steps": [{"label": "ADN", "icon": "health:dna"}, {"label": "ARN mensajero", "icon": "bio:ribosome"},
                        {"label": "Proteína", "icon": "health:enzyme"}]})
def sketch_diagram(sid, d, p, layout="full"):
    """Proceso de 2–5 pasos dibujado a mano: cajas con relleno rayado del color de acento, icono y etiqueta, y
    flechas trazadas de una a otra en zigzag (como draw-diagram, pero en pizarrón)."""
    steps = _items(p, "steps")
    n = len(steps)
    has_t = bool(p.get("title"))
    y0, y1 = (560 if has_t else 400), 1180
    ys = [y0 + (y1 - y0) * i / max(n - 1, 1) for i in range(n)] if n > 1 else [(y0 + y1) / 2]
    xs = [330 if i % 2 == 0 else 750 for i in range(n)]
    bw, bh = 380, 190 if n <= 3 else 150
    head = (f'<div class="sk-h" id="{sid}-h"><div class="t">{kinetic(p["title"])}</div></div>') if has_t else ""
    body, js = [], [SK_JS, f'const P = skPad("{sid}-sk", 31);']
    if has_t:
        js.append(kinetic_in(f"#{sid}-h .t", "rise", 0.15, len(plain(p["title"]))))
    seg = max((d - 0.9) / n, 0.45)
    for i, (s, x, y) in enumerate(zip(steps, xs, ys)):
        acc = ("accent", "accent2", "accent3")[i % 3]
        t = 0.35 + i * seg
        js.append(f'P.draw(P.rc.rectangle({x - bw / 2:.0f}, {y - bh / 2:.0f}, {bw}, {bh}, {{stroke: skVar("{acc}"), '
                  f'strokeWidth: 5, fill: skAlpha(skVar("{acc}"), .32), fillStyle: "hachure", hachureGap: 18, fillWeight: 2, '
                  f'hachureAngle: {-41 + 12 * i}}}), {t:.2f}, .55);')
        ic = s.get("icon")
        lab = s.get("label") or s.get("text") or ""
        inner = (f'<div class="sk-nic" style="margin-bottom:6px">{icons.icon(ic, 64 if bh > 160 else 50)}</div>'
                 if ic else "") + f'<div>{esc(plain(lab))}</div>'
        body.append(f'<div class="sk-node" id="{sid}-n{i}" style="left:{x - bw / 2 + 16:.0f}px;top:{y - bh / 2:.0f}px;'
                    f'width:{bw - 32}px;height:{bh}px">{inner}</div>')
        js.append(f'tl.fromTo("#{sid}-n{i}", {{opacity: 0, scale: .85}}, {{opacity: 1, scale: 1, duration: .4, '
                  f'ease: "back.out(1.8)"}}, {t + .25:.2f});')
        if i < n - 1:
            x2, y2 = xs[i + 1], ys[i + 1]
            ax, ay = (x + (bw / 2 - 30) * (1 if x2 > x else -1)), y + bh / 2 - 10
            bx, by = x2 + (-1 if x2 > x else 1) * 40, y2 - bh / 2 - 12
            mx = (ax + bx) / 2
            js.append(f'P.draw(P.rc.curve([[{ax:.0f}, {ay:.0f}], [{mx:.0f}, {(ay + by) / 2 + 30:.0f}], [{bx:.0f}, {by:.0f}]], '
                      f'{{stroke: skVar("muted"), strokeWidth: 4}}), {t + .5:.2f}, .35);')
            js.append(f'P.draw(P.rc.linearPath([[{bx - 26:.0f}, {by - 26:.0f}], [{bx:.0f}, {by:.0f}], [{bx + (22 if x2 > x else -22):.0f}, '
                      f'{by - 34:.0f}]], {{stroke: skVar("muted"), strokeWidth: 4}}), {t + .8:.2f}, .15);')
    return wrap(sid, d, layout, CSS, _svg(sid) + head + "".join(body), "\n".join(js))

