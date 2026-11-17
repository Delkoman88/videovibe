# Catálogo de formatos de animación

> Generado por `bin/format-catalog` desde `formats/`. No editar a mano.
> Uso en `storyboard.json → scenes` (ver `docs/storyboard.md`). `core` está siempre disponible;
> los paquetes se activan por canal en `channel.json → format_packs`.
> Para verlos con la marca de un canal: `bin/format-gallery --channel <id>`.

## Paquete `core`

### `agent-flow`

Diagrama vertical: un nodo superior (quien dirige) → varios agentes o pasos → un resultado.

- Layout por defecto: `full`
- Obligatorios: `top`, `agents`, `bottom`
- Ejemplo:

```json
{"id": "s-agent-flow", "format": "agent-flow", "in": 0.0, "out": 3.0, "params": {"kicker": "Sistema", "top": "Director", "agents": ["A", "B", "C"], "bottom": "Resultado", "bottom_at": 2.0}}
```

### `community`

Personas (iniciales) conectándose a un nodo central; palabras clave en secuencia.

- Layout por defecto: `full`
- Obligatorios: `center`, `words`
- Ejemplo:

```json
{"id": "s-community", "format": "community", "in": 0.0, "out": 3.0, "params": {"center": "Proyecto", "words": [["Uno", 0.2], ["Dos", 0.8], ["Tres", 1.6]]}}
```

### `hud-frame`

Marco HUD (esquinas + barrido) alrededor de un objeto en cuadro, con etiqueta.

- Layout por defecto: `over`
- Obligatorios: `box`, `label`
- Ejemplo:

```json
{"id": "s-hud-frame", "format": "hud-frame", "in": 0.0, "out": 3.0, "params": {"box": [330, 250, 730, 680], "label": "Objeto", "sublabel": "Detalle"}}
```

### `particle-title`

Un título que se forma con partículas y letras que convergen (semilla fija).

- Layout por defecto: `over`
- Obligatorios: `text`
- Ejemplo:

```json
{"id": "s-particle-title", "format": "particle-title", "in": 0.0, "out": 3.0, "params": {"text": "Título de prueba", "y": 250}}
```

### `terminal`

Ventana de terminal que escribe comandos, con salida y una curva que se dibuja. Marcada como ilustrativa.

- Layout por defecto: `full`
- Obligatorios: `steps`
- Ejemplo:

```json
{"id": "s-terminal", "format": "terminal", "in": 0.0, "out": 3.0, "params": {"steps": [{"at": 0.3, "cmd": "echo hola", "out": "hola"}, {"at": 1.5, "cmd": "python run.py", "chart": true}]}}
```

### `verify-refs`

Lista de fuentes o afirmaciones que se verifican; las falsas se tachan en ámbar. Marcada como ilustrativa.

- Layout por defecto: `full`
- Obligatorios: `rows`
- Ejemplo:

```json
{"id": "s-verify-refs", "format": "verify-refs", "in": 0.0, "out": 3.0, "params": {"title": "FUENTES", "rows": [["Fuente A", "ok", "ok", 0.5], ["Fuente B", "falla", "bad", 1.5]]}}
```

## Paquete `biotech`

### `dna-helix`

Doble hélice de ADN girando, con pares de bases; partículas de fondo fijas.

- Layout por defecto: `full`
- Obligatorios: —
- Ejemplo:

```json
{"id": "s-dna-helix", "format": "dna-helix", "in": 0.0, "out": 3.0, "params": {"label": "BIOTECNOLOGÍA"}}
```

### `health-trio`

Tres conceptos en secuencia: célula (entender), pulso (salud), barra de vida (vivir más). Con `only` (0, 1 o 2) muestra un solo concepto: para intercalarlos con la toma en cortes cortos.

- Layout por defecto: `full`
- Obligatorios: `labels`
- Ejemplo:

```json
{"id": "s-health-trio", "format": "health-trio", "in": 0.0, "out": 3.0, "params": {"labels": ["Uno", "Dos", "Tres"], "kickers": ["01", "02", "03"]}}
```

### `lab-network`

Un nodo central (1 persona + IA) que se expande en módulos biotech con íconos; fondo de secuencias ATCG y retícula molecular muy tenues.

- Layout por defecto: `full`
- Obligatorios: `core`, `core_label`, `modules`
- Ejemplo:

