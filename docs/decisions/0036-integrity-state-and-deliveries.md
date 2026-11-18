# 0036 — Estado, evidencia de aprobación y entregas independientes

Los controles de continuación deben usar la misma evidencia que el registro de aprobación.
A/B guardan versión, huella de entradas y de presentación; no basta una fecha. Las aprobaciones
históricas se conservan, pero al reanudar sin evidencia suficiente se requiere revisión. Las
consultas no escriben. Rechazo, ajustes y nuevas presentaciones invalidan la aprobación correspondiente.

El estado se normaliza al leer y se escribe con temporales únicos y reemplazo atómico. Un bloqueo
por pieza del sistema operativo protege comandos y subprocesos; otro protege transacciones breves.
La delegación a subprocesos comprueba propietario y token. No se espera indefinidamente: una operación
incompatible devuelve pieza ocupada. Las etapas registran entradas/salidas por contenido; los
artefactos derivados antiguos sin evidencia se reconstruyen al reanudar.

Entregas nuevas: copias independientes en versions/<huella>, manifiesto con hashes, recibo de
verificación y aprobaciones. Preparación temporal, promoción por rename y current.json atómico.
Una versión previa permanece intacta; una versión alterada no se reutiliza. Los renders finales se
escriben a temporal y se reemplazan después de comprobar B nuevamente. La entrega directa exige
verificación y aprobaciones vigentes. Verificar técnicamente una prueba no implica aprobación editorial.

Los enlaces duros antiguos se desacoplan solo mediante migración explícita; no se puede reconstruir
con certeza una aprobación antigua ni garantizar que sus bytes nunca cambiaron. La migración preserva
los bytes existentes, no certifica su historia. Sin nuevas dependencias de ejecución.

Los documentos editoriales (clasificación, transcripción, corte y subtítulos) pueden corregirse a mano:
una corrección no se sobrescribe como si fuese corrupción de caché. Alimenta las etapas dependientes
y las revisiones A/B. Refrescar un corte existente conserva sus decisiones; no repite heurísticas.
B exige además evidencia vigente de construcción de composición y preview. Los temporales y los
resultados audiovisuales generados se reconstruyen cuando sus huellas dejan de coincidir.


Corrección de auditoría: herencia explícita del descriptor POSIX y reservas de grupos de trabajadores;
el token solo no autoriza delegación. Recibos v3 incluyen plataformas, entradas estables y salidas.
B incluye la composición compilada. Cada render se promueve después de validar nuevamente entradas
y aprobación; sus bytes se registran por plataforma para reutilización independiente. Windows nativo
queda bloqueado para ejecución delegada hasta implementar y validar equivalencia, sin promesa de
portabilidad basada en tests macOS. Las reservas ambiguas fallan de forma conservadora.
