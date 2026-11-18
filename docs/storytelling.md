# Storytelling

Criterios del motor para guiones y organización de material. Entradas: brief, `CHANNEL.md`,
`style.md`, `rhythm.md` y `learnings.md`. Aplica el alcance de la petición: un cambio de título no
autoriza rehacer el video. [Procedencia y licencias](editorial-sources.md).

## Antes de grabar

Completa objetivo, audiencia, material previsto y CTA con la persona. «No aplica» puede ser una
CTA válida si el objetivo es explicar o crear una experiencia. Marca como previstas las tomas
que aún no existen. Crea la pieza con `bin/new-piece <canal> <slug>` sin `--from` si hace falta;
no intentes atravesar la pausa de material de `bin/edit`.

Define una idea central y qué debería comprender o sentir esa audiencia al terminar. Elige un
recorrido que la sostenga: ejemplo explicado, pregunta y respuesta, proceso, contraste o experiencia
musical. No fuerces conflicto, venta ni una fórmula narrativa cuando basta una demostración.
Separa hechos sustentados de decisiones creativas; lo que falta se pregunta o se marca pendiente.

Escribe `story-plan.md` con objetivo, audiencia, mensaje central, gancho, bloques, cierre y material
faltante. Recomienda una estructura; ofrece hasta dos alternativas solo si cambian realmente la
historia. Escribe `script.md` con palabras propuestas y notas de grabación, diferenciando claramente
locución, imagen sugerida y hechos pendientes de confirmar. Estos documentos no ejecutan el render.

## Con material grabado

Revisa media.json, transcripciones y el corte en papel antes de elegir un gancho. Para cada bloque de
`story-plan.md`, registra fuente, ids de líneas, tiempos de origen, idea y decisión propuesta con motivo.
Los tiempos de origen no son tiempos del master. Cita el texto real sin reescribir la transcripción
para hacerla coincidir con la historia deseada. Si una transcripción es dudosa, escucha el original.

Conserva negaciones, condiciones, incertidumbre y contexto. Una toma completa con una vacilación puede
ser mejor que una frase pulida que cambia el significado. Una imagen ilustrativa no demuestra una
conclusión. Distingue material disponible, recursos que faltan y frases que habría que grabar de nuevo.

Esta versión admite selección keep/drop y conserva el orden de fuentes y líneas. Si el gancho ideal
requiere mover frases, anótalo como propuesta no aplicada: no reordenes arrays, cambies timestamps ni
recortes palabras para simular soporte. La edición ejecutable sigue [criterio editorial](editorial.md).

## Presentación y mantenimiento

Resume la propuesta en terminal: mensaje, recorrido recomendado, cambios y faltantes. No impongas
una nueva pausa obligatoria. Si hace falta que la persona revise un documento, ábrelo con
`bin/open-review`, comprueba el resultado y muestra la ruta absoluta. La entrega de video conserva A/B.

Los documentos auxiliares son opcionales para piezas existentes. Si cambian fuentes, corte o brief,
revisa sus referencias antes de reutilizarlos. No reescribas un plan aprobado por una corrección puntual.
Registra preferencias solo cuando estén confirmadas, en el canal correspondiente.

## Estado de propuestas y revisiones

Las aprobaciones y su vigencia se consultan con `bin/status` y las comprobaciones del pipeline.
Los documentos narrativos describen propuestas: no duplican estados mutables como «pendiente de A».
Si cambian brief, fuentes o corte, revisar sus referencias antes de reutilizarlos. No reescribir
planes existentes automáticamente; corregir menciones obsoletas preservando decisiones y fuentes.
