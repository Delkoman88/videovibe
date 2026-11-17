# 0025 — Efectos sobre la toma: recorte local de la persona y capas dentro de la cámara

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Los formatos animan encima o entre tomas. Los efectos más llamativos de las redes interactúan con la toma:
texto detrás de la persona, fondo cambiado, halo, cuadro congelado con recorte. Necesitan separar a la
persona del fondo sin alterar su identidad (regla 3), sin red y con render determinista.

## Decisión

1. **Recorte con lo que ya trae HyperFrames:** `hyperframes remove-background` (modelo local
   `u2net_human_seg`, CoreML en Mac). Prueba técnica: bordes limpios en pelo, lentes y ropa sobre fondo claro
   y oscuro; ≈ 210 ms por cuadro (≈ 6 s por segundo de video). No se escribe ni se entrena un modelo propio.
2. **Solo los tramos que se usan** (`scripts/pipeline/cutout.py`): cada efecto recorta su tramo de
   `cut/master-cut.mp4` con 0.2 s de margen; `freeze-cutout` usa un solo cuadro (PNG). Caché en
   `<pieza>/work/cutout/` por huella del corte + tramo + modelo: recomponer no recalcula.
3. **Capas dentro de `#cam`:** placa → capa «detrás» → `<video>` del recorte con `data-media-start` → resto
   igual. La cámara escala placa y recorte juntos: probado con un `punch`, sin desalineo y con capturas en
   distinto orden idénticas. Sin `fx`, el `index.html` es el mismo de antes (regresión byte a byte).
4. **Colocación automática:** el recorte mide `subject_top` (primera fila con persona en la franja
   central); `text-behind` con `y: auto` se coloca para que la cabeza tape la parte baja del texto.
5. **Identidad y voz:** el recorte solo cambia de capa. `freeze-cutout` se rechaza si congela mientras se
   habla (validación con los tiempos de las palabras de `captions.json`): los labios quedarían quietos con la
   voz sonando.

## Revisión con la primera pieza (2026-11-17)

- **Parpadeo del fondo** en `background-swap`: el modelo, sin memoria entre cuadros, tomaba durante ~9 cuadros
  un triángulo de cortina y luego la silla como «persona». Solución (`scripts/pipeline/matte.py`): con cámara
  fija se reconstruye el fondo por mediana de los cuadros donde el modelo no ve persona en cada punto; se
  conserva el núcleo (persona en ≥ 90 % de los cuadros), se descarta lo igual al fondo, mayoría espacial 3×3 y
  de 5 cuadros, solo lo conectado al cuerpo y un margen de un punto. La decisión (135×240) solo quita regiones;
  el borde suave sigue siendo el del modelo. Con cámara en movimiento (fondo inestable) no se aplica.
- **Estabilizador revisado (estable-v6) con la segunda prueba.** La regla «igual al fondo» quitaba partes del
  cuerpo (chamarra oscura sobre la silla oscura, ≈ 17 %): escalones y halo asomando. Además el modelo **pierde**
  la chamarra 5–10 cuadros seguidos (lo inverso de la cortina). Ahora:
  - Se quita solo lo que es igual al fondo **y** pasajero (visto en < 50 % de ±1 s): la cortina (≈ 25 %) sí,
    la chamarra (≈ 85–90 %) no. Nada más se pone en cero (antes todo lo < 0.5 de opacidad se perdía).
  - Se rellena lo que el modelo pierde: persona en ≥ 50 % del tramo, igual en color a la última o próxima vez
    que fue cuerpo seguro (opacidad > 0.9, sin el filo mezclado con la pared) y en pedazos ≥ 5×5 puntos.
  - Opacidad más sólida (0.08 → 0, 0.7 → 1): la ropa tenue no deja ver el fondo nuevo.
  - Solo para `subject-glow` (el recorte va encima de la misma toma, rellenar de más no se nota): cierre en el
    tiempo (persona en alguno de los 8 cuadros anteriores y de los 8 siguientes) e interior sólido.
  Descartado: rellenar todo hueco cerrado (aros alrededor de los huecos reales entre brazo y cuerpo).
- **estable-v7 (detalles finos).** Los cuadritos junto a las manos y en el filo del cuadro venían del relleno:
  con la mano en movimiento devolvía pedazos de silla o de pared que el modelo, con razón, ya no veía, en bloques
  de 8 px. Ahora un pedazo de relleno se conserva solo si su contorno da sobre todo a cuerpo (≤ 65 % al fondo; el
  borde del cuadro no cuenta): el hueco de la chamarra sí (13–45 %), la silla tras la mano no (70–100 %). Y para
  el movimiento rápido (mano o manga borrosas que el modelo pierde 1–3 cuadros) se cierra en el tiempo: persona
  en alguno de los 4 cuadros anteriores y de los 4 siguientes, salvo donde el fondo está confirmado (visto en
  ≥ 3 muestras e igual). Descartado: tomar la forma del relleno de un cuadro anterior (el borde del modelo en la
  silla es inestable: quedaba más dentado).
- **Límite conocido:** el modelo incluye de forma estable objetos pegados a la persona (la silla gamer detrás de
  los hombros). No parpadean, así que el estabilizador no los toca; el halo los rodea y en `background-swap` se
  ven. Se evita al grabar (ver `docs/effects.md`); un modelo de video mejor queda en el backlog.
- Fundidos del fondo de 0.3 → 0.55 s (`sine.inOut`): el cambio de toda la pantalla era brusco.
- **`depth`** en `text-behind` (`behind`, `front`, `through`): la persona lo pidió delante a veces. `through`
  usa una copia delante del recorte que se desvanece (`data-layout-allow-overlap`).
- **`will-change: transform` rompía el determinismo**: con él, Chrome rasteriza cada letra animada una vez y
  el borde (subpíxel) dependía del orden de los cuadros (hasta 50 niveles en el 0.08 % de los píxeles). Se
  quitó de `formats/text.py` (afecta a `motion` y `text_fx`); capturas en distinto orden: ≤ 2 niveles.

## Hallazgos de la prueba técnica para las fases siguientes

- `hyperframes beats <archivo> --json` → `{bpm, beatTimes}` en ~1.4 s. Exacto con la música de `musicgen`
  (99.9 BPM); con una pista de Epidemic de 140 BPM se enganchó a un pulso de tresillo (94 BPM). Se usará el
  BPM de la biblioteca cuando exista y del detector solo la fase.
- Las transiciones del registro de HyperFrames (Apache-2.0) son CSS + GSAP simples: se adaptan con color de
  marca y sin CDN.
- Three.js 0.187 + postprocessing 6.39 empaquetados con esbuild en un IIFE (1 MB, compilación reproducible):
  deterministas; 4 s de 3D con bloom tardan 8 s con GPU y 17 s sin GPU.

## Consecuencias

- La primera composición de una pieza con `fx` tarda más (≈ 6 s por segundo de efecto); se avisa con más de 6 s.
- `hyperframes check` informa (`text_occluded`) cuánto tapa la persona al texto: es lo esperado.
- Si el borde no convence en alguna toma (pelo muy suelto, fondo del mismo color que la ropa), se cambia el
  tramo o se omite el efecto; nunca se retoca a la persona.
