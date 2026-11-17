"""Zonas temporales para apartar subtítulos de rostros u objetos importantes."""
from .common import _num

POSITIONS = {"upper-left", "upper-center"}


def validate(sb, state):
    zones = sb.get("caption_zones", [])
    if not isinstance(zones, list):
        state.errs.append("caption_zones: debe ser una lista")
        return
    previous_out = 0
    for i, zone in enumerate(zones):
        path = f"caption_zones[{i}]"
        if not isinstance(zone, dict):
            state.errs.append(f"{path}: debe ser un objeto")
            continue
        state.span(path, zone, allow_tail=False)
        if _num(zone.get("in")) and zone["in"] < previous_out - 0.001:
            state.errs.append(f"{path}.in: las zonas deben ir en orden y no solaparse")
        if _num(zone.get("out")):
            previous_out = max(previous_out, zone["out"])
        if zone.get("position") not in POSITIONS:
            state.errs.append(f"{path}.position: usa upper-left o upper-center")
