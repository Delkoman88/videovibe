"""Contrato puro del audio de insertos."""
import math
def settings(clip):
    a = clip.get('audio', {})
    if not isinstance(a, dict):
        raise ValueError('audio debe ser un objeto')
    if set(a) - {'enabled', 'gain_db', 'duck_db', 'fade_in', 'fade_out'}:
        raise ValueError('audio contiene claves desconocidas')
    if not isinstance(a.get('enabled', False), bool):
        raise ValueError('audio.enabled debe ser booleano')
    if any(not math.isfinite(clip[k]) for k in ('in', 'out')):
        raise ValueError('audio: tiempos finitos obligatorios')
    d = clip['out'] - clip['in']
    v = {'gain_db': -8, 'duck_db': -12, 'fade_in': .08, 'fade_out': .25, **a}
    for k in ('gain_db', 'duck_db', 'fade_in', 'fade_out'):
        if isinstance(v[k], bool) or not isinstance(v[k], (int, float)) or not math.isfinite(v[k]):
            raise ValueError(f'audio.{k}: número finito obligatorio')
    if not -60 <= v['gain_db'] <= 12 or not -60 <= v['duck_db'] <= 0:
        raise ValueError('audio: gain_db entre -60 y 12; duck_db entre -60 y 0')
    if min(v['fade_in'], v['fade_out']) < 0:
        raise ValueError('audio: fundidos no negativos')
    explicit = sum(v[k] for k in ('fade_in', 'fade_out') if k in a)
    if explicit > d:
        raise ValueError('audio: fundidos explícitos exceden el inserto')
    defaults = [k for k in ('fade_in', 'fade_out') if k not in a]
    weight = sum(v[k] for k in defaults)
    if weight:
        scale = min(1, max(0, d - explicit) / weight)
        for k in defaults:
            v[k] *= scale
    return v

