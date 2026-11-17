# Recursos visuales: Lottie, moléculas, modelos 3D e imágenes

> Para el agente que arma escenas con animaciones de diseñador o moléculas 3D. Formatos: paquetes `lottie`
> y `molecular`; escenas 3D: paquete `cinematic` (`docs/formats.md`). Decisiones técnicas: ADR 0023 (bibliotecas,
> Lottie), 0024 (moléculas) y 0027 (3D cinematográfico, modelos).

Las imágenes registradas se usan en objetos narrativos reutilizables; consulta «Imágenes» más abajo
y [dirección de animaciones](animation-direction.md) (ADR 0030).

## Qué es y cuándo usarlo

Lottie es el formato de animación vectorial que exportan After Effects (Bodymovin), LottieFiles, Rive y
LottieLab. Sirve para ilustrar una idea con movimiento hecho por un diseñador: un check, un cohete, una célula
que se divide, un ecualizador. VideoVibe las **recolorea con la marca del canal** al componer, así que una
animación de catálogo se ve con la identidad de cada canal.

| Formato | Uso |
|---|---|
| `lottie-scene` | Animación grande con kicker y título opcionales (`full` por defecto) |
| `lottie-accent` | Animación pequeña sobre la toma (`over`) en `x`/`y`, con etiqueta corta opcional |

Parámetros comunes: `anim` (id de la biblioteca), `from`/`to` (segundos de la animación: usar solo un
tramo), `speed` (0.1–4), `loops` (1–20 o `"fill"`: repetir hasta llenar la escena; para animaciones hechas
para bucle), `size`.

## Bibliotecas

- **Motor** (`assets/lottie/`, Apache-2.0, aptas para anuncios): `check-draw`, `pulse-rings`, `spark-burst`,
  `eq-bars`. Las genera `scripts/tools/lottie_builtins.py`.
- **Canal** (`<canal>/assets/lottie/`): las que agrega la persona. `library.json` va en git; los archivos de
  terceros, no (como la música).

Si el canal repite un id del motor, gana el del canal.

## Agregar una animación

```bash
scripts/tools/lottie.py add <archivo.json|.lottie> --channel <id> --id cohete \
    --origin "https://lottiefiles.com/… (autor)" --license "Lottie Simple License" [--ads] [--loop]
scripts/tools/lottie.py preview cohete --channel <id>        # hoja de contacto con la marca
```

- **Origen y licencia son obligatorios** (regla 5 de `AGENTS.md`): pregúntale a la persona si no los sabes.
  `--ads` solo si la licencia permite publicidad pagada; una pieza con plataforma `ads` no deja usar una
  animación sin ese permiso. Cada animación usada queda registrada sola en `<pieza>/assets.md`.
- `add` rechaza lo que no funciona sin red: imágenes externas (exportar con imágenes incrustadas) y capas de
  texto con fuentes (convertirlas a formas). Acepta `.lottie` (dotLottie).
- Archivos sueltos se buscan también en `input/` (como `bin/new-piece`).

## Colores

`add` deja `recolor: "auto"`: los grises van a `text`/`muted`/`surface` según su luz y los colores con
saturación, del más usado al menos usado, a `accent`, `accent2`, `accent3` y `warn`. Para elegir a mano:

```bash
scripts/tools/lottie.py list --channel <id>                                   # paleta original de cada una
scripts/tools/lottie.py recolor cohete --channel <id> --map "#ff3366=accent,#ffffff=text"
scripts/tools/lottie.py recolor cohete --channel <id> --none                 # colores originales
```

El archivo nunca se modifica: el mapa vive en la biblioteca y se aplica al componer.

## De dónde sacar animaciones

- **LottieFiles** (lottiefiles.com): catálogo grande; revisa la licencia de cada animación.
- **After Effects + Bodymovin**, **Rive** o **LottieLab**: animaciones propias o encargadas, exportadas a
  Lottie JSON.
- Para algo muy de marca, lo mejor es un encargo a un diseñador con licencia de uso para el canal.

