"""Perfiles versionados y metadatos narrativos; no cambian el render legado."""
from copy import deepcopy

PROFILES = {
    'restrained': dict(enter_s=.5, exit_s=.35, amplitude=12, ease='power2.out', stagger_s=.07, density=2),
    'balanced': dict(enter_s=.35, exit_s=.25, amplitude=28, ease='power3.out', stagger_s=.05, density=3),
    'energetic': dict(enter_s=.22, exit_s=.18, amplitude=48, ease='back.out(1.2)', stagger_s=.03, density=4),
}
GROUPS = {
    'highlight': 'kinetic-title particle-title particle-word logo-3d data-reveal signal-spell pixi-signal lottie-accent',
    'compare': 'chart-compare chart-bars molecule-compare health-trio',
    'process': 'agent-flow terminal verify-refs draw-diagram path-journey sketch-diagram lab-network patchbay-dream pixi-mixer',
    'transform': 'morph-icon lottie-scene',
    'locate': 'hud-frame community dna-helix molecule-spin molecule-focus cell-journey model-showcase sketch-annotate',
    'conclude': 'particle-burst space-field sketch-board chart-line',
}


def resolve(name, version=2):
    if name not in PROFILES:
        raise ValueError(f'perfil desconocido: {name}')
    if type(version) is not int or version not in (1, 2):
        raise ValueError('versión de movimiento desconocida')
    result = {'version': version, 'profile': name, **deepcopy(PROFILES[name])}
    if version == 2:
        result.update(internal_ratio={'restrained': 1.25, 'balanced': 1, 'energetic': .8}[name],
                      camera_ratio={'restrained': .45, 'balanced': 1, 'energetic': 1.35}[name],
                      reading_wps=3, minimum_read_s=1)
    return result


def validate(profile):
    if not isinstance(profile, dict) or type(profile.get('version')) is not int or profile.get('version') not in (1, 2):
        return ['motion: perfil resuelto version=1 o 2 obligatorio']
    try:
        expected = resolve(profile.get('profile'), profile['version'])
    except ValueError as e:
        return [str(e)]
    return [] if profile == expected else ['motion: valores distintos del perfil versionado; resuelve de nuevo el perfil']


# Limits are editorial capacities of the implemented layouts, not an unbounded promise.
# (minimum seconds, maximum seconds, characters per primary label, maximum items)
LIMITS = {
    'hud-frame': (2, 12, 32, 1), 'agent-flow': (4, 12, 22, 3),
    'terminal': (4, 15, 48, 4), 'community': (4, 12, 24, 4),
    'verify-refs': (4, 12, 28, 3), 'particle-title': (2, 8, 22, 1),
    'kinetic-title': (2, 8, 28, 1), 'data-reveal': (3, 10, 32, 1),
    'draw-diagram': (4, 15, 24, 5), 'morph-icon': (4, 15, 24, 5),
    'path-journey': (4, 15, 24, 5), 'particle-burst': (2, 8, 22, 1),
    'lab-network': (4, 12, 24, 4), 'dna-helix': (3, 12, 32, 1),
    'health-trio': (4, 12, 24, 3), 'signal-spell': (3, 8, 22, 1),
    'patchbay-dream': (4, 12, 22, 3), 'pixi-signal': (3, 10, 18, 1),
    'pixi-mixer': (4, 12, 18, 3), 'particle-word': (3, 10, 16, 1),
    'logo-3d': (3, 10, 12, 1), 'cell-journey': (4, 15, 32, 1),
    'model-showcase': (4, 15, 32, 1), 'space-field': (4, 15, 28, 1),
    'chart-bars': (5, 15, 22, 8), 'chart-line': (5, 15, 22, 20),
    'chart-compare': (4, 12, 26, 2), 'sketch-annotate': (3, 10, 32, 1),
    'sketch-board': (4, 15, 32, 5), 'sketch-diagram': (4, 15, 24, 5),
    'lottie-scene': (3, 15, 32, 1), 'lottie-accent': (2, 10, 28, 1),
    'molecule-spin': (4, 15, 32, 1), 'molecule-focus': (5, 15, 32, 1),
    'molecule-compare': (5, 15, 28, 2), 'narrative-sequence': (4, 20, 80, 5),
}


