"""Desacopla enlaces duros de entregas sin cambiar rutas ni bytes. Simulación por defecto.
Uso: python -m scripts.tools.migrate_deliveries --directory RUTA [--apply]
El diario .detach-journal.json permite reanudar repitiendo el comando.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path
from scripts.core import state, integrity


def migrate(directory,apply=False):
    root=Path(directory).resolve();journal=root/'.detach-journal.json'
    with state.lock(root):
        records=json.loads(journal.read_text()) if journal.exists() else {}
        pending=[]
        for f in sorted(root.rglob('*')):
            if 'work' in f.relative_to(root).parts or f==journal:continue
            if f.is_symlink():raise ValueError(f'enlace simbólico inesperado: {f}')
            if not f.is_file() or f.stat().st_nlink<2:continue
            digest=integrity.digest_bytes(f);key=str(f.relative_to(root));pending.append(key)
            if key in records and records[key]['hash']!=digest:raise ValueError(f'archivo modificado: {key}')
            if apply:
                records[key]={'hash':digest,'done':False};state.atomic(journal,json.dumps(records).encode())
                with tempfile.NamedTemporaryFile(dir=f.parent,delete=False) as t:
                    temp=Path(t.name)
                    with f.open('rb') as src:
                        import shutil
                        shutil.copyfileobj(src,t)
                    t.flush();os.fsync(t.fileno())
                try:
                    if integrity.digest_bytes(f)!=digest or integrity.digest_bytes(temp)!=digest:raise ValueError('contenido cambió')
                    os.replace(temp,f)
                    records[key]['done']=True;state.atomic(journal,json.dumps(records).encode())
                finally:temp.unlink(missing_ok=True)
        return {'ok':True,'apply':apply,'files':pending}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--directory',required=True);a.add_argument('--apply',action='store_true');args=a.parse_args()
    from scripts.core import oslib
    try: result=migrate(args.directory,args.apply)
    except (ValueError,OSError,RuntimeError) as e:oslib.emit({'ok':False,'error':str(e)},2)
    oslib.emit(result)
