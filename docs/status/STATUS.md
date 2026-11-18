# Estado del sistema

> Foto actual del motor. La actualiza el agente al cerrar cada sesión de desarrollo.
> Última actualización: 2026-11-17 · versión `v0.13.2-alpha`.

La clasificación sigue siendo **alpha**: hay entregas reales verificadas y 301 pruebas correctas,
pero faltan la validación de la dirección v2 actual en WSL/CI remoto, otros agentes y más evaluación
editorial real. La cobertura técnica no equivale a calidad editorial garantizada.

## Revisión de integridad — v0.13.2-alpha

- Subtítulos ligados al corte que los produjo: un corte nuevo ya no reutiliza la transcripción del
  master anterior (se guarda una copia con las correcciones).
- Huellas con rutas relativas (esquema 3): mover la carpeta de canales o cambiar de máquina no invalida.
- Etapas editables y B sin código del motor: activar un paquete o actualizar npm no vuelve a transcribir
  ni pide aprobar otra vez; B se invalida si cambia el HTML compilado.
- Presentar o aprobar A no borra B (B se valida con su propia evidencia); `bin/status --attest-legacy` (también desde el historial) para aprobaciones anteriores
  con revisión guardada coincidente.
- Migración automática de la evidencia guardada (`integrity.restamp`), comprobada contra el código
  original de v0.13.1 en todas las piezas reales: reproduce sus huellas sin diferencias.
- CI `animation-install` solo en Ubuntu (el runner macos-14 no está disponible); macOS se valida localmente.

## Consolidación de integridad — v0.13.1-alpha

### Correcciones de la auditoría final

Se corrigieron los seis hallazgos: bloqueo heredado y reservas de grupos POSIX; comprobación de
entradas estables antes del éxito; B vinculada a la composición compilada; temporales únicos y
validación antes de reemplazar finales; recibos v3 por plataformas y dependencias de subtítulos;
documentación canónica de entregas sin instrucciones contradictorias.
Validación actual: **288 tests correctos** (239.130 s), privacidad incluida, más 10 pruebas focalizadas
correctas de revisión tras exigir evidencia de salidas de composición. Seis regresiones nuevas
cubren los cinco fallos técnicos y liberación normal de trabajadores. Concurrencia con procesos
reales; mutaciones durante composición/render inyectadas de forma determinista en fixtures.
No se generó una nueva entrega audiovisual de una pieza personal en esta corrección.
Windows nativo rechaza ejecución delegada hasta implementar y validar el mecanismo equivalente;
WSL queda pendiente de validación. No se migraron entregas históricas.
Evidencia local: `work/integrity-audit/corrections/`.

### Evidencia de la consolidación anterior

Aprobaciones v2 vinculadas a entradas y presentación; registros históricos sin evidencia requieren
revisión al reanudar, sin escritura en consultas. Estado con valores estructurales por defecto,
transacciones y bloqueo por pieza del sistema operativo. Etapas con huellas de entradas/salidas;
render final temporal y comprobación de B antes de reemplazar el resultado.
Entregas nuevas independientes y versionadas, con hashes, recibo de verificación y current.json;
migración explícita para desacoplar enlaces duros antiguos. Contratos puros extraídos de compositor,
pipeline y herramientas, con prueba estática de límites entre paquetes. ADR 0036.
Validación: **282 tests en verde** (297.045 s), incluido el guardián de datos personales.
Copia aislada con composición, preview y finales nuevos: TikTok/Reels verificados y entregados;
sobrescribir el render de origen no modifica la copia entregada (SHA-256 idéntico). Al restaurarlo,
`bin/edit --plan` confirma entregable sin etapas pendientes. Corte/transcripción reutilizados como
fixture, aprobaciones simuladas: no constituye nueva aceptación editorial. Evidencia local:
`work/integrity-audit/`. No se migraron entregas de producción durante aquel ensayo.
Windows nativo y WSL no ejecutados en esta sesión. Las huellas se recalculan por contenido;
queda optimizar lecturas repetidas de originales grandes sin debilitar la detección de cambios.

## Revisión editorial previa y audio nativo — v0.13.0-alpha

Procedimiento del agente antes del preview: promesa inicial, desarrollo, función de recursos y cierre,
con evidencia en work/editorial-evaluation.md. Sin gate nuevo ni migración de piezas aprobadas.
B-roll con audio original optativo: intervalo compartido, ganancia, fundidos y atenuación durante voz;
WAV estéreo 48 kHz, silencios intactos, sin normalización SFX ni límite de cuatro segundos del kit.
Caché por contenido y audio en huellas de composición, revisión B y render. ADR 0035.
Prueba sintética renderizada: imagen y sonido coinciden dentro de un cuadro a 30 fps; extracción
superior a cuatro segundos, silencios, fundidos y automatización comprobados. Cuatro casos editoriales
ficticios evaluados por el implementador; no equivalen a aceptación de usuarios ni medición de retención.
Ensayo real en copia aislada: QA visual correcto; TikTok y Reels verificados
(77.9 s, −14.2 LUFS, −1.1 dBTP). **271 tests en verde** (321.2 s), incluido guardián de datos personales. La entrega original permanece intacta
y bin/edit --plan confirma que sigue entregable con A/B vigentes.

