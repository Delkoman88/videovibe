# 0033 — Estado de revisión y propuestas editoriales

`status.json` y las comprobaciones de vigencia del pipeline son la autoridad de aprobación.
La prosa narrativa no almacena una segunda copia de ese estado. No se reescriben automáticamente
planes antiguos; sus referencias se revisan al cambiar entradas editoriales.

La aprobación limpia exclusivamente su propio pendiente; avanzar de etapa sin pausa limpia el
pendiente anterior. Se mantiene el historial y las consultas son de solo lectura.

Las preguntas de contenido se pueden adaptar por pieza mediante `review-questions.json`.
La decisión final permanece obligatoria; las preguntas de cada gate forman parte de su huella.
Sin archivo se conserva la huella anterior para evitar invalidaciones innecesarias.
No se agregan gates ni migraciones globales. La evaluación editorial separa juicio del agente,
respuesta de la persona y resultados técnicos; no demuestra retención.
