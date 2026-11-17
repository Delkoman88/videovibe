"""Compara estilos, selecciona candidatos narrativos y fija perfiles en propuestas explícitas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from datetime import date, datetime
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import formats
from formats.direction import resolve, candidates
from scripts.core import oslib, reviewlib
from scripts.tools import gallery


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--channel',required=True)
    ap.add_argument('--project')
    ap.add_argument('--apply',choices=['restrained','balanced','energetic'])
    ap.add_argument('--snapshot',action='store_true',help='fija el perfil del canal en el storyboard e invalida B')
    ap.add_argument('--intent',choices=['highlight','compare','process','transform','locate','conclude'])
    ap.add_argument('--seconds',type=float,default=5)
    ap.add_argument('--text',default='Una idea clara')
    ap.add_argument('--dry-run', action='store_true', help='muestra y valida la propuesta sin escribir')
    ap.add_argument('--profiles', default='restrained,balanced', help='dos perfiles separados por coma')
    ap.add_argument('--run', help='manifest de comparación que se selecciona')
    ap.add_argument('--plate-start', type=float, default=0)
    ap.add_argument('--no-open',action='store_true')
    args=ap.parse_args()
    ch=oslib.load_channel(oslib.channel_path(args.channel))
    P=oslib.project_dir(args.project) if args.project else None
    if P and oslib.channel_dir(P)!=ch['dir']:oslib.die('la pieza no pertenece al canal')
    out=ROOT/'work'/'animation-style'/ch['id']
    brand_path=ch['dir']/'brand.json'
    brand_hash=hashlib.sha256(brand_path.read_bytes()).hexdigest()
    if args.intent:
        oslib.emit({'ok':True,'candidates':candidates(formats.registry(ch['config'].get('format_packs',[])),args.intent,args.seconds,args.text,channel_dir=ch['dir'],profile=ch['brand'].get('motion',{}).get('profile','balanced'))})
    if args.apply:
        manifest=Path(args.run) if args.run else out/'candidates.json'
        if not manifest.exists():oslib.die('genera y presenta alternativas antes de seleccionar')
        presented=oslib.read_json(manifest)
        if presented['brand_hash']!=brand_hash:oslib.die('la marca cambió: vuelve a generar alternativas')
        if args.apply not in presented['candidates']:oslib.die('esta alternativa no fue presentada')
        if not Path(presented['candidates'][args.apply]).is_file():oslib.die('falta el preview presentado')
        preview=Path(presented['candidates'][args.apply])
        if hashlib.sha256(preview.read_bytes()).hexdigest()!=presented.get('hashes',{}).get(args.apply):
            oslib.die('el preview cambió después de presentarlo; genera alternativas nuevas')
        quality=Path(presented.get('quality_reports',{}).get(args.apply,''))
        if not quality.is_file() or not oslib.read_json(quality).get('ok'):oslib.die('la alternativa necesita control visual válido')
        if hashlib.sha256(quality.read_bytes()).hexdigest()!=presented.get('quality_hashes',{}).get(args.apply):
            oslib.die('el control visual de la alternativa cambió; genera alternativas nuevas')
        if presented.get('profiles',{}).get(args.apply)!=resolve(args.apply):oslib.die('la versión del perfil cambió: genera alternativas nuevas')
        brand=ch['brand'];brand.setdefault('motion',{})['profile']=args.apply
        oslib.write_json(brand_path,brand)
        with (ch['dir']/'learnings.md').open('a') as f:f.write(f'\n- {date.today()}: perfil de movimiento elegido explícitamente: {args.apply}.\n')
        oslib.emit({'ok':True,'profile':args.apply,'scope':'channel','existing_storyboards':'unchanged'})
    if args.snapshot:
        if not P:oslib.die('--snapshot requiere --project')
        profile=ch['brand'].get('motion',{}).get('profile')
        if not profile:oslib.die('selecciona un perfil para el canal primero')
        from scripts.core.animationanchors import snapshot
        try: result = snapshot(P, resolve(profile), dry_run=args.dry_run)
        except ValueError as e: oslib.die(str(e))
        oslib.emit(result)
    if P:
        st=oslib.read_json(P/'status.json')
        if 'A' not in st.get('approvals',{}):oslib.die('aprueba A antes de comparar sobre la toma')
    plate=P/'cut'/'master-cut.mp4' if P else None
    if plate and not plate.is_file():oslib.die('falta el corte aprobado')
    selected=args.profiles.split(',')
    if len(selected)!=2 or len(set(selected))!=2 or any(p not in ('restrained','balanced','energetic') for p in selected):
        oslib.die('--profiles requiere dos perfiles diferentes')
    base=out;out=out/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8])
    previews={};checks={};quality_reports={}
    for profile in selected:
        reg=formats.registry(ch['config'].get('format_packs',[]))
        middle='narrative-sequence' if 'narrative-sequence' in reg else 'agent-flow'
        sb=gallery.gallery_storyboard(['particle-title',middle,'particle-title'],ch['config'].get('format_packs',[]),6)
        for scene in sb['scenes']:
            if scene['format']=='particle-title':scene['params']={'text':args.text,'y':350}
        sb['transitions']=[{'kind':'light-leak','at':6,'duration':.7},{'kind':'scribble','at':12,'duration':.7}]
        hf,sb=gallery.build(args.channel,['particle-title',middle,'particle-title'],6,out=out/profile/'hf',
                            motion=resolve(profile),plate=plate,plate_start=args.plate_start,plate_seconds=18,storyboard=sb)
        # IDs must be unique even when comparing the same format twice.
        r=gallery._hf(['check','--json','--no-cache'],hf)
        try:report=json.loads(r.stdout)
        except ValueError:oslib.die((r.stdout+r.stderr)[-1000:])
        if r.returncode or not report.get('ok'):oslib.die(f'preview {profile}: check falló: {r.stdout[-1000:]}')
        checks[profile]=report
        qa=subprocess.run(['node',str(ROOT/'scripts/tools/animation_quality.mjs'),str(hf),str(hf.parent/'storyboard.json')],capture_output=True,text=True,timeout=600)
        if qa.returncode:oslib.die('control del preview falló: '+qa.stderr[-1000:])
        quality=json.loads(qa.stdout)
        if not quality['ok']:oslib.die('corrige el preview antes de presentarlo: '+json.dumps(quality['issues'],ensure_ascii=False))
        quality_path=hf.parent/'quality.json';oslib.write_json(quality_path,quality);quality_reports[profile]=str(quality_path.resolve())
        video=hf.parent/'preview.mp4'
        r=gallery._hf(['render','-q','draft','--sdr','-o',str(video)],hf)
        if r.returncode or not video.exists():oslib.die(f'preview {profile}: {r.stderr[-1000:]}')
        phone = hf.parent/'phone-preview.mp4'
        result = subprocess.run([oslib.FFMPEG,'-v','error','-y','-i',str(video),'-vf','scale=360:640',
                                 '-c:v','libx264','-crf','20','-c:a','aac',str(phone)],capture_output=True,text=True)
        if result.returncode: oslib.die('preview de teléfono falló: '+result.stderr[-600:])
        previews[profile]=str(phone.resolve())
    opened=reviewlib.open_files(previews.values(),no_open=args.no_open)
    manifest={'quality_reports':quality_reports,'quality_hashes':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in quality_reports.items()},'brand_hash':brand_hash,'candidates':previews,'profiles':{k:resolve(k) for k in selected},
              'source':str(plate) if plate else 'synthetic', 'plate_start':args.plate_start,
              'source_hash':hashlib.sha256(plate.read_bytes()).hexdigest() if plate else None,
              'engine':oslib.read_json(ROOT/'package.json')['version'],
              'hashes':{k:hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in previews.items()}}
    oslib.write_json(out/'candidates.json',manifest)
    oslib.write_json(base/'candidates.json',manifest)
    oslib.emit({'ok':True,'manifest':str(out/'candidates.json'),'candidates':previews,'open_results':opened,'questions':[
        f'¿Prefieres {selected[0]} o {selected[1]}?', '¿La intensidad representa al canal?',
        '¿Se lee cómodamente en el teléfono?', '¿Qué ajustarías antes de guardar este estilo?'],
        'next':'Tras selección explícita: bin/animation-style --channel … --apply <perfil>'})

if __name__=='__main__':main()
