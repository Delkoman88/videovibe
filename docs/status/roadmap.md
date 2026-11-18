# Roadmap

| Fase | Objetivo | Estado |
|---|---|---|
| 1. Corte | De la toma cruda a un corte limpio aprobado (revisión A) | ✅ 2026-11-10 |
| 2. Composición | Subtítulos, plan visual, animaciones, color, render y verificación por plataforma | ✅ 2026-11-11 |
| 3. Multicanal | Motor separado de los canales; idiomas; estado del sistema documentado | ✅ Motor 2026-11-11; segundo canal real validado con MRΛN el 2026-11-16 (confirmado 2026-11-17) |
| 4. Portabilidad | Operado de punta a punta por Codex, Gemini CLI y Muse Code | ⏳ Demo Linux y entrega real Ubuntu/WSL completadas; falta validar Gemini CLI y Muse Code |
| 5. Audio | Voz tratada, música y efectos con licencia, mezcla con ducking, audios propios, micrófono externo | ✅ 2026-11-11 |
| 6. Material múltiple | B-roll, pantalla horizontal reencuadrada, voz en off | ⏳ |
| 7. Derivados | Versión corta, clips, portadas y copy automáticos; X | ⏳ |
| 8. Datos reales | Formatos que animan resultados reales | ⏳ |
| 9. YouTube | Shorts y video horizontal largo | ⏳ |
| 10. Público | Repo abierto (Apache-2.0), instalación y demo en inglés y español | ✅ Repo abierto; versión actual v0.13.1-alpha |

Cada fase de entrega se cierra cuando una pieza real la usa y pasa `verify.py`.

La [dirección de animaciones v2](../animation-direction.md) está implementada en el motor compartido,
incluida en v0.13.0-alpha. Su validación técnica local está cerrada (36 formatos × 3 perfiles); el ensayo aislado
no requiere B ni constituye una entrega editorial. Quedan la ejecución nueva en WSL y los jobs
remotos macOS/Ubuntu. Resultados y límites: [STATUS](STATUS.md).
