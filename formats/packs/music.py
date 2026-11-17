"""Paquete «music»: motion graphics para DJs y productores de música electrónica.

Osciloscopios, señal, patch bays y controles de mezcla con una estética cyberpunk sobria.
Se activa en un canal con channel.json → "format_packs": ["music"].
"""
from formats.motion import factor
import json
import math

from formats.core import CTX, esc, fmt, wrap


@fmt("signal-spell", layout="over", required=("text",),
     example={"text": "MÚSICA = MAGIA", "kicker": "LIVE // SIGNAL", "y": 310})
def signal_spell(sid, d, p, layout="over"):
    """La frase emerge de una señal de osciloscopio con anillos de deck y glitch controlado."""
    text = p["text"]
    y = p.get("y", 310)
    points = []
    for x in range(0, 881, 10):
        env = math.sin(math.pi * x / 880) ** 0.7
        wave = math.sin(x * 0.082) * 38 + math.sin(x * 0.23) * 13
        points.append(f"{x},{82 + env * wave:.1f}")
    letters = "".join(
        f'<span id="{sid}-g{i}">{"&nbsp;" if ch == " " else esc(ch)}</span>'
        for i, ch in enumerate(text)
    )
    ticks = "".join(
        f'<i style="transform:rotate({i * 15}deg) translateY(-112px)"></i>' for i in range(24)
    )
    pixels = "".join(
        f'<b id="{sid}-px{i}" style="left:{36 + (i * 73) % 940}px;top:{22 + (i * 47) % 250}px;'
        f'background:var(--{["accent", "accent2", "accent3", "warn"][i % 4]})"></b>'
        for i in range(28)
    )
    css = f"""
    .sig-panel {{ position:absolute; left:46px; right:46px; top:{y - 82}px; height:300px;
      overflow:hidden; background:linear-gradient(110deg,rgba(5,7,12,.94),rgba(12,8,25,.86));
      border:1px solid color-mix(in srgb,var(--accent) 65%,transparent);
      clip-path:polygon(0 18px,18px 0,100% 0,100% calc(100% - 26px),calc(100% - 26px) 100%,0 100%);
      box-shadow:0 0 34px color-mix(in srgb,var(--accent3) 28%,transparent),inset 0 0 60px rgba(0,0,0,.55); }}
    .sig-panel:after {{ content:"";position:absolute;inset:0;pointer-events:none;opacity:.18;
      background:repeating-linear-gradient(0deg,transparent 0 5px,var(--accent) 6px,transparent 7px); }}
    .sig-k {{ position:absolute;left:76px;top:{y - 48}px;font:600 25px var(--font-mono);letter-spacing:.18em;
      color:var(--accent2);text-transform:uppercase; }}
    .sig-title {{ position:absolute;left:112px;right:70px;top:{y + 72}px;font:700 66px var(--font-display);
      letter-spacing:.025em;color:var(--text);text-shadow:-3px 0 var(--accent3),3px 0 var(--accent),0 0 22px rgba(255,255,255,.24); }}
    .sig-title span {{ display:inline-block; }}
    svg.scope {{ position:absolute;left:112px;top:{y - 3}px;filter:drop-shadow(0 0 9px var(--accent)); }}
    .deck {{ position:absolute;left:58px;top:{y + 81}px;width:88px;height:88px;border:3px solid var(--accent3);
      border-radius:50%;box-shadow:0 0 18px color-mix(in srgb,var(--accent3) 55%,transparent); }}
    .deck:before {{ content:"";position:absolute;inset:25px;border:3px solid var(--accent);border-radius:50%; }}
    .deck i {{ position:absolute;left:41px;top:41px;width:5px;height:10px;background:var(--accent2);transform-origin:2px 2px; }}
    .sig-code {{ position:absolute;right:70px;top:{y - 47}px;font:400 22px var(--font-mono);color:var(--muted); }}
    .pixels {{position:absolute;left:46px;right:46px;top:{y - 82}px;height:300px;overflow:hidden;pointer-events:none}}
    .pixels b {{position:absolute;width:9px;height:9px;display:block;box-shadow:0 0 9px currentColor;opacity:0}}
    """
    body = (
        f'<div class="sig-panel" id="{sid}-panel"></div>'
        f'<div class="sig-k" id="{sid}-k">{esc(p.get("kicker", CTX["channel"] + " // AUDIO SIGNAL"))}</div>'
        f'<div class="sig-code" id="{sid}-code">48kHz / LIVE</div>'
        f'<svg class="scope" width="880" height="164" viewBox="0 0 880 164">'
        f'<polyline id="{sid}-wave" points="{" ".join(points)}" fill="none" stroke="var(--accent)" '
        f'stroke-width="5" stroke-linejoin="round" stroke-dasharray="1700" stroke-dashoffset="1700"/></svg>'
        f'<div class="deck" id="{sid}-deck">{ticks}</div>'
        f'<div class="sig-title" id="{sid}-title">{letters}</div><div class="pixels">{pixels}</div>'
    )
    js = [
        f'tl.fromTo("#{sid}-panel", {{scaleX:.15,opacity:0}}, {{scaleX:1,opacity:1,duration:.34,ease:"expo.out"}}, .02);',
        f'tl.to("#{sid}-wave", {{attr:{{"stroke-dashoffset":0}},duration:.72,ease:"power2.out"}}, .12);',
        f'tl.fromTo("#{sid}-deck", {{rotation:-90,scale:.4,opacity:0}}, {{rotation:0,scale:1,opacity:1,duration:.5,ease:"expo.out"}}, .18);',
        f'tl.to("#{sid}-deck", {{rotation:70,duration:{max(d - .4, .3):.3f},ease:"none"}}, .4);',
        f'tl.fromTo("#{sid}-k,#{sid}-code", {{opacity:0,y:-8}}, {{opacity:1,y:0,duration:.22}}, .2);',
    ]
    for i in range(len(text)):
        js.append(
            f'tl.fromTo("#{sid}-g{i}", {{opacity:0,x:{-18 if i % 2 else 18},y:{-7 if i % 3 else 8},'
            f'filter:"blur(7px)"}}, {{opacity:1,x:0,y:0,filter:"blur(0px)",duration:.22,ease:"steps(3)"}}, '
            f'{.42 + i * .025:.3f});'
        )
    for i in range(28):
        js.append(
            f'tl.fromTo("#{sid}-px{i}", {{opacity:0,scale:0}}, {{opacity:{.3 + (i % 4) * .12:.2f},scale:1,'
            f'duration:.06,ease:"steps(1)"}}, {0.08 + (i % 9) * .045:.3f});'
        )
        js.append(
            f'tl.to("#{sid}-px{i}", {{x:{18 if i % 2 else -18},opacity:0,duration:.1,ease:"steps(2)"}}, '
            f'{0.72 + (i % 7) * .055:.3f});'
        )
    js.append(f'tl.to("#{sid}-title", {{x:5,duration:.035,yoyo:true,repeat:3,ease:"none"}}, 1.02);')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("patchbay-dream", required=("inputs", "output"),
     example={"kicker": "ROUTE THE SIGNAL", "inputs": ["RECURSOS", "EXPERIENCIA", "DECISIÓN"],
              "output": "MASTER", "output_at": 2.0})
