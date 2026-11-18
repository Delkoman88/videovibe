# 0025 — Efectos sobre la toma: recorte local de la persona y capas dentro de la cámara

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Los formatos animan encima o entre tomas. Los efectos más llamativos de las redes interactúan con la toma:
texto detrás de la persona, fondo cambiado, halo, cuadro congelado con recorte. Necesitan separar a la
persona del fondo sin alterar su identidad (regla 3), sin red y con render determinista.

## Decisión

1. **Recorte con lo que ya trae HyperFrames:** `hyperframes remove-background` (modelo local
   `u2net_human_seg`, CoreML en Mac; ≈ 210 ms por cuadro, ≈ 6 s por segundo de video). No se escribe ni se
   entrena un modelo propio.
2. **Solo los tramos que se usan** (`scripts/pipeline/cutout.py`): cada efecto recorta su tramo de
   `cut/master-cut.mp4` con 0.2 s de margen; `freeze-cutout` usa un solo cuadro (PNG). Caché en
   `<pieza>/work/cutout/` por huella del corte + tramo + modelo + versión del estabilizador (`MATTE`).
3. **Capas dentro de `#cam`:** placa → capa «detrás» → `<video>` del recorte con `data-media-start` → resto
   igual. La cámara escala placa y recorte juntos. Sin `fx`, el `index.html` es el mismo de antes.
4. **Colocación automática:** el recorte mide `subject_top`; `text-behind` con `y: auto` se coloca para que la
   cabeza tape la parte baja del texto. `depth` (`behind`, `front`, `through`) elige si el texto va detrás,
   delante o atraviesa a la persona.
5. **Estabilizador temporal del recorte** (`scripts/pipeline/matte.py`, versión `estable-v7`). El modelo no
   tiene memoria entre cuadros: a ratos toma partes del fondo como persona o pierde partes del cuerpo. Con
   cámara fija:
   - se reconstruye el fondo por mediana de los cuadros sin persona en cada punto;
   - se quita solo lo que es igual al fondo **y** pasajero (visto en < 50 % de ±1 s);
   - se rellena lo que el modelo pierde (persona en ≥ 50 % del tramo, mismo color que cuando fue cuerpo seguro,
     pedazos ≥ 5×5), conservando un pedazo solo si su contorno da sobre todo a cuerpo (≤ 65 % al fondo);
   - cierre en el tiempo de ±4 cuadros para manos y mangas borrosas, salvo donde el fondo está confirmado;
   - opacidad más sólida (0.08 → 0, 0.7 → 1). El borde suave sigue siendo el del modelo.
   Con cámara en movimiento (fondo inestable) no se aplica.
6. **Identidad y voz:** el recorte solo cambia de capa. `freeze-cutout` se rechaza si congela mientras se
   habla (los labios quedarían quietos con la voz sonando).
7. **Determinismo del texto:** sin `will-change: transform` en `formats/text.py`; con él, el borde subpíxel
   de las letras dependía del orden de los cuadros.

## Alternativas descartadas

- Rellenar todo hueco cerrado del recorte: dejaba aros alrededor de los huecos reales entre brazo y cuerpo.
- Tomar la forma del relleno de un cuadro anterior: el borde del modelo en objetos del fondo es inestable.
- Un modelo de segmentación de video propio o en la nube (red, licencias, identidad).

## Consecuencias

- La primera composición de una pieza con `fx` tarda más (≈ 6 s por segundo de efecto); se avisa con más de 6 s.
- `hyperframes check` informa (`text_occluded`) cuánto tapa la persona al texto: es lo esperado.
- El modelo incluye de forma estable objetos pegados a la persona (una silla detrás de los hombros): no
  parpadean, así que el estabilizador no los toca. Se evita al grabar (`docs/effects.md`); un modelo de video
  mejor queda en el backlog.
- Si el borde no convence en alguna toma, se cambia el tramo o se omite el efecto (`cutout_review`, ADR 0032);
  nunca se retoca a la persona.
- Ritmo (`beat_fx`), 3D y transiciones se decidieron en sus propios ADR (0026–0028).
