"""Paquete «biotech»: formatos con elementos de biotecnología (ADN, proteínas, células, moléculas).

Se activa en un canal con channel.json → "format_packs": ["biotech"].
"""
import math

from formats.core import _rand, esc, fmt, wrap


ICONS = {
    # íconos de 80×80 (viewBox -40..40), trazo de marca
    "adn": ('<path d="M-14,-34 C 22,-20 22,-6 -14,8 C -50,22 -50,36 -14,50" transform="translate(0,-8) scale(0.8)" '
            'fill="none" stroke="var(--accent)" stroke-width="5"/>'
            '<path d="M14,-34 C -22,-20 -22,-6 14,8 C 50,22 50,36 14,50" transform="translate(0,-8) scale(0.8)" '
            'fill="none" stroke="var(--accent3)" stroke-width="5"/>'
            + "".join(f'<line x1="-10" x2="10" y1="{y}" y2="{y}" stroke="var(--surface-line)" stroke-width="4"/>'
                      for y in (-22, -8, 6, 20))),
    "proteina": ('<path d="M-32,20 C -30,-10 -10,-30 4,-14 C 16,0 -8,10 6,22 C 20,34 34,10 30,-14 C 28,-28 16,-34 8,-30" '
                 'fill="none" stroke="var(--accent2)" stroke-width="7" stroke-linecap="round"/>'
                 '<circle cx="-32" cy="20" r="6" fill="var(--accent)"/><circle cx="8" cy="-30" r="6" fill="var(--accent3)"/>'),
    "celula": ('<ellipse rx="34" ry="28" fill="color-mix(in srgb, var(--accent2) 15%, transparent)" stroke="var(--accent2)" '
               'stroke-width="4"/><circle cx="-6" cy="2" r="12" fill="var(--depth)" stroke="var(--accent)" stroke-width="3"/>'
               '<circle cx="16" cy="-12" r="4" fill="var(--accent2)"/><circle cx="14" cy="14" r="3" fill="var(--accent2)"/>'),
    "farmaco": ('<polygon points="0,-24 21,-12 21,12 0,24 -21,12 -21,-12" fill="none" stroke="var(--warn)" stroke-width="4"/>'
                '<polygon points="0,-14 12,-7 12,7 0,14 -12,7 -12,-7" fill="none" stroke="var(--warn)" stroke-width="2" opacity=".6"/>'
                '<line x1="21" y1="-12" x2="36" y2="-22" stroke="var(--warn)" stroke-width="4"/>'
                '<line x1="-21" y1="12" x2="-36" y2="22" stroke="var(--warn)" stroke-width="4"/>'
                '<circle cx="36" cy="-22" r="5" fill="var(--accent3)"/><circle cx="-36" cy="22" r="5" fill="var(--accent)"/>'),
}


def _icon(name, size=80):
    return f'<svg width="{size}" height="{size}" viewBox="-40 -40 80 80">{ICONS[name]}</svg>'


@fmt("lab-network", required=("core", "core_label", "modules"),
     example={"core": "1", "core_label": "persona", "plus": "+ IA",
              "modules": [["Genómica", "adn"], ["Proteínas", "proteina"], ["Células", "celula"], ["Fármacos", "farmaco"]]})
