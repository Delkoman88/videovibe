# 0018 — Carpetas `input/` y `deliveries/` en la raíz

**Fecha:** 2026-11-12 · **Estado:** vigente

## Contexto
Usando VideoVibe, los videos finales quedaban en `<canales>/<canal>/projects/<pieza>/renders/`, difíciles de
encontrar (más aún con los canales en otra carpeta). Y no había un lugar obvio donde dejar los originales.

## Decisión
- **`deliveries/<Nombre del canal>/<AAAA-MM-DD> <pieza>/`** en la raíz del repo (`$VIDEOVIBE_DELIVERIES` o
  `local.json → deliveries_dir` para cambiarla). Por plataforma: `<plat>.mp4`, `<plat> - cover.jpg`,
  `<plat> - copy.md`; más `subtitles.srt` y `README.md` (archivos, texto para publicar, licencia del sonido).
  Una carpeta por pieza, sin nivel de mes (decisión de la persona).
- Los archivos son **enlaces duros**: no duplican ~200 MB por video y en el explorador son archivos normales
  (a diferencia de los enlaces simbólicos). Si el sistema de archivos no lo permite (otro disco, algunos
  Windows), se **copian**. En ambos casos se informa la ruta absoluta.
- La llena `bin/edit` (`scripts/pipeline/deliver.py`) solo después de `verify.py` en verde, y la abre en el explorador
  (`open`, `xdg-open` u `os.startfile` en Windows). Se rehace en cada nueva entrega; quita plataformas que ya
  no forman parte de la pieza.
- **`input/`** en la raíz (`$VIDEOVIBE_MATERIAL` o `local.json → material_dir`): la persona deja ahí sus
  originales; `bin/new-piece --from` acepta solo el nombre del archivo o una carpeta, y si no lo encuentra
  lista lo que hay. El agente pregunta carpeta y nombre del archivo, o sugiere `input/`.
- Ambas carpetas están fuera de git (solo su `README.md` se versiona).

## Consecuencias
- Un render nuevo crea un archivo nuevo en la pieza: el enlace viejo apuntaría al anterior, por eso la carpeta
  se rehace en cada entrega (y `bin/edit` la recrea si falta).
- Con enlaces duros, borrar la pieza no borra el video de `deliveries/` (y viceversa): el espacio se libera al
  borrar ambos.

Actualización de rutas y organización: [ADR 0019](0019-packages-and-english-paths.md).
