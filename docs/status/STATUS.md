# Estado del sistema

> Foto actual del motor. La actualiza el agente al cerrar cada sesión de desarrollo.
> Última actualización: 2026-11-17 · versión `v0.11.0-alpha`.

## Organización del motor

Paquetes por responsabilidad, validador por secciones y nombres del sistema en inglés, sin alias.
Migración reversible disponible en `bin/migrate-layout` (ADR 0019; `docs/migration.md`).
Las revisiones afectadas por la migración requieren aprobación explícita de nuevo.
Validación: suite de 176 pruebas en verde (15 omitidas cuando el entorno no puede generar audio de sistema).

## Qué funciona hoy

| Etapa | Estado | Notas |
|---|---|---|
| Instalación y demo | ✅ | `bin/setup` (macOS/Linux), `bin/demo` (canal de ejemplo `science-60`) |
| Primeros pasos | ✅ | `bin/welcome` + `docs/getting-started.md`: de cero a la primera pieza (probado con una copia limpia del repo) |
| Carpetas `input/` y `deliveries/` | ✅ | Originales y finales en la raíz de VideoVibe (fuera de git); el agente siempre muestra las rutas |
| Piezas nuevas | ✅ | `bin/new-piece` (en la carpeta de canales correcta, con `raw/` y `brief.md`); `bin/edit` se detiene sin material o sin brief completo |
| Orquestación (`bin/edit`) | ✅ | Avanza hasta cada pausa; A/B presentan resumen, cuatro preguntas, abren archivos y muestran rutas absolutas. En WSL convierte la ruta y usa la aplicación predeterminada de Windows. `--platform` limita render, verificación y entrega sin invalidar el storyboard aprobado. Las aprobaciones nuevas requieren revisión vigente; las anteriores conservan validez |
| Canales (alta, validación, idiomas) | ✅ | `bin/new-channel`, `bin/doctor --channel`, `lang/es.json`, `lang/en.json` |
| Ingesta | ✅ | Detecta orientación, tipo de toma y HDR; sincroniza micrófonos externos al milisegundo (con deriva) |
| Transcripción | ✅ | whisper.cpp local, tramo por tramo; ~75 s por 90 s de audio |
| Corte en papel (revisión A) | ✅ | Retomas, muletillas, conectores sueltos, fragmentos ≤ 0.3 s, silencios |
| Aplicar corte | ✅ | HDR→SDR BT.709; ~3.5 min para 90 s con conversión HDR |
| Subtítulos | ✅ | Palabra por palabra; reimportación desde whisper.cpp y reparación parcial desde el corte aprobado/remapeo para conservar texto y sincronía tras cambios; revisar puntuación a mano |
| Plan visual + composición | ✅ | Storyboard validado antes de componer (`scripts/pipeline/storyboard.py`); HyperFrames 0.9.32; cámara, overlays orgánicos, CTA por plataforma, corrección de color, 24 formatos (paquete `motion` con plugins de GSAP; `lottie` con bibliotecas con licencia y color de marca; `molecular` con 3Dmol.js; `music` para DJs/productores, con PixiJS opcional); estilos de subtítulos y tarjetas por canal (`brand.json`); librerías opcionales por formato (`formats/vendors.py`) y galería visual `bin/format-gallery` |
| Render final | ✅ | `hyperframes render -q delivery`; ~5 min por plataforma |
| Verificación de entrega | ✅ | `scripts/pipeline/verify.py`; después, `deliveries/<Canal>/<fecha> <pieza>/` con los finales (enlaces o copias) y `README.md` |
| Estado por pieza | ✅ | `status.json` + `bin/status` |
| Copy, portada | ⚠️ parcial | El agente redacta el copy; portada con `scripts/pipeline/cover.py` (cuadro del gancho o `--at`) |
| Versión corta y clips | ❌ | Solo propuestos en `clips.json` |
| Audios aportados | ✅ | Música (`music.py add --source usuario`, `fit`) y efectos (`sfx.py add`) con licencia; bloque de sonido de `assets.md` automático |
| Tratamiento de voz | ✅ | `scripts/audio/voice.py` dentro de la composición; decide por medición; antes/después con `--compare` |
| Música y efectos | ✅ | Guía `docs/audio.md`. Efectos: kit base + recetas por canal (`recipes.json`). Música: Epidemic vía MCP o propia con `musicgen.py` (identidad por canal en `brand.json → music`); versión `ads` (anuncio) con música apta para pauta; volumen por canal |
| B-roll y grabaciones de pantalla | ⚠️ parcial | Insertos visuales mudos con cuadro completo, recorte o región de detalle; revisión B a 360×640 y aviso de legibilidad. Probado con una captura de Terminal sobre una toma vertical de 8 s y una pieza hablada real (revisión B aprobada; TikTok, Reels y anuncio verificados). El corte hablado sigue usando tomas a cámara |
| Voz en off sin video | ❌ | No entra al corte |

## Canales

Canales del motor (los de cada persona viven en su propia carpeta, ver `docs/channels.md`).

| Canal | Idioma | Piezas | Estado |
|---|---|---|---|
| `science-60` (ejemplo, ficticio) | es | 0 (las genera `bin/demo`) | ejemplo |

## Versiones fijadas

HyperFrames 0.9.32 · PixiJS 8.23.0 + pixi-filters 6.1.5 · GSAP 3.15.0 (`package.json`) ·
whisper.cpp + `ggml-large-v3-turbo-q5_0` + VAD Silero 5.1.2 ·
ffmpeg 9 (`ffmpeg-full` para HDR) · Node ≥ 22 · Python 3.14 + numpy (`.venv`).

## Limitaciones conocidas

- Zonas seguras de las plataformas aproximadas (no medidas con capturas reales).
- Agentes probados: Claude Code (uso real) y Codex CLI (copia limpia: de la bienvenida a la revisión A). Falta Gemini CLI y Muse Code.
- Probado en macOS con material real. Linux: la demo pasa en GitHub (Ubuntu 24.04, ffmpeg 6, sin GPU) y la primera pieza real en Ubuntu/WSL llega a revisión B; falta cerrar una entrega real verificada en Linux.
- La detección de retomas exige que la nueva toma empiece con las mismas 3 palabras.
- `compose.py` sobrescribe ediciones manuales hechas en la app de HyperFrames.
- Las pruebas que necesitan `say` se omiten si macOS genera audio vacío dentro del sandbox; la validación de voz requiere correr la suite con audio real (ADR 0016).

## Dónde seguir

`docs/status/backlog.md` (tareas priorizadas) · `docs/status/roadmap.md` (fases) · `docs/decisions/`.
