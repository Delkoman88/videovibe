"""Regresiones de la auditoría final; archivos sintéticos, sin piezas personales."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts.core import editlib, integrity, state, reviewlib, oslib
from scripts.tests.test_deliveries import piece


class AuditRegressions(unittest.TestCase):
    def test_platform_and_caption_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            _, p = piece(td, plats=('tiktok',))
            (p/'media.json').write_text('{"items":[]}')
            (p/'captions/captions.json').write_text('{}')
            st = {'stages': {stage: {'inputs': integrity.inputs(p, stage), 'outputs': integrity.outputs(p, stage)}
                             for stage in ('render','subtitulos')}}
            self.assertTrue(editlib.stage_dirty('render',p,st,['tiktok','reels'])[0])
            brand = p.parent.parent/'brand.json'
            data = json.loads(brand.read_text()); data['captions']['max_chars_per_line'] += 5
            brand.write_text(json.dumps(data))
            self.assertTrue(editlib.stage_dirty('subtitulos',p,st,['tiktok'])[0])

    def test_compiled_html_invalidates_B(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'hf').mkdir();(p/'storyboard.json').write_text('{}')
            html=p/'hf/index.html';html.write_text('before')
            st={'approvals':{'B':{'version':2,'inputs':integrity.approval_inputs(p,'B'),
                                 'presentation':reviewlib.fingerprint(p,'B')}}}
            html.write_text('after')
            self.assertFalse(integrity.valid(p,'B',st))

    def test_parent_death_does_not_release_worker(self):
        if os.name == 'nt': self.skipTest('POSIX workers')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            worker='import time; print("ready",flush=True); time.sleep(60)'
            code=('from scripts.core import state; from pathlib import Path; import sys\n'
                  'with state.lock(Path('+repr(td)+')):\n'
                  ' state.run([sys.executable,"-c",'+repr(worker)+'])')
            parent=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,text=True)
            try:
                self.assertEqual(parent.stdout.readline().strip(),'ready')
                # Worker has the OS descriptor even before its reservation is written.
                parent.terminate();parent.wait(timeout=10)
                with self.assertRaises(RuntimeError):
                    with state.lock(p): pass
            finally:
                for record in (p/'work').glob('worker-*.json'):
                    try: os.killpg(json.loads(record.read_text())['group'],9)
                    except ProcessLookupError: pass
                if parent.poll() is None: parent.kill();parent.wait()
                parent.stdout.close()

    def test_changed_composition_and_render_fail_before_success(self):
        loader=importlib.machinery.SourceFileLoader('audit_edit',str(oslib.ROOT/'bin/edit'))
        spec=importlib.util.spec_from_loader(loader.name,loader)
        edit=importlib.util.module_from_spec(spec);loader.exec_module(edit)
        with tempfile.TemporaryDirectory() as td:
            _, p=piece(td,plats=('tiktok',))
            (p/'media.json').write_text('{"items":[]}')
            (p/'storyboard.json').write_text('{"platforms":{"tiktok":{}}}')
            (p/'hf').mkdir();(p/'hf/index.html').write_text('old')
            def execute(stage):
                with patch.object(sys,'argv',['edit',str(p),'--until-stage',stage,'--json']), patch.object(state,'hold'), patch.object(edit.editlib,'next_action',return_value={'run':stage,'why':'fixture'}), patch.object(oslib,'emit') as emit:
                    edit.main()
                    return emit.call_args.args[0]
            def changing(*args):
                (p/'storyboard.json').write_text('{"tail_s":3,"platforms":{"tiktok":{}}}')
            with patch.object(edit,'do_stage',side_effect=changing):
                self.assertFalse(execute('composicion')['ok'])
            self.assertEqual(state.load(p)['stages']['composicion']['status'],'failed')
            state.update(p,approvals={'B':{'version':2,'inputs':integrity.approval_inputs(p,'B'),
                                         'presentation':reviewlib.fingerprint(p,'B')}})
            original=(p/'renders/tiktok.mp4').read_bytes()
            def rendering(cmd,*args,**kwargs):
                Path(cmd[cmd.index('-o')+1]).write_bytes(b'new')
                (p/'hf/index.html').write_text('changed')
            with patch.object(edit,'run',side_effect=rendering):
                self.assertFalse(execute('render')['ok'])
            self.assertEqual((p/'renders/tiktok.mp4').read_bytes(),original)
            self.assertFalse(list((p/'renders').glob('.*.pending.mp4')))


    def test_normal_worker_releases_reservation(self):
        if os.name == 'nt': self.skipTest('POSIX workers')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            with state.lock(p):
                result=state.run([sys.executable,'-c','print("done")'],capture_output=True,text=True)
                self.assertEqual(result.stdout.strip(),'done')
                self.assertFalse(list((p/'work').glob('worker-*.json')))
            with state.lock(p): pass

    def test_platform_receipt_invalidates_even_with_existing_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            _, p=piece(td)
            st={'stages':{'entrega':{'version':3,'platforms':['tiktok'],
                 'inputs':integrity.inputs(p,'entrega'),'outputs':integrity.outputs(p,'entrega')}}}
            self.assertTrue(editlib.stage_dirty('entrega',p,st,['tiktok','reels'])[0])
