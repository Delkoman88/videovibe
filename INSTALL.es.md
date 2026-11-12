# Instalación · [English](INSTALL.md)

## Automática (recomendada)

```bash
git clone https://github.com/Delkoman88/videovibe && cd videovibe
bin/setup            # pregunta antes de instalar paquetes del sistema; --yes para no preguntar
bin/demo --quick    # ~1 min: corte + plan visual + borrador en el canal de ejemplo
```

`bin/setup` se puede correr las veces que haga falta. Instala:

| Componente | macOS (Homebrew) | Linux (apt) |
|---|---|---|
| ffmpeg + `zscale` (HDR de teléfono → SDR) | `ffmpeg` + `ffmpeg-full` (keg-only) | `ffmpeg` de la distribución (revisa `bin/doctor`; si no, `VIDEOVIBE_FFMPEG`) |
| whisper.cpp (`whisper-cli`) | `whisper-cpp` | se compila en `tools/whisper.cpp` |
| Node ≥ 22 | `node` | desde nodejs.org o nvm (el de apt suele ser viejo) |
| Python 3 + numpy | `python` + `.venv` | `python3-venv` + `.venv` |
| Voz sintética para la demo | `say` (incluido) | `espeak-ng` |
| HyperFrames + GSAP (versiones fijadas) | `npm ci` | `npm ci` |
| Modelos (~600 MB, verificados por checksum) | `models/` | `models/` |

También necesita **Chrome o Chromium** (HyperFrames lo usa para convertir HTML en video).

## Manual

1. Instala los paquetes del sistema de la tabla.
2. `python3 -m venv .venv && .venv/bin/pip install numpy`
3. `npm ci`
4. Modelos en `models/`:
   - `ggml-large-v3-turbo-q5_0.bin` de `huggingface.co/ggerganov/whisper.cpp`
   - `ggml-silero-v5.1.2.bin` de `huggingface.co/ggml-org/whisper-vad`
5. `bin/install-agents` (punteros para Claude Code / Gemini CLI) y `bin/doctor` hasta que todo diga `ok`.

## Tus canales

`bin/new-channel <id> --name "Nombre" --lang es` crea un canal desde la plantilla y tu agente lo completa
(`AGENTS.md`). Para tener tus canales fuera del motor (p. ej. en un repo privado), crea `local.json` en la
raíz del repo:

```json
{"channels_dir": "~/mis-canales"}
```

o usa la variable `VIDEOVIBE_CHANNELS`. `bin/doctor` dice qué carpeta se está usando.

## Opcional

- **Epidemic Sound** (buscar música con licencia con su servidor MCP): `docs/connectors.md`.
- **Tests:** `.venv/bin/python -m unittest discover -s scripts/tests` (algunos necesitan `say` de macOS y los modelos).

## Problemas comunes

- Instalar o actualizar con Homebrew puede romper otras herramientas (librerías compartidas): revisa `node -v` después; `brew upgrade node` lo arregla.
- Si mueves o renombras el repo, recrea `.venv`: `rm -rf .venv && bin/setup`.
- ffmpeg 9 quitó `-filter_complex_script`; VideoVibe usa `-/filter_complex <archivo>`.
- En zsh, una variable con varias opciones (`$X`) no se separa en palabras: usa arrays o bash.
