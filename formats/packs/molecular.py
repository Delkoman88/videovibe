"""Paquete «molecular»: proteínas, ADN y moléculas en 3D (3Dmol.js) con los colores de la marca.

Las estructuras viven en bibliotecas (motor: assets/structures/; canal: <canal>/assets/structures/) y se
agregan con `scripts/tools/structures.py fetch --pdb 1HHO` o `--pubchem aspirin`: el render no usa red.
Cada cuadro se dibuja desde la línea de tiempo de la escena con vista y ángulo absolutos (ADR 0022, 0024);
las superficies se calculan antes del primer cuadro (`window.__hf.buildReady`).
Se activa con channel.json → "format_packs": [..., "molecular"].
"""
import json

from formats.core import esc, fmt, wrap
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain

STYLES = ("auto", "cartoon", "stick", "sphere", "surface", "ballstick")
COLORS = ("brand", "spectrum", "element")

# Estilo, colores de marca, vista y dibujo por cuadro. `vvMol(caja, datos, opciones)` → {v, base, draw, ready}.
MOL_JS = """
    const vvVar = (n) => getComputedStyle(document.documentElement).getPropertyValue("--" + n).trim();
    const vvMol = (boxId, key, o) => {
      const S = window.__vv[key], box = document.getElementById(boxId);
      const v = $3Dmol.createViewer(box, {antialias: true, preserveDrawingBuffer: true});
      v.setBackgroundColor(0x000000, 0);
      const m = v.addModel(S.text, S.format);
      const acc = ["accent", "accent2", "accent3", "warn"].map(vvVar);
      const elem = Object.assign({}, $3Dmol.elementColors.Jmol, {C: acc[0], H: vvVar("text") || "#ffffff"});
      const chains = [...new Set(m.selectedAtoms({hetflag: false}).map((a) => a.chain))];
      const big = chains.length > 0 && m.selectedAtoms({}).length > 60;
      const style = o.style === "auto" ? (big ? "cartoon" : "ballstick") : o.style;
      const chainColor = (i) => acc[i % acc.length];
      v.setStyle({}, {});
      const hets = {hetflag: true, not: {resn: ["HOH", "WAT", "DOD"]}};
      if (style === "cartoon" || style === "surface") {
        chains.forEach((c, i) => v.setStyle({chain: c, hetflag: false}, {cartoon: o.color === "spectrum"
          ? {color: "spectrum"} : {color: chainColor(i), thickness: .5}}));
        v.setStyle(hets, {stick: {radius: .28, colorscheme: {prop: "elem", map: Object.assign({}, elem, {C: acc[2]})}}});
      } else if (style === "sphere") {
        chains.forEach((c, i) => v.setStyle({chain: c}, {sphere: o.color === "brand" ? {color: chainColor(i)} : {colorscheme: {prop: "elem", map: elem}}}));
        if (!chains.length) v.setStyle({}, {sphere: {colorscheme: {prop: "elem", map: elem}}});
      } else if (style === "stick") {
        v.setStyle({}, {stick: {radius: .22, colorscheme: {prop: "elem", map: elem}}});
      } else {
        v.setStyle({}, {stick: {radius: .16, colorscheme: {prop: "elem", map: elem}},
                        sphere: {scale: .26, colorscheme: {prop: "elem", map: elem}}});
      }
      if (o.highlight) v.addStyle(o.highlight, {stick: {radius: .34, color: acc[2]}, sphere: {scale: .32, color: acc[2]}});
      if (o.outline) v.setViewStyle({style: "outline", color: vvVar("bg") || "#000000", width: .06});
      v.zoomTo(); v.zoom(o.zoom); v.render();
      const base = v.getView();
      let focus = base;
      if (o.focus) { v.zoomTo(o.focus); v.zoom(o.focusZoom); focus = v.getView(); v.setView(base); }
      let ready = Promise.resolve();
      if (style === "surface") {
        const jobs = chains.map((c, i) => v.addSurface($3Dmol.SurfaceType.VDW,
          {opacity: .72, color: chainColor(i)}, {chain: c, hetflag: false}));
        ready = Promise.all(jobs).then(() => v.render());
        window.__hf = window.__hf || {};
        (window.__hf.buildReady = window.__hf.buildReady || {})[boxId] = ready;
      }
      const draw = (angle, f) => {
        v.resize();
        const view = base.map((b, i) => i < 4 ? b + (focus[i] - b) * f : b);
        v.setView(view);
        if (angle) v.rotate(angle, o.axis, 0);
        v.render();
      };
      return {v, draw, ready};
    };"""


