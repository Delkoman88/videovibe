# Estado del sistema

> Foto actual del motor. La actualiza el agente al cerrar cada sesión de desarrollo.
> Última actualización: 2026-11-17 · versión `v0.12.0-alpha`.

## Organización del motor

Paquetes por responsabilidad, validador por secciones y nombres del sistema en inglés, sin alias.
Migración reversible disponible en `bin/migrate-layout` (ADR 0019; `docs/migration.md`).
Las revisiones afectadas por la migración requieren aprobación explícita de nuevo.
Validación anterior a dirección v2: 229 pruebas (15 omitidas cuando el entorno no puede generar audio de sistema).
La suite actual y su evidencia se describen en la siguiente sección.

## Dirección de animaciones v2 — sin nueva etiqueta de versión

Perfiles optativos con controles internos, candidatos con límites y licencias, objetos narrativos y
anclajes por palabra. Previews y producción comparten compositor; QA usa el runtime real y bloquea B
ante errores objetivos o informes obsoletos. Compatibilidad exacta del HTML legado/v1.

Validación: matriz renderizada de **108/108** casos en verde (36 formatos × 3 perfiles),
con check, QA y comparación inversa; 108 HTML actuales iguales a los medidos. Escenarios de dos marcas
con fx, beat_fx, transiciones y subtítulos en verde, incluidos rechazo de recortes y fuentes ausentes.
Instalación limpia local en macOS: npm ci, entorno Python nuevo, suite de 247 pruebas (4 omitidas
por disponibilidad del entorno) y render de prueba correctos. Suite final del árbol: **248 pruebas en verde** (192.7 s), incluido el guardián de datos personales.
Caché: reutilización y reconstrucción al faltar un cuadro inverso comprobadas. Imagen narrativa:
rechazo sin licencia y render con recurso registrado comprobados.
Prueba real exclusivamente en una copia aislada del canal científico privado: 510 instantes medidos,
0 errores objetivos y borrador generado. Validación técnica cerrada; la persona confirmó que esta
copia es una prueba del motor, sin entrega editorial ni aprobación B requerida. La revisión B se
solicitó por una clasificación incorrecta del ensayo; no se registra como aprobada. Persisten avisos
de zona segura y no se certifica una entrega final. Los originales siguen intactos.
El workflow de instalación macOS/Ubuntu está preparado; su ejecución remota y la prueba nueva en
WSL aún no se han realizado. Esto no reabre la entrega histórica del canal musical privado desde WSL.
Ver [uso y límites](../animation-direction.md) y ADR 0030.

## Qué funciona hoy

| Etapa | Estado | Notas |
|---|---|---|
| Instalación y demo | ✅ | `bin/setup` (macOS/Linux), `bin/demo` (canal de ejemplo `science-60`) |
| Primeros pasos | ✅ | `bin/welcome` + `docs/getting-started.md`: de cero a la primera pieza (probado con una copia limpia del repo) |
| Carpetas `input/` y `deliveries/` | ✅ | Originales y finales en la raíz de VideoVibe (fuera de git); el agente siempre muestra las rutas |
| Piezas nuevas | ✅ | `bin/new-piece` (en la carpeta de canales correcta, con `raw/` y `brief.md`); `bin/edit` se detiene sin material o sin brief completo |
| Orquestación (`bin/edit`) | ✅ | Avanza hasta cada pausa; A/B presentan resumen, cuatro preguntas, abren archivos y muestran rutas absolutas. En WSL convierte la ruta y usa la aplicación predeterminada de Windows. `--platform` limita render, verificación y entrega sin invalidar el storyboard aprobado. Las aprobaciones nuevas requieren revisión vigente; las anteriores conservan validez |
| Canales (alta, validación, idiomas) | ✅ | `bin/new-channel`, `bin/doctor --channel`, `lang/es.json`, `lang/en.json`; segundo canal real validado con el canal musical privado y su primera entrega en TikTok (2026-11-16; confirmado por la persona el 2026-11-17) |
| Ingesta | ✅ | Detecta orientación, tipo de toma y HDR; sincroniza micrófonos externos al milisegundo (con deriva) |
| Transcripción | ✅ | whisper.cpp local, tramo por tramo; ~75 s por 90 s de audio |
| Corte en papel (revisión A) | ✅ | Retomas, muletillas, conectores sueltos, fragmentos ≤ 0.3 s, silencios |
| Aplicar corte | ✅ | HDR→SDR BT.709; ~3.5 min para 90 s con conversión HDR |
| Subtítulos | ✅ | Palabra por palabra; reimportación desde whisper.cpp y reparación parcial desde el corte aprobado/remapeo para conservar texto y sincronía tras cambios; revisar puntuación a mano |
| Plan visual + composición | ✅ | Storyboard validado antes de componer (`scripts/pipeline/storyboard.py`); HyperFrames 0.9.32; cámara, overlays orgánicos, CTA por plataforma, corrección de color, 36 formatos (paquete `motion` con plugins de GSAP; `lottie` con bibliotecas con licencia y color de marca; `molecular` con 3Dmol.js; `cinematic` con Three.js + postprocesado y biblioteca de modelos `.glb`; `sketch` con Rough.js (pizarrón); `data` con d3 (gráficas con fuente obligatoria); iconos científicos CC0 `health:` y `bio:`; `music` para DJs/productores, con PixiJS opcional); estilos de subtítulos y tarjetas por canal (`brand.json`); librerías opcionales por formato (`formats/vendors.py`) y galería visual `bin/format-gallery`; efectos sobre la toma con la persona recortada (`fx`), al ritmo de la música (`beat_fx`) y transiciones que tapan el corte (`transitions`), ver `docs/effects.md` |
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
- Probado en macOS con material real. Linux: la demo pasa en GitHub (Ubuntu 24.04, ffmpeg 6, sin GPU) y se completó una entrega real verificada desde Ubuntu/WSL: primera pieza del canal musical privado para TikTok (2026-11-16; confirmado por la persona el 2026-11-17).
- La detección de retomas exige que la nueva toma empiece con las mismas 3 palabras.
- `compose.py` sobrescribe ediciones manuales hechas en la app de HyperFrames.
- Las pruebas que necesitan `say` se omiten si macOS genera audio vacío dentro del sandbox; la validación de voz requiere correr la suite con audio real (ADR 0016).

## Dónde seguir

`docs/status/backlog.md` (tareas priorizadas) · `docs/status/roadmap.md` (fases) · `docs/decisions/`.
