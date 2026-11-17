"""Paquete «data»: gráficas con datos reales (d3, ISC) en los colores de la marca.

d3 solo calcula (escalas con números «redondos», ejes y el trazo de la curva) al construir la escena; GSAP anima
(un solo reloj, ADR 0022 y 0029). Los datos van en `params.data` o en un archivo de la pieza
(`params.file`: `data/<nombre>.csv|json`, columnas label,value o x,y). La fuente es obligatoria y se muestra en
el pie; `illustrative: true` agrega la etiqueta del idioma (no son datos reales).
Se activa con channel.json → "format_packs": [..., "data"].
"""
import csv
import io
import json
import math
from pathlib import Path

from formats.core import CTX, esc, fmt, wrap
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain

X0, X1, Y0, Y1 = 130, 960, 470, 1020   # área de la gráfica: encima de la banda de subtítulos

CSS = KINETIC_CSS + """
    .ch-h { position: absolute; left: 80px; right: 80px; top: 220px; text-align: center; }
    .ch-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
               color: var(--accent2); margin-bottom: 12px; }
    .ch-h .t { font-family: var(--font-display); font-weight: 700; font-size: 60px; line-height: 1.05; color: var(--text); }
    .ch-svg { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }
    .ch-svg .grid line { stroke: var(--surface-line); stroke-width: 2; opacity: .55; }
    .ch-svg .axis text, .ch-x { font-family: var(--font-mono); font-size: 26px; fill: var(--muted); color: var(--muted); }
    .ch-src { position: absolute; left: 80px; right: 80px; top: 1095px; text-align: center; font-family: var(--font-mono);
              font-size: 26px; color: var(--muted); }
    .ch-v { position: absolute; font-family: var(--font-display); font-weight: 700; font-size: 40px; color: var(--text);
            text-align: center; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .ch-lab { position: absolute; font-family: var(--font-display); font-weight: 600; font-size: 30px; color: var(--text);
              text-align: center; line-height: 1.1; }
"""

# Formato de números en el navegador (mismo resultado siempre): decimales fijos y separadores del parámetro.
NUM_JS = """
    const chFmt = (v, dec, comma, unit) => { let s = Math.abs(v).toFixed(dec), [i, f] = s.split(".");
      i = i.replace(/\\B(?=(\\d{3})+(?!\\d))/g, comma ? "." : ",");
      return (v < 0 ? "−" : "") + i + (f ? (comma ? "," : ".") + f : "") + unit; };"""


def rows(p, kind):
    """Datos de la escena: [{label, value}] (barras, comparación) o [{x, y}] (línea). ValueError si no se puede."""
    data = p.get("data")
    if data is None and p.get("file"):
        base = CTX.get("piece_dir")
        if not base:
            raise ValueError("file: solo funciona dentro de una pieza (usa data en la galería)")
        f = Path(base) / p["file"]
        if not f.exists():
            raise ValueError(f"file: no existe {p['file']} en la pieza")
        text = f.read_text(encoding="utf-8")
        if f.suffix.lower() == ".json":
            data = json.loads(text)
        elif f.suffix.lower() == ".csv":
            data = list(csv.DictReader(io.StringIO(text)))
        else:
            raise ValueError("file: .csv o .json")
    if not isinstance(data, list) or not data:
        raise ValueError("data: lista de puntos (o file: data/<archivo>.csv|json)")
    keys = ("label", "value") if kind == "cat" else ("x", "y")
    out = []
    for i, r in enumerate(data):
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            r = dict(zip(keys, r))
        if not isinstance(r, dict):
            raise ValueError(f"data[{i}]: objeto con {keys[0]} y {keys[1]}")
        vals = list(r.values())
        a, b = r.get(keys[0], vals[0] if vals else None), r.get(keys[1], vals[1] if len(vals) > 1 else None)
        try:
            b = float(b)
            if kind == "line":
                a = float(a)
        except (TypeError, ValueError):
            raise ValueError(f"data[{i}]: «{keys[1]}» debe ser un número") from None
        if not math.isfinite(b):
            raise ValueError(f"data[{i}]: número no válido")
        item = {keys[0]: a if kind == "line" else str(a), keys[1]: b}
        if kind == "cat" and r.get("error") not in (None, ""):
            item["error"] = float(r["error"])
        out.append(item)
    return out


