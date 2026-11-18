# Dirección de animaciones

La función es optativa por pieza. `storyboard.json → motion` guarda el perfil resuelto y su versión;
cambiar `brand.json` no modifica propuestas existentes. Sin `motion`, y con perfiles v1, se conserva
el HTML anterior (fixtures de compatibilidad de todos los formatos).

## Comparar y guardar un estilo

```sh
bin/animation-style --channel <canal> --profiles restrained,balanced
bin/animation-style --channel <canal> --project <canal>/<pieza> --profiles balanced,energetic --plate-start 12
```

Cada ejecución crea una carpeta distinta en `work/animation-style/<canal>/`. Produce dos videos de
18 segundos y sus versiones 360×640: título, desarrollo interno y transiciones, con idénticos texto,
voz, duración y encuadre. Con pieza exige A y usa un fragmento de su corte; si este es corto, lo repite
solo en la comparación. Abre los previews y muestra rutas absolutas y cuatro preguntas. `--no-open`
permite automatización. No altera ni aprueba la pieza.

Tras una elección explícita:

```sh
bin/animation-style --channel <canal> --apply balanced --run /ruta/absoluta/candidates.json
```

El manifiesto conserva perfiles, origen, versión del motor y hashes de la marca y los videos. La
selección falla si cambió la marca o un preview. Sin `--run` usa la comparación más reciente.
La preferencia se guarda en la marca y en `learnings.md`; las propuestas anteriores quedan intactas.

## Propuesta y anclajes

```sh
bin/animation-style --channel <canal> --project <pieza> --snapshot --dry-run
bin/animation-style --channel <canal> --project <pieza> --snapshot
```

Ambas variantes resuelven anclajes y validan **toda** la propuesta. Muestran el diff en la terminal;
`--dry-run` no escribe. La aplicación reemplaza el JSON atómicamente, archiva B e invalida sus artefactos
solo cuando hay cambios válidos. Conserva A. No se aplica a una pieza aprobada sin un pedido de cambio.

Escenas y pasos de `narrative-sequence` aceptan `anchor: {"word_id":"w12","offset":0.1}`. Las escenas
conservan su duración; los pasos se resuelven a segundos locales `at`. Una palabra ausente, tiempos
invertidos, un paso fuera de escena o una propuesta sin lectura suficiente detienen la escritura.
La composición exige que los anclajes ya estén resueltos; nunca desplaza la voz.

## Perfiles y candidatos

| Versión | Control |
|---|---|
| v1 | Entrada y salida de toda la escena; contrato anterior conservado |
| v2 | Entradas CSS internas, amplitud, easing, stagger cuando existe; cámara decorativa en Three y amplitud de glitch en Pixi; entrada/salida y presupuesto de lectura |

`formats/direction.py` declara las capacidades reales, duración orientativa, capacidad de texto,
número de elementos, recursos y costo por formato. Los adaptadores no cambian los valores de gráficas,
la geometría molecular, los relojes Lottie, ni los timestamps editoriales. No se usa `timeScale` global.
El presupuesto distingue entrada, desarrollo, lectura (referencia de 3 palabras/s y mínimo 1 s) y salida.

```sh
bin/animation-style --channel <canal> --intent compare --seconds 5 --text "Antes y después"
```

Intenciones: highlight, compare, process, transform, locate, conclude. Devuelve candidatos explicados;
puede devolver una lista vacía. Comprueba recursos reales y licencias; un booleano de disponibilidad no
sustituye esa comprobación. El agente decide con el brief y las reglas del canal.

## Objetos narrativos reutilizables

Activa `narrative` en `channel.json → format_packs`. `narrative-sequence` tiene recetas `process`,
`compare`, `locate`; entre 2 y 5 pasos. Sin `objects` conserva la forma persistente inicial.
Con `objects` admite formas circle/square, texto, iconos del catálogo e imágenes registradas:

```json
{"recipe":"process","objects":[{"id":"sample","kind":"icon","icon":"dna"}],
 "steps":[{"object":"sample","text":"Observa","at":0},
          {"object":"sample","text":"Compara","at":3,"scale":1.15,"x":80}]}
```

Transformaciones por paso: `x`, `y`, `scale`, `rotation`, con límites validados. Se conserva el objeto;
no se regeneran imágenes ni se promete morph entre modelos 3D, moléculas y Lottie.
Para una imagen: `{"id":"sample","kind":"image","image":"sample-photo"}`.

```sh
.venv/bin/python -m scripts.tools.images add --channel <canal> --id sample-photo \
  --file /ruta/foto.png --origin "Fotografía propia" --license "Propia" --ads
.venv/bin/python -m scripts.tools.images list --channel <canal>
```

PNG, JPEG o WebP hasta 25 MB. No marques `--ads` sin autorización comercial. Las imágenes del canal
quedan fuera de Git; la composición registra sus créditos en `assets.md`.

## Calidad sobre la composición real

El compositor de producción, la galería v2 y los previews comparten `scripts/composer/project.py`.
La galería acepta fragmentos con `--with-plate`, `--plate-start`, `--plate-seconds`; no exige una toma
que dure toda la concatenación. La API `gallery.build` acepta storyboard, captions, recortes y beats
explícitos para probar conjuntamente escenas, tarjetas, subtítulos, fx, beat_fx y transiciones.

