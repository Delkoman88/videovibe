# Efectos sobre la toma

> Para el agente que escribe el plan visual. Efectos que actúan **sobre la toma**: la persona, la música y
> los cortes. Los formatos animados (escenas y tarjetas) están en `docs/formats.md`. Decisiones: ADR 0025
> (recorte), 0026 (ritmo) y 0028 (transiciones).

## Recorte de la persona (`storyboard.json → fx`)

El motor separa a la persona del fondo con el modelo local de HyperFrames (`remove-background`) y la pone
en una capa propia. **Solo cambia de capa: nunca altera rasgos, piel ni forma** (regla 3 de `AGENTS.md`).

| `type` | Qué hace | Campos |
|---|---|---|
| `text-behind` | Texto grande **detrás** de la persona: la cabeza tapa parte del texto | `in`, `out`, `text` (`*palabra*` en acento), `role`, `size`, `y` (`auto` por defecto: a la altura de la cabeza), `variant` (`rise`, `wave`, `blur`, `mask`), `depth`: `behind` (por defecto), `front` (delante) o `through` (aparece delante y luego queda detrás; `pass_at` = segundos desde `in`) |
| `background-swap` | El fondo se cambia por el de la marca (con `text` opcional detrás de la persona) | `in`, `out`, `text`, `role` |
| `subject-glow` | Halo del color de un rol alrededor de la persona | `in`, `out`, `role` |
| `freeze-cutout` | Congela el cuadro, la persona queda con contorno de acento y una etiqueta | `at`, `duration` (0.5–2.5 s), `label`, `label_y` (240 por defecto) |

```json
"fx": [
  {"id": "titulo", "type": "text-behind", "in": 8.0, "out": 11.0, "text": "CIENCIA *ABIERTA*"},
  {"id": "brillo", "type": "subject-glow", "in": 26.5, "out": 28.5, "role": "data"},
  {"id": "yo", "type": "freeze-cutout", "at": 38.24, "duration": 0.5, "label": "Este soy yo"}
]
```

Reglas:
- **`freeze-cutout` solo en pausas sin voz.** Congelar mientras se habla dejaría los labios quietos con la
  voz sonando; la validación lo rechaza con el tiempo de la palabra que choca. En cortes apretados (sin
  pausas ≥ 0.5 s) no se usa.
- Un efecto a la vez (no se solapan) y nunca dentro de una escena `full` (la tapa).
- 2–6 s por efecto. El recorte cuesta ≈ 6 s de cálculo por segundo de video **la primera vez**
  (`work/cutout/`, caché por huella del corte); recomponer después es instantáneo.
- Texto ≥ 28 px y por encima de la banda de subtítulos (`y` ≤ 1100).
- Funciona con la cámara: el recorte vive dentro de `#cam`, así que un `punch` lo mueve junto con la toma.
- **Cámara fija = recorte estable.** El modelo decide cuadro por cuadro y a veces toma un pedazo de fondo
  (cortina, silla) como persona y al siguiente no: el fondo «parpadea». Con cámara fija, el motor reconstruye
  el fondo real del propio tramo y descarta lo que es igual a él y aparece solo un instante
  (`scripts/pipeline/matte.py`); también rellena el cuerpo cuando el modelo lo pierde unos cuadros (ropa
  oscura sobre fondo oscuro) o el movimiento rápido lo emborrona. El cuerpo y las manos se conservan. Con
  cámara en mano no se puede reconstruir el fondo y queda el recorte original: para estos efectos, mejor grabar
  con el teléfono fijo.
- **Al grabar para `subject-glow` o `background-swap`:** que no asomen objetos pegados a la persona (respaldo
  alto de la silla, cojines, lámpara detrás de la cabeza). El modelo los toma como parte de la persona todo el
  tramo: el halo los rodea y el fondo nuevo no los tapa. Silla baja o fondo despejado detrás de los hombros.

Para ver los recortes sin componer: `scripts/pipeline/cutout.py --project <pieza>` (salida JSON con los
archivos y `subject_top`, la fila donde empieza la cabeza).

