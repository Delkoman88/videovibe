---
name: storytelling
description: Prepara guiones y estructuras narrativas de VideoVibe antes de grabar, o identifica una historia fiel en material grabado. Úsala para ideas, ganchos, progresión y cierre; una corrección técnica puntual no requiere replantear la historia.
---

# Storytelling para VideoVibe

Entrada del proyecto: lee `AGENTS.md`, corre `bin/welcome` y consulta el estado del motor.
Antes de proponer contenido, completa el brief con lo que falte y lee identidad, estilo, ritmo y
aprendizajes del canal. El idioma del contenido lo define el canal.

Sigue `docs/storytelling.md`, la fuente canónica de criterios y entregables:
- Antes de grabar: `story-plan.md` y `script.md` dentro de la pieza. Se puede crear con
  `bin/new-piece <canal> <slug>` sin originales. Declara el material como previsto; no ejecutes
  `bin/edit` hasta contar con material real.
- Con grabación: plan basado en fuentes y líneas reales, conservando orden y significado.
  Para ejecutar la edición, sigue `docs/editorial.md` y el flujo de `edit-video`.
- Con guion o estructura aportados: desarrolla lo solicitado sin reemplazar su intención.

No hay una aprobación adicional de storytelling. Presenta la recomendación en la terminal;
si solicitas revisar un archivo, usa `bin/open-review` y muestra su ruta absoluta.
Las revisiones de producción siguen en A y B. No inventes evidencias ni permisos.

Consulta aprobaciones con `bin/status`; evita duplicarlas en la prosa del plan. Al cambiar brief,
fuentes o corte, revisa sus referencias según `docs/editorial.md`.

Antes de componer una propuesta visual nueva, aplica «Antes del primer preview: revisión editorial con evidencia»
de `docs/editorial.md`: promesa, desarrollo, función de recursos y cierre; busca alternativas reales y
registra correcciones en work/editorial-evaluation.md. Contrasta con el preview antes de B.
No añade gates ni modifica piezas aprobadas por iniciativa propia.
