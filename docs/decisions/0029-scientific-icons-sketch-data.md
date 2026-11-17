# 0029 — Iconos científicos CC0, pizarrón con Rough.js y gráficas con d3

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Faltaban tres estilos para divulgación científica: iconografía de biología y salud (Lucide es genérico),
dibujo a mano (pizarrón) y gráficas con datos reales. Mismas reglas: opcional, sin red, determinista, con la
marca del canal y con los derechos registrados.

## Decisión

1. **Iconos: Health Icons y Bioicons, solo CC0.** Health Icons es CC0 en sus íconos (el plan suponía MIT; su
   LICENSE lo aclara). Bioicons asigna licencia por carpeta (CC0, CC BY, CC BY-SA, BSD, MIT): el motor solo
   incluye la carpeta CC0, así ninguna pieza queda debiendo atribución ni hereda share-alike. Selecciones
   versionadas (`formats/icons/selection-*.txt`), descarga en un commit fijado (`scripts/tools/icons.py --sets`).
   - Limpieza obligatoria para HTML en línea: estilos de clase (`.st0{…}`) pasados a cada elemento (si no, se
     aplican a toda la página), ids con prefijo propio, sin metadatos de Inkscape/Illustrator; Health Icons pasa
     su gris a `currentColor`. Descartados: > 80 KB (dibujos calcados), negros o con recuadro blanco (no se ven
     sobre fondo oscuro). Quedan 68 de Health Icons y 44 de Bioicons.
   - Prefijos `health:` y `bio:` en la misma API (`formats/icons`): sirven donde ya servía Lucide.
     `morph-icon` solo acepta Lucide (necesita trazos). Créditos de cada icono usado en `assets.md` aunque sea CC0.
2. **Pizarrón: Rough.js 4.6.6 (MIT)** en el navegador con semilla fija por escena: los trazos se generan al
   construir la escena y DrawSVG los dibuja desde la línea de tiempo. Los colores se leen de las variables de
   la marca (los atributos SVG no aceptan `var()`).
3. **Gráficas: d3 7.9.0 (ISC)** solo calcula: escalas con números redondos (`nice`), ejes, `curveMonotoneX`.
   GSAP anima (barras con `scaleY`, línea con DrawSVG, números que cuentan con `onUpdate` desde el valor del
   tween). 7.9.0 y no 7.9.2: la última tenía 14 días, en el límite de la regla de dos semanas.
   - Datos en el storyboard o en `<pieza>/data/*.csv|json` (`formats.CTX["piece_dir"]`, lo fija compose y la
     validación). **`source` obligatorio**; `illustrative` para datos que no son reales.

## Lecciones

- En elementos SVG, GSAP ignora `transform-origin` de CSS: el origen va en el tween (`transformOrigin`). La
  galería no lo mostró (captura el estado final); se vio en el render de una pieza: revisar cuadros intermedios.
- Un `<div>` opaco de pantalla completa como fondo hace que el revisor de HyperFrames marque el texto como
  tapado (`text_occluded`) en los primeros cuadros: usar el fondo de la escena (`wrap`) en vez de otra capa.
- `*palabra*` en títulos resalta una sola palabra.

## Consecuencias

- Paquetes `sketch` y `data` opcionales por canal (`format_packs`); sin ellos, nada cambia.
- `lab-network` acepta iconos de cualquier conjunto (su salida con los iconos propios no cambia).
