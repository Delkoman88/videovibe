"""Efectos sobre la toma (`storyboard.json → fx`, ADR 0025): capas dentro de `#cam`, con la misma escala de cámara.

Orden de capas: placa → capa «detrás» (texto, fondo) → recorte de la persona → (fuera de #cam) tarjetas y
subtítulos. El recorte viene de `scripts/pipeline/cutout.py`. Sin `fx`, nada de esto se genera y el
`index.html` es el de siempre.

Tipos:
  text-behind      texto grande detrás de la persona (`depth`: behind, front, o through = aparece delante y
                   luego queda detrás)
  background-swap  el fondo de la toma se cambia por el de la marca (con título opcional detrás)
  subject-glow     halo del color de acento alrededor de la persona
  freeze-cutout    cuadro congelado, persona recortada con contorno y etiqueta (solo en pausas sin voz)
"""
from formats.text import KINETIC_CSS, kinetic, kinetic_in, kinetic_out, plain, title_size

TYPES = ("text-behind", "background-swap", "subject-glow", "freeze-cutout")

FX_CSS = KINETIC_CSS + """
      .fx-full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
      .fx-behind { position: absolute; left: 0; right: 0; text-align: center;
                   filter: drop-shadow(0 12px 30px rgba(0,0,0,.35)); }
      /* La sombra va en el contenedor: text-shadow se recortaba en las letras animadas (rectángulo). */
      .fx-behind .fx-t { font-family: var(--font-display); font-weight: 700; line-height: .92; letter-spacing: -.03em; }
      .fx-bg { position: absolute; inset: 0; opacity: 0; background:
                 radial-gradient(900px 1100px at 50% 38%, color-mix(in srgb, var(--depth) 70%, transparent), transparent 70%),
                 linear-gradient(var(--bg), var(--bg)); }
      .fx-bg::after { content: ""; position: absolute; inset: 0; opacity: .14;
                      background-image: linear-gradient(var(--surface-line) 1px, transparent 1px),
                                        linear-gradient(90deg, var(--surface-line) 1px, transparent 1px);
                      background-size: 60px 60px; }
      .fx-glow { position: absolute; inset: 0; }
      .fx-dim { position: absolute; inset: 0; background: rgba(4,6,10,.55); }
      .fx-label { position: absolute; left: 80px; right: 80px; text-align: center; }
      .fx-label span { display: inline-block; padding: 14px 28px; border-radius: 14px; background: rgba(5,8,12,.85);
                       border: 2px solid var(--accent); font-family: var(--font-display); font-weight: 700;
                       font-size: 46px; color: var(--text); }
"""


def _role_color(brand, role):
    return f"var(--{brand['highlight_roles'].get(role or 'keyword', 'accent')})"


def _cut_video(fx, cut, track, extra=""):
    d = round(fx["out"] - fx["in"], 3)
    return (f'<video id="fxc-{fx["id"]}" class="clip fx-full" src="assets/fx-{fx["id"]}.webm" '
            f'data-start="{fx["in"]}" data-duration="{d}" data-media-start="{round(fx["in"] - cut["start"], 3)}" '
            f'data-track-index="{track}" muted playsinline{extra}></video>')


def text_y(fx, cut, size):
    """y del texto: el pedido, o justo para que la cabeza tape su parte de abajo."""
    if isinstance(fx.get("y"), (int, float)):
        return int(fx["y"])
    top = (cut or {}).get("subject_top")
    if top is None:
        return 160
    return int(max(110, min(top - size * 0.55, 900)))


