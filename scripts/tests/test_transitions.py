"""Transiciones de superposición (`storyboard.json → transitions`, ADR 0028)."""
import re
import unittest

from scripts.composer import transitions as tr
from scripts.pipeline import storyboard
from scripts.tests.test_storyboard import ctx

ALL = [{"at": 2.0, "kind": "flash"}, {"at": 4.0, "kind": "light-leak"}, {"at": 6.0, "kind": "scribble"},
       {"at": 8.0, "kind": "word-wall", "word": "Agentes"}, {"at": 10.0, "kind": "glitch", "duration": 0.5},
       {"at": 12.0, "kind": "zoom-lines", "role": "accent2"}]


def check(items, cuts=(2.0, 4.0, 6.0, 8.0, 10.0, 12.0)):
    c = {**ctx(), "cuts": list(cuts)}
    return storyboard.validate({"platforms": {"tiktok": {}}, "transitions": items}, c)


class CompositionTests(unittest.TestCase):
    def test_nothing_without_transitions(self):
        self.assertIsNone(tr.composition({}))
        self.assertEqual(tr.host({}, 20), "")
        self.assertEqual(tr.cues({}, {"whoosh": {}}), [])

    def test_every_kind_renders_with_one_timeline(self):
        html = tr.composition({"transitions": ALL})
        self.assertIn('window.__timelines["transitions"] = tl;', html)
        self.assertEqual(html.count('data-composition-id="transitions"'), 1)
        for i in range(len(ALL)):
            self.assertIn(f'id="tr{i}', html)
        for banned in ("Math.random", "Date.now", "requestAnimationFrame", "repeat: -1"):
            self.assertNotIn(banned, html)
        self.assertIn("AGENTES", html)                                  # la palabra del muro, en mayúsculas
        self.assertIn("--tr-color: var(--accent2)", html)               # el rol elegido
        self.assertIn('data-composition-src="compositions/transitions.html"', tr.host({"transitions": ALL}, 20))

    def test_peak_lands_on_the_cut(self):
        html = tr.composition({"transitions": [{"at": 5.0, "kind": "flash", "duration": 0.6}]})
        self.assertIn("duration: 0.3, ease: \"power3.in\", immediateRender: false}, 4.7);", html)  # sube de 4.7 a 5.0
        self.assertIn('tl.to("#tr0", {opacity: 0, duration: 0.3, ease: "power2.out"}, 5.0);', html)

    def test_glitch_is_frame_stable(self):
        a = tr.composition({"transitions": [{"at": 3.0, "kind": "glitch"}]})
        b = tr.composition({"transitions": [{"at": 3.0, "kind": "glitch"}]})
        self.assertEqual(a, b)
        self.assertNotIn("backgroundColor", a)                          # colores fijos en el HTML, no tl.set con var()

    def test_scribble_covers_the_frame(self):
        d, length = tr._zigzag()
        xs = [float(x) for x in re.findall(r"(-?\d+) -?\d+", d)]
        self.assertLess(min(xs), -150)
        self.assertGreater(max(xs), tr.W + 150)
        self.assertGreater(length, 10000)

    def test_sound_cues(self):
        kit = {"whoosh": {}, "impact": {}}
        cues = tr.cues({"transitions": [{"at": 4.0, "kind": "light-leak", "duration": 0.8},
                                        {"at": 7.0, "kind": "flash"},
                                        {"at": 9.0, "kind": "glitch"},                 # zap no está en el kit
                                        {"at": 11.0, "kind": "scribble", "sfx": False}]}, kit)
        self.assertEqual([(c["sound"], c["at"]) for c in cues], [("whoosh", 3.6), ("impact", 7.0)])


class ValidationTests(unittest.TestCase):
    def test_good(self):
        errs, warns = check(ALL)
        self.assertEqual(errs, [])
        self.assertEqual([w for w in warns if "transitions" in w], [])

    def test_errors_together(self):
        errs, _ = check([{"at": 2.0, "kind": "wipe"}, {"at": 3.0, "kind": "flash", "duration": 2},
                         {"at": 6.0, "kind": "word-wall"}, {"at": 9.0, "kind": "flash", "role": "rojo"},
                         {"at": 19.9, "kind": "flash"}, {"at": 13.0, "kind": "flash", "sfx": "trompeta"}, {"kind": "flash"}])
        joined = "\n".join(errs)
        for frag in ("transitions[0].kind", "transitions[1].duration", "transitions[1]: a 1.00 s",
                     "transitions[2].word", "transitions[3].role", "se sale del video", "transitions[5].sfx",
                     "transitions[6].at"):
            self.assertIn(frag, joined)

    def test_warns_when_not_on_a_cut(self):
        _, warns = check([{"at": 5.0, "kind": "flash"}], cuts=(2.0, 9.0))
        self.assertTrue(any("no cae en un corte" in w for w in warns), warns)


if __name__ == "__main__":
    unittest.main()
