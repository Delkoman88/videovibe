"""Formatos genéricos de escenas animadas (paquete `core`). Ver formats/__init__.py y docs/formats.md.

Cada formato es una función `formato(sid, d, p)` que devuelve el HTML de una sub-composición de
HyperFrames (dentro de <template>), con su tiempo local empezando en 0 y duración `d`.
`p` son los parámetros del storyboard. Colores y fuentes salen de las variables CSS de marca del canal
(--accent, --accent2, --accent3, --warn, --text, --muted, --bg, --surface, --surface-line, --depth,
--font-display, --font-mono). Los textos los aporta siempre el storyboard: aquí no hay textos de canal.

Layouts (lo decide el storyboard, no el formato):
  full    fondo opaco de marca; tapa la toma (máx. ~3.5 s sin burbuja)
  bubble  igual que full, con la cara de la persona en una burbuja (algunos canales lo prohíben: ver su style.md)
  over    fondo transparente; elementos encima de la toma

Reglas: todo determinista (sin Math.random sin semilla, sin timers); todo texto ≥ 28 px; nada en la
banda de subtítulos (y 1180–1330) salvo fondo; nada bajo y 1330; lo ilustrativo se marca con la etiqueta del idioma (CTX["labels"]["illustrative"]).
"""
import html
import json
import math
from string import Template

W, H = 1080, 1920
BUBBLE = {"x": 744, "y": 186, "d": 312}  # burbuja de cara (compose.py usa los mismos valores)

# Contexto que compose.py fija antes de renderizar (fuentes y etiquetas del canal/idioma).
CTX = {"font_faces": "", "labels": {"illustrative": "ILLUSTRATIVE"}}

# Registro de formatos: nombre → {fn, layout, required, example, doc, pack}
REGISTRY = {}


def fmt(name, layout="full", required=(), example=None):
    """Registra un formato. `required` son parámetros obligatorios; `example` sirve a tests y al catálogo."""
    def deco(fn):
        REGISTRY[name] = {"fn": fn, "layout": layout, "required": tuple(required), "example": example or {},
                          "doc": (fn.__doc__ or "").strip(), "pack": fn.__module__.rsplit(".", 1)[-1]}
        return fn
    return deco

BASE = Template("""<template>
  <style>
    $fonts
    #root { position: absolute; inset: 0; overflow: hidden; }
    .stage { position: absolute; inset: 0; }
    .stage.opaque { background:
        radial-gradient(1100px 900px at 50% 42%, color-mix(in srgb, var(--depth) 55%, transparent), transparent 70%),
        linear-gradient(var(--bg), var(--bg)); }
    .grid { position: absolute; inset: 0; opacity: .16;
        background-image: linear-gradient(var(--surface-line) 1px, transparent 1px),
                          linear-gradient(90deg, var(--surface-line) 1px, transparent 1px);
        background-size: 60px 60px; }
    .mono { font-family: var(--font-mono); }
    .disp { font-family: var(--font-display); }
    .tag-ilus { position: absolute; font-family: var(--font-mono); font-size: 28px; letter-spacing: .14em;
                color: var(--warn); }
    .ring { position: absolute; border-radius: 50%; border: 3px solid var(--accent);
            box-shadow: 0 0 24px color-mix(in srgb, var(--accent) 50%, transparent); }
    $css
  </style>
  <div id="root" data-composition-id="$sid" data-width="1080" data-height="1920">
    <div class="stage $opaque" id="$sid-stage">
      $grid
      $body
    </div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    $js
    window.__timelines["$sid"] = tl;
  </script>
</template>
""")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def _rand(seed):
    """Generador pseudoaleatorio determinista (LCG) en Python, para posiciones fijas."""
    state = [seed & 0xFFFFFFFF]

    def r():
        state[0] = (1664525 * state[0] + 1013904223) & 0xFFFFFFFF
        return state[0] / 0xFFFFFFFF
    return r


