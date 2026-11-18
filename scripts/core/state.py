"""Estado versionado y bloqueo por pieza. Los lectores no escriben."""
import atexit
import contextlib
import json
import os
from pathlib import Path
import tempfile
import uuid
import subprocess
import signal

_HELD = {}


def atomic(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
        temp=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    try: os.replace(temp,path)
    finally: temp.unlink(missing_ok=True)


def load(P):
    f=Path(P)/'status.json'
    s=json.loads(f.read_text()) if f.exists() else {}
    for k,v in {'version':2,'stage':None,'history':[],'approvals':{},'renders':{},'fingerprints':{}}.items():s.setdefault(k,v)
    return s


@contextlib.contextmanager
def lock(P, kind='operation'):
    P=Path(P).resolve();key=str(P)+':'+kind
    if key in _HELD:
        yield
        return
    folder=P/'work';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(kind+'.lock');owner=folder/(kind+'.owner.json')
    inherited=json.loads(os.environ.get('VIDEOVIBE_OPERATION','{}'))
    if kind == 'operation' and inherited.get('path') == str(P) and owner.exists():
        current = json.loads(owner.read_text())
        fd = inherited.get('fd')
        if current == inherited and isinstance(fd, int) and os.name != 'nt':
            try:
                stat = os.fstat(fd)
                valid = (stat.st_dev, stat.st_ino) == (path.stat().st_dev, path.stat().st_ino)
            except OSError:
                valid = False
            if valid:
                delegated = os.fdopen(os.dup(fd), 'a+b')
                _HELD[key] = delegated
                try:
                    yield
                finally:
                    _HELD.pop(key, None)
                    delegated.close()
                return
    f=path.open('a+b');f.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            if path.stat().st_size==0:f.write(b'0');f.flush()
            f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close();raise RuntimeError(f'pieza ocupada: {P} ({kind})')
    if kind == 'operation':
        for record in folder.glob('worker-*.json'):
            worker = json.loads(record.read_text())
            try:
                if os.name == 'nt':
                    raise RuntimeError('recuperación de trabajadores Windows pendiente de validación')
                os.killpg(worker['group'], 0)
            except ProcessLookupError:
                record.unlink(missing_ok=True)
            except BaseException:
                f.close()
                raise
            else:
                f.close()
                raise RuntimeError(f'pieza ocupada: trabajador activo en {P}')
    _HELD[key]=f;previous=os.environ.get('VIDEOVIBE_OPERATION')
    if kind=='operation':
        token={'path':str(P),'pid':os.getpid(),'token':uuid.uuid4().hex,'fd':f.fileno()}
        atomic(owner,json.dumps(token).encode());os.environ['VIDEOVIBE_OPERATION']=json.dumps(token)
    try:yield
    finally:
        if kind=='operation':
            owner.unlink(missing_ok=True)
            if previous is None:os.environ.pop('VIDEOVIBE_OPERATION',None)
            else:os.environ['VIDEOVIBE_OPERATION']=previous
        _HELD.pop(key,None);f.close()


def hold(P):
    """Mantiene el bloqueo durante un comando CLI y sus subprocesos."""
    cm=lock(P)
    try:cm.__enter__()
    except RuntimeError as e:
        from scripts.core.oslib import die
        die(str(e),1)
    atexit.register(cm.__exit__,None,None,None)


@contextlib.contextmanager
def transaction(P):
    with lock(P),lock(P,'state'):
        s=load(P)
        yield s
        s['version']=2
        atomic(Path(P)/'status.json',(json.dumps(s,ensure_ascii=False,indent=2)+'\n').encode())


def update(P, **fields):
    with transaction(P) as s:
        for k,v in fields.items():
            if isinstance(v,dict) and isinstance(s.get(k),dict):s[k].update(v)
            else:s[k]=v


def mutating(fn):
    import functools
    @functools.wraps(fn)
    def wrapped(P,*args,**kwargs):
        with lock(P):return fn(P,*args,**kwargs)
    return wrapped


def invalidate(s,gate,reason):
    for g in (('A','B') if gate=='A' else ('B',)):
        old=s.setdefault('approvals',{}).pop(g,None)
        if old:s.setdefault('approval_history',[]).append({'gate':g,'approval':old,'reason':reason})


def save(P,data):
    """Escritura de estado completo; para parches parciales usar update."""
    with transaction(P) as current:
        current.clear()
        current.update(data)
        for k,v in {'stage':None,'history':[],'approvals':{},'renders':{},'fingerprints':{}}.items():
            current.setdefault(k,v)


def run(cmd, **kwargs):
    """Ejecuta trabajadores con bloqueo heredado y reserva de su grupo POSIX."""
    token = json.loads(os.environ.get('VIDEOVIBE_OPERATION', '{}'))
    if not token or token.get('path') + ':operation' not in _HELD:
        return subprocess.run(cmd, **kwargs)
    if os.name == 'nt':
        raise RuntimeError('ejecución delegada Windows pendiente de validación; usa WSL')
    kwargs['pass_fds'] = tuple(set(kwargs.get('pass_fds', ())) | {token['fd']})
    kwargs['start_new_session'] = True
    capture = kwargs.pop('capture_output', False)
    if capture:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
    check = kwargs.pop('check', False)
    timeout = kwargs.pop('timeout', None)
    payload = kwargs.pop('input', None)
    if payload is not None:
        kwargs['stdin'] = subprocess.PIPE
    record = Path(token['path']) / 'work' / ('worker-' + uuid.uuid4().hex + '.json')
    child = subprocess.Popen(cmd, **kwargs)
    try:
        atomic(record, json.dumps({'group': child.pid}).encode())
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