def patchbay_dream(sid, d, p, layout="full"):
    """Recursos entran como canales de una mezcladora y se rutean por cables luminosos hacia la salida `output` (el nombre del artista o la idea final)."""
    inputs = p["inputs"][:3]
    xs = [180, 540, 900][:len(inputs)]
    paths, strips, js = [], [], []
    for i, (x, label) in enumerate(zip(xs, inputs)):
        path = f"M{x} 620 C{x} 760 {540 + (i - 1) * 120} 810 540 980"
        paths.append(
            f'<path id="{sid}-c{i}" d="{path}" fill="none" stroke="var(--{["accent", "accent2", "accent3"][i % 3]})" '
            f'stroke-width="6" stroke-linecap="round" stroke-dasharray="900" stroke-dashoffset="900"/>'
        )
        strips.append(
            f'<div class="strip" id="{sid}-s{i}" style="left:{x - 112}px">'
            f'<div class="meter"><i style="height:{58 + i * 13}%"></i></div><div class="knob"><b></b></div>'
            f'<div class="fader"><i style="top:{30 + i * 24}px"></i></div><span>{esc(label)}</span></div>'
        )
        js.extend([
            f'tl.fromTo("#{sid}-s{i}", {{opacity:0,y:35}}, {{opacity:1,y:0,duration:.34,ease:"expo.out"}}, {0.12 + i * .1:.2f});',
            f'tl.to("#{sid}-c{i}", {{attr:{{"stroke-dashoffset":0}},duration:.48,ease:"power2.out"}}, {0.55 + i * .12:.2f});',
            f'tl.fromTo("#{sid}-s{i} .meter i", {{scaleY:.08}}, {{scaleY:1,duration:{max(d - .4, .4):.2f},ease:"rough({{strength:.5,points:12,template:none.out,randomize:false}})"}}, .2);',
        ])
    pixel_bus = "".join(
        f'<i id="{sid}-bp{i}" style="left:{84 + (i * 89) % 900}px;top:{820 + (i % 4) * 26}px;'
        f'background:var(--{["accent", "accent2", "accent3"][i % 3]})"></i>'
        for i in range(22)
    )
    out_at = p.get("output_at", 2.0)
    css = """
    .music-grid { position:absolute;inset:0;opacity:.15;background-image:
      linear-gradient(var(--accent) 1px,transparent 1px),linear-gradient(90deg,var(--accent3) 1px,transparent 1px);
      background-size:54px 54px;transform:perspective(700px) rotateX(58deg) scale(1.5);transform-origin:50% 100%; }
    .scanlines {position:absolute;inset:0;opacity:.09;background:repeating-linear-gradient(0deg,transparent 0 6px,var(--text) 7px,transparent 8px)}
    .pb-k {position:absolute;left:66px;top:252px;font:600 28px var(--font-mono);letter-spacing:.18em;color:var(--accent2)}
    .pb-head {position:absolute;left:66px;top:310px;font:700 66px var(--font-display);color:var(--text)}
    .pb-head em {font-style:normal;color:var(--accent3);text-shadow:0 0 18px var(--accent3)}
    svg.cables {position:absolute;inset:0;filter:drop-shadow(0 0 8px rgba(77,163,255,.65))}
    .strip {position:absolute;top:470px;width:224px;height:300px;background:rgba(10,12,18,.9);border:1px solid var(--surface-line);
      clip-path:polygon(0 14px,14px 0,100% 0,100% calc(100% - 18px),calc(100% - 18px) 100%,0 100%)}
    .strip span {position:absolute;left:12px;right:12px;bottom:16px;text-align:center;font:600 24px var(--font-mono);color:var(--text)}
    .meter {position:absolute;left:28px;top:36px;width:28px;height:176px;border:1px solid var(--surface-line);display:flex;align-items:flex-end;padding:3px}
    .meter i {display:block;width:100%;background:linear-gradient(var(--warn),var(--accent2),var(--accent));transform-origin:50% 100%}
    .knob {position:absolute;left:90px;top:42px;width:70px;height:70px;border:5px solid var(--accent3);border-radius:50%;box-shadow:0 0 14px var(--accent3)}
    .knob b {position:absolute;left:30px;top:4px;width:5px;height:24px;background:var(--text)}
    .fader {position:absolute;left:112px;top:130px;width:8px;height:90px;background:var(--surface-line)}
    .fader i {position:absolute;left:-17px;width:42px;height:14px;background:var(--accent);box-shadow:0 0 12px var(--accent)}
    .core-out {position:absolute;left:180px;top:944px;width:720px;height:166px;border:2px solid var(--accent3);
      background:linear-gradient(100deg,rgba(10,12,18,.98),rgba(36,12,54,.94));display:flex;align-items:center;justify-content:center;
      font:700 90px var(--font-display);letter-spacing:.16em;color:var(--text);text-shadow:-4px 0 var(--accent3),4px 0 var(--accent);
      box-shadow:0 0 55px color-mix(in srgb,var(--accent3) 45%,transparent)}
    .out-code {position:absolute;left:202px;top:1128px;font:400 25px var(--font-mono);letter-spacing:.16em;color:var(--accent2)}
    .pixel-bus i {position:absolute;width:12px;height:12px;opacity:0;box-shadow:0 0 12px currentColor}
    """
    body = (
        '<div class="music-grid"></div><div class="scanlines"></div>'
        f'<div class="pb-k" id="{sid}-k">{esc(p.get("kicker", "PATCH THE DREAM"))}</div>'
        f'<div class="pb-head" id="{sid}-h">TODO ENTRA A LA <em>MEZCLA</em></div>'
        f'<svg class="cables" width="1080" height="1920">{"".join(paths)}</svg>{"".join(strips)}'
        f'<div class="pixel-bus">{pixel_bus}</div><div class="core-out" id="{sid}-out">{esc(p["output"])}</div>'
        f'<div class="out-code" id="{sid}-code">MASTER OUT // DREAM BUS</div>'
    )
    js.insert(0, f'tl.fromTo("#{sid}-k,#{sid}-h", {{opacity:0,x:-24}}, {{opacity:1,x:0,duration:.34,ease:"expo.out"}}, .04);')
    js.extend([
        f'tl.fromTo("#{sid}-out", {{opacity:0,scaleX:.25,filter:"blur(12px)"}}, '
        f'{{opacity:1,scaleX:1,filter:"blur(0px)",duration:.5,ease:"expo.out"}}, {out_at:.2f});',
        f'tl.fromTo("#{sid}-code", {{opacity:0}}, {{opacity:1,duration:.2}}, {out_at + .25:.2f});',
        f'tl.to("#{sid}-out", {{boxShadow:"0 0 90px var(--accent3)",duration:.16,yoyo:true,repeat:3}}, {out_at + .28:.2f});',
    ])
    for i in range(22):
        js.append(
            f'tl.fromTo("#{sid}-bp{i}", {{opacity:0,scale:0,x:-24}}, {{opacity:.85,scale:1,x:0,duration:.08,'
            f'ease:"steps(2)"}}, {0.82 + (i % 8) * .055:.3f});'
        )
        js.append(f'tl.to("#{sid}-bp{i}", {{opacity:0,x:28,duration:.12,ease:"steps(2)"}}, {1.42 + (i % 6) * .05:.3f});')
    return wrap(sid, d, layout, css, body, "\n".join(js))


