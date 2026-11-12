"""Migración de nombres administrados por VideoVibe, con diario reversible."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib

NAMES = {'estilo.md':'style.md', 'ritmo.md':'rhythm.md', 'temas.md':'topics.md',
         'aprendizajes.md':'learnings.md', 'vocabulario.txt':'vocabulary.txt',
         'LEEME.md':'README.md', 'subtitulos.srt':'subtitles.srt',
         '.videovibe-entrega.json':'.videovibe-delivery.json'}
REFERENCES = json.loads(Path(__file__).with_name('layout_paths.json').read_text())
TEXT = {'.json', '.md', '.html', '.js', '.css', '.txt', '.srt'}
SKIP = {'raw', 'node_modules', '.git', '__pycache__', 'work'}


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def atomic(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd, 'wb') as f: f.write(data)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def renamed(name):
    name = NAMES.get(name, name)
    name = name.replace(' - portada.jpg', ' - cover.jpg').replace(' - texto.md', ' - copy.md')
    if name.startswith('borrador-'): name = 'draft-' + name[9:]
    if name.startswith('anuncio.'): name = 'ads.' + name.split('.',1)[1]
    if name.startswith('anuncio - '): name = 'ads' + name[7:]
    if name.startswith('draft-anuncio.'): name = name.replace('draft-anuncio.', 'draft-ads.',1)
    return name


def plan(roots):
    ops = []
    for root, target in roots:
        root, target = Path(root), Path(target)
        if not root.exists(): continue
        for parent, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
            for name in sorted(files):
                if name.startswith('.') and name != '.videovibe-entrega.json': continue
                src = Path(parent)/name
                if src.is_symlink():
                    if root != target or renamed(name) != name:
                        raise ValueError(f'Enlace requiere revisión antes de migrar: {src}')
                    continue
                rel = src.relative_to(root)
                originals = target.name == 'input'
                dst = target / rel.parent / (name if originals else renamed(name))
                data = src.read_bytes() if src.suffix in TEXT else None
                changed = data
                if not originals and data is not None and (name in NAMES or name in {'CHANNEL.md', 'channel.json', 'brand.json', 'storyboard.json', 'status.json', 'assets.md', 'README.md', '.videovibe-delivery.json'} or any(part in rel.parts for part in ('hf', 'copy'))):
                    try: text = data.decode('utf-8')
                    except UnicodeDecodeError: continue
                    # Only file/path references, never arbitrary editorial words.
                    for old,new in sorted(REFERENCES.items(),key=lambda pair:-len(pair[0])):
                        text = text.replace(old,new)
                    for old,new in NAMES.items(): text = text.replace(old,new)
                    text = text.replace(' - portada.jpg',' - cover.jpg').replace(' - texto.md',' - copy.md')
                    text = text.replace('borrador-','draft-')
                    text = text.replace('anuncio.', 'ads.').replace('draft-anuncio.', 'draft-ads.').replace('anuncio - ', 'ads - ')
                    for a,b in roots:
                        if str(a)!=str(b): text=text.replace(str(a),str(b))
                    if src.suffix=='.json':
                        obj=json.loads(text)
                        def visit(x, key=''):
                            if isinstance(x,dict):
                                return {('ads' if k=='anuncio' else 'render:ads' if k=='render:anuncio' else k):visit(v,k) for k,v in x.items()}
                            if isinstance(x,list): return [visit(v,key) for v in x]
                            if x=='anuncio' and key in ('platform','platforms'): return 'ads'
                            return x
                        new=visit(obj)
                        if new!=obj: text=json.dumps(new,ensure_ascii=False,indent=2)+'\n'
                        # Preserve audit evidence; never fabricate a new approval.
                        if name=='status.json' and (src.parent/'storyboard.json').exists():
                            sb=(src.parent/'storyboard.json').read_text()
                            if '"anuncio"' in sb:
                                obj=json.loads(text)
                                approval=obj.get('approvals',{}).pop('B',None)
                                if approval is not None:
                                    obj.setdefault('migration_approvals',[]).append({'gate':'B','approval':approval,'reason':'platform renamed to ads'})
                                obj.get('reviews',{}).pop('B',None)
                                text=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
                    changed=text.encode()
                if src==dst and changed==data: continue
                if dst!=src and (dst.exists() or dst.is_symlink()):
                    raise ValueError(f'Destino existente: {dst}')
                ops.append({'src':str(src),'dst':str(dst),'before':digest(src),
                            'text':changed.decode() if changed is not None and changed!=data else None})
    destinations=[o['dst'] for o in ops]
    if len(set(destinations))!=len(destinations): raise ValueError('Destinos duplicados')
    return ops


def apply(ops, backup):
    backup=Path(backup); backup.mkdir(parents=True,exist_ok=False)
    manifest=backup/'manifest.json'
    journal={'version':1,'operations':ops}
    # Back up all changed text before any mutation; media is renamed, never rewritten.
    for i,o in enumerate(ops):
        if digest(Path(o['src']))!=o['before']: raise ValueError('Archivo cambió desde el inventario')
        if o['text'] is not None:
            saved=backup/f'{i}.original'; shutil.copy2(o['src'],saved); o['backup']=str(saved)
    atomic(manifest,json.dumps(journal,ensure_ascii=False,indent=2).encode())
    for o in ops:
        src,dst=Path(o['src']),Path(o['dst'])
        if src!=dst:
            dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists(): raise ValueError(f'Destino existente: {dst}')
            src.rename(dst)
        if o['text'] is not None: atomic(dst,o['text'].encode())
        o['after']=digest(dst)
        if o['text'] is None and o['after']!=o['before']: raise ValueError('Integridad de archivo incorrecta')
        o['done']=True
        atomic(manifest,json.dumps(journal,ensure_ascii=False,indent=2).encode())
    return manifest


def rollback(manifest):
    manifest=Path(manifest); journal=json.loads(manifest.read_text())
    for o in reversed(journal['operations']):
        src,dst=Path(o['src']),Path(o['dst'])
        if o.get('rolled_back'): continue
        if src!=dst and not dst.exists(): continue
        p=dst
        if not p.exists(): raise ValueError(f'Archivo ausente: {p}')
        expected=o.get('after')
        allowed={o['before']}
        if o['text'] is not None: allowed.add(hashlib.sha256(o['text'].encode()).hexdigest())
        if digest(p) not in (allowed|({expected} if expected else set())):
            raise ValueError(f'Archivo modificado después de migrar: {p}')
        if src!=dst and src.exists(): raise ValueError(f'Conflicto al restaurar: {src}')
        if o.get('backup'): atomic(p,Path(o['backup']).read_bytes())
        if src!=dst: p.rename(src)
        if digest(src)!=o['before']: raise ValueError('Restauración incorrecta')
        o['rolled_back']=True
        atomic(manifest,json.dumps(journal,ensure_ascii=False,indent=2).encode())


def resume(manifest):
    manifest = Path(manifest)
    journal = json.loads(manifest.read_text())
    for o in journal['operations']:
        if o.get('rolled_back'):
            raise ValueError('El diario ya fue revertido; crea un plan nuevo')
        src, dst = Path(o['src']), Path(o['dst'])
        if o.get('done'):
            if not dst.exists() or digest(dst) != o['after']:
                raise ValueError(f'Archivo modificado después de migrar: {dst}')
            continue
        expected = hashlib.sha256(o['text'].encode()).hexdigest() if o['text'] is not None else o['before']
        if src != dst and src.exists():
            if dst.exists() or digest(src) != o['before']:
                raise ValueError(f'Conflicto al reanudar: {src}')
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        if not dst.exists() or digest(dst) not in {o['before'], expected}:
            raise ValueError(f'Archivo inesperado: {dst}')
        if o['text'] is not None:
            atomic(dst, o['text'].encode())
        o['after'], o['done'] = digest(dst), True
        atomic(manifest, json.dumps(journal, ensure_ascii=False, indent=2).encode())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true'); ap.add_argument('--rollback')
    ap.add_argument('--resume')
    ap.add_argument('--json',action='store_true'); ap.add_argument('--channels-dir')
    ap.add_argument('--backup-dir')
    a=ap.parse_args()
    try:
        if a.resume:
            resume(a.resume); result={'ok':True,'manifest':a.resume}
        elif a.rollback:
            rollback(a.rollback); result={'ok':True,'restored':a.rollback}
        else:
            roots=[(Path(a.channels_dir).expanduser() if a.channels_dir else oslib.CHANNELS,)*2]
            if not a.channels_dir:
                roots += [(ROOT/'material',ROOT/'input'),(ROOT/'entregas',ROOT/'deliveries')]
                if oslib.DELIVERIES not in (ROOT/'entregas', ROOT/'deliveries'):
                    roots.append((oslib.DELIVERIES, oslib.DELIVERIES))
                # README files were already renamed by the source migration.
                roots=[(x,y) for x,y in roots if x.exists()]
            ops=plan(roots)
            local=ROOT/'local.json'
            if not a.channels_dir and local.exists():
                cfg=json.loads(local.read_text()); updated=dict(cfg)
                for key,old,new in [('material_dir','material','input'),('deliveries_dir','entregas','deliveries')]:
                    if key in cfg:
                        value=Path(cfg[key]).expanduser()
                        absolute=value if value.is_absolute() else ROOT/value
                        if absolute.resolve()==(ROOT/old).resolve():
                            updated[key]=str(ROOT/new) if value.is_absolute() else new
                if updated!=cfg:
                    ops.append({'src':str(local),'dst':str(local),'before':digest(local),
                                'text':json.dumps(updated,ensure_ascii=False,indent=2)+'\n'})
            result={'ok':True,'operations':[{k:v for k,v in o.items() if k!='text'} for o in ops]}
            if a.apply and ops:
                backup=Path(a.backup_dir).expanduser() if a.backup_dir else Path.home()/'.videovibe-backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
                result['manifest']=str(apply(ops,backup))
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False)); sys.exit(2)

if __name__=='__main__': main()
