import copy
import unittest
import formats
from formats.direction import resolve,validate,candidates,metadata
from scripts.core.animationqa import inspect

class TestDirection(unittest.TestCase):
    def test_profiles_are_isolated_and_versioned(self):
        a=resolve('balanced');a['enter_s']=99
        self.assertEqual(resolve('balanced')['enter_s'],.35)
        self.assertTrue(validate(a));self.assertFalse(validate(resolve('balanced')))

    def test_legacy_output_and_opt_in(self):
        s={'id':'title','format':'particle-title','in':0,'out':5,'params':{'text':'Hola'}}
        a=formats.render(s)
        b=formats.render(s,motion=resolve('restrained'))
        self.assertNotEqual(a,b)
        self.assertEqual(a,formats.render(s))
        self.assertIn('const vvMotion',b)

    def test_registry_has_intents(self):
        r=formats.registry(formats.available_packs())
        self.assertTrue(all(metadata(n,m)['intents'] for n,m in r.items()))
        cs=candidates(r,'compare',5)
        self.assertTrue(cs);self.assertFalse(any(x['resources'] for x in cs))
        self.assertEqual(cs,candidates(r,'compare',5))

    def test_overlaps_and_density(self):
        sb={'overlays':[{'in':0,'out':3,'text':'a'},{'in':2,'out':4,'text':'b'}]}
        self.assertFalse(inspect(sb,{})['ok'])
        self.assertEqual(inspect({}, {})['visual_review'],'pending')

    def test_sequence_determinism_and_validation(self):
        r=formats.registry(('narrative',));m=r['narrative-sequence']
        self.assertFalse(m['check'](m['example']))
        self.assertTrue(m['check']({'recipe':'missing','steps':[]}))
        s={'id':'seq','format':'narrative-sequence','in':0,'out':8,'params':copy.deepcopy(m['example'])}
        self.assertEqual(formats.render(s,('narrative',)),formats.render(s,('narrative',)))

    def test_snapshot_preserves_A_and_invalidates_B(self):
        import json, os, subprocess, tempfile, shutil, sys
        from pathlib import Path
        from scripts.core import oslib
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);channel=root/'sample'
            shutil.copytree(oslib.ROOT/'channels/_template',channel)
            config=json.loads((channel/'channel.json').read_text());config['id']='sample'
            (channel/'channel.json').write_text(json.dumps(config))
            piece=channel/'projects'/'piece';piece.mkdir()
            (piece/'storyboard.json').write_text('{"scenes":[]}')
            (piece/'status.json').write_text('{"approvals":{"A":{"note":"cut"},"B":{"note":"visual"}},"fingerprints":{"render:tiktok":"old","check":"old"}}')
            cmd=[sys.executable,'-m','scripts.tools.animation_style','--channel','sample','--project',str(piece),'--snapshot']
            env={**os.environ,'VIDEOVIBE_CHANNELS':td}
            r=subprocess.run(cmd,cwd=oslib.ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            status=json.loads((piece/'status.json').read_text())
            self.assertIn('A',status['approvals']);self.assertNotIn('B',status['approvals'])
            self.assertEqual(status['fingerprints'],{})
            before=(piece/'status.json').read_bytes()
            r=subprocess.run(cmd,cwd=oslib.ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual(before,(piece/'status.json').read_bytes())

    def test_all_format_examples_render_with_each_profile(self):
        reg=formats.registry(formats.available_packs())
        for name, meta in reg.items():
            for profile in ('restrained','balanced','energetic'):
                with self.subTest(format=name,profile=profile):
                    scene={'id':'matrix','format':name,'in':0,'out':8,'params':copy.deepcopy(meta['example'])}
                    output=formats.render(scene,formats.available_packs(),motion=resolve(profile))
                    self.assertIn('window.__timelines',output)
                    self.assertIn('const vvMotion',output)

    def test_legacy_and_v1_snapshots(self):
        import hashlib,json
        from pathlib import Path
        formats.configure('')
        formats.CTX['labels']={'illustrative':'ILLUSTRATIVE'}
        formats.CTX['channel']='VIDEOVIBE'
        fixture=json.loads((Path(__file__).parent/'fixtures/animation-v1.json').read_text())
        for name,m in formats.registry(formats.available_packs()).items():
            scene={'id':'baseline','format':name,'in':0,'out':8,'params':m['example']}
            for profile,expected in fixture[name].items():
                with self.subTest(format=name,profile=profile):
                    actual=formats.render(scene,formats.available_packs(),motion=None if profile=='legacy' else resolve(profile,1))
                    self.assertEqual(expected,hashlib.sha256(actual.encode()).hexdigest())

    def test_word_anchors_scene_and_steps(self):
        from scripts.core.animationanchors import resolve as anchors
        sb={'scenes':[{'id':'a','format':'narrative-sequence','in':0,'out':8,'anchor':{'word_id':'w1'},
                      'params':{'steps':[{'text':'Uno','anchor':{'word_id':'w2','offset':.1}}]}}]}
        new=anchors(sb,[{'id':'w1','start':2},{'id':'w2','start':4}])
        self.assertEqual(new['scenes'][0]['in'],2)
        self.assertEqual(new['scenes'][0]['params']['steps'][0]['at'],2.1)
        self.assertEqual(sb['scenes'][0]['in'],0)
        with self.assertRaises(ValueError):anchors(sb,[])

    def test_no_candidate_for_excess_text_or_duration(self):
        reg=formats.registry(formats.available_packs())
        self.assertEqual(candidates(reg,'highlight',.1),[])
        self.assertEqual(candidates(reg,'highlight',5,'x'*200),[])

    def test_phase_budget_rejects_unreadable_scene(self):
        from formats.direction import budget
        with self.assertRaises(ValueError):budget({'id':'short','in':0,'out':2,'params':{'text':'una frase demasiado larga para leer'}},resolve('balanced'))

    def test_invalid_snapshot_never_changes_files(self):
        import tempfile,shutil,json
        from pathlib import Path
        from scripts.core import oslib
        from scripts.core.animationanchors import snapshot
        with tempfile.TemporaryDirectory() as td:
            ch=Path(td)/'channel';shutil.copytree(oslib.ROOT/'channels/_template',ch)
            p=ch/'projects/p';p.mkdir()
            (p/'storyboard.json').write_text(json.dumps({'scenes':[{'id':'x','format':'particle-title','in':0,'out':.1,'params':{'text':'Inlegible'}}]}))
            (p/'status.json').write_text('{"approvals":{"A":true,"B":true}}')
            before=[(p/n).read_bytes() for n in ('storyboard.json','status.json')]
            with self.assertRaises(ValueError):snapshot(p,resolve('balanced'))
            self.assertEqual(before,[(p/n).read_bytes() for n in ('storyboard.json','status.json')])

    def test_dry_run_does_not_invalidate_approval(self):
        import tempfile,shutil
        from pathlib import Path
        from scripts.core import oslib
        from scripts.core.animationanchors import snapshot
        with tempfile.TemporaryDirectory() as td:
            ch=Path(td)/'channel';shutil.copytree(oslib.ROOT/'channels/_template',ch)
            p=ch/'projects/p';p.mkdir()
            (p/'storyboard.json').write_text('{"scenes":[]}')
            (p/'status.json').write_text('{"approvals":{"A":true,"B":true}}')
            before=(p/'status.json').read_bytes()
            result=snapshot(p,resolve('balanced'),dry_run=True)
            self.assertTrue(result['changed']);self.assertIn('motion',result['diff'])
            self.assertEqual(before,(p/'status.json').read_bytes())
            self.assertEqual((p/'storyboard.json').read_text(),'{"scenes":[]}')

    def test_missing_requested_frame_fails(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from types import SimpleNamespace
        from scripts.tools.gallery import snapshot
        with tempfile.TemporaryDirectory() as td,patch('scripts.tools.gallery._hf',return_value=SimpleNamespace(returncode=0)):
            with self.assertRaises(ValueError):snapshot(Path(td),[1.0],Path(td))

    def test_quality_fingerprint_tracks_fonts_and_excludes_evidence(self):
        import tempfile
        from pathlib import Path
        from scripts.tools.animation_quality import fingerprint
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'hf/assets/fonts').mkdir(parents=True)
            (p/'storyboard.json').write_text('{}');(p/'hf/index.html').write_text('html')
            f=p/'hf/assets/fonts/test.ttf';f.write_bytes(b'font one');a=fingerprint(p)
            (p/'hf/quality').mkdir();(p/'hf/quality/at-1.png').write_bytes(b'evidence')
            self.assertEqual(a,fingerprint(p))
            f.write_bytes(b'font two');self.assertNotEqual(a,fingerprint(p))

    def test_sequence_objects_and_licenses(self):
        from formats.packs.narrative import check,uses
        params={'recipe':'compare','objects':[{'id':'a','kind':'icon','icon':'dna'},{'id':'b','kind':'image','image':'licensed'}],
                'steps':[{'object':'a','text':'Antes'},{'object':'b','text':'Después'}]}
        self.assertFalse(check(params));self.assertEqual(uses(params),[('images','licensed')])
        params['steps'][1]['object']='missing';self.assertTrue(check(params))

    def test_candidate_boolean_does_not_bypass_asset_license(self):
        reg=formats.registry(formats.available_packs())
        result=candidates(reg,'locate',8,available_assets=True)
        self.assertFalse(any(r['resources'] for r in result))

    def test_unknown_profile_version_fails(self):
        p=resolve('balanced');p['version']=999
        self.assertTrue(validate(p))

    def test_status_failure_rolls_back_exact_storyboard_bytes(self):
        import tempfile,shutil
        from pathlib import Path
        from unittest.mock import patch
        from scripts.core import oslib,animationanchors
        with tempfile.TemporaryDirectory() as td:
            ch=Path(td)/'channel';shutil.copytree(oslib.ROOT/'channels/_template',ch)
            p=ch/'projects/p';p.mkdir()
            original=b'{"scenes":[]}\n'
            (p/'storyboard.json').write_bytes(original)
            (p/'status.json').write_text('{"approvals":{"A":true,"B":true}}')
            writer=animationanchors.atomic_json
            def fail_status(path,data):
                if path.name=='status.json':raise OSError('disk error')
                return writer(path,data)
            with patch.object(animationanchors,'atomic_json',side_effect=fail_status):
                with self.assertRaises(OSError):animationanchors.snapshot(p,resolve('balanced'))
            self.assertEqual(original,(p/'storyboard.json').read_bytes())
            self.assertTrue(oslib.read_json(p/'status.json')['approvals']['B'])
