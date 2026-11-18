# Backlog

> Tareas del motor priorizadas. P1 = siguiente; P2 = pronto; P3 = cuando haya tiempo.
> Al terminar una tarea: muévela a «Hecho» con fecha y actualiza `STATUS.md`.
> Presupuesto: si entra una tarea grande, antes se cierra o se descarta otra (el backlog no solo crece).

## P1

- [ ] **v0.15 — retirar lo heredado de integridad:** borrar `legacy_digest`, `legacy_fingerprint`, `_inputs_v2`,
  `scripts/core/legacy/`, `editlib.legacy_dirty` y la regla «sin recibos» de `stage_dirty`. Antes, cada
  instalación corre `bin/status --migrate --apply` (`docs/migration.md`).
- [ ] **Portabilidad de dirección v2:** ejecutar la versión nueva en WSL (el job remoto Ubuntu ya pasa).
- [ ] Reducir lecturas repetidas de huellas en originales grandes; conservar comprobaciones frescas antes/después de render y entrega.
- [ ] Validar la corrección de integridad en WSL; pruebas macOS no equivalen a portabilidad.
- [ ] Implementar y validar delegación de trabajadores en Windows nativo; actualmente falla explícitamente y recomienda WSL.

  La prueba técnica local está cerrada y no requiere aprobación B ni entrega editorial, según la
  aclaración de la persona. El canal musical privado no forma parte de esta prueba nueva
  (la validación histórica sigue cerrada).

- [ ] **Probar audios propios con material real**: una toma de 30–60 s con teléfono + micrófono externo (verificar sincronía de labios en el corte) y 1–2 efectos grabados (`sfx.py add` + `--preview`).

- [ ] **Probar con Codex** (y luego Gemini CLI, Muse Code): editar una pieza corta leyendo solo `AGENTS.md`.
  *Hecho cuando:* termina sin preguntar nada que esté documentado; lo que faltó queda corregido en docs.
## P1 — Efectos sobre la toma, ritmo, 3D, transiciones y estilos (plan aprobado 2026-11-17)

- [x] Fases 0 (prueba técnica), 1 (`fx`) y 2 (ritmo, `beat_fx`) — ver Hecho.
- [x] Fase 3 — 3D cinematográfico (2026-11-17): Three.js + postprocessing (IIFE con esbuild y huella), paquete `cinematic` (5 formatos), biblioteca `models` (.glb). ADR 0027.
- [x] Fase 4 — transiciones (2026-11-17): `storyboard.json → transitions` con seis tipos de superposición (CSS + GSAP, marca del canal, sonido automático), deterministas. ADR 0028.
- [x] Fase 5 (2026-11-17): iconos científicos CC0 (68 Health Icons, 44 Bioicons; prefijos `health:`/`bio:`), paquete `sketch` (Rough.js) y `data` (d3, `source` obligatorio, datos desde archivos de la pieza). ADR 0029.
- [x] Galería con fragmento de toma (`--with-plate`), compositor común y API para `fx`, `beat_fx` y transiciones; escenarios combinados renderizados con dos marcas públicas.

## P1 — Más y mejores animaciones (plan aprobado 2026-11-17)

- [ ] **Adopción editorial del paquete `motion` y `text_fx`:** usarlos en una futura pieza de
  producción con revisión B. Es un seguimiento editorial del paquete, distinto del bloque
  `storyboard.motion` v2; no bloquea el cierre de la prueba técnica del upgrade ni exige aprobarla.
## P2

- [ ] Previews parciales de cambios y métricas automatizadas de revisión (fuera de ADR 0035).


- [ ] Evaluar storytelling y criterio editorial con nuevas piezas reales; registrar correcciones por canal y comparar el esfuerzo de revisión. Primer caso real aprobado tras tres propuestas visuales: contexto, pertinencia de efectos y cierre. Continuar con más piezas; no hay medición de retención ni comparación controlada del esfuerzo. Los casos ficticios no sustituyen A/B.

- [ ] **Revisar actualización de HyperFrames**: la versión fijada 0.9.32 arrastra `undici` con avisos de seguridad de npm; probar 0.9.58 y migrar solo si la suite, la demo y una pieza real conservan salida y revisiones.

