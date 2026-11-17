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
4. Corre `bin/edit <canal>/<pieza>` y haz lo que pida en cada pausa (revisión A, storyboard,
   revisión B, copy/portada). En A/B, presenta el resumen y las preguntas que devuelve; los archivos
   se abren automáticamente y sus rutas quedan visibles. Para cualquier otro archivo que la persona
   deba revisar, usa `bin/open-review <archivo> [<archivo>…]`. Registra las aprobaciones explícitas con
   `bin/status <canal>/<pieza> --approve A|B` y vuelve a correr `bin/edit`. Al escribir el
   storyboard (valídalo con `scripts/pipeline/storyboard.py`), música y efectos según `docs/audio.md` (la música depende de «¿Publicidad pagada?»).
5. Termina cuando `bin/edit` diga «ENTREGABLE» (verificación de entrega en verde).

## Dirección de animaciones

Antes de elegir animaciones consulta `docs/animation-direction.md`. Para un canal nuevo o un cambio
de estilo explícito, presenta dos alternativas y guarda solo la elección confirmada. En una propuesta
nueva revisa primero `--snapshot --dry-run`, y fija el perfil con `bin/animation-style --channel <canal> --project <pieza> --snapshot`.
Inspecciona el informe y cuadros de calidad, abre el preview y conserva la revisión B de cuatro preguntas.
No cambies perfiles ni storyboards ya aprobados sin una solicitud de la persona.