## Ritmo (`storyboard.json → beat_fx`)

`scripts/pipeline/beats.py --project <pieza>` escribe `<pieza>/audio/beats.json` con los golpes en el tiempo
del video (`beats`, `downbeats` = primer tiempo de cada compás, `bpm`). `compose.py` lo calcula solo cuando
hay `beat_fx` (caché por huella).

- Fuente `music` (si hay `audio.music.track`): usa el BPM de la biblioteca y busca la fase en los ataques
  del audio (±30 ms). Sin BPM en la biblioteca, usa el detector de HyperFrames tal cual.
- Fuente `plate` (`--source plate`): el audio de la toma, para cuando la música suena en la cámara (DJ).

```json
"beat_fx": [
  {"in": 4.0, "out": 8.0, "fx": "pulse", "every": "bar", "strength": 0.5},
  {"in": 59.0, "out": 64.0, "fx": "flash", "every": "bar", "strength": 0.6}
]
```

| `fx` | Qué hace |
|---|---|
| `pulse` | La toma late (micro-zoom) en cada golpe |
| `shake` | Sacudida corta en cada golpe |
| `flash` | Destello del color de acento (debajo de tarjetas y subtítulos) |
| `strobe` | Destellos cortos alternando los acentos de la marca (para tramos de música sin voz) |

`every`: `beat`, `half` (uno sí, uno no), `bar` (compás), `2bars`. `strength` 0–1.

Reglas:
- No se solapan. Fuerte (`strength` > 0.6) mientras la persona habla, distrae: la validación lo avisa.
- Van en una envoltura de la cámara (`#beatwrap`): conviven con `camera.moves` sin pelearse.
- **Sincronía:** con `channel.json → "beat_snap": true`, la validación avisa cuando una escena, tarjeta o
  `fx` empieza a más de 80 ms de un golpe (lee `audio/beats.json`; corre `beats.py` antes de escribir el
  storyboard). Pensado para canales musicales.

## Transiciones (`storyboard.json → transitions`)

Capas que **cubren el cuadro un instante** con el máximo justo en `at`: el corte (de toma a toma, de toma a
escena o al revés) ocurre debajo y no se ve el salto. Van encima de la toma, el B-roll y las escenas, y debajo
de tarjetas y subtítulos (la frase sigue legible).

```json
"transitions": [
  {"at": 19.35, "kind": "scribble"},
  {"at": 45.3, "kind": "word-wall", "word": "Agentes", "duration": 0.9},
  {"at": 64.9, "kind": "zoom-lines", "role": "accent2"}
]
```

| `kind` | Qué hace | Sonido por defecto |
|---|---|---|
| `flash` | Destello blanco teñido del acento | `impact` |
| `light-leak` | Fugas de luz de colores de la marca que cruzan el cuadro | `whoosh` |
| `scribble` | Un trazo a mano grueso tapa todo y se borra | `whoosh` |
| `word-wall` | Un muro de la palabra (`word`, ≤ 14 caracteres) entra por filas y sale | `click` |
| `glitch` | Barras de color y un golpe del acento en el corte | `zap` |
| `zoom-lines` | Líneas de velocidad desde el centro y destello | `whoosh` |

Campos: `at` (segundo del corte, obligatorio), `duration` 0.4–1.2 s (0.7 por defecto; el máximo cae a la
mitad), `role` (`accent`, `accent2`, `accent3`), `sfx` (otro efecto del kit, o `false` para quitarlo), `sfx_db`
(−18 por defecto). Si el sonido por defecto no está en el kit del canal, la transición va sin sonido.

Reglas:
- `at` en un corte del master o en el borde de una escena o B-roll (±0.25 s); si no, la validación avisa: en
  otro punto solo tapa la toma sin esconder nada.
- Al menos 1.5 s entre transiciones; 2–4 por pieza. Para cambios de tema o de bloque, no en cada corte.
- `word-wall` es decoración (la palabra se repite): elige una que ya se escuche en la voz.
