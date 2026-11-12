import sys
"""Comprobaciones del entorno para pruebas que dependen de herramientas de macOS."""
import functools
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


@functools.lru_cache(maxsize=None)
def say_voice_available(voice="Paulina"):
    """`say` puede terminar en 0 y crear un AIFF vacío dentro de un sandbox."""
    if not shutil.which("say") or not shutil.which("ffprobe"):
        return False
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / "probe.aiff"
        try:
            made = subprocess.run(["say", "-v", voice, "-o", str(output), "Prueba de voz."],
                                  capture_output=True, timeout=15)
            if made.returncode or not output.exists() or output.stat().st_size < 2048:
                return False
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "json", str(output)], capture_output=True, text=True, timeout=15)
            return probe.returncode == 0 and float(json.loads(probe.stdout)["format"]["duration"]) > 0.25
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            return False
