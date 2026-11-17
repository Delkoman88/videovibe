#!/usr/bin/env python3
"""Registra imágenes PNG/JPEG/WebP con licencia para objetos de narrative-sequence. Salida JSON."""
import argparse
import re
import shutil
from pathlib import Path
from scripts.core import assetlib, oslib


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['add','list']);ap.add_argument('--channel',required=True)
    ap.add_argument('--file');ap.add_argument('--id');ap.add_argument('--origin');ap.add_argument('--license')
    ap.add_argument('--ads',action='store_true');args=ap.parse_args()
    ch=oslib.load_channel(oslib.channel_path(args.channel))
    if args.action=='list':oslib.emit({'ok':True,'items':list(assetlib.library('images',ch['dir']).values())})
    if not all(isinstance(v,str) and v.strip() for v in (args.file,args.id,args.origin,args.license)):oslib.die('add requiere --file, --id, --origin y --license')
    if not re.fullmatch('[a-z0-9][a-z0-9-]*',args.id):oslib.die('--id: minúsculas, números y guiones')
    src=Path(args.file).expanduser().resolve()
    if src.suffix.lower() not in ('.png','.jpg','.jpeg','.webp') or not src.is_file():oslib.die('archivo PNG, JPEG o WebP obligatorio')
    if src.stat().st_size>25*1024*1024:oslib.die('máximo 25 MB por imagen')
    info=oslib.ffprobe(src)
    if not any(s.get('codec_type')=='video' and s.get('width',0)>0 for s in info['streams']):oslib.die('imagen no decodificable')
    target=ch['dir']/'assets/images'/f'{args.id}{src.suffix.lower()}'
    target.parent.mkdir(parents=True,exist_ok=True)
    if src!=target:shutil.copy2(src,target)
    library=assetlib.save('images',ch['dir'],{'id':args.id,'file':target.name,'origin':args.origin,'license':args.license,'ads':args.ads})
    oslib.emit({'ok':True,'library':str(library),'file':str(target)})

if __name__=='__main__':main()
