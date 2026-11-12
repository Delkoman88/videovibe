# Contributing · Contribuir

Thanks for helping! · ¡Gracias por ayudar!

- **Bugs and ideas:** open an issue with what you ran, what you expected and the JSON output of the
  script (`bin/edit … --json`). · **Errores e ideas:** abre un issue con lo que corriste, lo que esperabas
  y la salida JSON del script.
- **Pull requests:** read `AGENTS.md` and `docs/status/` first. Logic lives in `scripts/` and `formats/`
  (deterministic, JSON output, tests). Run `.venv/bin/python -m unittest discover -s scripts/tests`.
  Technical decisions go in `docs/decisions/NNNN-*.md`; user-facing changes in `CHANGELOG.md`.
- **Never commit personal channels, footage, API keys or licensed audio.** Keep your channels in a
  separate folder (`local.json → channels_dir`). The test `test_engine_has_no_personal_data` guards the
  engine against leaks — extend its patterns locally if you fork. · **Nunca subas canales personales,
  material, claves ni audio con licencia.**
- Agent-facing docs are in Spanish; PRs in English or Spanish are both fine.
