"""Control local de escenas renderizadas y advertencias narrativas. Salida JSON."""

from scripts.core.quality_fingerprint import fingerprint
import hashlib
import argparse
import json
import subprocess
from pathlib import Path
from scripts.core import oslib
from scripts.core.animationqa import inspect
import formats




def check(P):
    initial_fingerprint=fingerprint(P)
    sb=oslib.read_json(P/'storyboard.json');ch=oslib.load_channel(P)
    structural=inspect(sb,formats.registry(ch['config'].get('format_packs',[])))
    cmap = P/'cut/cut-map.json'
    caps = P/'captions/captions.json'
    safes = [oslib.load_preset(p).get('safe_zone_px', {}) for p in sb.get('platforms', {})]
    options = {'duration': oslib.read_json(cmap)['duration_s'] + sb.get('tail_s',0) if cmap.exists() else max((s['out'] for s in sb.get('scenes',[])), default=0),
               'groups': oslib.read_json(caps).get('groups',[]) if caps.exists() else [],
               'safe': {k:max(s.get(k,0) for s in safes) for k in ('left','right','top','bottom')} if safes else None}
    options_file=P/'work/animation-quality-options.json';oslib.write_json(options_file,options)
    try:
        r=__import__('scripts.core.state', fromlist=['run']).run(['node',str(oslib.ROOT/'scripts/tools/animation_quality.mjs'),str(P/'hf'),str(P/'storyboard.json'),str(options_file)],capture_output=True,text=True,timeout=1800)
    except (subprocess.TimeoutExpired, OSError) as e:
        raise ValueError(f'medición visual no disponible: {e}') from e
    if r.returncode:raise ValueError('medición visual no completada: '+r.stderr[-1000:])
    if fingerprint(P)!=initial_fingerprint: raise ValueError('la composición cambió durante la medición: repite el control')
    report=json.loads(r.stdout);report['fingerprint']=initial_fingerprint;report['issues']=structural['issues']+report['issues']
    report['ok']=structural['ok'] and report['ok']
    timed=[]
    for frame in report.get('frames',[]):
        try: timed.append((float(Path(frame).stem.removeprefix('at-')),frame))
        except ValueError: pass
    report['review_frames']=list(dict.fromkeys(min(timed,key=lambda x:abs(x[0]-(s['in']+s['out'])/2))[1]
                                               for s in sb.get('scenes',[])[:3])) if timed else []
    oslib.write_json(P/'work'/'animation-quality.json',report)
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project',required=True);args=ap.parse_args()
    try:report=check(oslib.project_dir(args.project))
    except (ValueError,subprocess.TimeoutExpired) as e:oslib.die(str(e))
    oslib.emit(report,0 if report['ok'] else 1)

if __name__=='__main__':main()
