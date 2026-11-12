"""Tests del corte. Rápidos (lógica pura) + uno de punta a punta con voz sintética (macOS `say`).

Correr desde la raíz:  .venv/bin/python -m unittest discover -s scripts/tests -v
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
ROOT = SCRIPTS.parent
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import cutlib  # noqa: E402
from scripts.pipeline import transcribe  # noqa: E402
from scripts.tests.support import say_voice_available  # noqa: E402


def W(text, a, b):
    return {"w": text, "start": a, "end": b, "p": 1.0}


class TestCutLogic(unittest.TestCase):
    def test_retake_keeps_last(self):
        words = [W("Para", 0, .2), W("eso", .2, .4), W("necesito", .4, .8), W("un", .8, .9), W("agente.", .9, 1.3),
                 W("Para", 2, 2.2), W("eso", 2.2, 2.4), W("necesito", 2.4, 2.8), W("un", 2.8, 2.9),
                 W("agente", 2.9, 3.3), W("que", 3.3, 3.4), W("lea.", 3.4, 3.8)]
        lines = cutlib.split_lines("a", words)
        for i, ln in enumerate(lines, 1):
            ln["id"], ln["status"], ln["reason"] = f"L{i}", "keep", ""
        cutlib.mark_retakes(lines)
        self.assertEqual([l["status"] for l in lines], ["drop", "keep"])
        self.assertEqual(lines[0]["kept_as"], "L2")

    def test_different_sentences_not_retake(self):
        a = {"src": "a", "words": [W("El", 0, .1), W("primer", .1, .4), W("resultado", .4, .9)]}
        b = {"src": "a", "words": [W("El", 1, 1.1), W("segundo", 1.1, 1.4), W("paso", 1.4, 1.9)]}
        self.assertFalse(cutlib.is_retake(a, b))

    def test_filler_is_own_line(self):
        lines = cutlib.split_lines("a", [W("Hola.", 0, .4), W("eh", 1, 1.2), W("Seguimos.", 1.5, 2)])
        self.assertEqual([bool(l.get("filler")) for l in lines], [False, True, False])

    def test_lone_connector_dropped(self):
        lines = cutlib.split_lines("a", [W("Quiero", 0, .3), W("probarlo.", .3, .9), W("y", 1.8, 2.0),
                                         W("pues", 2.9, 3.1), W("empiezo.", 3.1, 3.6)])
        for i, ln in enumerate(lines, 1):
            ln["id"], ln["status"], ln["reason"] = f"L{i}", "keep", ""
        cutlib.mark_lone_connectors(lines)
        self.assertEqual([l["status"] for l in lines], ["keep", "drop", "keep"])

    def test_segments_keep_pause_without_eating_next_voice(self):
        lines = [{"id": "L1", "src": "a", "start": 0.0, "end": 1.0, "status": "keep"},
                 {"id": "L2", "src": "a", "start": 1.2, "end": 2.0, "status": "keep"},
                 {"id": "L3", "src": "a", "start": 5.0, "end": 6.0, "status": "keep"}]
        isl = {"a": [[0, 1.0], [1.2, 2.0], [5.0, 6.0]]}
        segs = cutlib.build_segments(lines, isl, pause_s=0.35)
        self.assertEqual(len(segs), 2)                    # L1+L2 unidos, L3 aparte
        self.assertAlmostEqual(segs[0]["out"], 2.35)      # pausa conservada
        self.assertAlmostEqual(segs[0]["in"], 0.0)        # no se come la primera palabra
        self.assertLessEqual(segs[1]["in"], 5.0)

    def test_align_handles_vad_absorbed_silence(self):
        # whisper+VAD: la palabra junto a un silencio "absorbe" el silencio (inicio/fin falsos)
        words = [W("Hola", 0, .3), W("mundo.", .3, 2.5), W("Eh", 2.5, 4.1), W("Sigo", 4.1, 4.4), W("aquí.", 4.4, 4.9)]
        islands = [[0, .8], [3.0, 3.25], [4.0, 4.9]]
        self.assertEqual(transcribe.align(words, islands), [(0, 2), (2, 3), (3, 5)])


@unittest.skipUnless(say_voice_available() and shutil.which("whisper-cli") and shutil.which("ffmpeg")
                     and (ROOT / "models" / "ggml-large-v3-turbo-q5_0.bin").exists(),
                     "requiere macOS say, whisper-cli, ffmpeg y el modelo")
class TestEndToEnd(unittest.TestCase):
    """Corte de punta a punta en un canal temporal creado desde channels/_template, en dos idiomas."""

    CASES = {
        "es": {"voice": "Paulina", "first": "hoy", "last": "funciona", "once": "necesito",
               "text": "Hoy voy a construir un laboratorio virtual. [[slnc 1800]] Para eso necesito un agente que lea "
                       "[[slnc 900]] Para eso necesito un agente que lea artículos científicos. [[slnc 1500]] eh "
                       "[[slnc 700]] El primer resultado es preliminar. [[slnc 2000]] Sígueme para ver si funciona."},
        "en": {"voice": "Samantha", "first": "today", "last": "works", "once": "need",
               "text": "Today I am building a virtual lab. [[slnc 1800]] For that I need an agent that reads "
                       "[[slnc 900]] For that I need an agent that reads scientific papers. [[slnc 1500]] um "
                       "[[slnc 700]] The first result is preliminary. [[slnc 2000]] Follow me to see if it works."},
    }

    def run_case(self, code):
        case = self.CASES[code]
        with tempfile.TemporaryDirectory() as td:
            chan = Path(td) / "canal-prueba"
            shutil.copytree(ROOT / "channels" / "_template", chan)
            cfg = json.loads((chan / "channel.json").read_text())
            cfg.update({"id": "canal-prueba", "name": "Canal de prueba", "language": code})
            (chan / "channel.json").write_text(json.dumps(cfg))
            P = chan / "projects" / "pieza"
            (P / "raw").mkdir(parents=True)
            aiff = Path(td) / "voz.aiff"
            subprocess.run(["say", "-v", case["voice"], "-o", str(aiff), case["text"]], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30", "-i", str(aiff),
                            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(P / "raw" / "toma.mp4")],
                           check=True)
            py = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv").exists() else sys.executable

            def step(name):
                r = subprocess.run([py, str(SCRIPTS / "pipeline" / name.replace("-", "_")), "--project", str(P)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"{code} {name}: {r.stdout}{r.stderr}")
                return json.loads(r.stdout)

            step("ingest.py")
            step("transcribe.py")
            pc = step("paper_cut.py")
            reasons = sorted(d["reason"] for d in pc["dropped"])
            self.assertIn("retoma", reasons, code)
            self.assertTrue({"muletilla", "sonido sin texto", "fragmento corto", "conector suelto"} & set(reasons), f"{code}: {reasons}")
            ac = step("apply_cut.py")
            self.assertTrue(ac["ok"])
            self.assertLess(ac["duration_s"], pc["source_s"] - 4)
            t = json.loads((P / "transcript" / "master-cut.remap.json").read_text())
            self.assertEqual(t["language"], code)
            words = [w["w"].lower().strip(".,¿?") for w in t["words"]]
            self.assertEqual(words[0], case["first"], f"{code}: {words}")
            self.assertEqual(words[-1], case["last"], f"{code}: {words}")
            self.assertEqual(words.count(case["once"]), 1, f"{code}: la retoma no debe estar")
            self.assertEqual(json.loads((P / "status.json").read_text())["stage"], "corte-aplicado")

    def test_pipeline_cut_es(self):
        self.run_case("es")

    @unittest.skipUnless(say_voice_available("Samantha"), "requiere voz Samantha con audio real")
    def test_pipeline_cut_en(self):
        self.run_case("en")


if __name__ == "__main__":
    unittest.main()


class TestWhisperCpuFallback(unittest.TestCase):
    """Si whisper falla con GPU (sandbox de un agente, máquina sin GPU), se reintenta sin GPU."""

    def test_retries_without_gpu_once(self):
        import importlib
        import os
        import stat
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "whisper-cli"
            calls = Path(td) / "calls.txt"
            fake.write_text(f"""#!/bin/sh
