"""Own exactly one encoder child per attempt; cancellation waits for its exit."""
from dataclasses import dataclass, field
import subprocess
import tempfile
import threading
import time
from types import SimpleNamespace


class Cancelled(RuntimeError):
    pass


@dataclass
class Control:
    attempt: str
    event: threading.Event = field(default_factory=threading.Event)
    process: object = None
    stopped: bool = False
    terminated: bool = False

    def check(self):
        if self.event.is_set():
            raise Cancelled('Render cancelado; no se publica el archivo parcial')


CONTROLS = {}  # Accessed under production_studio.LOCK, never by PID search.


def execute(command, work, control, timeout=600, env=None):
    control.check()
    # Errors go to a local temporary file, not an unbounded memory pipe.
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, cwd=work, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=errors,
                                   **({'env': env} if env is not None else {}))
        control.process = process
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                control.check()
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, timeout)
                try:
                    process.wait(timeout=.1)
                except subprocess.TimeoutExpired:
                    pass
            control.check()
        finally:
            if process.poll() is None:
                control.terminated = True
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            control.stopped = process.poll() is not None
        errors.seek(0, 2)
        errors.seek(max(0, errors.tell()-1500))
        return SimpleNamespace(returncode=process.returncode, stderr=errors.read())
