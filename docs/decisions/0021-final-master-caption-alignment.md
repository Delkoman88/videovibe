# 0021 — Alineación de subtítulos contra el master final

**Fecha:** 2026-11-16 · **Estado:** vigente

## Contexto

Una pieza puede conservar un `transcript/master-cut.json` generado antes del último cambio de corte.
El video y su audio quedan correctos, pero los subtítulos pueden incluir palabras eliminadas y desplazar
todo lo posterior. Volver a transcribir por islas no siempre sirve: en islas muy cortas el contexto de
marca puede convertirse en una alucinación y la carga repetida del modelo es lenta.

## Decisión

`captions.py --from-whisper-json <archivo>` admite el JSON producido por `whisper-cli -ojf -sow -ml 1`
sobre `cut/master-cut.mp4`. Esos timestamps globales son la fuente de sincronía. El importador corrige
solo tokens simultáneos o de duración cero, repartiendo su intervalo sin mover el anclaje global.

Después de importar, los nombres propios y la puntuación se corrigen en `transcript/master-cut.json` y
se regeneran los grupos con `--from-transcript`. No se cambia el audio, la voz ni el corte aprobado.

## Consecuencias

- Una frase eliminada del corte no puede seguir apareciendo en subtítulos.
- Se evita desplazar palabras entre islas de voz por intentar forzar una alineación global a la energía.
- Whisper puede equivocarse en ortografía o puntuación; la revisión editorial sigue siendo obligatoria.
- Los ids de palabra pueden cambiar, por lo que el storyboard debe volver a revisar `emphasis`.

## Validación

La pieza de un canal de DJ (Windows/WSL) eliminó una frase fantasma entre «Exacto» y «Ahora voy a poner…». Los anclajes quedaron
en 24.42–24.88 s y 24.88–25.27 s respectivamente; el storyboard y HyperFrames pasaron sus validaciones.
La importación y la regularización de tokens simultáneos están cubiertas por pruebas unitarias.