def _opts(p, zoom=1.0, **extra):
    o = {"style": p.get("style", "auto"), "color": p.get("color", "brand"), "zoom": float(p.get("zoom", zoom)),
         "axis": p.get("axis", "y"), "outline": bool(p.get("outline", True))}
    o.update(extra)
    return json.dumps(o, ensure_ascii=False)


def _check(p):
    errs = []
    if p.get("style", "auto") not in STYLES:
        errs.append(f"style: «{p.get('style')}» (usa {', '.join(STYLES)})")
    if p.get("color", "brand") not in COLORS:
        errs.append(f"color: «{p.get('color')}» (usa {', '.join(COLORS)})")
    deg = p.get("degrees", 140)
    if not isinstance(deg, (int, float)) or not 0 <= deg <= 720:
        errs.append("degrees: número entre 0 y 720")
    if p.get("axis", "y") not in ("x", "y", "z"):
        errs.append("axis: x, y o z")
    z = p.get("zoom", 1.0)
    if not isinstance(z, (int, float)) or not 0.3 <= z <= 4:
        errs.append("zoom: número entre 0.3 y 4")
    return errs


def _sel(focus):
    """{chain, resi, resn} del storyboard → selección de 3Dmol."""
    sel = {k: focus[k] for k in ("chain", "resi", "resn") if k in focus}
    return sel


def _check_focus(p):
    errs = _check(p)
    f = p.get("focus")
    if not isinstance(f, dict) or not set(f) & {"chain", "resi", "resn"} or set(f) - {"chain", "resi", "resn"}:
        errs.append("focus: objeto con chain, resi y/o resn (p. ej. {\"resn\": \"HEM\"})")
    return errs


def _check_items(p, items):
    """La selección de `focus` existe en la estructura (según el resumen guardado en la biblioteca)."""
    from scripts.core import structlib
    it = items.get(p.get("structure"))
    if not it or not isinstance(p.get("focus"), dict):
        return []
    return [f"focus: {e}" for e in structlib.selection_problems(p["focus"], it)]


HEAD_CSS = KINETIC_CSS + """
    .mol-h { position: absolute; left: 70px; right: 70px; top: 230px; text-align: center; }
    .mol-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
                color: var(--accent2); margin-bottom: 12px; }
    .mol-h .t { font-family: var(--font-display); font-weight: 700; font-size: 62px; line-height: 1.04; color: var(--text); }
    .mol-box { position: absolute;
               -webkit-mask-image: radial-gradient(ellipse 62% 58% at 50% 50%, #000 58%, transparent 100%);
               mask-image: radial-gradient(ellipse 62% 58% at 50% 50%, #000 58%, transparent 100%); }
    .mol-box canvas { outline: none; }
    .mol-cap { position: absolute; left: 70px; right: 70px; text-align: center; font-family: var(--font-mono);
               font-size: 28px; color: var(--muted); }
"""


def _head(sid, p):
    if not (p.get("title") or p.get("kicker")):
        return "", []
    html = (f'<div class="mol-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="t">{kinetic(p.get("title") or "")}</div></div>')
    js = [f'tl.fromTo("#{sid}-h .k", {{opacity: 0, y: -12}}, {{opacity: 1, y: 0, duration: .35}}, .05);']
    if p.get("title"):
        js.append(kinetic_in(f"#{sid}-h .t", "rise", 0.12, len(plain(p["title"]))))
    return html, js


@fmt("molecule-spin", required=("structure",), needs=("3dmol",), check=_check,
     uses=lambda p: [("structures", p["structure"])],
     example={"structure": "hemoglobin", "kicker": "PROTEÍNA", "title": "La *hemoglobina*",
              "caption": "PDB 1HHO · 2 cadenas + grupos hemo"})
