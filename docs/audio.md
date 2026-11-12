# Sonido: voz, música y efectos

Guía única de todo lo que suena en una pieza: qué herramienta usar, cuándo y con qué comando.
Lo que se escribe en el storyboard (`audio`, `voice`) está en `docs/storyboard.md`; aquí está el
**porqué** y el **cómo**.

## Mapa

| Capa | Herramienta | Dónde vive | Licencia |
|---|---|---|---|
| Voz | `scripts/audio/voice.py` (automático dentro de `compose.py`) | `cut/master-voice.wav`, `cut/voice-report.json` | — |
| Música con licencia | Conector MCP de Epidemic Sound + `scripts/audio/music.py add` | `channels/<canal>/audio/music/` | Epidemic: **no** sirve para anuncios con plan personal |
| Música propia | `scripts/audio/musicgen.py` | igual (`library.json → source: propia`) | propia, apta para anuncios |
| Efectos base | `scripts/audio/sfx.py` | `channels/<canal>/audio/sfx/` (en git) | propios |
| Efectos del canal | `audio/sfx/recipes.json` + `scripts/audio/sfx.py` | igual | propios |
| Música aportada | `scripts/audio/music.py add --source usuario` (+ `fit`) | igual | la que declare quien la aporta |
| Efectos aportados | `scripts/audio/sfx.py add` | `audio/sfx/user.json` (git) + `audio/sfx/user/` (fuera de git) | la que declare quien los aporta |
| Micrófono externo | automático en `ingest.py` (`scripts/audio/audiosync.py`) + `apply_cut.py` | `media.json → <toma>.mic` | — |
| Mezcla | `compose.py` (ducking por tiempos de palabra) + `verify.py` | `hf/index.html` | — |
| Licencias | automático: `compose.py` mantiene el bloque «Sonido» de `<pieza>/assets.md` | `assets.md` | — |

Configuración del canal:
- `brand.json → sound`: carácter de los efectos (`root_hz`, `brightness`, `texture`: `clean` o `glitchy`).
- `brand.json → music`: identidad musical (instrumentos). Ver «Identidad musical».
- `channel.json → audio`: volumen de música por defecto (`music_level_db` sin voz, `music_duck_db` bajo la voz).
- `channel.json → voice`: tratamiento de voz (`enabled`, `strength`: `natural` o `fuerte`).

Precedencia, como en todo el sistema: **pieza (storyboard) > canal > motor**.

## Árbol de decisión

**¿Qué música lleva la pieza?** (la respuesta del brief «¿Publicidad pagada?»)
- **no**: Epidemic Sound. Busca con el ánimo de `rhythm.md` del canal, propón 2–3 opciones y la
  persona elige. Ver «Música de Epidemic».
- **sí**: solo pistas con `ads: true` (`scripts/audio/music.py list --channel <canal> --ads`). Si no hay
  una adecuada, genérala con `musicgen.py`.
- **quizá** (por defecto): Epidemic para TikTok y Reels. Si luego se promociona, añade la plataforma
  `ads` (anuncio): el mismo video con la pista propia (`audio.music.ads_track`).

**¿Hace falta un efecto que no está en el kit?** (`scripts/audio/sfx.py --channel <canal> --list`)
- Si uno del kit sirve, úsalo; elige por lo que muestra la pantalla (tabla de efectos más abajo).
- Si no, **escribe una receta** en `audio/sfx/recipes.json`. No programes ni toques el motor.

**¿La voz suena mal?** Revisa `cut/voice-report.json`, que explica cada decisión. Si hace falta,
ajusta `voice` en el storyboard (p. ej. `"denoise": false` si el ambiente es parte de la escena) o
`strength: "fuerte"`. Para comparar: `scripts/audio/voice.py --project <canal>/<pieza> --compare`.

## Voz

`compose.py` llama a `voice.py`, que mide cada grabación y aplica solo lo que hace falta:
1. graves < 80 Hz;
2. ruido (se salta si la voz ya está limpia);
3. ecualización de hasta ±3 dB (barro, presencia, aire);
4. «s» silbantes;
5. compresión con expansor para que las pausas no suban.

Nunca cambia tono, timbre ni duración (regla universal 3). El volumen final (−14 LUFS) lo pone `compose.py`.

## Música de Epidemic Sound

Conexión y clave: `docs/connectors.md`.
1. `SearchRecordings` con términos del ánimo del canal, `vocals: false` y duración mayor que la del video.
2. La persona elige escuchando los `lqmp3Url`.
3. `EditRecording` con `targetDurationMs` = duración del video + 500 ms, `forceDuration: true` y
   `WAV`. Así termina con un cierre musical, sin cortarse.
4. `PollEditRecordingJob`, luego `DownloadRecordingEdit`, y la descarga va a una carpeta temporal.
5. Registra la pista:
   ```bash
   scripts/audio/music.py add --channel <canal> --file <wav> --title "…" --artist "…" --source epidemic \
     --source-id <id> --mood "…" --bpm N --license "Suscripción Epidemic Sound (cuenta de <persona>)"
   ```
   Pasa `--ads` solo si el plan cubre publicidad (Pro/Commercial).
