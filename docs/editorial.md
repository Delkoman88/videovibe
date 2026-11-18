# Criterio editorial y copy

La edición ejecuta el brief y las reglas del canal. Usa [storytelling](storytelling.md) para una
historia nueva o un cambio narrativo solicitado. Una corrección técnica puntual mantiene su alcance.
Adaptaciones y atribuciones: [fuentes](editorial-sources.md).

## Preparar A

En una pieza nueva, después del brief completo, ejecuta:

```sh
bin/edit <canal>/<pieza> --until-stage corte-en-papel
```

Si se detiene antes por material, brief o error, resuelve esa causa; no presupongas que existe un corte.
Si ya hay corte, léelo antes de ejecutar comandos que puedan regenerarlo. En una pieza aprobada,
solo plantea cambios de contenido si fueron solicitados.

Inspecciona la transcripción y escucha uniones dudosas. Revisa intentos completos antes de elegir
una retoma; conservar automáticamente la última no garantiza que sea la mejor. Protege negaciones,
condiciones y conclusiones. Conserva respiraciones o pausas útiles para comprender; no hay una
frecuencia universal de cortes. En esta versión conserva el orden y edita solo decisiones keep/drop
con motivos en `cut/cut-list.json`, dentro del encargo autorizado.

Tras ajustar el JSON, regenera la vista sin repetir heurísticas:

```sh
.venv/bin/python -m scripts.pipeline.paper_cut --project <canal>/<pieza> --refresh-from-cut
bin/edit <canal>/<pieza>
```

El refresco valida fuentes, tiempos, orden y decisiones antes de reemplazar `PAPER-CUT.md`; no cambia
JSON, transcripciones, aprobaciones ni status. Lee las islas de voz para estimar con el mismo algoritmo
que aplica el corte. Si falta información, corrígela; no fabriques tiempos. Un corte modificado sigue
requiriendo A vigente. Presenta el resumen y las preguntas del flujo guiado antes de registrar aprobación.

## Preparar B

Consulta el plan narrativo si existe y sigue storyboard, formatos y dirección de animaciones del motor.
Para cada recurso, identifica su función: mostrar evidencia, explicar una relación, orientar o crear
una experiencia apropiada al canal. Quita lo que solo repite el subtítulo y compite con la imagen.
Revisa continuidad de voz e imagen, lectura a tamaño teléfono y correspondencia de afirmaciones con
las fuentes. Revisa especialmente entradas, salidas y uniones del borrador; el QA técnico no certifica
sentido narrativo. Usa las revisiones existentes; no añadas aprobaciones ni sustituyas A/B por tu juicio.

## Títulos y copy

Antes de escribir, consulta objetivo, audiencia, voz del canal y el video realmente editado. Conserva
el vocabulario de la persona y el resultado real: preliminar no se convierte en comprobado.
En `copy/<plataforma>.md` incluye título recomendado, texto, CTA y enlaces/fuentes según el preset.
Ofrece alternativas solo cuando ayuden a decidir; no reescribas partes correctas de un encargo puntual.

Prefiere afirmaciones concretas respaldadas. El título debe prometer algo que la pieza entrega;
no añadas cifras, testimonios, urgencia ni beneficios sin fuente. Cada bloque comunica una idea.
La CTA responde al objetivo: comprender, escuchar, practicar, conversar o comprar cuando el brief lo pida.
En ciencia conserva incertidumbre y fuentes; en música respeta la experiencia sin imponer venta;
en tutoriales describe el resultado demostrado y sus condiciones. No prometas retención por aplicar
una fórmula. Abre los archivos que deban revisarse mediante `bin/open-review` y muestra rutas.

## Aprendizajes

Conserva la corrección confirmada, su contexto y fecha en el canal. Reemplaza reglas contradictorias;
no conviertas la preferencia de una persona en estilo del motor. La revisión editorial verifica claridad,
fidelidad, continuidad y utilidad de cada recurso; las medidas de audio/video corresponden a los scripts.

## Estado de propuestas y revisiones

Las aprobaciones y su vigencia se consultan con `bin/status` y las comprobaciones del pipeline.
Los documentos narrativos describen propuestas: no duplican estados mutables como «pendiente de A».
Si cambian brief, fuentes o corte, revisar sus referencias antes de reutilizarlos. No reescribir
planes existentes automáticamente; corregir menciones obsoletas preservando decisiones y fuentes.

## Evaluación en uso real

En `work/editorial-evaluation.md` de la pieza, evaluar gancho, claridad, ritmo y fidelidad.
Para cada criterio registrar satisfactorio, ajuste necesario o pendiente, con segundos, evidencia y
corrección propuesta. Separar juicio del agente, respuestas del usuario y mediciones técnicas.
Anotar rondas y cambios pedidos, sin estimar ahorros ni retención sin una comparación medida.
Las preferencias se guardan en el canal solo tras confirmación; los fallos generales van al motor.

## Antes del primer preview: revisión editorial con evidencia

En toda propuesta visual nueva, antes de componer, el agente lee brief, canal, corte y fuentes.
Registra en `work/editorial-evaluation.md` una sección «Antes del preview» con estos cuatro criterios:

| Criterio | Comprobación |
|---|---|
| Promesa inicial | El inicio anticipa el tema que realmente se desarrolla. |
| Desarrollo | Afirmaciones y relaciones tienen respaldo en las tomas. |
| Recursos visuales | Cada recurso explica, orienta, muestra evidencia o crea una experiencia pertinente. |
| Cierre | Una resolución, acción o experiencia completa el fragmento. |

Por criterio: satisfactorio, ajuste necesario o pendiente; archivo y tramo, líneas o ID del recurso;
corrección aplicada o limitación. Ante un problema, inspeccionar alternativas en los originales,
incluidas acciones sin diálogo y sonidos. Registrar alternativa elegida y motivo. No inventar un
cierre, moraleja o CTA ni imponer el gusto de otro canal. Si falta material, explicarlo en B.
Corregir dentro del encargo antes del preview; si cambia el corte hablado, requiere A de nuevo.
Después del render, contrastar estas decisiones con el preview real y presentar resumen y preguntas
A/B habituales. Las respuestas del usuario se registran separadas del juicio del agente.
Es un procedimiento editorial obligatorio para propuestas nuevas, no un nuevo gate del motor:
no bloquea piezas anteriores ni exige reescribir planes aprobados. Completar la tabla no certifica calidad.

Casos de referencia para evaluar el procedimiento (ficticios):
- Inicio «Mi nueva cámara», tomas sobre aprender fotografía: pedir contexto que anuncie el aprendizaje.
- Tres iconos decorativos sin relación con una reparación: retirar o sustituir por evidencia del paso.
- Despedida truncada, toma posterior con resultado y sonido propio: proponer esa toma como cierre.
- Despedida truncada sin más material: señalar la limitación; no inventar resultados o testimonios.
