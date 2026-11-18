# 0031 — Criterio editorial compartido y skills de entrada

Fecha: 2026-11-17. Estado: vigente.

## Decisión

Storytelling cubre preproducción y organización fiel de grabaciones; edit-video conserva la ejecución.
Los criterios viven en docs, accesibles desde AGENTS incluso sin carga automática de skills. Los planes
Markdown son auxiliares opcionales; el corte y storyboard siguen como fuentes ejecutables.

Se adaptan fragmentos de fuentes con revisión fijada y licencia conservada (docs/editorial-sources.md).
No se instalan pipelines externos ni se actualizan reglas automáticamente. El copy forma parte de edición.
No hay nuevos gates ni migración de piezas aprobadas. Seleccionar material no incluye reordenarlo: el
algoritmo actual de unión de segmentos presupone orden; ampliar ese contrato exige otro trabajo.

## Consecuencias

paper_cut --refresh-from-cut produce la vista del JSON editado sin repetir heurísticas, con validación
previa y reemplazo atómico. El agente prepara el corte antes de reanudar la revisión A. El análisis
editorial no certifica retención ni reemplaza las aprobaciones humanas o verify.py.

## Alternativas

Se descartan instalar skills enteras con sus propios gates y servicios, duplicar criterios en cada agente
y hacer obligatorio un nuevo archivo narrativo para todas las piezas existentes.
