"""Reproducible rendered profile matrix, resumable by source/config hash. No human approval implied."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
import formats
from formats.direction import resolve
from scripts.core import oslib
from scripts.tools import gallery


def digest(files):
    h=hashlib.sha256()
    for file in sorted(files):
        if file.is_file():h.update(str(file).encode());h.update(file.read_bytes())
    return h.hexdigest()


def run(channel='science-60', profiles=('restrained','balanced','energetic'), names=None, seconds=8):
    ch=oslib.load_channel(oslib.channel_path(channel));reg=formats.registry(formats.available_packs())
    names=names or sorted(reg)
    sources=[*oslib.ROOT.glob('formats/**/*.py'),*oslib.ROOT.glob('formats/**/*.js'),
             *oslib.ROOT.glob('scripts/composer/*.py'),Path(__file__),Path(__file__).with_name('animation_quality.mjs'),Path(gallery.__file__),
             oslib.font_file(ch,'display'),oslib.font_file(ch,'mono'),
             ch['dir']/'brand.json',ch['dir']/'channel.json',oslib.ROOT/'package-lock.json',
             *oslib.ROOT.glob('assets/**/*'),*oslib.ROOT.glob('formats/icons/*.json'),*ch['dir'].glob('assets/**/*')]
    source_hash=digest(sources)
    key=hashlib.sha256(json.dumps([source_hash,channel,names,seconds],sort_keys=True).encode()).hexdigest()[:20]
    root=oslib.ROOT/'work/animation-matrix'/key;root.mkdir(parents=True,exist_ok=True)
    reports=[]
    for profile in profiles:
        out=root/profile;cache=out/'result.json'
        if cache.exists():
            old=oslib.read_json(cache)
            if old.get('ok') and all(Path(f).is_file() and digest([Path(f)])==h for f,h in old.get('artifacts',{}).items()):
                reports.append(old);continue
        start=time.monotonic();out.mkdir(exist_ok=True)
        hf,sb=gallery.build(channel,names,seconds,out=out/'hf',motion=resolve(profile),packs_override=formats.available_packs())
        report={'profile':profile,'source_hash':source_hash,'ok':False,'cells':[]}
        try:
            check=gallery._hf(['check','--json','--no-cache'],hf,timeout=1800)
            (out/'check.json').write_text(check.stdout or check.stderr)
            check_json=json.loads(check.stdout)
            report['check_ok']=check.returncode==0 and check_json.get('ok',False)
            times=[round(s['in']+offset,3) for s in sb['scenes'] for offset in (.1,2,seconds*.7,seconds-.1)]
            options=out/'options.json';oslib.write_json(options,{'times':times,'duration':seconds*len(names)})
            cmd=['node',str(oslib.ROOT/'scripts/tools/animation_quality.mjs'),str(hf),str(out/'storyboard.json'),str(options)]
            qa=__import__('scripts.core.state', fromlist=['run']).run(cmd,capture_output=True,text=True,timeout=3600)
            if qa.returncode:raise ValueError(qa.stderr[-2500:])
            forward=json.loads(qa.stdout);oslib.write_json(out/'quality.json',forward)
            forward_dir=out/'forward';shutil.rmtree(forward_dir,ignore_errors=True);shutil.copytree(hf/'quality',forward_dir)
            oslib.write_json(options,{'times':list(reversed(times)),'duration':seconds*len(names)})
            reverse=__import__('scripts.core.state', fromlist=['run']).run(cmd,capture_output=True,text=True,timeout=3600)
            if reverse.returncode:raise ValueError(reverse.stderr[-2500:])
            json.loads(reverse.stdout)
            for scene in sb['scenes']:
                differences=[];shots=[]
                for t in [t for t in times if scene['in']<=t<scene['out']]:
                    a=forward_dir/f'at-{t:.3f}.png';b=hf/'quality'/a.name
                    if not a.is_file() or not b.is_file():differences.append({'time':t,'missing':True});continue
                    shots.append(str(a))
                    if a.read_bytes()!=b.read_bytes():
                        peak,fraction=gallery.pixel_diff(a,b)
                        if fraction>1e-4:differences.append({'time':t,'peak':peak,'fraction':fraction})
                issues=[i for i in forward['issues'] if scene['in']<=i['time']<scene['out']]
                report['cells'].append({'format':scene['format'],'profile':profile,'frames':shots,
                    'ok':not differences and not any(i['level']=='error' for i in issues),
                    'determinism':{'ok':not differences,'differences':differences},'issues':issues})
            report['ok']=report['check_ok'] and all(c['ok'] for c in report['cells'])
        except (ValueError,subprocess.TimeoutExpired) as e:report['error']=str(e)
        report['elapsed_s']=round(time.monotonic()-start,2)
        artifacts=[hf/'reading-windows.json',out/'check.json',out/'quality.json',out/'storyboard.json',hf/'index.html',
                   *out.glob('forward/*.png'),*hf.glob('quality/*.png'),
                   *hf.glob('compositions/*.html'),*hf.glob('assets/**/*')]
        report['artifacts']={str(f):digest([f]) for f in artifacts if f.is_file()}
        oslib.write_json(cache,report);reports.append(report)
        print(json.dumps({'profile':profile,'ok':report['ok'],'seconds':report['elapsed_s'],'report':str(cache)}),flush=True)
    result={'ok':all(r['ok'] for r in reports),'source_hash':source_hash,'root':str(root),
            'cells':sum(len(r['cells']) for r in reports),'profiles':reports,'human_review':'pending'}
    oslib.write_json(root/'matrix.json',result)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--channel',default='science-60');ap.add_argument('--profiles',default='restrained,balanced,energetic')
    ap.add_argument('--formats');ap.add_argument('--seconds',type=float,default=8)
    args=ap.parse_args();r=run(args.channel,args.profiles.split(','),args.formats.split(',') if args.formats else None,args.seconds)
    oslib.emit({'ok':r['ok'],'cells':r['cells'],'report':str(Path(r['root'])/'matrix.json')},0 if r['ok'] else 1)

if __name__=='__main__':main()
