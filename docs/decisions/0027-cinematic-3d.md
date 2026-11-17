# 0027 — 3D cinematográfico: Three.js empaquetado localmente, un solo reloj y biblioteca de modelos

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Los paquetes de formatos animan en 2D (GSAP, Pixi, Lottie) y moléculas (3Dmol). Faltaban escenas 3D con
acabado de cine (volumen, luz, bloom, profundidad de campo) y la posibilidad de mostrar objetos reales en 3D
(un equipo de laboratorio, una pieza). Requisitos de siempre: sin red, render determinista, opcional (solo se
carga si una escena lo pide) y con la marca del canal.

## Decisión

1. **Three.js 0.187.0 (MIT) + postprocessing 6.39.6 (Zlib)**, versiones exactas publicadas hace más de dos
   semanas. Three ya no publica un archivo para `<script>` (solo módulos ES), así que el motor lo
   **empaqueta con esbuild** (0.28.2, ya instalado por HyperFrames) en un IIFE: `formats/vendor-src/three-pack.js`
   deja `THREE`, `POSTPROCESSING` y `THREE_ADDONS` (GLTFLoader, RoomEnvironment).
   - `formats/vendors.py`: `Vendor.build` (entrada) y `Vendor.packages` (versiones que forman la huella). El build
     se guarda en `node_modules/.videovibe-build/` con su huella; se rehace solo si cambia la entrada o una
     versión. Misma huella → mismos bytes (prueba). No se versiona el archivo generado (1.1 MB).
   - Three usa `Math.random()` (uuid): `seeded=True`, se redirige al generador fijo como Pixi y 3Dmol.
2. **Paquete `cinematic`** (`formats/packs/cinematic.py`) con una base común (`vvCine`): renderer WebGL con
   `preserveDrawingBuffer`, `pixelRatio` 1, fondo opaco del color de la marca, composer con profundidad de campo
   (opcional), bloom y viñeta; colores de `--accent*`. Formatos: `particle-word`, `logo-3d`, `cell-journey`,
   `model-showcase`, `space-field`.
3. **Un solo reloj** (ADR 0022): `tl.fromTo(st, {t: 0}, {t: d, onUpdate: () => draw(st.t)})`. `draw(t)` fija
   cámara, objetos y partículas con valores absolutos del tiempo local; `composer.render(0)` (delta fijo).
   Azar con semilla propia (mulberry32). Nada de `requestAnimationFrame` ni relojes (prueba que lo busca).
4. **Lo que tarda antes del primer cuadro** (texto con la fuente del canal en un canvas, `GLTFLoader.parse`) se
   registra en `window.__hf.buildReady`: HyperFrames espera antes de capturar.
5. **Texto 3D sin fuentes tipográficas 3D:** el texto se dibuja en un canvas con la fuente del canal; las
   partículas toman sus posiciones de los píxeles y el volumen de `logo-3d` son 64 capas con el mismo contorno
   (frente con degradado de acento y metal, costados más oscuros). Funciona con cualquier fuente del canal.
6. **Biblioteca `models`** (`scripts/core/assetlib.py`): `.glb` con todo incrustado, origen y licencia
   obligatorios, ≤ 25 MB, validado por `scripts/core/glb.py` (rechaza recursos externos). Se sirve en base64
   (`assets/data/models-<id>.js`), sin red. Materiales `brand-accent*` toman el color de la marca. El modelo de
   ejemplo del motor (`flask`) se genera con código (`scripts/tools/models.py builtins`): nada descargado.
   `.gitignore` tenía `models/` (modelos de whisper) e ignoraba cualquier carpeta así: ahora `/models/`.

## Pruebas

- Galería `science-60` con los cinco formatos: `hyperframes check` sin errores; capturas en distinto orden
  idénticas (`--determinism`). Render de 16 s de 3D: 24 s con GPU (Apple Silicon).
- Copia de una pieza real con `particle-word` y `cell-journey`: validación, composición, `check` y render en
  borrador correctos, con los colores del canal.
- Hallazgos: el texto de la escena debe quedar por encima de la banda de subtítulos (≤ 1100 px) y el `kicker`
  arriba choca con el título del gancho si la escena cae en los primeros segundos (`content_overlap`). El ancho
  del texto se ajusta al ancho visible de la cámara (`cineSpan`), no a un número fijo.

## Consecuencias

- Agregar efectos de postprocesado o complementos de Three = importar en `three-pack.js` (la huella cambia y el
  build se rehace solo). El grano animado (`NoiseEffect`) depende del reloj interno: no se usa.
- Las piezas sin escenas 3D no cambian (el `index.html` solo carga GSAP); activar el paquete en un canal no
  altera piezas existentes.
- Sin GPU (WSL, CI) el 3D tarda ≈ 4 s por segundo de escena.