```json
{"id": "s-lab-network", "format": "lab-network", "in": 0.0, "out": 3.0, "params": {"core": "1", "core_label": "persona", "plus": "+ IA", "modules": [["Genómica", "adn"], ["Proteínas", "proteina"], ["Células", "celula"], ["Fármacos", "farmaco"]]}}
```

## Paquete `cinematic`

### `cell-journey`

La cámara viaja por un espacio con organelos translúcidos (membranas con brillo en el borde y núcleos de color), polvo y profundidad de campo: lo cercano y lo lejano se desenfocan. Título y pie opcionales; `density` 0.3–2 (cuántos organelos).

- Layout por defecto: `full`
- Obligatorios: —
- Librerías: `three`
- Ejemplo:

```json
{"id": "s-cell-journey", "format": "cell-journey", "in": 0.0, "out": 3.0, "params": {"kicker": "VIAJE AL INTERIOR", "title": "Dentro de la *célula*", "caption": "Ilustrativo · no a escala"}}
```

### `logo-3d`

Título o nombre del canal en 3D: letras con volumen (fuente del canal, degradado de acento), entran girando, se asientan con un destello de luz que las recorre y bloom. `text` ≤ 16 caracteres.

- Layout por defecto: `full`
- Obligatorios: `text`
- Librerías: `three`
- Ejemplo:

```json
{"id": "s-logo-3d", "format": "logo-3d", "in": 0.0, "out": 3.0, "params": {"text": "OPEN LAB", "kicker": "PRESENTA", "caption": "Ciencia abierta, en 3D"}}
```

### `model-showcase`

Un modelo 3D (.glb de la biblioteca `models`) gira con luz de estudio, reflejos y un piso de luz del color de acento; título arriba y etiqueta abajo. Los materiales `brand-accent*` toman los colores de la marca. `degrees` 0–720 (giro total).

- Layout por defecto: `full`
- Obligatorios: `model`
- Librerías: `three`
- Ejemplo:

```json
{"id": "s-model-showcase", "format": "model-showcase", "in": 0.0, "out": 3.0, "params": {"model": "flask", "kicker": "EN EL LABORATORIO", "label": "Matraz Erlenmeyer", "sublabel": "Modelo 3D de ejemplo del motor"}}
```

### `particle-word`

Miles de partículas (semilla fija) vuelan desde el fondo y forman una palabra o cifra con los colores de acento; luego respiran con un brillo suave. `text` ≤ 16 caracteres, `count` 2000–30000.

- Layout por defecto: `full`
- Obligatorios: `text`
- Librerías: `three`
- Ejemplo:

```json
{"id": "s-particle-word", "format": "particle-word", "in": 0.0, "out": 3.0, "params": {"text": "CRISPR", "kicker": "UNA PALABRA", "caption": "Miles de partículas, siempre las mismas"}}
```

### `space-field`

Fondo 3D con profundidad para un título: rejilla de luz que se pierde en la niebla, polvo y orbes desenfocados; la cámara avanza despacio. Sirve de portadilla o separador de capítulos.

- Layout por defecto: `full`
- Obligatorios: `title`
- Librerías: `three`
- Ejemplo:

```json
{"id": "s-space-field", "format": "space-field", "in": 0.0, "out": 3.0, "params": {"kicker": "CAPÍTULO 2", "title": "Lo que *no* vemos", "caption": "Un fondo con profundidad"}}
```

## Paquete `data`

### `chart-bars`

Barras que crecen desde cero con su valor contando encima; eje con números redondos (d3), una barra resaltada en acento (`highlight` = su etiqueta) y la fuente al pie. 2–8 barras.

- Layout por defecto: `full`
- Obligatorios: `source`
- Librerías: `d3`
- Ejemplo:

```json
{"id": "s-chart-bars", "format": "chart-bars", "in": 0.0, "out": 3.0, "params": {"kicker": "DATOS ABIERTOS", "title": "Artículos en *acceso* abierto", "unit": "%", "data": [{"label": "2016", "value": 32}, {"label": "2018", "value": 39}, {"label": "2020", "value": 47}, {"label": "2022", "value": 54}, {"label": "2024", "value": 61}], "highlight": "2024", "source": "Fuente: ejemplo para la galería", "illustrative": true}}
```

### `chart-compare`

Dos grupos lado a lado (control y tratamiento, antes y después): barras con barra de error opcional (`error`), valores que cuentan y la diferencia resaltada con un corchete y «×N» o «+N». Exactamente 2 grupos.

