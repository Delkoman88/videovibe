# Canales

Un **canal** es todo lo que hace que los videos de una persona o marca se vean y suenen como suyos.
El **motor** (scripts, formatos, presets) es igual para todos. Separarlos permite usar el mismo
sistema para temáticas, estéticas e idiomas distintos.

## Qué tiene un canal (`channels/<id>/`)

| Archivo | Qué define | Lo leen |
|---|---|---|
| `channel.json` | id, nombre, idioma, personas en cámara, plataformas activas, paquetes de formatos, tratamiento de voz (`voice`), volumen de música por defecto (`audio`) | scripts y agente |
| `CHANNEL.md` | identidad, intención, audiencia, tono, principio editorial, guardarraíles, CTA, reglas del canal | agente |
| `style.md` | dirección visual, roles de color, permitido/prohibido, animaciones, tratamiento de imagen | agente |
| `rhythm.md` | gancho, limpieza del corte, densidad, subtítulos, sonido | agente |
| `topics.md` | temas frecuentes con B-roll/gráficos sugeridos y cuidados | agente |
| `brand.json` | colores por función, roles de resaltado, fuentes (archivo), estilo de subtítulos y movimiento, sonido de efectos (`sound`) e identidad musical (`music`) | scripts |
| `vocabulary.txt` | términos que la transcripción debe acertar; los de varias palabras no se parten en subtítulos | scripts |
| `learnings.md` | notas de la persona convertidas en reglas, con fecha | agente |
| `fonts/` (opcional) | fuentes propias del canal; si no, se buscan en `assets/fonts/` | scripts |
| `audio/sfx/` | kit de efectos propio (`scripts/audio/sfx.py --channel <id>`; carácter en `brand.json → sound`) efectos del canal en `recipes.json` y efectos aportados en `user.json` + `user/` (fuera de git) (ver `docs/audio.md`) | compose |
| `assets/lottie/` | animaciones Lottie del canal: `library.json` (origen, licencia, anuncios, colores) y archivos (los de terceros, fuera de git); `scripts/tools/lottie.py` (ver `docs/visual-assets.md`) | compose |
| `assets/images/` | imágenes PNG/JPEG/WebP registradas con origen y licencia para objetos narrativos; `scripts.tools.images add` / `list` (fuera de git) | compose |
| `audio/music/` | biblioteca de música con licencia (`library.json` en git; audios fuera de git). Música propia: `scripts/audio/musicgen.py` (apta para anuncios) | compose |
| `projects/` | las piezas del canal (fuera de git) | todos |

`channels/science-60/` es un ejemplo completo (ficticio).

**Dónde viven los canales:** por defecto en `channels/` del repo. Para separar tus canales del
motor (p. ej. en un repo privado), crea `local.json` en la raíz con `{"channels_dir": "~/mis-canales"}`
o usa la variable `VIDEOVIBE_CHANNELS`. `_template` y `science-60` siempre se leen del motor.

## Capas de reglas y precedencia

1. **Motor** (`AGENTS.md`, reglas universales): no las cambia nadie.
2. **Canal** (`CHANNEL.md` + archivos del canal + `learnings.md`).
3. **Pieza** (`brief.md`): manda sobre el canal para esa pieza.

Si una pieza necesita romper una regla del canal, se anota en su brief («Notas»).

## Alta de un canal

**Lo rápido (primera vez):** `docs/getting-started.md` → `bin/new-channel <id> --about … --person …`
crea un canal completo con valores por defecto que se ajustan con el uso. Lo de abajo es el alta a fondo.

```bash
bin/new-channel <id> --name "Nombre del canal" --lang es   # copia channels/_template/
```
Después, el agente:
1. Hace las preguntas de `templates/channel-brief.md` que no pueda deducir.
2. Redacta los archivos del canal y elimina todos los `TODO`.
3. Propone una paleta por función y dos fuentes con licencia libre (display + mono), las descarga a
   `channels/<id>/fonts/` y registra la licencia.
4. Elige paquetes de formatos (`formats/packs/`); si la temática no tiene paquete, lo anota en
   `docs/status/backlog.md` (crear un paquete es trabajo del motor).
5. Sonido (`docs/audio.md`): ajusta `brand.json → sound` y genera el kit (`scripts/audio/sfx.py --channel <id>`);
   propone 2–3 paletas de `brand.json → music` con un muestrario de `musicgen.py` y fija la que elija la persona.
6. Corre `bin/doctor --channel <id>` hasta que salga limpio.

## Preferencia de animaciones

`brand.json → motion.profile` guarda `restrained`, `balanced` o `energetic`. Antes de fijarla,
presenta dos alternativas con `bin/animation-style --channel <id>`; guarda solo la elección explícita
mediante `--apply <perfil> --run /ruta/absoluta/candidates.json`. El manifiesto comprueba que los
previews y la marca siguen vigentes; la elección también queda en `learnings.md`.

Las propuestas nuevas incorporan el perfil con `--snapshot`; cambiar la preferencia del canal no
reescribe el bloque `motion` de storyboards existentes. Para objetos narrativos activa `narrative`
en `channel.json → format_packs`. Comandos completos, anclajes y compatibilidad:
[dirección de animaciones](animation-direction.md).

## Idiomas

El idioma del canal (`channel.json → language`) necesita `lang/<código>.json`, que define muletillas,
conectores, frases típicas de alucinación de whisper, reglas de subtítulos y etiquetas (p. ej.
«ILUSTRATIVO»). Para un idioma nuevo: copia `lang/en.json`, tradúcelo y pruébalo con
`scripts/tests/test_cut.py` (añade un caso con una voz de `say`).

## Paleta por función

Los formatos y subtítulos no conocen colores concretos, solo funciones:
`bg`, `surface`, `surface_line` (fondos) · `depth`, `depth2` (profundidad, nunca texto) ·
`accent` (palabra clave) · `accent2` (dato) · `accent3` (remate) · `warn` (advertencia) ·
`text`, `muted` (texto). Cada canal asigna sus colores a esas funciones en `brand.json`.

## Estilo de subtítulos y tarjetas

Por defecto todos los canales usan el estilo sobrio del motor. Un canal puede elegir otro en `brand.json`:

| Clave | Valores | Qué cambia |
|---|---|---|
| `captions.style` | `classic` (por defecto) · `neon` | `neon`: el cuerpo queda blanco y la palabra activa cambia de color, escala y glow con separación RGB (pensado para fuentes pixel como Pixelify Sans) |
| `overlays.style` | `panel` (por defecto) · `liquid` | `liquid`: título, tarjetas y CTA con vidrio amorfo, órbita de deck, cable y medidor (estética de música electrónica) |

Los formatos que necesitan librerías opcionales (hoy PixiJS en `pixi-signal` y `pixi-mixer` del paquete
`music`) solo las copian y cargan en las piezas que los usan (ADR 0020).

Cambiar `channel.json` o `brand.json` (por ejemplo, activar un paquete) marca las piezas del canal para
recomponer. Si el HTML resultante no cambia, `bin/edit` lo detecta: las aprobaciones y los renders
siguen válidos y solo se vuelve a verificar la entrega.

`channel.json → beat_snap: true` (canales musicales): la validación del storyboard avisa cuando una escena,
tarjeta o efecto no empieza en un golpe de la música (`docs/effects.md`).
