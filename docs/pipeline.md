# Pipeline

Variables de trabajo (desde la raíz del repo):

```bash
P="<canal>/<fecha>-<slug>"   # pieza, p. ej. science-60/2026-11-12-por-que-sube-el-pan
# (= channels/<canal>/projects/<fecha>-<slug>/; todos los scripts aceptan esta forma corta)
```

## Estructura de una pieza

```
channels/<canal>/projects/<fecha>-<slug>/
├── brief.md            ← objetivo, audiencia, pregunta eje, CTA, plataformas (templates/brief.md)
├── raw/                ← material crudo tal cual (no se modifica nunca)
├── media.json          ← inventario: tipo de toma, orientación, duración, fps (lo genera ingest)
├── transcript/         ← transcripción con tiempos por palabra
├── cut/                ← PAPER-CUT.md, cut-list.json, master-cut.mp4
├── storyboard.json     ← el plan visual: subtítulos, B-roll, zooms, gráficos, sonido
├── snaps/              ← cuadros de revisión del plan
├── renders/            ← <plataforma>.mp4, short.mp4, clips/
├── captions/           ← <plataforma>.srt
├── copy/               ← <plataforma>.md
├── covers/             ← <plataforma>.jpg
├── assets.md           ← fuente y licencia de cada recurso usado
└── faltantes.md        ← recursos visuales que hacen falta
```

## Flujo con `bin/edit` (lo normal)

```bash
bin/new-piece <canal> <slug> --from ~/Descargas/toma.mp4   # pieza nueva: raw/ + brief.md
bin/edit <canal>/<pieza>          # avanza hasta la siguiente pausa; repítelo tras cada pausa
bin/edit <canal>/<pieza> --plan   # qué haría, sin ejecutar
```

`bin/edit` lee `status.json`, ejecuta solo lo que falta o quedó desactualizado y **se detiene** en:

| Pausa | Qué hace el agente | Qué hace la persona |
|---|---|---|
| `material` | Pone los archivos en `raw/` (o `bin/new-piece … --from`) | Entrega el material |
| `brief` | Hace las preguntas ★ de `templates/brief.md` y escribe las respuestas en `brief.md` | Responde |
| `aprobación A` | `bin/edit` presenta el resumen, abre `cut/PAPER-CUT.md`, muestra su ruta y hace cuatro preguntas. Aplica notas en `cut/cut-list.json` y repite la revisión si hay cambios | Aprueba explícitamente el corte → `bin/status <pieza> --approve A` |
| `storyboard` | Escribe `storyboard.json` (`docs/storyboard.md`, `docs/formats.md`); corrige texto en `transcript/master-cut.json` si hace falta | — |
| `aprobación B` | `bin/edit` presenta momentos clave, abre borrador, hoja y vistas de teléfono, muestra sus rutas y hace cuatro preguntas. Ajusta `storyboard.json` y repite si hace falta | Aprueba explícitamente el plan → `bin/status <pieza> --approve B` |
| `copy/portada` | Redacta `copy/<plat>.md` y crea la portada con `scripts/pipeline/cover.py` (ver `templates/deliverables.md`) | Revisa el copy |

- Si se edita `cut-list.json` después de aprobar A, o `storyboard.json`/`captions.json` después de
  aprobar B, la aprobación queda **invalidada** y `bin/edit` pide aprobar otra vez.
- `bin/review <pieza> --gate A|B --reopen` vuelve a abrir los archivos de la revisión. Una aprobación
  nueva requiere que se haya presentado la versión vigente; «ajustar» y «rechazar» se registran con
  `bin/review <pieza> --gate A|B --decision adjust|reject --note "…"`. Si el visor no funciona,
  se muestra la ruta absoluta y la persona puede abrirla manualmente antes de decidir.
- Para copy, portada, audio u otro archivo que deba revisar la persona: `bin/open-review <archivos…>`.
  El comando abre cada archivo una vez y siempre imprime su ruta absoluta.
- `--from-stage <etapa>` rehace desde una etapa; `--until-stage <etapa>` se detiene tras ella.
- Exit 1 = falló una etapa (`check` con errores, `verify` en rojo…): el JSON trae el error y
  `work/edit.log` el detalle de cada comando.
- Plataformas de la pieza: claves de `storyboard.json → platforms` (o las del canal).

## Etapas