def wrap(sid, d, layout, css, body, js):
    opaque = "opaque" if layout in ("full", "bubble") else ""
    grid = '<div class="grid"></div>' if opaque else ""
    ring = ""
    if layout == "bubble":
        b = BUBBLE
        ring = (f'<div class="ring" id="{sid}-ring" style="left:{b["x"] - 6}px;top:{b["y"] - 6}px;'
                f'width:{b["d"] + 12}px;height:{b["d"] + 12}px"></div>')
        js += (f'\ntl.fromTo("#{sid}-ring", {{scale: 0.6, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.4, '
               f'ease: "expo.out"}}, 0.05);')
    # entrada y salida de la escena completa
    js = (f'tl.fromTo("#{sid}-stage", {{opacity: 0}}, {{opacity: 1, duration: 0.18, ease: "power2.out"}}, 0);\n'
          + js +
          f'\ntl.to("#{sid}-stage", {{opacity: 0, duration: 0.2, ease: "power2.in"}}, {max(d - 0.22, 0.2):.3f});')
    return BASE.substitute(fonts=CTX["font_faces"], sid=sid, opaque=opaque, grid=grid, css=css,
                           body=body + ring, js=js)


# ---------------------------------------------------------------- formatos

@fmt("hud-frame", layout="over", required=("box", "label"),
     example={"box": [330, 250, 730, 680], "label": "Objeto", "sublabel": "Detalle"})
def hud_frame(sid, d, p, layout="over"):
    """Marco HUD (esquinas + barrido) alrededor de un objeto en cuadro, con etiqueta."""
    x, y, w, h = p["box"]
    lab = p["label"]
    sub = p.get("sublabel", "")
    css = f"""
    .c {{ position: absolute; width: 70px; height: 70px; border: 0 solid var(--accent);
          filter: drop-shadow(0 0 10px color-mix(in srgb, var(--accent) 70%, transparent)); }}
    .scan {{ position: absolute; left: {x}px; width: {w}px; height: 3px; background: var(--accent); opacity: .8;
             box-shadow: 0 0 16px var(--accent); }}
    .lab {{ position: absolute; left: {x}px; top: {y + h + 18}px; padding: 12px 20px; border-radius: 12px;
            background: rgba(7, 9, 12, .78); border: 1px solid var(--surface-line); }}
    .lab .a {{ font-family: var(--font-display); font-weight: 700; font-size: 44px; color: var(--text); }}
    .lab .b {{ font-family: var(--font-mono); font-size: 28px; color: var(--accent); letter-spacing: .06em; }}
    """
    corners = [(x, y, "4px 0 0 4px"), (x + w - 70, y, "4px 4px 0 0"), (x, y + h - 70, "0 0 4px 4px"),
               (x + w - 70, y + h - 70, "0 4px 4px 0")]
    body = "".join(f'<div class="c" id="{sid}-c{i}" style="left:{cx}px;top:{cy}px;border-width:{bw}"></div>'
                   for i, (cx, cy, bw) in enumerate(corners))
    body += f'<div class="scan" id="{sid}-scan" style="top:{y}px"></div>'
    body += f'<div class="lab" id="{sid}-lab"><div class="a">{esc(lab)}</div><div class="b">{esc(sub)}</div></div>'
    js = [f'tl.fromTo("#{sid}-c{i}", {{opacity: 0, scale: 1.4}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "expo.out"}}, '
          f'{0.02 + i * 0.04:.2f});' for i in range(4)]
    js.append(f'tl.fromTo("#{sid}-scan", {{y: 0, opacity: 0.9}}, {{y: {h}, opacity: 0, duration: 0.8, ease: "power1.inOut"}}, 0.1);')
    js.append(f'tl.fromTo("#{sid}-lab", {{opacity: 0, y: 12}}, {{opacity: 1, y: 0, duration: 0.3, ease: "power3.out"}}, 0.2);')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("agent-flow", required=("top", "agents", "bottom"),
     example={"kicker": "Sistema", "top": "Director", "agents": ["A", "B", "C"], "bottom": "Resultado", "bottom_at": 2.0})
