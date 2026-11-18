"""Regeneración de la vista sin pérdida de decisiones ni aprobaciones."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pipeline.paper_cut import refresh_from_cut, main
from unittest.mock import patch


class TestPaperRefresh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        (self.p / 'cut').mkdir()
        (self.p / 'transcript').mkdir()
        self.cut = {'version': 1, 'sources': ['a'], 'pause_s': .35, 'lines': [
            {'id': 'L1', 'src': 'a', 'start': .2, 'end': 1, 'text': 'No está demostrado.', 'status': 'keep', 'reason': ''},
            {'id': 'L2', 'src': 'a', 'start': 2, 'end': 3, 'text': 'Retoma.', 'status': 'drop', 'reason': 'repetición'}]}
        self.write('cut/cut-list.json', self.cut)
        self.write('media.json', {'items': [{'id': 'a', 'duration_s': 5}]})
        self.write('transcript/a.json', {'islands': [[.2, 1], [2, 3]]})
        self.write('status.json', {'approvals': {'A': 'original'}})
        (self.p / 'cut/PAPER-CUT.md').write_text('anterior')

    def write(self, name, value):
        (self.p / name).write_text(json.dumps(value, indent=3))

    def test_refresh_preserves_source_bytes_and_approval(self):
        names = ['cut/cut-list.json', 'transcript/a.json', 'status.json', 'media.json']
        before = {n: (self.p/n).read_bytes() for n in names}
        result = refresh_from_cut(self.p)
        self.assertAlmostEqual(result['estimated_s'], 1.21)
        text = (self.p/'cut/PAPER-CUT.md').read_text()
        self.assertIn('No está demostrado.', text)
        self.assertIn('repetición', text)
        self.assertEqual(before, {n: (self.p/n).read_bytes() for n in names})
        refresh_from_cut(self.p)
        self.assertEqual(text, (self.p/'cut/PAPER-CUT.md').read_text())

    def test_invalid_data_never_replaces_review(self):
        mutations = [lambda c: c['lines'][0].update(status='maybe'),
                     lambda c: c['lines'][0].update(end=99),
                     lambda c: c['lines'][0].update(start=float('nan')),
                     lambda c: c['lines'][1].update(id='L1'),
                     lambda c: c['lines'].reverse(),
                     lambda c: c.update(sources=['../a']),
                     lambda c: c.update(pause_s=-1),
                     lambda c: c['lines'][0].update(status='drop')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = copy.deepcopy(self.cut); mutate(value)
                self.write('cut/cut-list.json', value)
                with self.assertRaises(ValueError): refresh_from_cut(self.p)
                self.assertEqual('anterior', (self.p/'cut/PAPER-CUT.md').read_text())

    def test_missing_source_never_replaces_review(self):
        (self.p/'transcript/a.json').unlink()
        with self.assertRaisesRegex(ValueError, 'a.json'): refresh_from_cut(self.p)
        self.assertEqual('anterior', (self.p/'cut/PAPER-CUT.md').read_text())

    def test_cli_refresh_does_not_load_channel_or_generate_cut(self):
        with patch('sys.argv', ['paper_cut', '--project', str(self.p), '--refresh-from-cut']), \
             patch('scripts.pipeline.paper_cut.oslib.project_dir', return_value=self.p), \
             patch('scripts.pipeline.paper_cut.oslib.load_channel', side_effect=AssertionError('generation')), \
             patch('scripts.pipeline.paper_cut.oslib.emit') as emit:
            main()
            self.assertTrue(emit.call_args.args[0]['ok'])