- Layout por defecto: `full`
- Obligatorios: `source`
- Librerías: `d3`
- Ejemplo:

```json
{"id": "s-chart-compare", "format": "chart-compare", "in": 0.0, "out": 3.0, "params": {"kicker": "RESULTADO", "title": "Con el *tratamiento*", "unit": "%", "decimals": 0, "data": [{"label": "Control", "value": 18, "error": 4}, {"label": "Tratamiento", "value": 63, "error": 6}], "source": "Fuente: ejemplo para la galería", "illustrative": true}}
```

### `chart-line`

Curva que se traza de izquierda a derecha con área suave debajo; hasta 3 puntos clave (`points`) se marcan con un círculo y una nota cuando la línea llega a ellos. Eje con números redondos (d3).

- Layout por defecto: `full`
- Obligatorios: `source`
- Librerías: `d3`, `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-chart-line", "format": "chart-line", "in": 0.0, "out": 3.0, "params": {"kicker": "TENDENCIA", "title": "Genomas *secuenciados*", "unit": "", "data": [[2001, 1], [2005, 3], [2008, 12], [2011, 140], [2014, 1200], [2017, 6800], [2020, 21000], [2023, 52000]], "points": [{"x": 2008, "label": "Nueva secuenciación"}, {"x": 2023, "label": "Hoy"}], "source": "Fuente: ejemplo para la galería", "illustrative": true}}
```

## Paquete `lottie`

### `lottie-accent`

Una animación Lottie pequeña sobre la toma (sello, check, pulso, flecha) en una posición elegida, con etiqueta corta opcional. Para subrayar un momento sin tapar a la persona.

- Layout por defecto: `over`
- Obligatorios: `anim`
- Librerías: `lottie`
- Ejemplo:

```json
{"id": "s-lottie-accent", "format": "lottie-accent", "in": 0.0, "out": 3.0, "params": {"anim": "pulse-rings", "x": 540, "y": 560, "size": 360, "label": "AQUÍ", "loops": "fill"}}
```

### `lottie-scene`

Una animación Lottie grande (tramo, velocidad y repeticiones a elegir), con kicker y título opcionales que entran letra por letra. Para ilustrar una idea con movimiento de diseñador.

- Layout por defecto: `full`
- Obligatorios: `anim`
- Librerías: `lottie`
- Ejemplo:

```json
{"id": "s-lottie-scene", "format": "lottie-scene", "in": 0.0, "out": 3.0, "params": {"anim": "check-draw", "kicker": "VERIFICADO", "title": "Los datos *cuadran*"}}
```

## Paquete `molecular`

### `molecule-compare`

Dos estructuras lado a lado girando sincronizadas (p. ej. normal vs. mutada, fármaco vs. fármaco), cada una con su etiqueta y color de acento.

- Layout por defecto: `full`
- Obligatorios: `left`, `right`
- Librerías: `3dmol`
- Ejemplo:

```json
{"id": "s-molecule-compare", "format": "molecule-compare", "in": 0.0, "out": 3.0, "params": {"kicker": "COMPARA", "left": {"structure": "aspirin", "label": "Aspirina"}, "right": {"structure": "caffeine", "label": "Cafeína"}}}
```

### `molecule-focus`

La estructura completa gira un momento y la cámara viaja hasta un sitio (cadena, residuos o ligando, p. ej. {"resn": "HEM"}), que se resalta en color con un anillo y una etiqueta. Para señalar dónde ocurre algo.

- Layout por defecto: `full`
- Obligatorios: `structure`, `focus`, `label`
- Librerías: `3dmol`
- Ejemplo:

```json
{"id": "s-molecule-focus", "format": "molecule-focus", "in": 0.0, "out": 3.0, "params": {"structure": "hemoglobin", "focus": {"resn": "HEM", "chain": "A"}, "label": "Grupo hemo: aquí se une el O₂", "kicker": "SITIO ACTIVO"}}
```

### `molecule-spin`

Proteína, ADN o molécula girando despacio en 3D, con los colores de la marca por cadena (estilos cartoon, stick, sphere, surface o ballstick; `auto` elige según el tamaño), título y pie con la fuente.

- Layout por defecto: `full`
- Obligatorios: `structure`
- Librerías: `3dmol`
- Ejemplo:

