"""Clean installation smoke on the current OS; emits evidence, never claims a different OS."""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts.core import oslib


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='work/animation-install.json');args=ap.parse_args()
    report={'ok':False,'system':platform.platform(),'python':sys.version,'wsl':'microsoft' in platform.release().lower(),'steps':[]}
    with tempfile.TemporaryDirectory(prefix='videovibe-install-') as tmp:
        root=Path(tmp)
        files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=oslib.ROOT).decode().split('\0')
        for name in set(files):
            if not name:continue
            src=oslib.ROOT/name;dst=root/name
            if not src.is_file() and not src.is_symlink():continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            if src.is_symlink(): dst.symlink_to(os.readlink(src))
            else: shutil.copy2(src,dst)
        commands=[['npm','ci','--no-audit','--no-fund'],[sys.executable,'-m','venv','.venv'],
                  [str(root/'.venv/bin/pip'),'install','numpy'],
                  [str(root/'.venv/bin/python'),'-m','unittest','discover','-s','scripts/tests'],
                  [str(root/'.venv/bin/python'),'-m','scripts.tools.animation_matrix','--formats','particle-title,narrative-sequence','--profiles','balanced']]
        for cmd in commands:
            r=__import__('scripts.core.state', fromlist=['run']).run(cmd,cwd=root,capture_output=True,text=True,timeout=1800,env={k:v for k,v in os.environ.items() if k!='VIDEOVIBE_CHANNELS'})
            report['steps'].append({'command':cmd,'exit_code':r.returncode,'output':(r.stdout+r.stderr)[-4000:]})
            if r.returncode:break
        report['ok']=len(report['steps'])==len(commands) and all(s['exit_code']==0 for s in report['steps'])
        if (root/'work/animation-matrix').exists():
            evidence=Path(args.out).resolve().parent/'animation-install-evidence'
            shutil.copytree(root/'work/animation-matrix',evidence,dirs_exist_ok=True)
            report['evidence']=str(evidence)
    oslib.write_json(Path(args.out).resolve(),report);oslib.emit(report,0 if report['ok'] else 1)

if __name__=='__main__':main()
