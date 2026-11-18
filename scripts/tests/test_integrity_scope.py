"""Alcance de las huellas de integridad (revisión de v0.13.x): subtítulos ligados a su corte,
huellas sin rutas absolutas, motor fuera de las etapas editables y de B, reaprobación de A."""
import importlib.machinery
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.core import editlib, integrity, oslib, reviewlib
from scripts.tests.test_deliveries import piece


def load_bin(name):
    loader = importlib.machinery.SourceFileLoader(f"scope_{name}", str(oslib.ROOT / "bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def load_edit():
    return load_bin("edit")


def cut_map(p, segments):
    (p / "cut").mkdir(exist_ok=True)
    segs = [{"src": "t1", "src_in": a, "src_out": b} for a, b in segments]
    (p / "cut" / "cut-map.json").write_text(json.dumps({"duration_s": sum(b - a for a, b in segments),
                                                        "segments": segs}))


class CaptionsFollowCut(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        _, self.p = piece(self.td.name, plats=("tiktok",))
        cut_map(self.p, [(0, 5)])
        (self.p / "transcript").mkdir(exist_ok=True)
        self.t = self.p / "transcript" / "master-cut.json"

    def tearDown(self):
        self.td.cleanup()

    def write_transcript(self, fp="__current__", **extra):
        data = {"id": "master-cut", "words": [{"id": "w0", "w": "hola", "start": 0, "end": 0.4}], **extra}
        if fp:
            data["cut_fingerprint"] = editlib.cut_fingerprint(self.p) if fp == "__current__" else fp
        self.t.write_text(json.dumps(data))

    def test_matches_only_its_cut(self):
        self.assertIsNone(editlib.transcript_matches_cut(self.p))
        self.write_transcript()
        self.assertTrue(editlib.transcript_matches_cut(self.p))
        cut_map(self.p, [(0, 3), (4, 6)])                     # corte nuevo
        self.assertFalse(editlib.transcript_matches_cut(self.p))

    def test_legacy_transcript_uses_captions_fingerprint(self):
        self.write_transcript(fp=None)
        self.assertFalse(editlib.transcript_matches_cut(self.p))   # sin forma de saberlo
        (self.p / "captions" / "captions.json").write_text(json.dumps({"cut_fingerprint": editlib.cut_fingerprint(self.p)}))
        self.assertTrue(editlib.transcript_matches_cut(self.p))
        cut_map(self.p, [(1, 5)])
        self.assertFalse(editlib.transcript_matches_cut(self.p))

    def test_edit_retranscribes_after_recut_and_keeps_backup(self):
        edit = load_edit()
        self.write_transcript()
        old = editlib.cut_fingerprint(self.p)
        cut_map(self.p, [(0, 2), (3, 5)])
        calls = []
        with patch.object(edit, "run", side_effect=lambda cmd, P, **k: calls.append(cmd) or {"ok": True}):
            out = edit.do_stage("subtitulos", self.p, "cocina/x", ["tiktok"], {}, True)
        self.assertNotIn("--from-transcript", calls[0])
        self.assertTrue((self.p / "transcript" / f"master-cut.{old}.json").is_file())
        self.assertIn("vuelve a aplicarlas", out["warning"])

    def test_edit_reuses_transcript_of_current_cut(self):
        edit = load_edit()
        self.write_transcript()
        calls = []
        with patch.object(edit, "run", side_effect=lambda cmd, P, **k: calls.append(cmd) or {"ok": True}):
            out = edit.do_stage("subtitulos", self.p, "cocina/x", ["tiktok"], {}, True)
        self.assertIn("--from-transcript", calls[0])
        self.assertNotIn("warning", out)
        self.assertEqual(sorted(x.name for x in (self.p / "transcript").iterdir()), ["master-cut.json"])


def labels(P, stage, engine=True):
    paths, _ = integrity._paths(P, stage, engine)
    return {integrity.label(x, P) for x in paths}


class FingerprintScope(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        _, self.p = piece(self.td.name, plats=("tiktok",))
        self.ch = integrity.channel_dir(self.p)
        cut_map(self.p, [(0, 5)])
        (self.p / "raw").mkdir(exist_ok=True)
        (self.p / "raw" / "t1.mp4").write_bytes(b"toma")
        (self.p / "storyboard.json").write_text('{"platforms": {"tiktok": {}}}')
        (self.p / "hf").mkdir(exist_ok=True)
        (self.p / "hf" / "index.html").write_text("<html>v1</html>")

    def tearDown(self):
        self.td.cleanup()

    def test_editable_stages_ignore_engine_and_unrelated_channel_settings(self):
        for stage in integrity.EDITABLE:
            names = labels(self.p, stage)
            self.assertFalse(any(n.startswith("engine:") and not n.startswith(("engine:models/", "engine:lang/"))
                                 for n in names), (stage, names))
            self.assertNotIn("channel:channel.json", names, stage)
        before = integrity.inputs(self.p, "transcripcion")
        cfg = json.loads((self.ch / "channel.json").read_text())
        cfg["format_packs"] = cfg.get("format_packs", []) + ["sketch"]     # activar un paquete
        (self.ch / "channel.json").write_text(json.dumps(cfg))
        self.assertEqual(before, integrity.inputs(self.p, "transcripcion"))
        (self.ch / "vocabulary.txt").write_text("Laboratorio abierto\n")
        self.assertNotEqual(before, integrity.inputs(self.p, "transcripcion"))

    def test_B_depends_on_content_and_compiled_html_not_engine(self):
        self.assertFalse(any(n.startswith("engine:") for n in labels(self.p, "composicion", engine=False)))
        self.assertTrue(any(n.startswith("engine:formats/") for n in labels(self.p, "composicion")))
        b = integrity.approval_inputs(self.p, "B")
        (self.p / "storyboard.json").write_text('{"platforms": {"tiktok": {}}, "scenes": []}')
        self.assertNotEqual(b, integrity.approval_inputs(self.p, "B"))
        b = integrity.approval_inputs(self.p, "B")
        (self.p / "hf" / "index.html").write_text("<html>v2</html>")
        self.assertNotEqual(b, integrity.approval_inputs(self.p, "B"))

    def test_moving_the_channels_folder_keeps_fingerprints(self):
        stages = ("ingesta", "transcripcion", "corte-en-papel", "corte-aplicado", "subtitulos", "composicion", "render")
        before = {s: (integrity.inputs(self.p, s), integrity.outputs(self.p, s)) for s in stages}
        before["A"] = integrity.approval_inputs(self.p, "A")
        before["B"] = integrity.approval_inputs(self.p, "B")
        before["hf"] = editlib.hf_fingerprint(self.p)
        with tempfile.TemporaryDirectory() as other:
            moved = Path(other) / "en-otra-parte"
            shutil.copytree(self.ch.parent, moved)
            q = moved / self.p.resolve().relative_to(self.ch.parent)
            after = {s: (integrity.inputs(q, s), integrity.outputs(q, s)) for s in stages}
            after["A"] = integrity.approval_inputs(q, "A")
            after["B"] = integrity.approval_inputs(q, "B")
            after["hf"] = editlib.hf_fingerprint(q)
        self.assertEqual(before, after)

    def test_restamp_converts_saved_evidence_without_redoing_work(self):
        p, plats = self.p, ["tiktok"]
        st = {"version": 2, "fingerprints": {"check": editlib.hf_fingerprint(p, scheme=1),
                                             "revision": editlib.hf_fingerprint(p, scheme=2)},
              "stages": {"composicion": {"version": 3, "platforms": plats,
                                         "inputs": integrity.inputs(p, "composicion", 2),
                                         "outputs": integrity.outputs(p, "composicion", 2)},
                         "render": {"version": 3, "platforms": plats, "inputs": "otra cosa", "outputs": "x"}},
              "approvals": {"A": {"version": 2, "inputs": integrity.approval_inputs(p, "A", 2)},
                            "B": {"at": "2026-11-11T00:00:00"}}}
        new, changes = integrity.restamp(p, st, plats)
        self.assertEqual(new["fingerprints"]["check"], editlib.hf_fingerprint(p))
        self.assertEqual(new["fingerprints"]["revision"], editlib.hf_fingerprint(p))
        self.assertEqual(new["stages"]["composicion"]["inputs"], integrity.inputs(p, "composicion"))
        self.assertEqual(new["stages"]["render"]["inputs"], "otra cosa")       # cambió de verdad: se deja
        self.assertEqual(new["approvals"]["A"]["inputs"], integrity.approval_inputs(p, "A"))
        self.assertNotIn("version", new["approvals"]["B"])                       # anterior: no se certifica sola
        self.assertEqual(new["digest_scheme"], integrity.SCHEME)
        self.assertNotIn("digest_scheme", st)                                    # no modifica el original
        self.assertEqual(integrity.restamp(p, new, plats), (new, []))
        self.assertFalse(editlib.stage_dirty("check", p, {**new, "stages": {}}, plats)[0])


class Reapproval(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.p = Path(self.td.name) / "pieza"
        (self.p / "cut").mkdir(parents=True)
        (self.p / "cut" / "PAPER-CUT.md").write_text("# Corte\n")
        (self.p / "cut" / "cut-list.json").write_text('{"lines": [{"status": "keep", "text": "Hola"}]}')
        self.status = load_bin("status")

    def tearDown(self):
        self.td.cleanup()

    def reviewed(self, gate="A"):
        return {"inputs": integrity.approval_inputs(self.p, gate), "fingerprint": reviewlib.fingerprint(self.p, gate),
                "files": [], "decision": None}

    def test_reapproving_A_never_drops_B(self):
        st = {"approvals": {"A": {"version": 2, "inputs": integrity.approval_inputs(self.p, "A")}, "B": {"version": 2}},
              "reviews": {"A": self.reviewed()}}
        self.status.approve(self.p, st, "A", "otra vez")
        self.assertIn("B", st["approvals"])
        (self.p / "cut" / "cut-list.json").write_text('{"lines": [{"status": "drop", "text": "Hola"}]}')
        st["reviews"]["A"] = self.reviewed()
        self.status.approve(self.p, st, "A", "corte nuevo")
        self.assertIn("B", st["approvals"])            # se conserva el registro; su evidencia decide
        self.assertEqual(st["approval_history"][-1]["gate"], "A")

    def test_presenting_A_does_not_drop_B(self):
        from scripts.core import oslib as o
        o.write_json(self.p / "status.json", {"approvals": {"A": {"at": "2026-11-10T00:00:00"},
                                                             "B": {"at": "2026-11-11T00:00:00"}}})
        reviewlib.present(self.p, "A", no_open=True)
        st = json.loads((self.p / "status.json").read_text())
        self.assertEqual(sorted(st["approvals"]), ["B"])                  # A se presenta de nuevo; B se conserva

    def test_approving_A_after_presentation_keeps_B(self):
        st = {"approvals": {"B": {"version": 2}}, "reviews": {"A": self.reviewed()}}   # A quitada al presentarla
        self.status.approve(self.p, st, "A", "aprobada")
        self.assertEqual(sorted(st["approvals"]), ["A", "B"])

    def test_attest_recovers_last_approval_from_history(self):
        st = {"approvals": {}, "approval_history": [{"gate": "A", "approval": {"at": "2026-11-10", "note": "vieja"}}],
              "reviews": {"A": {**self.reviewed(), "decision": "approved"}}}
        self.status.attest(self.p, st, "A", "la persona lo confirmó")
        self.assertEqual(st["approvals"]["A"]["attested_from"]["note"], "vieja")

    def test_attest_needs_matching_approved_review(self):
        st = {"approvals": {"A": {"at": "2026-11-10T00:00:00", "note": "vieja"}}, "reviews": {}}
        with self.assertRaises(SystemExit):
            self.status.attest(self.p, st, "A", "la persona lo confirmó")
        st["reviews"]["A"] = {**self.reviewed(), "decision": "approved"}
        with self.assertRaises(SystemExit):
            self.status.attest(self.p, st, "A", "")                          # nota obligatoria
        self.status.attest(self.p, st, "A", "la persona lo confirmó")
        a = st["approvals"]["A"]
        self.assertEqual((a["version"], a["attested_from"]["note"]), (2, "vieja"))
        self.assertTrue(integrity.valid(self.p, "A", st))
        with self.assertRaises(SystemExit):
            self.status.attest(self.p, st, "A", "dos veces")


if __name__ == "__main__":
    unittest.main()
