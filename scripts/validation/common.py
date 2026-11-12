from dataclasses import dataclass, field

ROOT_KEYS = {"version", "video", "tail_s", "camera", "emphasis", "overlays", "scenes", "platforms", "grading",
             "audio", "voice", "broll"}
OVERLAY_TYPES = {"title", "card", "tag", "cta"}
LAYOUTS = {"full", "over", "bubble"}
MOVE_TYPES = {"punch", "creep"}
ADS_VALUES = {"si", "no", "quiza"}
VOICE_KEYS = {"enabled", "strength", "denoise", "eq", "deess", "compress"}
STRENGTHS = {"natural", "fuerte"}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


@dataclass
class State:
    ctx: dict
    dur: object
    end: object
    errs: list = field(default_factory=list)
    warns: list = field(default_factory=list)
    ids: set = field(default_factory=set)
    ads_plats: list = field(default_factory=list)

    def span(self, path, item, allow_tail=True):
        a, b = item.get("in"), item.get("out")
        if not _num(a) or not _num(b):
            self.errs.append(f"{path}: «in» y «out» son obligatorios (segundos)")
            return
        if a < 0:
            self.errs.append(f"{path}.in: {a} es negativo")
        if b <= a:
            self.errs.append(f"{path}.out: {b} debe ser mayor que in ({a})")
        lim = self.end if allow_tail else self.dur
        if lim is not None and b > lim + 0.05:
            self.errs.append(f"{path}.out: {b} pasa del final del video ({lim:.2f} s)")

    def sound(self, path, name):
        if self.ctx.get("kit") and name not in self.ctx["kit"]:
            self.errs.append(f"{path}: el efecto «{name}» no está en el kit del canal "
                        f"(scripts/audio/sfx.py --channel … --list)")

