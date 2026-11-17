"""Estabilizar el recorte de la persona en cámara fija (ADR 0025).

El modelo de recorte decide cuadro por cuadro, sin memoria: a veces toma como «persona» un pedazo de cortina
o la silla y al cuadro siguiente ya no (el fondo parpadea). Con la cámara fija, el fondo real se puede
reconstruir del propio tramo y usarlo de referencia:

1. Fondo de referencia: por cada punto, la mediana de los cuadros donde el modelo NO ve persona ahí.
2. Se quita solo lo que cumple todo: no es el núcleo del cuerpo (persona en ≥ 90 % de los cuadros), es
   igual al fondo de referencia y es pasajero (el modelo lo ve en menos de la mitad de los cuadros de ±1 s).
   La cortina que aparece 9 cuadros se va; la chamarra oscura sobre la silla oscura se queda.
3. Lo quitado se limpia con mayoría espacial 3×3 y de 5 cuadros, con 1 punto de margen junto al cuerpo.
4. Lo inverso: si el modelo deja de ver un pedazo del cuerpo unos cuadros (ropa oscura), ese punto es persona
   en ≥ 50 % del tramo, se ve igual que cuando sí lo era y es un pedazo grande (≥ 5×5 puntos), se rellena.
5. La opacidad del modelo se vuelve más sólida (0.08 → 0, 0.7 → 1): la ropa oscura que el modelo deja
   semitransparente ya no deja ver el fondo nuevo ni el halo a través del cuerpo.

La decisión se toma a baja resolución (135×240) y multiplica la máscara original a resolución completa:
los bordes suaves del modelo se conservan. Si la cámara se mueve (el fondo no es estable), no se toca nada.
Solo cambia qué píxeles son de la persona; nunca los colores ni la forma (regla 3).
"""
import subprocess

import numpy as np

from scripts.core import oslib

W, H = 1080, 1920
SW, SH = 135, 240           # resolución de decisión
DIFF = 22                   # diferencia mínima con el fondo (0–255, media de RGB) para ser persona
CORE = 0.9                  # fracción de cuadros para ser «núcleo»
UNSTABLE = 18               # desviación típica del fondo por encima de la cual se asume cámara en movimiento
PERSIST = 0.5               # fracción de cuadros (±1 s) con persona a partir de la cual algo NO es un parpadeo
PERSIST_R = 15              # radio de esa ventana en cuadros
FILL = 0.5                  # fracción de cuadros del tramo con persona para rellenar un hueco pasajero
SEEN = 0.08                 # opacidad del modelo a partir de la cual «ve» algo (= SOLID[0])
SOLID = (0.08, 0.7)
BLUR = 4                    # cuadros antes y después para cerrar el cuerpo que el movimiento rápido emborrona
OPEN = 0.65                 # fracción máxima del contorno de un relleno que puede dar al fondo         # opacidad del modelo que pasa a 0 y a 1: el cuerpo tenue (ropa oscura) queda sólido


def _frames(cmd, shape):
    """Lee cuadros crudos de un proceso ffmpeg."""
    size = int(np.prod(shape))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(shape)
    finally:
        p.stdout.close()
        p.wait()


def _rgb(path, w, h):
    return _frames([oslib.FFMPEG, "-v", "error", "-i", str(path), "-vf", f"scale={w}:{h}:flags=area",
                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], (h, w, 3))


def _alpha(path, w, h):
    return _frames([oslib.FFMPEG, "-v", "error", "-c:v", "libvpx-vp9", "-i", str(path),
                    "-vf", f"alphaextract,scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"], (h, w))


