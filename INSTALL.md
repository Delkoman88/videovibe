# Install · [Español](INSTALL.es.md)

## Automatic (recommended)

```bash
git clone https://github.com/Delkoman88/videovibe && cd videovibe
bin/setup            # asks before installing system packages; --yes to skip the questions
bin/demo --quick    # ~1 min: cut + visual plan + draft on the example channel
```

`bin/setup` is idempotent (safe to run again). It installs:

| Component | macOS (Homebrew) | Linux (apt) |
|---|---|---|
| ffmpeg + `zscale` (phone HDR → SDR) | `ffmpeg` + `ffmpeg-full` (keg-only) | distro `ffmpeg` (check `bin/doctor`; otherwise set `VIDEOVIBE_FFMPEG`) |
| whisper.cpp (`whisper-cli`) | `whisper-cpp` | built from source into `tools/whisper.cpp` |
| Node ≥ 22 | `node` | install from nodejs.org or nvm (apt's is usually too old) |
| Python 3 + numpy | `python` + `.venv` | `python3-venv` + `.venv` |
| Synthetic voice for the demo | built-in `say` | `espeak-ng` |
| HyperFrames + GSAP (pinned) | `npm ci` | `npm ci` |
| Models (~600 MB, checksum verified) | `models/` | `models/` |

It also needs **Chrome or Chromium** (HyperFrames renders HTML to video with it).

## Manual

1. Install the system packages from the table.
2. `python3 -m venv .venv && .venv/bin/pip install numpy`
3. `npm ci`
4. Models into `models/`:
   - `ggml-large-v3-turbo-q5_0.bin` from `huggingface.co/ggerganov/whisper.cpp`
   - `ggml-silero-v5.1.2.bin` from `huggingface.co/ggml-org/whisper-vad`
5. `bin/install-agents` (pointers for Claude Code / Gemini CLI) and `bin/doctor` until everything is `ok`.

## Your channels

`bin/new-channel <id> --name "Name" --lang en` creates a channel from the template; your agent
completes it (`AGENTS.md`). To keep your channels outside the engine (e.g. a private repo), create
`local.json` in the repo root:

```json
{"channels_dir": "~/my-channels"}
```

or set `VIDEOVIBE_CHANNELS`. `bin/doctor` prints which folder is in use.

## Optional

- **Epidemic Sound** (licensed music search via its MCP server): `docs/connectors.md`.
- **Tests:** `.venv/bin/python -m unittest discover -s scripts/tests` (some need macOS `say` and the models).

## Troubleshooting

- A Homebrew upgrade can break other tools (shared libraries): check `node -v` afterwards; `brew upgrade node` fixes it.
- If you move or rename the repo, recreate `.venv`: `rm -rf .venv && bin/setup`.
- ffmpeg 9 removed `-filter_complex_script`; VideoVibe uses `-/filter_complex <file>` on ffmpeg ≥ 7 and the old option on ffmpeg 6 (e.g. Ubuntu 24.04), detected automatically.
