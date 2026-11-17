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
