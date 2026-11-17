"""Texto cinético compartido: partir un texto en palabras y letras (en Python, sin depender de que cargue
la fuente) y animarlo con GSAP. Lo usan el paquete `motion` y las tarjetas con `text_fx` (scripts/composer).
`*palabra*` marca una palabra en color de acento."""
from formats.core import esc

VARIANTS = ("rise", "wave", "blur", "mask")

def kinetic(text, cls="kt"):
    """Texto partido en palabras y letras (spans). *palabra* → acento de color."""
    words = []
    for raw in str(text).split():
        acc = raw.startswith("*") and raw.endswith("*") and len(raw) > 2
        word = raw.strip("*") if acc else raw
        chars = "".join(f'<span class="ch">{esc(c)}</span>' for c in word)
        words.append(f'<span class="kw{" acc" if acc else ""}"><span class="kwi">{chars}</span></span>')
    return f'<span class="{cls}">{" ".join(words)}</span>'


def plain(text):
    return str(text).replace("*", "")


def title_size(text, big=132):
    n = len(plain(text))
    return big if n <= 12 else int(big * .85) if n <= 22 else int(big * .7) if n <= 36 else int(big * .58)


KINETIC_CSS = """
    .kt { display: inline; }
    .kw { display: inline-block; overflow: hidden; padding: .14em .02em .1em; margin: -.14em 0 -.1em;
          vertical-align: bottom; }
    .kwi { display: inline-block; }
    .ch { display: inline-block; }  /* sin will-change: con él, Chrome rasteriza cada letra una vez y el borde
                                      depende del orden en que se visitan los cuadros (ADR 0025) */
    .acc { color: var(--accent); text-shadow: 0 0 28px color-mix(in srgb, var(--accent) 55%, transparent); }
"""


def kinetic_in(sel, variant, t0, n_chars):
    """Tweens de entrada para el texto de `kinetic` (sel = contenedor)."""
    st = min(0.035, 0.9 / max(n_chars, 1))
    if variant == "wave":
        return (f'tl.fromTo("{sel} .ch", {{y: 70, rotation: 14, opacity: 0}}, {{y: 0, rotation: 0, opacity: 1, '
                f'duration: .55, ease: "back.out(2.2)", stagger: {st:.3f}}}, {t0:.3f});')
    if variant == "blur":
        return (f'tl.fromTo("{sel} .ch", {{opacity: 0, scale: 1.7, filter: "blur(14px)"}}, {{opacity: 1, scale: 1, '
                f'filter: "blur(0px)", duration: .5, ease: "power3.out", stagger: {st:.3f}}}, {t0:.3f});')
    if variant == "mask":
        return (f'tl.fromTo("{sel} .kwi", {{yPercent: 105}}, {{yPercent: 0, duration: .6, ease: "expo.out", '
                f'stagger: .07}}, {t0:.3f});')
    return (f'tl.fromTo("{sel} .ch", {{yPercent: 115}}, {{yPercent: 0, duration: .62, ease: "expo.out", '
            f'stagger: {st:.3f}}}, {t0:.3f});')  # rise


def kinetic_out(sel, variant, t):
    if variant in ("rise", "mask"):
        return (f'tl.to("{sel} .kwi", {{yPercent: -105, duration: .32, ease: "power3.in", stagger: .03}}, {t:.3f});')
    return (f'tl.to("{sel} .ch", {{opacity: 0, y: -24, filter: "blur(8px)", duration: .28, ease: "power2.in", '
            f'stagger: .008}}, {t:.3f});')


