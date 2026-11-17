"""Efectos sobre la toma: validación, recortes con caché y capas en index.html (ADR 0025)."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import formats
from scripts.composer import fx as fxlayers
from scripts.pipeline import cutout, storyboard
from scripts.tests.test_storyboard import ctx

BRAND = {"highlight_roles": {"keyword": "accent", "data": "accent2"}}


def validate(fx, scenes=(), speech=((0.0, 5.0), (6.0, 9.0))):
    c = {**ctx(), "speech": list(speech), "formats": formats.registry(("biotech",))}
    return storyboard.validate({"fx": fx, "scenes": list(scenes), "platforms": {"tiktok": {}}}, c)


class ValidationTests(unittest.TestCase):
    def test_good_effects(self):
        errs, warns = validate([{"id": "a", "type": "text-behind", "in": 1, "out": 3, "text": "Hola"},
                                {"id": "b", "type": "freeze-cutout", "at": 5.1, "duration": 0.6, "label": "Yo"},
                                {"id": "c", "type": "subject-glow", "in": 10, "out": 12}])
        self.assertEqual(errs, [])

    def test_freeze_over_speech_is_rejected(self):
        errs, _ = validate([{"id": "b", "type": "freeze-cutout", "at": 6.5, "duration": 1}])
        self.assertTrue(any("regla 3" in e for e in errs), errs)

    def test_all_problems_together(self):
        errs, _ = validate([{"id": "a", "type": "text-behind", "in": 1, "out": 3},
                            {"id": "a", "type": "magia", "in": 1, "out": 2},
                            {"id": "c", "type": "subject-glow", "in": 2, "out": 14, "size": 9, "variant": "spin"},
                            {"id": "d", "type": "background-swap", "in": 2.5, "out": 4, "y": 1500}])
        for needle in ("text: obligatorio", "repetido", "no existe", "máximo 10 s", "size", "variant", "y:",
                       "se solapa"):
            self.assertTrue(any(needle in e for e in errs), (needle, errs))

    def test_effect_under_full_scene_warns(self):
        _, warns = validate([{"id": "a", "type": "subject-glow", "in": 8, "out": 9}],
                            scenes=[{"id": "s", "format": "dna-helix", "in": 7, "out": 10, "params": {}}])
        self.assertTrue(any("tapa la toma" in w for w in warns))


class CutoutTests(unittest.TestCase):
    def test_jobs_margin_and_kinds(self):
        sb = {"fx": [{"id": "a", "type": "text-behind", "in": 0.1, "out": 3}, {"id": "b", "type": "freeze-cutout", "at": 5},
                     {"id": "x", "type": "otro"}]}
        j = [(fx["id"], kind, a, b) for fx, kind, a, b in cutout.jobs(sb, 3.1)]
        self.assertEqual(j, [("a", "webm", 0.0, 3.1), ("b", "png", 5, 5)])

    def test_cache_is_reused_without_recomputing(self):
        with tempfile.TemporaryDirectory() as d:
            P = Path(d)
            (P / "cut").mkdir()
            (P / "cut" / "cut-map.json").write_text(json.dumps({"duration_s": 10, "segments": [
                {"src": "a", "src_in": 0, "src_out": 10}]}))
            (P / "cut" / "master-cut.mp4").write_text("x")
            sb = {"fx": [{"id": "a", "type": "subject-glow", "in": 1, "out": 2}]}
            fx, kind, a, b = cutout.jobs(sb, 10)[0]
            key = cutout._key(P, kind, a, b, cutout._interior(fx))
            cache = P / "work" / "cutout"
            cache.mkdir(parents=True)
            (cache / f"{key}.webm").write_text("v")
            (cache / f"{key}.json").write_text(json.dumps({"start": 0.8, "end": 2.2, "kind": "webm", "subject_top": 400}))
            res = cutout.ensure(P, sb)  # sin llamar a remove-background: viene de caché
            self.assertEqual(res["a"]["start"], 0.8)
            (P / "cut" / "cut-map.json").write_text(json.dumps({"duration_s": 10, "segments": [
                {"src": "a", "src_in": 0.5, "src_out": 10}]}))
            self.assertNotEqual(cutout._key(P, kind, a, b, True), key)  # otro corte, otra huella


class MarkupTests(unittest.TestCase):
    def test_no_fx_no_markup(self):
        self.assertEqual(fxlayers.markup({}, BRAND, {}), ("", ""))
        self.assertEqual(fxlayers.css({}), "")

    def test_layers_and_media_offset(self):
        sb = {"fx": [{"id": "t", "type": "text-behind", "in": 2.0, "out": 4.0, "text": "Hola *mundo*", "role": "data"}]}
        html, js = fxlayers.markup(sb, BRAND, {"t": {"start": 1.8, "subject_top": 500, "kind": "webm"}})
        self.assertLess(html.index('id="fxt-t"'), html.index('id="fxc-t"'))  # el texto va debajo de la persona
        self.assertIn('data-media-start="0.2"', html)
        self.assertIn("var(--accent2)", html)
        self.assertIn('tl.fromTo("#fxt-t .ch"', js)

    def test_auto_y_puts_text_behind_the_head(self):
        self.assertEqual(fxlayers.text_y({}, {"subject_top": 600}, 200), 490)
        self.assertEqual(fxlayers.text_y({}, {"subject_top": 50}, 200), 110)
        self.assertEqual(fxlayers.text_y({"y": 300}, {"subject_top": 600}, 200), 300)
        self.assertEqual(fxlayers.text_y({}, None, 200), 160)


if __name__ == "__main__":
    unittest.main()


class MatteTests(unittest.TestCase):
    """Estabilizador del recorte con cámara fija (scripts/pipeline/matte.py)."""

    def scene(self, moving_camera=False):
        import numpy as np
        from scripts.pipeline import matte
        rng = np.random.default_rng(3)
        T, h, w = 24, matte.SH, matte.SW
        bg = rng.integers(60, 200, (h + 40, w + 40, 3)).astype(np.uint8)
        rgb = np.empty((T, h, w, 3), np.uint8)
        alpha = np.zeros((T, h, w), np.uint8)
        yy, xx = np.mgrid[0:h, 0:w]
        body = ((yy - 160) / 70) ** 2 + ((xx - 67) / 40) ** 2 < 1
        for t in range(T):
            s = (t * 3) % 40 if moving_camera else 0
            rgb[t] = bg[s:s + h, s:s + w]
            rgb[t][body] = (40, 90, 40)
            alpha[t][body] = 255
            hand = ((yy - 120) / 10) ** 2 + ((xx - (30 + 3 * t)) / 10) ** 2 < 1   # mano que se mueve
            rgb[t][hand] = (220, 160, 130)
            alpha[t][hand] = 255
            if 5 <= t < 15:                                                     # «cortina» tomada por persona
                alpha[t][20:60, 95:130] = 255
                alpha[t][60:100, 100:110] = 255                                 # pegada al cuerpo
        return matte, rgb, alpha, body

    def test_spurious_background_is_removed_body_and_hand_kept(self):
        matte, rgb, alpha, body = self.scene()
        keep, info = matte.decide(rgb, alpha)
        self.assertTrue(info["applied"], info)
        self.assertFalse(keep[8][20:60, 95:130].any(), "la cortina sigue en el recorte")
        self.assertTrue(keep[8][body].all())
        self.assertTrue(keep[8][120, 30 + 24])  # la mano (t=8, x≈54)

    def test_faint_but_steady_body_is_kept(self):
        """Ropa oscura que el modelo ve tenue (opacidad < 0.5) pero siempre: no se quita (v3 la recortaba)."""
        matte, rgb, alpha, body = self.scene()
        import numpy as np
        h, w = alpha.shape[1:]
        yy, xx = np.mgrid[0:h, 0:w]
        sleeve = ((yy - 200) / 30) ** 2 + ((xx - 15) / 14) ** 2 < 1
        for t in range(len(alpha)):
            alpha[t][sleeve] = 100
            rgb[t][sleeve] = rgb[t][sleeve]   # igual al fondo: como la chamarra sobre la silla
        keep, info = matte.decide(rgb, alpha)
        self.assertTrue(keep[8][sleeve].all())

    def test_body_lost_for_a_few_frames_is_filled(self):
        """El modelo pierde un pedazo del cuerpo 6 cuadros: se rellena; la mano que se fue no deja hueco relleno."""
        matte, rgb, alpha, body = self.scene()
        lost = body.copy()
        lost[:, 67:] = False
        for t in range(10, 16):
            alpha[t][lost] = 0
        keep, info = matte.decide(rgb, alpha)
        self.assertTrue((keep[12][lost] == 2).mean() > 0.85, info)  # el filo de 1 punto queda como dice el modelo
        self.assertFalse((keep[12] == 2)[120, 25])  # donde estuvo la mano al principio ya es fondo

    def test_lost_piece_open_to_background_is_not_filled(self):
        """Un pedazo suelto que el modelo deja de ver (la silla tras la mano, un filo del cuadro) y da al fondo
        por casi todo su contorno no se rellena: saldría en cuadros de 8 px."""
        matte, rgb, alpha, body = self.scene()
        chair = (slice(40, 60), slice(10, 30))                                  # lejos del cuerpo, quieto
        for t in range(len(alpha)):
            rgb[t][chair] = (30, 30, 30)
            alpha[t][chair] = 255 if t < 8 or t >= 14 else 0
        keep, info = matte.decide(rgb, alpha)
        self.assertFalse((keep[10][chair] == 2).any(), info)

    def test_blurred_part_lost_for_two_frames_is_filled(self):
        """Movimiento rápido: un pedazo del cuerpo cambia de color (borroso) y el modelo lo pierde 2 cuadros; no es
        fondo, hay cuerpo antes y después: se rellena."""
        matte, rgb, alpha, body = self.scene()
        hole = (slice(150, 175), slice(55, 80))
        for t in (11, 12):
            alpha[t][hole] = 0
            rgb[t][hole] = (150, 120, 100)
        keep, info = matte.decide(rgb, alpha)
        self.assertTrue((keep[11][hole] == 2).mean() > 0.85, info)

    def test_glow_closes_holes_in_time(self):
        """Para el halo: un hueco de pocos cuadros dentro del cuerpo se rellena; el fondo de alrededor no."""
        import numpy as np
        from scripts.pipeline import matte
        T, h, w = 12, matte.SH, matte.SW
        alpha = np.zeros((T, h, w), np.uint8)
        alpha[:, 80:200, 30:100] = 255
        alpha[4:7, 120:160, 40:70] = 0                                         # el modelo pierde un pedazo
        keep = matte.fill_interior(np.ones((T, h, w), np.uint8), alpha)
        self.assertTrue((keep[5][120:160, 40:70] == 2).all())
        self.assertFalse((keep[5][:70] == 2).any())

    def test_moving_camera_is_left_untouched(self):
        matte, rgb, alpha, _ = self.scene(moving_camera=True)
        keep, info = matte.decide(rgb, alpha)
        self.assertIsNone(keep)
        self.assertFalse(info["applied"])


class DepthTests(unittest.TestCase):
    def test_depths(self):
        cut = {"t": {"start": 1.8, "subject_top": 500, "kind": "webm"}}
        base = {"id": "t", "type": "text-behind", "in": 2.0, "out": 5.0, "text": "Hola"}
        h_behind, _ = fxlayers.markup({"fx": [base]}, BRAND, cut)
        h_front, _ = fxlayers.markup({"fx": [{**base, "depth": "front"}]}, BRAND, cut)
        h_thr, js_thr = fxlayers.markup({"fx": [{**base, "depth": "through"}]}, BRAND, cut)
        self.assertNotIn("fxtf-t", h_behind)
        self.assertNotIn('id="fxt-t"', h_front)
        self.assertLess(h_front.index('id="fxc-t"'), h_front.index('id="fxtf-t"'))  # delante del recorte
        self.assertIn('id="fxt-t"', h_thr)
        self.assertIn('tl.to("#fxtf-t", {opacity: 0', js_thr)
        self.assertIn("data-layout-allow-overlap", h_thr)
        errs, _ = validate([{**base, "depth": "arriba"}])
        self.assertTrue(any(".depth" in e for e in errs))