def _common_check(p, kind, lo, hi):
    errs = []
    if not str(p.get("source") or "").strip():
        errs.append("source: obligatorio (de dónde salen los datos: estudio, base, año)")
    try:
        r = rows(p, kind)
        if not lo <= len(r) <= hi:
            errs.append(f"data: {lo} a {hi} puntos (tiene {len(r)})")
        if kind == "cat":
            long = [x["label"] for x in r if len(x["label"]) > 14]
            if long:
                errs.append(f"data: etiquetas de máximo 14 caracteres ({long[0]!r})")
    except ValueError as e:
        errs.append(str(e))
    dec = p.get("decimals", 0)
    if not isinstance(dec, int) or not 0 <= dec <= 3:
        errs.append("decimals: entero de 0 a 3")
    if len(str(p.get("unit", ""))) > 6:
        errs.append("unit: máximo 6 caracteres (%, mg, °C, M…)")
    return errs


def _head(sid, p):
    if not (p.get("title") or p.get("kicker")):
        return "", []
    html = (f'<div class="ch-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="t">{kinetic(p.get("title") or "")}</div></div>')
    js = [f'tl.fromTo("#{sid}-h .k", {{opacity: 0, y: -12}}, {{opacity: 1, y: 0, duration: .35}}, .1);']
    if p.get("title"):
        js.append(kinetic_in(f"#{sid}-h .t", "rise", 0.15, len(plain(p["title"]))))
    return html, js


def _foot(sid, p, at):
    ilus = (f'<div class="tag-ilus" style="left:80px;top:1140px">{esc(CTX["labels"]["illustrative"])}</div>'
            if p.get("illustrative") else "")
    return (f'<div class="ch-src" id="{sid}-src">{esc(p["source"])}</div>{ilus}',
            [f'tl.fromTo("#{sid}-src", {{opacity: 0}}, {{opacity: 1, duration: .4}}, {at:.2f});'])


def _opts(p):
    return int(p.get("decimals", 0)), "true" if p.get("decimal_comma") else "false", json.dumps(str(p.get("unit", "")))


# ---------------------------------------------------------------- chart-bars

@fmt("chart-bars", required=("source",), needs=("d3",), check=lambda p: _common_check(p, "cat", 2, 8),
     example={"kicker": "DATOS ABIERTOS", "title": "Artículos en *acceso* abierto", "unit": "%",
              "data": [{"label": "2016", "value": 32}, {"label": "2018", "value": 39}, {"label": "2020", "value": 47},
                       {"label": "2022", "value": 54}, {"label": "2024", "value": 61}],
              "highlight": "2024", "source": "Fuente: ejemplo para la galería", "illustrative": True})
