# 0011 — Sonido del canal declarado en archivos (recetas e identidad musical)

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto
Los efectos eran un kit fijo en código y la música propia usaba los mismos instrumentos para todos
los canales. Un agente no podía crear un efecto nuevo sin modificar el motor, y dos canales sonaban
parecido. Además, al medir la música generada, el pad quedaba 6–10 dB por encima de las demás capas:
por eso los cuatro ánimos se parecían.

## Decisión
- **Efectos:** cada canal puede declarar efectos en `audio/sfx/recipes.json` con capas de síntesis
  (tone, noise, fm, sub, grains) y fx. `scripts/audio/sfxrecipes.py` los valida sin numpy (también desde
  `bin/doctor`). Las frecuencias pueden ser relativas al tono de la marca (`"root*1.5"`); se
  interpretan con una expresión regular, nunca con `eval`.
- **Música:** `brand.json → music` fija la paleta de instrumentos (pad, lead, bass, drums, melodía,
  swing, brillo). El ánimo aporta escala, tempo, progresión y **energía**, y la energía decide la
  mezcla por capa (`MIX_DB`).
- **Documentación:** una sola guía, `docs/audio.md`, enlazada desde `AGENTS.md`.

## Consecuencias
- Personalizar el sonido de un canal es editar JSON, no código.
- Los kits y pistas siguen siendo deterministas: misma marca + recetas + semilla dan el mismo audio.
- La calidad depende de la síntesis propia. Si un canal necesita sonidos grabados, la siguiente opción
  son los efectos de Epidemic para la versión orgánica (backlog).
