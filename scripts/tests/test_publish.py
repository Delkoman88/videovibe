"""La publicación debe detenerse antes de crear commits si falla una comprobación."""
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]

class TestPublishGate(unittest.TestCase):
    def run_failure(self, fail_guard):
        module=runpy.run_path(str(ROOT/'bin'/'publish'),run_name='publish_test')
        main=module['main']
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'local.json').write_text(json.dumps({'publish':{'author':'Test','email':'test@users.noreply.github.com'}}))
            calls=[]
            def git(*args,**kwargs):
                calls.append(args)
                return 'tree' if args==('rev-parse','HEAD^{tree}') else ''
            results=[subprocess.CompletedProcess([],1 if fail_guard else 0,'','failure')]
            if not fail_guard:results.append(subprocess.CompletedProcess([],1,'','failure'))
            with patch.dict(main.__globals__,{'ROOT':root,'git':git}), patch('sys.argv',['publish','--message','test']), patch('subprocess.run',side_effect=results):
                with self.assertRaises(SystemExit) as exc:main()
            self.assertIn('no se publica',str(exc.exception))
            self.assertFalse(any(a[0] in ('commit-tree','update-ref','push','tag') for a in calls))

    def test_privacy_failure_stops_publication(self):self.run_failure(True)
    def test_test_failure_stops_publication(self):self.run_failure(False)
