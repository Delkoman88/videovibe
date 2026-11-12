# Catálogo de formatos de animación

> Generado por `bin/format-catalog` desde `formats/`. No editar a mano.
> Uso en `storyboard.json → scenes` (ver `docs/storyboard.md`). `core` está siempre disponible;
> los paquetes se activan por canal en `channel.json → format_packs`.

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
