# 0026 — Efectos al ritmo: rejilla de la biblioteca, fase por ataques y envoltura de cámara

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Sincronizar cortes, destellos y pulsos con la música hace que un video se sienta profesional, y para un
canal de DJ es obligatorio. Hace falta saber dónde caen los golpes en el tiempo del video y animar sin
pelear con los movimientos de cámara existentes.

## Decisión

1. **Detector de HyperFrames** (`hyperframes beats <archivo> --json`) como base. En la prueba falló con una
   pista de Epidemic de 140 BPM (devolvió 94: se engancha a un pulso de tresillo).
2. **Si la biblioteca trae el BPM**, la rejilla es exacta a ese BPM y su fase se elige por la suma de ataques
   (flujo espectral cada 10 ms, ventana de 1024 muestras a 16 kHz; el tiempo de cada cuadro es el centro de su
   ventana: corregirlo quitó un desfase sistemático de 32 ms). Error medido contra el detector en pistas
   propias: 15 ms de media, 26 ms máximo.
3. **Compases:** de cada grupo de cuatro golpes, el que más graves tiene (< 160 Hz) es el primer tiempo.
4. **Tiempo del video:** se resta `audio.music.start`; la música no se repite. Con `--source plate` se analiza
   el audio de la toma (música en la cámara).
5. **Envoltura `#beatwrap`** alrededor de `#cam` para `pulse` y `shake`, y capa `#beatflash` (modo `screen`)
   debajo de tarjetas y subtítulos para `flash` y `strobe`. Cada golpe es un tween corto con
   `immediateRender: false` y una base fijada en 0: cualquier cuadro se calcula igual (probado con capturas en
   distinto orden). Sin `beat_fx`, nada cambia en el HTML.
6. **Ayuda de sincronía** opcional por canal (`beat_snap`): avisos a más de 80 ms de un golpe.

## Consecuencias

- Las pistas sin BPM en la biblioteca dependen del detector; vale la pena registrar el BPM al agregarlas.
- `strobe` y `shake` fuertes son para tramos sin voz; la validación lo recuerda.