def markup(sb, brand, cutouts):
    """(html dentro de #cam, js para la línea de tiempo principal). Vacío si no hay fx."""
    html, js = [], []
    for k, fx in enumerate(sb.get("fx", [])):
        t = fx["type"]
        cut = cutouts.get(fx["id"], {})
        base = 40 + k * 4
        if t == "freeze-cutout":
            at, d = fx["at"], fx.get("duration", 1.2)
            html.append(
                f'<div id="fx-{fx["id"]}" class="clip" data-start="{at}" data-duration="{d}" data-track-index="{base}" '
                f'style="position:absolute;inset:0">'
                f'<img class="fx-full" src="assets/fx-{fx["id"]}-frame.png" alt="" />'
                f'<div class="fx-dim" id="fxd-{fx["id"]}"></div>'
                f'<img class="fx-full" id="fxp-{fx["id"]}" src="assets/fx-{fx["id"]}.png" alt="" '
                f'style="filter: drop-shadow(0 0 0 var(--accent)) drop-shadow(0 0 6px var(--accent)) '
                f'drop-shadow(0 0 22px var(--accent))" />'
                + (f'<div class="fx-label" id="fxl-{fx["id"]}" style="top:{fx.get("label_y", 240)}px">'
                   f'<span>{_esc(fx["label"])}</span></div>' if fx.get("label") else "") + '</div>')
            js += [f'tl.fromTo("#fxd-{fx["id"]}", {{opacity: 0}}, {{opacity: 1, duration: .18}}, {at});',
                   f'tl.fromTo("#fxp-{fx["id"]}", {{scale: 1, rotation: 0}}, {{scale: 1.06, rotation: -1.2, duration: .35, '
                   f'ease: "back.out(2)"}}, {at});']
            if fx.get("label"):
                js.append(f'tl.fromTo("#fxl-{fx["id"]}", {{opacity: 0, y: 24}}, {{opacity: 1, y: 0, duration: .35, '
                          f'ease: "expo.out"}}, {at + .15:.3f});')
            continue
        a, b = fx["in"], fx["out"]
        d = round(b - a, 3)
        if t in ("text-behind", "background-swap"):
            layer = []
            if t == "background-swap":
                layer.append(f'<div class="fx-bg" id="fxb-{fx["id"]}"></div>')
            text = fx.get("text")
            depth = fx.get("depth", "behind")
            front = ""
            if text:
                size = int(fx.get("size") or title_size(text, 230))
                y = text_y(fx, cut, size)
                block = (f'<div class="fx-t" style="font-size:{size}px;color:{_role_color(brand, fx.get("role"))}">'
                         f'{kinetic(text)}</div>')
                variant = fx.get("variant", "rise")
                if depth != "front":
                    layer.append(f'<div class="fx-behind" id="fxt-{fx["id"]}" style="top:{y}px">{block}</div>')
                    js.append(kinetic_in(f'#fxt-{fx["id"]}', variant, a + 0.05, len(plain(text))))
                    js.append(kinetic_out(f'#fxt-{fx["id"]}', variant, max(b - 0.4, a + 0.6)))
                if depth in ("front", "through"):
                    # copia delante de la persona; en «through» se desvanece a mitad y el texto «pasa» detrás
                    front = (f'<div id="fxf-{fx["id"]}" class="clip" data-start="{a}" data-duration="{d}" '
                             f'data-track-index="{base + 2}" data-layout-allow-overlap style="position:absolute;inset:0">'
                             f'<div class="fx-behind" id="fxtf-{fx["id"]}" style="top:{y}px">{block}</div></div>')
                    js.append(kinetic_in(f'#fxtf-{fx["id"]}', variant, a + 0.05, len(plain(text))))
                    if depth == "through":
                        mid = a + max(min(fx.get("pass_at", (b - a) * 0.45), b - a - 0.6), 0.5)
                        js.append(f'tl.to("#fxtf-{fx["id"]}", {{opacity: 0, duration: .45, ease: "sine.inOut"}}, {mid:.3f});')
                    else:
                        js.append(kinetic_out(f'#fxtf-{fx["id"]}', variant, max(b - 0.4, a + 0.6)))
            if t == "background-swap":
                js += [f'tl.fromTo("#fxb-{fx["id"]}", {{opacity: 0}}, {{opacity: 1, duration: .55, ease: "sine.inOut"}}, {a});',
                       f'tl.to("#fxb-{fx["id"]}", {{opacity: 0, duration: .55, ease: "sine.inOut"}}, {b - 0.55:.3f});']
            html.append(f'<div id="fx-{fx["id"]}" class="clip" data-start="{a}" data-duration="{d}" '
                        f'data-track-index="{base}" style="position:absolute;inset:0">{"".join(layer)}</div>')
            html.append(_cut_video(fx, cut, base + 1))
            if front:
                html.append(front)
        elif t == "subject-glow":
            col = _role_color(brand, fx.get("role"))
            # El contenedor no lleva tiempo (HyperFrames temporiza el <video>); solo se anima su opacidad.
            html.append(f'<div id="fx-{fx["id"]}" class="fx-glow" style="filter: drop-shadow(0 0 4px {col}) '
                        f'drop-shadow(0 0 18px {col}) drop-shadow(0 0 40px {col})">{_cut_video(fx, cut, base + 1)}</div>')
            js += [f'tl.fromTo("#fx-{fx["id"]}", {{opacity: 0}}, {{opacity: 1, duration: .35}}, {a});',
                   f'tl.to("#fx-{fx["id"]}", {{opacity: 0, duration: .35}}, {b - 0.35:.3f});']
    if not html:
        return "", ""
    return "\n        " + "\n        ".join(html), "\n      ".join(js)


def _esc(s):
    import html as h
    return h.escape(str(s or ""), quote=True)


def css(sb):
    return FX_CSS if sb.get("fx") else ""