| # | Etapa | Script (estado) | Salida |
|---|---|---|---|
| 0 | Brief | — (agente + `templates/brief.md`) | `brief.md` completo |
| 1 | Ingesta | `scripts/pipeline/ingest.py` ✅ — detecta HDR; sincroniza micrófonos externos (`audiosync.py`) | `media.json` (con `mic`), audio 16 kHz |
| 2 | Transcripción | `scripts/pipeline/transcribe.py` ✅ — whisper.cpp tramo por tramo | `transcript/*.json` |
| 3 | Corte en papel | `scripts/pipeline/paper_cut.py` ✅ — retomas, muletillas, conectores sueltos, fragmentos cortos, silencios | `cut/PAPER-CUT.md`, `cut/cut-list.json` |
| **A** | **Revisión: el corte** | La persona responde en lenguaje natural; `bin/status $P --approve A` | `cut-list.json` aprobado |
| 4 | Aplicar corte | `scripts/pipeline/apply_cut.py` ✅ — HDR→SDR BT.709; audio del micrófono si lo hay (verificado por segmento) | `cut/master-cut.mp4`, `cut/cut-map.json` |
| 5 | Subtítulos | `scripts/pipeline/captions.py` ✅ | `transcript/master-cut.json` (texto definitivo, se corrige aquí), `captions/captions.json`, `captions/master.srt` |
| 6 | Plan visual | agente escribe `storyboard.json` (`docs/storyboard.md`) | `storyboard.json` |
| 6b | Validar storyboard | `scripts/pipeline/storyboard.py` ✅ — todos los problemas juntos, con su ruta (compose lo corre también) | — |
| 7 | Composición | `scripts/pipeline/compose.py` ✅ → proyecto HyperFrames en `hf/` (trata la voz y convierte B-roll a H.264 SDR mudo) | `hf/index.html`, `hf/assets/broll-*.mp4`, `hf/variables/<plat>.json`, `cut/master-voice.wav`, `cut/voice-report.json` |
| 8 | Verificación + hoja | `npx hyperframes check` y `snapshot` (desde `hf/`) | 0 errores; `snaps/contact-sheet-*.jpg` |
| **B** | **Revisión: el plan** | La persona ve la hoja, `snaps/phone-*.png` (insertos a tamaño de teléfono) y un borrador `-q draft`; `bin/status $P --approve B` | `storyboard.json` aprobado |
| 9 | Render final | `npx hyperframes render -q delivery --sdr --variables-file variables/<plat>.json -o ../renders/<plat>.mp4` | `renders/<plataforma>.mp4` (con `bin/edit`, solo las plataformas cuyo contenido cambió) |
| 10 | Copy, portadas, clips | agente redacta el copy; portada con `scripts/pipeline/cover.py` (cuadro del gancho o `--at`) | `copy/`, `covers/`, `captions/<plat>.srt`, `clips.json`, `faltantes.md`, `assets.md` |
| 11 | Verificación de entrega | `scripts/pipeline/verify.py` ✅ — lienzo, fps, códec, BT.709, −14 LUFS, pico, duración, archivos | exit 1 = no entregar |
| 12 | Carpeta de entregas | `scripts/pipeline/deliver.py` ✅ — enlaces (o copias si no se puede) en `deliveries/<Canal>/<fecha> <pieza>/` + `README.md`; `bin/edit` la abre | ruta absoluta en `status.json → delivery` |

## Pasos manuales (referencia: lo que `bin/edit` ejecuta)

### Corte

```bash
scripts/pipeline/ingest.py      --project $P   # inventario + audio; revisar `kind` en media.json
scripts/pipeline/transcribe.py  --project $P   # transcript/<id>.json
scripts/pipeline/paper_cut.py   --project $P [--platform tiktok | --pause 0.35]
# → Punto A: mostrar cut/PAPER-CUT.md; al aprobar: bin/status $P --approve A
scripts/pipeline/apply_cut.py   --project $P   # cut/master-cut.mp4
```

Cómo aplicar las notas del punto A:
- «conserva L2 / quita L5»: cambiar `status` de esa línea en `cut/cut-list.json` y correr `apply_cut.py`.
- «más pausa»: volver a correr `paper_cut.py --pause 0.45` y reaplicar los cambios manuales de `status`.
- Error de transcripción: corregir la palabra en `transcript/<id>.json` (campo `w`). Si es un término
  recurrente, agregarlo a `channels/<canal>/vocabulary.txt`.
- Tomas de pantalla (`kind=pantalla`) no entran al corte hablado: se colocan desde `storyboard.json → broll`.
  `in`/`out` marcan cuándo aparecen sobre el master y `source_in` el punto del archivo de pantalla;
  la voz y los subtítulos del master siguen. Para reencuadrar horizontal, usa `fit=cover` y ajusta
  `focus_x` tras mirar la hoja de revisión B; usa `contain` si debe verse toda la interfaz.
  `origin` y `license` quedan registrados automáticamente en `assets.md`.
  Para acercar una zona legible de una captura horizontal, usa `fit=region` y coordenadas
  proporcionales (`region: {x,y,w,h}`). Cada cambio de zona es otro inserto consecutivo; revisa
  sus cuadros de 360×640 en B. `contain` horizontal puede producir un aviso de legibilidad.

