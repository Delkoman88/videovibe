from scripts.core.state import mutating
from scripts.core.animationanchors import resolve, atomic_json, atomic_bytes
from scripts.core import oslib
import json, difflib
@mutating
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