def agent_flow(sid, d, p, layout="full"):
    """Diagrama vertical: un nodo superior (quien dirige) → varios agentes o pasos → un resultado."""
    top, agents, bottom = p["top"], p["agents"], p["bottom"]
    kicker = p.get("kicker", "")
    t_bottom = p.get("bottom_at", 2.5)
    xs = [190, 540, 890][:len(agents)]
    ytop, yag, ybot = 430, 760, 1060
    paths, js = [], []
    for i, x in enumerate(xs):
        for j, (ya, yb, xa, xb) in enumerate([(ytop + 50, yag - 55, 540, x), (yag + 55, ybot - 60, x, 540)]):
            L = math.hypot(xb - xa, yb - ya)
            paths.append(f'<line id="{sid}-p{i}{j}" x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="var(--{"accent" if j == 0 else "accent3"})" '
                         f'stroke-width="3" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}"/>')
            t = (0.45 + i * 0.12) if j == 0 else (t_bottom - 0.5 + i * 0.08)
            js.append(f'tl.to("#{sid}-p{i}{j}", {{attr: {{"stroke-dashoffset": 0}}, duration: 0.35, ease: "power2.out"}}, {t:.2f});')
    css = """
    svg.fl { position: absolute; inset: 0; }
    .node { position: absolute; height: 110px; border-radius: 18px; display: flex; align-items: center; justify-content: center;
            background: rgba(18, 23, 29, .92); border: 1px solid var(--surface-line);
            font-family: var(--font-display); font-weight: 700; color: var(--text); }
    .node.top { border-color: var(--accent); font-size: 46px; }
    .node.ag { font-size: 38px; width: 300px; }
    .node.bot { border: 2px solid var(--accent3); font-size: 52px;
                box-shadow: 0 0 40px color-mix(in srgb, var(--accent3) 40%, transparent); }
    .kick { position: absolute; left: 0; right: 0; top: 250px; text-align: center; font-family: var(--font-mono);
            font-size: 32px; letter-spacing: .16em; text-transform: uppercase; color: var(--accent); }
    """
    body = (f'<div class="kick" id="{sid}-k">{esc(kicker)}</div>'
            f'<svg class="fl" width="1080" height="1920">{"".join(paths)}</svg>'
            f'<div class="node top" id="{sid}-top" style="left:240px;width:600px;top:{ytop - 55}px">{esc(top)}</div>'
            + "".join(f'<div class="node ag" id="{sid}-a{i}" style="left:{x - 150}px;top:{yag - 55}px">{esc(a)}</div>'
                      for i, (x, a) in enumerate(zip(xs, agents)))
            + f'<div class="node bot" id="{sid}-bot" style="left:190px;width:700px;top:{ybot - 60}px;height:120px">{esc(bottom)}</div>')
    js = [f'tl.fromTo("#{sid}-k", {{opacity: 0, filter: "blur(6px)"}}, {{opacity: 1, filter: "blur(0px)", duration: 0.25}}, 0.05);',
          f'tl.fromTo("#{sid}-top", {{opacity: 0, y: -20}}, {{opacity: 1, y: 0, duration: 0.35, ease: "expo.out"}}, 0.1);'] + js
    js += [f'tl.fromTo("#{sid}-a{i}", {{opacity: 0, scale: 0.8}}, {{opacity: 1, scale: 1, duration: 0.35, ease: "expo.out"}}, '
           f'{0.7 + i * 0.12:.2f});' for i in range(len(xs))]
    js.append(f'tl.fromTo("#{sid}-bot", {{opacity: 0, scale: 0.85, filter: "blur(8px)"}}, {{opacity: 1, scale: 1, '
              f'filter: "blur(0px)", duration: 0.45, ease: "expo.out"}}, {t_bottom:.2f});')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("terminal", required=("steps",),
     example={"steps": [{"at": 0.3, "cmd": "echo hola", "out": "hola"}, {"at": 1.5, "cmd": "python run.py", "chart": True}]})
