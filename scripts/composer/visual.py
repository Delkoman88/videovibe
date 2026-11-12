"""HTML de HyperFrames de una pieza: subtítulos, tarjetas, cámara, escenas e index.html (raíz)."""
import html
import json

import formats
from scripts.composer.context import H, W


def esc(s):
    return html.escape(str(s or ""), quote=True)


def css_vars(brand):
    c = brand["colors"]
    fonts = brand["fonts"]
    lines = [f"  --{k.replace('_', '-')}: {v};" for k, v in c.items()]
    lines.append(f"  --font-display: '{fonts['display']['family']}', sans-serif;")
    lines.append(f"  --font-mono: '{fonts['mono']['family']}', monospace;")
    return "\n".join(lines)



def captions_html(caps, emphasis, brand, safe, ctx):
    role_color = {r: f"var(--{brand['highlight_roles'][r]})" for r in brand["highlight_roles"]}
    words = {w["id"]: w for w in caps["words"]}
    size = brand["captions"]["size_px"]
    bottom = H - safe["text_bottom"]
    groups, tl = [], []
    for g in caps["groups"]:
        spans = []
        for wid in g["words"]:
            role = emphasis.get(wid)
            cls = f"w r-{role}" if role else "w"
            spans.append(f'<span id="{wid}" class="{cls}">{esc(words[wid]["w"])}</span>')
        dur = round(g["out"] - g["in"], 3)
        groups.append(f'    <div id="{g["id"]}" class="cap clip" data-start="{g["in"]}" data-duration="{dur}" '
                      f'data-track-index="0"><p class="line">{" ".join(spans)}</p></div>')
        sel = f'"#{g["id"]} .line"'
        tl.append(f'tl.fromTo({sel}, {{opacity: 0, y: 14, filter: "blur(6px)"}}, '
                  f'{{opacity: 1, y: 0, filter: "blur(0px)", duration: 0.14, ease: "power3.out"}}, {g["in"]});')
        for wid in g["words"]:
            t = max(words[wid]["start"], g["in"])
            tl.append(f'tl.fromTo("#{wid}", {{opacity: 0.62}}, {{opacity: 1, duration: 0.06, ease: "none"}}, {t:.3f});')
        tl.append(f'tl.to({sel}, {{opacity: 0, duration: 0.08, ease: "power2.in"}}, {max(g["out"] - 0.08, g["in"]):.3f});')
    role_css = "\n".join(
        f"    .r-{r} {{ color: {col}; text-shadow: 0 0 18px color-mix(in srgb, {col} 55%, transparent), "
        f"0 4px 18px rgba(0,0,0,.7); }}" for r, col in role_color.items())
    return f"""<template>
  <style>
    {ctx.font_faces}
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; right: 0; bottom: {bottom}px; display: flex; justify-content: center;
            overflow: visible; }}
    .line {{ margin: 0; max-width: 940px; text-align: center; font-family: var(--font-display);
             font-weight: {brand['captions']['weight']}; font-size: {size}px; line-height: 1.08; letter-spacing: -0.01em;
             color: var(--text); text-shadow: {brand['captions']['shadow']}; }}
    .w {{ display: inline-block; }}
{role_css}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}" data-layout-allow-caption-zone>
{chr(10).join(groups)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join('    ' + x for x in tl).strip()}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


OVERLAY_CSS = """
    .ov {{ position: absolute; left: 0; right: 0; top: {top}px; display: flex; justify-content: center; }}
    .panel {{ position: relative; max-width: 900px; padding: 22px 34px 24px; border-radius: 18px;
              background: rgba(7, 9, 12, 0.74); backdrop-filter: blur(18px);
              border: 1px solid var(--surface-line); text-align: center;
              box-shadow: 0 18px 50px rgba(0,0,0,.45); }}
    .kicker {{ font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .14em;
               text-transform: uppercase; color: var(--card-accent); margin-bottom: 8px; }}
    .t1 {{ font-family: var(--font-display); font-weight: 700; font-size: 54px; line-height: 1.05;
           color: var(--text); letter-spacing: -0.015em; }}
    .t2 {{ font-family: var(--font-mono); font-weight: 400; font-size: 30px; line-height: 1.3;
           color: var(--muted); margin-top: 10px; white-space: pre-line; }}
    .ov-title .t1 {{ font-size: 60px; }}
    .ov-tag .t1 {{ font-size: 46px; }}
    .corner {{ position: absolute; width: 22px; height: 22px; border-color: var(--card-accent); border-style: solid; }}
    .corner.tl {{ left: -1px; top: -1px; border-width: 2px 0 0 2px; border-top-left-radius: 18px; }}
    .corner.br {{ right: -1px; bottom: -1px; border-width: 0 2px 2px 0; border-bottom-right-radius: 18px; }}
    .role-keyword {{ --card-accent: var(--accent); }}
    .role-data {{ --card-accent: var(--accent2); }}
    .role-punchline {{ --card-accent: var(--accent3); }}
    .role-warning {{ --card-accent: var(--warn); }}
