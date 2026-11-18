# Decisiones técnicas (ADR)

Una página por decisión: contexto, decisión, alternativas descartadas y consecuencias. Antes de
cambiar algo que una decisión cubre, léela; si la cambias, escribe una decisión nueva que la
reemplace (y marca la vieja como «Reemplazada por NNNN»).

| # | Decisión | Estado |
|---|---|---|
| 0001 | [Lógica en scripts deterministas; los agentes los operan](0001-deterministic-scripts.md) | vigente |
| 0002 | [Transcribir tramo por tramo](0002-chunked-transcription.md) | vigente |
| 0003 | [HDR (HLG/PQ) → SDR BT.709 con curva hable](0003-hdr-to-sdr.md) | vigente |
| 0004 | [HyperFrames para composición y render](0004-hyperframes.md) | vigente |
| 0005 | [Variantes por plataforma como variables de una sola composición](0005-variants-as-variables.md) | vigente |
| 0006 | [Motor separado de los canales](0006-engine-and-channels.md) | vigente |
| 0007 | [Orquestador idempotente con pausas (`bin/edit`)](0007-orchestrator-with-pauses.md) | vigente |
| 0008 | [Sonido: música con licencia por canal y efectos sintetizados propios](0008-audio.md) | vigente |
| 0009 | [Música distinta para la versión de anuncio](0009-music-for-ads.md) | vigente |
| 0010 | [Tratamiento de voz medido, con filtros clásicos](0010-voice-processing.md) | vigente |
| 0011 | [Sonido del canal declarado en archivos (recetas e identidad musical)](0011-declarative-channel-audio.md) | vigente |
| 0012 | [Audios aportados por la persona y micrófono externo](0012-provided-audio-and-microphone.md) | vigente |
| 0013 | [Storyboard validado antes de componer; compose dividido; audio en un solo módulo](0013-validation-and-modules.md) | vigente |
| 0014 | [Insertos visuales desde el storyboard](0014-visual-inserts.md) | vigente |
| 0015 | [Regiones fijas de pantalla para video vertical](0015-screen-regions.md) | vigente |
| 0016 | [Pruebas de voz dependientes del entorno](0016-sandbox-voice-tests.md) | vigente |
| 0017 | [Revisiones guiadas y apertura de archivos](0017-guided-reviews.md) | vigente |
| 0018 | [Carpetas `input/` y `deliveries/` en la raíz](0018-input-and-delivery-folders.md) | vigente |
| 0019 | [Paquetes del motor y nombres del sistema en inglés](0019-packages-and-english-paths.md) | vigente |
| 0020 | [Formatos PixiJS deterministas](0020-pixi-deterministic-formats.md) | vigente |
| 0021 | [Alineación de subtítulos contra el master final](0021-final-master-caption-alignment.md) | vigente |
| 0022 | [Librerías de animación opcionales y un solo reloj por escena](0022-optional-animation-libraries.md) | vigente |
| 0023 | [Animaciones Lottie: bibliotecas con licencia, datos locales y color de marca](0023-lottie-libraries.md) | vigente |
| 0024 | [Moléculas 3D con 3Dmol.js: vista absoluta por cuadro, superficies con espera y datos locales](0024-molecular-structures.md) | vigente |
| 0025 | [Efectos sobre la toma: recorte local de la persona y capas dentro de la cámara](0025-effects-on-footage.md) | vigente |
| 0026 | [Efectos al ritmo: rejilla de la biblioteca, fase por ataques y envoltura de cámara](0026-beats.md) | vigente |
| 0027 | [3D cinematográfico: Three.js empaquetado localmente, un solo reloj y biblioteca de modelos](0027-cinematic-3d.md) | vigente |
| 0028 | [Transiciones de superposición: una capa propia, solo CSS + GSAP y el máximo en el corte](0028-transitions.md) | vigente |
| 0029 | [Iconos científicos CC0, pizarrón con Rough.js y gráficas con d3](0029-scientific-icons-sketch-data.md) | vigente |
| 0030 | [Perfiles versionados, composición compartida y revisión visual](0030-animation-direction.md) | vigente |
| 0031 | [Criterio editorial compartido y skills de entrada](0031-editorial-skills.md) | vigente |
| 0032 | [Lectura por elemento y sustituciones conservadoras](0032-visual-reading-and-cutout-fallbacks.md) | vigente |
| 0033 | [Estado de revisión y propuestas editoriales](0033-editorial-review-state.md) | vigente |
| 0034 | [Extractos audiovisuales breves](0034-media-excerpts.md) | vigente |
| 0035 | [Audio nativo de B-roll y revisión editorial previa](0035-native-broll-audio.md) | vigente |
| 0036 | [Estado, evidencia de aprobación y entregas independientes](0036-integrity-state-and-deliveries.md) | vigente |
