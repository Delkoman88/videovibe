# Migrar a la estructura de paquetes

Este cambio rompe rutas antiguas deliberadamente. No hay alias.

- `bin/welcome` reemplaza `bin/bienvenida`; opciones `--skip-doctor` y `--channels-dir`.
- `bin/format-catalog` reemplaza `bin/catalogo-formatos`.
- `bin/demo --quick` reemplaza `--rapido`.
- `bin/edit --from-stage` y `--until-stage` reemplazan `--desde` y `--hasta`.
- Las herramientas se ejecutan desde la raíz con `.venv/bin/python -m scripts.pipeline.<módulo>`
  o `scripts.audio.<módulo>`. Por ejemplo: `scripts.pipeline.paper_cut`, `scripts.pipeline.verify`.
- Las bibliotecas están en `scripts.core`; el compositor en `scripts.composer` y la validación
  en `scripts.validation`. No importar módulos mediante la antigua carpeta plana.

## Datos existentes

1. `bin/migrate-layout --json`: inspeccionar operaciones y conflictos sin cambiar datos.
2. `bin/migrate-layout --apply`: guardar respaldo y aplicar; conservar la ruta del manifiesto.
3. `bin/welcome --skip-doctor` y `bin/doctor --channel <canal>`: comprobar el canal.
4. Si la revisión B quedó pendiente, presentarla de nuevo y solicitar aprobación explícita.

Para probar una copia: `bin/migrate-layout --channels-dir /ruta/copia --apply`.
Para recuperar una interrupción: `bin/migrate-layout --resume /ruta/manifest.json`.
Para revertir: `bin/migrate-layout --rollback /ruta/manifest.json` y restaurar la versión anterior
del código. No editar los archivos afectados mientras se aplica o revierte la migración.

Los nombres editoriales del canal ahora son `style.md`, `rhythm.md`, `topics.md`, `learnings.md`
y `vocabulary.txt`. `ads` reemplaza la plataforma `anuncio`. Las carpetas predeterminadas son
`input/` y `deliveries/`. Las rutas personalizadas mantienen su nombre. Conserva las variables
`VIDEOVIBE_MATERIAL`, `VIDEOVIBE_DELIVERIES` y sus claves `material_dir`, `deliveries_dir`.
Si `local.json` apunta explícitamente a una carpeta predeterminada antigua, la migración
actualiza esa ruta. Las variables de entorno se mantienen bajo control de quien las configura. Los títulos y originales personales se conservan.

Configuración de la carpeta de originales: `local.json → input_dir` o `$VIDEOVIBE_INPUT`. Los nombres
anteriores (`material_dir`, `$VIDEOVIBE_MATERIAL`) siguen valiendo.

## Integridad de etapas y entregas (ADR 0036)
A/B se vinculan a contenido y presentación; cambios relevantes requieren revisión. Aprobaciones
antiguas sin evidencia se conservan como historia, pero requieren revisión al reanudar, salvo que
su revisión guardada coincida con la presentación actual: entonces, con confirmación de la persona,
`bin/status <pieza> --attest-legacy A|B --note "…"` deja constancia sin repetir la revisión. Consultar
estado no migra archivos. Las huellas usan rutas relativas (mover la carpeta de canales no invalida
nada) y la evidencia de versiones anteriores se migra sola al reanudar (`integrity.restamp`). Las etapas guardan huellas de entradas/salidas; copia y portada no invalidan B.
Entregas nuevas: `deliveries/<Canal>/<pieza>/versions/<huella>/`, copias independientes con manifiesto;
`current.json` indica la versión actual y bin/edit abre su ruta. No se sobrescriben versiones previas.

Para desacoplar enlaces duros antiguos sin cambiar sus bytes ni rutas:
`python -m scripts.tools.migrate_deliveries --directory <carpeta>` simula; añadir `--apply` ejecuta.
Repetir el comando reanuda el diario `.detach-journal.json`. Rechaza enlaces simbólicos inesperados
y conflictos. Desacoplar no certifica la aprobación histórica. No hay migración automática.

## Evidencia de versiones anteriores (antes de v0.15)

v0.13.2 cambió el esquema de huellas (rutas relativas; el motor fuera de las etapas editables y de B).
`bin/edit` migra cada pieza al reanudarla; para migrar todas de una vez:

```bash
bin/status --migrate          # simula: qué cambiaría en cada pieza (no escribe)
bin/status --migrate --apply  # guarda
```

Las piezas con aprobaciones anteriores a v0.13.1 aparecen con `legacy_approvals`: si su revisión
guardada coincide con la presentación actual, `bin/status <pieza> --attest-legacy A|B --note "…"` deja
constancia (solo después de que la persona lo confirme); si no, `bin/edit` presenta la revisión de nuevo.
**v0.15 retira el código de migración**: después de esa versión, la evidencia sin migrar requiere revisar
y reconstruir.

