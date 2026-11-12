# 0012 — Audios aportados por la persona y micrófono externo

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto
En uso real se necesitó usar música y efectos propios o de terceros, y grabar con micrófono externo
además del teléfono. El sistema solo conocía Epidemic, la síntesis propia y el audio de la cámara.

## Decisión
- **Música y efectos aportados** entran por los mismos registros que el resto (`library.json`,
  `sfx.json` vía `user.json`), con licencia obligatoria, quién lo aportó y si sirve para anuncios.
  Los originales quedan fuera de git (como la música de Epidemic).
- **`music.py fit`** ajusta la duración en local, cortando o repitiendo compases según el BPM.
- **`assets.md`:** el bloque de sonido lo escribe `compose.py`, para que no dependa de que alguien se
  acuerde de actualizarlo.
- **Micrófono:**
  - Sincronización automática en dos pasos: envolventes en todo el largo, luego GCC-PHAT en 12
    ventanas.
  - La aceptación sale del **consenso** de ventanas en una recta (desfase + deriva) a ±3 ms, no de la
    nitidez de cada ventana: en audio con eco, los picos de reflexión engañan a la correlación de
    una ventana sola, pero no se ponen de acuerdo entre sí.
  - El micrófono puede cubrir solo parte de la toma.
  - `apply-cut.py` verifica cada segmento antes de usarlo.

## Consecuencias
- La transcripción usa el micrófono cuando lo hay, así que mejora sin cambiar `transcribe.py`.
- Ante la duda se usa la cámara: peor sonido, pero nunca labios fuera de sincronía.
- La voz en off sin video queda para la fase de B-roll y pantalla.
