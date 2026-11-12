# VideoVibe — instrucciones para agentes

Motor de edición de video vertical (TikTok, Reels, X; YouTube después) para **varios canales**.
Este archivo es la entrada canónica para cualquier agente CLI (Codex, Claude Code, Gemini CLI,
Muse Code u otro). `CLAUDE.md` y `GEMINI.md` solo lo importan: **no dupliques reglas en otros
archivos de agente.**

## Al empezar una sesión

**Antes que nada: `bin/welcome`.** Dice en qué etapa está la persona (`instalar`, `crear-canal`,
`completar-canal`, `primera-pieza` o `listo`). Si no es `listo`, sigue **`docs/getting-started.md`** antes
de lo que te hayan pedido (si pidieron algo concreto, retómalo al terminar). Si es `listo`:

Los canales de cada persona pueden vivir fuera del repo (repo privado): la carpeta sale de
`$VIDEOVIBE_CHANNELS` o de `local.json → channels_dir` (si no, `channels/`). `bin/doctor` dice cuál se usa.

1. Lee `docs/status/STATUS.md`: qué funciona hoy, limitaciones y versiones.
2. Si vas a trabajar en una pieza: `bin/status <canal>/<pieza>` (etapa, aprobaciones, renders).
3. Primera sesión en esta máquina: `bin/doctor` (si falta algo: `bin/setup`, ver `INSTALL.es.md`) y
   `bin/doctor --channel <canal>`.

## Qué leer según la tarea (no leas todo)

| Tarea | Lee |
|---|---|
| Primera vez, canal nuevo o persona que no conoce el sistema | `bin/welcome` + `docs/getting-started.md` |
| Editar una pieza de un canal | Pieza nueva: `bin/new-piece <canal> <slug> --from <archivos>` (la crea donde viven los canales, con `raw/` y `brief.md`). Después `bin/edit <canal>/<pieza>` y haz lo que indique al pausar. Antes de decisiones creativas: `channels/<canal>/CHANNEL.md`, `style.md`, `rhythm.md`, `learnings.md`. Detalle: `docs/pipeline.md` |
| Escribir el plan visual (storyboard) | `docs/storyboard.md` + `docs/formats.md` (+ `brand.json` del canal) |
| Sonido (voz, música, efectos) | `docs/audio.md` |
| Adaptar a una plataforma | `presets/<plataforma>.json` + `docs/platforms.md` |
| Dar de alta un canal | `docs/channels.md` + `templates/channel-brief.md` |
| Cambiar el motor (scripts, formatos) | `docs/status/` (backlog, roadmap) + `docs/decisions/` antes de tocar nada |
| Conectores, otros agentes, instalación | `docs/connectors.md`, `docs/agents.md`, `INSTALL.es.md` |

## Reglas universales (ningún canal ni pieza las cambia)

1. **Pregunta antes de inventar.** Sin `brief.md` completo de la pieza (objetivo, audiencia,
   material, llamada a la acción), haz las preguntas de `templates/brief.md` antes de decidir nada creativo.
2. **Dos revisiones humanas por pieza:** A (el corte) y B (el plan visual). Regístralas con
   `bin/status <canal>/<pieza> --approve A|B` solo después de que `bin/edit` presente la revisión guiada
   (resumen, archivos abiertos y 3–5 preguntas) y la persona apruebe explícitamente. Si pide cambios,
   aplícalos y vuelve a presentar la revisión. Nada de render final sin B.
3. **Identidad intacta de quien aparece.** Solo corrección natural de color, luz y contraste. Nunca
   filtros de belleza, cambios de rasgos, regeneración facial ni desincronizar labios. En la voz:
   solo limpieza, ecualización y dinámica; nunca cambiar tono, timbre ni palabras.
4. **La lógica vive en `scripts/` y `formats/`.** Cortes, tiempos, render y verificación con scripts
   deterministas (`--help`, salida JSON). Si falta una herramienta, créala y documéntala.
5. **Nada sin derechos.** Música, efectos, imágenes y fuentes propios o con licencia; regístralo en
   `<pieza>/assets.md`.
6. **No se entrega sin `scripts/pipeline/verify.py` en verde.**
7. **Archivos para revisión:** si necesitas que la persona vea o escuche cualquier archivo, corre
   `bin/open-review <archivo> [<archivo>…]`, muestra sus rutas absolutas y comprueba si se abrieron.
   Si no hay visor, explica el motivo y deja las rutas para apertura manual. Las pausas A/B lo hacen
   automáticamente; `bin/review <pieza> --gate A|B --reopen` vuelve a mostrarlas cuando haga falta.