```json
{"id": "s-molecule-spin", "format": "molecule-spin", "in": 0.0, "out": 3.0, "params": {"structure": "hemoglobin", "kicker": "PROTEÍNA", "title": "La *hemoglobina*", "caption": "PDB 1HHO · 2 cadenas + grupos hemo"}}
```

## Paquete `motion`

### `data-reveal`

Un dato grande que se descifra y cuenta hasta su valor dentro de un medidor circular (lleno al % si es porcentaje), con etiqueta, fuente y etiqueta «ilustrativo» opcional.

- Layout por defecto: `full`
- Obligatorios: `value`, `label`
- Librerías: `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-data-reveal", "format": "data-reveal", "in": 0.0, "out": 3.0, "params": {"value": "87%", "label": "de los datos ya son abiertos", "kicker": "EL DATO", "source": "Fuente: ejemplo 2026", "illustrative": true}}
```

### `draw-diagram`

Proceso de 2 a 5 pasos en zigzag: cada nodo se dibuja con su icono, las conexiones se trazan solas y un pulso de luz las recorre de paso en paso.

- Layout por defecto: `full`
- Obligatorios: `steps`
- Librerías: `gsap:DrawSVGPlugin`, `gsap:MotionPathPlugin`
- Ejemplo:

```json
{"id": "s-draw-diagram", "format": "draw-diagram", "in": 0.0, "out": 3.0, "params": {"title": "Del dato al hallazgo", "kicker": "PROCESO", "steps": [{"icon": "database", "label": "Datos abiertos"}, {"icon": "bot", "label": "Análisis con IA"}, {"icon": "microscope", "label": "Validación"}, {"icon": "lightbulb", "label": "Hallazgo"}]}}
```

### `kinetic-title`

Título que se arma letra por letra (variantes rise, wave, blur, mask); *palabra* va en color de acento, con kicker que se descifra y una barra que se dibuja.

- Layout por defecto: `over`
- Obligatorios: `text`
- Ejemplo:

```json
{"id": "s-kinetic-title", "format": "kinetic-title", "in": 0.0, "out": 3.0, "params": {"text": "La ciencia *abierta* cambia todo", "kicker": "CAPÍTULO 01", "variant": "rise"}}
```

### `morph-icon`

Un icono grande que se transforma en el siguiente (2 a 4 etapas) con un anillo de progreso y la etiqueta de cada etapa; el color avanza por los acentos de la marca.

- Layout por defecto: `full`
- Obligatorios: `stages`
- Librerías: `gsap:MorphSVGPlugin`, `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-morph-icon", "format": "morph-icon", "in": 0.0, "out": 3.0, "params": {"kicker": "DE LA IDEA AL RESULTADO", "stages": [{"icon": "lightbulb", "label": "Una idea"}, {"icon": "flask-conical", "label": "Un experimento"}, {"icon": "trophy", "label": "Un resultado"}]}}
```

### `particle-burst`

Remate: el texto golpea en pantalla mientras una explosión de partículas de la marca sale despedida con física (gravedad, ángulos y velocidades fijas por semilla) y una onda de choque se expande.

- Layout por defecto: `over`
- Obligatorios: `text`
- Librerías: `gsap:Physics2DPlugin`
- Ejemplo:

```json
{"id": "s-particle-burst", "format": "particle-burst", "in": 0.0, "out": 3.0, "params": {"text": "¡Funcionó!", "kicker": "RESULTADO"}}
```

### `path-journey`

Una ruta curva que se dibuja mientras un punto de luz viaja de parada en parada (2 a 5): cada parada se enciende con su etiqueta y nota al llegar el punto. Ideal para cronologías e historias.

- Layout por defecto: `full`
- Obligatorios: `stops`
- Librerías: `gsap:DrawSVGPlugin`, `gsap:MotionPathPlugin`
- Ejemplo:

```json
{"id": "s-path-journey", "format": "path-journey", "in": 0.0, "out": 3.0, "params": {"title": "Cómo llegamos aquí", "kicker": "EL CAMINO", "stops": [{"label": "2024", "note": "La primera idea"}, {"label": "2025", "note": "El primer laboratorio"}, {"label": "2026", "note": "Ciencia abierta"}]}}
```

## Paquete `music`

### `patchbay-dream`

Recursos entran como canales de una mezcladora y se rutean por cables luminosos hacia la salida `output` (el nombre del artista o la idea final).

- Layout por defecto: `full`
- Obligatorios: `inputs`, `output`
- Ejemplo:

