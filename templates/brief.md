# Brief de pieza

> `bin/new-piece` copia esta plantilla a la pieza. El agente la completa **preguntándole a la persona del
> canal** lo que no pueda deducir del material, escribiendo la respuesta en la misma línea, después de
> los dos puntos. Las 4 marcadas con ★ son obligatorias: `bin/edit` no avanza sin ellas.

- **Título de trabajo:**
- ★ **Objetivo:**
  _¿Qué debe lograr esta pieza?_
- ★ **Audiencia principal:**
  _Una, de `CHANNEL.md` del canal._
- ★ **Material disponible:**
  _Archivos en `raw/` y qué es cada uno: cámara, pantalla, B-roll, voz en off, audio de micrófono externo.
  ¿Hay música o efectos propios? De dónde vienen y con qué licencia (`docs/audio.md`)._
- ★ **Llamada a la acción:**
- **Pregunta eje:**
  _De las preguntas del principio editorial (`CHANNEL.md`)._
- **Temas:**
  _Ids de `topics.md` del canal._
- **Plataformas:** [ ] TikTok  [ ] Reels  [ ] X  [ ] YouTube
- **¿Publicidad pagada?:** no / sí / quizá
  _no → música de la biblioteca (Epidemic Sound u otra). sí → solo música con licencia para anuncios
  (`scripts/audio/music.py list --channel … --ads`). quizá → música normal y, si luego se promociona, se
  agrega la plataforma `ads` (anuncio). Va en `storyboard.json → audio.music.ads`._
- **Duración objetivo:**
- **Estado del resultado mostrado:** preliminar / validado / fallido / no aplica
- **Fuentes o enlaces:**
  _Papers, repositorio, datos._
- **Lo que NO debe salir:**
  _Tomas, datos, nombres._
- **Notas de la persona del canal:**
