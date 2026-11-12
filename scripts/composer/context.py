"""Contexto de una composición: lo que antes eran variables globales de compose.py."""
from dataclasses import dataclass

W, H = 1080, 1920


@dataclass(frozen=True)
class Ctx:
    brand: dict
    packs: tuple
    font_faces: str
    lang: str


def font_faces(brand):
    """@font-face de las fuentes de marca (display y mono), servidas desde assets/fonts/ del proyecto hf."""
    out = []
    for key in ("display", "mono"):
        f = brand["fonts"][key]
        out.append(f"@font-face {{ font-family: '{f['family']}'; src: url('assets/fonts/{f['file']}'); "
                   f"font-weight: 100 900; }}")
    return "\n".join(out)
