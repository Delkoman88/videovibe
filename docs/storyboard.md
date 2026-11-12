# Contrato de `storyboard.json`

> **Valida siempre después de escribirlo:** `scripts/pipeline/storyboard.py --project <canal>/<pieza>` devuelve
> todos los problemas juntos con la ruta exacta del campo. Es la fuente de verdad de lo permitido;
> `compose.py` lo corre al empezar y no compone si hay problemas.

El storyboard es el plan visual de una pieza **y** la fuente del render: retocar algo es cambiar un
número y volver a correr `scripts/pipeline/compose.py`. Lo escribe el agente después de `captions.py`,
siguiendo el canal (`CHANNEL.md`, `style.md`, `rhythm.md`, `brand.json`) y el brief.

```json
{
  "version": 1,
  "video": "cut/master-cut.mp4",
  "tail_s": 1.5,
  "camera": {
    "origin": "50% 30%",
    "moves": [
      {"type": "punch", "t": 5.55, "scale": 1.08, "until": 7.41},
      {"type": "creep", "t": 50.9, "scale": 1.06, "until": 57.0},
      {"type": "punch", "t": 86.45, "scale": 1.12, "until": 88.98, "release": false}
    ]
  },
  "emphasis": {"w5": "keyword", "w60": "data", "w93": "punchline", "w168": "warning"},
  "broll": [
    {"id": "pantalla-demo", "source": "grabacion-pantalla", "in": 12.0, "out": 16.0,
     "source_in": 3.5, "fit": "cover", "focus_x": 65, "focus_y": 50,
     "origin": "grabación aportada por la persona", "license": "propia", "ads": true}
  ],
  "overlays": [
    {"id": "hook", "type": "title", "in": 0.15, "out": 4.0,
     "kicker": "Ciencia en 60 segundos", "text": "¿Por qué sube el pan?", "role": "keyword"},
    {"id": "nombre", "type": "card", "in": 11.45, "out": 17.2, "kicker": "Divulgador",
     "text": "Alex Ejemplo", "text2": "Química de la cocina", "role": "data"},
    {"id": "cta", "type": "cta", "in": 82.5, "out": 88.98, "kicker": "Ciencia en 60 segundos", "text": "Sígueme", "role": "punchline"}
  ],
  "platforms": {
    "tiktok": {"cta_text": "Sígueme y deja tu pregunta"},
    "reels":  {"cta_text": "Guárdalo y compártelo con alguien de ciencia"}
  },
  "grading": {"adjust": {"exposure": 0.15, "shadows": 0.08, "highlights": -0.05, "contrast": 0.04, "temperature": -0.06}}
}
```

| Clave | Qué es | Reglas |
|---|---|---|
| `tail_s` | Segundos de último cuadro congelado al final | Para que la CTA se lea; 1–2 s |
| `camera.origin` | Ancla del zoom | Arriba (≈30 %) para no cortar la cabeza |
| `camera.moves` | `punch` (0.32 s) o `creep` (lento, de `t` a `until`) | Si `until` coincide con un corte, vuelve a 1.0 de golpe; si no, en 0.5 s. Escala 1.05–1.12 |
| `emphasis` | `id de palabra → rol` (ids de `captions/captions.json`) | Roles de `brand.json → highlight_roles`: keyword, data, punchline, warning (cada canal les asigna color). Máx. 1 rol por grupo de subtítulo, salvo dato + palabra clave |
| `overlays` | Tarjetas en la franja superior (`title`, `card`, `tag`, `cta`) | Una a la vez; nunca sobre la cara; 4–6 s; texto de ≥ 30 px; la `cta` usa el texto de `platforms.<plat>.cta_text` |
| `broll` | Insertos de video mudo sobre la cámara; `source` es un id de `media.json` con `kind=broll` o `kind=pantalla` | `in`/`out` son segundos del master; `source_in` indica dónde empieza el archivo fuente. No se solapan ni pasan del corte. `fit=cover` recorta horizontal a vertical con `focus_x`/`focus_y` (0–100); `contain` muestra el cuadro completo con fondo. `origin` y `license` son obligatorios; `ads:true` si hay plataforma de anuncio. El audio original del inserto se descarta y la voz aprobada continúa. |