### Subtítulos, plan visual y render

```bash
scripts/pipeline/captions.py --project $P            # transcribe el master y arma grupos de subtítulos
# corregir texto/puntuación en transcript/master-cut.json, luego:
scripts/pipeline/captions.py --project $P --from-transcript
# escribir storyboard.json (docs/storyboard.md)
scripts/pipeline/compose.py  --project $P --platform tiktok --platform reels
cd channels/<canal>/projects/<pieza>/hf
npx hyperframes check --json                 # 0 errores antes de seguir
npx hyperframes snapshot --at <momentos clave> --no-end -o ../snaps
npx hyperframes render -q draft --sdr --variables-file variables/tiktok.json -o ../renders/draft-tiktok.mp4
# → Punto B: hoja + borrador; al aprobar: bin/status $P --approve B. Luego render final por plataforma.
```

La persona puede abrir `hf/` en la app de escritorio de HyperFrames para retocar a mano; si lo hace,
`compose.py` sobrescribe sus cambios: después de editar a mano, no volver a correr `compose.py`
sin pasar esos cambios al storyboard.

Tests (después de tocar cualquier script): `.venv/bin/python -m unittest discover -s scripts/tests -v`

## Lecciones con material real

- **Transcribir tramo por tramo.** Una pasada de whisper sobre el archivo completo (con o sin VAD)
  omite muletillas y frases cortas tras una pausa («¿no?», «eh…») y desplaza tiempos hasta 1 s.
  `transcribe.py` transcribe cada tramo de voz por separado: no hay palabras que alinear entre tramos.
  Es más lento (~75 s por 90 s de audio, carga el modelo por tramo; optimizable con whisper-server).
- **Las ventanas cortadas a mitad de frase hacen alucinar a whisper** (en una prueba inventó
  «enfermedades *humanas*»). Nunca transcribir ventanas que corten una frase; verificar dudas
  transcribiendo el tramo completo.
- **Teléfonos graban HDR (HLG).** Sin conversión, el master queda en 8 bits etiquetado HDR: colores
  lavados en redes y render HDR en HyperFrames. `apply_cut.py` convierte a SDR BT.709 (curva hable).
- **Audio de teléfono muy fuerte** (−9.6 LUFS). `compose.py` normaliza la pista a −14 LUFS / −1 dBTP.
- **Voz** (`scripts/audio/voice.py`, lo llama `compose.py`): mide la grabación y aplica solo lo necesario
  (graves < 80 Hz, ruido, ecualización ±3 dB, «s», compresión + expansor para las pausas). El porqué de
  cada paso queda en `cut/voice-report.json`. Para que la persona compare: `scripts/audio/voice.py --project
  … --compare` → `renders/voz-antes-despues.wav` (pares original → bip → tratado, mismo volumen).
  Medido en la primera pieza: el ruido «aparente» eran respiraciones y colas de voz; el piso de ruido
  real se mide en el percentil 10 de los cuadros sin voz. En cortes ajustados las pausas son cortas: el
  expansor necesita liberación rápida (80 ms) o no actúa.
- **whisper pierde puntuación** al transcribir tramos sueltos: revisar la puntuación del gancho
  (pregunta con «¿?») y de nombres propios antes de generar subtítulos.

## Decisiones técnicas

- **Transcripción:** whisper.cpp local (large-v3-turbo q5, español), tramo por tramo, con el texto
  previo como contexto y filtro de alucinaciones. Sin enviar audio a la nube.
- **Composición y render:** HyperFrames 0.9.32 (fijado en `package.json`): HTML/CSS/GSAP renderizado
  a video, local y determinista. FFmpeg (`ffmpeg-full` para HDR) para cortes, color base y audio.
- **Color de la imagen de quien aparece:** conversión HDR→SDR + corrección mínima vía
  `hyperframes media-treatment` (exposición, sombras, temperatura). Nada generativo sobre el rostro.
- **Variantes por plataforma:** una sola composición; lo que cambia (texto de la CTA) son variables
  de HyperFrames con un archivo por plataforma en `hf/variables/`.
- **Cada script:** `--help`, entradas y salidas explícitas, salida JSON en stdout, códigos de salida
  (0 ok, 1 fallo de verificación, 2 error de uso). Así cualquier agente lo usa igual.

## Estado de la pieza

Cada script registra su etapa en `<pieza>/status.json`. `bin/status` lista todas las piezas;
`bin/status $P` muestra una (etapa, aprobaciones A/B, renders verificados). Un agente que retoma una
pieza a medias empieza por ahí.
