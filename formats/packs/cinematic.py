"""Paquete «cinematic»: escenas 3D con Three.js y postprocesado (bloom, profundidad de campo, viñeta) en los
colores de la marca.

Cada escena dibuja su cuadro desde la línea de tiempo con valores absolutos del tiempo local (`draw(t)`, un
solo reloj, ADR 0022 y 0027): nada de `requestAnimationFrame`, relojes propios ni estados acumulados. El azar
usa semillas fijas. Lo que se prepara antes del primer cuadro (texto con la fuente del canal, modelos glTF)
se espera con `window.__hf.buildReady`. La librería es un IIFE construido con esbuild (`formats/vendors.py`).
Se activa con channel.json → "format_packs": [..., "cinematic"].
"""
from formats.motion import factor
import json

from formats.core import esc, fmt, wrap
from formats.text import KINETIC_CSS, kinetic, kinetic_in, plain

# Base común: renderer + cámara + postprocesado con la marca, texto a canvas con la fuente del canal y polvo.
CINE_JS = """
    const cineVar = (n) => getComputedStyle(document.documentElement).getPropertyValue("--" + n).trim();
    const cineRnd = (seed) => { let s = seed | 0; return () => { s = s + 0x6D2B79F5 | 0;
      let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
    const cineClamp = (x) => x < 0 ? 0 : x > 1 ? 1 : x;
    const cineOut = (x) => 1 - Math.pow(1 - cineClamp(x), 3);
    const cineInOut = (x) => { x = cineClamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
    const cineSpan = (cam, dist) => 2 * Math.tan(cam.fov * Math.PI / 360) * cam.aspect * dist;  // ancho visible
    const cineReady = (key, p) => { window.__hf = window.__hf || {};
      (window.__hf.buildReady = window.__hf.buildReady || {})[key] = p; return p; };
    const cineFont = () => { const f = cineVar("font-display");
      return f && document.fonts ? document.fonts.load("700 120px " + f).then(() => document.fonts.ready) : Promise.resolve(); };
    const cineText = (text, o) => {
      const c = document.createElement("canvas"); c.width = o.w; c.height = o.h;
      const g = c.getContext("2d"), fam = cineVar("font-display") || "sans-serif";
      let size = o.size; g.font = "700 " + size + "px " + fam;
      const m = g.measureText(text).width;
      if (m > c.width * .9) { size = Math.floor(size * c.width * .9 / m); g.font = "700 " + size + "px " + fam; }
      g.textAlign = "center"; g.textBaseline = "middle";
      if (o.gradient) { const gr = g.createLinearGradient(0, c.height * .2, 0, c.height * .8);
        gr.addColorStop(0, o.gradient[0]); gr.addColorStop(1, o.gradient[1]); g.fillStyle = gr; }
      else g.fillStyle = o.fill || "#ffffff";
      g.fillText(text, c.width / 2, c.height / 2 + size * .04);
      return c;
    };
    const cineSprite = (T) => { const c = document.createElement("canvas"); c.width = c.height = 64;
      const g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(.35, "rgba(255,255,255,.55)");
      r.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = r; g.fillRect(0, 0, 64, 64);
      return new T.CanvasTexture(c); };
    const vvCine = (id, o) => {
      const T = THREE, P = POSTPROCESSING, cv = document.getElementById(id);
      const renderer = new T.WebGLRenderer({canvas: cv, antialias: false, alpha: false, stencil: false,
        preserveDrawingBuffer: true, powerPreference: "high-performance"});
      renderer.setPixelRatio(1); renderer.setSize(cv.width, cv.height, false);
      const col = (n, f) => new T.Color(cineVar(n) || f || "#ffffff");
      const scene = new T.Scene(); scene.background = col("bg", "#07090d");
      if (o.fog) scene.fog = new T.FogExp2(scene.background.getHex(), o.fog);
      const camera = new T.PerspectiveCamera(o.fov || 38, cv.width / cv.height, .1, 400);
      const composer = new P.EffectComposer(renderer, {frameBufferType: T.HalfFloatType});
      composer.addPass(new P.RenderPass(scene, camera));
      let dof = null;
      if (o.dof) { dof = new P.DepthOfFieldEffect(camera, {focusDistance: o.dof[0], focusRange: o.dof[1], bokehScale: o.dof[2]});
        composer.addPass(new P.EffectPass(camera, dof)); }
      composer.addPass(new P.EffectPass(camera,
        new P.BloomEffect({intensity: o.bloom ?? 1.4, luminanceThreshold: o.threshold ?? .22, luminanceSmoothing: .25,
                           mipmapBlur: true, radius: .72}),
        new P.VignetteEffect({darkness: o.vignette ?? .55, offset: .3})));
      const accents = ["accent", "accent2", "accent3"].map((n) => col(n));
      const dust = (n, spread, seed, size) => {
        const r = cineRnd(seed), p = new Float32Array(n * 3), c = new Float32Array(n * 3);
        for (let i = 0; i < n; i++) {
          p[i * 3] = (r() - .5) * spread[0]; p[i * 3 + 1] = (r() - .5) * spread[1]; p[i * 3 + 2] = (r() - .5) * spread[2] + (spread[3] || 0);
          const a = accents[Math.floor(r() * 3)], k = .35 + r() * .5; c[i * 3] = a.r * k; c[i * 3 + 1] = a.g * k; c[i * 3 + 2] = a.b * k;
        }
        const g = new T.BufferGeometry();
        g.setAttribute("position", new T.BufferAttribute(p, 3)); g.setAttribute("color", new T.BufferAttribute(c, 3));
        const pts = new T.Points(g, new T.PointsMaterial({size: size || .06, map: cineSprite(T), vertexColors: true,
          transparent: true, depthWrite: false, blending: T.AdditiveBlending}));
        scene.add(pts); return pts;
      };
      return {T, scene, camera, renderer, composer, col, accents, dof, dust, render: () => composer.render(0)};
    };"""

