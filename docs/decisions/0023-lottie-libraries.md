# 0023 — Animaciones Lottie: bibliotecas con licencia, datos locales y color de marca

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Queremos animaciones de diseñador (After Effects, LottieFiles, Rive) sin perder tres garantías del motor:
render sin red y determinista, derechos registrados de todo lo que sale en pantalla y la identidad de cada
canal.

## Decisión

1. **Bibliotecas por tipo** (`scripts/core/assetlib.py`), con el modelo de la música: `library.json` con
   origen, licencia y permiso de anuncios; motor (`assets/<tipo>/`) y canal (`<canal>/assets/<tipo>/`), el
   canal gana si repite un id. Sin licencia no se usa; con plataforma `ads`, solo lo marcado `ads: true`.
2. **Recursos declarados por el formato**: `@fmt(..., uses=lambda p: [("lottie", p["anim"])])`. Con eso:
   - la validación del storyboard revisa existencia, licencia y anuncios, con los demás errores;
   - `scripts/composer/data.py` sirve cada recurso como `hf/assets/data/<tipo>-<id>.js` (define
     `window.__vv["<tipo>:<id>"]`), sin `fetch`, y borra lo que sobra;
   - `assets.md` registra cada recurso usado (bloque automático `animations:auto`).
   El mismo mecanismo servirá a las estructuras moleculares (fase 3).
3. **Un solo reloj** (ADR 0022): `lottie-web` 5.13.0 (render SVG) se renombra al cargar (`__vvLottie`) para
   que el adaptador de HyperFrames no la mueva; la escena llama `goToAndStop(cuadro, true)` desde su línea de
   tiempo. Tramos (`from`/`to`), velocidad y repeticiones (`loops`, `"fill"`) se calculan del tiempo local.
4. **Color de marca sin tocar el archivo**: la biblioteca guarda un mapa `{color → rol}` o `"auto"`
   (`scripts/core/lottielib.py`); se aplica al servir los datos con `brand.json` del canal. La misma
   animación se ve distinta en cada canal y el original queda intacto.
5. **Animaciones propias del motor** generadas por código (`scripts/tools/lottie_builtins.py`, Apache-2.0):
   reproducibles, con colores «marcadores» mapeados a los acentos.

## Consecuencias

- `scripts/tools/lottie.py add|list|recolor|preview` es la puerta de entrada; rechaza imágenes externas y
  capas de texto con fuentes (no funcionarían sin red o cambiarían de aspecto).
- Los degradados de Lottie no se recolorean (se conservan); si estorban, el mapa manual no los cubre y hay
  que pedir la animación sin degradados.
- Activar un paquete en `channel.json` marca las piezas para recomponer; si el HTML no cambia, aprobaciones y
  renders siguen válidos.
