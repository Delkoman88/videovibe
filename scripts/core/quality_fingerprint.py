import hashlib
from pathlib import Path
from scripts.core import oslib
def fingerprint(P):
    h=hashlib.sha256()
    files = [oslib.ROOT/'scripts/composer/timing.py', oslib.ROOT/'scripts/composer/reading.py', oslib.ROOT/'formats/text.py', P/'hf/reading-windows.json', P/'storyboard.json', P/'hf/index.html', P/'hf/hyperframes.json',
             *sorted((P/'hf/assets').rglob('*')), *sorted((P/'hf/compositions').rglob('*')),
             *sorted((P/'hf/variables').rglob('*')),
             *sorted((oslib.ROOT/'presets').glob('*.json')),
             oslib.ROOT/'scripts/tools/animation_quality.py', oslib.ROOT/'scripts/tools/animation_quality.mjs',
             oslib.ROOT/'package-lock.json', oslib.ROOT/'scripts/core/animationqa.py']
    for p in files:
        if not p.is_file() or (p.is_relative_to(P/'hf') and 'quality' in p.relative_to(P/'hf').parts):
            continue
        if p.suffix in ('.mp4', '.wav', '.png', '.jpg') and 'assets' not in p.parts: continue
        h.update(str(p.relative_to(P) if p.is_relative_to(P) else p.relative_to(oslib.ROOT)).encode())
        with p.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