```sh
bin/format-gallery --channel <canal> --formats particle-title,narrative-sequence \
  --seconds 8 --motion-profile balanced --with-plate /ruta/video.mp4 --plate-seconds 8
.venv/bin/python -m scripts.tools.animation_quality --project <pieza>
```

El control usa el compilador, servidor, navegador y seek reales de HyperFrames **0.9.32**. Una actualización
de esa dependencia exige adaptar y volver a comprobar la integración. No hay API de visión externa.
Muestrea cada 0.5 s y los cambios de escenas, grupos de subtítulos, pasos, efectos y transiciones;
conserva mediciones de todos los instantes y capturas representativas y de errores.

Bloquean B: texto fuera del lienzo o recortado durante lectura, colisiones con subtítulos/regiones
protegidas, contraste menor a 3:1 sobre fondos opacos medibles, recursos/fuentes/runtime ausentes,
informe obsoleto. Las cancelaciones normales de peticiones de medios al buscar un cuadro no se
confunden con archivos ausentes. Se comparan las huellas antes y después de medir.

Advertencias: texto pequeño en teléfono, contraste entre 3:1 y 4.5:1, zonas seguras de presets aún no
verificados en la aplicación móvil, posible oclusión, densidad y repetición. Los glifos se miden por su
área visible para no confundir el espacio vertical de la fuente con texto recortado. Durante entradas
intencionales se guardan cuadros, pero no se reporta un recorte transitorio como fallo de lectura.

Informe: `<pieza>/work/animation-quality.json`; evidencia: `<pieza>/hf/quality/`. La huella incluye HTML,
recursos, fuentes, variables, presets, lockfile y versión del comprobador; excluye evidencia y cachés.
El agente debe revisar rostro, manos, texto dibujado en canvas/WebGL, contraste sobre video y sentido
narrativo. `visual_review: pending` nunca equivale a aprobación humana. B presenta resumen, archivos
abiertos, rutas y cuatro preguntas; un final sigue requiriendo B y `verify.py` en verde.

La prueba aislada de este upgrade se cerró como validación técnica del motor, sin aprobación B
ni entrega editorial. No se registra una aprobación ficticia ni se considera el borrador un final;
consulta el [estado de validación](status/STATUS.md).

## Pruebas reproducibles e instalación

```sh
.venv/bin/python -m scripts.dev.animation_matrix
.venv/bin/python -m scripts.dev.animation_scenarios
.venv/bin/python -m scripts.dev.animation_install_check
.venv/bin/python -m unittest discover -s scripts/tests
```

La matriz carga todos los paquetes públicos: 36 formatos × 3 perfiles. Corre HyperFrames check,
capturas reales, QA y comparación de píxeles en orden inverso, con tiempos y manifiestos en
`work/animation-matrix/`. Solo reutiliza resultados correctos cuyos hashes y archivos siguen vigentes;
un cuadro ausente falla. Conserva la tolerancia GPU existente (≤ 0.01 % de píxeles con diferencia > 8).
`animation_scenarios` prueba dos marcas públicas, capas combinadas y fallos deliberados de texto/fuentes.

`animation_install_check` crea una copia pública temporal, ejecuta `npm ci`, un entorno Python nuevo,
la suite y un render de prueba. Declara el sistema operativo real y conserva evidencia. Se puede ejecutar
igual desde WSL. `.github/workflows/animation.yml` prepara instalaciones limpias macOS/Ubuntu; que exista
el workflow no significa que sus jobs remotos ya hayan pasado. Una entrega histórica en WSL no valida
esta versión nueva. Los resultados y pendientes de la sesión se registran en `docs/status/STATUS.md`.

## Ventanas de lectura y avisos

El compositor escribe `hf/reading-windows.json` como metadato interno. Tarjetas, subtítulos, efectos
y escenas se evalúan por separado: una escena en movimiento no oculta problemas de otra tarjeta.
Las máscaras de revelado conocidas y la entrada desde fuera del lienzo se permiten durante transición; el recorte persistente en
lectura sigue siendo error. Una animación sin intervalo de lectura produce `no_reading_window`.
Los avisos de zona segura durante movimiento son informativos; durante lectura siguen siendo
advertencias. El informe agrupa por elemento, texto, causa y fase, conservando primera/última
ocurrencia y cantidad. Se priorizan errores y advertencias sobre transitorios.
Regresión pública: `python -m scripts.dev.reliability_scenarios` (revelados y recorte persistente).

Los subtítulos de hasta 0.32 s aparecen sin fundido de línea: las animaciones habituales consumirían
su intervalo de lectura. Se conservan palabras, marcas de tiempo y estilo; los grupos más largos
mantienen sus entradas y salidas habituales. Esto se comparte entre compositor y medición.

En `kinetic-title`, la ventana termina al empezar la salida interna del texto y kicker, aunque
el fundido exterior de la escena empiece después. El recorte durante lectura permanece bloqueante.
