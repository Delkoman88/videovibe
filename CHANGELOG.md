# Changelog

## 0.13.0-alpha — 2026-11-17

### revisión editorial previa y audio nativo de B-roll

- Procedimiento previo al preview con evidencia de promesa, desarrollo, recursos y cierre; sin gates nuevos.
- Audio original opcional por inserto: intervalo sincronizado, ganancia, fundidos y atenuación durante voz.
- Extracción sin kit SFX ni límite de cuatro segundos; caché y huellas por contenido. Compatibilidad muda por defecto.
- ADR 0035; no modifica las entregas aprobadas ni habilita voz de pantalla como corte.
- Validación: 271 tests correctos, sincronía audiovisual dentro de un cuadro y copia real verificada para TikTok/Reels.

### extractos audiovisuales breves

- Herramienta de extracción de video y audio con intervalo/fundidos compartidos, sin sobrescribir originales.
- Cierre con B-roll y sonido aportado sincronizado mediante las capacidades existentes, hasta 4 s.
- Guía y límites documentados; no habilita reordenamiento de diálogo ni voz de pantalla. ADR 0034.
- Tercera propuesta del vlog aprobada explícitamente: contexto inicial, efectos temáticos y cierre
  con sonido original y fundido. Se conservan el corte hablado y los subtítulos.
- Entrega TikTok/Reels verificada, con portadas, textos y subtítulos; carpeta abierta para el usuario.

### estado y evaluación editorial

- Primera evaluación real del usuario: relato comprensible; solicita más contexto inicial, efectos
  relacionados con el tema y cierre menos abrupto. Segunda propuesta presentada con esos ajustes;
  corte y subtítulos conservados. El cierre se ajustó y aprobó en la tercera propuesta.

- Limpieza de pendientes al aprobar o avanzar; consultas de estado sin escritura.
- La ventana de lectura de kinetic-title respeta su salida interna, anterior al fundido de escena.
- Preguntas específicas por pieza, incluidas en la huella de revisión y con decisión final obligatoria.
- Planes narrativos remiten al estado canónico; mantenimiento de referencias sin reescribir propuestas.
- Evaluación real con respuestas del usuario y ajustes registrados; aprobación explícita tras tres propuestas visuales. ADR 0033.

### fiabilidad visual

- QA con ventanas de lectura por elemento; permite revelados y entradas desde fuera del lienzo,
  manteniendo el rechazo de texto truncado al asentarse. Agrupa avisos por causa y fase.
- Subtítulos de hasta 0.32 s sin fundidos de línea, conservando palabras y tiempos.
- `cutout_review` genera evidencia y sustituye efectos defectuosos/inciertos según el dictamen del
  agente: tarjetas, etiquetas o toma original. Conserva A, invalida B y muestra los cambios en B.
- Validación de huellas, archivo del plan previo, ejecución de prueba e idempotencia. Si falta el
  modelo o la composición, mantiene el dictamen incierto; no certifica la calidad de la máscara.
- Regresiones públicas sintéticas y ensayo aislado con material real. Sin nuevo modelo ni gate.
  Guías de efectos, animaciones, storyboard, pipeline y skill reconciliadas; ADR 0032.

### storytelling y criterio editorial

- Skill storytelling para preproducción y material grabado; guías compartidas y copy integrado en edit-video.
- Adaptaciones editoriales con commits de origen fijados, atribución y licencias conservadas.
- paper_cut --refresh-from-cut regenera el documento desde decisiones existentes, sin repetir heurísticas ni alterar aprobaciones.
- Sin reordenamiento de frases, nuevas aprobaciones ni migración de piezas existentes. ADR 0031.
- Prueba técnica con material real: matriz de 108 combinaciones y suite de 252 pruebas correctas.
  Documentados límites del recorte junto a objetos y posible falso positivo de QA durante el
  revelado de letras. Fue evidencia previa a esta corrección; el cambio de modelo sigue pendiente.
  Sin aprobación editorial implícita.

### Dirección de animaciones

La dirección de animaciones v2, previamente disponible en main, queda incluida en esta versión.

