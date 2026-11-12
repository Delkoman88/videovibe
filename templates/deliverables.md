# Checklist de entregables

Por cada plataforma marcada en el brief:

- [ ] `renders/<plataforma>.mp4` — pasa `scripts/pipeline/verify.py`
- [ ] `captions/<plataforma>.srt`
- [ ] Título en pantalla (gancho) dentro de la zona segura
- [ ] `copy/<plataforma>.md` — copy, hashtags según preset, CTA, enlaces/fuentes
- [ ] `covers/<plataforma>.jpg` — `scripts/pipeline/cover.py --project <pieza> --platform <p> [--at <s>]` (un cuadro con el gancho); que funcione también recortada (Reels 4:5)

Una vez por pieza:

- [ ] `clips.json` — clips secundarios propuestos: `{in, out, motivo, plataforma}` (solo la propuesta: la
      versión corta y los clips renderizados aún no existen, ver `docs/status/STATUS.md`)
- [ ] `faltantes.md` — recursos visuales que harían falta (qué, para qué segundo, cómo conseguirlo)
- [ ] `assets.md` — fuente y licencia de todo lo usado
- [ ] Guardarraíles de contenido del canal (`CHANNEL.md`) revisados en títulos, subtítulos y copy
- [ ] `scripts/pipeline/verify.py` en verde y `bin/status` con aprobaciones A y B
