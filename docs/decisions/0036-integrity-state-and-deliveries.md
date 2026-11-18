# 0036 — Estado, evidencia de aprobación y entregas independientes

**Fecha:** 2026-11-17 (vigente desde v0.13.2; retiro de lo heredado en v0.15) · **Estado:** vigente

## Contexto

Las aprobaciones A/B se comprobaban por fecha y los artefactos por fecha o tamaño; las entregas eran
enlaces duros. Una edición concurrente, un archivo cambiado sin cambiar su fecha o un render
sobrescrito podían dejar una entrega distinta de lo aprobado sin que nada lo detectara. Al mismo
tiempo, la evidencia no debe invalidarse por razones ajenas al contenido (mover carpetas, actualizar
el motor), porque eso obliga a revisar y renderizar de nuevo sin motivo.

## Decisión

**Estado y bloqueo** (`scripts/core/state.py`)
- `status.json` se normaliza al leer y se escribe con temporal único, fsync y reemplazo atómico.
  Las consultas no escriben.
- Bloqueo por pieza del sistema operativo, no bloqueante («pieza ocupada»). Los subprocesos de
  `bin/edit` lo heredan con descriptor y token comprobados, y registran su grupo POSIX: la pieza
  sigue ocupada mientras viva un trabajador. Windows nativo rechaza la ejecución delegada (usar WSL).

**Etapas** (`scripts/core/stages.py`, `scripts/core/integrity.py`)
- Una tabla única declara por etapa su script, si es editable a mano, de qué depende y qué produce.
- Cada etapa terminada deja un recibo (versión 3: plataformas, huella de entradas y de salidas). Las
  editables (ingesta, transcripción, corte en papel, subtítulos) solo se rehacen si cambian sus fuentes:
  una corrección a mano no es caché corrupta.
- Las editables dependen del contenido de la pieza y de lo que el canal les aporta (vocabulario, idioma,
  marca para subtítulos), no del código del motor. Las derivadas incluyen el código del motor que las
  produce y las dependencias de npm (no la versión del propio VideoVibe).
- La transcripción del master guarda la huella del corte que la produjo; con otro corte se transcribe
  de nuevo y la anterior se conserva. Antes de volver a transcribir las tomas se copia `transcript/`.

**Huellas** — SHA-256 del contenido, con cada archivo identificado por una etiqueta relativa
(`piece:`, `channel:`, `engine:`, `ext:`), nunca por su ruta absoluta.

**Aprobaciones**
- A y B guardan versión, huella de entradas y huella de la presentación que vio la persona.
  A: corte, tomas y transcripción. B: contenido de la pieza + HTML compilado, sin código del motor
  (si el motor cambia lo que se ve, cambia el HTML y B se invalida sola).
- Aprobar exige una revisión presentada vigente. Ajustar o rechazar invalida. Presentar o aprobar A no
  borra B: B se valida con su propia evidencia.
- B exige además recibos vigentes de composición y preview, y el control visual al día.
- Aprobaciones anteriores a v0.13.1: se conservan como historia y requieren revisión, salvo que su
  revisión guardada coincida con la presentación actual; entonces, con confirmación de la persona,
  `bin/status --attest-legacy A|B` deja constancia.

**Render y entrega**
- Cada render final se escribe a temporal y se promueve solo si B y sus entradas siguen iguales; sus
  bytes se registran por plataforma para reutilizarlo.
- La entrega exige verificación (`verify.py`) y aprobaciones vigentes. Se prepara en temporal y se
  promueve a `deliveries/<Canal>/<pieza>/versions/<huella>/` (copias independientes, manifiesto con
  hashes, recibo de verificación y aprobaciones); `current.json` apunta a la vigente. Una versión
  previa no se modifica; una alterada no se reutiliza.

**Migración y retiro**
- `integrity.restamp` convierte la evidencia de esquemas anteriores (1: sha1 por tamaño; 2: rutas
  absolutas) recalculándola con su algoritmo original; si coincide, se reemplaza. Piezas sin recibos
  reciben recibo en las etapas que la lógica anterior daba por buenas, salvo la composición, que se
  reconstruye. `bin/edit` la aplica al reanudar; `bin/status --migrate --apply` la aplica a todas.
- `migrate_deliveries` desacopla enlaces duros antiguos sin cambiar bytes; no certifica su historia.
- **v0.15** retira los esquemas 1 y 2, `scripts/core/legacy/` y la decisión sin recibos.

## Alternativas descartadas

- Esperar indefinidamente un bloqueo: oculta conflictos; se prefiere «pieza ocupada».
- Incluir el código del motor en B y en las etapas editables: invalidaba aprobaciones y transcripciones
  en cada actualización sin cambiar lo que se ve.
- Rutas absolutas en las huellas: mover la carpeta de canales invalidaba todo.
- Reconstruir certezas sobre entregas antiguas: no es posible; la migración preserva bytes, no historia.

## Consecuencias

- Una pieza no avanza si su evidencia no coincide; el motivo se muestra en `bin/edit --plan`.
- Actualizar el motor recompone (barato y determinista) pero no repite revisiones si el HTML no cambia.
- Cada entrega nueva ocupa su propia copia en disco.
