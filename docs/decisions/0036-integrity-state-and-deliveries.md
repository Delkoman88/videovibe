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

## Revisión — v0.13.2-alpha (esquema de huellas 3)

La revisión de v0.13.1 encontró que las huellas invalidaban de más y que los subtítulos podían
quedar ligados a un corte anterior. Se corrige sin relajar la evidencia:

- **Subtítulos y corte.** `transcript/master-cut.json` guarda la huella del corte que lo produjo.
  `bin/edit` solo usa `--from-transcript` si coincide; si no, guarda la versión anterior
  (`transcript/master-cut.<huella>.json`) y transcribe el master nuevo. `captions.py --from-transcript`
  rechaza una transcripción de otro corte.
- **Huellas relativas.** Cada archivo entra con una etiqueta `piece:`, `channel:`, `engine:` o `ext:`;
  nunca con su ruta absoluta. Mover la carpeta de canales o cambiar de máquina no invalida nada.
- **Alcance.** Las etapas editables (ingesta, transcripción, corte en papel, subtítulos) dependen del
  contenido de la pieza y de lo que el canal les aporta (vocabulario, idioma, marca para subtítulos), no
  del código del motor ni de `channel.json` completo: activar un paquete o actualizar npm ya no
  vuelve a transcribir. Las etapas derivadas conservan el código del motor (rehacerlas es barato y
  determinista). **B** depende del contenido de la pieza y del HTML compilado, no del código del motor:
  si el motor cambia lo que se ve, cambia el HTML y B se invalida igual.
- **Transcripción protegida.** Antes de `transcribe --force`, `bin/edit` copia `transcript/*.json` a
  `work/transcript-backup/<fecha>/` y lo avisa.
- **Presentar o aprobar A** no borra B: B guarda su
  propia evidencia (corte, subtítulos y HTML compilado) y deja de valer sola si el corte cambió.
- **Migración (`integrity.restamp`).** La evidencia guardada se recalcula con el algoritmo con que se
  escribió (esquema 1: sha1 por tamaño; esquema 2: rutas absolutas, con los bytes originales de
  `integrity.py` de v0.13.1 en `scripts/core/legacy/`). Si coincide, se reemplaza por la del esquema 3;
  si no, se deja y la etapa o aprobación queda pendiente como antes. Las piezas sin recibos reciben
  recibo solo en las etapas que la lógica anterior consideraba al día, salvo la composición, que se
  reconstruye. `bin/edit` y `bin/status --approve` migran bajo bloqueo; `--plan` calcula en memoria.
- **Constancia de aprobaciones anteriores.** `bin/status <pieza> --attest-legacy A|B --note "…"`
  convierte una aprobación anterior a v0.13.1 solo si la revisión guardada fue aprobada y coincide con
  la presentación actual (y, para B, con recibos vigentes de composición y preview). El agente la corre
  solo después de que la persona lo confirme. Sin revisión guardada, hay que presentarla de nuevo.