- Documentación canónica reconciliada: README en ambos idiomas (36 formatos y estado multicanal),
  contrato de storyboard, pipeline, canales, instalación, recursos e índice completo de ADR.
  Se distingue la validación técnica del upgrade de su adopción editorial y de la portabilidad pendiente.

- Perfiles v2 optativos con controles internos y presupuesto de lectura; compatibilidad exacta del
  HTML legado/v1. Metadatos y candidatos por intención, capacidad y recursos con licencia.
- Secuencias con objetos reutilizables (formas, texto, iconos e imágenes) y anclajes por palabra
  en escenas/pasos. Snapshot validado, diff y escritura atómica antes de invalidar B.
- Previews por ejecución y compositor visual compartido; galería con fragmentos reutilizables.
- QA sobre el runtime real: texto, capas y regiones protegidas, evidencia y huellas vigentes para B.
- Trayectorias y morphs v2 deterministas al buscar cuadros en reversa; matrices renderizadas,
  escenarios de dos marcas y comprobación de instalación limpia. Workflow macOS/Ubuntu preparado.
- Resultados ejecutados y verificaciones pendientes separados en STATUS y ADR 0030.
- Corregida la clasificación del ensayo local: prueba técnica del motor cerrada, sin requerir B
  ni generar una entrega editorial. Se conserva el flujo de aprobación de las piezas de producción.


## 0.12.0-alpha — 2026-11-17

- Documentación reconciliada con la validación confirmada por la persona: segundo canal real (canal de DJ) y entrega verificada desde Ubuntu/WSL completados el 2026-11-16. Se retiran esos pendientes de estado, backlog y roadmap; micrófono externo y otros agentes siguen pendientes.
- **Iconos científicos, pizarrón y gráficas**: Health Icons y Bioicons (solo CC0) como `health:<id>` y `bio:<id>` en todos los formatos con iconos, con créditos automáticos; paquete `sketch` (Rough.js: `sketch-annotate`, `sketch-board`, `sketch-diagram`) y paquete `data` (d3: `chart-bars`, `chart-line`, `chart-compare`, fuente obligatoria, datos en `data/*.csv|json` de la pieza). ADR 0029.
- **Transiciones** (`storyboard.json → transitions`): `flash`, `light-leak`, `scribble`, `word-wall`, `glitch` y `zoom-lines` cubren el corte con el máximo en `at`, en los colores de la marca y con sonido automático del kit; validación de corte cercano y separación ≥ 1.5 s. ADR 0028.
- **3D cinematográfico** (paquete `cinematic`): `particle-word`, `logo-3d`, `cell-journey`, `model-showcase` y `space-field` con Three.js 0.187 + postprocessing 6.39 (bloom, profundidad de campo, viñeta) en los colores de la marca, deterministas. Three se empaqueta localmente con esbuild (huella por versión). Biblioteca de modelos 3D `.glb` (`scripts/tools/models.py add|list|preview`) con origen y licencia; modelo de ejemplo `flask`. ADR 0027.

- Efectos sobre la toma (`storyboard.json → fx`): `text-behind` (texto detrás de la persona, colocado solo
  a la altura de la cabeza), `background-swap`, `subject-glow` y `freeze-cutout` (solo en pausas sin voz).
  La persona se recorta con el modelo local de HyperFrames, solo en los tramos usados y con caché
  (`scripts/pipeline/cutout.py`). Guía: `docs/effects.md`. ADR 0025.
- Recorte estable con cámara fija (`scripts/pipeline/matte.py`): quita lo que parpadea (cortina, silla) sin
  comer el cuerpo, rellena el cuerpo que el modelo pierde unos cuadros o emborrona por movimiento rápido, y el
  halo cierra huecos en el tiempo; opacidad sólida y fundidos más suaves.
- `text-behind` con `depth`: `behind`, `front` o `through` (aparece delante y pasa detrás).
- Corregido: las letras animadas (`motion`, `text_fx`, efectos) podían diferir en el borde según el orden de los
  cuadros por `will-change: transform`; ahora el render es determinista.
