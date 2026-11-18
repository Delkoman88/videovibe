# 0032 — Lectura por elemento y sustituciones conservadoras

El QA global por escena confundía revelados de tarjetas con texto truncado y podía ocultar fallos
de otros elementos. El compositor ahora emite ventanas internas por elemento; las máscaras
conocidas solo están exentas durante transición. La comprobación persistente permanece activa.
Las ventanas y los informes forman parte de las huellas de QA. No se migra el storyboard ni cambia
el HTML legado por añadir estas ventanas. El borde del lienzo durante una entrada se trata como
movimiento; los contenedores interiores arbitrarios permanecen estrictos. Como corrección separada,
los subtítulos de hasta 0.32 s omiten fundidos de línea para conservar un intervalo de lectura, sin
modificar texto ni tiempos.

La segmentación no determina si su resultado representa correctamente a una persona. El agente
inspecciona evidencia vinculada a fuente, máscara y composición. Dictámenes inciertos/defectuosos
producen alternativas deterministas, sin modificar voz ni tiempos; los conflictos omiten el efecto.
Se archiva el plan previo y se conserva A, invalidando B cuando cambia el plan. No hay nuevo gate,
modelo ni permiso de publicación. Los originales personales siguen fuera del repositorio público.
