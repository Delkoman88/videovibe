# 0024 — Moléculas 3D con 3Dmol.js: vista absoluta por cuadro, superficies con espera y datos locales

**Fecha:** 2026-11-17 · **Estado:** vigente

## Contexto

Un canal de ciencia o biotecnología necesita mostrar proteínas, ADN y fármacos con calidad
de divulgación: girando, señalando un sitio activo y comparando moléculas, con los colores de la marca y sin
romper el render determinista ni depender de internet.

## Decisión

1. **3Dmol.js 2.5.5** (BSD-3, WebGL) como librería opcional (`needs=("3dmol",)`, ADR 0022). Se descartó Mol*
   por tamaño y porque 3Dmol expone una API simple de vista (`getView`/`setView`) y estilos por selección.
2. **Vista absoluta por cuadro:** en cada cuadro `resize()` → `setView(vista interpolada)` → `rotate(ángulo
   absoluto)` → `render()`. La vista del foco se calcula al construir (`zoomTo(selección)` y se vuelve a la
   base); el viaje interpola posición y zoom (el cuaternión no cambia). Nunca rotaciones acumuladas.
3. **Superficies con espera:** `addSurface` es asíncrono (usa workers); la promesa se registra en
   `window.__hf.buildReady[<caja>]` y HyperFrames no captura hasta que termina. Probado: capturas en distinto
   orden con superficie dan píxeles idénticos.
4. **Datos locales con resumen:** `scripts/tools/structures.py fetch` descarga una vez de RCSB PDB o PubChem
   y guarda en la biblioteca (`assetlib`, tipo `structures`) el resumen: cadenas, rango de residuos y
   ligandos. Con eso la validación del storyboard revisa `focus` (`@fmt(..., check_items=...)`).
5. **Marca:** cada cadena toma un acento (`accent`, `accent2`, `accent3`, `warn`); los ligandos van en
   `accent3`; el carbono de las moléculas pequeñas en `accent`. Fondo transparente y borde con desvanecido
   radial para que la molécula se integre al fondo de la escena.

## Consecuencias

- Licencias de datos: PDB CC0 1.0; PubChem dominio público; modelos propios con la licencia que declare la
  persona (`add`). Todo queda en `assets.md` de la pieza.
- WebGL sin GPU (WSL, CI) es más lento; una superficie de proteína grande tarda segundos en calcularse antes
  del primer cuadro.
- Estructuras enormes (ribosomas, cápsides) pueden ser pesadas para el navegador; preferir un fragmento
  (`add` de un PDB recortado) o el estilo `cartoon`.