- Efectos al ritmo (`storyboard.json → beat_fx`): `pulse`, `shake`, `flash`, `strobe` por golpe o compás.
  `scripts/pipeline/beats.py` ubica los golpes en el tiempo del video (BPM de la biblioteca + fase por ataques,
  ±30 ms; o el audio de la toma). `channel.json → beat_snap` avisa cuando algo no cae en el golpe. ADR 0026.

## 0.11.0-alpha — 2026-11-17

Más y mejores animaciones: de 13 a 24 formatos, todos con la marca de cada canal, validados y deterministas.

- Librerías de animación opcionales en una sola tabla (`formats/vendors.py`): los formatos declaran
  `needs=(...)` y solo se copian y cargan en las piezas que los usan; plugins de GSAP listos
  (SplitText, ScrambleText, DrawSVG, MorphSVG, MotionPath, Physics2D, CustomEase). ADR 0022.
- `bin/format-gallery --channel <id> [--check] [--determinism]`: cada formato renderizado con la marca del
  canal, en hojas de contacto, con chequeo de HyperFrames y prueba de determinismo.
- 77 iconos de Lucide (ISC) para los formatos: `formats.icons.icon("dna", 96)`.
- El catálogo de formatos muestra las librerías de cada formato.
- Nuevo paquete `motion` (activado en la plantilla de canal): `kinetic-title`, `data-reveal`,
  `draw-diagram`, `morph-icon`, `path-journey` y `particle-burst`, con DrawSVG, MorphSVG, MotionPath y
  Physics2D. Toman colores y fuentes de la marca de cada canal.
- Tarjetas con `text_fx` (`rise`, `wave`, `blur`, `mask`): el texto se arma letra por letra.
- Validación por formato (`@fmt(..., check=fn)`): listas, iconos y valores se revisan con el storyboard.
- Guía «qué formato usar para qué» en `docs/storyboard.md`.
- Nuevo paquete `lottie` (activado en la plantilla): `lottie-scene` y `lottie-accent`, con tramos, velocidad
  y repeticiones; las animaciones se recolorean con la marca del canal al componer.
- Bibliotecas de recursos visuales con licencia (`scripts/core/assetlib.py`): motor + canal; validación de
  licencia y anuncios; registro automático en `assets.md`. Guía: `docs/visual-assets.md`. ADR 0023.
- `scripts/tools/lottie.py add|list|recolor|preview` y cuatro animaciones propias (`check-draw`,
  `pulse-rings`, `spark-burst`, `eq-bars`).
- Los formatos pueden declarar recursos (`@fmt(..., uses=...)`), servidos como archivos locales del proyecto.
- Nuevo paquete `molecular` (3Dmol.js 2.5.5): `molecule-spin`, `molecule-focus` (zoom a cadena, residuos o
  ligando con anillo y etiqueta) y `molecule-compare`; colores de marca por cadena, superficies translúcidas.
- `scripts/tools/structures.py fetch --pdb|--pubchem`, `add`, `list`, `preview`; cinco estructuras de ejemplo.
  La validación revisa que la selección de `focus` exista (`@fmt(..., check_items=...)`). ADR 0024.

## 0.10.0-alpha — 2026-11-17

Primera pieza real hecha en Windows (WSL) para un canal de DJ; lo que salió de ahí, integrado al motor.

