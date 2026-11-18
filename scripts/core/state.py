"""Estado versionado y bloqueo por pieza. Los lectores no escriben (ADR 0036)."""
import atexit
import contextlib
import functools
import json
import os
import signal
import subprocess
import tempfile
import uuid
from pathlib import Path

DEFAULTS = {"stage": None, "history": [], "approvals": {}, "renders": {}, "fingerprints": {}}
_HELD = {}  # "<pieza>:<tipo>" → archivo de bloqueo abierto por este proceso


def atomic(path, data):
    """Escribe bytes con temporal único + fsync + reemplazo atómico."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def load(P):
    """Lee status.json normalizado (sin escribir)."""
    f = Path(P) / "status.json"
    s = json.loads(f.read_text()) if f.exists() else {}
    s.setdefault("version", 2)
    for k, v in DEFAULTS.items():
        s.setdefault(k, type(v)() if isinstance(v, (list, dict)) else v)
    return s


def _inherit(P, key, path, owner):
    """Bloqueo heredado del proceso padre (bin/edit → etapa). Devuelve el archivo o None."""
    inherited = json.loads(os.environ.get("VIDEOVIBE_OPERATION", "{}"))
    if inherited.get("path") != str(P) or not owner.exists() or os.name == "nt":
        return None
    fd = inherited.get("fd")
    if json.loads(owner.read_text()) != inherited or not isinstance(fd, int):
        return None
    try:
        stat, disk = os.fstat(fd), path.stat()
    except OSError:
        return None
    if (stat.st_dev, stat.st_ino) != (disk.st_dev, disk.st_ino):
        return None
    return os.fdopen(os.dup(fd), "a+b")


def _acquire(f, path, P, kind):
    try:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                f.write(b"0")
                f.flush()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        raise RuntimeError(f"pieza ocupada: {P} ({kind})")


def _check_workers(folder, f, P):
    """Un trabajador de una operación anterior que sigue vivo mantiene la pieza ocupada."""
    for record in folder.glob("worker-*.json"):
        worker = json.loads(record.read_text())
        try:
            if os.name == "nt":
                raise RuntimeError("recuperación de trabajadores Windows pendiente de validación")
            os.killpg(worker["group"], 0)
        except ProcessLookupError:
            record.unlink(missing_ok=True)
        except BaseException:
            f.close()
            raise
        else:
            f.close()
            raise RuntimeError(f"pieza ocupada: trabajador activo en {P}")


@contextlib.contextmanager
def lock(P, kind="operation"):
    """Bloqueo exclusivo no bloqueante por pieza: «operation» (comandos) o «state» (transacciones)."""
    P = Path(P).resolve()
    key = f"{P}:{kind}"
    if key in _HELD:
        yield
        return
    folder = P / "work"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{kind}.lock"
    owner = folder / f"{kind}.owner.json"
    if kind == "operation":
        delegated = _inherit(P, key, path, owner)
        if delegated is not None:
            _HELD[key] = delegated
            try:
                yield
            finally:
                _HELD.pop(key, None)
                delegated.close()
            return
    f = path.open("a+b")
    f.seek(0)
    _acquire(f, path, P, kind)
    if kind == "operation":
        _check_workers(folder, f, P)
    _HELD[key] = f
    previous = os.environ.get("VIDEOVIBE_OPERATION")
    if kind == "operation":
        token = {"path": str(P), "pid": os.getpid(), "token": uuid.uuid4().hex, "fd": f.fileno()}
        atomic(owner, json.dumps(token).encode())
        os.environ["VIDEOVIBE_OPERATION"] = json.dumps(token)
    try:
        yield
    finally:
        if kind == "operation":
            owner.unlink(missing_ok=True)
            if previous is None:
                os.environ.pop("VIDEOVIBE_OPERATION", None)
            else:
                os.environ["VIDEOVIBE_OPERATION"] = previous
        _HELD.pop(key, None)
        f.close()


def hold(P):
    """Mantiene el bloqueo durante un comando CLI y sus subprocesos."""
    cm = lock(P)
    try:
        cm.__enter__()
    except RuntimeError as e:
        from scripts.core.oslib import die
        die(str(e), 1)
    atexit.register(cm.__exit__, None, None, None)


@contextlib.contextmanager
def transaction(P):
    """Leer-modificar-escribir status.json bajo bloqueo; se guarda al salir sin error."""
    with lock(P), lock(P, "state"):
        s = load(P)
        yield s
        s["version"] = 2
        atomic(Path(P) / "status.json", (json.dumps(s, ensure_ascii=False, indent=2) + "\n").encode())


def update(P, **fields):
    """Parche parcial: los dicts se fusionan en el primer nivel; el resto se reemplaza."""
    with transaction(P) as s:
        for k, v in fields.items():
            if isinstance(v, dict) and isinstance(s.get(k), dict):
                s[k].update(v)
            else:
                s[k] = v


def mutating(fn):
    @functools.wraps(fn)
    def wrapped(P, *args, **kwargs):
        with lock(P):
            return fn(P, *args, **kwargs)
    return wrapped


def invalidate(s, gate, reason, cascade=True):
    """Quita la aprobación (con `cascade`, A arrastra a B) y la guarda en approval_history.
    B guarda su propia evidencia (corte, subtítulos, HTML compilado): sin `cascade` deja de valer sola
    si el corte cambia."""
    for g in (("A", "B") if gate == "A" and cascade else (gate,)):
        old = s.setdefault("approvals", {}).pop(g, None)
        if old:
            s.setdefault("approval_history", []).append({"gate": g, "approval": old, "reason": reason})


def save(P, data):
    """Escritura de estado completo; para parches parciales usar update."""
    with transaction(P) as current:
        current.clear()
        current.update(data)
        for k, v in DEFAULTS.items():
            current.setdefault(k, type(v)() if isinstance(v, (list, dict)) else v)


def run(cmd, **kwargs):
    """Ejecuta trabajadores con bloqueo heredado y reserva de su grupo POSIX."""
    token = json.loads(os.environ.get("VIDEOVIBE_OPERATION", "{}"))
    if not token or f"{token.get('path')}:operation" not in _HELD:
        return subprocess.run(cmd, **kwargs)
    if os.name == "nt":
        raise RuntimeError("ejecución delegada Windows pendiente de validación; usa WSL")
    kwargs["pass_fds"] = tuple(set(kwargs.get("pass_fds", ())) | {token["fd"]})
    kwargs["start_new_session"] = True
    if kwargs.pop("capture_output", False):
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    check = kwargs.pop("check", False)
    timeout = kwargs.pop("timeout", None)
    payload = kwargs.pop("input", None)
    if payload is not None:
        kwargs["stdin"] = subprocess.PIPE
    record = Path(token["path"]) / "work" / f"worker-{uuid.uuid4().hex}.json"
    child = subprocess.Popen(cmd, **kwargs)
    try:
        atomic(record, json.dumps({"group": child.pid}).encode())
        stdout, stderr = child.communicate(payload, timeout=timeout)
        result = subprocess.CompletedProcess(cmd, child.returncode, stdout, stderr)
        if check:
            result.check_returncode()
        return result
    except BaseException:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()
        raise
    finally:
        try:
            os.killpg(child.pid, 0)
        except ProcessLookupError:
            record.unlink(missing_ok=True)