@fmt("pixi-signal", layout="over", required=("text",), needs=("pixi",),
     example={"text": "MÚSICA = MAGIA", "kicker": "LIVE // SIGNAL"})
def pixi_signal(sid, d, p, layout="over"):
    """Señal pixelada construida con PixiJS: waveform, platter, bloom y separación RGB."""
    text = json.dumps(str(p["text"]), ensure_ascii=False)
    kicker = esc(p.get("kicker", CTX["channel"] + " // LIVE SIGNAL"))
    css = """
    .pixi-shell {position:absolute;left:0;top:138px;width:1080px;height:620px;overflow:visible;pointer-events:none}
    .pixi-shell canvas {display:block;width:1080px;height:620px;image-rendering:pixelated}
    .pixi-kicker {position:absolute;left:66px;top:176px;font:600 28px var(--font-mono);letter-spacing:.18em;
      color:var(--accent2);z-index:2;text-transform:uppercase;text-shadow:0 0 14px var(--accent2)}
    .pixi-chip {position:absolute;right:66px;top:176px;font:400 28px var(--font-mono);letter-spacing:.10em;
      color:var(--muted);z-index:2}
    .deck-transport {position:absolute;left:48px;bottom:6px;display:flex;gap:14px;z-index:3}
    .deck-transport i {display:block;width:42px;height:42px;border-radius:50%;border:2px solid var(--surface-line);
      background:rgba(5,8,14,.75)}
    .deck-transport i:first-child {border-color:var(--accent2);box-shadow:0 0 14px var(--accent2)}
    .deck-transport i:nth-child(2) {border-color:var(--accent);box-shadow:0 0 14px var(--accent)}
    .deck-model {position:absolute;left:240px;bottom:14px;font:600 20px var(--font-mono);letter-spacing:.12em;
      color:var(--muted);z-index:3}
    """
    body = (f'<div class="pixi-shell"><canvas id="{sid}-canvas" width="1080" height="620"></canvas>'
            f'<div class="deck-transport"><i></i><i></i><i></i><i></i></div>'
            f'<div class="deck-model" data-layout-ignore>{esc(p.get("deck_label", CTX["channel"] + "–3000 // PLAYER A"))}</div></div>'
            f'<div class="pixi-kicker">{kicker}</div><div class="pixi-chip">48KHZ // PIXI CORE</div>')
    js = f"""
    const state = {{ reveal: 0, pulse: 0, glitch: 0 }};
    const canvas = document.getElementById("{sid}-canvas");
    let pixiApp = null, gfx = null, title = null, rgb = null, ready = false;
    function drawPixi() {{
      if (!ready) return;
      const p = state.reveal;
      gfx.clear();
      gfx.circle(10,80,220).fill({{color:0x2EE6F0,alpha:.08*p}});
      gfx.circle(1060,40,250).fill({{color:0x9B6BFF,alpha:.09*p}});
      gfx.ellipse(740,170,300,118).fill({{color:0x02050A,alpha:.74*p}}).stroke({{color:0x2EE6F0,width:3,alpha:.5*p}});
      for(let band=0;band<4;band++) {{
        gfx.moveTo(250,120+band*18).bezierCurveTo(410,20+band*20,560,250-band*16,760,108+band*18)
          .bezierCurveTo(870,42+band*12,950,182,1070,92+band*16)
          .stroke({{color:[0x2EE6F0,0x9B6BFF,0xFF3D9A,0xB9FF3D][band],width:3,alpha:.45*p}});
      }}
      const cx=142, cy=284;
      gfx.circle(cx,cy,112).fill({{color:0x050811,alpha:.62*p}}).stroke({{color:0x9B6BFF,width:6,alpha:.9*p}});
      gfx.circle(cx,cy,70).stroke({{color:0x2EE6F0,width:4,alpha:.9*p}});
      gfx.circle(cx,cy,28).fill({{color:0x101827,alpha:.86*p}}).stroke({{color:0xB9FF3D,width:3,alpha:.9*p}});
      for (let i=0;i<32;i++) {{
        const a=i*Math.PI/16 + state.pulse*.45, r=130;
        const x=cx+Math.cos(a)*r, y=cy+Math.sin(a)*r;
        gfx.rect(Math.round(x/4)*4,Math.round(y/4)*4,8,8).fill({{color:i%3===0?0xB9FF3D:0x2EE6F0,alpha:.35+.55*p}});
      }}
      const count=Math.floor(42*p);
      for (let i=0;i<count;i++) {{
        const x=430+i*13, env=Math.sin(Math.PI*i/41), amp=(Math.sin(i*.82+state.pulse*5)*48+Math.sin(i*1.9)*14)*env;
        const h=10+Math.abs(amp), y=176+amp*.38-h/2;
        gfx.rect(Math.round(x/6)*6,Math.round(y/6)*6,9,Math.round(h/6)*6).fill({{color:i%5===0?0xB9FF3D:0x2EE6F0,alpha:.72}});
      }}
      for (let i=0;i<34;i++) {{
        const active=i/34<p, edge=i%2===0, x=edge?24+(i*37)%190:900+(i*29)%150, y=30+(i*71)%520;
        if(active) gfx.rect(x,y,6+(i%3)*4,6+(i%2)*4).fill({{color:[0x2EE6F0,0x9B6BFF,0xFF3D9A][i%3],alpha:.22}});
      }}
      title.alpha=Math.min(1,Math.max(0,(p-.28)*2.4));
      title.scale.set(.92+.08*Math.min(1,p*1.4));
      if(rgb) {{ rgb.redX=-2-state.glitch*{factor("amplitude", "8", 28)}; rgb.blueX=2+state.glitch*{factor("amplitude", "8", 28)}; }}
      pixiApp.render();
    }}
    (async function() {{
      if (!window.PIXI) return;
      await document.fonts.ready;
      pixiApp = new PIXI.Application();
      await pixiApp.init({{canvas,width:1080,height:620,backgroundAlpha:0,antialias:false,resolution:1,
                          autoStart:false,preference:"webgl",powerPreference:"high-performance"}});
      gfx = new PIXI.Graphics(); pixiApp.stage.addChild(gfx);
      title = new PIXI.Text({{text:{text},style:{{fontFamily:"Pixelify Sans",fontSize:76,fontWeight:"700",
        fill:0xF5F6F7,letterSpacing:2,align:"center"}}}});
      title.anchor.set(.5); title.position.set(735,275);
      try {{
        const glow=new PIXI.filters.GlowFilter({{distance:18,outerStrength:2.5,color:0x2EE6F0,quality:.2}});
        rgb=new PIXI.filters.RGBSplitFilter({{red:[-2,0],green:[0,0],blue:[2,0]}});
        title.filters=[glow,rgb];
        gfx.filters=[new PIXI.filters.PixelateFilter(3)];
      }} catch(e) {{}}
      pixiApp.stage.addChild(title); ready=true; drawPixi();
    }})();
    tl.to(state,{{reveal:1,duration:{max(d * .58, .6):.3f},ease:"power2.out",onUpdate:drawPixi}},.02);
    tl.to(state,{{pulse:1,duration:{max(d - .1, .5):.3f},ease:"none",onUpdate:drawPixi}},.02);
    tl.to(state,{{glitch:1,duration:.07,yoyo:true,repeat:3,ease:"steps(1)",onUpdate:drawPixi}}, {max(d * .46, .4):.3f});
    """
    return wrap(sid, d, layout, css, body, js)