"""


def overlay_block(o, indent="    "):
    role = o.get("role", "keyword")
    kicker = f'<div class="kicker">{esc(o.get("kicker"))}</div>' if o.get("kicker") else ""
    var = ' data-var-text="cta_text"' if o["type"] == "cta" else ""
    t2 = f'<div class="t2">{esc(o.get("text2"))}</div>' if o.get("text2") else ""
    return (f'{indent}<div id="{o["id"]}" class="ov clip ov-{o["type"]} role-{role}" data-start="{o["in"]}" '
            f'data-duration="{round(o["out"] - o["in"], 3)}" data-track-index="{3 if o["type"] == "cta" else 0}">\n'
            f'{indent}  <div class="panel"><span class="corner tl"></span><span class="corner br"></span>'
            f'{kicker}<div class="t1"{var}>{esc(o.get("text"))}</div>{t2}</div>\n{indent}</div>')


def overlay_tweens(o):
    p = f'"#{o["id"]} .panel"'
    tw = [f'tl.fromTo({p}, {{opacity: 0, y: -16, filter: "blur(8px)"}}, '
          f'{{opacity: 1, y: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out"}}, {o["in"]});',
          f'tl.fromTo("#{o["id"]} .corner", {{scale: 0.4, opacity: 0}}, '
          f'{{scale: 1, opacity: 1, duration: 0.35, ease: "power3.out", stagger: 0.06}}, {o["in"] + 0.1:.3f});']
    if o["type"] != "cta":
        tw.append(f'tl.to({p}, {{opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power2.in"}}, '
                  f'{o["out"] - 0.27:.3f});')
    return tw


def overlays_html(sb, brand, safe, ctx):
    """Escena con título y tarjetas HUD. La CTA va en la raíz (su texto es variable por plataforma)."""
    blocks, tl = [], []
    for o in sb.get("overlays", []):
        if o["type"] == "cta":
            continue
        blocks.append(overlay_block(o))
        tl += overlay_tweens(o)
    css = OVERLAY_CSS.format(top=safe["text_top"] + 14).replace("{{", "{").replace("}}", "}")
    return f"""<template>
  <style>
    {ctx.font_faces}
    #root {{ position: absolute; inset: 0; }}
{css}
  </style>
  <div id="root" data-composition-id="overlays" data-width="{W}" data-height="{H}">
{chr(10).join(blocks)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join('    ' + x for x in tl)}
    window.__timelines["overlays"] = tl;
  </script>