6. Ponla en `storyboard.json → audio.music.track` y anótala en `<pieza>/assets.md`.

## Música propia (`musicgen.py`)

```bash
scripts/audio/musicgen.py --channel <canal> --duration <s del video + 0.5> --mood <ánimo> --seed N \
  [--palette '{"pad":"keys"}'] [--add --title "…"]
```
- **Ánimos:** `esperanzador`, `misterioso`, `energico` y `ambiental`. Cada uno decide escala, tempo,
  progresión y energía (cuánta percusión y bajo hay, y cuánto pesa la atmósfera).
- **Semilla:** cambia progresión, arpegio y melodía. Para dar opciones, genera 2–3 semillas o ánimos,
  sin `--add`, en `work/musicgen/`. Registra solo la que elija la persona (`--add`).
- Siempre dura exactamente lo pedido, tiene estructura (intro → clímax → pausa → final) y deja un
  hueco de ecualización para la voz. Sus pistas quedan con `ads: true`.

### Identidad musical (`brand.json → music`)

| Clave | Opciones | Carácter |
|---|---|---|
| `pad` | `saw` · `keys` · `strings` · `glass` | sintetizador clásico · piano eléctrico · cuerdas · campanas de cristal |
| `lead` | `pluck` · `bell` · `square` · `none` | arpegio pulsado · campana · cuadrada suave · sin arpegio |
| `bass` | `sub` · `pluck` · `none` | grave redondo · bajo rítmico · sin bajo |
| `drums` | `soft` · `electronic` · `halftime` · `breakbeat` · `none` | suave · electrónica · lenta · quebrada · sin percusión |
| `melody` | `true` / `false` | melodía principal en el clímax |
| `swing` | 0–0.3 | balanceo de las corcheas |
| `brightness` | 0–1 | brillo general |

Lo que el canal no fije lo pone el ánimo. Para probar sin tocar la marca, usa `--palette`. Para
fijar la identidad: genera un muestrario con 2–3 paletas, la persona elige y se escribe en
`brand.json → music`.

## Efectos

Kit base (`scripts/audio/sfx.py --channel <canal> --list` muestra el kit del canal con el uso de cada uno):

| Lo que hay en pantalla | Efecto |
|---|---|
| red, idea, conexión | `bell`, `ping` |
| ADN, moléculas, algo nuevo | `sparkle`, `scan` |
| célula, biología | `bubbles` |
| salud, pulso | `heartbeat` |
| agente o herramienta actuando | `zap`, `blip` |
| terminal, código | `typing`, `data` |
| dato fuerte, revelación | `impact` (poco), antes un `riser` que termine justo ahí |
| verificado / error | `success` / `warn` |
| tarjeta o etiqueta | `click` |
| salida de escena | `whoosh` (`sfx_auto.exits`) |

Para que el sonido no se vuelva repetitivo, alterna familias distintas: tonos, ruido, graves y
granulares.

### Recetas: efectos del canal sin programar

`channels/<canal>/audio/sfx/recipes.json`:
```json
{"recipes": {
  "pipeta": {"use": "Gota de pipeta: líquido, muestra", "duration": 0.45,
    "layers": [
      {"type": "tone", "f0": "root/2", "f1": "root*1.4", "harm": 0.1, "decay": 0.05, "length": 0.12},
      {"type": "noise", "lo": 1500, "hi": 6000, "decay": 0.015, "gain": 0.35}],
    "fx": {"reverb": 0.35}}}}
```
- `use` es obligatorio: dice cuándo usarlo. `duration` va de 0.03 a 4 s. `entrance: true` lo suma a
  las entradas que rota `sfx_auto`. Una receta con el nombre de un efecto base lo reemplaza en ese canal.
- **Capas (1–12):**

  | Tipo | Para qué | Campos |
  |---|---|---|
  | `tone` | bleeps, pulsos, láser | `f0`, `f1`, `harm` |
  | `noise` | aire, whoosh, agua | `lo`, `hi`; barrido con `lo1`, `hi1` |
  | `fm` | campana, metal, cristal | `f`, `ratio`, `index`, `index_decay` |
  | `sub` | golpe grave | `f0`, `f1` |
  | `grains` | burbujas, chispas, tecleo | `count`, `f_lo`, `f_hi`, `grain`, `spread`, `rising`, `seed` |

  Campos comunes: `at`, `gain`, `pan`, `attack`, `decay`, `length`, `repeat` + `every` (latidos,
  tecleo).
- **Frecuencias:** en Hz o relativas al tono del canal (`"root"`, `"root*1.5"`, `"root/2"`), para que
  la receta suene en la tonalidad de la marca.
- **`fx`:** `reverb` (0–1), `lowpass`, `highpass` (Hz), `bitcrush` (2–12 bits), `tremolo` (Hz) y
  `tremolo_depth`.
