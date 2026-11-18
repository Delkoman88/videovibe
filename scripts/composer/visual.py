from scripts.composer.timing import caption_enter, caption_exit, CAPTION_IN, CAPTION_OUT, PANEL_IN, LIQUID_IN, LIQUID_SHAPE, OVERLAY_OUT
"""HTML de HyperFrames de una pieza: subtítulos, tarjetas, cámara, escenas e index.html (raíz)."""
import html
import json

import formats
from formats import vendors
from scripts.composer import data, transitions
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain
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



CAPTION_STYLES = ("classic", "neon")
OVERLAY_STYLES = ("panel", "liquid")


def zone_css(zones):
    """CSS de `caption_zones`; vacío si la pieza no las usa (el HTML queda igual que sin la función)."""
    if not zones:
        return ""
    return ("\n    .zone-upper-left { bottom: 920px; justify-content: flex-start; padding-left: 72px; padding-right: 220px; }"
            "\n    .zone-upper-left .line { max-width: 760px; text-align: left; }"
            "\n    .zone-upper-center { bottom: 920px; }")


def captions_html(caps, emphasis, brand, safe, ctx, zones=()):
    """Subtítulos palabra por palabra. Estilo por canal: brand.json → captions.style
    (`classic`, por defecto; `neon`: palabra activa con color, escala y separación RGB)."""
    style = brand["captions"].get("style", "classic")
    fn = _captions_neon if style == "neon" else _captions_classic
    return fn(caps, emphasis, brand, safe, ctx, zones)


def _captions_classic(caps, emphasis, brand, safe, ctx, zones=()):
    role_color = {r: f"var(--{brand['highlight_roles'][r]})" for r in brand["highlight_roles"]}
    words = {w["id"]: w for w in caps["words"]}
    size = brand["captions"]["size_px"]
    bottom = H - safe["text_bottom"]
    groups, tl = [], []
    for g in caps["groups"]:
        position = next((z["position"] for z in zones
                         if g["out"] > z["in"] and g["in"] < z["out"]), None)
        zone_class = f" zone-{position}" if position else ""
        spans = []
        for wid in g["words"]:
            role = emphasis.get(wid)
            cls = f"w r-{role}" if role else "w"
            spans.append(f'<span id="{wid}" class="{cls}">{esc(words[wid]["w"])}</span>')
        dur = round(g["out"] - g["in"], 3)
        groups.append(f'    <div id="{g["id"]}" class="cap clip{zone_class}" data-start="{g["in"]}" data-duration="{dur}" '
                      f'data-track-index="0"><p class="line">{" ".join(spans)}</p></div>')
        sel = f'"#{g["id"]} .line"'
        tl.append(f'tl.fromTo({sel}, {{opacity: 0, y: 14, filter: "blur(6px)"}}, '
                  f'{{opacity: 1, y: 0, filter: "blur(0px)", duration: {caption_enter(dur)}, ease: "power3.out"}}, {g["in"]});')
        for wid in g["words"]:
            t = max(words[wid]["start"], g["in"])
            tl.append(f'tl.fromTo("#{wid}", {{opacity: 0.62}}, {{opacity: 1, duration: 0.06, ease: "none"}}, {t:.3f});')
        tl.append(f'tl.to({sel}, {{opacity: 0, duration: {caption_exit(dur)}, ease: "power2.in"}}, {max(g["out"] - caption_exit(dur), g["in"]):.3f});')
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
{role_css}{zone_css(zones)}
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


