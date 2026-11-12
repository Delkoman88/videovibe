# 0010 — Tratamiento de voz medido, con filtros clásicos

**Fecha:** 2026-11-11 · **Estado:** vigente

## Contexto
La voz solo se normalizaba a −14 LUFS. Cada grabación (cuarto, micrófono, distancia) suena distinta y
la voz es lo que más pesa en un video a cámara.

## Decisión
- `scripts/audio/voice.py` mide cada master (piso de ruido, SNR, espectro de los tramos con voz frente a una
  curva típica, sibilancia, nivel) y elige una cadena de filtros de ffmpeg: highpass, afftdn, hasta 3
  bandas de EQ, deesser, acompressor y un expansor (agate) en segunda pasada. Cada paso se omite si
  la medida dice que no hace falta, y queda explicado en `cut/voice-report.json`.
- Límites conservadores («natural»: EQ ±3 dB, reducción de ruido ≤ 12 dB) y opción «fuerte».
- Sin modelos de IA de «voz de estudio» ni regeneración de voz: alteran el timbre (regla universal 3).
- Se integra en `compose.py` (no es una etapa nueva); la duración de salida debe ser idéntica a la del
  master o no se usa (sincronía de labios).

## Consecuencias
- Toda pieza sale con voz tratada sin pasos manuales; el antes/después se genera con `--compare`.
- Las curvas de referencia son aproximadas: si una voz concreta sale mal, ajustar por canal
  (`channel.json → voice`) y anotar el caso.
