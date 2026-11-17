# 0022 — Librerías de animación opcionales y un solo reloj por escena

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Queremos muchas formas de animar (plugins de GSAP, Lottie, moléculas 3D, Pixi) sin que cada pieza cargue
todo, sin que un canal cambie de aspecto por lo que pide otro y sin perder el render determinista de
HyperFrames. Hasta 0.10.0 Pixi era un caso especial dentro de `compose.py` y `visual.py`.

## Decisión

1. **Una tabla:** `formats/vendors.py → VENDORS` declara cada librería: archivos de `node_modules`, orden
   de carga, si usa azar (`seeded`) y, para plugins de GSAP, el nombre a registrar. Un formato declara lo
   que usa con `@fmt(..., needs=(...))`; el registro rechaza nombres desconocidos.
2. **Solo lo necesario:** `compose.py` copia a `hf/assets/vendor/` GSAP y lo que piden las escenas del
   storyboard (solo si el archivo cambió) y borra lo que sobra; `index.html` carga lo mismo, en orden. Sin
   necesidades, el HTML es idéntico al de antes (prueba: la cabecera de Pixi de 0.10.0 se conserva byte a byte).
3. **Azar fijo:** las librerías `seeded` se copian con `Math.random()` redirigido a
   `globalThis.__videovibeRandom` (xorshift con semilla fija, ADR 0020).
4. **Un solo reloj:** toda librería ajena a GSAP se dibuja desde la línea de tiempo de GSAP de su escena
   (`tl.fromTo(estado, …, {onUpdate: dibujar})`), con valores absolutos calculados del tiempo local:
   nunca con su propio `play()`, `requestAnimationFrame` ni rotaciones acumuladas. Así funcionan tramos,
   velocidad y repeticiones, y HyperFrames puede saltar a cualquier cuadro.
5. **Datos sin red:** estructuras, animaciones y otros datos se sirven como archivos locales del proyecto
   (p. ej. `assets/data/<id>.js` que define una variable global), nunca con `fetch` a internet.
6. **Versiones exactas** en `package.json`, publicadas hace al menos dos semanas; licencia en `NOTICE`.

## Prueba técnica (HyperFrames 0.9.32)

Proyecto desechable con una escena Lottie (`lottie-web` 5.13.0, render SVG) y otra 3D (`3Dmol.js` 2.5.5,
proteína 1CRN), las dos manejadas desde GSAP:
- Lottie: `loadAnimation({autoplay:false, animationData})` + `goToAndStop(cuadro, true)` en `onUpdate`.
  HyperFrames trae un adaptador que también mueve las animaciones registradas en `window.lottie`; para que
  haya un solo reloj, la librería se renombra al cargarla (`__vvLottie`) y el adaptador no la ve.
- 3Dmol: `createViewer(…, {preserveDrawingBuffer:true})`; en cada cuadro `resize()`, `setView(vista base)`,
  `rotate(ángulo absoluto)` y `render()`. Sin `resize()` el visor nace con tamaño cero (la escena aún no
  tiene medidas) y la molécula sale desplazada.
- `hyperframes check`: 0 errores. Capturas en orden 1.2/4.0/5.4 s y 5.4/1.2/4.0 s: píxeles idénticos.

## Lecciones del paquete `motion` (fase 1)

- **Texto partido en Python**, no con SplitText: no depende de que la fuente haya cargado al construir la
  escena (`formats/text.py`, compartido por `motion` y por `text_fx` de las tarjetas).
- **«Descifrar» con hash del cuadro**, no con ScrambleText: ScrambleText pide azar en cada actualización y
  el resultado dependería del orden en que HyperFrames visita los cuadros.
- **Recorridos dentro del SVG de la ruta**, sin `align` de MotionPath: `align` mide la pantalla al construir
  la escena (oculta, tamaño cero) y el punto quedaba en (0, 0).
- **Nada de `fromTo` con render inmediato para elementos que aparecen después**: usar `set` + `to`.
- **Colores para tweens** leídos de las variables CSS (`getComputedStyle`): GSAP no interpola `var(--x)`.
- **Validación por formato** (`@fmt(..., check=fn)`): listas, iconos y valores se validan con el storyboard,
  todos los errores juntos, antes de componer.
- **Determinismo con GPU:** el suavizado puede variar 1–2 niveles por píxel entre capturas; la galería
  tolera ≤ 8 niveles en ≤ 0.01 % de los píxeles. Un fallo real (un elemento en otro lugar) lo rebasa.

## Galería y control de calidad

`bin/format-gallery --channel <id> [--check] [--determinism]` arma un proyecto con una escena por formato
(mismo `formats.render`, marca y librerías del canal), captura cada una y, con `--determinism`, vuelve a
capturar en orden inverso y compara píxeles. Es la prueba visual obligatoria de todo formato nuevo.

## Consecuencias

- Agregar una librería = una entrada en `VENDORS` + versión en `package.json` + `NOTICE`; ningún cambio en
  `compose.py` ni en `visual.py`.
- WebGL (Pixi, 3Dmol) renderiza más lento sin GPU (WSL, CI); se mide en la galería.
- Los iconos de Lucide (ISC) viven en `formats/icons/` (selección versionada, `scripts/tools/icons.py`), sin
  dependencia de npm en el render.
