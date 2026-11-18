---
name: edit-video
description: Edita videos verticales (TikTok, Instagram Reels, X) de cualquier canal del sistema VideoVibe, o da de alta un canal nuevo. Úsala cuando la persona entregue material crudo (tomas a cámara, pantalla, B-roll, voz en off) y pida cortar, subtitular, animar, crear variantes por plataforma, copy, portadas o clips; cuando pida crear un canal; o cuando diga "guarda esto en el sistema".
---

# Editar video (VideoVibe)

Esta skill es un atajo. La fuente de verdad está en la raíz del repo:

0. Corre `bin/welcome`. Si no dice `listo`, sigue `docs/getting-started.md` primero.
1. Lee `AGENTS.md` y `docs/status/STATUS.md`. Sigue la tabla «Qué leer según la tarea».
2. Identifica el canal (`channels/<canal>/`). Si no existe y la persona quiere uno nuevo: `docs/channels.md`.
3. Pieza nueva: `bin/new-piece <canal> <slug> --from <archivos>` (la crea en la carpeta de canales correcta,
   copia el material a `raw/` y deja `brief.md`). Completa el brief preguntándole a la persona los campos ★:
   `bin/edit` no avanza sin ellos.
4. Para una pieza nueva, prepara primero el corte según `docs/editorial.md`: usa `bin/edit <canal>/<pieza> --until-stage corte-en-papel`, revisa la narrativa y refresca la vista tras editar decisiones. Después corre `bin/edit <canal>/<pieza>` y haz lo que pida en cada pausa (revisión A, storyboard,
   revisión B, copy/portada). En A/B, presenta el resumen y las preguntas que devuelve; los archivos
   se abren automáticamente y sus rutas quedan visibles. Para cualquier otro archivo que la persona
   deba revisar, usa `bin/open-review <archivo> [<archivo>…]`. Registra las aprobaciones explícitas con
   `bin/status <canal>/<pieza> --approve A|B` y vuelve a correr `bin/edit`. Al escribir el
   storyboard (valídalo con `scripts/pipeline/storyboard.py`; prefiere los formatos «probado» de
   `bin/format-catalog --usage`), música y efectos según `docs/audio.md` (la música depende de «¿Publicidad pagada?»).
5. Termina cuando `bin/edit` diga «ENTREGABLE» (verificación de entrega en verde).

## Dirección de animaciones

Antes de elegir animaciones consulta `docs/animation-direction.md`. Para un canal nuevo o un cambio
de estilo explícito, presenta dos alternativas y guarda solo la elección confirmada. En una propuesta
nueva revisa primero `--snapshot --dry-run`, y fija el perfil con `bin/animation-style --channel <canal> --project <pieza> --snapshot`.
Inspecciona el informe y cuadros de calidad, abre el preview y conserva la revisión B de cuatro preguntas.
No cambies perfiles ni storyboards ya aprobados sin una solicitud de la persona.

## Criterio editorial

Guiones o historias nuevas: `docs/storytelling.md`. Cortes, continuidad, plan visual y copy: `docs/editorial.md`.
Los planes narrativos son auxiliares opcionales. No replantees una pieza por una corrección puntual.

## Fiabilidad de recortes

Para una propuesta con `fx`, sigue `docs/effects.md → Inspección y alternativas automáticas`:
prepara evidencia con `scripts.tools.cutout_review`, examina originales, contraste y composición,
registra el dictamen y aplica las sustituciones de defectuosos/inciertos sin otra pregunta.
Recompón y repite QA; presenta los cambios en la revisión B existente. No marques usable por
estadísticas de máscara o por render correcto. No reproceses una pieza aprobada sin solicitud.

Consulta aprobaciones con `bin/status`; evita duplicarlas en la prosa del plan. Al cambiar brief,
fuentes o corte, revisa sus referencias según `docs/editorial.md`.

Antes de componer una propuesta visual nueva, aplica «Antes del primer preview: revisión editorial con evidencia»
de `docs/editorial.md`: promesa, desarrollo, función de recursos y cierre; busca alternativas reales y
registra correcciones en work/editorial-evaluation.md. Contrasta con el preview antes de B.
No añade gates ni modifica piezas aprobadas por iniciativa propia.
