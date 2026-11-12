"""Migración reversible: datos, colisiones y recuperación tras interrupciones."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.tools.migrate_layout import plan, apply, rollback, resume


class TestMigration(unittest.TestCase):
    def test_apply_idempotence_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'canal'; root.mkdir()
            (root/'estilo.md').write_text('Mi estilo personal; consulta ritmo.md')
            (root/'raw').mkdir(); (root/'raw'/'anuncio.mp4').write_bytes(b'original')
            piece=root/'projects'/'pieza'; piece.mkdir(parents=True)
            (piece/'storyboard.json').write_text('{"platforms":{"anuncio":{}}}')
            (piece/'status.json').write_text('{"approvals":{"A":"yes","B":"yes"}}')
            before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            manifest=apply(plan([(root,root)]),Path(td)/'backup')
            self.assertEqual(plan([(root,root)]),[])
            self.assertEqual((root/'raw'/'anuncio.mp4').read_bytes(),b'original')
            status=json.loads((piece/'status.json').read_text())
            self.assertNotIn('B',status['approvals']); self.assertEqual(status['approvals']['A'],'yes')
            rollback(manifest)
            self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            rollback(manifest)

    def test_collision_and_later_edit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'c';root.mkdir()
            (root/'estilo.md').write_text('old');(root/'style.md').write_text('new')
            with self.assertRaises(ValueError):plan([(root,root)])
            (root/'style.md').unlink()
            manifest=apply(plan([(root,root)]),Path(td)/'backup')
            (root/'style.md').write_text('human edit')
            with self.assertRaises(ValueError):rollback(manifest)

    def test_move_media_keeps_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'old';dst=Path(td)/'new';src.mkdir()
            (src/'anuncio.mp4').write_bytes(b'video')
            manifest=apply(plan([(src,dst)]),Path(td)/'backup')
            self.assertEqual((dst/'ads.mp4').read_bytes(),b'video')
            rollback(manifest)
            self.assertEqual((src/'anuncio.mp4').read_bytes(),b'video')

    def test_resume_after_rename_before_journal_update(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'c';root.mkdir()
            (root/'estilo.md').write_text('referencia ritmo.md')
            ops=plan([(root,root)])
            backup=Path(td)/'backup';backup.mkdir()
            saved=backup/'0.original';saved.write_bytes((root/'estilo.md').read_bytes())
            ops[0]['backup']=str(saved)
            manifest=backup/'manifest.json'
            manifest.write_text(json.dumps({'version':1,'operations':ops}))
            (root/'estilo.md').rename(root/'style.md')
            resume(manifest)
            self.assertEqual((root/'style.md').read_text(),'referencia rhythm.md')
            resume(manifest)
            rollback(manifest)
            self.assertEqual((root/'estilo.md').read_text(),'referencia ritmo.md')
