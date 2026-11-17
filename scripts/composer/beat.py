"""Efectos al ritmo (`storyboard.json → beat_fx`, ADR 0026): una envoltura de la cámara (`#beatwrap`) que
late o se sacude en los golpes, y una capa de destello (`#beatflash`) debajo de tarjetas y subtítulos.

Los movimientos de cámara (`camera.moves`) siguen en `#cam`; los golpes van en la envoltura, así nunca
animan la misma propiedad del mismo elemento. Sin `beat_fx`, no se genera nada.
"""
from scripts.pipeline.beats import pick

ROLES = ("accent", "accent2", "accent3")


def _hash(i, salt):
    x = (i * 374761393 + salt * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return (x & 0xFFFF) / 0xFFFF - 0.5


def markup(sb, beats_data):
    """(abrir envoltura, cerrar envoltura + capa de destello, js). Vacío si no hay beat_fx."""
    items = sb.get("beat_fx") or []
    if not items or not beats_data:
        return "", "", ""
    js = ['tl.set("#beatwrap", {scale: 1, x: 0, y: 0}, 0);', 'tl.set("#beatflash", {opacity: 0}, 0);']
    n = 0
    for it in items:
        s = float(it.get("strength", 0.5))
        times = pick(beats_data, it["in"], it["out"], it.get("every", "beat"))
        for k, t in enumerate(times):
            gap = (times[k + 1] - t) if k + 1 < len(times) else 0.4
            dur = round(max(min(gap * 0.8, 0.3), 0.08), 3)
            fx = it["fx"]
            if fx == "pulse":
                js.append(f'tl.fromTo("#beatwrap", {{scale: {1 + 0.05 * s:.4f}}}, {{scale: 1, duration: {dur}, '
                          f'ease: "power2.out", immediateRender: false}}, {t});')
            elif fx == "shake":
                dx, dy = round(_hash(n, 1) * 36 * s, 1), round(_hash(n, 2) * 36 * s, 1)
                js.append(f'tl.fromTo("#beatwrap", {{x: {dx}, y: {dy}}}, {{x: 0, y: 0, duration: {min(dur, .16)}, '
                          f'ease: "power2.out", immediateRender: false}}, {t});')
            elif fx == "flash":
                js.append(f'tl.fromTo("#beatflash", {{opacity: {0.32 * s:.3f}}}, {{opacity: 0, duration: {min(dur, .24)}, '
                          f'ease: "power2.out", immediateRender: false}}, {t});')
            else:  # strobe: destellos cortos alternando los acentos de la marca
                js.append(f'tl.set("#beatflash", {{backgroundColor: vvBeatColor({n % 3})}}, {t});')
                js.append(f'tl.fromTo("#beatflash", {{opacity: {0.55 * s:.3f}}}, {{opacity: 0, duration: {min(dur, .12)}, '
                          f'ease: "none", immediateRender: false}}, {t});')
            n += 1
    js.insert(0, 'const vvBeatColor = (i) => getComputedStyle(document.documentElement)'
                 '.getPropertyValue(["--accent", "--accent2", "--accent3"][i]).trim();')
    opening = '<div id="beatwrap" style="position:absolute;inset:0;transform-origin:50% 45%">\n      '
    closing = ('\n      </div>\n      <div id="beatflash" style="position:absolute;inset:0;background:var(--accent);'
               'opacity:0;mix-blend-mode:screen;pointer-events:none"></div>')
    return opening, closing, "\n      ".join(js)