- Estilos opcionales por canal en `brand.json`: `captions.style: "neon"` (palabra activa con color, escala y separación RGB) y `overlays.style: "liquid"` (tarjetas con vidrio amorfo, órbita, cable y medidor). Sin esas claves todo se ve igual que antes.
- PixiJS 8.23.0 y pixi-filters 6.1.5 (versiones fijas) solo se copian y cargan en piezas cuyas escenas los usan (`@fmt(..., needs=("pixi",))`).
- Storyboards: nuevas `caption_zones` temporales (`upper-left` o `upper-center`) para apartar subtítulos de rostros, manos y equipo.
- El orquestador fuerza un informe nuevo de HyperFrames al verificar; una respuesta desde caché ya no provoca el falso error «check no dejó informe».
- Los cortes con muchos fragmentos toleran la cuantización acumulada a cuadros y el priming declarado por AAC; el mapa adopta la duración reproducible del contenedor para no recortar la última sílaba.
- Subtítulos: una cola de baja confianza puede repararse con las palabras aprobadas del remapeo, conservando el intervalo real observado en el master y sin duplicar la palabra de la costura.
- Subtítulos: el prefijo puede restaurarse desde las líneas aprobadas del corte A sin reemplazar un tramo posterior cuya sincronía ya fue revisada.
- Los insertos pueden sostenerse durante `tail_s`, de modo que una CTA final no revele de nuevo el encuadre base al congelar la última imagen.
- La cola congelada admite hasta 5 s para cierres y CTA que necesiten más aire.
- `bin/edit --platform <nombre>` limita render, verificación y entrega a las plataformas solicitadas sin modificar ni invalidar el storyboard aprobado.
- Subtítulos: se pueden reimportar tiempos por palabra de whisper.cpp sobre el master final para reparar desincronías después de un cambio de corte.
- Las revisiones abiertas desde Ubuntu en WSL ahora usan la aplicación predeterminada de Windows.
- Nuevo paquete de cuatro formatos `music` (`signal-spell`, `patchbay-dream`, `pixi-signal`, `pixi-mixer`) para DJs y productores: PixiJS/pixi-filters locales, señal, mezcladora, bloom, glitch y píxeles neón reproducibles con semilla fija.
- Pixelify Sans (SIL OFL) disponible para subtítulos con palabra activa en glow/RGB split y español completo.

## Sin publicar — 2026-11-12

- Cambio incompatible: paquetes Python por responsabilidad y nombres de sistema en inglés, sin alias.
- Validador del storyboard por secciones, conservando resultados y orden de mensajes.
- Migración reversible con respaldo; títulos y originales personales intactos.
- Ver `docs/migration.md` y ADR 0019.

Formato: una entrada por versión; dentro, lo que cambió para quien usa el motor. Las decisiones
técnicas y su porqué están en `docs/decisions/`.

## 0.9.2-alpha
- Corregido en Linux: el control de sincronía de la voz tratada comparaba la duración declarada del contenedor (el «priming» de AAC se declara distinto en ffmpeg 6 y 9); ahora compara las muestras decodificadas.

## 0.9.1-alpha
- Corregido en Linux: el corte usaba `-/filter_complex`, que no existe en ffmpeg 6 (Ubuntu 24.04); ahora se detecta la versión de ffmpeg. Encontrado por la demo de punta a punta en GitHub.
- La demo muestra el error real de `bin/edit` cuando un paso falla.