def decide(rgb, alpha):
    """rgb (T,SH,SW,3) uint8 y alpha (T,SH,SW) uint8 → (decisión (T,SH,SW) uint8, info).
    Por punto: 0 quitar (fondo que parpadea), 1 dejar como dice el modelo, 2 rellenar (cuerpo que el modelo perdió)."""
    a = alpha.astype(np.float32) / 255
    person = a > 0.5
    core = person.mean(axis=0) >= CORE
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)  # puntos sin muestras de fondo → NaN, se tratan aparte
    sample = rgb[::2].astype(np.float32)
    bgmask = (a[::2] < 0.15)[..., None]
    bg = np.nanmedian(np.where(bgmask, sample, np.nan), axis=0)          # (SH,SW,3), NaN sin muestras
    valid = ~np.isnan(bg[..., 0])
    spread = np.nanstd(np.where(bgmask, sample, np.nan), axis=0).mean(axis=-1)
    stability = float(np.nanmedian(spread[valid])) if valid.any() else 99.0
    info = {"stability": round(stability, 1), "background_known": round(float(valid.mean()), 3)}
    if stability > UNSTABLE or valid.mean() < 0.2 or not core.any():
        return None, {**info, "applied": False}
    diff = _box(np.abs(rgb.astype(np.float32) - np.nan_to_num(bg)[None]).mean(axis=-1), 1)
    seen = a > SEEN                                                     # el modelo lo ve, aunque sea tenue
    steady = _tmean(seen, PERSIST_R) >= PERSIST                         # lo ve casi todo el segundo: no es parpadeo
    cand = seen & ~core[None] & valid[None] & (diff <= DIFF) & ~steady  # igual al fondo Y pasajero
    drop = _box(cand.astype(np.float32), 1) >= 5 / 9                    # mayoría espacial 3×3: sin motas…
    drop = (_box(drop.astype(np.float32), 1) > 0) & cand                # …sin perder esquinas ni bordes
    loose = seen & ~core[None] & valid[None] & ~steady
    for _ in range(2):                                                  # el filo de lo quitado (línea fina) también
        drop |= loose & (_box(drop.astype(np.float32), 1) >= 4 / 9)
    drop = _tmajority(drop, 2)                                          # mayoría de 5 cuadros: sin parpadeo
    body = seen & ~drop
    drop &= ~(_box(body.astype(np.float32), 1) > 0)                     # margen de 1 punto junto al cuerpo: no come pelo ni dedos
    removed = float((person & drop).sum() / max(person.sum(), 1))
    # Lo inverso: el modelo deja de ver un pedazo del cuerpo unos cuadros (la chamarra oscura). Si ahí hay persona
    # casi todo el segundo y el punto se ve igual que cuando sí era persona (nada se movió), se rellena.
    inner = (a > 0.9) & (_box(person.astype(np.float32), 1) >= 1)     # cuerpo seguro (no el filo con pared mezclada)
    same = _like_last_body(rgb, inner)
    present = (person.mean(axis=0) >= FILL)[None]                      # persona en la mayor parte del tramo
    fill = ~person & present & same & ~drop
    # Movimiento rápido: la mano o la manga borrosas que el modelo pierde 1–3 cuadros. Si el punto es persona en
    # alguno de los BLUR cuadros anteriores y en alguno de los siguientes y no es fondo confirmado, se rellena.
    known = bgmask.sum(axis=0)[..., 0] >= 3                             # fondo visto en varios cuadros, no solo en el hueco
    background = (valid & known)[None] & (diff <= DIFF)
    fill |= _around(person, BLUR) & ~person & ~background & ~drop
    core5 = _box(fill.astype(np.float32), 2) >= 1                       # apertura 5×5: solo pedazos grandes (la chamarra),
    fill = (_box(core5.astype(np.float32), 2) > 0) & fill               # no los filos delgados junto a la cabeza
    fill = _enclosed_pieces(fill, person)                               # no la silla ni el filo del cuadro: solo huecos del cuerpo
    filled = float(fill.sum() / max(person.sum(), 1))
    out = np.where(drop, 0, np.where(fill, 2, 1)).astype(np.uint8)
    return out, {**info, "applied": True, "removed": round(removed, 4), "filled": round(filled, 4)}