def metadata(name, meta):
    intents = [k for k, v in GROUPS.items() if name in v.split()]
    if name == 'narrative-sequence': intents = ['process', 'compare', 'locate']
    lo, hi, chars, items = LIMITS[name]
    controls = ['scene_entrance', 'scene_exit', 'internal_entrance', 'ease', 'amplitude']
    if name in ('particle-title', 'particle-burst', 'signal-spell', 'data-reveal'):
        controls.append('stagger')
    if meta['pack'] == 'cinematic': controls.append('decorative_camera')
    if name.startswith('pixi-'): controls = ['scene_entrance', 'scene_exit', 'decorative_amplitude']
    return {'intents': intents, 'duration_s': [lo, hi], 'max_text_chars': chars,
            'max_items': items, 'layouts': ['full', 'over', 'bubble'],
            'intensity': 'high' if 'three' in meta['needs'] else 'medium',
            'cost': 'high' if set(meta['needs']) & {'three', '3dmol', 'pixi'} else 'low',
            'resources': bool(meta['uses'](meta['example'])) if meta.get('uses') else False, 'motion_controls': controls,
            'adapter': meta['pack'], 'reading': '3 words/s; minimum 1s after development',
            'protected': ['captions', 'platform_safe_zone']}


def candidates(registry, intent, duration, text='', previous=None, available_assets=False,
               profile='balanced', channel_dir=None, ads=False):
    resolve(profile)
    if intent not in GROUPS: raise ValueError('intención desconocida')
    out = []
    from scripts.core import assetlib
    for name, meta in sorted(registry.items()):
        info = metadata(name, meta)
        if intent not in info['intents'] or not info['duration_s'][0] <= duration <= info['duration_s'][1]: continue
        if len(text) > info['max_text_chars']: continue
        resources = meta['uses'](meta['example']) if meta.get('uses') else []
        # A boolean is never proof of a license. Resolve actual catalog entries.
        if resources and (channel_dir is None or any(assetlib.problems(k, i, channel_dir, ads=ads) for k, i in resources)): continue
        out.append({'format': name, 'score': (1 if name == previous else 2) - (1 if profile == 'restrained' and info['intensity'] == 'high' else 0),
                    'reason': f'intención {intent}; {duration:g}s dentro de {info["duration_s"]}; texto dentro de {info["max_text_chars"]} caracteres; recursos verificados', **info})
    return sorted(out, key=lambda x: (-x['score'], x['format']))


def reading_text(params):
    """Only editorial labels, never file paths, sources, IDs or numeric data."""
    keys = {'text', 'title', 'label', 'sublabel', 'caption', 'top', 'bottom', 'center', 'output', 'cmd', 'out'}
    found = []
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in keys and isinstance(item, str): found.append(item)
                elif isinstance(item, (dict, list)): walk(item)
        elif isinstance(value, list):
            for item in value: walk(item)
    walk(params)
    return ' '.join(found)


def budget(scene, motion):
    """Absolute local windows; never accelerates voice or editorial step times."""
    d = round(scene['out'] - scene['in'], 3)
    words = len(reading_text(scene.get('params', {})).split())
    read = max(motion.get('minimum_read_s', 1), words / motion.get('reading_wps', 3))
    entrance, leave = motion['enter_s'], motion['exit_s']
    development = min(1.5, max(.5, d * .2))
    if d < entrance + development + read + leave:
        raise ValueError(f"{scene['id']}: {d:g}s no alcanzan para entrada, desarrollo, lectura ({read:.2f}s) y salida")
    return dict(entrance=[0, entrance], development=[entrance, entrance + development],
                reading=[entrance + development, d - leave], exit=[d - leave, d])
