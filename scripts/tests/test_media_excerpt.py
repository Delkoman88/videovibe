import hashlib
import tempfile
import unittest
import wave
from pathlib import Path
from scripts.core import oslib
from scripts.tools.media_excerpt import extract


class MediaExcerptTests(unittest.TestCase):
    def test_synchronized_excerpt_and_source_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); source = p/'source.mp4'
            oslib.run([oslib.FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', 'color=red:s=90x160:r=30:d=2',
                       '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2',
                       '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(source)])
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            v, a = p/'clip.mp4', p/'clip.wav'
            extract(source, .2, 1.5, .08, .5, v, a)
            self.assertAlmostEqual(float(oslib.ffprobe(v)['format']['duration']), 1.5, delta=.05)
            with wave.open(str(a)) as wav:
                self.assertEqual(wav.getnframes(), 72000)
                self.assertEqual(wav.getframerate(), 48000)
                import numpy as np
                samples = np.frombuffer(wav.readframes(72000), dtype='<i2').reshape(-1, 2).astype(float)
                self.assertLess(abs(samples[-240:]).mean(), abs(samples[24000:24240]).mean() * .05)
            self.assertEqual(original, hashlib.sha256(source.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError, 'ya existen'):
                extract(source, .2, 1.5, .08, .5, v, a)

    def test_invalid_intervals_and_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for start, duration, fade in [(-1, 1, .1), (0, 0, .1), (0, 1, 2), (float('nan'), 1, .1)]:
                with self.assertRaises(ValueError):
                    extract(p/'input', start, duration, fade, fade, p/'out.mp4', p/'out.wav')
            with self.assertRaises(ValueError):
                extract(p/'input', 0, 1, 0, 0, p/'input', p/'out.wav')
