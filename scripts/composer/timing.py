"""Timing constants shared by rendering and measurement."""
CAPTION_IN = .14
CAPTION_OUT = .08
PANEL_IN = .45
LIQUID_IN = .48
LIQUID_SHAPE = .78
OVERLAY_OUT = .27


def caption_enter(duration, style='classic'):
    if duration <= CAPTION_IN + CAPTION_OUT + .1: return 0.0
    return min(CAPTION_IN, max(.02, duration-CAPTION_OUT)) if style=='neon' else CAPTION_IN


def caption_exit(duration):
    return 0.0 if duration <= CAPTION_IN + CAPTION_OUT + .1 else CAPTION_OUT
