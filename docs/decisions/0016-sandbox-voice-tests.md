# 0016 — Pruebas de voz dependientes del entorno

**Fecha:** 2026-11-12 · **Estado:** vigente

## Contexto

En el sandbox de macOS, `say` existe y termina con código 0, pero puede generar un AIFF sin muestras. Las pruebas que solo comprobaban la presencia del ejecutable intentaban usar ese audio vacío; fallaban después en FFmpeg y en la transcripción, sin señalar la causa.

## Decisión

Las pruebas que sintetizan voz consultan `scripts/tests/support.py`. La comprobación crea un AIFF temporal con la voz necesaria y exige un archivo con duración real medida por `ffprobe`. El resultado se guarda por voz durante la ejecución de la suite. Si el entorno no puede producir audio, se omiten esas pruebas; las demás siguen ejecutándose.

La validación completa se hace fuera del sandbox en un macOS donde `say` sí genere audio. El CI y las máquinas sin esa capacidad pueden ejecutar la suite sin falsos fallos.

## Consecuencias

El recuento de pruebas omitidas depende del entorno. Una suite verde dentro del sandbox no demuestra que funcionen la transcripción y el corte con voz; para esos caminos se requiere la ejecución completa con audio real.
