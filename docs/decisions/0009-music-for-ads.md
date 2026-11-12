# 0009 — Música distinta para la versión de anuncio

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto
El plan personal de Epidemic Sound permite usar su música en los canales propios (también
monetizados y con patrocinios dentro del canal), pero no en anuncios ni posts promocionados. Muchas
veces la decisión de promocionar un video llega después de publicarlo, cuando ya funcionó.

## Decisión
- Cada pista de la biblioteca del canal declara si su licencia cubre publicidad (`ads`). Las propias
  sí; las de Epidemic solo si se registran con `--ads` (plan Pro/Commercial).
- El brief pregunta «¿Publicidad pagada?» (no / sí / quizá) → `storyboard.audio.music.ads`. Con «sí»
  solo se aceptan pistas `ads: true`.
- La versión para pauta es una plataforma más (`presets/ads.json`, `ads: true`). La pista de
  música es una variable de la composición (`music_src`), como el CTA (ADR 0005): el anuncio es el
  mismo video con otra pista, sin recomponer.
- `compose.py` copia cada pista normalizada a −14 LUFS para que ambas usen la misma ganancia y el
  *ducking* sea idéntico.

## Consecuencias
- Decidir tarde no cuesta: se añade `anuncio` a las plataformas y `bin/edit` renderiza esa versión.
- Hace falta al menos una pista propia (o con licencia de anuncios) por canal; hoy la del canal es la
  pista sintética de prueba. Mejorar la música propia queda en el backlog.

## Actualización (2026-11-11)
La música propia sale de `scripts/audio/musicgen.py` (síntesis por capas, determinista). Se descartaron
los modelos de IA de música locales (MusicGen, Stable Audio Open: licencias no comerciales o
limitadas) y las bibliotecas gratuitas (reclamos de Content ID frecuentes aunque la licencia lo permita).
