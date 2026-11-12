# 0008 — Sonido: música con licencia por canal y efectos sintetizados propios

**Contexto.** Los perfiles de canal piden música baja bajo la voz y efectos sutiles. Hay que evitar reclamos de derechos y que la música tape la voz.
**Decisión.**
- **Música:** biblioteca por canal (`channels/<id>/audio/music/library.json`) con licencia, ánimo, duración y volumen medido (LUFS). Fuente elegida en el primer canal real: Epidemic Sound vía su MCP oficial. `compose.py` calcula la ganancia desde los LUFS medidos y genera una envolvente de *ducking* con los tiempos de las palabras (HyperFrames `data-automation`), a niveles fijados en el storyboard (`level_db`, `duck_db`).
- **Efectos:** sintetizados por código (`scripts/audio/sfx.py`), deterministas y 100 % propios; el carácter sale de `brand.json → sound`.
**Descartado.** MusicGen (licencia no comercial); catálogo de HeyGen (licencia para redes sin verificar); efectos de bibliotecas CC (licencias mezcladas).
**Consecuencias.** Los audios con licencia no van a git. Una pieza no se puede componer con una pista que no cubra su duración. El volumen final lo vigila `verify.py`.