def terminal(sid, d, p, layout="full"):
    """Ventana de terminal que escribe comandos, con salida y una curva que se dibuja. Marcada como ilustrativa."""
    steps = p["steps"]  # [{"at": s, "cmd": "...", "out": "...", "chart": bool}]
    css = """
    .term { position: absolute; left: 50px; top: 540px; width: 980px; height: 600px; border-radius: 18px; overflow: hidden;
            background: rgba(7, 9, 12, .96); border: 1px solid var(--surface-line); box-shadow: 0 30px 80px rgba(0,0,0,.6); }
    .bar { height: 56px; display: flex; align-items: center; gap: 12px; padding: 0 22px; background: var(--surface);
           border-bottom: 1px solid var(--surface-line); }
    .bar i { width: 16px; height: 16px; border-radius: 50%; display: block; }
    .bar .ttl { font-family: var(--font-mono); font-size: 28px; color: var(--muted); margin-left: 12px; }
    .body { padding: 26px 30px; font-family: var(--font-mono); font-size: 30px; line-height: 1.5; color: var(--text); }
    .cmd .pr { color: var(--accent); }
    .out { color: var(--accent2); }
    svg.ch { display: block; margin-top: 10px; }
    """
    lines, js = [], []
    for k, s in enumerate(steps):
        cmd = s["cmd"]
        lines.append(f'<div class="cmd"><span class="pr">$ </span><span id="{sid}-c{k}" data-full="{esc(cmd)}"></span></div>')
        typing = min(p.get("max_typing", 1.1), 0.035 * len(cmd))
        js.append(f'(function(){{ const el = document.getElementById("{sid}-c{k}"); const full = el.dataset.full; '
                  f'const st = {{n: 0}}; const upd = () => {{ el.textContent = full.slice(0, Math.round(st.n)); }}; upd(); '
                  f'tl.to(st, {{n: full.length, duration: {typing:.2f}, ease: "none", onUpdate: upd}}, {s["at"]:.2f}); }})();')
        if s.get("out"):
            lines.append(f'<div class="out" id="{sid}-o{k}">› {esc(s["out"])}</div>')
            js.append(f'tl.fromTo("#{sid}-o{k}", {{opacity: 0}}, {{opacity: 1, duration: 0.15}}, {s["at"] + typing + 0.25:.2f});')
        if s.get("chart"):
            pts = " ".join(f"{x},{180 - 160 / (1 + math.exp(-(x - 420) / 70)):.1f}" for x in range(0, 881, 20))
            lines.append(f'<svg class="ch" width="900" height="200"><polyline id="{sid}-pl" points="{pts}" fill="none" '
                         f'stroke="var(--accent3)" stroke-width="5" stroke-dasharray="1400" stroke-dashoffset="1400"/></svg>')
            js.append(f'tl.to("#{sid}-pl", {{attr: {{"stroke-dashoffset": 0}}, duration: 0.9, ease: "power2.out"}}, '
                      f'{s["at"] + typing + 0.2:.2f});')
    body = (f'<div class="term" id="{sid}-term"><div class="bar"><i style="background:#FF5F57"></i>'
            f'<i style="background:#FEBC2E"></i><i style="background:#28C840"></i>'
            f'<span class="ttl">{esc(p.get("title", "zsh"))}</span></div>'
            f'<div class="body">{"".join(lines)}</div></div>'
            f'<div class="tag-ilus" style="left:60px;top:1150px">{esc(CTX["labels"]["illustrative"])}</div>')
    js.insert(0, f'tl.fromTo("#{sid}-term", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.4, ease: "expo.out"}}, 0.05);')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("community", required=("center", "words"),
     example={"center": "Proyecto", "words": [["Uno", 0.2], ["Dos", 0.8], ["Tres", 1.6]]})
