# 0003 — HDR (HLG/PQ) → SDR BT.709 con curva hable

**Contexto.** Los teléfonos graban HDR HLG. Recomprimir a 8 bits conservando la etiqueta HDR deja colores lavados en redes y hace que HyperFrames renderice en HDR.
**Decisión.** `ingest.py` detecta HDR; `apply-cut.py` convierte con zscale + tonemap hable a BT.709 y etiqueta la salida. Requiere `ffmpeg-full` (keg-only). La corrección de color posterior (media-treatment) levanta la exposición.
**Descartado.** Mobius (piel rojiza); sin conversión (gris y plano).
**Consecuencias.** `bin/doctor` exige `ffmpeg-full`. `verify.py` rechaza renders que no sean BT.709.
