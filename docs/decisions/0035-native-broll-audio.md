# 0035 — Audio nativo de B-roll y revisión editorial previa

El ensayo real mostró que el contexto inicial, la pertinencia de efectos y un cierre significativo
requieren revisión editorial además de QA. Se formaliza el procedimiento del agente con evidencia,
sin añadir gates ni obligar a migrar planes anteriores.

Se amplía el inserto con audio opcional. Video mudo más WAV sincronizado permite usar la mezcla
existente sin reproducción doble. Extracción exacta sin normalización SFX, defaults conservadores,
fundidos una vez y atenuación durante la voz. Caché por contenido y audio en huellas de revisión.
El límite de cuatro segundos de ADR 0034 permanece solo para el kit SFX; los insertos nativos no
pasan por él. No se habilita reordenamiento de diálogo ni voz de pantalla como corte. Sin dependencias nuevas.
