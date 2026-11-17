# 0020 — Formatos PixiJS deterministas

**Fecha:** 2026-11-16 · **Estado:** vigente

## Decisión

Los paquetes temáticos pueden usar PixiJS y `pixi-filters` para visuales que necesiten canvas,
bloom, separación RGB, glitch o pixelado. El motor fija las dependencias en `package.json`, las
copia dentro de cada proyecto HyperFrames y no requiere red durante composición o render.

Los archivos de Pixi incluidos por terceros contienen llamadas internas a `Math.random()`, aunque
el formato no solicite azar. Al empaquetarlos, `compose.py` redirige esas llamadas a un generador
xorshift con semilla fija declarado antes de cargar Pixi. Así, HyperFrames puede buscar cualquier
cuadro de forma reproducible y `StaticGuard` no bloquea la composición.

Las fuentes pixel se incorporan como archivos locales con su licencia. Para subtítulos, el cuerpo
permanece blanco y opaco entre palabras; solo la palabra activa cambia de color, escala y glow/RGB
split. Esto mantiene la lectura móvil y evita depender de variables CSS dentro de tweens GSAP.

## Opcional por canal (2026-11-17)

Nada de esto cambia los canales que no lo piden:
- Un formato declara sus librerías con `@fmt(..., needs=("pixi",))`. `compose.py` copia Pixi y el
  generador fijo en `index.html` solo si alguna escena del storyboard usa uno de esos formatos.
- Los subtítulos neón y las tarjetas «liquid» son estilos que el canal elige en `brand.json`
  (`captions.style: "neon"`, `overlays.style: "liquid"`). Sin esas claves, el HTML es el mismo de antes.
- Las versiones de PixiJS y pixi-filters van fijadas exactas en `package.json`, como GSAP.

## Consecuencias

- Los formatos Pixi funcionan sin CDN y pueden renderizar en WSL mediante WebGL por software.
- El render por CPU en WSL es más lento; no se cambia la configuración del usuario ni sus grupos.
- Toda dependencia visual nueva que use azar debe pasar por el mismo empaquetado determinista.
- Actualizar HyperFrames o Pixi requiere volver a ejecutar la suite y una revisión B real.

## Validación

`hyperframes check` 0.9.32: cero errores de lint, runtime, layout, motion y audio sobre la primera
pieza de un canal de DJ (Windows/WSL). Cinco capturas puntuales y el borrador completo muestran las dos escenas Pixi, los
subtítulos Pixelify y el inserto de actuación. Suite completa: 128 pruebas en verde, 15 omitidas por
audio de sistema no disponible en este entorno.
