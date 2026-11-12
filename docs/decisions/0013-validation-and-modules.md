# 0013 — Storyboard validado antes de componer; compose dividido; audio en un solo módulo

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto
Antes de publicar, la revisión de la arquitectura encontró tres deudas:
- El storyboard, que es lo que escriben los agentes, solo fallaba a mitad de la composición, error
  por error.
- `compose.py` tenía 631 líneas y estado global (`MUSIC_SRCS`, `AUDIO_CREDITS`, `FONT_FACES`, `PACKS`).
- Las primitivas de audio estaban duplicadas entre `sfx.py`, `musicgen.py`, `audiotools.py` e
  `ingest.py`.

## Decisión
- **`scripts/pipeline/storyboard.py`:** validador sin numpy, como `sfxrecipes.py`. Devuelve todos los
  problemas con su ruta (`overlays[2].out: …`) y es la fuente de verdad de lo permitido.
  `compose.py` lo corre antes de nada y no compone si hay problemas.
- **`scripts/composer/`:** `context` (dataclass `Ctx`), `visual`, `audio` (devuelve un `AudioPlan`),
  `credits` y `plate`. `compose.py` (167 líneas) solo orquesta y reexporta los nombres públicos
  anteriores.
- **`scripts/audio/audiotools.py`:** concentra E/S, síntesis y análisis. Las funciones que eran iguales se
  fusionan. Las que solo se parecen y suenan distinto quedan como pares con nombre claro, para no
  cambiar ningún sonido: `noise_band_frac`/`noise_band_hz`, `reverb_short`/`reverb_ir` y
  `env_decay`/`adsr`.

## Cómo se verificó
Se generó una «foto» de referencia antes de tocar nada: la composición de una pieza real y de la
demo, los kits de efectos de dos canales y tres pistas de música, 114 archivos en total. La foto se
repitió después de cada parte: **0 diferencias, byte a byte.**

Actualización de rutas y organización: [ADR 0019](0019-packages-and-english-paths.md).
