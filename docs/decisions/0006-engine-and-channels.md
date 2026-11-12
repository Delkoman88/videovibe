# 0006 — Motor separado de los canales

**Contexto.** El sistema nació para un canal y su identidad estaba en el código (rutas a `profile/`, idioma fijo, textos de canal en las animaciones). Se quiere reutilizar para otros canales, temáticas e idiomas.
**Decisión.** `channels/<id>/` contiene todo lo del canal (perfil, marca, vocabulario, aprendizajes, piezas). Los scripts encuentran el canal subiendo desde la pieza hasta `channel.json`. El idioma vive en `lang/<código>.json`. Las animaciones se dividen en `formats/core.py` (genéricas, sin textos) y `formats/packs/<tema>.py`, activados por canal. Colores por función (`accent`, `warn`…), no por tono. Reglas en tres capas: motor (universales) < canal < pieza.
**Consecuencias.** Un canal nuevo no debe requerir cambios en `scripts/` ni en `formats/core.py`; si los requiere, es un fallo de separación. `scripts/tests/test_channel.py` impide que vuelvan rutas o nombres de canal al motor.
