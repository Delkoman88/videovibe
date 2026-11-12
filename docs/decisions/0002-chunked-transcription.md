# 0002 — Transcribir tramo por tramo

**Contexto.** whisper sobre el archivo completo (con o sin VAD) omitía muletillas y frases cortas tras una pausa («¿no?», «eh…») y desplazaba tiempos hasta 1 s. Con VAD, la palabra pegada a un silencio lo «absorbe». Ventanas cortadas a mitad de frase hicieron alucinar palabras («enfermedades *humanas*»).
**Decisión.** `transcribe.py` detecta tramos de voz por energía y transcribe cada tramo por separado, sin VAD, con el texto previo como contexto y filtro de alucinaciones por idioma. Las palabras se reparten dentro del tramo por longitud.
**Descartado.** Pasada completa + alineación por programación dinámica (queda como `--mode full`); dos pasadas fusionadas (introducía repeticiones falsas).
**Consecuencias.** Más lento (~75 s por 90 s; carga el modelo por tramo). Pierde algo de puntuación: revisar el gancho a mano. Mejora pendiente: whisper en modo servidor.
