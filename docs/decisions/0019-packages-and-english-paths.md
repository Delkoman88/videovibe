# 0019 — Paquetes del motor y nombres del sistema en inglés

**Fecha:** 2026-11-12 · **Estado:** vigente

## Decisión

El motor separa `scripts/` en `pipeline`, `audio`, `core`, `composer`, `validation`, `tools` y
`tests`. Las importaciones usan el paquete `scripts`; las herramientas admiten `python -m`.
Los comandos principales siguen en `bin/`. No se conservan alias de rutas retiradas.

`validation/storyboard.py` coordina raíz, overlays, scenes, camera, emphasis, platforms,
broll, audio y voice, en ese orden. Cada ejecución tiene su propio estado compartido:
identificadores, límites temporales, plataformas publicitarias y resultados. La extracción
conserva el contrato, los mensajes y su orden; no introduce nuevas reglas de validación.

Todos los nombres definidos por el sistema están en inglés. Comandos y documentos usan
kebab-case; módulos Python, snake_case. La documentación permanece en español. Los nombres
personales de canales, piezas, títulos y originales no se traducen. Tampoco se cambian los
valores editoriales de los esquemas existentes, salvo el identificador de plataforma `ads`
que sustituye a `anuncio` junto con su preset y archivos relacionados.

Esta decisión sustituye las rutas citadas en ADR 0013 y 0018: `input/` y `deliveries/` son
las carpetas predeterminadas; `README.md`, `subtitles.srt`, `cover.jpg` y `copy.md` nombran
los archivos de entrega. Se conservan las variables y claves de configuración existentes.

## Migración

`bin/migrate-layout` simula por defecto; `--apply` respalda los textos modificados y guarda
un diario fuera del repositorio, en `~/.videovibe-backups/`. Los medios se renombran sin
reescribirlos, comprobando SHA-256. `--resume <manifest>` recupera una interrupción;
`--rollback <manifest>` restaura nombres y contenido, rechazando conflictos o modificaciones
posteriores. `--channels-dir` permite probar sobre una copia aislada.

Los originales de `raw/`, dependencias, Git y registros históricos de `work/` quedan fuera.
Los enlaces simbólicos que necesiten un cambio bloquean la migración para revisión explícita;
no se siguen silenciosamente. Los destinos existentes bloquean el plan antes de escribir.
La aprobación B afectada por el cambio de plataforma se archiva y requiere nueva revisión.

## Validación

49 casos del validador comparados con la implementación anterior, conservados como fixtures.
HTML/CSS/JS de una composición y 23 efectos deterministas idénticos byte a byte.
Migración real probada sobre copia: aplicación y reversión de 29 operaciones, con los 173
archivos comprobados idénticos después de revertir. Pruebas de colisión, idempotencia,
interrupción, reanudación y protección de modificaciones posteriores.

La validación Linux completa, otros agentes, voz de pantalla y velocidad de transcripción
siguen pendientes; este cambio no las considera resueltas.

Cierre: suite completa de 120 pruebas en verde (209 s), más dos pruebas nuevas del bloqueo
de publicación en verde. Sin omisiones. Whisper reintentó sin GPU durante la suite.
Catálogo vigente, ayudas CLI comprobadas desde fuera del repositorio y enlaces Markdown
sin destinos rotos. Migración aplicada; una segunda simulación devuelve cero operaciones.
