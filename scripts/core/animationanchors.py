"""One resolver for scene/step anchors and transactional storyboard updates."""
from copy import deepcopy
import difflib
import json
import math
import os
from pathlib import Path
import tempfile
from scripts.core import oslib


def resolve(sb, words):
    result = deepcopy(sb)
    lookup = {w['id']: w for w in words}
    def time(anchor):
        if not isinstance(anchor, dict) or anchor.get('word_id') not in lookup:
            raise ValueError('anchor.word_id: palabra ausente del corte aprobado')
        offset = anchor.get('offset', 0)
        if not isinstance(offset, (int, float)) or isinstance(offset, bool) or not math.isfinite(offset):
            raise ValueError('anchor.offset: número finito obligatorio')
        w = lookup[anchor['word_id']]
        return round(w.get('start', w.get('t')) + offset, 3)
    for scene in result.get('scenes', []):
        if scene.get('anchor'):
            duration = scene['out'] - scene['in']
            scene['in'] = time(scene['anchor'])
            scene['out'] = round(scene['in'] + duration, 3)
        if scene.get('format') == 'narrative-sequence':
            for step in scene['params']['steps']:
                if step.get('anchor'): step['at'] = round(time(step['anchor']) - scene['in'], 3)
    return result


def atomic_bytes(path, payload):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        f.write(payload); f.flush(); os.fsync(f.fileno())
    try: os.replace(tmp, path)
    finally: tmp.unlink(missing_ok=True)


def atomic_json(path, data):
    atomic_bytes(path, (json.dumps(data, indent=2, ensure_ascii=False)+'\n').encode())


def snapshot(P, motion, dry_run=False):
    from scripts.validation.storyboard import context, validate
    original_bytes = (P/'storyboard.json').read_bytes()
    source = json.loads(original_bytes)
    caps = P/'captions/captions.json'
    proposed = resolve(source, oslib.read_json(caps)['words'] if caps.exists() else [])
    proposed['motion'] = motion
    errors, warnings = validate(proposed, context(P))
    if errors: raise ValueError('; '.join(errors))
    diff = ''.join(difflib.unified_diff(json.dumps(source,indent=2,ensure_ascii=False).splitlines(True),
                                      json.dumps(proposed,indent=2,ensure_ascii=False).splitlines(True),
                                      fromfile='storyboard actual', tofile='storyboard propuesto'))
    if diff:
        import sys
        print(diff, file=sys.stderr)
    if diff and not dry_run:
        status_path = P/'status.json'
        status = oslib.read_json(status_path) if status_path.exists() else {}
        old = status.get('approvals', {}).pop('B', None)
        if old: status.setdefault('animation_approval_history', []).append(old)
        status.get('reviews', {}).pop('B', None)
        status['fingerprints'] = {k:v for k,v in status.get('fingerprints',{}).items()
                                  if k not in ('check','revision','entrega') and not k.startswith('render:')}
        # On disk the storyboard changes atomically first; gates also bind the current fingerprint.
        # If status cannot be saved, restore the original storyboard and report the failure.
        atomic_json(P/'storyboard.json', proposed)
        try: atomic_json(status_path, status)
        except BaseException:
            atomic_bytes(P/'storyboard.json', original_bytes)
            raise
    return {'ok': True, 'diff': diff, 'changed': bool(diff), 'dry_run': dry_run,
            'warnings': warnings, 'motion': motion, 'next': 'bin/edit para recomponer y presentar B'}
