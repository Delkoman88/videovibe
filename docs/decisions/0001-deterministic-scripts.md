# 0001 — Lógica en scripts deterministas; los agentes los operan

**Contexto.** El sistema debe funcionar igual con Codex, Claude Code, Gemini CLI o Muse Code, y dar el mismo resultado cada vez.
**Decisión.** Cortes, tiempos, composición, render y verificación viven en `scripts/` y `formats/`, con `--help`, salida JSON y códigos de salida (0 ok, 1 verificación fallida, 2 error). El agente decide lo creativo (storyboard, copy) y ejecuta scripts; no edita video «a ojo».
**Descartado.** Instrucciones largas en prosa para que el agente haga cada paso a mano (como un SKILL.md de 1 000 líneas): depende del modelo y no se puede probar.
**Consecuencias.** Cada capacidad nueva es un script con test. La documentación describe cuándo usar cada script, no cómo cortar.
