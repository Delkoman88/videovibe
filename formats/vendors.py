"""Librerías de animación opcionales: qué archivos copia cada una y cómo se carga en index.html.

Un formato declara lo que usa con `@fmt(..., needs=("pixi", "gsap:SplitText"))`. compose.py reúne las
necesidades de las escenas del storyboard (`formats.needs(sb)`) y aquí se resuelven:
- `copy(needs, node_modules, vendor_dir)` deja en hf/assets/vendor/ exactamente lo necesario
  (GSAP siempre; lo demás solo si se pide) y borra lo que quedó de una composición anterior.
- `head(needs)` devuelve las etiquetas <script> en orden de carga.

Reglas para agregar una librería (ADR 0022):
- Versión exacta en package.json; nunca CDN: el render no usa red.
- Si la librería usa `Math.random()` (ids, semillas, efectos), `seeded=True`: al copiarla se redirige al
  generador fijo `globalThis.__videovibeRandom` que `head()` declara antes de cargarla.
- `before_gsap=True` solo si otra librería debe existir antes que GSAP (hoy, ninguna lo exige; Pixi lo
  conserva para que las piezas existentes salgan idénticas).
- Los plugins de GSAP se nombran `gsap:<Plugin>` y se registran con `gsap.registerPlugin` tras cargar GSAP.
"""
import hashlib
from dataclasses import dataclass

GSAP = ("gsap/dist/gsap.min.js", "gsap.min.js")
SEED = 0x4d524c4e  # semilla del generador fijo; cambiarla altera el render de las piezas con librerías `seeded`

PRNG = f"""    <script>
      globalThis.__videovibeSeed = 0x{SEED:08x};
      globalThis.__videovibeRandom = () => {{
        let x = globalThis.__videovibeSeed >>> 0;
        x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
        globalThis.__videovibeSeed = x >>> 0;
        return globalThis.__videovibeSeed / 4294967296;
      }};
    </script>
"""


@dataclass(frozen=True)
class Vendor:
    files: tuple            # ((ruta dentro de node_modules, nombre en assets/vendor/), …) en orden de carga
    seeded: bool = False    # redirigir Math.random() al generador fijo
    before_gsap: bool = False
    plugin: str = ""        # nombre global para gsap.registerPlugin (solo plugins de GSAP)
    license: str = ""
    after: str = ""         # script en línea tras cargar la librería (p. ej. renombrar su variable global)


def _gsap_plugin(name, file=None):
    file = file or name
    return Vendor(files=((f"gsap/dist/{file}.min.js", f"{file}.min.js"),), plugin=name, license="GSAP (sin costo)")


VENDORS = {
    "pixi": Vendor(files=(("pixi.js/dist/pixi.min.js", "pixi.min.js"),
                          ("pixi-filters/dist/pixi-filters.js", "pixi-filters.js")),
                   seeded=True, before_gsap=True, license="MIT"),
    # Lottie: se renombra para que el adaptador de HyperFrames no la mueva por su cuenta; la mueve la
    # línea de tiempo de cada escena (un solo reloj, ADR 0022).
    "lottie": Vendor(files=(("lottie-web/build/player/lottie_svg.min.js", "lottie_svg.min.js"),), seeded=True,
                     license="MIT", after="globalThis.__vvLottie = globalThis.lottie; delete globalThis.lottie;"),
    # 3Dmol.js: moléculas con WebGL; cada escena dibuja su cuadro desde la línea de tiempo (ADR 0024).
    "3dmol": Vendor(files=(("3dmol/build/3Dmol-min.js", "3Dmol-min.js"),), seeded=True, license="BSD-3-Clause"),
    "gsap:SplitText": _gsap_plugin("SplitText"),
    "gsap:ScrambleTextPlugin": Vendor(files=(("gsap/dist/ScrambleTextPlugin.min.js", "ScrambleTextPlugin.min.js"),),
                                      seeded=True, plugin="ScrambleTextPlugin", license="GSAP (sin costo)"),
    "gsap:DrawSVGPlugin": _gsap_plugin("DrawSVGPlugin"),
    "gsap:MorphSVGPlugin": _gsap_plugin("MorphSVGPlugin"),
    "gsap:MotionPathPlugin": _gsap_plugin("MotionPathPlugin"),
    "gsap:Physics2DPlugin": _gsap_plugin("Physics2DPlugin"),
    "gsap:CustomEase": _gsap_plugin("CustomEase"),
}


def unknown(needs):
    return sorted(set(needs) - set(VENDORS))


def _ordered(needs):
    return [k for k in VENDORS if k in needs]  # orden estable: el de la tabla


def files(needs):
    """[(origen en node_modules, nombre en vendor/, seeded)] de GSAP + lo pedido, en orden de carga."""
    out = [(GSAP[0], GSAP[1], False)]
    for key in _ordered(needs):
        v = VENDORS[key]
        out += [(src, dst, v.seeded) for src, dst in v.files]
    return out


def seeded_source(source):
    """Redirige la aleatoriedad de terceros al generador fijo del proyecto."""
    return source.replace("Math.random()", "globalThis.__videovibeRandom()")


def _write_if_changed(dst, data):
    if dst.exists() and dst.stat().st_size == len(data) and \
            hashlib.sha256(dst.read_bytes()).digest() == hashlib.sha256(data).digest():
        return False
    dst.write_bytes(data)
    return True


def copy(needs, node_modules, vendor_dir):
    """Copia lo necesario a vendor_dir (solo si cambió) y borra lo que sobra. Devuelve faltantes."""
    if bad := unknown(needs):
        raise KeyError(f"librerías desconocidas: {bad} (disponibles: {sorted(VENDORS)})")
    wanted = files(needs)
    missing = [src for src, _, _ in wanted if not (node_modules / src).exists()]
    if missing:
        return missing
    vendor_dir.mkdir(parents=True, exist_ok=True)
    keep = set()
    for src, dst, seeded in wanted:
        data = (node_modules / src).read_bytes()
        if seeded:
            data = seeded_source(data.decode("utf-8")).encode("utf-8")
        _write_if_changed(vendor_dir / dst, data)
        keep.add(dst)
    for old in vendor_dir.iterdir():  # restos de una composición anterior con otras escenas
        if old.is_file() and old.name not in keep:
            old.unlink()
    return []


def head(needs):
    """Etiquetas <script> para index.html, en orden de carga. Sin necesidades: solo GSAP."""
    keys = _ordered(needs)
    tag = '    <script src="assets/vendor/{}"></script>\n'
    out = PRNG if any(VENDORS[k].seeded for k in keys) else ""
    for k in keys:
        if VENDORS[k].before_gsap:
            out += "".join(tag.format(dst) for _, dst in VENDORS[k].files)
            if VENDORS[k].after:
                out += f"    <script>{VENDORS[k].after}</script>\n"
    out += tag.format(GSAP[1])
    for k in keys:
        if not VENDORS[k].before_gsap:
            out += "".join(tag.format(dst) for _, dst in VENDORS[k].files)
            if VENDORS[k].after:
                out += f"    <script>{VENDORS[k].after}</script>\n"
    plugins = [VENDORS[k].plugin for k in keys if VENDORS[k].plugin]
    if plugins:
        out += f'    <script>gsap.registerPlugin({", ".join(plugins)});</script>\n'
    return out