def lab_network(sid, d, p, layout="full"):
    """Un nodo central (1 persona + IA) que se expande en módulos biotech con íconos; fondo de secuencias
    ATCG y retícula molecular muy tenues."""
    cx, cy = 540, 840
    mods = p["modules"]
    pos = [(250, 590), (830, 590), (250, 1070), (830, 1070)][:len(mods)]
    r = _rand(5)
    seq_rows = "".join(
        f'<div class="seq" id="{sid}-q{i}" style="top:{220 + i * 92}px">'
        + "".join("ATCG"[int(r() * 4)] for _ in range(70)) + '</div>' for i in range(11))
    hexes = []
    for row in range(9):
        for col in range(8):
            hx, hy = col * 150 + (75 if row % 2 else 0), 240 + row * 112
            pts = " ".join(f"{hx + 46 * math.cos(math.pi / 3 * k + math.pi / 6):.0f},"
                           f"{hy + 46 * math.sin(math.pi / 3 * k + math.pi / 6):.0f}" for k in range(6))
            hexes.append(f'<polygon points="{pts}"/>')
    lines, nodes, js = [], [], []
    for i, ((x, y), (name, icon)) in enumerate(zip(pos, mods)):
        L = math.hypot(x - cx, y - cy)
        lines.append(f'<line id="{sid}-l{i}" x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="var(--accent)" '
                     f'stroke-width="3" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}" opacity=".85"/>')
        nodes.append(f'<div class="mod" id="{sid}-m{i}" style="left:{x - 160}px;top:{y - 66}px">'
                     f'{_icon(icon, 84)}<span class="disp">{esc(name)}</span></div>')
        t = 0.32 + i * 0.12
        js.append(f'tl.to("#{sid}-l{i}", {{attr: {{"stroke-dashoffset": 0}}, duration: 0.35, ease: "power2.out"}}, {t:.2f});')
        js.append(f'tl.fromTo("#{sid}-m{i}", {{opacity: 0, scale: 0.7, filter: "blur(6px)"}}, '
                  f'{{opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.4, ease: "expo.out"}}, {t + 0.22:.2f});')
        js.append(f'tl.fromTo("#{sid}-m{i} svg", {{rotate: -25}}, {{rotate: 0, duration: 0.6, ease: "expo.out"}}, {t + 0.22:.2f});')
    for i in range(11):  # las secuencias corren despacio, en sentidos alternos
        js.append(f'tl.fromTo("#{sid}-q{i}", {{x: {-60 if i % 2 else 0}}}, {{x: {0 if i % 2 else -60}, duration: {d:.2f}, '
                  f'ease: "none"}}, 0);')
    css = """
    .seq { position: absolute; left: -40px; white-space: nowrap; font-family: var(--font-mono); font-size: 30px;
           letter-spacing: .32em; color: var(--accent2); opacity: .07; }
    svg.hex { position: absolute; inset: 0; opacity: .08; }
    svg.hex polygon { fill: none; stroke: var(--accent); stroke-width: 1.5; }
    .core { position: absolute; width: 200px; height: 200px; border-radius: 50%;
            border: 3px solid var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--bg));
            box-shadow: 0 0 44px color-mix(in srgb, var(--accent) 45%, transparent);
            display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .core .n { font-family: var(--font-display); font-weight: 700; font-size: 66px; color: var(--text); line-height: 1; }
    .core .s { font-family: var(--font-mono); font-size: 28px; color: var(--accent); margin-top: 6px; }
    .ai { position: absolute; font-family: var(--font-display); font-weight: 700; font-size: 56px; color: var(--accent3);
          text-shadow: 0 0 22px color-mix(in srgb, var(--accent3) 60%, transparent); }
    .mod { position: absolute; width: 320px; height: 132px; border-radius: 20px; display: flex; align-items: center;
           justify-content: center; gap: 16px; background: rgba(18, 23, 29, .92); border: 1px solid var(--surface-line);
           font-size: 40px; font-weight: 700; color: var(--text); }
    svg.links { position: absolute; inset: 0; }
    """
    body = (seq_rows + f'<svg class="hex" width="1080" height="1920">{"".join(hexes)}</svg>'
            f'<svg class="links" width="1080" height="1920">{"".join(lines)}</svg>'
            f'<div class="core" id="{sid}-core" style="left:{cx - 100}px;top:{cy - 100}px">'
            f'<span class="n">{esc(p["core"])}</span><span class="s">{esc(p["core_label"])}</span></div>'
            f'<div class="ai" id="{sid}-ai" style="left:{cx + 100}px;top:{cy - 160}px">{esc(p.get("plus", ""))}</div>'
            + "".join(nodes))
    js = [f'tl.fromTo("#{sid}-core", {{scale: 0.3, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.45, ease: "expo.out"}}, 0.06);',
          f'tl.fromTo("#{sid}-ai", {{opacity: 0, x: -20, filter: "blur(8px)"}}, {{opacity: 1, x: 0, filter: "blur(0px)", '
          f'duration: 0.35, ease: "power3.out"}}, {p.get("plus_at", 0.3)});'] + js
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("dna-helix", example={"label": "BIOTECNOLOGÍA"})
def dna_helix(sid, d, p, layout="full"):
    """Doble hélice de ADN girando, con pares de bases; partículas de fondo fijas."""
    n = 22
    y0, y1, cx, amp = 330, 1110, 470, 190
    r = _rand(7)
    dots = "".join(f'<circle cx="{r() * 1080:.0f}" cy="{200 + r() * 1000:.0f}" r="{1.5 + r() * 2.5:.1f}" '
                   f'fill="var(--{["accent", "accent2", "accent3"][int(r() * 3)]})" opacity="{0.25 + r() * 0.4:.2f}"/>'
                   for _ in range(60))
    pairs = "".join(f'<line id="{sid}-r{i}" stroke="var(--surface-line)" stroke-width="5"/>'
                    f'<circle id="{sid}-a{i}" r="13" fill="var(--accent)"/><circle id="{sid}-b{i}" r="13" fill="var(--accent3)"/>'
                    for i in range(n))
    css = """
    svg.dna { position: absolute; inset: 0; }
    .lbl { position: absolute; left: 70px; top: 1130px; font-size: 30px; letter-spacing: .14em; color: var(--accent2); }
    """
    body = (f'<svg class="dna" width="1080" height="1920"><g>{dots}</g><g id="{sid}-h">{pairs}</g></svg>'
            f'<div class="lbl mono" id="{sid}-lbl">{esc(p.get("label", ""))}</div>')
    turns = p.get("turns", 0.9)
    js = f"""
    const N = {n}, Y0 = {y0}, Y1 = {y1}, CX = {cx}, AMP = {amp};
    const st = {{ phase: 0, grow: 0 }};
    function draw() {{
      for (let i = 0; i < N; i++) {{
        const y = Y0 + (Y1 - Y0) * i / (N - 1);
        const a = st.phase + i * 0.55;
        const s = Math.sin(a), c = Math.cos(a);
        const show = Math.max(0, Math.min(1, st.grow * N - i));
        const xa = CX + AMP * s * show, xb = CX - AMP * s * show;
        const A = document.getElementById("{sid}-a" + i), B = document.getElementById("{sid}-b" + i);
        const R = document.getElementById("{sid}-r" + i);
        A.setAttribute("cx", xa); A.setAttribute("cy", y); A.setAttribute("r", 9 + 5 * (c + 1) / 2);
        B.setAttribute("cx", xb); B.setAttribute("cy", y); B.setAttribute("r", 9 + 5 * (1 - c) / 2);
        A.setAttribute("opacity", show * (0.45 + 0.55 * (c + 1) / 2));
        B.setAttribute("opacity", show * (0.45 + 0.55 * (1 - c) / 2));
        R.setAttribute("x1", xa); R.setAttribute("y1", y); R.setAttribute("x2", xb); R.setAttribute("y2", y);
        R.setAttribute("opacity", show * 0.8);
      }}
    }}
    draw();
    tl.to(st, {{ grow: 1, duration: 0.9, ease: "power2.out", onUpdate: draw }}, 0.05);
    tl.to(st, {{ phase: {turns * 2 * math.pi:.3f}, duration: {d:.3f}, ease: "none", onUpdate: draw }}, 0);
    tl.fromTo("#{sid}-lbl", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.3 }}, 0.5);
    """
    return wrap(sid, d, layout, css, body, js)