def _labels(m):
    """Componentes conexas (4 vecinos) por cuadro: etiqueta única > 0 en `m`, 0 fuera (propagación del máximo)."""
    lab = np.where(m, np.arange(1, m.size + 1).reshape(m.shape), 0)
    while True:
        p = np.pad(lab, [(0, 0), (1, 1), (1, 1)])
        nb = np.maximum.reduce([p[:, :-2, 1:-1], p[:, 2:, 1:-1], p[:, 1:-1, :-2], p[:, 1:-1, 2:], lab])
        nb = np.where(m, nb, 0)
        if np.array_equal(nb, lab):
            return lab
        lab = nb


def _enclosed_pieces(fill, person):
    """Deja solo los pedazos de relleno cuyo contorno toca sobre todo cuerpo (el hueco de la chamarra) y no fondo:
    un pedazo que da al fondo en más de OPEN de su contorno es fondo que el modelo, con razón, dejó de ver
    (la silla tras la mano, un filo del cuadro). El borde del cuadro no cuenta como fondo."""
    if not fill.any():
        return fill
    lab = _labels(fill)
    def touches(m):
        p = np.pad(m, [(0, 0), (1, 1), (1, 1)])
        return p[:, :-2, 1:-1] | p[:, 2:, 1:-1] | p[:, 1:-1, :-2] | p[:, 1:-1, 2:]
    outside = touches(~person & ~fill) & fill
    body = touches(person) & fill
    n = lab.max() + 1
    o = np.bincount(lab[outside], minlength=n)
    b = np.bincount(lab[body], minlength=n)
    ok = o <= OPEN * np.maximum(o + b, 1)
    ok[0] = False
    return ok[lab]


def _box(x, r):
    """Media en una caja (2r+1)² por cuadro (ejes -2, -1)."""
    n = 2 * r + 1
    pad = [(0, 0)] * (x.ndim - 2) + [(r, r), (r, r)]
    c = np.cumsum(np.cumsum(np.pad(x, pad, mode="edge"), axis=-2), axis=-1)
    c = np.pad(c, [(0, 0)] * (x.ndim - 2) + [(1, 0), (1, 0)])
    return (c[..., n:, n:] - c[..., :-n, n:] - c[..., n:, :-n] + c[..., :-n, :-n]) / (n * n)


def fill_interior(keep, alpha, r=8):
    """Cierre en el tiempo para efectos donde el recorte va encima de la misma toma (`subject-glow`): un punto
    que es persona en algún cuadro de los r anteriores Y en alguno de los r siguientes se rellena (2), igual que
    el interior del cuerpo (el contorno sigue siendo el del modelo). Si el
    modelo pierde la chamarra unos cuadros, el halo no asoma por el hueco; rellenar de más ahí no se nota,
    porque muestra los mismos píxeles de la toma."""
    body = (keep > 0) & ((alpha > 0.5 * 255) | (keep == 2))
    T = len(body)
    past = np.zeros_like(body)
    futr = np.zeros_like(body)
    for t in range(T):
        past[t] = body[max(t - r, 0):t].any(axis=0) if t else False
        futr[t] = body[t + 1:t + 1 + r].any(axis=0) if t + 1 < T else False
    fill = past & futr & ~body & (keep > 0)
    inner = _box((body | fill).astype(np.float32), 1) >= 1             # interior (sin el contorno): huecos finos del modelo
    keep = keep.copy()
    keep[fill | (inner & (keep > 0))] = 2
    return keep


def _like_last_body(rgb, person):
    """True donde el punto se ve igual (≤ DIFF) que la última o la próxima vez que fue cuerpo seguro (`person`)."""
    T = len(rgb)
    x = rgb.astype(np.float32)
    out = np.zeros(person.shape, bool)
    for order in (range(T), range(T - 1, -1, -1)):
        last = np.full(x.shape[1:], -999.0, np.float32)
        for t in order:
            out[t] |= _box(np.abs(x[t] - last).mean(axis=-1), 1) <= DIFF
            last = np.where(person[t][..., None], x[t], last)
    return out