## Storytelling y criterio editorial — v0.13.0-alpha

Nueva skill `storytelling`: guiones antes de grabar y propuestas trazables al material existente.
`edit-video` incorpora revisión editorial antes de A/B y copy adaptado al canal. Guías canónicas:
[storytelling](../storytelling.md), [edición](../editorial.md) y [procedencia](../editorial-sources.md).
`paper_cut.py --refresh-from-cut` regenera la vista sin reescribir decisiones ni aprobaciones;
valida entradas y reemplaza el Markdown atómicamente. Sin migraciones, nuevos gates ni dependencias.
Reordenar frases continúa fuera del alcance. Planes narrativos opcionales para piezas existentes.
Seis casos ficticios revisados manualmente por el implementador (es/en); evidencia local en
`work/editorial-evaluation/report.md`. No equivalen a evaluación independiente o mejora de retención.
Validación: **252 tests en verde**, ambas skills válidas, catálogo vigente y 81 enlaces locales sin
rutas rotas. Formato habitual del corte comparado byte a byte con la versión anterior en un caso
keep/drop con retoma y sugerencias; sin diferencias.

## Fiabilidad visual — v0.13.0-alpha

QA con ventanas de lectura por elemento: distingue máscaras de revelado y movimiento de entrada
al lienzo de recortes persistentes. Los avisos de zona segura se agrupan y separan entre lectura
(advertencia) y transición (información). Los subtítulos de hasta 0.32 s omiten fundidos de línea,
sin alterar palabras ni tiempos.
`cutout_review` prepara originales, máscaras y composición para inspección del agente; aplica
alternativas deterministas ante dictámenes defectuosos/inciertos. Conserva A, invalida B y presenta
los cambios en la revisión habitual. Incluye huellas, archivo del storyboard y ejecución de prueba.
No hay nuevo modelo ni detector semántico automático. Ver [efectos](../effects.md) y ADR 0032.
Validación: **261 pruebas en verde** (327.1 s), incluido el guardián de datos personales.
Ensayo real en copia aislada: mismo master, mapa de cortes y subtítulos; sustitución de texto detrás
de la persona por tarjeta y preview técnico de 4 s. En ese ensayo, la pieza principal conservaba A sin B; aprobación posterior en la sección de extractos.
QA real: **683 instantes, 0 errores**, 9 advertencias persistentes de zona segura y 77 avisos
transitorios informativos. No equivale a una entrega verificada. Regresiones públicas: cuatro
revelados, subtítulo breve, zonas seguras por fase y dos recortes persistentes rechazados.
Pruebas focalizadas adicionales de restauración ante fallo de escritura y privacidad: 10 en verde.
Matriz pública: **108/108 combinaciones** con QA actual en verde, 186 archivos compilados iguales
a los medidos y cuadros actuales iguales a los de referencia. Se reutilizan el check y el
determinismo inverso de esas mismas composiciones; el informe inicial conserva el fallo detectado
en una entrada al lienzo. Cierre y evidencia: `work/reliability-scenarios/matrix-recheck/report.json`.

## Estado y evaluación editorial — v0.13.0-alpha

Pendientes coherentes al aprobar o avanzar de etapa; preguntas por pieza con decisión final fija
y huella de presentación. Sin configuración se conservan preguntas y huellas anteriores.
Los planes narrativos remiten al estado canónico en lugar de duplicar aprobaciones. ADR 0033.
Evaluación real de vlog preparada: preview completo y revisión B de cuatro preguntas presentados,
archivos abiertos. Gancho, claridad y fidelidad revisados contra fuentes; valoración audiovisual del
usuario recibida: confirma comprensión, pide contexto inicial, recursos más pertinentes y cierre
menos abrupto. Segunda propuesta visual de 76.9 s presentada y abierta: contexto inicial, ruta conceptual
y cierre con 3 s de cola. QA: 712 instantes, cero errores, 11 advertencias y 81 avisos
transitorios. Corte y subtítulos intactos. Esa segunda propuesta requirió ajustar el cierre; aprobación posterior en la sección de extractos. QA de la
primera propuesta: 709 instantes: cero errores, diez advertencias
de zona segura y 79 avisos transitorios. Corte y subtítulos conservados por comparación de huellas. No constituye una medición de retención ni una evaluación independiente.
Validación final: **265 tests en verde** (302.2 s), incluido el guardián de datos personales.
Primer preview de 73.9 s, 1080×1920, video H.264 y audio AAC. En esa ronda no hubo entrega ni aprobación B inferida.

