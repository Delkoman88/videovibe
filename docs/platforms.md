# Adaptación por plataforma

Los datos técnicos están en `presets/*.json`. Este archivo define el **enfoque editorial**.
Principio: **un solo master editado**, del que se derivan variantes cambiando duración, gancho,
cierre, densidad y copy. No se edita tres veces desde cero.

| | TikTok | Instagram Reels | X |
|---|---|---|---|
| Intención | Retener y provocar comentario | Verse pulido y compartirse | Informar con precisión técnica |
| Gancho | El más fuerte, ≤ 1.5 s, pregunta o resultado inesperado | Visual primero, emoción, ≤ 2 s | La afirmación técnica directa ("Hice X con Y; esto salió") |
| Ritmo | Rápido, pausas mínimas | Medio, más respiro, mejor acabado visual | Medio, prioriza que se lea el código/gráfica |
| Subtítulos | Grandes, palabra activa resaltada | Grandes, más limpios, menos resaltado | Legibles; puede ir más texto técnico |
| Cierre | Invitar a comentar o seguir el proyecto | Invitar a guardar o compartir | Enlace a código/datos o pregunta técnica |
| Copy | Breve, pregunta al final | Emocional, cuenta la historia en 3–5 líneas | Post (o hilo) que explica el avance, hallazgo o pregunta |

## Anuncio (pauta pagada)

`presets/ads.json`: la versión para promocionar (TikTok Promote, anuncios de Meta, posts
promocionados). Mismo formato 9:16 y mismo video; solo cambia la música, que sale de una pista con
licencia para publicidad (`library.json → ads: true`). Motivo: el plan personal de Epidemic Sound no
cubre anuncios ni posts promocionados (el Pro/Commercial sí). Si la persona tiene ese plan, registra
sus pistas con `scripts/audio/music.py add … --ads` y el anuncio puede usar Epidemic. Se decide en el brief
(«¿Publicidad pagada?»). Si se decide después, basta con añadir `ads` a `storyboard.platforms` y
correr `bin/edit`.

## Entregables por pieza

Definidos en `templates/deliverables.md`. Para cada plataforma activa:

1. Video de la variante (`renders/<plataforma>.mp4`)
2. Subtítulos `.srt`
3. Título en pantalla (texto del gancho)
4. Copy / descripción (`copy/<plataforma>.md`)
5. Llamada a la acción
6. Portada (`covers/<plataforma>.jpg`)

Además, una vez por pieza: versión corta (≤ `short_max`), clips secundarios propuestos
(`clips.json` con tiempos y motivo) y la lista de recursos visuales faltantes (`faltantes.md`).
