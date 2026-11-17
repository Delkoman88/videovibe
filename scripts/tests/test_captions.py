"""Tests de subtítulos (lógica pura). Correr: .venv/bin/python -m unittest discover -s scripts/tests -v"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pipeline import captions  # noqa: E402
from scripts.core import cutlib  # noqa: E402


def W(i, text, a, b):
    return {"id": f"w{i}", "w": text, "start": a, "end": b}


class TestCaptions(unittest.TestCase):
    def test_repair_from_remap_keeps_master_span_and_approved_words(self):
        base = [
            {"w": "¿no?", "start": 0.7, "end": 1.0},
            {"w": "frase", "start": 1.1, "end": 1.5},
            {"w": "mala", "start": 1.5, "end": 2.0},
        ]
        remap = [
            {"w": "¿no?", "start": 0.9, "end": 1.1},
            {"w": "cierre", "start": 1.2, "end": 1.6},
            {"w": "completo", "start": 1.6, "end": 1.9},
        ]
        got = captions.repair_from_remap(base, remap, 1.05, 2.1)
        self.assertEqual([w["w"] for w in got], ["¿no?", "cierre", "completo"])
        self.assertEqual(got[1]["start"], 1.1)
        self.assertEqual(got[-1]["end"], 2.0)
        self.assertEqual([w["id"] for w in got], ["w0", "w1", "w2"])

    def test_repair_prefix_uses_only_approved_cut_text(self):
        base = [{"w": "mal", "start": 0, "end": 1}, {"w": "después", "start": 2, "end": 3}]
        cut = {"lines": [{"id": "L1", "text": "texto correcto", "status": "keep"}]}
        cmap = {"segments": [{"out_in": 0, "out_out": 1, "lines": ["L1"]}]}
        got = captions.repair_prefix_from_approved_cut(base, cut, cmap, 1)
        self.assertEqual([w["w"] for w in got], ["texto", "correcto", "después"])
        self.assertEqual(got[1]["end"], 1.0)
    def test_imports_word_timestamps_from_whisper_json(self):
        data = {"transcription": [
            {"text": "", "offsets": {"from": 0, "to": 0}, "tokens": []},
            {"text": " música", "offsets": {"from": 420, "to": 910},
             "tokens": [{"text": " música", "p": 0.8}]},
        ]}
        self.assertEqual(captions.words_from_whisper_json(data), [
            {"w": "música", "start": 0.42, "end": 0.91, "p": 0.8},
        ])

    def test_regularizes_simultaneous_words_without_moving_anchor(self):
        words = [W(0, "Los", 6.3, 6.3), W(1, "que", 6.3, 6.3), W(2, "tocamos", 6.3, 6.49),
                 W(3, "y", 6.49, 6.6)]
        captions.regularize_zero_duration_words(words)
        self.assertEqual(words[0]["start"], 6.3)
        self.assertEqual(words[2]["end"], 6.49)
        self.assertGreater(words[0]["end"], words[0]["start"])
        self.assertGreaterEqual(words[1]["start"], words[0]["end"])

    def test_groups_never_overlap_and_break_on_sentence(self):
        ws = [W(0, "Hola", 0.2, 0.5), W(1, "mundo.", 0.5, 0.9), W(2, "Esto", 1.0, 1.2), W(3, "sigue", 1.2, 1.5)]
        gs = captions.build_groups(ws, max_words=4, max_chars=22, duration=2.0)
        self.assertEqual([g["text"] for g in gs], ["Hola mundo.", "Esto sigue"])
        for a, b in zip(gs, gs[1:]):
            self.assertLessEqual(a["out"], b["in"])
        self.assertGreaterEqual(gs[0]["in"], 0.1)  # nunca en 0 exacto

    def test_protected_term_not_split(self):
        ws = [W(0, "Esto", 0, .2), W(1, "es", .2, .3), W(2, "Laboratorio", .3, .7), W(3, "Virtual", .7, .9),
              W(4, "Abierto", .9, 1.3), W(5, "hasta", 1.3, 1.5)]
        gs = captions.build_groups(ws, max_words=4, max_chars=22, duration=2.0, vocab=["Laboratorio Virtual Abierto"])
        texts = [g["text"] for g in gs]
        self.assertTrue(any("Virtual Abierto" in t for t in texts), texts)

    def test_tidy_capitalizes_and_opens_question(self):
        ws = [{"w": "laboratorio"}, {"w": "virtual."}, {"w": "voy"}, {"w": "no?"}]
        captions.tidy(ws)
        self.assertEqual([w["w"] for w in ws], ["Laboratorio", "virtual.", "Voy", "¿no?"])


    def test_tidy_english_has_no_inverted_marks(self):
        import json
        en = json.loads((Path(__file__).resolve().parents[2] / "lang" / "en.json").read_text())
        ws = [{"w": "right?"}, {"w": "this"}]
        captions.tidy(ws, en)
        self.assertEqual([w["w"] for w in ws], ["Right?", "This"])


class TestCutRules(unittest.TestCase):
    def test_short_fragment_dropped(self):
        lines = [{"words": [{"w": "no?"}], "start": 1.0, "end": 1.22, "status": "keep"},
                 {"words": [{"w": "Hola"}, {"w": "a"}, {"w": "todos."}], "start": 2.0, "end": 3.0, "status": "keep"}]
        cutlib.mark_short_fragments(lines)
        self.assertEqual([l["status"] for l in lines], ["drop", "keep"])

    def test_connectors_only_line_dropped(self):
        lines = [{"words": [{"w": "y"}, {"w": "y"}], "start": 1.0, "end": 1.9, "status": "keep"}]
        cutlib.mark_lone_connectors(lines)
        self.assertEqual(lines[0]["status"], "drop")


if __name__ == "__main__":
    unittest.main()
