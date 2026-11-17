"""Paquete «lottie»: animaciones de After Effects / LottieFiles / Rive exportadas a Lottie, con la marca del canal.

Las animaciones viven en bibliotecas (motor: assets/lottie/; canal: <canal>/assets/lottie/) con origen y
licencia; se agregan con `scripts/tools/lottie.py add` y se recolorean con la paleta de la marca al componer.
La línea de tiempo de la escena mueve cada cuadro (`goToAndStop`): tramos, velocidad y repeticiones son
deterministas (ADR 0022, 0023). Se activa con channel.json → "format_packs": [..., "lottie"].
"""
import json

from formats.core import esc, fmt, wrap
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain


def _uses(p):
    return [("lottie", p["anim"])]


def _check(p):
    errs = []
    speed = p.get("speed", 1)
    if not isinstance(speed, (int, float)) or not 0.1 <= speed <= 4:
        errs.append("speed: número entre 0.1 y 4")
    loops = p.get("loops", 1)
    if loops != "fill" and not (isinstance(loops, int) and 1 <= loops <= 20):
        errs.append("loops: entero de 1 a 20 o «fill» (repetir hasta llenar la escena)")
    a, b = p.get("from", 0), p.get("to")
    if not isinstance(a, (int, float)) or a < 0 or (b is not None and (not isinstance(b, (int, float)) or b <= a)):
        errs.append("from/to: segundos de la animación, con from < to")
    return errs


def _player_js(sid, d, p, box_id, t0):
    """Carga la animación (datos locales) y la mueve desde la línea de tiempo de la escena."""
    key = json.dumps(f"lottie:{p['anim']}")
    loops = json.dumps(p.get("loops", 1))
    to = "null" if p.get("to") is None else float(p["to"])
    return f"""
    const A = window.__vv[{key}];
    const L = __vvLottie.loadAnimation({{container: document.getElementById("{box_id}"), renderer: "svg",
      loop: false, autoplay: false, animationData: JSON.parse(JSON.stringify(A)),
      rendererSettings: {{preserveAspectRatio: "xMidYMid meet", progressiveLoad: false}}}});
    const fr = A.fr, fa = {float(p.get('from', 0))} * fr, fb = {to} === null ? A.op - A.ip : Math.min({to} * fr, A.op - A.ip);
    const span = Math.max(fb - fa, 1), play = span / fr / {float(p.get('speed', 1))};
    const reps = {loops} === "fill" ? Math.max(1, Math.floor(({d} - {t0} - .25) / play)) : {loops};
    const ls = {{f: 0}};
    const lDraw = () => L.goToAndStop(ls.f >= reps * span ? fb - 0.01 : fa + (ls.f % span), true);
    tl.fromTo(ls, {{f: 0}}, {{f: reps * span, duration: reps * play, ease: "none", onUpdate: lDraw}}, {t0});
    lDraw();"""


@fmt("lottie-scene", required=("anim",), needs=("lottie",), check=_check, uses=_uses,
     example={"anim": "check-draw", "kicker": "VERIFICADO", "title": "Los datos *cuadran*"})
def lottie_scene(sid, d, p, layout="full"):
    """Una animación Lottie grande (tramo, velocidad y repeticiones a elegir), con kicker y título opcionales que
    entran letra por letra. Para ilustrar una idea con movimiento de diseñador."""
    size = int(p.get("size", 760))
    has_title = bool(p.get("title"))
    cy = int(p.get("y", 760 if has_title else 680))
    css = KINETIC_CSS + f"""
    .lt-box {{ position: absolute; left: {540 - size // 2}px; top: {cy - size // 2}px; width: {size}px; height: {size}px; }}
    .lt-box svg {{ width: 100% !important; height: 100% !important; }}
    .lt-h {{ position: absolute; left: 70px; right: 70px; top: 250px; text-align: center; }}
    .lt-h .k {{ font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
                color: var(--accent2); margin-bottom: 14px; }}
    .lt-h .t {{ font-family: var(--font-display); font-weight: 700; font-size: 66px; line-height: 1.04; color: var(--text); }}
    """
    head = ""
    if has_title or p.get("kicker"):
        head = (f'<div class="lt-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
                f'<div class="t">{kinetic(p.get("title", ""))}</div></div>')
    body = head + f'<div class="lt-box" id="{sid}-lot"></div>'
    js = [_player_js(sid, d, p, f"{sid}-lot", 0.12),
          f'tl.fromTo("#{sid}-lot", {{opacity: 0, scale: .86}}, {{opacity: 1, scale: 1, duration: .45, ease: "expo.out"}}, .05);']
    if head:
        js.append(f'tl.fromTo("#{sid}-h .k", {{opacity: 0, y: -12}}, {{opacity: 1, y: 0, duration: .35}}, .05);')
        if has_title:
            js.append(kinetic_in(f"#{sid}-h .t", "rise", 0.15, len(plain(p["title"]))))
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("lottie-accent", layout="over", required=("anim",), needs=("lottie",), check=_check, uses=_uses,
     example={"anim": "pulse-rings", "x": 540, "y": 560, "size": 360, "label": "AQUÍ", "loops": "fill"})
def lottie_accent(sid, d, p, layout="over"):
    """Una animación Lottie pequeña sobre la toma (sello, check, pulso, flecha) en una posición elegida, con
    etiqueta corta opcional. Para subrayar un momento sin tapar a la persona."""
    size = int(p.get("size", 320))
    x, y = int(p.get("x", 540)), int(p.get("y", 560))
    css = f"""
    .la-box {{ position: absolute; left: {x - size // 2}px; top: {y - size // 2}px; width: {size}px; height: {size}px;
               filter: drop-shadow(0 8px 26px rgba(0,0,0,.55)); }}
    .la-box svg {{ width: 100% !important; height: 100% !important; }}
    .la-l {{ position: absolute; left: {x - 300}px; width: 600px; top: {y + size // 2 + 8}px; text-align: center;
             font-family: var(--font-mono); font-weight: 600; font-size: 32px; letter-spacing: .2em; color: var(--text);
             text-shadow: 0 2px 12px rgba(0,0,0,.8); }}
    """
    label = f'<div class="la-l" id="{sid}-l">{esc(p["label"])}</div>' if p.get("label") else ""
    body = f'<div class="la-box" id="{sid}-lot"></div>{label}'
    js = [_player_js(sid, d, p, f"{sid}-lot", 0.05),
          f'tl.fromTo("#{sid}-lot", {{opacity: 0, scale: .6}}, {{opacity: 1, scale: 1, duration: .35, ease: "back.out(2)"}}, 0);']
    if label:
        js.append(f'tl.fromTo("#{sid}-l", {{opacity: 0, y: 12}}, {{opacity: 1, y: 0, duration: .3}}, .2);')
    return wrap(sid, d, layout, css, body, "\n".join(js))
