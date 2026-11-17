"""Rendered boundary cases with two public brands, all composition layers, and expected QA failures."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from scripts.core import oslib
from scripts.tools import gallery
from formats.direction import resolve


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='work/animation-scenarios');args=ap.parse_args()
    root=Path(args.out).resolve();root.mkdir(parents=True,exist_ok=True)
    # A synthetic plate and freeze frame exercise layers without anyone's face or private material.
    plate=root/'synthetic.mp4';gallery.prepare_plate(None,plate,8)
    frame=root/'synthetic.png'
    oslib.run([oslib.FFMPEG,'-v','error','-y','-i',str(plate),'-frames:v','1',str(frame)])
    results=[]
    for channel in ('science-60','_template'):
        sb={'scenes':[{'id':'title','format':'particle-title','in':0,'out':4,'params':{'text':'Ácido y ADN','y':330}}],
            'overlays':[{'id':'card','type':'card','in':4.1,'out':7.9,'text':'Una idea clara','role':'keyword'}],
            'fx':[{'id':'freeze','type':'freeze-cutout','at':5,'duration':1.2,'label':'Prueba sintética','label_y':800}],
            'beat_fx':[{'in':0,'out':4,'fx':'pulse','strength':.2,'every':'beat'}],
            'transitions':[{'kind':'scribble','at':4,'duration':.6}]}
        # Last scene establishes duration; transparent title shares captions below.
        sb['scenes'].append({'id':'end','format':'particle-title','in':4,'out':8,'params':{'text':'Reproducible','y':580}})
        caps={'words':[{'id':'w1','w':'Subtítulos','start':1,'end':7.5}],
              'groups':[{'id':'g1','in':1,'out':7.5,'words':['w1']}]}
        out=root/channel;hf,_=gallery.build(channel,['particle-title'],8,out=out/'hf',motion=resolve('balanced'),
                   plate=plate,storyboard=sb,captions=caps,fx_cuts={'freeze':{'file':frame,'frame':frame,'kind':'png'}},
                   beat_data={'beats':[1,2,3],'downbeats':[1],'bpm':60})
        options=out/'options.json';oslib.write_json(options,{'times':[.2,2,3.8,4.1,5.6,6.8,7.8],'duration':8})
        def measure():
            r=subprocess.run(['node',str(oslib.ROOT/'scripts/tools/animation_quality.mjs'),str(hf),str(out/'storyboard.json'),str(options)],capture_output=True,text=True,timeout=300)
            if r.returncode: raise ValueError(r.stderr[-1500:])
            return json.loads(r.stdout)
        good=measure();oslib.write_json(out/'quality.json',good)
        # Text clipping must fail rather than be silently cropped in a delivered preview.
        index=hf/'index.html';source=index.read_text()
        index.write_text(source.replace('</body>','<div style="position:absolute;top:600px;left:1000px;width:50px;overflow:hidden;font-size:64px">Texto excesivamente largo</div></body>'))
        clipped=measure();index.write_text(source)
        # A missing font must fail closed, not render a fallback and claim success.
        font=next((hf/'assets/fonts').iterdir());saved=font.read_bytes();font.unlink()
        font_failed=False
        try:measure()
        except ValueError:font_failed=True
        finally:font.write_bytes(saved)
        results.append({'channel':channel,'composition_ok':good['ok'],'clipping_rejected':not clipped['ok'],
                        'missing_font_rejected':font_failed,'issues':good['issues']})
    report={'ok':all(r['composition_ok'] and r['clipping_rejected'] and r['missing_font_rejected'] for r in results),'cases':results}
    oslib.write_json(root/'report.json',report);oslib.emit(report,0 if report['ok'] else 1)

if __name__=='__main__':main()
