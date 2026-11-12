# Changelog

## Sin publicar — 2026-11-12

- Cambio incompatible: paquetes Python por responsabilidad y nombres de sistema en inglés, sin alias.
- Validador del storyboard por secciones, conservando resultados y orden de mensajes.
- Migración reversible con respaldo; títulos y originales personales intactos.
- Ver `docs/migration.md` y ADR 0019.

Formato: una entrada por versión; dentro, lo que cambió para quien usa el motor. Las decisiones
técnicas y su porqué están en `docs/decisions/`.

## 0.9.2-alpha
- Corregido en Linux: el control de sincronía de la voz tratada comparaba la duración declarada del contenedor (el «priming» de AAC se declara distinto en ffmpeg 6 y 9); ahora compara las muestras decodificadas.

## 0.9.1-alpha
- Corregido en Linux: el corte usaba `-/filter_complex`, que no existe en ffmpeg 6 (Ubuntu 24.04); ahora se detecta la versión de ffmpeg. Encontrado por la demo de punta a punta en GitHub.
- La demo muestra el error real de `bin/edit` cuando un paso falla.

## 0.9.0-alpha — primera versión pública
- Carpeta de originales configurable como `input_dir` / `$VIDEOVIBE_INPUT` (los nombres `material_dir` / `$VIDEOVIBE_MATERIAL` siguen valiendo); documentación corregida: la plataforma de anuncio es `ads` y los scripts se llaman `apply_cut.py` / `paper_cut.py`.
- Carpetas fáciles de encontrar en la raíz: `input/` (originales; `bin/new-piece --from <nombre>` los busca ahí) y `deliveries/<Canal>/<fecha> <pieza>/` (finales verificados con portada, texto y `README.md`, como enlaces o copias; `bin/edit` la abre al entregar). ADR 0018.
- Revisiones A/B guiadas en terminal: resumen, cuatro preguntas, apertura de archivos y rutas absolutas; la aprobación requiere una presentación vigente. `bin/open-review` abre otros archivos de revisión.
- B-roll y grabaciones de pantalla como insertos visuales del storyboard: recorte vertical, tiempo de origen, conversión SDR, registro de derechos y revisión B.
- Validado con material real: fuente HDR horizontal y captura de Terminal; borrador vertical de 8 s con audio y `hyperframes check` sin errores ni avisos.
- Encuadres de detalle para capturas horizontales (`fit=region`), avisos de legibilidad y cuadros de revisión B a tamaño de teléfono.
- Prueba técnica adicional con una fuente vertical real aportada por la persona y la captura de Terminal: borrador 9:16 de 8 s y vistas a tamaño de teléfono.
- Probado el inserto de Terminal sobre una pieza hablada y cortada: revisión B aprobada y entregas TikTok, Reels y anuncio verificadas.
- Corregido: la huella de composición con B-roll cambiaba también la de piezas sin insertos y obligaba a re-verificar piezas ya aprobadas; ahora solo cambia cuando hay insertos.
- Pruebas de voz: detectan cuando `say` produce un archivo vacío en el sandbox y se omiten en ese entorno; se ejecutan normalmente cuando macOS genera audio real.
- Nombre: **VideoVibe**. Licencia Apache-2.0.
- Los canales pueden vivir fuera del repo (`local.json → channels_dir` o `VIDEOVIBE_CHANNELS`).
- Canal de ejemplo ficticio `science-60`, `bin/setup`, `bin/demo`; README e instalación en inglés y español.
- `bin/doctor` multiplataforma (macOS y Linux); ffmpeg detectado (`VIDEOVIBE_FFMPEG`).
- `scripts/pipeline/storyboard.py`: valida el storyboard y devuelve todos los problemas juntos con su ruta; `compose.py` no compone si hay problemas.
- **Primeros pasos:** `bin/welcome` (etapa de la persona: instalar, crear-canal, completar-canal, primera-pieza, listo) y `docs/getting-started.md` (bienvenida, demo, 6 preguntas, canal con valores por defecto, primera pieza). `bin/new-channel --about … --person …` crea un canal completo sin TODO.
- Corregido: `sfx.py` fallaba con canales fuera del repo. Whisper reintenta solo sin GPU si la GPU falla (sandbox de Codex, máquinas sin GPU).
- `bin/new-piece` (pieza nueva en la carpeta de canales correcta) y pausas «material» y «brief» en `bin/edit` (la regla «nada sin brief» ya no depende de que el agente se acuerde); `scripts/pipeline/cover.py` (portada desde el gancho).
- Interno: `compose.py` dividido en `scripts/composer/`; primitivas de audio en `audiotools.py`; `bin/publish`; test de `verify.py`; demo de punta a punta en CI.

## 0.8 — audios aportados y micrófono externo
- Música aportada: revisión del archivo, `--trim`, BPM estimado, `music.py fit` (duración exacta por compases).
- Efectos aportados: `sfx.py add` (precedencia usuario > receta > base).
- Bloque de sonido de `assets.md` automático; regla de licencias para la versión anuncio.
- Micrófono externo: sincronización automática (desfase + deriva, cobertura parcial); la transcripción y el corte lo usan, con verificación por segmento.

## 0.7 — sonido por canal
- Guía única `docs/audio.md`.
- Efectos por receta (`audio/sfx/recipes.json`), `sfx.py --list/--preview`.
- Identidad musical (`brand.json → music`): instrumentos por ánimo, melodía, mezcla por energía; intro nivelada.
- Render por plataforma: solo se rehace la versión que cambió.

## 0.6 — voz
- Tratamiento de voz medido (`scripts/audio/voice.py`): ruido, ecualización, «s», compresión y expansor; `--compare`.
- Volumen de música por defecto por canal (`channel.json → audio`).

## 0.5 — sonido
- Mezcla con ducking por tiempos de palabra; kit de efectos sintetizado por canal; biblioteca de música con licencia (Epidemic Sound vía MCP).
- Versión `anuncio` con música apta para publicidad; música propia (`scripts/audio/musicgen.py`).

## 0.4 — orquestador
- `bin/edit`: avanza solo hasta cada revisión humana; idempotente; invalida aprobaciones si cambia lo aprobado.

## 0.3 — multicanal
- Motor separado de los canales (`channels/<canal>/`), idiomas (`lang/`), formatos con paquetes temáticos, estado por pieza (`bin/status`).

## 0.2 — primera pieza
- Corte en papel (revisión A), transcripción por tramos, HDR→SDR, subtítulos palabra por palabra, composición con HyperFrames, verificación de entrega.