def chart_bars(sid, d, p, layout="full"):
    """Barras que crecen desde cero con su valor contando encima; eje con números redondos (d3), una barra
    resaltada en acento (`highlight` = su etiqueta) y la fuente al pie. 2–8 barras."""
    data = rows(p, "cat")
    dec, comma, unit = _opts(p)
    head, hjs = _head(sid, p)
    t0, grow = 0.45, min(max(d * 0.35, 0.7), 1.4)
    foot, fjs = _foot(sid, p, t0 + grow * .8)
    js = [NUM_JS, f"""
    const D = {json.dumps(data, ensure_ascii=False)}, HL = {json.dumps(p.get("highlight"), ensure_ascii=False)};
    const svg = d3.select("#{sid}-svg");
    const x = d3.scaleBand().domain(D.map((r) => r.label)).range([{X0}, {X1}]).padding(.28);
    const lo = Math.min(0, d3.min(D, (r) => r.value)), hi = Math.max(0, d3.max(D, (r) => r.value));
    const y = d3.scaleLinear().domain([lo, hi]).nice(4).range([{Y1}, {Y0}]);
    const g = svg.append("g").attr("class", "grid");
    y.ticks(4).forEach((v) => {{ g.append("line").attr("x1", {X0}).attr("x2", {X1}).attr("y1", y(v)).attr("y2", y(v));
      svg.append("text").attr("class", "axis").attr("x", {X0 - 14}).attr("y", y(v) + 9).attr("text-anchor", "end")
        .attr("class", "ch-x").text(chFmt(v, 0, {comma}, "")); }});
    const box = document.getElementById("{sid}-st");
    D.forEach((r, i) => {{
      const hl = HL === null ? i === D.length - 1 : r.label === HL, col = hl ? "var(--accent)" : "color-mix(in srgb, var(--accent2) 55%, var(--surface-line))";
      const top = y(Math.max(r.value, 0)), h = Math.abs(y(r.value) - y(0));
      svg.append("rect").attr("id", "{sid}-b" + i).attr("x", x(r.label)).attr("y", top).attr("width", x.bandwidth())
        .attr("height", h).attr("rx", 10).attr("fill", col);
      const v = document.createElement("div"); v.className = "ch-v"; v.id = "{sid}-v" + i;
      v.style.left = (x(r.label) + x.bandwidth() / 2 - 110) + "px"; v.style.width = "220px";
      v.style.top = (r.value >= 0 ? top - 58 : top + h + 8) + "px"; if (hl) v.style.color = "var(--accent)";
      v.textContent = chFmt(r.value, {dec}, {comma}, {unit}); box.appendChild(v);
      const l = document.createElement("div"); l.className = "ch-lab"; l.id = "{sid}-l" + i;
      l.style.left = (x(r.label) + x.bandwidth() / 2 - 90) + "px"; l.style.width = "180px"; l.style.top = ({Y1} + 18) + "px";
      l.textContent = r.label; box.appendChild(l);
    }});
    D.forEach((r, i) => {{
      const t = {t0} + i * {grow / max(len(data), 1) * .5:.3f};
      tl.fromTo("#{sid}-b" + i, {{scaleY: 0, transformOrigin: r.value >= 0 ? "50% 100%" : "50% 0%"}},
        {{scaleY: 1, duration: {grow:.2f}, ease: "power3.out", immediateRender: true}}, t);
      tl.fromTo("#{sid}-l" + i, {{opacity: 0}}, {{opacity: 1, duration: .3}}, t);
      const o = {{v: 0}}, el = document.getElementById("{sid}-v" + i);
      tl.fromTo(o, {{v: 0}}, {{v: r.value, duration: {grow:.2f}, ease: "power3.out",
        onUpdate: () => {{ el.textContent = chFmt(o.v, {dec}, {comma}, {unit}); }}}}, t);
      tl.fromTo(el, {{opacity: 0}}, {{opacity: 1, duration: .25}}, t + .1);
    }});""", *hjs, *fjs]
    body = f'<svg class="ch-svg" id="{sid}-svg" viewBox="0 0 1080 1920"></svg><div id="{sid}-st"></div>' + head + foot
    return wrap(sid, d, layout, CSS, body, "\n".join(js))


# ---------------------------------------------------------------- chart-line

def _check_line(p):
    errs = _common_check(p, "line", 3, 80)
    for i, k in enumerate(p.get("points") or []):
        if not isinstance(k, dict) or not isinstance(k.get("x"), (int, float)) or not k.get("label"):
            errs.append(f"points[{i}]: {{x, label}} (un punto de la curva con su nota)")
        elif len(plain(k["label"])) > 22:
            errs.append(f"points[{i}].label: máximo 22 caracteres")
    if len(p.get("points") or []) > 3:
        errs.append("points: máximo 3 notas")
    return errs