# Estructuras moleculares (paquete `molecular`)

Proteínas, ADN y moléculas pequeñas en 3D con 3Dmol.js, coloreadas con la marca (una cadena por acento;
ligandos en `accent3`). Cada cuadro se dibuja desde la línea de tiempo de la escena: giros y zoom deterministas.

| Formato | Uso |
|---|---|
| `molecule-spin` | La estructura girando (`degrees`, `axis`), con título y pie (fuente) |
| `molecule-focus` | Gira y la cámara viaja a un sitio (`focus`: `{"chain"}`, `{"resn": "HEM"}`, `{"chain": "A", "resi": [41, 145]}`), resaltado con anillo y etiqueta |
| `molecule-compare` | Dos estructuras lado a lado, giro sincronizado (`left`/`right`: `{structure, label, style}`) |

Estilos (`style`): `auto` (cartoon para proteínas y ácidos nucleicos, bolas y varillas para moléculas
pequeñas), `cartoon`, `stick`, `sphere`, `ballstick` y `surface` (cartoon + superficie translúcida; se calcula
antes del primer cuadro). Color (`color`): `brand` (por defecto), `spectrum` (N→C) o `element`. `zoom` 0.3–4.

## Agregar estructuras

```bash
scripts/tools/structures.py fetch --channel <id> --pdb 6LU7 --id proteasa-covid    # RCSB PDB (CC0)
scripts/tools/structures.py fetch --channel <id> --pubchem ibuprofen                # PubChem 3D (dominio público)
scripts/tools/structures.py add modelo.pdb --channel <id> --id mi-modelo --origin "AlphaFold / laboratorio" --license "…"
scripts/tools/structures.py list --channel <id>      # cadenas, rangos de residuos y ligandos (para `focus`)
scripts/tools/structures.py preview proteasa-covid --channel <id>
```

- La descarga ocurre una vez; el render usa la copia local. La fuente queda en la biblioteca y en `assets.md`.
- `list` dice qué acepta `focus`; la validación del storyboard rechaza cadenas o residuos que no existen.
- En el PDB, un inhibidor peptídico puede venir como cadena propia (en 6LU7 el N3 es la cadena C): revisa
  `list` antes de escribir `focus`.
- Del motor (para probar): `crambin`, `hemoglobin` (1HHO), `dna-dodecamer` (1BNA), `aspirin`, `caffeine`.

## Escenas 3D y modelos (paquete `cinematic`)

Se activa con `channel.json → "format_packs": [..., "cinematic"]`. Todo usa los colores de la marca.

| Formato | Uso |
|---|---|
| `particle-word` | Una palabra o cifra (≤ 16 caracteres) que se arma con miles de partículas: gancho, dato clave |
| `logo-3d` | Nombre del canal o título con volumen que entra girando: apertura o cierre |
| `cell-journey` | Viaje por organelos translúcidos con profundidad de campo (ilustrativo): «dentro de la célula» |
| `model-showcase` | Un modelo 3D de la biblioteca girando con luz de estudio y etiqueta: un equipo, un objeto |
| `space-field` | Fondo 3D con profundidad para un título: portadilla o cambio de capítulo |

- Son escenas `full` de 2–5 s. El render 3D tarda más (≈ 1.5 s de cálculo por segundo de escena con GPU, ≈ 4 s sin GPU: WSL, CI).
- El texto de la escena queda encima de la banda de subtítulos (≤ 1100 px); el título, arriba.
- No las pongas durante el gancho de la pieza si llevan `kicker`: chocan con el título del gancho.

### Agregar modelos

```bash
scripts/tools/models.py add microscopio.glb --channel <id> --id microscopio --origin "Poly Haven (autor)" --license "CC0 1.0" --ads
scripts/tools/models.py list --channel <id>
scripts/tools/models.py preview microscopio --channel <id>
```