def community(sid, d, p, layout="full"):
    """Personas (iniciales) conectándose a un nodo central; palabras clave en secuencia."""
    center, words = p["center"], p["words"]
    cx, cy = 540, 720
    r = _rand(11)
    n = 12
    av, ln, js = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n + 0.2
        x, y = cx + 410 * math.cos(a), cy + 330 * math.sin(a)
        L = math.hypot(x - cx, y - cy)
        letter = "ABCDEFGHJKLMNPRS"[int(r() * 16)]
        col = ["accent", "accent2", "accent3"][i % 3]
        ln.append(f'<line id="{sid}-k{i}" x1="{x:.0f}" y1="{y:.0f}" x2="{cx}" y2="{cy}" stroke="var(--{col})" stroke-width="2" '
                  f'opacity=".6" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}"/>')
        av.append(f'<div class="av" id="{sid}-v{i}" style="left:{x - 42:.0f}px;top:{y - 42:.0f}px;border-color:var(--{col})">{letter}</div>')
        t = 0.1 + i * 0.07
        js.append(f'tl.fromTo("#{sid}-v{i}", {{opacity: 0, scale: 0.4}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "expo.out"}}, {t:.2f});')
        js.append(f'tl.to("#{sid}-k{i}", {{attr: {{"stroke-dashoffset": 0}}, duration: 0.4, ease: "power2.out"}}, {t + 0.2:.2f});')
    css = """
    svg.net { position: absolute; inset: 0; }
    .av { position: absolute; width: 84px; height: 84px; border-radius: 50%; border: 3px solid; background: var(--surface);
          display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-weight: 700;
          font-size: 36px; color: var(--text); }
    .hub { position: absolute; left: 190px; width: 700px; height: 130px; border-radius: 65px; display: flex;
           align-items: center; justify-content: center; background: color-mix(in srgb, var(--accent) 12%, var(--bg));
           border: 2px solid var(--accent); font-family: var(--font-display); font-weight: 700; font-size: 50px; color: var(--text);
           box-shadow: 0 0 50px color-mix(in srgb, var(--accent) 40%, transparent); }
    .words { position: absolute; left: 0; right: 0; top: 1100px; display: flex; justify-content: center; gap: 30px;
             font-family: var(--font-mono); font-size: 34px; color: var(--accent2); letter-spacing: .04em; }
    """
    body = (f'<svg class="net" width="1080" height="1920">{"".join(ln)}</svg>' + "".join(av)
            + f'<div class="hub" id="{sid}-hub" style="top:{cy - 65}px">{esc(center)}</div>'
            + '<div class="words">' + "".join(f'<span id="{sid}-w{i}">{esc(w)}</span>' for i, (w, _) in enumerate(words))
            + '</div>')
    js.insert(0, f'tl.fromTo("#{sid}-hub", {{opacity: 0, scale: 0.8}}, {{opacity: 1, scale: 1, duration: 0.4, ease: "expo.out"}}, 0.05);')
    js += [f'tl.fromTo("#{sid}-w{i}", {{opacity: 0, y: 10}}, {{opacity: 1, y: 0, duration: 0.25, ease: "power3.out"}}, {t:.2f});'
           for i, (_, t) in enumerate(words)]
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("verify-refs", required=("rows",),
     example={"title": "FUENTES", "rows": [["Fuente A", "ok", "ok", 0.5], ["Fuente B", "falla", "bad", 1.5]]})
def verify_refs(sid, d, p, layout="full"):
    """Lista de fuentes o afirmaciones que se verifican; las falsas se tachan en ámbar. Marcada como ilustrativa."""
    rows = p["rows"]
    css = """
    .card { position: absolute; left: 50px; top: 560px; width: 980px; border-radius: 20px; padding: 30px 34px;
            background: rgba(7, 9, 12, .95); border: 1px solid var(--surface-line); box-shadow: 0 30px 80px rgba(0,0,0,.6); }
    .hd { font-family: var(--font-mono); font-size: 30px; color: var(--muted); letter-spacing: .1em; margin-bottom: 18px; }
    .row { display: flex; align-items: center; justify-content: space-between; padding: 18px 0;
           border-top: 1px solid var(--surface-line); }
    .row .n { font-family: var(--font-display); font-weight: 700; font-size: 44px; color: var(--text); position: relative; }
    .row .st { font-family: var(--font-mono); font-size: 30px; }
    .ok { color: var(--accent2); } .bad { color: var(--warn); }
    .strike { position: absolute; left: 0; top: 52%; height: 4px; width: 100%; background: var(--warn); transform-origin: 0 50%; }
    """
    body_rows, js = [], [f'tl.fromTo("#{sid}-card", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.4, ease: "expo.out"}}, 0.05);']
    for i, (name, status, kind, t) in enumerate(rows):
        mark = "✓" if kind == "ok" else "⚠"
        strike = f'<i class="strike" id="{sid}-x{i}"></i>' if kind == "bad" else ""
        body_rows.append(f'<div class="row" id="{sid}-r{i}"><span class="n">{esc(name)}{strike}</span>'
                         f'<span class="st {kind}" id="{sid}-s{i}">{mark} {esc(status)}</span></div>')
        js.append(f'tl.fromTo("#{sid}-r{i}", {{opacity: 0, x: -16}}, {{opacity: 1, x: 0, duration: 0.25, ease: "power3.out"}}, {0.25 + i * 0.15:.2f});')
        js.append(f'tl.fromTo("#{sid}-s{i}", {{opacity: 0, scale: 0.7}}, {{opacity: 1, scale: 1, duration: 0.25, ease: "back.out(1.6)"}}, {t:.2f});')
        if kind == "bad":
            js.append(f'tl.fromTo("#{sid}-x{i}", {{scaleX: 0}}, {{scaleX: 1, duration: 0.3, ease: "power2.out"}}, {t + 0.1:.2f});')
    body = (f'<div class="card" id="{sid}-card"><div class="hd">{esc(p.get("title", ""))}</div>'
            + "".join(body_rows) + f'</div><div class="tag-ilus" style="left:60px;top:1110px">{esc(CTX["labels"]["illustrative"])}</div>')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("particle-title", layout="over", required=("text",), example={"text": "Título de prueba", "y": 250})