echo "$@" >> {calls}
case " $* " in *" -ng "*) ;; *) echo "GGML_ASSERT(buffer) failed" >&2; exit 134;; esac
while [ $# -gt 0 ]; do [ "$1" = "-of" ] && OUT="$2"; shift; done
echo '{{"transcription": [{{"text": "hola", "offsets": {{"from": 0, "to": 500}}, "tokens": []}}]}}' > "$OUT.json"
""")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            old = os.environ["PATH"]
            os.environ["PATH"] = f"{td}:{old}"
            try:
                from scripts.pipeline import transcribe
                importlib.reload(transcribe)
                w1 = transcribe.whisper_words(Path(td) / "a.wav", Path(td) / "m.bin", "", vad=False)
                w2 = transcribe.whisper_words(Path(td) / "a.wav", Path(td) / "m.bin", "", vad=False)
            finally:
                os.environ["PATH"] = old
            self.assertEqual([w["w"] for w in w1 + w2], ["hola", "hola"])
            lines = calls.read_text().splitlines()
            self.assertEqual(len(lines), 3, "1 intento con GPU + 1 reintento + la 2.ª llamada ya sin GPU")
            self.assertNotIn("-ng", lines[0])
            self.assertTrue(all("-ng" in l for l in lines[1:]))
            self.assertTrue(transcribe._CPU_ONLY["fallback"])


class TestFfmpegFilterScript(unittest.TestCase):
    """ffmpeg ≥ 7 usa `-/filter_complex <archivo>`; ffmpeg 6 (Ubuntu 24.04) solo `-filter_complex_script`."""

    def test_version_parsing(self):
        from scripts.core import oslib
        self.assertEqual(oslib.ffmpeg_major("ffmpeg version 9.0.2 Copyright (c) 2000-2026"), 9)
        self.assertEqual(oslib.ffmpeg_major("ffmpeg version 6.1.1-3ubuntu5 Copyright"), 6)
        self.assertEqual(oslib.ffmpeg_major("ffmpeg version n7.1 Copyright"), 7)
        self.assertIsNone(oslib.ffmpeg_major("ffmpeg version N-112233-gabcdef Copyright"))

    def test_args_match_installed_ffmpeg(self):
        import subprocess
        from scripts.core import oslib
        args = oslib.filter_script_args("g.txt")
        self.assertEqual(args[1], "g.txt")
        first = subprocess.run([oslib.FFMPEG, "-version"], capture_output=True, text=True).stdout.splitlines()[0]
        major = oslib.ffmpeg_major(first)
        self.assertEqual(args[0], "-filter_complex_script" if major is not None and major < 7 else "-/filter_complex")

