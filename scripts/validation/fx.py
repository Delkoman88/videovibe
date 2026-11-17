"""`fx`: efectos sobre la toma (recorte de la persona, ADR 0025)."""
from formats.text import VARIANTS

from .common import _num

TYPES = ("text-behind", "background-swap", "subject-glow", "freeze-cutout")


def validate(sb, state):
    ctx, errs, warns = state.ctx, state.errs, state.warns
    items = sb.get("fx", [])
    if not isinstance(items, list):
        errs.append("fx: debe ser una lista")
        return
    spans = []
    for i, fx in enumerate(items):
        p = f"fx[{i}]"
        if not isinstance(fx, dict):
            errs.append(f"{p}: debe ser un objeto")
            continue
        if not fx.get("id"):
            errs.append(f"{p}.id: obligatorio")
        elif fx["id"] in state.ids:
            errs.append(f"{p}.id: «{fx['id']}» repetido")
        state.ids.add(fx.get("id"))
        t = fx.get("type")
        if t not in TYPES:
            errs.append(f"{p}.type: «{t}» no existe ({', '.join(TYPES)})")
            continue
        if t == "freeze-cutout":
            at, d = fx.get("at"), fx.get("duration", 1.2)
            if not _num(at) or (state.dur is not None and not 0 <= at < state.dur):
                errs.append(f"{p}.at: segundo del corte donde se congela")
                continue
            if not _num(d) or not 0.5 <= d <= 2.5:
                errs.append(f"{p}.duration: entre 0.5 y 2.5 s")
                continue
            a, b = at, at + d
            talk = [w for w in ctx.get("speech") or [] if w[0] < b - 0.05 and w[1] > a + 0.05]
            if talk:
                errs.append(f"{p}: congela {a:.2f}–{b:.2f} s mientras se habla ({talk[0][0]:.2f} s): los labios "
                            f"quedarían quietos con la voz sonando (regla 3). Muévelo a una pausa")
        else:
            state.span(p, fx, allow_tail=False)
            a, b = fx.get("in"), fx.get("out")
            if not (_num(a) and _num(b)):
                continue
            if b - a > 10:
                errs.append(f"{p}: máximo 10 s (el recorte cuesta ≈ 6 s de cálculo por segundo)")
            elif b - a > 6:
                warns.append(f"{p}: {b - a:.1f} s de recorte (≈ {6 * (b - a):.0f} s de cálculo la primera vez)")
        if t == "text-behind" and not fx.get("text"):
            errs.append(f"{p}.text: obligatorio")
        if "depth" in fx and fx["depth"] not in ("behind", "front", "through"):
            errs.append(f"{p}.depth: «{fx['depth']}» (usa behind, front o through)")
        if "variant" in fx and fx["variant"] not in VARIANTS:
            errs.append(f"{p}.variant: «{fx['variant']}» (usa {', '.join(VARIANTS)})")
        if "size" in fx and (not _num(fx["size"]) or not 28 <= fx["size"] <= 400):
            errs.append(f"{p}.size: entre 28 y 400 px")
        if "y" in fx and fx["y"] != "auto" and (not _num(fx["y"]) or not 0 <= fx["y"] <= 1100):
            errs.append(f"{p}.y: «auto» o px entre 0 y 1100 (arriba de los subtítulos)")
        if "role" in fx and ctx.get("roles") and fx["role"] not in ctx["roles"]:
            errs.append(f"{p}.role: «{fx['role']}» no existe en brand.json → highlight_roles")
        spans.append((a, b, p))
    spans.sort()
    for (a1, b1, p1), (a2, b2, p2) in zip(spans, spans[1:]):
        if a2 < b1 - 0.001:
            errs.append(f"{p2}: se solapa con {p1} (un efecto sobre la toma a la vez)")
    reg = ctx.get("formats") or {}
    for sc in sb.get("scenes", []) if isinstance(sb.get("scenes"), list) else []:
        layout = sc.get("layout") or reg.get(sc.get("format"), {}).get("layout")
        if layout != "full" or not _num(sc.get("in")) or not _num(sc.get("out")):
            continue
        for a, b, p in spans:
            if a < sc["out"] and b > sc["in"]:
                warns.append(f"{p}: cae dentro de la escena «{sc.get('id')}» (full), que tapa la toma")
