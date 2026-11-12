# 0017 — Revisiones guiadas y apertura de archivos

**Fecha:** 2026-11-12 · **Estado:** vigente

## Contexto

Mostrar la ruta de un storyboard, una hoja o un borrador dejaba a la persona con trabajo de localizar
archivos y sin preguntas concretas para decidir. Además, `bin/status --approve` no comprobaba que se
hubiera presentado la versión que se aprobaba.

## Decisión

Al pausar en A o B, `bin/edit` presenta un resumen de una pantalla, cuatro preguntas y todos los
archivos necesarios para revisar. Los abre con el visor local y siempre muestra rutas absolutas.
`bin/review` permite repetir la presentación y registrar ajustes o rechazo; `bin/open-review` sirve
para cualquier otro archivo solicitado al usuario. Sin interfaz gráfica, se muestran rutas y motivo,
y la persona puede revisar manualmente.

Cada presentación guarda en `status.json` una huella del contenido aprobado, fecha, rutas y resultados
de apertura. `bin/status --approve` solo acepta una revisión vigente, sin decisión previa de ajustar
o rechazar. Una aprobación global explícita basta; las preguntas orientan, no son un formulario.
La demo registra revisiones simuladas, sin abrir visores. Las aprobaciones antiguas siguen siendo
válidas y no se migran.
