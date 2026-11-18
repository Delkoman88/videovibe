# Estado del sistema

> Foto del motor **hoy** (no su historia: eso está en `CHANGELOG.md` y `docs/decisions/`).
> Máximo 100 líneas. Última actualización: 2026-11-18 · versión `v0.13.3-alpha`.

Clasificación **alpha**: hay entregas reales verificadas en varios canales y la suite pasa completa
(`.venv/bin/python -m unittest discover -s scripts/tests`), pero faltan uso sostenido con piezas
reales, validación en WSL de la integridad actual, otros agentes y medición editorial (retención).
La cobertura técnica no equivale a calidad editorial garantizada.

## Qué funciona hoy

| Área | Estado | Notas |
|---|---|---|
| Instalación y demo | ✅ | `bin/setup` (macOS/Linux), `bin/demo` (canal de ejemplo `science-60`), `bin/welcome` + `docs/getting-started.md` |
| Piezas y carpetas | ✅ | `bin/new-piece` (con `raw/` y `brief.md`); originales en `input/`, finales en `deliveries/` (fuera de git) |
| Orquestación (`bin/edit`) | ✅ | Avanza hasta cada pausa y solo rehace lo desactualizado; A/B guiadas (resumen, preguntas, archivos abiertos, rutas). `--platform` limita render y entrega |
| Integridad | ✅ | Bloqueo por pieza; A/B ligadas a su evidencia (B: contenido + HTML compilado); recibos por etapa; huellas relativas (mover carpetas no invalida); `bin/status --migrate` y `--attest-legacy` para evidencia anterior (ADR 0036) |
| Canales | ✅ | `bin/new-channel`, `bin/doctor --channel`, idiomas `lang/es.json` y `lang/en.json` |
| Ingesta | ✅ | Orientación, tipo de toma y HDR; micrófono externo sincronizado al milisegundo |
| Transcripción | ✅ | whisper.cpp local, tramo por tramo (~75 s por 90 s de audio) |
| Corte en papel (A) | ✅ | Retomas, muletillas, conectores sueltos, fragmentos cortos, silencios; `--refresh-from-cut` conserva decisiones |
| Aplicar corte | ✅ | HDR→SDR BT.709 (~3.5 min para 90 s con HDR) |
| Subtítulos | ✅ | Palabra por palabra contra el master; ligados a su corte; reparación parcial tras cambios. Revisar puntuación a mano |
| Guion e historia | ✅ | Skill `storytelling` (antes de grabar) y revisión editorial previa a A/B (`docs/storytelling.md`, `docs/editorial.md`) |
| Plan visual + composición | ✅ | Storyboard validado; HyperFrames; 36 formatos en paquetes por canal (motion, lottie, molecular, cinematic 3D, sketch, data, music); dirección de animación v2 por perfiles (`docs/animation-direction.md`) |
| Efectos sobre la toma | ✅ | Recorte de la persona (`fx`), ritmo (`beat_fx`), transiciones; `cutout_review` con alternativas conservadoras (`docs/effects.md`) |
| Control visual | ✅ | QA por elemento con el runtime real; bloquea B ante errores objetivos o informes viejos |
| B-roll y pantallas | ⚠️ parcial | Insertos con audio original opcional, recorte o región; el corte hablado usa tomas a cámara |
| Extractos | ✅ | `media_excerpt`: video y audio del mismo intervalo para cierres de hasta 4 s |
| Sonido | ✅ | Voz tratada por medición; música (Epidemic vía MCP o `musicgen.py`), versión `ads`, efectos con recetas por canal; audios aportados con licencia |
| Render y verificación | ✅ | `render -q delivery` (~5 min por plataforma); `verify.py`; entregas versionadas e independientes |
| Copy y portada | ⚠️ parcial | El agente redacta el copy; portada con `scripts/pipeline/cover.py` |
| Versión corta y clips | ❌ | Solo propuestos en `clips.json` |
| Voz en off sin video | ❌ | No entra al corte |

## Canales

Los de cada persona viven en su propia carpeta (`docs/channels.md`; `bin/doctor` dice cuál).
En el motor solo está `science-60` (ejemplo ficticio; sus piezas las genera `bin/demo`).
`bin/format-catalog --usage` muestra qué formatos se usan en las piezas de tus canales.

## Versiones fijadas

HyperFrames 0.9.32 · GSAP 3.15.0 · PixiJS 8.23.0 + pixi-filters 6.1.5 · three 0.187.0 +
postprocessing 6.39.6 · Rough.js 4.6.6 · d3 7.9.0 (`package.json`) · whisper.cpp +
`ggml-large-v3-turbo-q5_0` + VAD Silero 5.1.2 · ffmpeg 9 (`ffmpeg-full` para HDR) · Node ≥ 22 ·
Python 3.14 + numpy (`.venv`).

## Plataformas y CI

- macOS: uso real completo. Ubuntu/WSL: una entrega real verificada; la integridad actual falta validarla en WSL.
- Windows nativo: la ejecución delegada (`bin/edit`) se rechaza explícitamente; usar WSL.
- CI público: `tests` y `animation-install` en Ubuntu 24.04 (macOS se valida localmente).

## Limitaciones conocidas

- Zonas seguras de las plataformas aproximadas (no medidas con capturas reales).
- Agentes probados: Claude Code (uso real) y Codex CLI (de la bienvenida a la revisión A). Falta Gemini CLI y Muse Code.
- La detección de retomas exige que la nueva toma empiece con las mismas 3 palabras.
- `compose.py` sobrescribe ediciones manuales hechas en la app de HyperFrames.
- Las pruebas que necesitan `say` se omiten si macOS genera audio vacío dentro del sandbox (ADR 0016).
- Evidencia de versiones anteriores: se retira en v0.15; antes, `bin/status --migrate --apply` (`docs/migration.md`).

## Dónde seguir

`docs/status/backlog.md` (tareas) · `docs/status/roadmap.md` (fases) · `docs/decisions/` (por qué) ·
`CHANGELOG.md` (qué cambió en cada versión).
