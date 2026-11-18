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
    if Path(path).name == 'status.json':
        from scripts.core.state import save
        save(Path(path).parent,data)
        return
    atomic_bytes(path, (json.dumps(data, indent=2, ensure_ascii=False)+'\n').encode())