@fmt("chart-line", required=("source",), needs=("d3", "gsap:DrawSVGPlugin"), check=_check_line,
     example={"kicker": "TENDENCIA", "title": "Genomas *secuenciados*", "unit": "",
              "data": [[2001, 1], [2005, 3], [2008, 12], [2011, 140], [2014, 1200], [2017, 6800], [2020, 21000],
                       [2023, 52000]],
              "points": [{"x": 2008, "label": "Nueva secuenciación"}, {"x": 2023, "label": "Hoy"}],
              "source": "Fuente: ejemplo para la galería", "illustrative": True})
def chart_line(sid, d, p, layout="full"):
    """Curva que se traza de izquierda a derecha con área suave debajo; hasta 3 puntos clave (`points`) se
    marcan con un círculo y una nota cuando la línea llega a ellos. Eje con números redondos (d3)."""
    data = rows(p, "line")
    dec, comma, unit = _opts(p)
    head, hjs = _head(sid, p)
    t0, draw = 0.45, min(max(d * 0.5, 1.0), 2.4)
    foot, fjs = _foot(sid, p, t0 + draw * .7)
    js = [NUM_JS, f"""
    const D = {json.dumps(data)}, K = {json.dumps(p.get("points") or [], ensure_ascii=False)};
    const svg = d3.select("#{sid}-svg");
    const x = d3.scaleLinear().domain(d3.extent(D, (r) => r.x)).range([{X0 + 20}, {X1 - 20}]);
    const y = d3.scaleLinear().domain([Math.min(0, d3.min(D, (r) => r.y)), d3.max(D, (r) => r.y)]).nice(4).range([{Y1}, {Y0}]);
    const g = svg.append("g").attr("class", "grid");
    y.ticks(4).forEach((v) => {{ g.append("line").attr("x1", {X0}).attr("x2", {X1}).attr("y1", y(v)).attr("y2", y(v));
      svg.append("text").attr("class", "ch-x").attr("x", {X0 - 14}).attr("y", y(v) + 9).attr("text-anchor", "end")
        .text(chFmt(v, 0, {comma}, "")); }});
    x.ticks(5).forEach((v) => svg.append("text").attr("class", "ch-x").attr("x", x(v)).attr("y", {Y1 + 44})
      .attr("text-anchor", "middle").text(Number.isInteger(v) ? String(v) : chFmt(v, 1, {comma}, "")));
    const defs = svg.append("defs"), gr = defs.append("linearGradient").attr("id", "{sid}-ga").attr("x1", 0).attr("x2", 0)
      .attr("y1", 0).attr("y2", 1);
    gr.append("stop").attr("offset", 0).attr("stop-color", "var(--accent)").attr("stop-opacity", .35);
    gr.append("stop").attr("offset", 1).attr("stop-color", "var(--accent)").attr("stop-opacity", 0);
    const curve = d3.curveMonotoneX;
    svg.append("path").attr("id", "{sid}-area").attr("fill", "url(#{sid}-ga)")
      .attr("d", d3.area().x((r) => x(r.x)).y0(y(Math.max(0, y.domain()[0]))).y1((r) => y(r.y)).curve(curve)(D));
    svg.append("path").attr("id", "{sid}-line").attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 9)
      .attr("stroke-linecap", "round").attr("d", d3.line().x((r) => x(r.x)).y((r) => y(r.y)).curve(curve)(D));
    tl.fromTo("#{sid}-line", {{drawSVG: "0%"}}, {{drawSVG: "100%", duration: {draw:.2f}, ease: "power1.inOut"}}, {t0});
    tl.fromTo("#{sid}-area", {{opacity: 0}}, {{opacity: 1, duration: {draw:.2f}, ease: "power1.in"}}, {t0});
    const box = document.getElementById("{sid}-st"), span = x.domain()[1] - x.domain()[0] || 1;
    K.forEach((k, i) => {{
      const near = D.reduce((a, b) => Math.abs(b.x - k.x) < Math.abs(a.x - k.x) ? b : a), px = x(near.x), py = y(near.y);
      svg.append("circle").attr("id", "{sid}-p" + i).attr("cx", px).attr("cy", py).attr("r", 16)
        .attr("fill", "var(--bg)").attr("stroke", "var(--accent2)").attr("stroke-width", 7);
      const n = document.createElement("div"); n.className = "ch-lab"; n.id = "{sid}-n" + i;
      n.style.width = "300px"; n.style.left = Math.min(Math.max(px - 150, 40), 740) + "px";
      n.style.top = (py - 112 < {Y0 - 40} ? py + 34 : py - 112) + "px";
      n.innerHTML = "<b style='color:var(--accent2)'>" + chFmt(near.y, {dec}, {comma}, {unit}) + "</b><br>";
      n.appendChild(document.createTextNode(k.label)); box.appendChild(n);
      const t = {t0} + {draw:.2f} * Math.max(0, Math.min(1, (near.x - x.domain()[0]) / span));
      tl.fromTo("#{sid}-p" + i, {{scale: 0, transformOrigin: "50% 50%"}}, {{scale: 1, duration: .35, ease: "back.out(2.5)"}}, t);
      tl.fromTo(n, {{opacity: 0, y: 12}}, {{opacity: 1, y: 0, duration: .35, ease: "expo.out"}}, t + .05);
    }});""", *hjs, *fjs]
    body = f'<svg class="ch-svg" id="{sid}-svg" viewBox="0 0 1080 1920"></svg><div id="{sid}-st"></div>' + head + foot
    return wrap(sid, d, layout, CSS, body, "\n".join(js))


