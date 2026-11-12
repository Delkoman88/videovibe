# Conectores y servicios externos

Todos son **opcionales**. El pipeline base funciona solo con herramientas locales.

| Servicio | Para qué | Estado | Alternativa local |
|---|---|---|---|
| [OpenChatCut](https://github.com/0xsline/OpenChatCut) (MCP local, `http://localhost:5199/api/external-mcp/mcp`) | Retoques manuales en timeline | opcional, sin integrar | — |
| Epidemic Sound (MCP oficial, beta) | Buscar y descargar música (y ajustar su duración) | opcional; requiere suscripción y clave | `scripts/audio/music.py add` con cualquier pista con licencia |
| Efectos de sonido | Efectos tecnológicos sutiles | **propios**: `scripts/audio/sfx.py` los sintetiza por canal | — |
| Generación de imagen/video IA | B-roll ilustrativo | por definir | — |

## Cómo documentar un conector nuevo

Para cada uno: qué hace, si es obligatorio (no debería), variables de entorno (en `.env`, nunca en
el repo), y la configuración MCP para cada agente de `docs/agents.md`.

Las credenciales van en `.env` (ignorado por git). Nunca en `channels/`, `docs/` ni `presets/`.

## Epidemic Sound (música)

Servidor MCP oficial: `https://www.epidemicsound.com/a/mcp-service/mcp` (HTTP). Requiere suscripción
activa (descargar) y una **clave de servidor MCP** creada en Account → API keys
(https://www.epidemicsound.com/account/api-keys), válida un año. La clave va en una variable de entorno
(`EPIDEMIC_SOUND_MCP_API_KEY`), nunca en el repo.

Probado (2026-11-11, Claude Code):
- En `--header` va el **nombre** de la variable (`${EPIDEMIC_SOUND_MCP_API_KEY}`), no la clave.
- La variable debe existir **cuando arranca el agente**: guárdala en `~/.zshrc` y abre el agente
  desde una terminal nueva. Las apps de escritorio no leen `~/.zshrc` (usa `launchctl setenv`).
  Síntoma si falta: `401 … Missing environment variables`.
- Para escribirla sin que quede en pantalla ni en el historial:
  `read -s "KEY?Clave: " && echo "export EPIDEMIC_SOUND_MCP_API_KEY=\"$KEY\"" >> ~/.zshrc && unset KEY`.
- Si la clave se pega en un chat con un agente, revócala y crea otra.

| Agente | Configuración |
|---|---|
| Claude Code | `claude mcp add -s user --transport http epidemic-sound https://www.epidemicsound.com/a/mcp-service/mcp --header 'Authorization: Bearer ${EPIDEMIC_SOUND_MCP_API_KEY}'` (comillas simples: la variable se expande al usarse) |
| Codex CLI | Servidor MCP HTTP en `~/.codex/config.toml` con la misma URL y cabecera `Authorization: Bearer …` desde la variable de entorno. *Sintaxis exacta por verificar en la doc de Codex al configurarlo.* |
| Gemini CLI / Muse Code | Cualquier cliente MCP que envíe la cabecera `Authorization`. *Por verificar.* |

Herramientas útiles: `SearchRecordings` (filtros de ánimo, género, BPM…), `SearchSimilarToRecording`,
`DownloadRecording`, `EditRecording` + `PollEditRecordingJob` + `DownloadRecordingEdit` (ajustar una
pista a la duración del video, hasta 5 min), `SearchSoundEffects`.

Flujo para una pieza:
1. Busca con el ánimo del canal (`rhythm.md` → Sonido) y la duración del video (`cut/cut-map.json`).
2. `EditRecording` con `targetDurationMs` ≈ duración del video + 0.5 s, `forceDuration: true`,
   `downloadAudioFormat: WAV`: termina con un cierre musical (no hace falta fade largo).
3. Descarga y registra: `scripts/audio/music.py add --channel <canal> --file <descarga> --title … --artist …
   --source epidemic --source-id <id> --mood "…" --license "Suscripción Epidemic Sound (cuenta de <persona>)"`.
4. Úsala en `storyboard.json → audio.music.track`.

Licencia: el uso queda cubierto por la suscripción vigente; confirma en el plan contratado que incluye
las plataformas del canal. Registra la pista en `<pieza>/assets.md`.