CSS = KINETIC_CSS + """
    .cine-c { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
    .cine-scrim { position: absolute; left: 0; right: 0; pointer-events: none; }
    .cine-scrim.top { top: 0; height: 640px;
        background: linear-gradient(var(--bg) 45%, color-mix(in srgb, var(--bg) 80%, transparent) 70%, transparent); }
    .cine-scrim.bot { top: 1020px; height: 400px;
        background: linear-gradient(transparent, color-mix(in srgb, var(--bg) 75%, transparent) 40%,
                    color-mix(in srgb, var(--bg) 75%, transparent) 60%, transparent); }
    .cine-h { position: absolute; left: 70px; right: 70px; top: 220px; text-align: center; }
    .cine-h .k { font-family: var(--font-mono); font-weight: 600; font-size: 30px; letter-spacing: .24em;
                 color: var(--accent2); margin-bottom: 12px; }
    .cine-h .t { font-family: var(--font-display); font-weight: 700; font-size: 64px; line-height: 1.04;
                 color: var(--text); text-shadow: 0 0 30px color-mix(in srgb, var(--bg) 80%, transparent); }
    .cine-cap { position: absolute; left: 70px; right: 70px; top: 1100px; text-align: center;
                font-family: var(--font-mono); font-size: 30px; color: var(--muted); }
"""
MAX_TEXT = 16


def _canvas(sid):
    return f'<canvas class="cine-c" id="{sid}-c3" width="1080" height="1920"></canvas>'


def _head(sid, p, at=0.2):
    if not (p.get("title") or p.get("kicker")):
        return "", []
    html = (f'<div class="cine-h" id="{sid}-h"><div class="k">{esc(p.get("kicker", ""))}</div>'
            f'<div class="t">{kinetic(p.get("title") or "")}</div></div>')
    js = [f'tl.fromTo("#{sid}-h .k", {{opacity: 0, y: -12}}, {{opacity: 1, y: 0, duration: .35}}, {at:.2f});']
    if p.get("title"):
        js.append(kinetic_in(f"#{sid}-h .t", "rise", at + 0.1, len(plain(p["title"]))))
    return html, js


