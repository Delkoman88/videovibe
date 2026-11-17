"""Ritmo: rejilla de golpes, selección por compás, efectos al ritmo y avisos de sincronía (ADR 0026)."""
import unittest

import numpy as np

import formats
from scripts.composer import beat as beatlayers
from scripts.pipeline import beats, storyboard
from scripts.tests.test_storyboard import ctx

DATA = {"beats": [round(0.5 * k, 3) for k in range(40)], "downbeats": [round(2.0 * k, 3) for k in range(10)]}


class GridTests(unittest.TestCase):
    def test_phase_from_onsets_with_window_center(self):
        bpm, phase = 120.0, 0.23
        env = np.zeros(3000)
        for t in np.arange(phase, 29, 60 / bpm):
            env[int(round((t - beats.ENV_CENTER) * 100))] = 1.0
        g = beats.grid(bpm, env, 30)
        self.assertAlmostEqual(g[0], phase, delta=0.011)
        self.assertAlmostEqual(g[1] - g[0], 0.5, delta=0.001)

    def test_pick_every(self):
        self.assertEqual(beats.pick(DATA, 1.0, 3.0, "beat"), [1.0, 1.5, 2.0, 2.5])
        self.assertEqual(beats.pick(DATA, 1.0, 3.0, "half"), [1.0, 2.0])
        self.assertEqual(beats.pick(DATA, 0.0, 9.0, "bar"), [0.0, 2.0, 4.0, 6.0, 8.0])
        self.assertEqual(beats.pick(DATA, 0.0, 9.0, "2bars"), [0.0, 4.0, 8.0])


class MarkupTests(unittest.TestCase):
    def test_nothing_without_beat_fx(self):
        self.assertEqual(beatlayers.markup({}, DATA), ("", "", ""))

    def test_pulse_and_strobe(self):
        op, close, js = beatlayers.markup({"beat_fx": [{"in": 0, "out": 4, "fx": "pulse", "every": "bar"},
                                                       {"in": 4, "out": 6, "fx": "strobe", "every": "beat"}]}, DATA)
        self.assertIn('id="beatwrap"', op)
        self.assertIn('id="beatflash"', close)
        self.assertEqual(js.count('tl.fromTo("#beatwrap", {scale:'), 2)  # compases en 0 y 2
        self.assertEqual(js.count("backgroundColor: vvBeatColor"), 4)   # golpes en 4, 4.5, 5, 5.5
        self.assertNotIn("immediateRender: true", js)


class ValidationTests(unittest.TestCase):
    def run_v(self, sb, **extra):
        c = {**ctx(), "formats": formats.registry(("biotech",)), "speech": [(0.0, 3.0)], **extra}
        return storyboard.validate({"platforms": {"tiktok": {}}, **sb}, c)

    def test_errors_together(self):
        errs, _ = self.run_v({"beat_fx": [{"in": 1, "out": 4, "fx": "boom", "every": "nunca", "strength": 3},
                                          {"in": 3, "out": 5, "fx": "flash"}]})
        for needle in (".fx:", ".every:", ".strength:", "se solapa"):
            self.assertTrue(any(needle in e for e in errs), (needle, errs))

    def test_warnings_speech_and_snap(self):
        _, warns = self.run_v({"beat_fx": [{"in": 0, "out": 2, "fx": "shake", "strength": 0.9}],
                               "scenes": [{"id": "s", "format": "dna-helix", "in": 5.27, "out": 7, "params": {}}],
                               "audio": {"music": {"track": "pista"}}},
                              beats=[5.0, 5.5, 6.0], beat_snap=True)
        self.assertTrue(any("mientras se habla" in w for w in warns), warns)
        self.assertTrue(any("del golpe más cercano" in w for w in warns), warns)


if __name__ == "__main__":
    unittest.main()
