# 0028 — Transiciones de superposición: una capa propia, solo CSS + GSAP y el máximo en el corte

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Los cambios de toma a toma o de toma a escena eran cortes secos o fundidos de la escena. Las redes usan
transiciones con energía (destellos, fugas de luz, trazos, muros de texto, glitch). Requisitos: no tocar la
placa ni la cámara (los cortes del master no cambian), con la marca del canal, deterministas y sin red.

## Decisión

1. **Superposición, no mezcla de dos tomas:** cada transición cubre el cuadro y llega a su máximo justo en `at`
   (la mitad de su duración); el corte real ocurre debajo. Así sirve igual entre tomas, escenas y B-roll y no
   obliga a recortar ni alargar la placa.
2. **Una sub-composición** (`compositions/transitions.html`, `scripts/composer/transitions.py`) montada después
   de escenas y burbujas y antes de tarjetas y subtítulos. Sin `transitions`, no existe y el `index.html` es el
   de siempre (prueba).
3. **Solo CSS + GSAP**, inspiradas en los bloques del registro de HyperFrames (light leak, flash, scribble,
   clone wall, glitch) pero escritas aquí, con variables de la marca: sin shaders, sin `filter` animado, sin azar
   en el navegador. `glitch` sale de un hash del índice del paso (mismo resultado en cualquier orden de
   captura); los colores de las barras van fijos en el HTML (GSAP no interpola `var()`).
4. **Estados iniciales en el HTML** (opacidad 0, trazo con `dashoffset` = largo) y no con `tl.set(..., 0)`: un
   `set` en 0 no se pinta con la línea de tiempo en pausa (aviso de HyperFrames). Opacidad y transformaciones
   en tweens separados (sin tweens superpuestos sobre la misma propiedad).
5. **Sonido automático** por tipo (`impact`, `whoosh`, `click`, `zap`) desde el kit del canal; los de barrido
   empiezan al inicio para culminar en el corte. `sfx: false` lo quita.
6. **Validación:** tipo, duración 0.4–1.2 s, dentro del video, ≥ 1.5 s entre transiciones, `word` en
   `word-wall`, rol y sonido existentes; aviso si `at` no cae en un corte (`cut-map.json`) ni en un borde de
   escena o B-roll (±0.25 s).

## Pruebas

Copia de una pieza real con los seis tipos en bordes de escena: `hyperframes check` sin errores; capturas en
orden directo e inverso idénticas píxel a píxel (12 instantes alrededor de los cortes). `word-wall` lleva
`data-layout-ignore` (texto decorativo: el revisor de HyperFrames lo marcaba como recortado e ilegible).

## Consecuencias

- Agregar un tipo = una rama en `_one()` + su sonido en `SFX` + una fila en `docs/effects.md`.
- Los subtítulos quedan encima de la transición: durante un `flash` la frase sigue visible (intencional).