@fmt("pixi-mixer", required=("inputs", "output"), needs=("pixi",),
     example={"kicker": "PATCH THE DREAM", "inputs": ["RECURSOS", "EXPERIENCIA", "DECISIÓN"],
              "output": "MASTER", "output_at": 1.9})
def pixi_mixer(sid, d, p, layout="full"):
    """Consola de mezcla PixiJS: canales pixel-neón convergen en la salida `output` con bloom y glitch."""
    inputs = [str(x) for x in p["inputs"][:3]]
    labels = json.dumps(inputs, ensure_ascii=False)
    output = json.dumps(str(p["output"]), ensure_ascii=False)
    out_at = float(p.get("output_at", 1.9))
    css = """
    .mix-title {position:absolute;left:54px;top:220px;font:700 68px var(--font-display);letter-spacing:.025em;color:var(--text);
      text-shadow:-3px 0 var(--accent3),3px 0 var(--accent),0 0 18px var(--accent3)}
    .mix-kicker {position:absolute;left:58px;top:176px;font:600 30px var(--font-mono);letter-spacing:.16em;color:var(--accent2)}
    .mix-shell {position:absolute;left:28px;top:300px;width:1024px;height:1040px;overflow:visible;
      filter:drop-shadow(0 26px 44px rgba(0,0,0,.65))}
    .mix-shell canvas {display:block;width:1024px;height:1040px;image-rendering:pixelated}
    """
    body = (f'<div class="mix-kicker">{esc(p.get("kicker", "PATCH THE DREAM"))}</div>'
            f'<div class="mix-title">RUTEA TU <span style="color:var(--accent3)">CAMINO</span></div>'
            f'<div class="mix-shell"><canvas id="{sid}-canvas" width="1024" height="1040"></canvas></div>')
    js = f"""
    const mixState={{flow:0,out:0,beat:0,glitch:0}};
    const mixCanvas=document.getElementById("{sid}-canvas");
    const mixLabels={labels};
    let mixApp=null,mixG=null,mixTexts=[],mixOut=null,mixRgb=null,mixReady=false;
    function mixDraw() {{
      if(!mixReady) return;
      mixG.clear();
      for(let x=0;x<1024;x+=48) mixG.moveTo(x,0).lineTo(x,1040).stroke({{color:0x2EE6F0,width:1,alpha:.045}});
      for(let y=0;y<1040;y+=48) mixG.moveTo(0,y).lineTo(1024,y).stroke({{color:0x9B6BFF,width:1,alpha:.045}});
      mixG.ellipse(512,520,462,478).fill({{color:0x050811,alpha:.96}}).stroke({{color:0x293044,width:3,alpha:.8}});
      mixG.ellipse(244,430,188,360).fill({{color:0x08101A,alpha:.94}}).stroke({{color:0x2EE6F0,width:3,alpha:.28}});
      mixG.ellipse(790,410,196,348).fill({{color:0x0B0818,alpha:.94}}).stroke({{color:0x9B6BFF,width:3,alpha:.3}});
      mixG.circle(512,84,54).fill({{color:0x070A12,alpha:1}}).stroke({{color:0xB9FF3D,width:5,alpha:.78}});
      const xs=[174,512,850], cols=[0x2EE6F0,0xB9FF3D,0x9B6BFF];
      for(let i=0;i<3;i++) {{
        const x=xs[i], appear=Math.min(1,Math.max(0,mixState.flow*3-i*.28));
        mixG.roundRect(x-94,112,188,470,94).fill({{color:0x070B13,alpha:.9*appear}}).stroke({{color:cols[i],width:3,alpha:.58*appear}});
        for(let q=0;q<3;q++) {{
          const ky=172+q*82, angle=-2.3+mixState.beat*1.6+i*.35+q*.22;
          mixG.circle(x,ky,35).fill({{color:0x05070D,alpha:appear}}).stroke({{color:cols[i],width:5,alpha:appear}});
          mixG.moveTo(x,ky).lineTo(x+Math.cos(angle)*25,ky+Math.sin(angle)*25).stroke({{color:0xF5F6F7,width:4,alpha:appear}});
        }}
        mixG.ellipse(x,414,48,24).fill({{color:cols[i],alpha:.28*appear}}).stroke({{color:cols[i],width:2,alpha:appear}});
        mixG.rect(x-64,452,18,94).stroke({{color:0x293044,width:2,alpha:appear}});
        const meter=.22+.68*Math.abs(Math.sin(mixState.beat*5+i*1.7));
        mixG.rect(x-60,542-82*meter,10,82*meter).fill({{color:meter>.75?0xFF3D9A:cols[i],alpha:appear}});
        mixG.rect(x+28,452,8,94).fill({{color:0x293044,alpha:appear}});
        const fy=470+Math.sin(mixState.beat*3+i)*18;
        mixG.rect(x+10,fy,46,15).fill({{color:cols[i],alpha:appear}});
        const route=Math.min(1,Math.max(0,(mixState.flow-.3-i*.06)*2));
        const sx=x,sy=580,ex=512,ey=720,mx=sx+(ex-sx)*route,my=sy+(ey-sy)*route;
        mixG.moveTo(sx,sy).bezierCurveTo(sx,650,mx,650,mx,my).stroke({{color:cols[i],width:7,alpha:.9*route}});
        for(let k=0;k<7;k++) {{
          const q=(mixState.beat*.22+k/7)%1, px=sx+(ex-sx)*q,py=sy+(ey-sy)*q;
          if(q<route) mixG.rect(Math.round(px/6)*6,Math.round(py/6)*6,9,9).fill({{color:cols[i],alpha:.8}});
        }}
        mixTexts[i].alpha=appear;
      }}
      mixG.ellipse(512,804,382,142).fill({{color:0x02040A,alpha:.96*mixState.out}}).stroke({{color:0x9B6BFF,width:4,alpha:mixState.out}});
      for(let i=0;i<40;i++) {{
        const active=i/40<mixState.out, x=168+(i*83)%690,y=710+(i*47)%165;
        if(active) mixG.rect(x,y,8+(i%3)*4,8).fill({{color:[0x2EE6F0,0xB9FF3D,0x9B6BFF,0xFF3D9A][i%4],alpha:.28}});
      }}
      mixG.moveTo(250,950).bezierCurveTo(390,900,632,1000,774,942).stroke({{color:0x293044,width:12,alpha:1}});
      const crossX=260+mixState.out*250,crossY=948+Math.sin(mixState.out*Math.PI)*6;
      mixG.circle(crossX,crossY,26).fill({{color:0x2EE6F0,alpha:.92}}).stroke({{color:0xF5F6F7,width:3,alpha:.8}});
      mixOut.alpha=mixState.out; mixOut.scale.set(.86+.14*mixState.out);
      if(mixRgb) {{mixRgb.redX=-3-mixState.glitch*{factor("amplitude", "10", 28)};mixRgb.blueX=3+mixState.glitch*{factor("amplitude", "10", 28)};}}
      mixApp.render();
    }}
    (async function() {{
      if(!window.PIXI)return;
      await document.fonts.ready;
      mixApp=new PIXI.Application();
      await mixApp.init({{canvas:mixCanvas,width:1024,height:1040,backgroundAlpha:0,antialias:false,resolution:1,
                         autoStart:false,preference:"webgl",powerPreference:"high-performance"}});
      mixG=new PIXI.Graphics();mixApp.stage.addChild(mixG);
      const xs=[174,512,850];
      mixLabels.forEach((s,i)=>{{const t=new PIXI.Text({{text:s,style:{{fontFamily:"JetBrains Mono",fontSize:25,
        fontWeight:"600",fill:0xF5F6F7,align:"center"}}}});t.anchor.set(.5);t.position.set(xs[i],610);mixTexts.push(t);mixApp.stage.addChild(t);}});
      mixOut=new PIXI.Text({{text:{output},style:{{fontFamily:"Pixelify Sans",fontSize:118,fontWeight:"700",
        fill:0xF5F6F7,letterSpacing:12}}}});mixOut.anchor.set(.5);mixOut.position.set(512,790);
      try {{const glow=new PIXI.filters.GlowFilter({{distance:24,outerStrength:3,color:0x9B6BFF,quality:.2}});
        mixRgb=new PIXI.filters.RGBSplitFilter({{red:[-3,0],green:[0,0],blue:[3,0]}});mixOut.filters=[glow,mixRgb];
        mixG.filters=[new PIXI.filters.PixelateFilter(2)];}} catch(e){{}}
      mixApp.stage.addChild(mixOut);mixReady=true;mixDraw();
    }})();
    tl.to(mixState,{{flow:1,duration:{max(d*.52,.7):.3f},ease:"power2.out",onUpdate:mixDraw}},.04);
    tl.to(mixState,{{beat:1,duration:{max(d-.1,.6):.3f},ease:"none",onUpdate:mixDraw}},.02);
    tl.to(mixState,{{out:1,duration:.42,ease:"expo.out",onUpdate:mixDraw}},{out_at:.3f});
    tl.to(mixState,{{glitch:1,duration:.06,yoyo:true,repeat:3,ease:"steps(1)",onUpdate:mixDraw}},{out_at + .3:.3f});
    """
    return wrap(sid, d, layout, css, body, js)
