# Compatibilidad entre agentes

Una sola fuente de verdad: `AGENTS.md` + `docs/` + `channels/` + `scripts/` + `formats/`. Cada agente solo
necesita un puntero pequeño.

| Agente | Instrucciones | Skill | Notas |
|---|---|---|---|
| Codex CLI | `AGENTS.md` (nativo) | `.agents/skills/edit-video/` | — |
| Claude Code | `CLAUDE.md` → importa `@AGENTS.md` | `.claude/skills` → enlace simbólico a `.agents/skills` | — |
| Gemini CLI | `GEMINI.md` → importa `@AGENTS.md` | `.agents/skills/` | Alternativa: `context.fileName` en `.gemini/settings.json` |
| Muse Code (Meta) | `AGENTS.md` | `.agents/skills/` | Las skills y reglas del proyecto requieren marcar la carpeta como confiable. Rutas no confirmadas en docs oficiales; verificar en el primer uso. |

Para (re)crear los punteros: `bin/install-agents`.

Si un agente no carga la skill, basta con pedirle: "Lee AGENTS.md y sigue el pipeline". La skill es
un atajo, no la fuente de verdad.

## Probado

- **Codex CLI 0.166** (2026-11-11, `codex exec -s workspace-write`, copia limpia del repo): siguió solo
  `AGENTS.md` → `bin/welcome` → skill + `docs/getting-started.md`, creó el canal y la pieza y se detuvo
  bien en la revisión A. Lo que se aprendió:
  - Su sandbox **bloquea la GPU** (Metal): whisper fallaba. Ahora `transcribe.py` reintenta solo sin GPU
    (`VIDEOVIBE_WHISPER_CPU=1` lo fuerza desde el principio).
  - Su sandbox **no tiene red**: `bin/setup` hay que correrlo fuera de Codex (o permitir red).
- **Codex CLI** (2026-11-12, prueba de la persona con las revisiones guiadas A/B): sin problemas.
- **Claude Code**: es el agente con el que se construyó el sistema.

## Reglas para mantenerlo portable

- Nada específico de un agente dentro de `channels/`, `docs/`, `scripts/` o `formats/`.
- No usar herramientas propias de un agente (navegador integrado, conectores de una app) como
  paso obligatorio. Si se usan, deben tener alternativa por CLI documentada en `docs/connectors.md`.
- Las revisiones usan `bin/review` y `bin/open-review`: abren con el visor del sistema, muestran rutas
  absolutas y devuelven datos JSON cuando un agente necesita procesarlos.
- Los conectores MCP se documentan una vez, con la config para cada agente.