@fmt("health-trio", required=("labels",),
     example={"labels": ["Uno", "Dos", "Tres"], "kickers": ["01", "02", "03"]})
def health_trio(sid, d, p, layout="full"):
    """Tres conceptos en secuencia: célula (entender), pulso (salud), barra de vida (vivir más).
    Con `only` (0, 1 o 2) muestra un solo concepto: para intercalarlos con la toma en cortes cortos."""
    beats = p.get("beats", [0.1, 2.6, 5.2])
    labels = p["labels"]
    ecg = "M 0 120 L 170 120 L 210 120 L 240 40 L 280 210 L 320 0 L 360 160 L 390 120 L 560 120 L 600 80 L 640 120 L 760 120"
    css = """
    .beat { position: absolute; left: 0; right: 0; top: 520px; height: 640px; display: flex; flex-direction: column;
            align-items: center; justify-content: center; gap: 46px; }
    .beat .t { font-family: var(--font-display); font-weight: 700; font-size: 58px; color: var(--text); text-align: center; }
    .beat .k { font-family: var(--font-mono); font-size: 30px; letter-spacing: .16em; color: var(--muted); }
    .bar { width: 720px; height: 34px; border-radius: 17px; background: var(--surface); border: 1px solid var(--surface-line);
           overflow: hidden; }
    .bar i { display: block; height: 100%; width: 100%; transform-origin: 0 50%; border-radius: 17px;
             background: linear-gradient(90deg, var(--accent2), var(--accent3)); }
    """
    cell = (f'<svg width="420" height="360" viewBox="-210 -180 420 360">'
            f'<ellipse id="{sid}-mem" rx="190" ry="160" fill="color-mix(in srgb, var(--accent2) 10%, transparent)" '
            f'stroke="var(--accent2)" stroke-width="4"/>'
            f'<circle id="{sid}-nuc" cx="-30" cy="10" r="62" fill="color-mix(in srgb, var(--depth) 80%, transparent)" '
            f'stroke="var(--accent)" stroke-width="3"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="{rr}" fill="var(--accent2)" opacity=".7"/>'
                      for x, y, rr in [(90, -70, 12), (110, 60, 9), (-120, -80, 8), (40, 110, 10), (-110, 90, 7)])
            + f'<line id="{sid}-scan" x1="-200" x2="200" y1="-150" y2="-150" stroke="var(--accent)" stroke-width="3" opacity=".9"/></svg>')
    pulse = (f'<svg width="760" height="220" viewBox="0 0 760 220"><path id="{sid}-ecg" d="{ecg}" fill="none" '
             f'stroke="var(--accent)" stroke-width="6" stroke-linejoin="round" stroke-dasharray="1500" stroke-dashoffset="1500"/></svg>')
    bar = f'<div class="bar"><i id="{sid}-life"></i></div>'
    visuals = [cell, pulse, bar]
    kick = p.get("kickers", ["01", "02", "03"])
    show = [p["only"]] if "only" in p else [0, 1, 2]
    if "only" in p:
        beats = [0.06]
    body = "".join(f'<div class="beat" id="{sid}-b{i}"><div class="k">{esc(kick[i])}</div>{visuals[i]}'
                   f'<div class="t">{esc(labels[i])}</div></div>' for i in show)
    js = []
    anims = {
        0: f'tl.fromTo("#{sid}-scan", {{attr: {{y1: -150, y2: -150}}}}, {{attr: {{y1: 150, y2: 150}}, duration: 1.4, '
           f'ease: "power1.inOut"}}, {{t}});',
        1: f'tl.to("#{sid}-ecg", {{attr: {{"stroke-dashoffset": 0}}, duration: 1.2, ease: "power1.inOut"}}, {{t}});',
        2: f'tl.fromTo("#{sid}-life", {{scaleX: 0.35}}, {{scaleX: 0.92, duration: 1.1, ease: "power2.out"}}, {{t}});',
    }
    for i, t in zip(show, beats):
        js.append(anims[i].replace("{t}", f"{t + 0.2:.2f}"))
    for n, (i, t) in enumerate(zip(show, beats)):
        end = beats[n + 1] - 0.05 if n + 1 < len(beats) else d - 0.25
        js.append(f'tl.fromTo("#{sid}-b{i}", {{opacity: 0, filter: "blur(10px)", scale: 0.96}}, '
                  f'{{opacity: 1, filter: "blur(0px)", scale: 1, duration: 0.3, ease: "expo.out"}}, {t:.2f});')
        if n + 1 < len(beats):
            js.append(f'tl.to("#{sid}-b{i}", {{opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in"}}, {end - 0.18:.2f});')
    return wrap(sid, d, layout, css, body, "\n".join(js))
