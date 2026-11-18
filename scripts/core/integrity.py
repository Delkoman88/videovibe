"""Huellas por contenido y evidencia de etapas/aprobaciones."""
import hashlib
import json
import os
from pathlib import Path
from scripts.core import oslib


def digest(paths):
    h=hashlib.sha256()
    for p in sorted({Path(p).resolve() for p in paths}):
        h.update(str(p).encode())
        if not p.is_file():h.update(b':missing');continue
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def files(P,*names):
    out=[]
    for name in names:
        p=Path(P)/name
        out.extend(sorted(x for x in p.rglob('*') if x.is_file() and not x.name.startswith('.') and '__pycache__' not in x.parts) if p.is_dir() else [p])
    return out


def inputs(P,stage):
    P=Path(P)
    groups={'ingesta':['raw'],'transcripcion':['raw','media.json'],
            'corte-en-papel':['transcript','media.json'], 'corte-aplicado':['cut/cut-list.json','raw','media.json','transcript'],
            'subtitulos':['cut/cut-map.json','transcript'],
            'composicion':['storyboard.json','captions/captions.json','captions/master.srt','cut/master-cut.mp4','cut/cut-map.json','media.json','raw'],
            'check':['hf/index.html','hf/compositions','hf/assets','hf/variables'],
            'revision':['hf/index.html','hf/compositions','hf/assets','hf/variables'],
            'render':['hf/index.html','hf/compositions','hf/assets','hf/variables'],
            'entrega':['renders','copy','covers','captions/master.srt','brief.md','assets.md']}
    paths=files(P,*groups[stage])
    if stage in ('transcripcion','corte-en-papel','corte-aplicado'):
        paths=[x for x in paths if not x.name.startswith('master-cut')]
    for channel in P.parents:
        if (channel/'channel.json').exists():
            if stage in ('transcripcion','corte-en-papel','corte-aplicado','subtitulos'):
                paths += files(channel,'channel.json','brand.json','vocabulary.txt')
                paths += files(oslib.ROOT,'lang','presets','scripts/core/cutlib.py')
            break
    if stage == 'transcripcion':
        paths += [Path(os.environ.get('VIDEOVIBE_WHISPER_MODEL') or oslib.ROOT/'models/ggml-large-v3-turbo-q5_0.bin'),
                  oslib.ROOT/'models/ggml-silero-v5.1.2.bin']
    if stage == 'transcripcion' and (P/'media.json').exists():
        for item in oslib.read_json(P/'media.json').get('items', []):
            if item.get('audio'):
                paths.append(P/item['audio'])
    metadata=[]
    if stage=='composicion':
        for d in P.parents:
            if (d/'channel.json').exists():
                paths+=files(d,'channel.json','brand.json','fonts')
                sb=oslib.read_json(P/'storyboard.json') if (P/'storyboard.json').exists() else {}
                cfg=oslib.read_json(d/'channel.json')
                music=sb.get('audio',{}).get('music') or {}
                library=d/'audio/music/library.json'
                if music and library.exists():
                    tracks=oslib.read_json(library).get('tracks',[])
                    chosen={music.get('track'),music.get('ads_track')}
                    for track in tracks:
                        if track['id'] in chosen or (not music.get('ads_track') and track.get('ads')):
                            metadata.append(track);paths.append(d/'audio/music'/track['file'])
                kit=d/'audio/sfx/sfx.json'
                if kit.exists() and (sb.get('audio',{}).get('sfx') or sb.get('audio',{}).get('sfx_auto') or sb.get('transitions')):
                    data=oslib.read_json(kit);metadata.append(data)
                    paths += [d/'audio/sfx'/v['file'] for v in data.get('sounds',{}).values()]
                import formats
                from scripts.core import assetlib
                formats.load_packs(cfg.get('format_packs',[]))
                for _,kind,ident in formats.uses(sb):
                    item=assetlib.item(kind,ident,d)
                    metadata.append(item)
                    if item:paths.append(Path(item['path']))
                for scene in sb.get('scenes',[]):
                    if scene.get('params',{}).get('file'):paths.append(P/scene['params']['file'])
                break
        paths+=files(oslib.ROOT,'formats','presets','scripts/composer')
    paths += [oslib.ROOT/'scripts/pipeline'/({'ingesta':'ingest','transcripcion':'transcribe','corte-en-papel':'paper_cut','corte-aplicado':'apply_cut','subtitulos':'captions','composicion':'compose'}.get(stage,stage)+'.py')]
    paths += [Path(__file__),oslib.ROOT/'package-lock.json']
    return hashlib.sha256((digest(paths)+json.dumps(metadata,sort_keys=True)).encode()).hexdigest()


def outputs(P,stage):
    groups={'ingesta':['media.json'],'transcripcion':['transcript'], 'corte-en-papel':['cut/cut-list.json','cut/PAPER-CUT.md'],
            'corte-aplicado':['cut/master-cut.mp4','cut/cut-map.json'], 'subtitulos':['captions/captions.json','captions/master.srt'],
            'composicion':['hf/index.html','hf/compositions','hf/assets','hf/variables'],
            'check':[], 'revision':['snaps'], 'render':['renders'], 'entrega':['copy','covers']}
    paths=files(P,*groups[stage])
    if stage=='entrega':
        from scripts.core.state import load
        destination=load(P).get('delivery')
        if destination:paths+=files(Path(destination),'.')+[Path(destination)/'.videovibe-delivery.json']
    if stage=='revision':paths+=list((Path(P)/'renders').glob('draft-*.mp4'))
    if stage=='transcripcion':paths=[p for p in paths if not p.name.startswith('master-cut')]
    return digest(paths)


def approval_inputs(P,gate):
    P=Path(P)
    if gate=='A':return digest([x for x in files(P,'cut/cut-list.json','raw','transcript','media.json') if not x.name.startswith('master-cut')])
    return hashlib.sha256((inputs(P,'composicion') + outputs(P,'composicion')).encode()).hexdigest()


def valid(P,gate,st):
    from scripts.core.reviewlib import fingerprint
    a=st.get('approvals',{}).get(gate,{})
    return isinstance(a,dict) and a.get('version')==2 and a.get('inputs')==approval_inputs(P,gate) and a.get('presentation')==fingerprint(P,gate)


def verification(P,plats):
    return digest(files(P,'storyboard.json','cut/cut-map.json','captions','copy','covers','assets.md','brief.md')+
                  [Path(P)/'renders'/f'{p}.mp4' for p in plats]+[oslib.ROOT/'presets'/f'{p}.json' for p in plats])


def digest_bytes(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def stable_inputs(P, stage, protect_transcript=False):
    """Entradas externas que no puede producir la propia etapa."""
    if stage == 'subtitulos':
        # La etapa escribe transcript/master-cut.json; controlar sus entradas externas.
        paths = files(P,'cut/master-cut.mp4','cut/cut-map.json')
        if protect_transcript:
            paths += files(P, 'transcript/master-cut.json')
        for channel in Path(P).parents:
            if (channel/'channel.json').exists():
                paths += files(channel,'channel.json','brand.json','vocabulary.txt')
                break
        return digest(paths + files(oslib.ROOT,'lang','scripts/pipeline/captions.py'))
    return inputs(P,stage)
