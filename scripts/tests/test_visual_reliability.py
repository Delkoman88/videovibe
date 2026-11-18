"""Public synthetic regression cases: reading and conservative cutout fallbacks."""
import unittest
from copy import deepcopy
from scripts.composer.reading import windows
from formats.text import kinetic_duration
from scripts.tools.cutout_review import propose

class ReliabilityTests(unittest.TestCase):
    def test_long_reveal_and_independent_caption(self):
        sb={'overlays':[{'id':'title','in':0,'out':5,'type':'title','text':'Una historia completa','text_fx':'rise'}]}
        w=windows(sb,{'groups':[{'id':'g','in':0,'out':1}]},{})
        self.assertGreater(w['title']['read_start'],.7)
        self.assertEqual(w['g']['read_start'],.14)
        self.assertTrue(w['title']['mask'])
    def test_short_captions_keep_their_exact_span(self):
        from scripts.composer.timing import caption_enter, caption_exit
        for style in ('classic','neon'):
            self.assertEqual(caption_enter(.18,style),0)
            self.assertEqual(caption_exit(.18),0)
            w=windows({}, {'groups':[{'id':'g','in':2,'out':2.18}]},{'captions':{'style':style}})['g']
            self.assertEqual((w['read_start'],w['read_end']),(2,2.18))

    def test_kinetic_title_internal_exit_matches_reading(self):
        from formats.direction import resolve
        import formats
        sb={'motion':resolve('restrained'),'scenes':[{'id':'bike','format':'kinetic-title','in':59.44,'out':63.27,'params':{'text':'Scrambler *400X*'}}]}
        w=windows(sb,{}, {})['bike']
        self.assertAlmostEqual(w['read_end'],62.67)
        self.assertLess(w['read_start'],w['read_end'])

    def test_all_text_variants(self):
        for v in ('rise','wave','blur','mask'):
            self.assertGreater(kinetic_duration(v,'Un título con acentos'),kinetic_duration(v,'A'))
    def test_all_fallbacks_and_source_unchanged(self):
        for kind,textkey,action in [('text-behind','text','card'),('background-swap','text','card'),('subject-glow',None,'removed'),('freeze-cutout','label','tag')]:
            f={'id':'fx','type':kind,**({'at':2,'duration':1} if kind=='freeze-cutout' else {'in':2,'out':4})}
            if textkey:f[textkey]='Mismo texto'
            sb={'fx':[f],'video':'cut/master-cut.mp4','audio':{'test':1}}
            original=deepcopy(sb)
            result,changes=propose(sb,[{'id':'fx','verdict':'defective','reason':'Objeto ajeno'}])
            self.assertEqual(changes[0]['action'],action);self.assertEqual(sb,original)
            self.assertEqual(result['audio'],sb['audio']);self.assertEqual(result['fx'],[])
    def test_conflicting_card_is_preserved(self):
        sb={'fx':[{'id':'f','type':'text-behind','in':2,'out':4,'text':'Extra'}], 'overlays':[{'id':'existing','type':'card','in':1,'out':5,'text':'Original'}]}
        r,c=propose(sb,[{'id':'f','verdict':'uncertain','reason':'No hay certeza'}])
        self.assertEqual(r['overlays'],sb['overlays']);self.assertTrue(c[0]['conflict'])
    def test_usable_unchanged_and_missing_verdict_rejected(self):
        sb={'fx':[{'id':'f','type':'subject-glow','in':2,'out':4}]}
        r,c=propose(sb,[{'id':'f','verdict':'usable','reason':'Inspección completada'}]);self.assertFalse(c);self.assertEqual(r['fx'],sb['fx'])
        with self.assertRaises(ValueError):propose(sb,[])

    def test_transaction_and_idempotence(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts.tools.cutout_review import apply
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);sb={'fx':[{'id':'f','type':'subject-glow','in':2,'out':4}]}
            (p/'storyboard.json').write_text(json.dumps(sb));(p/'status.json').write_text(json.dumps({'approvals':{'A':{'at':'a'},'B':{'at':'b'}},'fingerprints':{'render:tiktok':'old'}}))
            evidence=p/'e.png';evidence.write_bytes(b'evidence')
            import hashlib
            report={'version':1,'fingerprint':'test','evidence_hashes':{str(evidence):hashlib.sha256(evidence.read_bytes()).hexdigest()},'effects':[{'id':'f','verdict':'uncertain','reason':'No fiable','evidence':[str(evidence)]}]}
            with patch('scripts.tools.cutout_review.fingerprint',return_value='test'),patch('scripts.tools.cutout_review.cutout.ensure',return_value={}),patch('scripts.validation.storyboard.context'),patch('scripts.validation.storyboard.validate',return_value=([],[])):
                with self.assertRaises(ValueError):apply(p,report)
                original=(p/'storyboard.json').read_bytes()
                apply(p,report,dry_run=True,reprocess=True);self.assertEqual(original,(p/'storyboard.json').read_bytes())
                with patch('scripts.validation.storyboard.validate',return_value=(['invalid'],[])):
                    with self.assertRaises(ValueError):apply(p,report,reprocess=True)
                self.assertEqual(original,(p/'storyboard.json').read_bytes())
                from scripts.core.animationanchors import atomic_json as real_write
                def fail_status(path,data):
                    if path.name=='status.json':raise OSError('simulated write failure')
                    return real_write(path,data)
                with patch('scripts.tools.cutout_review.atomic_json',side_effect=fail_status):
                    with self.assertRaises(OSError):apply(p,report,reprocess=True)
                self.assertEqual(original,(p/'storyboard.json').read_bytes())
                status_original=(p/'status.json').read_bytes()
                def fail_receipt(path,data):
                    if path.name=='substitutions.json':raise OSError('simulated receipt failure')
                    return real_write(path,data)
                with patch('scripts.tools.cutout_review.atomic_json',side_effect=fail_receipt):
                    with self.assertRaises(OSError):apply(p,report,reprocess=True)
                self.assertEqual(original,(p/'storyboard.json').read_bytes())
                self.assertEqual(status_original,(p/'status.json').read_bytes())
                apply(p,report,reprocess=True)
                status=json.loads((p/'status.json').read_text());self.assertIn('A',status['approvals']);self.assertNotIn('B',status['approvals'])
                self.assertFalse(apply(p,report)['changed'])

    def test_stale_evidence_rejected(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts.tools.cutout_review import apply
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'storyboard.json').write_text('{"fx": []}')
            with patch('scripts.tools.cutout_review.fingerprint',return_value='new'),patch('scripts.tools.cutout_review.cutout.ensure',return_value={}):
                with self.assertRaisesRegex(ValueError,'desactualizada'):apply(p,{'version':1,'fingerprint':'old'})

    def test_unavailable_segmentation_yields_uncertain_evidence(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from scripts.tools.cutout_review import prepare
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'cut').mkdir();(p/'cut/master-cut.mp4').write_bytes(b'fixture');(p/'cut/cut-map.json').write_text('{}')
            (p/'storyboard.json').write_text(json.dumps({'fx':[{'id':'f','type':'subject-glow','in':0,'out':2}]}))
            def frame(args):Path(args[-1]).write_bytes(b'synthetic-frame')
            with patch('scripts.tools.cutout_review.cutout.ensure',side_effect=ValueError('model unavailable')),patch('scripts.tools.cutout_review.oslib.run',side_effect=frame):
                report=prepare(p)
            self.assertEqual(report['effects'][0]['verdict'],'uncertain')
            self.assertFalse(report['effects'][0]['segmented'])
            self.assertEqual(len(report['effects'][0]['evidence']),3)