def _caption(sid, p, at=0.7):
    if not p.get("caption"):
        return "", []
    return (f'<div class="cine-cap" id="{sid}-cap">{esc(p["caption"])}</div>',
            [f'tl.fromTo("#{sid}-cap", {{opacity: 0}}, {{opacity: 1, duration: .4}}, {at:.2f});'])


def _clock(d):
    """La línea de tiempo mueve `st.t` (segundos locales) y cada cambio dibuja el cuadro."""
    return ['const st = {t: 0};',
            f'tl.fromTo(st, {{t: 0}}, {{t: {d:.3f}, duration: {d:.3f}, ease: "none", onUpdate: () => draw(st.t)}}, 0);',
            'draw(0);']


def _check_text(key, required=True):
    def check(p):
        t = plain(p.get(key) or "")
        if not t and required:
            return [f"{key}: texto obligatorio"]
        if len(t) > MAX_TEXT:
            return [f"{key}: máximo {MAX_TEXT} caracteres en una línea (tiene {len(t)}): una palabra o cifra"]
        return []
    return check


def _num(p, key, lo, hi, default):
    v = p.get(key, default)
    return [] if isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi \
        else [f"{key}: número entre {lo} y {hi}"]


def _js_str(s):
    """Texto como literal de JS seguro dentro de <script> (sin «</» que cierre la etiqueta)."""
    return json.dumps(plain(s or ""), ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------- formatos

def _check_particles(p):
    return _check_text("text")(p) + _num(p, "count", 2000, 30000, 14000)


@fmt("particle-word", required=("text",), needs=("three",), check=_check_particles,
     example={"text": "CRISPR", "kicker": "UNA PALABRA", "caption": "Miles de partículas, siempre las mismas"})
def particle_word(sid, d, p, layout="full"):
    """Miles de partículas (semilla fija) vuelan desde el fondo y forman una palabra o cifra con los colores de
    acento; luego respiran con un brillo suave. `text` ≤ 16 caracteres, `count` 2000–30000."""
    n = int(p.get("count", 14000))
    head, hjs = _head(sid, p, at=max(d * 0.45, 0.6))
    cap, cjs = _caption(sid, p, at=max(d * 0.55, 0.9))
    asm = min(max(d * 0.55, 1.0), 2.4)
    js = [CINE_JS, f"""
    const C = vvCine("{sid}-c3", {{bloom: 1.7, threshold: .18, fov: 40}});
    const {{T, scene, camera}} = C;
    const N = {n}, A = {asm:.3f}, rnd = cineRnd(7), rnd2 = cineRnd(11);
    const start = new Float32Array(N * 3), target = new Float32Array(N * 3), delay = new Float32Array(N), ph = new Float32Array(N);
    for (let i = 0; i < N; i++) {{
      const r = 6 + rnd() * 10, a = rnd() * 6.2832, b = (rnd() - .5) * 3.1;
      start[i * 3] = r * Math.cos(a) * Math.cos(b); start[i * 3 + 1] = r * Math.sin(b); start[i * 3 + 2] = r * Math.sin(a) * Math.cos(b) - 4;
      delay[i] = rnd() * .35; ph[i] = rnd() * 6.2832;
    }}
    const pos = new Float32Array(N * 3), colr = new Float32Array(N * 3);
    const geo = new T.BufferGeometry();
    geo.setAttribute("position", new T.BufferAttribute(pos, 3)); geo.setAttribute("color", new T.BufferAttribute(colr, 3));
    const pts = new T.Points(geo, new T.PointsMaterial({{size: .05, map: cineSprite(T), vertexColors: true, transparent: true,
      depthWrite: false, blending: T.AdditiveBlending}}));
    scene.add(pts);
    const bgDust = C.dust(900, [24, 30, 20, -10], 3, .05);
    let ok = false;
    const draw = (t) => {{
      if (ok) {{
        const u = t / A;
        for (let i = 0; i < N; i++) {{
          const k = cineInOut((u - delay[i]) / .65), j = i * 3, w = (1 - k) * 1.6;
          const sw = Math.sin(ph[i] + t * 1.7) * .05 * k;
          pos[j] = start[j] + (target[j] - start[j]) * k + Math.sin(ph[i] + t) * w * .3;
          pos[j + 1] = start[j + 1] + (target[j + 1] - start[j + 1]) * k + Math.cos(ph[i] + t * .8) * w * .3 + sw;
          pos[j + 2] = start[j + 2] + (target[j + 2] - start[j + 2]) * k + sw;
        }}
        geo.attributes.position.needsUpdate = true;
        pts.rotation.y = (1 - cineOut(u)) * .7;
      }}
      bgDust.rotation.y = t * .03;
      camera.position.set(0, 0, 9.5 - {factor("camera_ratio", ".9")} * cineInOut(t / {d:.3f})); camera.lookAt(0, 0, 0);
      C.render();
    }};
    cineReady("{sid}", cineFont().then(() => {{
      const c = cineText({_js_str(p["text"])}, {{w: 1024, h: 384, size: 270}});
      const im = c.getContext("2d").getImageData(0, 0, c.width, c.height).data, cand = [];
      for (let y = 0; y < c.height; y += 2) for (let x = 0; x < c.width; x += 2) if (im[(y * c.width + x) * 4 + 3] > 128) cand.push(x, y);
      const M = cand.length / 2, sc = cineSpan(camera, 8.6) * .84 / c.width;
      for (let i = 0; i < N; i++) {{
        const q = M ? Math.floor(rnd2() * M) : 0, x = M ? cand[q * 2] : c.width / 2, y = M ? cand[q * 2 + 1] : c.height / 2;
        target[i * 3] = (x - c.width / 2) * sc; target[i * 3 + 1] = -(y - c.height / 2) * sc + .35; target[i * 3 + 2] = (rnd2() - .5) * .3;
        const a = C.accents[0].clone().lerp(C.accents[1], x / c.width).multiplyScalar(.75 + rnd2() * .5);
        colr[i * 3] = a.r; colr[i * 3 + 1] = a.g; colr[i * 3 + 2] = a.b;
      }}
      geo.attributes.color.needsUpdate = true; ok = true; draw(st.t);
    }}));""", *_clock(d), *hjs, *cjs]
    return wrap(sid, d, layout, CSS, _canvas(sid) + head + cap, "\n".join(js))


@fmt("logo-3d", required=("text",), needs=("three",), check=_check_text("text"),
     example={"text": "OPEN LAB", "kicker": "PRESENTA", "caption": "Ciencia abierta, en 3D"})
def logo_3d(sid, d, p, layout="full"):
    """Título o nombre del canal en 3D: letras con volumen (fuente del canal, degradado de acento), entran
    girando, se asientan con un destello de luz que las recorre y bloom. `text` ≤ 16 caracteres."""
    head, hjs = _head(sid, {"kicker": p.get("kicker")}, at=0.15)
    cap, cjs = _caption(sid, p, at=max(d * 0.5, 0.9))
    js = [CINE_JS, f"""
    const C = vvCine("{sid}-c3", {{bloom: 1.25, threshold: .35, fov: 34}});
    const {{T, scene, camera}} = C;
    scene.add(new T.AmbientLight(0xffffff, .55));
    const key = new T.DirectionalLight(0xffffff, 2.4); key.position.set(2, 3, 6); scene.add(key);
    const sweep = new T.PointLight(C.accents[1], 60, 9); scene.add(sweep);
    const group = new T.Group(); group.position.y = .55; scene.add(group);
    const dust = C.dust(1400, [20, 30, 16, -6], 5, .045);
    const L = 64, DEPTH = .45;
    let ok = false;
    const draw = (t) => {{
      const e = cineOut(t / 1.5);
      group.rotation.set((1 - e) * .5 + Math.sin(t * .7) * .04 * e, (1 - e) * -1.35 + Math.sin(t * .9) * .16 * e, 0);
      group.scale.setScalar(.6 + .4 * e);
      sweep.position.set(-5 + 10 * cineInOut((t - .6) / 1.6), 1.2, 2.2);
      dust.rotation.y = t * .04; dust.position.y = t * .05;
      camera.position.set(0, 0, 7.9 - {factor("camera_ratio", ".5")} * cineInOut(t / {d:.3f})); camera.lookAt(0, .35, 0);
      C.render();
    }};
    cineReady("{sid}", cineFont().then(() => {{
      const hex = (c) => "#" + c.getHexString(T.SRGBColorSpace);
      const front = new T.CanvasTexture(cineText({_js_str(p["text"])}, {{w: 2048, h: 512, size: 300,
        gradient: [hex(C.accents[0]), hex(C.accents[1])]}}));
      front.colorSpace = T.SRGBColorSpace; front.anisotropy = 8;
      const mask = new T.CanvasTexture(cineText({_js_str(p["text"])}, {{w: 2048, h: 512, size: 300, fill: "#ffffff"}}));
      const W = cineSpan(camera, 7.4) * .9, plane = new T.PlaneGeometry(W, W / 4);
      const side = C.accents[0].clone().lerp(C.col("bg"), .55);
      for (let k = L; k >= 0; k--) {{
        const m = k === 0
          ? new T.MeshStandardMaterial({{map: front, alphaTest: .5, metalness: .35, roughness: .28, emissive: 0xffffff,
              emissiveMap: front, emissiveIntensity: .32}})
          : new T.MeshBasicMaterial({{map: mask, alphaTest: .5, color: side.clone().multiplyScalar(1 - .55 * k / L)}});
        const mesh = new T.Mesh(plane, m); mesh.position.z = -k * DEPTH / L; group.add(mesh);
      }}
      ok = true; draw(st.t);
    }}));""", *_clock(d), *hjs, *cjs]
    return wrap(sid, d, layout, CSS, _canvas(sid) + head + cap, "\n".join(js))


@fmt("cell-journey", needs=("three",), check=lambda p: _num(p, "density", 0.3, 2, 1),
     example={"kicker": "VIAJE AL INTERIOR", "title": "Dentro de la *célula*", "caption": "Ilustrativo · no a escala"})
def cell_journey(sid, d, p, layout="full"):
    """La cámara viaja por un espacio con organelos translúcidos (membranas con brillo en el borde y núcleos
    de color), polvo y profundidad de campo: lo cercano y lo lejano se desenfocan. Título y pie opcionales;
    `density` 0.3–2 (cuántos organelos)."""
    head, hjs = _head(sid, p, at=0.3)
    cap, cjs = _caption(sid, p, at=max(d * 0.5, 0.9))
    n = int(46 * float(p.get("density", 1)))
    js = [CINE_JS, f"""
    const C = vvCine("{sid}-c3", {{bloom: 1.5, threshold: .2, fov: 48, fog: .03, dof: [5.5, 3.5, 3.0]}});
    const {{T, scene, camera}} = C;
    scene.add(new T.AmbientLight(0xffffff, .35));
    const lamp = new T.PointLight(0xffffff, 40, 30); scene.add(lamp);
    const memb = (c) => new T.ShaderMaterial({{transparent: true, depthWrite: false, side: T.DoubleSide,
      uniforms: {{uColor: {{value: c}}}},
      vertexShader: "varying vec3 vN; varying vec3 vV; void main(){{ vec4 mv = modelViewMatrix * vec4(position, 1.0);"
        + " vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }}",
      fragmentShader: "uniform vec3 uColor; varying vec3 vN; varying vec3 vV; void main(){{"
        + " float f = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.4);"
        + " gl_FragColor = vec4(uColor * (0.3 + 1.8 * f), 0.05 + 0.85 * f); }}"}});
    const rnd = cineRnd(21), cells = [], N = {n}, LEN = 70;
    const sphere = new T.IcosahedronGeometry(1, 5), core = new T.IcosahedronGeometry(1, 3);
    for (let i = 0; i < N; i++) {{
      const a = rnd() * 6.2832, rad = 1.4 + rnd() * 4.2, z = 4 - (i / N) * LEN - rnd() * 3;
      const r = .45 + rnd() * 1.9, c = C.accents[Math.floor(rnd() * 3)];
      const g = new T.Group(); g.position.set(Math.cos(a) * rad, Math.sin(a) * rad * 1.3, z);
      const m = new T.Mesh(sphere, memb(c)); m.scale.setScalar(r); m.scale.y *= .8 + rnd() * .4; g.add(m);
      const k = new T.Mesh(core, new T.MeshStandardMaterial({{color: c, emissive: c, emissiveIntensity: .5, roughness: .4}}));
      k.scale.setScalar(r * (.18 + rnd() * .2)); k.position.set((rnd() - .5) * r * .6, (rnd() - .5) * r * .6, 0); g.add(k);
      scene.add(g); cells.push({{g, s: (rnd() - .5) * .8, p: rnd() * 6.28}});
    }}
    const dust = C.dust(2600, [16, 22, LEN + 10, -LEN / 2], 9, .035);
    const draw = (t) => {{
      const u = cineInOut(t / {d:.3f}), z = 9 - u * (LEN * .62);
      camera.position.set(Math.sin(t * .45) * {factor("camera_ratio", ".5")}, Math.cos(t * .37) * .4, z);
      camera.lookAt(Math.sin(t * .3) * .3, 0, z - 10);
      lamp.position.set(0, 1, z - 3);
      for (const c of cells) c.g.rotation.set(c.p + t * c.s * .5, c.p + t * c.s, 0);
      C.render();
    }};""", *_clock(d), *hjs, *cjs]
    # Velo detrás del título y de la banda de subtítulos: los organelos brillan y el texto de la pieza va encima.
    scrim = ('<div class="cine-scrim top"></div>' if head else "") + '<div class="cine-scrim bot"></div>'
    return wrap(sid, d, layout, CSS, _canvas(sid) + scrim + head + cap, "\n".join(js))


def _check_model(p):
    errs = _num(p, "degrees", 0, 720, 200)
    if not isinstance(p.get("model"), str) or not p.get("model"):
        errs.append("model: id de la biblioteca de modelos (scripts/tools/models.py list)")
    return errs


MODEL_CSS = CSS + """
    .cine-lab { position: absolute; left: 70px; right: 70px; top: 1060px; text-align: center; }
    .cine-lab .l { font-family: var(--font-display); font-weight: 700; font-size: 52px; color: var(--text); }
    .cine-lab .s { font-family: var(--font-mono); font-size: 28px; color: var(--muted); margin-top: 8px; }
"""


@fmt("model-showcase", required=("model",), needs=("three",), check=_check_model,
     uses=lambda p: [("models", p["model"])],
     example={"model": "flask", "kicker": "EN EL LABORATORIO", "label": "Matraz Erlenmeyer",
              "sublabel": "Modelo 3D de ejemplo del motor"})
def model_showcase(sid, d, p, layout="full"):
    """Un modelo 3D (.glb de la biblioteca `models`) gira con luz de estudio, reflejos y un piso de luz del
    color de acento; título arriba y etiqueta abajo. Los materiales `brand-accent*` toman los colores de la
    marca. `degrees` 0–720 (giro total)."""
    key = json.dumps(f"models:{p['model']}")
    head, hjs = _head(sid, p, at=0.2)
    lab = ""
    ljs = []
    if p.get("label") or p.get("sublabel"):
        lab = (f'<div class="cine-lab" id="{sid}-lab"><div class="l">{esc(p.get("label", ""))}</div>'
               f'<div class="s">{esc(p.get("sublabel", ""))}</div></div>')
        ljs = [f'tl.fromTo("#{sid}-lab", {{opacity: 0, y: 16}}, {{opacity: 1, y: 0, duration: .5, ease: "expo.out"}}, .55);']
    deg = float(p.get("degrees", 200))
    js = [CINE_JS, f"""
    const C = vvCine("{sid}-c3", {{bloom: .8, threshold: .55, fov: 30}});
    const {{T, scene, camera, renderer}} = C;
    const pm = new T.PMREMGenerator(renderer);
    scene.environment = pm.fromScene(new THREE_ADDONS.RoomEnvironment(), .04).texture;
    scene.environmentIntensity = .45;
    const key = new T.DirectionalLight(0xffffff, 1.6); key.position.set(3, 5, 4); scene.add(key);
    const rim = new T.PointLight(C.accents[1], 50, 14); rim.position.set(-3, 3, -3); scene.add(rim);
    const glow = (a, k) => {{ const c = document.createElement("canvas"); c.width = c.height = 256;
      const g = c.getContext("2d"), r = g.createRadialGradient(128, 128, 0, 128, 128, 128);
      r.addColorStop(0, "#" + a.getHexString(T.SRGBColorSpace)); r.addColorStop(1, "rgba(0,0,0,0)");
      g.globalAlpha = k; g.fillStyle = r; g.fillRect(0, 0, 256, 256); const tx = new T.CanvasTexture(c); tx.colorSpace = T.SRGBColorSpace; return tx; }};
    const floor = new T.Mesh(new T.CircleGeometry(2.2, 96), new T.MeshBasicMaterial({{map: glow(C.accents[0], .3),
      transparent: true, depthWrite: false}}));
    floor.rotation.x = -Math.PI / 2; scene.add(floor);
    const shadow = new T.Mesh(new T.CircleGeometry(1.5, 64), new T.MeshBasicMaterial({{map: glow(new T.Color(0, 0, 0), .8),
      transparent: true, depthWrite: false}}));
    shadow.rotation.x = -Math.PI / 2; shadow.position.y = .005; scene.add(shadow);
    const dust = C.dust(800, [14, 16, 12, -3], 13, .04);
    const pivot = new T.Group(); scene.add(pivot);
    const draw = (t) => {{
      const e = cineOut(t / 1.0);
      pivot.rotation.y = -.6 + {deg:.1f} * Math.PI / 180 * cineInOut(t / {d:.3f});
      pivot.scale.setScalar(.82 + .18 * e); pivot.position.y = (1 - e) * -.4;
      dust.rotation.y = t * .05;
      camera.position.set(0, 1.0, 7.2 - {factor("camera_ratio", ".4")} * cineInOut(t / {d:.3f})); camera.lookAt(0, .05, 0);
      C.render();
    }};
    cineReady("{sid}", new Promise((ok, fail) => {{
      const b = atob(window.__vv[{key}].glb), u = new Uint8Array(b.length);
      for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i);
      new THREE_ADDONS.GLTFLoader().parse(u.buffer, "", (g) => {{
        const m = g.scene;
        m.traverse((o) => {{ if (o.isMesh) {{ const k = {{"brand-accent": 0, "brand-accent2": 1, "brand-accent3": 2}}[o.material.name];
          if (k !== undefined) {{ o.material.color.copy(C.accents[k]); o.material.emissive.copy(C.accents[k]).multiplyScalar(.25); }} }} }});
        const box = new T.Box3().setFromObject(m), s = box.getSize(new T.Vector3()), c = box.getCenter(new T.Vector3());
        const f = Math.min(1.45 / s.y, 1.05 / Math.max(s.x, s.z)); m.scale.setScalar(f); m.position.set(-c.x * f, -box.min.y * f, -c.z * f);
        pivot.add(m); draw(st.t); ok();
      }}, fail);
    }}));""", *_clock(d), *hjs, *ljs]
    return wrap(sid, d, layout, MODEL_CSS, _canvas(sid) + head + lab, "\n".join(js))


SPACE_CSS = CSS + """
    .cine-big { position: absolute; left: 60px; right: 60px; top: 700px; text-align: center; }
    .cine-big .k { font-family: var(--font-mono); font-weight: 600; font-size: 32px; letter-spacing: .26em;
                   color: var(--accent2); margin-bottom: 18px; }
    .cine-big .t { font-family: var(--font-display); font-weight: 700; font-size: 92px; line-height: 1.02;
                   color: var(--text); text-shadow: 0 0 40px color-mix(in srgb, var(--accent) 45%, transparent); }
"""


@fmt("space-field", required=("title",), needs=("three",),
     example={"kicker": "CAPÍTULO 2", "title": "Lo que *no* vemos", "caption": "Un fondo con profundidad"})
def space_field(sid, d, p, layout="full"):
    """Fondo 3D con profundidad para un título: rejilla de luz que se pierde en la niebla, polvo y orbes
    desenfocados; la cámara avanza despacio. Sirve de portadilla o separador de capítulos."""
    big = (f'<div class="cine-big" id="{sid}-b"><div class="k">{esc(p.get("kicker", ""))}</div>'
           f'<div class="t">{kinetic(p["title"])}</div></div>')
    bjs = [f'tl.fromTo("#{sid}-b .k", {{opacity: 0, y: -14}}, {{opacity: 1, y: 0, duration: .6, ease: "expo.out"}}, .25);',
           kinetic_in(f"#{sid}-b .t", "rise", 0.4, len(plain(p["title"])))]
    cap, cjs = _caption(sid, p, at=max(d * 0.45, 0.9))
    js = [CINE_JS, f"""
    const C = vvCine("{sid}-c3", {{bloom: 1.5, threshold: .15, fov: 55, fog: .045}});
    const {{T, scene, camera}} = C;
    const grid = new T.GridHelper(120, 90, C.accents[0], C.accents[0].clone().multiplyScalar(.45));
    grid.position.y = -2.6; scene.add(grid);
    const roof = new T.GridHelper(120, 60, C.accents[1].clone().multiplyScalar(.5), C.accents[1].clone().multiplyScalar(.25));
    roof.position.y = 5.5; scene.add(roof);
    const dust = C.dust(3000, [30, 14, 90, -35], 17, .05);
    const rnd = cineRnd(31), orbs = [];
    for (let i = 0; i < 16; i++) {{
      const c = C.accents[i % 3], m = new T.Mesh(new T.SphereGeometry(.12 + rnd() * .25, 24, 16),
        new T.MeshBasicMaterial({{color: c.clone().multiplyScalar(2.2)}}));
      m.position.set((rnd() - .5) * 16, -1 + rnd() * 5, -6 - rnd() * 50); scene.add(m); orbs.push({{m, p: rnd() * 6.28}});
    }}
    const draw = (t) => {{
      const u = cineInOut(t / {d:.3f});
      camera.position.set(Math.sin(t * .25) * .4, .4 + u * .3, 10 - u * {factor("camera_ratio", "7")}); camera.lookAt(0, .6, -20);
      orbs.forEach((o) => o.m.scale.setScalar(1 + .25 * Math.sin(t * 1.3 + o.p)));
      dust.rotation.z = t * .01;
      C.render();
    }};""", *_clock(d), *bjs, *cjs]
    return wrap(sid, d, layout, SPACE_CSS, _canvas(sid) + big + cap, "\n".join(js))
