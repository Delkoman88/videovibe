# 0004 — HyperFrames para composición y render

**Contexto.** Hacen falta subtítulos animados palabra por palabra, tarjetas, animaciones ilustrativas y render reproducible, local y sin costo por render. El ffmpeg de Homebrew no trae libass ni drawtext.
**Decisión.** HyperFrames (HeyGen, Apache-2.0), versión fijada en `package.json`: HTML/CSS/GSAP renderizado cuadro a cuadro. `compose.py` genera el proyecto en `<pieza>/hf/`; también se puede abrir en la app de escritorio de HyperFrames.
**Descartado.** ASS/drawtext en ffmpeg (estilo limitado); OpenChatCut/Remotion como motor (menos control desde scripts).
**Consecuencias.** Hay que seguir el contrato de HyperFrames (`hyperframes check` sin errores antes de renderizar). La corrección de color va por `hyperframes media-treatment`, no CSS. GSAP se sirve local (`assets/vendor/`).
