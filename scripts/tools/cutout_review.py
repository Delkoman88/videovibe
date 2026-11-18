"""Evidence and conservative replacements for cutouts. No approval is inferred.

--prepare generates evidence; inspect it and edit verdict/reason in the report.
--apply-fallbacks applies defective/uncertain verdicts; --dry-run only validates.
An approved storyboard requires --reprocess-approved (explicitly requested work).
"""
import argparse
from copy import deepcopy
import hashlib
import json
import sys
from pathlib import Path
from scripts.core import oslib
from scripts.core.animationanchors import atomic_json, atomic_bytes
from scripts.pipeline import cutout

VERSION = 1


def fingerprint(P, sb, cuts):
    h=hashlib.sha256(json.dumps({'version':VERSION,'storyboard':sb,'model':cutout.MODEL,'matte':cutout.MATTE},sort_keys=True).encode())
    for p in [P/'cut/master-cut.mp4',P/'cut/cut-map.json',*[Path(c['file']) for c in cuts.values()]]:
        h.update(str(p).encode())
        with p.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    h.update(Path(__file__).read_bytes())
    if (P/'hf/index.html').exists():
        from scripts.tools.animation_quality import fingerprint as composition_fingerprint
        h.update(composition_fingerprint(P).encode())
    return h.hexdigest()


def propose(sb, entries):
    result=deepcopy(sb); replacements=[]; keep=[]
    lookup={e['id']:e for e in entries}
    if len(lookup)!=len(entries):raise ValueError('dictámenes duplicados')
    expected={f['id'] for f in sb.get('fx',[]) if f['type'] in cutout.NEEDS_CUTOUT}
    if set(lookup)!=expected:raise ValueError('dictámenes incompletos o desconocidos')
    used={x['id'] for group in ('scenes','overlays','fx') for x in sb.get(group,[])}
    for f in sb.get('fx',[]):
        if f['id'] not in expected:keep.append(f);continue
        entry=lookup[f['id']]; verdict=entry.get('verdict')
        if verdict not in ('usable','defective','uncertain'):raise ValueError('dictamen inválido')
        if not str(entry.get('reason','')).strip():raise ValueError('falta motivo de inspección')
        if verdict=='usable':keep.append(f);continue
        a=f.get('in',f.get('at'));b=f.get('out',a+f.get('duration',1.2))
        text=f.get('label') if f['type']=='freeze-cutout' else f.get('text') if f['type'] in ('text-behind','background-swap') else None
        conflicts=[x for x in result.get('overlays',[]) if x['in']<b and x['out']>a]
        import formats
        conflicts += [x for x in result.get('scenes',[]) if x['in']<b and x['out']>a and (x.get('layout') or formats.REGISTRY[x['format']]['layout'])=='full']
        action='removed'
        if text and not conflicts:
            ident='fallback-'+f['id'];n=1
            while ident in used:ident=f"fallback-{f['id']}-{n}";n+=1
            used.add(ident)
            result.setdefault('overlays',[]).append({'id':ident,'type':'tag' if f['type']=='freeze-cutout' else 'card','in':a,'out':b,'text':text if f['type']=='freeze-cutout' else text.replace('*',''),'role':f.get('role') or 'keyword'})
            action='card' if f['type']!='freeze-cutout' else 'tag'
        replacements.append({'id':f['id'],'original':f,'action':action,'reason':entry['reason'],'conflict':bool(conflicts)})
    result['fx']=keep
    result['overlays']=sorted(result.get('overlays',[]),key=lambda x:x['in'])
    return result,replacements


def prepare(P):
    import contextlib, io, subprocess
    sb=oslib.read_json(P/'storyboard.json'); capture=io.StringIO(); failure=None
    try:
        with contextlib.redirect_stdout(capture):cuts=cutout.ensure(P,sb)
    except (SystemExit, OSError, ValueError) as error:
        cuts={};failure='Recorte no disponible: '+(capture.getvalue() or str(error))[-2000:]
    out=P/'work/cutout-review';out.mkdir(parents=True,exist_ok=True)
    composition_ok=False
    if cuts:
        args=[sys.executable,'-m','scripts.pipeline.compose','--project',str(P)]
        for platform in list(sb.get('platforms',{})) or ['tiktok']:args += ['--platform',platform]
        run=subprocess.run(args,capture_output=True,text=True)
        composition_ok=run.returncode==0
        if not composition_ok:failure='Composición no disponible: '+(run.stderr or run.stdout)[-2000:]
    from scripts.tools.gallery import snapshot
    entries=[]
    for i,f in enumerate(sb.get('fx',[])):
        if f['type'] not in cutout.NEEDS_CUTOUT:continue
        c=cuts.get(f['id']);a=f.get('in',f.get('at'));b=f.get('out',a+f.get('duration',1.2))
        times=[a] if f['type']=='freeze-cutout' else [a+.05,(a+b)/2,b-.05]
        evidence=[];composed=[]
        for j,t in enumerate(times):
            original=out/f'{i}-{j}-original.png';mask=out/f'{i}-{j}-contrast.png'
            oslib.run([oslib.FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(P/'cut/master-cut.mp4'),'-frames:v','1',str(original)])
            evidence.append(str(original))
            if c:
                decoder=['-c:v','libvpx-vp9','-ss',str(max(0,t-c['start']))] if c['kind']=='webm' else []
                oslib.run([oslib.FFMPEG,'-v','error','-y',*decoder,'-i',str(c['file']),'-f','lavfi','-i','color=c=cyan:s=1080x1920','-filter_complex','[1:v][0:v]overlay','-frames:v','1',str(mask)])
                evidence.append(str(mask))
        if composition_ok:
            try:
                with contextlib.redirect_stdout(capture):composed=[str(f) for f in snapshot(P/'hf',times,out/f'composition-{i}').values()]
            except (SystemExit,ValueError,OSError) as error:failure='Captura compuesta no disponible: '+str(error)
            evidence += composed
        entries.append({'id':f['id'],'verdict':'uncertain','reason':failure or 'Inspección visual pendiente','times':times,
                        'segmented':bool(c),'composition_evidence':composed,'evidence':evidence})
    hashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for e in entries for f in e['evidence']}
    report={'evidence_hashes':hashes,'cutouts':{k:{'file':str(v['file'])} for k,v in cuts.items()},
            'version':VERSION,'fingerprint':fingerprint(P,sb,cuts),'effects':entries}
    atomic_json(out/'report.json',report)
    return report


