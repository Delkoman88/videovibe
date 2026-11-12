# Cuestionario de alta de canal

> El agente hace estas preguntas (las que no pueda deducir de material existente) y con las
> respuestas redacta los archivos del canal en `channels/<id>/`. Las marcadas con ★ son obligatorias.
> Ejemplo completo de un canal ya dado de alta: `channels/science-60/` (ficticio).

## 1. Identidad → `CHANNEL.md`, `channel.json`
- ★ Nombre del canal e id corto (minúsculas-con-guiones).
- ★ Quién aparece o narra (nombre, rol, ¿sale a cámara?).
- ★ De qué trata: qué documenta, enseña o cuenta. La pregunta o promesa central.
- ★ Idioma del contenido (debe existir `lang/<idioma>.json`).

## 2. Intención y audiencia → `CHANNEL.md`
- ★ Qué debe lograr el canal (3–8 objetivos).
- ★ Audiencias (una o varias) y qué saben del tema.
- Qué NO debe parecer o hacer el canal.

## 3. Tono y guardarraíles → `CHANNEL.md`
- ★ Tono en 3–5 adjetivos y ejemplos de frases que sí / que no.
- Temas sensibles y cómo tratarlos (salud, dinero, política, menores, afirmaciones científicas…).
- ★ Principio editorial: qué preguntas debe responder cada pieza.
- ★ Llamadas a la acción típicas y persona gramatical.

## 4. Material → `CHANNEL.md` (sección material) y `topics.md`
- ★ Qué se graba (a cámara, pantalla, manos, B-roll, voz en off, IA generativa…) y en qué orientación.
- ★ Temas frecuentes (lista).

## 5. Dirección visual → `style.md`, `brand.json`
- ★ Estética en una frase + referencias. Elementos permitidos y prohibidos.
- ★ Paleta (o adjetivos para proponerla) con roles: fondo, profundidad, palabra clave, dato, remate, advertencia.
- Tipografías (si no, se proponen dos con licencia libre: display + mono).
- Animaciones preferidas; ¿hay un paquete temático que encaje (`formats/packs/`) o hay que crearlo?
- ★ Tratamiento de la imagen de quien aparece (qué se corrige, qué nunca se toca).

## 6. Ritmo y sonido → `rhythm.md`
- ★ Gancho (segundos y tipo), pausas, qué se limpia y qué se conserva.
- Densidad de efectos, acercamientos, subtítulos (tamaño, resaltado).
- Música y efectos (estilo, fuente con licencia).

## 7. Plataformas → `channel.json`, `CHANNEL.md`
- ★ Plataformas activas y enfoque de cada una (deben existir en `presets/`).
- Entregables por pieza (variantes, versión corta, clips, copy, portada).

## 8. Vocabulario → `vocabulary.txt`
- Nombres propios, siglas y términos técnicos que la transcripción debe escribir bien.