- [ ] **Transcripción más rápida y con progreso**: sin GPU (sandbox de Codex) 19 s de video tardaron 148 s porque se recarga el modelo en cada tramo; usar whisper-server (modelo cargado una vez) y que `bin/edit` muestre el avance («tramo 3/7»). En la prueba con Codex, el agente fue a leer `transcribe.py` porque no sabía si seguía trabajando.

- [ ] **Recorte de video con memoria entre cuadros**: `u2net_human_seg` (HyperFrames) toma objetos pegados a la persona (respaldo de la silla) como persona en todo el tramo; el estabilizador no puede distinguirlos. Evaluar un modelo de matting de video con licencia compatible (RVM es GPL-3.0: descartado) y medir tiempo por segundo.
  Confirmado con material exterior (2026-11-17): conserva partes de una moto y pierde zonas de ropa.
  Fondo, halo y congelado pueden pasar el render y aun fallar visualmente; revisar las máscaras
  sobre fondo contrastante y sobre la composición antes de recomendar esos efectos.
  Ya hay inspección con evidencia y sustitución conservadora automática; cambiar el modelo sigue pendiente.
- [ ] **Versión corta y clips** desde `clips.json` (render por segmentos del master compuesto).
- [ ] **B-roll y grabaciones de pantalla**: insertos visuales y encuadre de detalle implementados; falta soportar audio/voz de pantalla como fuente del corte hablado.
- [ ] **Formatos con datos reales**: animar salidas reales (BLAST, tablas, curvas de simulación) en lugar de ilustrativas.
- [ ] **Portada diseñada**: hoy `scripts/pipeline/cover.py` toma un cuadro del video (el gancho); falta una composición propia de portada (título grande, recorte para Reels 4:5).


- [ ] **Efectos de Epidemic Sound para la versión orgánica** (`SearchSoundEffects`), con los propios en `ads` (anuncio) (mismo mecanismo que la música).
- [ ] **Efecto por defecto por formato**: cada formato de `formats/` declara su sonido (ADN → sparkle, célula → bubbles) y `sfx_auto` lo usa.
- [ ] **Comprobación automática de mezcla** en `verify.py`: música siempre ≥ N dB bajo la voz; ningún efecto tapa una palabra.

## P3

- [ ] Velocidad: whisper en modo servidor (no recargar el modelo por tramo); codificación por hardware.
- [ ] Versión para X: lienzo 4:5 opcional, copy técnico, hilo.
- [ ] Medir zonas seguras reales con capturas de TikTok e Instagram y marcar `_verified: true`.
- [ ] Copiar ediciones manuales de la app de HyperFrames de vuelta al storyboard (hoy `compose.py` las pisa).
- [ ] Respaldo remoto del repo (GitHub privado o público).

## Hecho

- [x] Revisión de integridad v0.13.2 (ADR 0036): subtítulos ligados a su corte, huellas relativas, motor fuera de etapas editables y de B, reaprobación de A, `--attest-legacy`, migración automática y CI solo Ubuntu.
- [x] Consolidación de integridad (ADR 0036): huellas de aprobación/etapas, bloqueo por pieza, entregas independientes y contratos neutrales. Ver STATUS para validación y límites.

- [x] Revisión editorial previa con evidencia y audio nativo opcional de B-roll (ADR 0035); sin gates ni migración de piezas.


- [x] Extractos audiovisuales breves (ADR 0034): fuente intacta, intervalo y fundidos comunes para video y audio; integración con B-roll y efectos aportados.

- [x] Estado y preguntas editoriales (ADR 0033): pendientes coherentes, preguntas por pieza con huella y planes sin estados duplicados.

- [x] **Fiabilidad visual (2026-11-17; ADR 0032):** lectura por elemento, revelados intencionales
  diferenciados de recortes persistentes, avisos transitorios agrupados y subtítulos breves sin
  fundido de línea. Evidencia de recortes, alternativas deterministas y resumen en la revisión B.

