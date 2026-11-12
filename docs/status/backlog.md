# Backlog

> Tareas del motor priorizadas. P1 = siguiente; P2 = pronto; P3 = cuando haya tiempo.
> Al terminar una tarea: muévela a «Hecho» con fecha y actualiza `STATUS.md`.

## P1

- [ ] **Validación real** antes de más funciones: toma con micrófono externo, segundo canal. (Codex: ✅ 2026-11-11, de la bienvenida a la revisión A en una copia limpia.)

- [ ] **Probar audios propios con material real**: una toma de 30–60 s con teléfono + micrófono externo (verificar sincronía de labios en el corte) y 1–2 efectos grabados (`sfx.py add` + `--preview`).

- [ ] **Validar con un segundo canal real** (otra temática y otra persona).
  Alta con `bin/new-channel` + una pieza corta de punta a punta.
  *Hecho cuando:* la pieza pasa `verify.py` sin tocar `scripts/` ni `formats/core.py`.
- [ ] **Probar con Codex** (y luego Gemini CLI, Muse Code): editar una pieza corta leyendo solo `AGENTS.md`.
  *Hecho cuando:* termina sin preguntar nada que esté documentado; lo que faltó queda corregido en docs.
## P2

- [ ] **Transcripción más rápida y con progreso**: sin GPU (sandbox de Codex) 19 s de video tardaron 148 s porque se recarga el modelo en cada tramo; usar whisper-server (modelo cargado una vez) y que `bin/edit` muestre el avance («tramo 3/7»). En la prueba con Codex, el agente fue a leer `transcribe.py` porque no sabía si seguía trabajando.

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