</template>
"""


def camera_js(sb, cuts):
    cam = sb.get("camera", {})
    js = ['tl.set("#cam", {scale: 1}, 0);  // estado base estable para cualquier seek']
    for m in cam.get("moves", []):
        t, s, until = m["t"], m["scale"], m["until"]
        if m.get("type") == "creep":
            js.append(f'tl.to("#cam", {{scale: {s}, duration: {until - t:.3f}, ease: "power1.inOut"}}, {t});')
        else:
            js.append(f'tl.to("#cam", {{scale: {s}, duration: 0.32, ease: "power2.out"}}, {t});')
        if any(abs(until - c) < 0.05 for c in cuts):
            js.append(f'tl.set("#cam", {{scale: 1}}, {until});')  # en el corte: vuelve a 100 %
        elif m.get("release", True) and until < sb["_duration"]:
            js.append(f'tl.to("#cam", {{scale: 1, duration: 0.5, ease: "power2.inOut"}}, {until});')
    return "\n      ".join(js)


def scenes_markup(sb, packs=()):
    """Hosts de escenas animadas + burbujas de cara (video sin sonido, recortado en círculo)."""
    hosts, bubbles, js = [], [], []
    b = formats.BUBBLE
    for k, sc in enumerate(sb.get("scenes", [])):
        d = round(sc["out"] - sc["in"], 3)
        hosts.append(f'      <div id="{sc["id"]}" data-composition-id="{sc["id"]}" '
                     f'data-composition-src="compositions/scene-{sc["id"]}.html" data-start="{sc["in"]}" '
                     f'data-duration="{d}" data-track-index="{10 + k}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}"></div>')
        layout = sc.get("layout") or formats.default_layout(sc["format"], packs)
        if layout == "bubble":
            # la cara (≈ x 540, y 700 en la toma) centrada en la burbuja, a escala 0.5
            bubbles.append(
                f'      <div class="bubble" id="bub-{sc["id"]}" style="left:{b["x"]}px;top:{b["y"]}px;'
                f'width:{b["d"]}px;height:{b["d"]}px">\n'
                f'        <video id="bv-{sc["id"]}" class="clip bubble-video" src="assets/plate.mp4" muted playsinline '
                f'data-start="{sc["in"]}" data-duration="{d}" data-media-start="{sc["in"]}" data-track-index="{30 + k}" '
                f'style="left:{b["d"] // 2 - 270}px;top:{b["d"] // 2 - 350}px"></video>\n      </div>')
            js.append(f'tl.fromTo("#bub-{sc["id"]}", {{scale: 0}}, {{scale: 1, duration: 0.4, ease: "expo.out"}}, {sc["in"] + 0.05:.3f});')
            js.append(f'tl.to("#bub-{sc["id"]}", {{scale: 0, duration: 0.2, ease: "power2.in"}}, {sc["out"] - 0.22:.3f});')
    if js:
        js.insert(0, 'tl.set(".bubble", {scale: 0}, 0);')
    return "\n".join(hosts), "\n".join(bubbles), "\n      ".join(js)



def broll_markup(sb, media):
    """Insertos mudos sobre la placa; el audio del master conserva su tiempo."""
    clips = []
    for clip in sb.get("broll", []):
        src = media[clip["source"]]
        duration = round(clip["out"] - clip["in"], 3)
        fit = clip.get("fit", "cover")
        if fit == "region":
            r = clip["region"]
            sw, sh = src["width"], src["height"]
            scale = max(W / (r["w"] * sw), H / (r["h"] * sh))
            left = W / 2 - (r["x"] + r["w"] / 2) * sw * scale
            top = H / 2 - (r["y"] + r["h"] / 2) * sh * scale
            style = (f'left:{left:.3f}px;top:{top:.3f}px;width:{sw * scale:.3f}px;'
                     f'height:{sh * scale:.3f}px;object-fit:fill')
        else:
            style = (f'left:0;top:0;width:{W}px;height:{H}px;object-fit:{fit};'
                     f'object-position:{clip.get("focus_x", 50)}% {clip.get("focus_y", 50)}%')
        video = (f'<video id="broll-{esc(clip["id"])}" class="clip broll-video" '
                 f'src="assets/broll-{esc(src["id"])}.mp4" muted playsinline '
                 f'data-start="{clip["in"]}" data-duration="{duration}" '
                 f'data-media-start="{clip.get("source_in", 0)}" data-track-index="5" '
                 f'style="{style}"></video>')
        clips.append(f'      <div class="broll-window" data-layout-allow-overflow>{video}</div>'
                     if fit == "region" else f'      {video}')
    return "\n".join(clips)


def index_html(sb, brand, safe, dur, total, cuts, default_cta, audio_els="", ctx=None, music_srcs=None,
               media=None):
    origin = sb.get("camera", {}).get("origin", "50% 30%")
    ctas = [o for o in sb.get("overlays", []) if o["type"] == "cta"]
    cta_html = "\n".join(overlay_block({**o, "text": default_cta or o.get("text")}, "      ") for o in ctas)
    cta_tl = "\n      ".join(x for o in ctas for x in overlay_tweens(o))
    css = OVERLAY_CSS.format(top=safe["text_top"] + 14).replace("{{", "{").replace("}}", "}")
    tail = round(total - dur, 3)
    hold = (f'<img id="hold" class="clip" src="assets/last-frame.png" data-start="{dur}" data-duration="{tail}" '
            f'data-track-index="0" style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover" />'
            if tail > 0 else "")
    scene_hosts, bubbles, bubble_js = scenes_markup(sb, ctx.packs)
    variables = [{"id": "cta_text", "type": "string", "label": "Llamada a la acción", "default": default_cta or ""}]
    if music_srcs:
        variables.append({"id": "music_src", "type": "string", "label": "Pista de música",
                          "default": music_srcs["main"]})
    variables = json.dumps(variables, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="{sb.get('_lang', 'es')}" data-composition-variables='{esc(variables)}'>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      {ctx.font_faces}
      :root {{
{css_vars(brand)}
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: var(--bg); }}
      #root {{ position: absolute; inset: 0; }}
      #cam {{ position: absolute; inset: 0; transform-origin: {origin}; overflow: hidden; }}
      #plate {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: cover; }}
      .broll-video {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px;
                       background: var(--bg); }}
      .broll-window {{ position: absolute; inset: 0; overflow: hidden; }}
{css}
      .bubble {{ position: absolute; border-radius: 50%; overflow: hidden; transform-origin: 50% 50%; }}
      .bubble-video {{ position: absolute; width: 540px; height: 960px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
      <div id="cam">
        <video id="plate" class="clip" src="assets/plate.mp4" data-start="0" data-duration="{dur}"
               data-track-index="0" data-has-audio="true" data-volume="1" playsinline></video>
        {hold}
      </div>
{broll_markup(sb, media or {})}
{scene_hosts}
{bubbles}
{audio_els}
      <div id="overlays" data-composition-id="overlays" data-composition-src="compositions/overlays.html"
           data-start="0" data-duration="{total}" data-track-index="1" data-track-kind="graphics"
           data-width="{W}" data-height="{H}"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
           data-start="0" data-duration="{dur}" data-track-index="2" data-track-kind="captions"
           data-width="{W}" data-height="{H}"></div>
{cta_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {camera_js(sb, cuts)}
      {bubble_js}
      {cta_tl}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def safe_zone(preset):
    # Banda donde va todo el texto (guía de HyperFrames para 9:16: 168–1330 px), acotada por el preset.
    sz = preset.get("safe_zone_px", {})
    top = max(168, sz.get("top", 168))
    bottom_px = min(1330, H - sz.get("bottom", 590))
    return {"text_top": top, "text_bottom": bottom_px}

