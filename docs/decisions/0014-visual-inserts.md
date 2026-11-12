# 0014 — Insertos visuales desde el storyboard

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto

La ingesta ya clasifica videos sin audio como `broll` y videos horizontales con audio como
`pantalla`, pero el corte hablado usa tomas `camara`. Hacía falta mostrar esas fuentes en una
pieza sin alterar su voz, sus subtítulos ni la aprobación A.

## Decisión

`storyboard.json → broll` declara cada inserto con tiempos del master (`in`, `out`), comienzo
del archivo fuente (`source_in`) y ajuste vertical (`fit`, `focus_x`, `focus_y`). `source` refiere
al id de `media.json`, y se aceptan videos `broll` y `pantalla`. No se mezclan sus audios: la
voz aprobada continúa en la placa. El compositor convierte las fuentes usadas a H.264 SDR y
las monta como videos mudos encima de la cámara, antes de las gráficas y subtítulos. El agente
registra origen, licencia y permiso para anuncios en cada inserto; `compose.py` copia esos
datos a `assets.md`. Los insertos no se solapan, para que el resultado sea inequívoco.

## Consecuencias

La aprobación B y la huella de render cubren estos insertos. Una pieza sin insertos conserva la
huella anterior (`editlib.hf_fingerprint`), para que las piezas ya aprobadas no se re-verifiquen. Si cambia `media.json`, el
orquestador recompone. La variante `cover` recorta al lienzo vertical y deja elegir el punto
focal; `contain` conserva toda la pantalla con fondo. La pantalla como fuente hablada, y el
audio de una captura, quedan para una extensión posterior.

## Validación con material real

Una fuente HEVC HDR 3840×2160 y una captura H.264 de Terminal se combinaron en una prueba técnica
de 8 s. `scripts/pipeline/storyboard.py` y `hyperframes check` terminaron sin problemas; el borrador
resultó H.264 1080×1920, BT.709, con audio de la placa durante los dos insertos. La revisión
visual mostró que `contain` conserva toda la Terminal, pero el texto queda demasiado pequeño
para leerse en un teléfono: falta un encuadre de detalle para capturas horizontales.