# ---------------------------------------------------------------- chart-compare

@fmt("chart-compare", required=("source",), needs=("d3",), check=lambda p: _common_check(p, "cat", 2, 2),
     example={"kicker": "RESULTADO", "title": "Con el *tratamiento*", "unit": "%", "decimals": 0,
              "data": [{"label": "Control", "value": 18, "error": 4}, {"label": "Tratamiento", "value": 63, "error": 6}],
              "source": "Fuente: ejemplo para la galería", "illustrative": True})
def chart_compare(sid, d, p, layout="full"):
    """Dos grupos lado a lado (control y tratamiento, antes y después): barras con barra de error opcional
    (`error`), valores que cuentan y la diferencia resaltada con un corchete y «×N» o «+N». Exactamente 2 grupos."""
    data = rows(p, "cat")
    dec, comma, unit = _opts(p)
    head, hjs = _head(sid, p)
    t0, grow = 0.45, min(max(d * 0.35, 0.7), 1.3)
    foot, fjs = _foot(sid, p, t0 + grow + .5)
    a, b = data[0]["value"], data[1]["value"]
    if a > 0 and b / a >= 2:
        delta = f"×{b / a:.1f}".replace(".", "," if p.get("decimal_comma") else ".").replace(",0", "").replace(".0", "")
    else:
        dv = b - a
        delta = ("+" if dv >= 0 else "−") + (f"{abs(dv):.{int(p.get('decimals', 0))}f}") + str(p.get("unit", ""))
        if p.get("decimal_comma"):
            delta = delta.replace(".", ",")
    js = [NUM_JS, f"""
    const D = {json.dumps(data, ensure_ascii=False)};
    const svg = d3.select("#{sid}-svg");
    const x = d3.scaleBand().domain(D.map((r) => r.label)).range([{X0 + 80}, {X1 - 80}]).padding(.34);
    const top = d3.max(D, (r) => r.value + (r.error || 0));
    const y = d3.scaleLinear().domain([0, top * 1.25]).nice(4).range([{Y1}, {Y0 + 60}]);
    const g = svg.append("g").attr("class", "grid");
    y.ticks(4).forEach((v) => g.append("line").attr("x1", {X0}).attr("x2", {X1}).attr("y1", y(v)).attr("y2", y(v)));
    const box = document.getElementById("{sid}-st"), cols = ["color-mix(in srgb, var(--muted) 70%, var(--surface-line))", "var(--accent)"];
    D.forEach((r, i) => {{
      const cx = x(r.label) + x.bandwidth() / 2;
      svg.append("rect").attr("id", "{sid}-b" + i).attr("x", x(r.label)).attr("y", y(r.value)).attr("width", x.bandwidth())
        .attr("height", {Y1} - y(r.value)).attr("rx", 14).attr("fill", cols[i]);
      if (r.error) svg.append("path").attr("id", "{sid}-e" + i).attr("fill", "none").attr("stroke", "var(--text)")
        .attr("stroke-width", 4).attr("d", `M${{cx - 22}} ${{y(r.value + r.error)}}H${{cx + 22}}M${{cx}} ${{y(r.value + r.error)}}`
          + `V${{y(r.value - r.error)}}M${{cx - 22}} ${{y(r.value - r.error)}}H${{cx + 22}}`);
      const v = document.createElement("div"); v.className = "ch-v"; v.id = "{sid}-v" + i; v.style.fontSize = "56px";
      v.style.left = (cx - 150) + "px"; v.style.width = "300px"; v.style.top = (y(r.value + (r.error || 0)) - 80) + "px";
      if (i === 1) v.style.color = "var(--accent)"; v.textContent = chFmt(r.value, {dec}, {comma}, {unit}); box.appendChild(v);
      const l = document.createElement("div"); l.className = "ch-lab"; l.id = "{sid}-l" + i; l.style.fontSize = "36px";
      l.style.left = (cx - 170) + "px"; l.style.width = "340px"; l.style.top = ({Y1} + 18) + "px"; l.textContent = r.label;
      box.appendChild(l);
      const t = {t0} + i * .25, o = {{v: 0}};
      tl.fromTo("#{sid}-b" + i, {{scaleY: 0, transformOrigin: "50% 100%"}}, {{scaleY: 1, duration: {grow:.2f}, ease: "power3.out"}}, t);
      tl.fromTo(l, {{opacity: 0}}, {{opacity: 1, duration: .3}}, t);
      tl.fromTo(o, {{v: 0}}, {{v: r.value, duration: {grow:.2f}, ease: "power3.out",
        onUpdate: () => {{ v.textContent = chFmt(o.v, {dec}, {comma}, {unit}); }}}}, t);
      tl.fromTo(v, {{opacity: 0}}, {{opacity: 1, duration: .25}}, t + .1);
      if (r.error) tl.fromTo("#{sid}-e" + i, {{opacity: 0}}, {{opacity: .8, duration: .3}}, t + {grow:.2f});
    }});
    const yb = {Y0 - 10}, x0 = x(D[0].label) + x.bandwidth() / 2, x1 = x(D[1].label) + x.bandwidth() / 2;
    svg.append("path").attr("id", "{sid}-br").attr("fill", "none").attr("stroke", "var(--accent2)").attr("stroke-width", 6)
      .attr("stroke-linecap", "round").attr("d", `M${{x0}} ${{yb + 40}}V${{yb}}H${{x1}}V${{yb + 40}}`);
    tl.fromTo("#{sid}-br", {{opacity: 0, y: 14}}, {{opacity: 1, y: 0, duration: .4, ease: "expo.out"}}, {t0 + grow + .25:.2f});
    tl.fromTo("#{sid}-dl", {{opacity: 0, scale: .6}}, {{opacity: 1, scale: 1, duration: .45, ease: "back.out(2)"}}, {t0 + grow + .35:.2f});""",
          *hjs, *fjs]
    delta_html = (f'<div class="ch-v" id="{sid}-dl" style="left:390px;width:300px;top:{Y0 - 78}px;font-size:58px;'
                  f'color:var(--accent2)">{esc(delta)}</div>')
    body = (f'<svg class="ch-svg" id="{sid}-svg" viewBox="0 0 1080 1920"></svg><div id="{sid}-st"></div>' + delta_html
            + head + foot)
    return wrap(sid, d, layout, CSS, body, "\n".join(js))
