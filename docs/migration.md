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
