import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from scripts.core import integrity, state, reviewlib, editlib
from scripts.pipeline.deliver import place, deliver
from scripts.tools.migrate_deliveries import migrate

class IntegrityTests(unittest.TestCase):
    def test_approval_and_preserved_dates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'storyboard.json').write_text('{}');(p/'media.json').write_text('{"items":[]}')
            a={'version':2,'inputs':integrity.approval_inputs(p,'B'),'presentation':reviewlib.fingerprint(p,'B')}
            self.assertTrue(integrity.valid(p,'B',{'approvals':{'B':a}}))
            stamp=(p/'storyboard.json').stat().st_mtime
            (p/'storyboard.json').write_text('{"tail_s":1}');os.utime(p/'storyboard.json',(stamp,stamp))
            self.assertFalse(integrity.valid(p,'B',{'approvals':{'B':a}}))
            self.assertFalse(integrity.valid(p,'B',{'approvals':{'B':{'at':'2020-01-01'}}}))
    def test_copy_and_migration(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);src=p/'src';dst=p/'dst';src.write_bytes(b'one');place(src,dst);src.write_bytes(b'two')
            self.assertEqual(dst.read_bytes(),b'one')
            linked=p/'linked';os.link(src,linked)
            self.assertIn('linked',migrate(p)['files'])
            migrate(p,True);src.write_bytes(b'three');self.assertEqual(linked.read_bytes(),b'two')
    def test_state_read_only_and_process_lock(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.assertEqual(state.load(p)['approvals'],{});self.assertFalse((p/'status.json').exists())
            with state.lock(p):
                env={k:v for k,v in os.environ.items() if k!='VIDEOVIBE_OPERATION'}
                code='from scripts.core.state import lock; from pathlib import Path\nwith lock(Path('+repr(td)+')): pass'
                r=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True)
                self.assertNotEqual(r.returncode,0)
            with state.transaction(p) as s:s['custom']=True
            self.assertTrue(state.load(p)['custom'])
    def test_boundaries(self):
        root=Path(__file__).resolve().parents[2]/'scripts'
        forbidden={'core':{'tools','pipeline','validation','composer'},'validation':{'composer','pipeline','tools'},'composer':{'pipeline','tools'}}
        errors=[]
        for group,blocked in forbidden.items():
            for p in (root/group).glob('*.py'):
                for n in ast.walk(ast.parse(p.read_text())):
                    if isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('scripts.') and n.module.split('.')[1] in blocked:errors.append(str(p)+':'+n.module)
        self.assertEqual(errors,[])
    def test_unverified_delivery_refused(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'verificación'):deliver(Path(td),['tiktok'])

    def test_verify_rejects_mutation_during_measurement(self):
        from unittest.mock import patch
        from scripts.pipeline import verify
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'cut').mkdir();(p/'renders').mkdir()
            (p/'storyboard.json').write_text('{}');(p/'cut/cut-map.json').write_text('{}')
            f=p/'renders/tiktok.mp4';f.write_bytes(b'old')
            def changing(*args):
                f.write_bytes(b'new')
                return {'platform':'tiktok','checks':[]}
            with patch.object(sys,'argv',['verify','--project','fixture','--platform','tiktok']),patch.object(verify.oslib,'project_dir',return_value=p),patch.object(verify,'check_platform',side_effect=changing),patch.object(verify.oslib,'emit') as emit:
                verify.main()
            self.assertFalse(emit.call_args.args[0]['ok'])
            self.assertIn('contenido cambió',emit.call_args.args[0]['failed'][0])

    def test_atomic_failure_preserves_previous_state(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);state.update(p,value='original');before=(p/'status.json').read_bytes()
            with patch.object(state.os,'replace',side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):state.atomic(p/'status.json',b'partial')
            self.assertEqual((p/'status.json').read_bytes(),before)

    def test_dead_process_releases_lock(self):
        with tempfile.TemporaryDirectory() as td:
            code='from scripts.core.state import lock; from pathlib import Path; import time\nwith lock(Path('+repr(td)+')):\n print("ready",flush=True)\n time.sleep(60)'
            child=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),'ready')
                child.terminate();child.wait(timeout=10)
                with state.lock(Path(td)):pass
            finally:
                if child.poll() is None:child.kill();child.wait()
                child.stdout.close()

    def test_manual_transcript_is_not_overwritten_by_cache(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'transcript').mkdir();(p/'raw').mkdir()
            (p/'media.json').write_text('{"items":[{"id":"s","file":"raw/s.mp4","audio":"s.wav"}]}')
            (p/'raw/s.mp4').write_bytes(b'source');f=p/'transcript/s.json';f.write_text('{}')
            st={'stages':{'transcripcion':{'inputs':integrity.inputs(p,'transcripcion'),'outputs':integrity.outputs(p,'transcripcion')}}}
            f.write_text('{"manual":"correction"}')
            self.assertFalse(editlib.stage_dirty('transcripcion',p,st,['tiktok'])[0])

    def test_interrupted_editorial_stage_must_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'media.json').write_text('{"items":[]}')
            for status in ('running','failed'):
                self.assertTrue(editlib.stage_dirty('ingesta',p,{'stages':{'ingesta':{'status':status}}},['tiktok'])[0])