Las reglas de cada canal (tono, guardarraíles de contenido, estilo) están en su `CHANNEL.md`.
Precedencia: **pieza (brief) > canal > motor**, salvo estas reglas universales.

## Estructura

| Ruta | Contenido |
|---|---|
| `channels/<canal>/` (o la carpeta de `local.json`) | Perfil del canal (`channel.json`, `CHANNEL.md`, `style.md`, `rhythm.md`, `topics.md`, `brand.json`, `vocabulary.txt`, `learnings.md`) y sus piezas en `projects/` |
| `channels/<canal>/projects/<fecha>-<slug>/` | Una pieza: `raw/`, `brief.md`, cortes, `storyboard.json`, `hf/`, `renders/`, `status.json` |
| `input/` | Originales de la persona: deja ahí sus videos; `bin/new-piece … --from <nombre>` los busca ahí (fuera de git) |
| `deliveries/` | Finales verificados por canal y pieza (`deliveries/<Canal>/<fecha> <pieza>/`): enlaces a los renders + portada, texto y `README.md`. Los llena `bin/edit` al entregar; dile siempre a la persona la ruta (fuera de git) |
| `channels/_template/`, `channels/science-60/` | Esqueleto para canales nuevos (`bin/new-channel`) y canal de ejemplo (`bin/demo`) |
| `scripts/` | Paquetes `pipeline/`, `audio/`, `core/`, `composer/`, `validation/`, `tools/`, `tests/`. Pipeline (ver `docs/pipeline.md`). `--project` acepta `<canal>/<pieza>`. `compose.py` orquesta `scripts/composer/` (visual, audio, créditos, placa) |
| `formats/` | Animaciones: `core.py` (genéricas) + `packs/` (temáticas). Catálogo: `docs/formats.md` |
| `lang/` | Paquetes de idioma (muletillas, conectores, reglas de subtítulos, etiquetas) |
| `presets/` | Especificación técnica por plataforma |
| `docs/status/` | Estado del desarrollo: `STATUS.md`, `backlog.md`, `roadmap.md` |
| `docs/decisions/` | Decisiones técnicas (por qué las cosas son como son) |
| `bin/` | `welcome` (en qué etapa está la persona), `setup` (instalación), `demo` (prueba de punta a punta), `new-piece` (pieza nueva), `edit` (orquestador), `review` (revisiones A/B guiadas), `open-review` (abrir archivos para la persona), `status`, `doctor`, `new-channel`, `format-catalog`, `install-agents` |
| `.agents/skills/edit-video/` | Skill (formato abierto SKILL.md); `.claude/skills` apunta aquí |

## «Guarda esto en el sistema»

Clasifica la nota antes de escribirla:
- **Del canal** (gusto, tono, estilo, ritmo de esa persona): regla corta en el archivo del canal al
  que pertenece (`style.md`, `rhythm.md`, `CHANNEL.md`; colores/fuentes en `brand.json`) y una línea
  con fecha en `learnings.md`.
- **Del motor** (un fallo, una herramienta, una técnica que sirve a todos los canales): en `docs/`
  o en el código, con test si aplica, y una entrada en `docs/status/backlog.md` si queda trabajo.
- Si contradice una regla anterior, **reemplázala**; nunca dejes ambas. Anota el cambio en `CHANGELOG.md`.

## Al terminar una sesión de desarrollo del motor

Actualiza `docs/status/STATUS.md` (si cambió lo que funciona), `docs/status/backlog.md` (hecho/nuevo),
`CHANGELOG.md`, y crea `docs/decisions/NNNN-*.md` si tomaste una decisión técnica. Corre los
tests: `.venv/bin/python -m unittest discover -s scripts/tests`.

## Idioma

Documentación del motor en español. El idioma del contenido lo define cada canal
(`channel.json → language`). Código y nombres definidos por el sistema en inglés: comandos/documentos con guiones, módulos Python
con guiones bajos. Se conservan nombres personales, títulos, originales y códigos de idioma.
Las claves JSON nuevas van en inglés; los valores editoriales existentes conservan su contrato.
Migración de instalaciones anteriores: `docs/migration.md`.
