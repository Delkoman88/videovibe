# 0030 — Perfiles versionados, composición compartida y revisión visual

Fecha: 2026-11-17. Estado: vigente (instalación limpia y matriz en CI Ubuntu; la aceptación editorial se registra por pieza).

La propuesta fija `motion` y su versión. La marca es una preferencia para propuestas nuevas; no altera
piezas ya aprobadas. Se conservan byte a byte los formatos sin motion y con v1. V2 adapta las entradas
internas en la API de la línea de tiempo y las cámaras decorativas en el código de cada familia;
no sustituye números del JS generado ni acelera toda la composición. El audio y los datos científicos
conservan sus tiempos y valores. Cada formato publica las capacidades que realmente implementa.

Los anclajes de escenas y pasos comparten resolución y validación. La escritura requiere propuesta
válida, muestra diff y reemplaza el storyboard atómicamente; solo después invalida B, conservando A.
La selección de perfil se vincula a los previews presentados y a su marca mediante hashes.

Producción y previews comparten `scripts/composer/project.py`. La medición usa las funciones reales
de compilación, servidor y búsqueda de HyperFrames; el adaptador está ligado a 0.9.32 y falla ante otra
versión. Esta dependencia interna explícita evita mantener un reproductor paralelo que mida algo
distinto del render. Actualizar HyperFrames exige validar el adaptador y la matriz nuevamente.

Se mide texto visible y colisiones sobre la composición completa, en ventanas de lectura y cambios
relevantes. El informe diferencia errores, advertencias y juicio editorial. No promete medir texto
rasterizado en canvas/3D, reconocer caras ni determinar si una explicación es correcta. Los presets
móviles no verificados generan advertencias de zona segura. La falta de runtime, fuentes o recursos
falla; el aborto normal de una petición de medios durante un seek no equivale a recurso ausente.

La huella del informe cubre entradas de render y comprobador, excluyendo cachés y capturas. Se valida
antes/después de medir y al presentar/aprobar B. Ningún resultado automático concede aprobación.

Las pruebas en orden inverso revelaron estado implícito en MotionPath/DrawSVG/MorphSVG. En v2 las
trayectorias se calculan desde un reloj absoluto después de actualizar toda la línea de tiempo, y los
morphs parten de una forma explícita. V1 conserva su contrato. No se relajó la tolerancia GPU.

Las recetas narrativas conservan objetos identificados (texto, formas, iconos y fotos con licencia).
No son un morph universal entre recursos. Recursos privados y pruebas reales quedan en `work/` o en
el canal externo, nunca en fixtures públicos. Solo se utiliza el canal científico privado para la prueba nueva; la
validación histórica del canal musical privado/WSL se conserva como evidencia de aquella entrega, no de esta función.

Ver comandos y límites en [Dirección de animaciones](../animation-direction.md). La aprobación B,
el render final verificado y la ejecución de esta versión en WSL son verificaciones independientes;
no se presentan como realizadas por haber implementado los comandos o la configuración CI.

Aclaración de alcance de esta prueba: la persona confirmó que el ensayo aislado sirve para validar
el motor y no requiere aprobación B. Se cierra con la evidencia técnica ya obtenida, sin registrar
aprobación humana ni certificar una entrega final. Las revisiones de piezas destinadas a entrega
conservan su flujo normal. La validación nueva en WSL/CI remoto sigue pendiente.