## 0.9.0-alpha — primera versión pública
- Carpeta de originales configurable como `input_dir` / `$VIDEOVIBE_INPUT` (los nombres `material_dir` / `$VIDEOVIBE_MATERIAL` siguen valiendo); documentación corregida: la plataforma de anuncio es `ads` y los scripts se llaman `apply_cut.py` / `paper_cut.py`.
- Carpetas fáciles de encontrar en la raíz: `input/` (originales; `bin/new-piece --from <nombre>` los busca ahí) y `deliveries/<Canal>/<fecha> <pieza>/` (finales verificados con portada, texto y `README.md`, como enlaces o copias; `bin/edit` la abre al entregar). ADR 0018.
- Revisiones A/B guiadas en terminal: resumen, cuatro preguntas, apertura de archivos y rutas absolutas; la aprobación requiere una presentación vigente. `bin/open-review` abre otros archivos de revisión.
- B-roll y grabaciones de pantalla como insertos visuales del storyboard: recorte vertical, tiempo de origen, conversión SDR, registro de derechos y revisión B.
- Validado con material real: fuente HDR horizontal y captura de Terminal; borrador vertical de 8 s con audio y `hyperframes check` sin errores ni avisos.
- Encuadres de detalle para capturas horizontales (`fit=region`), avisos de legibilidad y cuadros de revisión B a tamaño de teléfono.
- Prueba técnica adicional con una fuente vertical real aportada por la persona y la captura de Terminal: borrador 9:16 de 8 s y vistas a tamaño de teléfono.
- Probado el inserto de Terminal sobre una pieza hablada y cortada: revisión B aprobada y entregas TikTok, Reels y anuncio verificadas.
- Corregido: la huella de composición con B-roll cambiaba también la de piezas sin insertos y obligaba a re-verificar piezas ya aprobadas; ahora solo cambia cuando hay insertos.
- Pruebas de voz: detectan cuando `say` produce un archivo vacío en el sandbox y se omiten en ese entorno; se ejecutan normalmente cuando macOS genera audio real.
- Nombre: **VideoVibe**. Licencia Apache-2.0.
- Los canales pueden vivir fuera del repo (`local.json → channels_dir` o `VIDEOVIBE_CHANNELS`).
- Canal de ejemplo ficticio `science-60`, `bin/setup`, `bin/demo`; README e instalación en inglés y español.
- `bin/doctor` multiplataforma (macOS y Linux); ffmpeg detectado (`VIDEOVIBE_FFMPEG`).
- `scripts/pipeline/storyboard.py`: valida el storyboard y devuelve todos los problemas juntos con su ruta; `compose.py` no compone si hay problemas.
- **Primeros pasos:** `bin/welcome` (etapa de la persona: instalar, crear-canal, completar-canal, primera-pieza, listo) y `docs/getting-started.md` (bienvenida, demo, 6 preguntas, canal con valores por defecto, primera pieza). `bin/new-channel --about … --person …` crea un canal completo sin TODO.
- Corregido: `sfx.py` fallaba con canales fuera del repo. Whisper reintenta solo sin GPU si la GPU falla (sandbox de Codex, máquinas sin GPU).
- `bin/new-piece` (pieza nueva en la carpeta de canales correcta) y pausas «material» y «brief» en `bin/edit` (la regla «nada sin brief» ya no depende de que el agente se acuerde); `scripts/pipeline/cover.py` (portada desde el gancho).
- Interno: `compose.py` dividido en `scripts/composer/`; primitivas de audio en `audiotools.py`; `bin/publish`; test de `verify.py`; demo de punta a punta en CI.

## 0.8 — audios aportados y micrófono externo
- Música aportada: revisión del archivo, `--trim`, BPM estimado, `music.py fit` (duración exacta por compases).
- Efectos aportados: `sfx.py add` (precedencia usuario > receta > base).
- Bloque de sonido de `assets.md` automático; regla de licencias para la versión anuncio.
- Micrófono externo: sincronización automática (desfase + deriva, cobertura parcial); la transcripción y el corte lo usan, con verificación por segmento.

## 0.7 — sonido por canal
- Guía única `docs/audio.md`.
- Efectos por receta (`audio/sfx/recipes.json`), `sfx.py --list/--preview`.
- Identidad musical (`brand.json → music`): instrumentos por ánimo, melodía, mezcla por energía; intro nivelada.
- Render por plataforma: solo se rehace la versión que cambió.

## 0.6 — voz
- Tratamiento de voz medido (`scripts/audio/voice.py`): ruido, ecualización, «s», compresión y expansor; `--compare`.
- Volumen de música por defecto por canal (`channel.json → audio`).

## 0.5 — sonido
- Mezcla con ducking por tiempos de palabra; kit de efectos sintetizado por canal; biblioteca de música con licencia (Epidemic Sound vía MCP).
- Versión `anuncio` con música apta para publicidad; música propia (`scripts/audio/musicgen.py`).

## 0.4 — orquestador
- `bin/edit`: avanza solo hasta cada revisión humana; idempotente; invalida aprobaciones si cambia lo aprobado.

## 0.3 — multicanal
- Motor separado de los canales (`channels/<canal>/`), idiomas (`lang/`), formatos con paquetes temáticos, estado por pieza (`bin/status`).

## 0.2 — primera pieza
- Corte en papel (revisión A), transcripción por tramos, HDR→SDR, subtítulos palabra por palabra, composición con HyperFrames, verificación de entrega.