def apply(P, report, dry_run=False, reprocess=False):
    original=(P/'storyboard.json').read_bytes();sb=json.loads(original)
    receipt=P/'work/cutout-review/substitutions.json'
    if receipt.exists():
        done=oslib.read_json(receipt)
        if done.get('source_fingerprint')==report.get('fingerprint') and done.get('storyboard_hash')==hashlib.sha256(original).hexdigest():return {'ok':True,'changed':False}
    if report.get('version')!=VERSION:raise ValueError('versión de informe incompatible')
    if report.get('fingerprint')!=fingerprint(P,sb,report.get('cutouts',{})):raise ValueError('evidencia desactualizada; repite --prepare')
    if set(report.get('evidence_hashes',{}))!={p for e in report['effects'] for p in e.get('evidence',[])}:raise ValueError('faltan huellas de evidencia')
    for file,digest in report.get('evidence_hashes',{}).items():
        if not Path(file).exists() or hashlib.sha256(Path(file).read_bytes()).hexdigest()!=digest:raise ValueError('evidencia modificada')
    for e in report['effects']:
        if e.get('verdict')=='usable' and (not e.get('segmented') or not e.get('composition_evidence')):raise ValueError('usable requiere máscara y composición inspeccionables')
        if not e.get('evidence') or any(not Path(p).is_file() for p in e['evidence']):raise ValueError('falta evidencia')
    proposed,changes=propose(sb,report['effects'])
    if not changes:return {'ok':True,'changed':False}
    status_path=P/'status.json';status_original=status_path.read_bytes() if status_path.exists() else None
    status=json.loads(status_original) if status_original is not None else {}
    if status.get('approvals',{}).get('B') and not reprocess:raise ValueError('pieza aprobada: requiere reproceso solicitado (--reprocess-approved)')
    from scripts.validation.storyboard import context,validate
    errors,warnings=validate(proposed,context(P))
    if errors:raise ValueError('; '.join(errors))
    if not dry_run:
        out=P/'work/cutout-review';out.mkdir(parents=True,exist_ok=True)
        key=hashlib.sha256(original).hexdigest()[:16]
        atomic_bytes(out/f'storyboard-{key}.json',original)
        old=status.get('approvals',{}).pop('B',None)
        if old:status.setdefault('animation_approval_history',[]).append(old)
        status.get('reviews',{}).pop('B',None)
        status['stage']='subtitulos'
        status['pending']='recomponer tras sustitución de efectos'
        status['renders']={}
        status['fingerprints']={k:v for k,v in status.get('fingerprints',{}).items() if k not in ('check','revision','entrega') and not k.startswith('render:')}
        atomic_json(P/'storyboard.json',proposed)
        try:
            atomic_json(status_path,status)
            atomic_json(out/'substitutions.json',{'version':VERSION,'source_fingerprint':report['fingerprint'],'storyboard_hash':hashlib.sha256((P/'storyboard.json').read_bytes()).hexdigest(),'changes':changes})
        except BaseException:
            atomic_bytes(P/'storyboard.json',original)
            if status_original is None:status_path.unlink(missing_ok=True)
            else:atomic_bytes(status_path,status_original)
            raise
    return {'ok':True,'changed':True,'dry_run':dry_run,'changes':changes,'warnings':warnings,'next':'Recomponer y repetir QA; no se registra B'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project',required=True)
    mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--apply-fallbacks',action='store_true')
    ap.add_argument('--report',type=Path);ap.add_argument('--dry-run',action='store_true');ap.add_argument('--reprocess-approved',action='store_true');args=ap.parse_args()
    P=oslib.project_dir(args.project)
    try:
        result=prepare(P) if args.prepare else apply(P,oslib.read_json(args.report or P/'work/cutout-review/report.json'),args.dry_run,args.reprocess_approved)
        oslib.emit(result)
    except (ValueError,KeyError,OSError) as e:oslib.die(str(e))

if __name__=='__main__':main()