- [x] Storytelling y criterio editorial (2026-11-17; ADR 0031): guiones, selección fiel, copy por canal, fuentes fijadas con licencias y refresco seguro de la vista del corte.

- [x] **Documentación canónica de dirección v2 (2026-11-17):** README en ambos idiomas, storyboard,
  pipeline, canales, instalación e índice completo de ADR reconciliados con la guía y el estado.

- [x] **Implementación de dirección v2 (2026-11-17; ADR 0030):** adaptadores internos, objetos/anclajes por paso,
  compositor común, QA con runtime real, matriz renderizada y herramientas de instalación.

- [x] **Segundo canal real validado** (2026-11-16; confirmado por la persona el 2026-11-17): el canal musical privado, canal de DJ, con su primera pieza entregada en TikTok desde Ubuntu/WSL y `verify.py` en verde. Cerradas la validación multicanal y la entrega real en WSL; la prueba de micrófono externo continúa pendiente por separado.

- [x] **Efectos al ritmo (`beat_fx`)** (2026-11-17): golpes en el tiempo del video con la rejilla de la
  biblioteca, envoltura de cámara y avisos de sincronía por canal. ADR 0026.
- [x] **Efectos sobre la toma (`fx`)** (2026-11-17): recorte local de la persona con caché, cuatro efectos
  y validación (incluido «no congelar mientras se habla»). Probado sobre una pieza real. ADR 0025.

- [x] **Fase 3 de animaciones: paquete `molecular`** (2026-11-17): 3Dmol.js con vista y ángulo absolutos por
  cuadro, superficies con `buildReady`, `scripts/tools/structures.py` (PDB, PubChem) y validación de `focus`. ADR 0024.
- [x] **Fase 2 de animaciones: paquete `lottie`** (2026-11-17): bibliotecas con licencia (motor + canal),
  recoloreo con la marca, datos locales, `scripts/tools/lottie.py` y cuatro animaciones propias. ADR 0023.
- [x] **Fase 1 de animaciones: paquete `motion`** (2026-11-17): seis formatos con plugins de GSAP, `text_fx`
  en tarjetas, validación por formato y guía de uso. Galería de los dos canales con check y determinismo en verde.
- [x] **Fase 0 de animaciones** (2026-11-17): tabla de librerías opcionales (`formats/vendors.py`), prueba
  técnica de Lottie y 3Dmol en HyperFrames (deterministas), `bin/format-gallery` e iconos Lucide. ADR 0022.

- [x] **Primera pieza real de un canal de DJ, entregada desde Windows/WSL** (2026-11-16): extensión del corte con una conclusión real, subtítulos reparados por tramos, posiciones que evitan el rostro, B-roll vertical sincronizado, CTA con cola de 4 s y render/entrega limitados a TikTok. `verify.py` en verde y suite de 137 pruebas.

- [x] **Realineación de subtítulos desde el master final** (2026-11-16): `captions.py --from-whisper-json` importa timestamps globales de whisper.cpp, regulariza solo tokens de duración cero y conserva los anclajes; corrige subtítulos obsoletos después de un cambio de corte.

- [x] **Apertura de revisiones en WSL** (2026-11-16): `bin/open-review` detecta Ubuntu/WSL, convierte rutas con `wslpath` y abre video, imágenes y documentos con la aplicación predeterminada de Windows; cubierto por prueba automática.

- [x] **Paquete visual para música electrónica** (2026-11-16): cuatro formatos —incluidos `pixi-signal` y `pixi-mixer` con PixiJS/pixi-filters—, osciloscopio, deck, mezcladora, cables, glitch y píxeles neón. Dependencias locales, semilla fija y revisión B real en un canal de DJ.

- [x] **Linux de punta a punta en GitHub** (2026-11-12): la demo pasa en Ubuntu 24.04 tras dos correcciones (sintaxis de filtros de ffmpeg 6 y sincronía de la voz por muestras decodificadas). El job `demo` ya bloquea.

- [x] **Organización y nombres** (2026-11-12): validador por secciones, paquetes por responsabilidad, rutas en inglés sin alias y migración reversible de canales y entregas (ADR 0019).