def _captions_neon(caps, emphasis, brand, safe, ctx, zones=()):
    colors = brand["colors"]
    role_color = {r: colors[brand["highlight_roles"][r]] for r in brand["highlight_roles"]}
    text_color = colors["text"]
    default_active = colors["accent"]
    warn = colors["warn"]
    words = {w["id"]: w for w in caps["words"]}
    size = brand["captions"]["size_px"]
    bottom = H - safe["text_bottom"]
    groups, tl = [], []
    for g in caps["groups"]:
        position = next((z["position"] for z in zones
                         if g["out"] > z["in"] and g["in"] < z["out"]), None)
        zone_class = f" zone-{position}" if position else ""
        spans = []
        for wid in g["words"]:
            role = emphasis.get(wid)
            active_color = role_color.get(role, default_active)
            cls = f"w r-{role}" if role else "w"
            spans.append(f'<span id="{wid}" class="{cls}">{esc(words[wid]["w"])}</span>')
        dur = round(g["out"] - g["in"], 3)
        line_in_duration = caption_enter(dur, 'neon')
        groups.append(f'    <div id="{g["id"]}" class="cap clip{zone_class}" data-start="{g["in"]}" data-duration="{dur}" '
                      f'data-track-index="0"><p class="line">{" ".join(spans)}</p></div>')
        sel = f'"#{g["id"]} .line"'
        tl.append(f'tl.fromTo({sel}, {{opacity: 0, y: 14, filter: "blur(6px)"}}, '
                  f'{{opacity: 1, y: 0, filter: "blur(0px)", duration: {line_in_duration:.3f}, '
                  f'overwrite: "auto", ease: "power3.out"}}, {g["in"]});')
        for wid in g["words"]:
            t = max(words[wid]["start"], g["in"])
            end = min(words[wid]["end"], g["out"])
            attack = min(0.06, max(0.005, end - t))
            tl.append(f'tl.fromTo("#{wid}", {{opacity: 1, scale: 1, y: 0, color: "{text_color}"}}, '
                      f'{{opacity: 1, scale: 1.08, y: -3, color: "{active_color}", duration: {attack:.3f}, '
                      f'textShadow: "-3px 0 {warn}, 3px 0 {default_active}, 0 0 24px {active_color}, '
                      f'0 5px 18px rgba(0,0,0,.85)", overwrite: "auto", ease: "steps(2)"}}, {t:.3f});')
            tl.append(f'tl.to("#{wid}", {{opacity: 1, scale: 1, y: 0, color: "{text_color}", duration: 0.07, '
                      f'textShadow: "0 4px 18px rgba(0,0,0,.78)", overwrite: "auto", '
                      f'ease: "steps(2)"}}, {end:.3f});')
        tl.append(f'tl.to({sel}, {{opacity: 0, duration: {caption_exit(dur)}, overwrite: "auto", ease: "power2.in"}}, '
                  f'{max(g["out"] - caption_exit(dur), g["in"]):.3f});')
    return f"""<template>
  <style>
    {ctx.font_faces}
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; right: 0; bottom: {bottom}px; display: flex; justify-content: center;
            overflow: visible; }}
    .zone-upper-left {{ bottom: 920px; justify-content: flex-start; padding-left: 72px; padding-right: 220px; }}
    .zone-upper-left .line {{ max-width: 760px; text-align: left; }}
    .zone-upper-center {{ bottom: 920px; }}
    .line {{ margin: 0; max-width: 940px; text-align: center; font-family: var(--font-display);
             font-weight: {brand['captions']['weight']}; font-size: {size}px; line-height: 1.04; letter-spacing: .015em;
             color: var(--text); text-shadow: {brand['captions']['shadow']};
             -webkit-font-smoothing: none; font-smooth: never; }}
    .w {{ display: inline-block; transform-origin: 50% 75%;
          -webkit-text-stroke: 1px rgba(0,0,0,.48); }}
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


OVERLAY_CSS_LIQUID = """
    .ov {{ position: absolute; left: 0; right: 0; top: {top}px; display: flex; justify-content: center; }}
    .panel {{ position:relative;width:920px;min-height:194px;filter:drop-shadow(0 22px 36px rgba(0,0,0,.58)); }}
    .liquid-main {{ position:absolute;left:112px;right:88px;top:6px;min-height:178px;padding:22px 48px 42px 70px;
                    background:radial-gradient(circle at 22% 18%,color-mix(in srgb,var(--card-accent) 18%,transparent),
                    transparent 38%),linear-gradient(145deg,rgba(16,22,34,.94),rgba(2,4,9,.92));
                    border:2px solid color-mix(in srgb,var(--card-accent) 65%,transparent);
                    border-radius:42% 58% 48% 52% / 58% 43% 57% 42%;overflow:hidden;
                    box-shadow:inset 0 0 46px rgba(0,0,0,.72),0 0 24px color-mix(in srgb,var(--card-accent) 24%,transparent); }}
    .liquid-main::before {{ content:"";position:absolute;width:260px;height:130px;right:-70px;top:-52px;
                           border-radius:50%;background:color-mix(in srgb,var(--accent3) 15%,transparent);
                           filter:blur(10px); }}
    .liquid-main::after {{ content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,
                          transparent 0 8px,rgba(46,230,240,.03) 9px);pointer-events:none; }}
    .orbit {{ position:absolute;left:18px;top:22px;width:156px;height:156px;border-radius:50%;z-index:3;
              border:3px solid var(--card-accent);box-shadow:0 0 18px var(--card-accent),inset 0 0 30px rgba(0,0,0,.8);
              background:radial-gradient(circle,rgba(3,6,12,.96) 0 22%,transparent 24% 43%,rgba(3,6,12,.88) 45% 100%); }}
    .orbit i {{ position:absolute;border-radius:50%;border:2px solid color-mix(in srgb,var(--card-accent) 70%,transparent); }}
    .orbit i:nth-child(1) {{ inset:18px; }} .orbit i:nth-child(2) {{ inset:40px;border-color:var(--accent2); }}
    .orbit i:nth-child(3) {{ left:50%;top:4px;width:5px;height:28px;border:0;background:var(--text); }}
    .liquid-meter {{ position:absolute;right:12px;top:30px;width:132px;height:132px;border-radius:48% 52% 58% 42% / 44% 56% 44% 56%;
                     background:conic-gradient(from 215deg,var(--accent2) 0 38%,var(--warn) 39% 49%,#151a24 50% 100%);
                     padding:15px;z-index:3;box-shadow:0 0 20px color-mix(in srgb,var(--card-accent) 30%,transparent); }}
    .liquid-meter::after {{ content:"";display:block;width:100%;height:100%;border-radius:50%;background:#070a11;
                           box-shadow:inset 0 0 18px rgba(0,0,0,.85); }}
    .liquid-meter i {{ position:absolute;left:62px;top:30px;width:5px;height:48px;background:var(--text);
                       transform-origin:50% 100%;transform:rotate(32deg);z-index:2;box-shadow:0 0 8px var(--card-accent); }}
    .liquid-cable {{ position:absolute;inset:-8px 0 0 0;width:920px;height:205px;overflow:visible;z-index:1; }}
    .liquid-cable path {{ fill:none;stroke:var(--card-accent);stroke-width:5;stroke-linecap:round;
                          filter:drop-shadow(0 0 7px var(--card-accent));stroke-dasharray:18 12; }}
    .droplet {{ position:absolute;border-radius:50%;background:var(--card-accent);box-shadow:0 0 14px var(--card-accent);z-index:4; }}
    .d1 {{ left:184px;top:2px;width:18px;height:18px; }} .d2 {{ right:168px;bottom:0;width:13px;height:13px; }}
    .topline {{ position:relative;display:flex;align-items:center;justify-content:space-between;gap:20px; }}
    .kicker {{ font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .14em;
               text-transform: uppercase; color: var(--card-accent); }}
    .bpm {{ font:600 19px var(--font-mono);color:var(--accent2);letter-spacing:.08em;white-space:nowrap; }}
    .t1 {{ position:relative;font-family: var(--font-display); font-weight: 700; font-size: 54px; line-height: 1.0;
           color: var(--text); letter-spacing: .01em;margin-top:7px;text-shadow:-2px 0 var(--warn),2px 0 var(--accent); }}
    .t2 {{ font-family: var(--font-mono); font-weight: 400; font-size: 30px; line-height: 1.3;
           color: var(--muted); margin-top: 6px; white-space: pre-line; }}
    .mini-wave {{ position:absolute;left:72px;right:74px;bottom:16px;height:24px;display:flex;align-items:center;gap:5px; }}
    .mini-wave i {{ flex:1;height:var(--h);background:var(--card-accent);box-shadow:0 0 6px var(--card-accent);
                    transform-origin:50% 50%;opacity:.8; }}
    .ov-title .t1 {{ font-size: 58px; }}
    .ov-tag .t1 {{ font-size: 46px; }}
    .ov-cta .t1 {{ font-size:43px;line-height:1.08; }}
    .role-keyword {{ --card-accent: var(--accent); }}
    .role-data {{ --card-accent: var(--accent2); }}
    .role-punchline {{ --card-accent: var(--accent3); }}
    .role-warning {{ --card-accent: var(--warn); }}
"""


def _overlay_block_panel(o, indent="    "):
    role = o.get("role", "keyword")
    kicker = f'<div class="kicker">{esc(o.get("kicker"))}</div>' if o.get("kicker") else ""
    var = ' data-var-text="cta_text"' if o["type"] == "cta" else ""
    t2 = f'<div class="t2">{esc(o.get("text2"))}</div>' if o.get("text2") else ""
    return (f'{indent}<div id="{o["id"]}" class="ov clip ov-{o["type"]} role-{role}" data-start="{o["in"]}" '
            f'data-duration="{round(o["out"] - o["in"], 3)}" data-track-index="{3 if o["type"] == "cta" else 0}">\n'
            f'{indent}  <div class="panel"><span class="corner tl"></span><span class="corner br"></span>'
            f'{kicker}<div class="t1"{var}>{_t1(o)}</div>{t2}</div>\n{indent}</div>')


def _overlay_block_liquid(o, indent="    "):
    role = o.get("role", "keyword")
    kicker = f'<div class="kicker">{esc(o.get("kicker"))}</div>' if o.get("kicker") else ""
    var = ' data-var-text="cta_text"' if o["type"] == "cta" else ""
    t2 = f'<div class="t2">{esc(o.get("text2"))}</div>' if o.get("text2") else ""
    wave = "".join(f'<i style="--h:{8 + ((i * 13) % 15)}px"></i>' for i in range(22))
    return (f'{indent}<div id="{o["id"]}" class="ov clip ov-{o["type"]} role-{role}" data-start="{o["in"]}" '
            f'data-duration="{round(o["out"] - o["in"], 3)}" data-track-index="{3 if o["type"] == "cta" else 0}">\n'
            f'{indent}  <div class="panel"><svg class="liquid-cable" viewBox="0 0 920 205"><path d="M20 162 C120 18 238 202 358 72 S640 16 900 132"/></svg>'
            f'<div class="orbit"><i></i><i></i><i></i></div><div class="liquid-main">'
            f'<div class="topline">{kicker}<span class="bpm" data-layout-ignore>LIVE SIGNAL</span></div>'
            f'<div class="t1"{var}>{_t1(o)}</div>{t2}<div class="mini-wave">{wave}</div></div>'
            f'<div class="liquid-meter"><i></i></div><i class="droplet d1"></i><i class="droplet d2"></i></div>\n{indent}</div>')


def _overlay_tweens_panel(o):
    p = f'"#{o["id"]} .panel"'
    tw = [f'tl.fromTo({p}, {{opacity: 0, y: -16, filter: "blur(8px)"}}, '
          f'{{opacity: 1, y: 0, filter: "blur(0px)", duration: {PANEL_IN}, ease: "expo.out"}}, {o["in"]});',
          f'tl.fromTo("#{o["id"]} .corner", {{scale: 0.4, opacity: 0}}, '
          f'{{scale: 1, opacity: 1, duration: 0.35, ease: "power3.out", stagger: 0.06}}, {o["in"] + 0.1:.3f});']
    if o["type"] != "cta":
        tw.append(f'tl.to({p}, {{opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power2.in"}}, '
                  f'{o["out"] - OVERLAY_OUT:.3f});')
    return tw


def _overlay_tweens_liquid(o):
    p = f'"#{o["id"]} .panel"'
    tw = [f'tl.fromTo({p}, {{opacity: 0, scale: .82, filter: "blur(10px)"}}, '
          f'{{opacity: 1, scale: 1, filter: "blur(0px)", duration: {LIQUID_IN}, ease: "expo.out"}}, {o["in"]});',
          f'tl.fromTo("#{o["id"]} .orbit", {{rotation: -70, scale: .55}}, '
          f'{{rotation: 86, scale: 1, duration: .82, ease: "expo.out"}}, {o["in"] + .02:.3f});',
          f'tl.fromTo("#{o["id"]} .liquid-main", {{borderRadius: "68% 32% 62% 38% / 38% 64% 36% 62%"}}, '
          f'{{borderRadius: "42% 58% 48% 52% / 58% 43% 57% 42%", duration: {str(LIQUID_SHAPE).lstrip(chr(48))}, ease: "sine.inOut"}}, {o["in"]:.3f});',
          f'tl.fromTo("#{o["id"]} .mini-wave i", {{scaleY: .15, opacity: .2}}, '
          f'{{scaleY: 1, opacity: .85, duration: .22, ease: "steps(3)", stagger: .018}}, {o["in"] + .12:.3f});',
          f'tl.fromTo("#{o["id"]} .liquid-cable path", {{strokeDashoffset: 160}}, '
          f'{{strokeDashoffset: 0, duration: .9, ease: "power2.out"}}, {o["in"] + .06:.3f});',
          f'tl.fromTo("#{o["id"]} .droplet", {{scale:0,opacity:0}}, '
          f'{{scale:1,opacity:1,duration:.28,ease:"back.out(2)",stagger:.12}}, {o["in"] + .24:.3f});',
          f'tl.fromTo("#{o["id"]} .liquid-meter i", {{rotation:-42}}, '
          f'{{rotation:32,duration:.68,ease:"elastic.out(1,.35)"}}, {o["in"] + .1:.3f});']
    if o["type"] != "cta":
        tw.append(f'tl.to({p}, {{opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power2.in"}}, '
                  f'{o["out"] - OVERLAY_OUT:.3f});')
    return tw


def _t1(o):
    """Texto principal de una tarjeta: tal cual, o partido en letras si pide `text_fx` (no en la CTA)."""
    if o.get("text_fx") and o["type"] != "cta":
        return kinetic(o.get("text"))
    return esc(o.get("text"))


def _text_fx_tweens(o):
    if not o.get("text_fx") or o["type"] == "cta":
        return []
    return [kinetic_in(f'#{o["id"]} .t1', o["text_fx"], o["in"] + 0.12, len(plain(o.get("text", ""))))]


def overlay_style(brand):
    """Estilo de tarjetas por canal: brand.json → overlays.style (`panel`, por defecto; `liquid`)."""
    return (brand.get("overlays") or {}).get("style", "panel")


def overlay_css(brand, top):
    css = OVERLAY_CSS_LIQUID if overlay_style(brand) == "liquid" else OVERLAY_CSS
    return css.format(top=top).replace("{{", "{").replace("}}", "}")


def overlay_block(o, indent="    ", brand=None):
    fn = _overlay_block_liquid if brand and overlay_style(brand) == "liquid" else _overlay_block_panel
    return fn(o, indent)


def overlay_tweens(o, brand=None):
    fn = _overlay_tweens_liquid if brand and overlay_style(brand) == "liquid" else _overlay_tweens_panel
    return fn(o) + _text_fx_tweens(o)


def overlays_html(sb, brand, safe, ctx):
    """Escena con título y tarjetas HUD. La CTA va en la raíz (su texto es variable por plataforma)."""
    blocks, tl = [], []
    for o in sb.get("overlays", []):
        if o["type"] == "cta":
            continue
        blocks.append(overlay_block(o, brand=brand))
        tl += overlay_tweens(o, brand)
    css = overlay_css(brand, safe["text_top"] + 14)
    if any(o.get("text_fx") and o["type"] != "cta" for o in sb.get("overlays", [])):
        css += KINETIC_CSS
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
               media=None, fx=("", "", ""), beat=("", "", "")):
    """`fx` = (html dentro de #cam, js, css) de scripts/composer/fx.py; `beat` = (abrir, cerrar, js) de
    scripts/composer/beat.py. Vacíos si la pieza no los usa: el HTML es el de siempre."""
    fx_js = ("\n      " + fx[1]) if fx[1] else ""
    fx_js += ("\n      " + beat[2]) if beat[2] else ""
    origin = sb.get("camera", {}).get("origin", "50% 30%")
    ctas = [o for o in sb.get("overlays", []) if o["type"] == "cta"]
    cta_html = "\n".join(overlay_block({**o, "text": default_cta or o.get("text")}, "      ", brand) for o in ctas)
    cta_tl = "\n      ".join(x for o in ctas for x in overlay_tweens(o, brand))
    css = overlay_css(brand, safe["text_top"] + 14)
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
{vendors.head(formats.needs(sb))}{data.head(sb)}    <style>
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
      .bubble-video {{ position: absolute; width: 540px; height: 960px; object-fit: cover; }}{fx[2]}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
      {beat[0]}<div id="cam">
        <video id="plate" class="clip" src="assets/plate.mp4" data-start="0" data-duration="{dur}"
               data-track-index="0" data-has-audio="true" data-volume="1" playsinline></video>
        {hold}{fx[0]}
      </div>{beat[1]}
{broll_markup(sb, media or {})}
{scene_hosts}
{bubbles}
{transitions.host(sb, total)}{audio_els}
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
      {camera_js(sb, cuts)}{fx_js}
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