## Extractos audiovisuales breves — v0.13.0-alpha

`media_excerpt` extrae video SDR y WAV desde el mismo intervalo, con fundidos comunes y protección
contra sobrescritura de fuentes/salidas. Cierres de hasta 4 s mediante B-roll y efectos aportados,
sin cambiar el contrato del corte hablado ni habilitar voz de pantalla (ADR 0034).
Tercera propuesta real: prueba de sonido original tras la última frase, con salida a negro/audio.
Inicio, efectos y cierre aprobados explícitamente por el usuario; B registrada el 2026-11-17. Corte y subtítulos
idénticos por huella. QA: 708 muestras, cero errores, diez advertencias y 79 avisos transitorios.
Audio del extracto y del kit: 4 s completos, correlación sin desplazamiento > 0.9999.
Entrega real completada para TikTok y Reels: 77.9 s, 1080×1920, H.264/AAC;
`verify.py` en verde para ambas plataformas. Portadas, copy y subtítulos incluidos; carpeta abierta.
Aceptación editorial de un caso real; no demuestra mejora de retención ni valida todas las capacidades.
Validación: 267 pruebas en verde (221.6 s), incluido el guardián de datos personales.

## Organización del motor

Paquetes por responsabilidad, validador por secciones y nombres del sistema en inglés, sin alias.
Migración reversible disponible en `bin/migrate-layout` (ADR 0019; `docs/migration.md`).
Las revisiones afectadas por la migración requieren aprobación explícita de nuevo.
Validación anterior a dirección v2: 229 pruebas (15 omitidas cuando el entorno no puede generar audio de sistema).
La suite actual y su evidencia se describen en la siguiente sección.

## Dirección de animaciones v2 — incluida en v0.13.0-alpha

Perfiles optativos con controles internos, candidatos con límites y licencias, objetos narrativos y
anclajes por palabra. Previews y producción comparten compositor; QA usa el runtime real y bloquea B
ante errores objetivos o informes obsoletos. Los formatos legado/v1 conservan su HTML; la corrección
de subtítulos breves descrita arriba es independiente de esos formatos.

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

Ensayo técnico adicional con material real de vlog (2026-11-17): matriz de **108/108** combinaciones
con una marca nueva y suite de **252 pruebas en verde** (541.8 s, con renders concurrentes).
La matriz usa ejemplos del catálogo; no certifica todas las combinaciones sobre cualquier toma.
La inspección real encontró objetos ajenos y huecos de ropa en el recorte, y un posible falso positivo
de `container_clip` durante la entrada `text_fx: rise` de una tarjeta (texto completo al asentarse).
El falso positivo y las alternativas conservadoras se atienden en la sección de fiabilidad visual;
cambiar el modelo permanece en backlog. Los borradores técnicos no equivalen a entrega editorial
ni aprobación B.

| Etapa | Estado | Notas |
|---|---|---|
| Instalación y demo | ✅ | `bin/setup` (macOS/Linux), `bin/demo` (canal de ejemplo `science-60`) |
| Primeros pasos | ✅ | `bin/welcome` + `docs/getting-started.md`: de cero a la primera pieza (probado con una copia limpia del repo) |
| Carpetas `input/` y `deliveries/` | ✅ | Originales y finales en la raíz de VideoVibe (fuera de git); el agente siempre muestra las rutas |
| Piezas nuevas | ✅ | `bin/new-piece` (en la carpeta de canales correcta, con `raw/` y `brief.md`); `bin/edit` se detiene sin material o sin brief completo |
| Orquestación (`bin/edit`) | ✅ | Avanza hasta cada pausa; A/B presentan resumen, cuatro preguntas, abren archivos y muestran rutas absolutas. En WSL convierte la ruta y usa la aplicación predeterminada de Windows. `--platform` limita render, verificación y entrega sin invalidar el storyboard aprobado. Las aprobaciones requieren revisión vigente; las anteriores a v0.13.1 se reconocen con `--attest-legacy` si su revisión guardada coincide, o se presentan de nuevo |
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
| B-roll y grabaciones de pantalla | ⚠️ parcial | Insertos visuales con sonido original opcional, cuadro completo, recorte o región de detalle; revisión B a 360×640 y aviso de legibilidad. Probado con una captura de Terminal sobre una toma vertical de 8 s y una pieza hablada real (revisión B aprobada; TikTok, Reels y anuncio verificados). El corte hablado sigue usando tomas a cámara |
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