- [x] **Revisiones guiadas A/B** (2026-11-12): resumen y cuatro preguntas en terminal, archivos abiertos con rutas absolutas, decisión ligada a la versión presentada y comando genérico para cualquier archivo; alternativa manual sin visor (ADR 0017).

- [x] **Prueba de B-roll sobre pieza hablada real** (2026-11-12): variante aislada de una pieza con corte A, 3 insertos de Terminal y revisión B aprobada; TikTok, Reels y anuncio pasaron `verify.py`, y `bin/edit --plan` indica `done`. Informe local en `work/` (ignorado por Git).

- [x] **Prueba técnica con fuente vertical real** (2026-11-12): fuente con rotación −90° como video base y captura de Terminal como B-roll; borrador 1080×1920/8 s con audio y tres cuadros a tamaño de teléfono. Informe local en `work/` (ignorado por Git).
- [x] **Suite estable dentro del sandbox** (2026-11-12): las pruebas dependientes de `say` verifican audio real antes de ejecutarse; se omiten cuando macOS crea un AIFF vacío. Resultado: 101 pruebas, 15 omitidas en sandbox; 101 pruebas sin omisiones fuera del sandbox (ADR 0016).

- [x] **Encuadre por región para capturas horizontales** (2026-11-12): `fit=region` por tramo, cortes directos, aviso de reducción y cuadros de revisión B a 360×640. Validado con la captura de Terminal: texto de detalle visible y `hyperframes check` con 0 errores/avisos.

- [x] **Insertos visuales B-roll y pantalla** (2026-11-11): fuentes de `media.json`, recorte vertical con punto focal o cuadro completo, audio mudo, derechos registrados y revisión B. Prueba real: toma HDR 3840×2160 + captura de Terminal, borrador 1080×1920/8 s con audio; HyperFrames check sin errores ni avisos.

- [x] **Deuda técnica antes de publicar** (2026-11-11): validación del storyboard (`scripts/pipeline/storyboard.py`), `compose.py` dividido en `scripts/composer/`, audio unificado en `audiotools.py`. Salida idéntica byte a byte (ADR 0013).

- [x] **Audios aportados y micrófono externo** (2026-11-11): `music.py add/fit`, `sfx.py add`, `audiosync.py`, licencias automáticas en `assets.md`. Falta probar con material real (teléfono + micrófono).

- [x] **Render por plataforma** (2026-11-11): `editlib.platform_fingerprint` (composición común sin valores por defecto + variables de la plataforma + archivos que eligen; binarios por contenido).

- [x] **Sonido por canal** (2026-11-11): `docs/audio.md`, recetas de efectos (`recipes.json`), identidad musical (`brand.json → music`), mezcla por energía. Corrige «los ánimos suenan parecido».
- [x] **Tratamiento de voz** (2026-11-11): `scripts/audio/voice.py`.

- [x] **Música real de Epidemic Sound** (2026-11-11): MCP conectado; «Challenges Ahead» en la pieza 2026-11-09, registrada en `library.json` y `assets.md`.

- [x] **Música propia para anuncios**: `scripts/audio/musicgen.py` (4 ánimos, semillas, duración exacta, hueco para la voz). Siguiente nivel posible: más ánimos/instrumentos, variación melódica.

- 2026-11-11 — Sonido: mezcla con ducking automático, efectos sintetizados por canal, biblioteca de música con licencia (ADR 0008).
- 2026-11-11 — `bin/edit`: orquestador idempotente con pausas; corrige además que `apply-cut` pisaba la transcripción corregida y que el corte podía pasar del final de la toma.
- 2026-11-11 — Motor multicanal: canales, idiomas, formatos por paquetes, estado por pieza, docs de estado.
- 2026-11-11 — Animaciones intercaladas a pantalla completa (sin burbuja); paquete biotech.
- 2026-11-11 — Fase 2: subtítulos, composición HyperFrames, verificación de entrega.
- 2026-11-10 — Fase 1: corte automático con revisión A.

- [x] Correcciones de auditoría final: exclusión heredada y reservas de trabajadores, estabilidad de entradas, promoción segura, plataformas y dependencias, documentación de copias versionadas. Validación y límites en STATUS.
