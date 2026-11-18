"""Selección pura de golpes."""
EVERY = {"beat": 1, "half": 2, "bar": 4, "2bars": 8}
def pick(beats_data, a, b, every):
    """Golpes del tramo [a, b) según `every` (beat, half, bar, 2bars)."""
    if every in ("bar", "2bars"):
        src, step = beats_data["downbeats"], 1 if every == "bar" else 2
    else:
        src, step = beats_data["beats"], EVERY[every]
    inside = [t for t in src if a <= t < b]
    return inside[::step]

