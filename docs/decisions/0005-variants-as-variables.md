# 0005 — Variantes por plataforma como variables de una sola composición

**Contexto.** Tener un `index-<plataforma>.html` por plataforma hacía que HyperFrames detectara varias raíces (error `multiple_root_compositions`) y duplicaba trabajo.
**Decisión.** Una sola raíz `hf/index.html`; lo que cambia por plataforma (hoy la CTA) es una variable de composición. `compose.py` escribe `hf/variables/<plataforma>.json` y el render usa `--variables-file`.
**Consecuencias.** Diferencias por plataforma mayores (otra duración, otro gancho) requerirán más variables o storyboards derivados; la zona segura usada es la más estricta de las plataformas pedidas.
