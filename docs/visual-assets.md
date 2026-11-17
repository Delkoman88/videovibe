# Recursos visuales: animaciones Lottie y estructuras moleculares

> Para el agente que arma escenas con animaciones de diseñador o moléculas 3D. Formatos: paquetes `lottie`
> y `molecular` (`docs/formats.md`). Decisiones técnicas: ADR 0023 (bibliotecas, Lottie) y 0024 (moléculas).

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
