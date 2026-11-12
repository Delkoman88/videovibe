"""Tratamiento de voz: decide por medición, no toca lo que está bien y conserva la sincronía."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402
from scripts.audio import voice  # noqa: E402
from scripts.tests.support import say_voice_available  # noqa: E402

oslib.ensure_venv()
import numpy as np  # noqa: E402

SR = 48000


def say_voice(td):
    aiff = Path(td) / "v.aiff"
    subprocess.run(["say", "-v", "Paulina", "-o", str(aiff),
                    "Hola, soy un biólogo. Estoy construyendo un laboratorio de investigación con inteligencia "
                    "artificial. Sígueme para ver cómo sale."], check=True)
    return oslib.load_audio(aiff, SR)


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[1:] /= np.sqrt(f[1:])
    X[0] = 0
    x = np.fft.irfft(X, n)
    return x / np.sqrt(np.mean(x ** 2))


def peaking(x, f0, gain_db, q=1.0):
    """EQ de campana por FFT (para fabricar una voz «con barro»)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    bw = f0 / q
    g = 10 ** (gain_db * np.exp(-0.5 * ((f - f0) / (bw / 2)) ** 2) / 20)
    return np.fft.irfft(X * g, len(x))


def make_project(td, audio):
    P = Path(td) / "pieza"
    (P / "cut").mkdir(parents=True)
    wav = Path(td) / "a.wav"
    data = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())
    subprocess.run([oslib.FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30",
                    "-i", str(wav), "-shortest", "-c:v", "libx264", "-c:a", "aac", "-b:a", "256k",
                    str(P / "cut" / "master-cut.mp4")], check=True)
    return P


def with_pauses(v):
    gap = np.zeros(int(0.8 * SR))
    return np.concatenate([gap, v * 0.5, gap, v * 0.5, gap])


@unittest.skipUnless(say_voice_available(), "requiere `say` con audio real (no disponible en sandbox)")
class TestVoice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.mkdtemp()
        cls.v = say_voice(cls.td)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.td)

    def run_voice(self, audio, **cfg):
        with tempfile.TemporaryDirectory() as td:
            P = make_project(td, audio)
            out, rep = voice.ensure_voice(P, voice.config(P, {}, {"voice": cfg}))
            a = oslib.load_audio(P / "cut" / "master-cut.mp4", SR)
            b = oslib.load_audio(out, SR)
            return rep, a, b

    def test_noisy_voice_gets_denoised(self):
        x = with_pauses(self.v)
        x = x + pink(len(x), np.random.default_rng(1)) * 10 ** (-40 / 20)
        rep, a, b = self.run_voice(x)
        steps = {s["step"]: s["filter"] for s in rep["chain"]}
        self.assertTrue(steps["denoise"], rep["chain"])
        self.assertAlmostEqual(rep["before"]["noise_db"], -40, delta=4)
        # pausas (percentil 5) más bajas respecto a la voz que en el original
        da, db_ = oslib.rms_db(a, SR), oslib.rms_db(b, SR)
        rel = lambda d: np.percentile(d, 95) - np.percentile(d, 5)  # noqa: E731
        self.assertGreater(rel(db_), rel(da) + 3)

    def test_clean_voice_is_not_denoised(self):
        x = with_pauses(self.v) + pink(len(with_pauses(self.v)), np.random.default_rng(2)) * 10 ** (-75 / 20)
        rep, _, _ = self.run_voice(x)
        den = next(s for s in rep["chain"] if s["step"] == "denoise")
        self.assertIsNone(den["filter"], den)

    def test_muddy_voice_gets_low_mid_cut_within_limits(self):
        x = peaking(with_pauses(self.v), 280, 9.0)
        rep, _, _ = self.run_voice(x)
        eqs = [s for s in rep["chain"] if s["step"] == "eq" and s["filter"] and "f=280" in s["filter"]]
        self.assertTrue(eqs, rep["chain"])
        for s in rep["chain"]:
            if s["step"] == "eq" and s["filter"]:
                g = float(s["filter"].split("g=")[1].split(":")[0])
                self.assertLessEqual(abs(g), voice.LIMITS["natural"]["eq_db"])

    def test_same_length_and_deterministic(self):
        x = with_pauses(self.v)
        with tempfile.TemporaryDirectory() as td:
            P = make_project(td, x)
            cfg = voice.config(P, {}, {})
            out, _ = voice.ensure_voice(P, cfg)
            d0, _ = voice.n_samples(P / "cut" / "master-cut.mp4")
            d1, _ = voice.n_samples(out)
            self.assertAlmostEqual(d0, d1, delta=0.002)
            first = out.read_bytes()
            voice.ensure_voice(P, cfg, force=True)
            self.assertEqual(first, out.read_bytes())

    def test_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            P = make_project(td, with_pauses(self.v))
            out, rep = voice.ensure_voice(P, voice.config(P, {"voice": {"enabled": False}}, {}))
            self.assertIsNone(out)
            self.assertFalse(rep["enabled"])

    def test_precedence_piece_over_channel(self):
        cfg = voice.config(Path("."), {"voice": {"strength": "fuerte", "denoise": False}}, {"voice": {"denoise": True}})
        self.assertEqual(cfg["strength"], "fuerte")
        self.assertTrue(cfg["denoise"])


if __name__ == "__main__":
    unittest.main()
