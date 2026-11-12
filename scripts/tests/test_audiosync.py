"""Micrófono externo: sincronización (desfase, deriva, cobertura) y uso en el corte de punta a punta."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

oslib.ensure_venv()
import numpy as np  # noqa: E402

from scripts.audio import audiosync  # noqa: E402
from scripts.tests.support import say_voice_available  # noqa: E402

SR = audiosync.SR
TEXT = ("Hola, soy biólogo y estoy construyendo un laboratorio de investigación biomédica con inteligencia "
        "artificial. Voy a documentar todo el proceso, los avances, los errores y también cuando la inteligencia "
        "artificial se equivoque. Sígueme para ver cómo sale este proyecto y comenta qué investigar primero.")


def phone(x, rng):
    """Simula el audio del teléfono: eco del cuarto, banda telefónica y ruido."""
    ir = rng.standard_normal(int(0.3 * SR)) * np.exp(-np.arange(int(0.3 * SR)) / SR / 0.06)
    ir[0] = 3
    y = np.convolve(x, ir)[:len(x)]
    X = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / SR)
    X[(f < 300) | (f > 3400)] *= 0.1
    y = np.fft.irfft(X, len(y))
    return y / np.abs(y).max() + 0.02 * rng.standard_normal(len(y))


def mic_of(base, off, ppm, extra_s, rng):
    """Micrófono: la voz limpia con t_mic = t_cam·(1+ppm) + off."""
    n = len(base) + int((abs(off) + extra_s) * SR)
    src = (np.arange(n) / SR - off) / (1 + ppm * 1e-6)
    return np.interp(src * SR, np.arange(len(base)), base, left=0, right=0) + 0.003 * rng.standard_normal(n)


@unittest.skipUnless(say_voice_available(), "requiere `say` con audio real (no disponible en sandbox)")
class TestSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.mkdtemp()
        aiff = Path(cls.td) / "v.aiff"
        subprocess.run(["say", "-v", "Paulina", "-o", str(aiff), TEXT], check=True)
        v = oslib.load_audio(aiff, SR)
        cls.base = np.concatenate([np.zeros(SR // 2), v, np.zeros(SR)])
        cls.cam = phone(cls.base, np.random.default_rng(1))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.td)

    def test_offsets_and_drift(self):
        rng = np.random.default_rng(2)
        for off, ppm in ((3.217, 0), (3.217, 80), (0.4, -120)):
            r = audiosync.sync(self.cam, mic_of(self.base, off, ppm, 3, rng))
            self.assertTrue(r["paired"], (off, ppm, r))
            self.assertAlmostEqual(r["offset_s"], off, delta=0.002)
            self.assertAlmostEqual(r["drift_ppm"], ppm, delta=15)

    def test_mic_started_late_covers_part(self):
        r = audiosync.sync(self.cam, mic_of(self.base, -1.5, 0, 3, np.random.default_rng(3)))
        self.assertTrue(r["paired"], r)
        self.assertAlmostEqual(r["offset_s"], -1.5, delta=0.002)
        self.assertAlmostEqual(r["covers_s"][0], 1.5, delta=0.01)
        m = {**r}
        self.assertFalse(audiosync.covered(m, 0.5, 1.2))
        self.assertTrue(audiosync.covered(m, 3.0, 5.0))

    def test_one_mic_two_takes(self):
        rng = np.random.default_rng(4)
        half = len(self.base) // 2
        take1, take2 = self.base[:half], self.base[half:]
        mic = np.concatenate([np.zeros(2 * SR), take1, np.zeros(3 * SR), take2, np.zeros(SR)])
        mic += 0.003 * rng.standard_normal(len(mic))
        r1 = audiosync.sync(phone(take1, rng), mic)
        r2 = audiosync.sync(phone(take2, rng), mic)
        self.assertTrue(r1["paired"] and r2["paired"], (r1, r2))
        self.assertAlmostEqual(r1["offset_s"], 2.0, delta=0.002)
        self.assertAlmostEqual(r2["offset_s"], 2.0 + half / SR + 3.0, delta=0.002)

    def test_unrelated_is_not_paired(self):
        rng = np.random.default_rng(5)
        other = phone(self.base[::-1].copy(), rng)
        self.assertFalse(audiosync.sync(self.cam, np.concatenate([other, other]))["paired"])
        self.assertFalse(audiosync.sync(self.cam, 0.1 * rng.standard_normal(len(self.cam) * 2))["paired"])

    def test_align_and_residual(self):
        m = audiosync.sync(self.cam, mic_of(self.base, 2.0, 60, 2, np.random.default_rng(6)))
        aligned = audiosync.align(mic_of(self.base, 2.0, 60, 2, np.random.default_rng(6)), m, len(self.cam))
        r = audiosync.residual(self.cam, aligned, 5.0, 9.0)
        self.assertIsNotNone(r)
        self.assertLess(abs(r), 2.0)


def write_wav(path, x, sr):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


@unittest.skipUnless(say_voice_available() and shutil.which("whisper-cli")
                     and (ROOT / "models" / "ggml-large-v3-turbo-q5_0.bin").exists(),
                     "requiere macOS say, whisper-cli y el modelo")
class TestMicEndToEnd(unittest.TestCase):
    def test_ingest_pairs_and_cut_uses_mic(self):
        with tempfile.TemporaryDirectory() as td:
            chan = Path(td) / "canal-prueba"
            shutil.copytree(ROOT / "channels" / "_template", chan)
            cfg = json.loads((chan / "channel.json").read_text())
            cfg.update({"id": "canal-prueba", "name": "Canal de prueba", "language": "es"})
            (chan / "channel.json").write_text(json.dumps(cfg))
            P = chan / "projects" / "pieza"
            (P / "raw").mkdir(parents=True)
            aiff = Path(td) / "v.aiff"
            subprocess.run(["say", "-v", "Paulina", "-o", str(aiff), TEXT], check=True)
            hi = 48000
            v = oslib.load_audio(aiff, hi)
            base = np.concatenate([np.zeros(hi // 2), v, np.zeros(hi)])
            rng = np.random.default_rng(7)
            # cámara: banda telefónica (sin agudos) + ruido; micrófono: voz completa, empieza 2.5 s antes
            X = np.fft.rfft(base)
            f = np.fft.rfftfreq(len(base), 1 / hi)
            X[(f < 300) | (f > 3400)] *= 0.05
            cam = np.fft.irfft(X, len(base))
            cam = 0.5 * cam / np.abs(cam).max() + 0.01 * rng.standard_normal(len(cam))
            mic = np.concatenate([np.zeros(int(2.5 * hi)), base * 0.5, np.zeros(2 * hi)])
            write_wav(Path(td) / "cam.wav", cam, hi)
            write_wav(P / "raw" / "lavalier.wav", mic, hi)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30",
                            "-i", str(Path(td) / "cam.wav"), "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", str(P / "raw" / "toma.mp4")], check=True)
            py = str(ROOT / ".venv" / "bin" / "python")

            def step(name):
                r = subprocess.run([py, str(SCRIPTS / "pipeline" / name.replace("-", "_")), "--project", str(P)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"{name}: {r.stdout}{r.stderr}")
                return json.loads(r.stdout)

            step("ingest.py")
            media = {m["id"]: m for m in json.loads((P / "media.json").read_text())["items"]}
            self.assertEqual(media["lavalier"]["kind"], "mic")
            self.assertAlmostEqual(media["toma"]["mic"]["offset_s"], 2.5, delta=0.03)  # AAC añade ~20 ms
            step("transcribe.py")
            self.assertFalse((P / "transcript" / "lavalier.json").exists(), "el micro no se transcribe aparte")
            step("paper_cut.py")
            ac = step("apply_cut.py")
            self.assertTrue(ac["ok"])
            self.assertGreater(ac["audio"]["mic"], 0)
            self.assertEqual(ac["audio"]["camara"], 0, ac["audio"])
            # el master tiene los agudos del micrófono (la cámara los había perdido)
            # el fondo del master es el del micrófono (limpio), no el ruido constante de la cámara
            def floor_db(path):
                return float(np.percentile(oslib.rms_db(oslib.load_audio(path, hi), hi), 5))
            self.assertLess(floor_db(P / "cut" / "master-cut.mp4"), floor_db(P / "raw" / "toma.mp4") - 15)


if __name__ == "__main__":
    unittest.main()