- Flujo:
  1. Escribe la receta y genera el kit (`scripts/audio/sfx.py --channel <canal>`). Los errores dicen el
     campo exacto.
  2. Arma un muestrario con `--preview <nombre> …` (`work/sfx-preview-<canal>.wav`) para que la persona
     lo escuche.
  3. Úsala en el storyboard. `bin/doctor --channel` también valida las recetas.

## Audios aportados por la persona

Antes de registrar cualquier archivo, **pregunta siempre**:
- de dónde viene (quién lo hizo o lo compró);
- qué licencia tiene;
- si permite publicidad pagada.

Sin licencia clara no se usa (regla universal 5).

**Música** (comprada, compuesta, de un amigo):
```bash
scripts/audio/music.py add --channel <canal> --file <ruta> --title "…" --source usuario --provided-by "<persona>" \
  --license "…" [--ads] [--trim] [--bpm N] [--mood "…"]
scripts/audio/music.py fit --channel <canal> --track <id> --duration <s del video + 0.5>
```
- `add` revisa el archivo y avisa en `warnings`: saturación, silencios largos al inicio o al final
  (`--trim` los quita), muestreo bajo o compresión fuerte. Si no pasas `--bpm`, lo estima.
- `fit` crea `<id>-<s>s` a la duración exacta, con la misma licencia:
  - si la pista es más larga, la corta en compás con un fundido de 2 s;
  - si es más corta, repite compases del centro con fundido cruzado.

  Es lo mismo que hace `EditRecording` con las pistas de Epidemic. Si el BPM no es fiable, usa
  fundidos largos y lo avisa.

**Efectos** (sonidos reales: centrífuga, pipeta, teclado del laboratorio):
```bash
scripts/audio/sfx.py add --channel <canal> --file <ruta> --name centrifuga --use "Centrífuga: muestras, laboratorio" \
  --license "Propio (grabado por <persona>)" --provided-by "<persona>" --ads [--entrance]
scripts/audio/sfx.py --channel <canal> --preview centrifuga
```
- El original va a `audio/sfx/user/` (fuera de git) y el registro a `audio/sfx/user.json` (en git).
- En el kit queda una copia sin silencios, con fundidos de 5 ms, pico a −1 dBFS y máximo 4 s.
- Si hay nombres repetidos, gana el efecto aportado sobre la receta, y la receta sobre el efecto base.

**Licencias:** `compose.py` escribe solo el bloque «Sonido» de `<pieza>/assets.md` (entre
`<!-- audio:auto -->` y `<!-- /audio:auto -->`): música normal y de anuncio, efectos propios y aportados,
con su origen y licencia. No lo edites a mano. Si la pieza lleva la plataforma `ads` (anuncio) y usa un
efecto o una pista sin licencia para anuncios, `compose.py` se detiene.

## Micrófono externo

Un micrófono de solapa o una grabadora suena mucho mejor que el teléfono. Para usarlo:
1. Pon su archivo de audio en `raw/` junto al video. Sirve un archivo por toma o una grabación larga
   que cubra varias tomas; si empezó tarde o terminó antes, se usa donde cubra.
2. `ingest.py` (o `bin/edit`) lo sincroniza solo con cada toma (`scripts/audio/audiosync.py`):
   - primero, búsqueda aproximada en toda la grabación;
   - después, ajuste fino al milisegundo en 12 ventanas;
   - y corrige la deriva de reloj entre los dos aparatos.

   Si se sincroniza, el archivo queda como `kind: mic` y la toma recibe `mic` con `offset_s`,
   `drift_ppm`, `covers_s` y `confidence`. La salida (`mic_sync`) explica cada intento.
3. Desde ahí, whisper transcribe el audio del micrófono (mejor transcripción) y `apply_cut.py` arma
   el corte con él. En cada segmento comprueba de nuevo la sincronía (desfase residual ≤ 20 ms); si no
   puede asegurarla, ese segmento usa el audio de la cámara y queda anotado en `cut/cut-map.json`
   (`audio`, `audio_note`).
4. `voice.py` trata la voz del micrófono como cualquier otra.

**Si no se empareja**, la salida dice por qué: no se parecen, no cubre la toma, ventanas en
desacuerdo. Causas típicas:
- el micrófono grabó otra cosa;
- la cámara no grabó audio;
- hay demasiado ruido en la cámara.

Para ayudar, aplaude una vez al empezar a grabar. Como último recurso, escribe el emparejamiento en
`media.json → <toma>.mic` con `"source": "manual"`: `ingest.py` lo respeta. La sincronía de labios es
intocable: ante la duda, el sistema no usa el micrófono.

## Mezcla

- **Música:** −24 sin voz y −32 bajo la voz son buenos puntos de partida (probados en un canal real). El
  ducking sigue los tiempos de las palabras.
- **Efectos:** −18 a −26 dB, solo cuando algo en pantalla los justifica.
- **Comprobación:** `verify.py` mide −14 LUFS ±1 y pico ≤ −1 dB. Lo demás, que la música no tape la
  voz, lo juzga la persona al escuchar el borrador.