def _around(m, r):
    """True donde `m` es cierto en alguno de los r cuadros anteriores Y en alguno de los r siguientes."""
    c = np.cumsum(np.concatenate([np.zeros_like(m[:1], np.int32), m.astype(np.int32)]), axis=0)
    t = np.arange(len(m))
    past = c[t] - c[np.clip(t - r, 0, None)]
    futr = c[np.clip(t + 1 + r, None, len(m))] - c[np.clip(t + 1, None, len(m))]
    return (past > 0) & (futr > 0)


def _tmean(m, r):
    """Fracción de cuadros con `m` en una ventana de 2r+1 cuadros (en los extremos, solo los cuadros que hay)."""
    c = np.cumsum(np.concatenate([np.zeros_like(m[:1], np.int32), m.astype(np.int32)]), axis=0)
    t = np.arange(len(m))
    lo, hi = np.clip(t - r, 0, len(m)), np.clip(t + r + 1, 0, len(m))
    shape = (-1,) + (1,) * (m.ndim - 1)
    return (c[hi] - c[lo]) / (hi - lo).reshape(shape)


def _tmajority(m, r):
    """Mayoría temporal en una ventana de 2r+1 cuadros."""
    p = np.concatenate([m[:1].repeat(r, 0), m, m[-1:].repeat(r, 0)]).astype(np.uint8)
    c = np.cumsum(np.concatenate([np.zeros_like(p[:1]), p]), axis=0, dtype=np.int32)
    return (c[2 * r + 1:] - c[:-2 * r - 1]) > r


def _upsample(mask):
    """Máscara 135×240 → 1080×1920 casi binaria (transición de 5 px): el borde suave lo pone el modelo; esta
    máscara solo quita regiones. Una franja semitransparente ancha sobre texto de alto contraste hacía que la
    mezcla en GPU variara según el orden de los cuadros."""
    up = np.repeat(np.repeat(mask.astype(np.float32), H // SH, axis=0), W // SW, axis=1)
    c = np.cumsum(np.pad(up, ((3, 2), (0, 0)), mode="edge"), axis=0)
    up = (c[5:] - c[:-5]) / 5
    c = np.cumsum(np.pad(up, ((0, 0), (3, 2)), mode="edge"), axis=1)
    return np.clip(((c[:, 5:] - c[:, :-5]) / 5 - 0.5) * 4 + 0.5, 0, 1)


def stabilize(src_mp4, raw_webm, out_webm, fps=30, interior=False):
    """Escribe out_webm con la máscara estabilizada. Devuelve info (applied=False si no hacía falta o no se pudo).
    `interior=True` rellena además los huecos pasajeros del cuerpo (cierre en el tiempo, ver `fill_interior`)."""
    rgb = np.stack(list(_rgb(src_mp4, SW, SH)))
    alpha = np.stack(list(_alpha(raw_webm, SW, SH)))
    n = min(len(rgb), len(alpha))
    if n < 6:
        return {"applied": False, "reason": "tramo muy corto"}
    keep, info = decide(rgb[:n], alpha[:n])
    if keep is None:
        if not interior:
            return info
        keep, info = np.ones(alpha[:n].shape, np.uint8), {**info, "applied": True, "removed": 0.0, "filled": 0.0}
    if interior:
        keep = fill_interior(keep, alpha[:n])
        info["interior"] = True
    enc = subprocess.Popen([oslib.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(fps), "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18",
                            "-b:v", "0", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", str(out_webm)],
                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    frame = np.empty((H, W, 4), np.uint8)
    for i, (color, al) in enumerate(zip(_rgb(src_mp4, W, H), _alpha(raw_webm, W, H))):
        if i >= n:
            break
        frame[..., :3] = color
        solid = ((al.astype(np.float32) / 255 - SOLID[0]) / (SOLID[1] - SOLID[0])).clip(0, 1)
        solid = np.maximum(solid, _upsample(keep[i] == 2))
        frame[..., 3] = (solid * _upsample(keep[i] > 0) * 255).round().astype(np.uint8)
        enc.stdin.write(frame.tobytes())
    enc.stdin.close()
    if enc.wait():
        oslib.die(f"no se pudo codificar el recorte estabilizado: {enc.stderr.read().decode()[-400:]}")
    return info