Para texto de una grabación horizontal, usa `fit: "region"` con un rectángulo proporcional de
la fuente: `"region": {"x": 0.02, "y": 0.10, "w": 0.30, "h": 0.80}`. El motor lo amplía al lienzo
9:16 sin deformarlo; la parte que no cabe se recorta. Cada inserto tiene una región fija. Para
cambiar de zona, añade otro inserto consecutivo con el mismo `source`, otros `in`/`out` y otra
`region`. Conserva `source_in` según el tiempo de la grabación. La revisión B genera
`snaps/phone-<id>.png` a 360×640 para mirar la legibilidad real; un `contain` horizontal muy
reducido produce un aviso, no bloquea la composición.
| `platforms` | Lo que cambia por plataforma | Hoy: `cta_text`. Se pasa al render como variable |
| `audio` | Música con ducking y efectos | Ver «Sonido» |
| `grading` | Corrección de color (`hyperframes media-treatment`) | Solo corrección natural (`rhythm.md` del canal). Partir de `media-treatment --analyze` |

## Sonido (`audio`)

```json
"audio": {
  "music": {"track": "<id en la biblioteca del canal>", "start": 0, "level_db": -20, "duck_db": -28,
            "fade_in": 1.0, "fade_out": 2.0, "ads": "quiza", "ads_track": "<opcional>"},
  "sfx_auto": {"scenes": "pulse", "overlays": "click", "db": -22},
  "sfx": [{"at": 75.66, "sound": "warn", "db": -18}]
}
```

Qué música y efectos elegir, comandos y recetas: **`docs/audio.md`**. Aquí, solo los campos:

- `music.track`: id en `channels/<canal>/audio/music/library.json`; debe cubrir el video desde `start`.
- `music.level_db` / `duck_db`: volumen sin voz / bajo la voz (si se omiten, los de `channel.json → audio`).
- `music.ads`: `"no"` · `"si"` · `"quiza"` (del brief). `ads_track`: pista para la plataforma `ads` (anuncio)
  (si se omite, la primera del canal con `ads: true` que cubra el video). Cambia por variable (`music_src`).
- `sfx_auto.scenes`: efecto al entrar cada escena (uno, una lista que rota o `"variado"`);
  `sfx_auto.overlays`: al entrar cada tarjeta; `sfx_auto.exits` + `exits_db`: al salir cada escena.
  En cada escena: `"sfx": "<efecto>"` lo fija, `"sfx": false` lo quita, `"sfx_out": false` quita la salida.
- `sfx`: efectos puntuales `{at, sound, db}` en un segundo exacto.

## Voz (`voice`, opcional)

Tratamiento automático de la voz (`scripts/audio/voice.py`, ver `docs/audio.md`). Por defecto lo que diga `channel.json → voice`;
la pieza puede cambiarlo: `"voice": {"strength": "natural"|"fuerte", "denoise": false, "eq": true,
"deess": true, "compress": true, "enabled": true}`. Ejemplo: `"denoise": false` si el sonido ambiente
es parte de la escena (laboratorio, calle).

## Escenas animadas (`scenes`)

Animaciones que ilustran lo que se dice. Cada escena usa un **formato** del catálogo
(`docs/formats.md`, generado desde `formats/`): `core` siempre disponible + los paquetes del canal
(`channel.json → format_packs`).

```json
{"id": "s-dna", "format": "dna-helix", "in": 19.35, "out": 21.65, "layout": "full", "params": {"label": "BIOTECNOLOGÍA × IA"}}
```

- Los textos de las escenas los aporta siempre el storyboard (los formatos no traen textos de canal);
  `compose.py` falla si falta un parámetro obligatorio.
- Layouts: `full` (fondo de marca, tapa la toma; ≈ 2–3.5 s, intercalado con la toma), `over`
  (transparente, sobre la toma) y `bubble` (cara en círculo; revisa si el canal lo permite).
- Cada escena empieza en la palabra que ilustra (o 0.1 s antes); tiempos locales en `params`.
- Lo que parezca dato o comando sin serlo lleva la etiqueta «ilustrativo» del idioma
  (la ponen solos `terminal` y `verify-refs`).
- No encadenar dos escenas `full` seguidas; dejar respiros con la toma entre escenas.
- Quitar tarjetas y movimientos de cámara que caigan dentro de una escena `full`.
- **Formato nuevo:** función con `@fmt(nombre, layout, required, example)` en `formats/core.py` (genérico)
  o en `formats/packs/<tema>.py`, docstring de una línea, y `bin/format-catalog` para regenerar el
  catálogo. `scripts/tests/test_formats.py` lo valida solo con su `example`.

**Los ids de palabra cambian si se vuelve a transcribir** (`captions.py` sin `--from-transcript`).
Después de re-transcribir, revisar `emphasis` (compose.py falla si un id no existe).

Densidad orientativa (de `rhythm.md` del canal): un elemento nuevo (tarjeta o movimiento de
cámara) cada 3–5 s como máximo, y tramos de respiro solo con la persona y subtítulos.