- Solo `.glb` (glTF binario) con todo incrustado y ≤ 25 MB. Desde Blender: Exportar → glTF 2.0 → «glTF Binary».
- Fuentes: **Poly Haven** (CC0), **Smithsonian 3D** (CC0 los marcados), **NIH 3D** (revisa cada licencia),
  Sketchfab con filtro de licencia (CC BY pide crédito: queda en `assets.md`). Sin permiso comercial, sin `--ads`.
- Materiales llamados `brand-accent`, `brand-accent2` o `brand-accent3` toman el color de la marca.
- Del motor (para probar): `flask` (matraz Erlenmeyer, generado por `scripts/tools/models.py builtins`).
- Los archivos de terceros quedan fuera de git (`<canal>/assets/models/`); `library.json` sí va en git.

## Iconos científicos

Además de Lucide (líneas, sin prefijo), los formatos que llevan iconos (`draw-diagram`, `sketch-board`,
`sketch-diagram`, `lab-network`…) aceptan:

- `health:<id>` — **Health Icons** (CC0): cuerpo, órganos, equipos médicos, laboratorio, personas, medicamentos.
  Toman el color de la marca. Ej.: `health:dna`, `health:lungs`, `health:microscope`, `health:bacteria`… (lista en
  `formats/icons/health.json` o `formats.icons.all_names()`).
- `bio:<id>` — **Bioicons** (solo los CC0): ilustraciones científicas a color: `bio:mitochondria`, `bio:ribosome`,
  `bio:erlenmeyer-filled`, `bio:96-well-plate`, `bio:crispr-cas9`, `bio:celegans`… Conservan sus colores.
- `morph-icon` solo transforma iconos de Lucide (los de relleno no tienen un trazo que se pueda transformar).
- Cada icono `health:`/`bio:` que usa una pieza queda en su `assets.md` con autor y licencia (automático).
- Agregar más: una línea en `formats/icons/selection-health.txt` o `selection-bio.txt` y
  `scripts/tools/icons.py --sets` (descarga en el commit fijado; descarta los que pesan > 80 KB). Revisa que se
  vean sobre fondo oscuro: los Bioicons negros o con recuadro blanco no sirven.

## Pizarrón y gráficas (paquetes `sketch` y `data`)

| Formato | Uso |
|---|---|
| `sketch-annotate` (`over`) | Señalar algo en la toma con un trazo a mano: `circle`, `underline`, `box`, `arrow`, `cross` en `box` [x, y, ancho, alto] |
| `sketch-board` | Pizarra con título y 2–4 ideas con viñeta o icono: resumen, conclusiones |
| `sketch-diagram` | Proceso de 2–5 pasos a mano, cajas rayadas y flechas |
| `chart-bars` | 2–8 barras que crecen con su valor; `highlight` resalta una |
| `chart-line` | Una curva que se traza; hasta 3 `points` con nota |
| `chart-compare` | Dos grupos (control/tratamiento) con barra de error opcional y la diferencia («×3.5», «+12 %») |

Gráficas:
- Datos en `params.data` (`[{"label", "value"}]` o `[[x, y], …]`) o en un archivo de la pieza:
  `"file": "data/casos.csv"` (columnas label,value o x,y; también `.json`).
- **`source` obligatorio** (estudio, base de datos, año): se muestra al pie. Si los datos no son reales,
  `"illustrative": true` agrega la etiqueta «ILUSTRATIVO».
- `unit` (%, mg, °C…), `decimals` (0–3) y `decimal_comma: true` para escribir 3,5 en vez de 3.5.
- Nunca inventes datos presentados como reales: si la persona no da la fuente, pregunta.

## Imágenes reutilizables en secuencias

El paquete `narrative` admite fotos PNG/JPEG/WebP registradas con origen, licencia y permiso de anuncios
en `<canal>/assets/images/library.json`. Alta/listado: `python -m scripts.tools.images --help`.
La composición incrusta el archivo local y registra créditos en `assets.md`. Ejemplos y anclajes en
[Dirección de animaciones](animation-direction.md). No se transforman rasgos de personas en las imágenes.