def particle_title(sid, d, p, layout="over"):
    """Un título que se forma con partículas y letras que convergen (semilla fija)."""
    text = p["text"]
    y = p.get("y", 250)
    r = _rand(23)
    letters = "".join(f'<span class="ch" id="{sid}-ch{i}">{"&nbsp;" if ch == " " else esc(ch)}</span>'
                      for i, ch in enumerate(text))
    dots = "".join(f'<i class="pt" id="{sid}-pt{i}" style="left:{100 + r() * 880:.0f}px;top:{y + 30 + r() * 60:.0f}px;'
                   f'background:var(--{["accent", "accent2", "accent3"][i % 3]})"></i>' for i in range(46))
    css = f"""
    .plate {{ position: absolute; left: 70px; right: 70px; top: {y - 26}px; height: 150px; border-radius: 22px;
              background: rgba(7, 9, 12, .78); border: 1px solid var(--surface-line);
              box-shadow: 0 18px 50px rgba(0,0,0,.45); }}
    .tt {{ position: absolute; left: 0; right: 0; top: {y}px; text-align: center; font-family: var(--font-display);
           font-weight: 700; font-size: 76px; color: var(--text); letter-spacing: -0.01em;
           text-shadow: 0 0 30px color-mix(in srgb, var(--accent) 55%, transparent), 0 6px 24px rgba(0,0,0,.7); }}
    .ch {{ display: inline-block; }}
    .pt {{ position: absolute; width: 8px; height: 8px; border-radius: 50%; display: block; }}
    """
    js = []
    for i in range(len(text)):
        dx, dy = (r() - 0.5) * 600, (r() - 0.5) * 500
        js.append(f'tl.fromTo("#{sid}-ch{i}", {{x: {dx:.0f}, y: {dy:.0f}, opacity: 0, filter: "blur(10px)"}}, '
                  f'{{x: 0, y: 0, opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out"}}, {0.05 + i * 0.025:.3f});')
    for i in range(46):
        dx, dy = (r() - 0.5) * 900, (r() - 0.5) * 700
        js.append(f'tl.fromTo("#{sid}-pt{i}", {{x: {dx:.0f}, y: {dy:.0f}, opacity: 0}}, {{x: 0, y: 0, opacity: 0.9, '
                  f'duration: 0.6, ease: "power3.out"}}, {0.02 + (i % 12) * 0.03:.2f});')
        js.append(f'tl.to("#{sid}-pt{i}", {{opacity: 0, scale: 0.2, duration: 0.3}}, {1.0 + (i % 7) * 0.03:.2f});')
    js.insert(0, f'tl.fromTo("#{sid}-plate", {{opacity: 0, scaleX: 0.6}}, {{opacity: 1, scaleX: 1, duration: 0.35, '
                 f'ease: "expo.out"}}, 0.02);')
    body = f'<div class="plate" id="{sid}-plate"></div><div class="tt">{letters}</div>{dots}'
    return wrap(sid, d, layout, css, body, "\n".join(js))