def molecule_spin(sid, d, p, layout="full"):
    """Proteína, ADN o molécula girando despacio en 3D, con los colores de la marca por cadena (estilos cartoon,
    stick, sphere, surface o ballstick; `auto` elige según el tamaño), título y pie con la fuente."""
    has_head = bool(p.get("title") or p.get("kicker"))
    top, h = (380, 760) if has_head else (260, 900)
    key = json.dumps(f"structures:{p['structure']}")
    css = HEAD_CSS + f".mol-box {{ left: 40px; top: {top}px; width: 1000px; height: {h}px; }}"
    head, hjs = _head(sid, p)
    cap = f'<div class="mol-cap" id="{sid}-c" style="top:{top + h - 10}px">{esc(p.get("caption", ""))}</div>' \
        if p.get("caption") else ""
    body = head + f'<div class="mol-box" id="{sid}-mol"></div>' + cap
    js = [MOL_JS,
          f'const M = vvMol("{sid}-mol", {key}, {_opts(p, zoom=1.35)});',
          'const ms = {a: 0};',
          f'tl.fromTo(ms, {{a: 0}}, {{a: {float(p.get("degrees", 140))}, duration: {d:.3f}, ease: "none", '
          f'onUpdate: () => M.draw(ms.a, 0)}}, 0);',
          'M.draw(0, 0);',
          f'tl.fromTo("#{sid}-mol", {{opacity: 0, scale: .9}}, {{opacity: 1, scale: 1, duration: .6, ease: "expo.out"}}, .05);',
          *hjs]
    if cap:
        js.append(f'tl.fromTo("#{sid}-c", {{opacity: 0}}, {{opacity: 1, duration: .4}}, .5);')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("molecule-focus", required=("structure", "focus", "label"), needs=("3dmol",), check=_check_focus,
     uses=lambda p: [("structures", p["structure"])], check_items=_check_items,
     example={"structure": "hemoglobin", "focus": {"resn": "HEM", "chain": "A"}, "label": "Grupo hemo: aquí se une el O₂",
              "kicker": "SITIO ACTIVO"})
def molecule_focus(sid, d, p, layout="full"):
    """La estructura completa gira un momento y la cámara viaja hasta un sitio (cadena, residuos o ligando,
    p. ej. {"resn": "HEM"}), que se resalta en color con un anillo y una etiqueta. Para señalar dónde ocurre algo."""
    top, h = 300, 860
    key = json.dumps(f"structures:{p['structure']}")
    sel = _sel(p["focus"])
    cx, cy = 540, top + h // 2
    css = HEAD_CSS + f"""
    .mol-box {{ left: 40px; top: {top}px; width: 1000px; height: {h}px; }}
    .mf-ring {{ position: absolute; left: {cx - 150}px; top: {cy - 150}px; width: 300px; height: 300px; border-radius: 50%;
                border: 5px solid var(--accent3); opacity: 0;
                box-shadow: 0 0 30px color-mix(in srgb, var(--accent3) 60%, transparent); }}
    .mf-l {{ position: absolute; left: 90px; right: 90px; top: {cy + 175}px; text-align: center; opacity: 0; }}
    .mf-l span {{ display: inline-block; padding: 14px 26px; border-radius: 14px; background: rgba(5,8,12,.82);
                  border: 2px solid var(--accent3); font-family: var(--font-display); font-weight: 700; font-size: 44px;
                  line-height: 1.1; color: var(--text); }}
    .mf-k {{ position: absolute; left: 0; right: 0; top: 230px; text-align: center; font-family: var(--font-mono);
             font-weight: 600; font-size: 30px; letter-spacing: .24em; color: var(--accent2); }}
    """
    body = (f'<div class="mf-k" id="{sid}-k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="mol-box" id="{sid}-mol"></div><div class="mf-ring" id="{sid}-r"></div>'
            f'<div class="mf-l" id="{sid}-l"><span>{esc(p["label"])}</span></div>')
    t_zoom = max(min(d * 0.32, 1.2), 0.5)
    zoom_dur = max(min(d * 0.35, 1.4), 0.6)
    js = [MOL_JS,
          f'const M = vvMol("{sid}-mol", {key}, {_opts(p, focus=sel, highlight=sel, focusZoom=float(p.get("focus_zoom", 0.6)))});',
          'const ms = {a: 0, f: 0};',
          f'tl.fromTo(ms, {{a: 0}}, {{a: {float(p.get("degrees", 50))}, duration: {t_zoom:.3f}, ease: "sine.inOut", '
          f'onUpdate: () => M.draw(ms.a, ms.f)}}, 0);',
          f'tl.fromTo(ms, {{f: 0}}, {{f: 1, duration: {zoom_dur:.3f}, ease: "power3.inOut", '
          f'onUpdate: () => M.draw(ms.a, ms.f)}}, {t_zoom:.3f});',
          'M.draw(0, 0);',
          f'tl.fromTo("#{sid}-mol", {{opacity: 0, scale: .9}}, {{opacity: 1, scale: 1, duration: .6, ease: "expo.out"}}, .05);',
          f'tl.fromTo("#{sid}-k", {{opacity: 0, y: -12}}, {{opacity: 1, y: 0, duration: .35}}, .05);',
          f'tl.fromTo("#{sid}-r", {{opacity: 0, scale: 1.8}}, {{opacity: 1, scale: 1, duration: .5, ease: "expo.out"}}, '
          f'{t_zoom + zoom_dur - .15:.3f});',
          f'tl.fromTo("#{sid}-l", {{opacity: 0, y: 24}}, {{opacity: 1, y: 0, duration: .45, ease: "expo.out"}}, '
          f'{t_zoom + zoom_dur:.3f});']
    return wrap(sid, d, layout, css, body, "\n".join(js))


