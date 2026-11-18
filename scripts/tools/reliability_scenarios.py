"""Rendered public regression: intentional reveals vs persistent clipping."""
import argparse,json,re,subprocess
from pathlib import Path
from formats.direction import resolve
from scripts.core import oslib
from scripts.tools import gallery


def run(channel,out):
    sb={'scenes':[{'id':'end','format':'particle-title','in':20,'out':24,'params':{'text':'Listo','y':600}}],
        'overlays':[{'id':v,'type':'title','in':i*5,'out':i*5+4.8,'text':'Una idea clara','text_fx':v} for i,v in enumerate(('rise','wave','blur','mask'))]}
    hf,_=gallery.build(channel,['particle-title'],out=out/'hf',motion=resolve('balanced'),storyboard=sb,captions={'words':[{'id':'short-word','w':'Sí','start':2,'end':2.18}], 'groups':[{'id':'short-caption','in':2,'out':2.18,'words':['short-word']}]})
    def measure(name,options=None):
        cmd=['node',str(oslib.ROOT/'scripts/tools/animation_quality.mjs'),str(hf),str(out/'storyboard.json')]
        if options is not None:
            options_file=out/f'{name}-options.json';oslib.write_json(options_file,options);cmd.append(str(options_file))
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
        if result.returncode:raise ValueError(result.stderr)
        data=json.loads(result.stdout);oslib.write_json(out/f'{name}.json',data);return data
    good=measure('reveals')
    # Deliberately narrow synthetic safe zone: the same title crosses it during entry and reading.
    safe=measure('safe-zone',{'times':[.25,2,5.25,7],'duration':24,'safe':{'left':100,'right':540,'top':180,'bottom':300}})
    safe_levels={(i['phase'],i['level']) for i in safe['issues'] if i['code']=='safe_zone'}
    safe_ok={('enter','info'),('reading','warning')}<=safe_levels and safe['ok']
    index=hf/'index.html';original=index.read_text()
    scene=hf/'compositions/scene-end.html';scene_original=scene.read_text()
    try:
        index.write_text(original.replace('</body>','<div style="position:absolute;left:100px;top:950px;width:35px;overflow:hidden;font-size:64px"><span id="persistent-unowned">Texto recortado permanente</span></div></body>'))
        scene.write_text(re.sub(r'(<div id="root"[^>]*>)',r'\1<div class="kw" style="position:absolute;left:100px;top:950px;width:35px;overflow:hidden;font-size:64px"><span id="persistent-known-mask">Texto recortado permanente</span></div>',scene_original,count=1))
        bad=measure('persistent-clip')
    finally:
        index.write_text(original);scene.write_text(scene_original)
    rejected={i['path'] for i in bad['issues'] if i['code']=='container_clip' and i['level']=='error' and i.get('phase')=='reading'}
    negative_ok={'persistent-unowned','persistent-known-mask'}<=rejected
    report={'ok':good['ok'] and negative_ok and safe_ok,'reveals_ok':good['ok'],'persistent_clip_rejected':negative_ok,'safe_zone_phases_ok':safe_ok,'issues':good['issues']}
    oslib.write_json(out/'report.json',report);return report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--channel',default='science-60');ap.add_argument('--out',type=Path,default=Path('work/reliability-scenarios'));args=ap.parse_args()
    result=run(args.channel,args.out.resolve());oslib.emit(result,0 if result['ok'] else 1)

if __name__=='__main__':main()
