# 0015 — Regiones fijas de pantalla para video vertical

**Fecha:** 2026-11-12 · **Estado:** vigente

## Contexto

La prueba real mostró que `contain` conserva una Terminal horizontal completa, pero su texto
queda demasiado pequeño en 9:16. Un recorte centrado tampoco indica qué zona importa.

## Decisión

`broll[].fit = "region"` acepta un rectángulo `{x,y,w,h}` proporcional al video fuente. Cada
inserto mantiene una región fija y dos insertos consecutivos cambian de región por corte directo.
El video se amplía sin deformarlo; si el rectángulo tiene otra proporción que 9:16 se recorta
desde el centro de esa región. `cover` y `contain` siguen intactos. La fuente conserva su tiempo
con `source_in` y su audio permanece mudo.

La revisión B extrae del borrador un cuadro 360×640 por inserto. Una captura horizontal mostrada
completa con reducción fuerte produce un aviso calculado por escala; no bloquea el render porque
el tamaño de las letras de la fuente no se conoce sin OCR. La persona decide la legibilidad en B.

## Consecuencias

El storyboard valida que la región tenga área positiva y quede dentro de la fuente. No se añade
OCR ni una dependencia nueva. El comportamiento de piezas antiguas no cambia.

## Validación real

La captura de Terminal se mostró completa durante 0.5 s y luego en dos regiones fijas de detalle.
`storyboard.py` emitió solo el aviso esperado para la vista completa; `hyperframes check` terminó
con 0 errores y 0 avisos, y el borrador de 8 s mostró texto más grande en cuadros de 360×640.