def _check_compare(p):
    errs = _check(p)
    for k in ("left", "right"):
        if not isinstance(p.get(k), dict) or not p[k].get("structure"):
            errs.append(f"{k}: objeto con structure y label")
    return errs


@fmt("molecule-compare", required=("left", "right"), needs=("3dmol",), check=_check_compare,
     uses=lambda p: [("structures", p["left"]["structure"]), ("structures", p["right"]["structure"])],
     example={"kicker": "COMPARA", "left": {"structure": "aspirin", "label": "Aspirina"},
              "right": {"structure": "caffeine", "label": "Cafeína"}})
def molecule_compare(sid, d, p, layout="full"):
    """Dos estructuras lado a lado girando sincronizadas (p. ej. normal vs. mutada, fármaco vs. fármaco), cada una
    con su etiqueta y color de acento."""
    top, h, w = 420, 700, 500
    css = HEAD_CSS + f"""
    .mc-l {{ position: absolute; top: {top - 70}px; width: {w}px; text-align: center; font-family: var(--font-display);
             font-weight: 700; font-size: 46px; color: var(--text); }}
    .mc-l i {{ display: block; width: 70px; height: 6px; margin: 12px auto 0; border-radius: 3px; }}
    .mc-vs {{ position: absolute; left: 500px; top: {top + h // 2 - 40}px; width: 80px; text-align: center;
              font-family: var(--font-mono); font-weight: 600; font-size: 34px; color: var(--muted); }}
    """
    head, hjs = _head(sid, {"kicker": p.get("kicker"), "title": p.get("title")})
    parts, js = [head], [MOL_JS, 'const ms = {a: 0};']
    for k, (side, x, acc) in enumerate((("left", 30, "accent"), ("right", 550, "accent3"))):
        s = p[side]
        parts.append(f'<div class="mc-l" id="{sid}-l{k}" style="left:{x}px">{esc(s.get("label", ""))}'
                     f'<i style="background:var(--{acc})"></i></div>'
                     f'<div class="mol-box" id="{sid}-m{k}" style="left:{x}px;top:{top}px;width:{w}px;height:{h}px"></div>')
        js.append(f'const M{k} = vvMol("{sid}-m{k}", {json.dumps("structures:" + s["structure"])}, '
                  f'{_opts({**p, **{kk: vv for kk, vv in s.items() if kk in ("style", "color", "zoom")}})});')
        js.append(f'tl.fromTo("#{sid}-l{k}", {{opacity: 0, y: -16}}, {{opacity: 1, y: 0, duration: .4, ease: "expo.out"}}, {.15 + k * .12:.2f});')
        js.append(f'tl.fromTo("#{sid}-m{k}", {{opacity: 0, scale: .85}}, {{opacity: 1, scale: 1, duration: .55, ease: "expo.out"}}, {.1 + k * .12:.2f});')
    parts.append(f'<div class="mc-vs" id="{sid}-vs">vs</div>')
    js += [f'tl.fromTo(ms, {{a: 0}}, {{a: {float(p.get("degrees", 180))}, duration: {d:.3f}, ease: "none", '
           f'onUpdate: () => {{ M0.draw(ms.a, 0); M1.draw(ms.a, 0); }}}}, 0);',
           'M0.draw(0, 0); M1.draw(0, 0);',
           f'tl.fromTo("#{sid}-vs", {{opacity: 0}}, {{opacity: 1, duration: .3}}, .4);', *hjs]
    return wrap(sid, d, layout, css, "".join(parts), "\n".join(js))