```json
{"id": "s-patchbay-dream", "format": "patchbay-dream", "in": 0.0, "out": 3.0, "params": {"kicker": "ROUTE THE SIGNAL", "inputs": ["RECURSOS", "EXPERIENCIA", "DECISIÓN"], "output": "MASTER", "output_at": 2.0}}
```

### `pixi-mixer`

Consola de mezcla PixiJS: canales pixel-neón convergen en la salida `output` con bloom y glitch.

- Layout por defecto: `full`
- Obligatorios: `inputs`, `output`
- Librerías: `pixi`
- Ejemplo:

```json
{"id": "s-pixi-mixer", "format": "pixi-mixer", "in": 0.0, "out": 3.0, "params": {"kicker": "PATCH THE DREAM", "inputs": ["RECURSOS", "EXPERIENCIA", "DECISIÓN"], "output": "MASTER", "output_at": 1.9}}
```

### `pixi-signal`

Señal pixelada construida con PixiJS: waveform, platter, bloom y separación RGB.

- Layout por defecto: `over`
- Obligatorios: `text`
- Librerías: `pixi`
- Ejemplo:

```json
{"id": "s-pixi-signal", "format": "pixi-signal", "in": 0.0, "out": 3.0, "params": {"text": "MÚSICA = MAGIA", "kicker": "LIVE // SIGNAL"}}
```

### `signal-spell`

La frase emerge de una señal de osciloscopio con anillos de deck y glitch controlado.

- Layout por defecto: `over`
- Obligatorios: `text`
- Ejemplo:

```json
{"id": "s-signal-spell", "format": "signal-spell", "in": 0.0, "out": 3.0, "params": {"text": "MÚSICA = MAGIA", "kicker": "LIVE // SIGNAL", "y": 310}}
```

## Paquete `narrative`

### `narrative-sequence`

Proceso, comparación o acercamiento con un elemento persistente y etiquetas sucesivas.

- Layout por defecto: `full`
- Obligatorios: `recipe`, `steps`
- Ejemplo:

```json
{"id": "s-narrative-sequence", "format": "narrative-sequence", "in": 0.0, "out": 3.0, "params": {"recipe": "process", "steps": [{"text": "Observa"}, {"text": "Compara"}, {"text": "Explica"}]}}
```

## Paquete `sketch`

### `sketch-annotate`

Señala algo de la toma con un trazo a mano: `circle` (lo rodea), `underline`, `box`, `arrow` (flecha que llega desde la etiqueta) o `cross` (tacha), con etiqueta corta opcional. `box` = [x, y, ancho, alto].

- Layout por defecto: `over`
- Obligatorios: `box`
- Librerías: `rough`, `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-sketch-annotate", "format": "sketch-annotate", "in": 0.0, "out": 3.0, "params": {"box": [300, 560, 480, 360], "shape": "circle", "label": "¡Aquí está!", "role": "accent"}}
```

### `sketch-board`

Pizarra: un título que se subraya a mano y 2–4 ideas que aparecen una por una con su viñeta dibujada (círculo o el icono que se indique, Lucide, Health Icons o Bioicons), dentro de un marco a mano.

- Layout por defecto: `full`
- Obligatorios: `title`, `items`
- Librerías: `rough`, `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-sketch-board", "format": "sketch-board", "in": 0.0, "out": 3.0, "params": {"kicker": "EN RESUMEN", "title": "Ciencia *abierta*", "items": [{"text": "Datos que cualquiera revisa", "icon": "health:database"}, {"text": "Métodos paso a paso", "icon": "bio:erlenmeyer-filled"}, {"text": "Resultados replicables", "icon": "check"}]}}
```

### `sketch-diagram`

Proceso de 2–5 pasos dibujado a mano: cajas con relleno rayado del color de acento, icono y etiqueta, y flechas trazadas de una a otra en zigzag (como draw-diagram, pero en pizarrón).

- Layout por defecto: `full`
- Obligatorios: `steps`
- Librerías: `rough`, `gsap:DrawSVGPlugin`
- Ejemplo:

```json
{"id": "s-sketch-diagram", "format": "sketch-diagram", "in": 0.0, "out": 3.0, "params": {"title": "Del *gen* a la proteína", "steps": [{"label": "ADN", "icon": "health:dna"}, {"label": "ARN mensajero", "icon": "bio:ribosome"}, {"label": "Proteína", "icon": "health:enzyme"}]}}
```
