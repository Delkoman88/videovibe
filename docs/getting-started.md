# Primeros pasos (guía para el agente)

Úsala cuando `bin/welcome` diga una etapa distinta de `listo`. El objetivo es que la persona tenga su
primer video editado en una sesión, no que llene un cuestionario.

**Cómo hablar:**
- En el idioma de la persona.
- Frases cortas, un bloque de preguntas a la vez.
- Sin jerga del motor (nada de «storyboard», «preset» o «pipeline» si no hace falta).
- Si la persona pidió algo concreto al llegar, dile que primero dejan listo su canal (2–3 minutos) y
  retómalo al terminar.

## 1. Bienvenida (etapa `instalar` o primera vez)

Explícalo en 3–4 frases, con tus palabras:

> VideoVibe edita videos verticales (TikTok, Reels, X) a partir de lo que grabas. Tú me das el material;
> yo lo corto, le pongo subtítulos, animaciones, música y efectos, y te pido aprobación dos veces: el
> corte y el plan visual. Al final te entrego una versión por plataforma, revisada técnicamente.
> Todo corre en tu computadora y cada canal tiene su propio estilo, que aprende de tus notas.

- Si `bin/welcome` dice `instalar`: di en una frase qué falta y ofrece `bin/setup`. Pide
  confirmación antes de instalar paquetes del sistema (puede pedir contraseña de administrador).
- Si nunca se corrió la demo (`"demo": false`), ofrécela: «¿Quieres ver un ejemplo en un minuto antes
  de empezar?» → `bin/demo --quick`, y muéstrale el borrador (`renders/draft-tiktok.mp4`). Si dice
  que no, sigue.

## 2. Preguntas básicas (etapa `crear-canal`)

Hazlas **juntas, en un solo mensaje**, numeradas, con un ejemplo en cada una:

1. ¿Cómo se llama tu canal y de qué trata? (p. ej. «Cocina Fácil: recetas rápidas y baratas para estudiantes»)
2. ¿Quién aparece o narra, y con qué rol? (p. ej. «yo, Ana, cocinera»; o «nadie sale a cámara, solo voz»)
3. ¿En qué idioma son los videos? (hoy: español o inglés)
4. ¿Dónde vas a publicar? (TikTok, Reels, X…)
5. ¿Quieres guardar tus canales en una carpeta privada aparte del sistema (por ejemplo para respaldarlos
   en un repo privado), o dentro de la carpeta de VideoVibe? (si no sabe: dentro, se puede cambiar después)
6. Música: ¿tienes suscripción a una biblioteca con licencia (Epidemic Sound) o usamos la música que
   genera el sistema (gratis, sirve también para anuncios)?

Si alguna respuesta no llega, usa el valor por defecto y dilo.

## 3. Crear el canal

1. Respuesta 5, si quiere carpeta aparte: `bin/welcome --channels-dir ~/mis-canales` (o la ruta que
   diga). Guarda la carpeta en `local.json` y la crea.
2. `bin/new-channel <id> --name "<nombre>" --lang <es|en> --about "<de qué trata>" --person "<Nombre>:<rol>"
   [--person …] --platforms <tiktok,reels,…> --music <propia|epidemic> [--no-camera]`.
   - `<id>`: el nombre en minúsculas con guiones (p. ej. `cocina-facil`).
   - Crea el canal completo con valores por defecto (estilo, ritmo, paleta neutra y kit de efectos) y
     lo valida; `problems` debe salir vacío.
3. Si eligió Epidemic: explica que hace falta conectar su clave (`docs/connectors.md`) y que, mientras
   tanto, el sistema usa su música propia.
4. Dile qué quedó por defecto, en una frase: «Dejé colores, letra, ritmo y sonidos con valores por
   defecto; los ajustamos con tus notas después del primer video».

Opcional, solo si la persona quiere personalizar ya:
- **Paleta:** propón 2 opciones de colores (fondo, acento, dato, remate) y cambia `brand.json → colors`.
- Más a fondo: `templates/channel-brief.md`.

## 4. Completar un canal (etapa `completar-canal`)

`bin/welcome` lista los problemas. Un canal creado sin `--about` tiene marcadores `TODO`: hazle las
preguntas básicas de la sección 2 y reescribe esos archivos, o vuelve a crearlo con `--about`. Termina
con `bin/doctor --channel <id>` en verde.

## 5. Primera pieza (etapa `primera-pieza`)

> «Tu canal está listo. ¿Dónde está tu primer video? Dime la carpeta y el nombre del archivo (por ejemplo
> «Descargas, toma1.mp4»), o ponlo en la carpeta `input/` de VideoVibe y dime cómo se llama.»

- Muéstrale la ruta absoluta de `input/` (`bin/welcome` → `input_dir`; ahí también lista los archivos
  que ya hay). Si la persona no sabe la ruta exacta, que lo arrastre a esa carpeta.
- `bin/new-piece <canal> <slug> --from <archivos>`: acepta rutas, carpetas enteras o solo el nombre si está
  en `input/`. Si no lo encuentra, el error lista lo que sí hay en `input/`: pregunta de nuevo.
- Al terminar, los videos finales quedan en `deliveries/<Nombre del canal>/<fecha> <pieza>/` (con portada,
  texto para publicar y `README.md`); `bin/edit` abre esa carpeta. Dile siempre la ruta absoluta.
- Completa el brief con la persona: objetivo, audiencia, material y llamada a la acción. Lo que puedas
  deducir del canal, propónlo en vez de preguntarlo.
- Corre `bin/edit <canal>/<pieza>` y sigue sus pausas (`docs/pipeline.md`). En la primera pieza, explica
  cada pausa en una frase. El comando abre los archivos, muestra sus rutas y propone cuatro preguntas
  concretas. Hazlas y acepta una aprobación global explícita o aplica los ajustes que pida la persona.
- Al final de la primera pieza, pregunta qué cambiaría: cada nota es una regla del canal
  (`AGENTS.md` → «Guarda esto en el sistema»). Así se ajustan los valores por defecto.
