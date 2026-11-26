"""Owned-process pilot transport; not a discoverable tool."""
import os
import time
import subprocess
from lib import hyperframes_runtime
from tools.video.hyperframes_compose import HyperFramesCompose


def windows_descendants(parent):
    """Read the process table; retain only the live, owned root's descendants."""
    import ctypes
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD),
                    ('pid', wintypes.DWORD), ('heap', ctypes.c_size_t),
                    ('module', wintypes.DWORD), ('threads', wintypes.DWORD),
                    ('parent', wintypes.DWORD), ('priority', wintypes.LONG),
                    ('flags', wintypes.DWORD), ('name', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), 'Process snapshot failed')
    rows = []; entry = Entry(); entry.size = ctypes.sizeof(entry)
    try:
        ok = kernel.Process32FirstW(handle, ctypes.byref(entry))
        while ok:
            rows.append({'pid': entry.pid, 'parent': entry.parent, 'name': entry.name})
            ok = kernel.Process32NextW(handle, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(handle)
    if parent is None:
        return rows
    owned = {parent}; result = []
    while True:
        children = [row for row in rows if row['parent'] in owned and row['pid'] not in owned]
        if not children:
            return result
        result.extend(children); owned.update(row['pid'] for row in children)


def stop_owned(process, record):
    """Never discover a target by name or touch the active Studio process."""
    if process.poll() is not None:
        return
    if os.name == 'nt':
        children = windows_descendants(process.pid)
        record['children_before_stop'] = children
        stopped = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                 capture_output=True, text=True, timeout=10)
        record.update(tree_stop_exit=stopped.returncode, tree_stop_output=stopped.stdout,
                      tree_stop_error=stopped.stderr)
        process.wait(timeout=10)
        # Read-only follow-up. No additional kill based on a stale PID.
        remaining = windows_descendants(None)
        seen = {row['pid'] for row in remaining}
        record['children_still_present'] = [row for row in children if row['pid'] in seen]
    else:
        process.terminate(); process.wait(timeout=10)

class OwnedHyperFrames(HyperFramesCompose):
    def __init__(self,root,cancel=False):
        super().__init__();self.root=root;self.cancel=cancel;self.processes=[]

    def _run_hf(self,args,*,cwd,timeout,check):
        cmd=hyperframes_runtime.command(args)
        if args[0]=='render':cmd+=['--workers','1','--no-browser-gpu']
        log=self.root/'artifacts'/('cancel.log' if self.cancel else args[0]+'.log')
        started=time.monotonic();cancelled=False
        with log.open('wb') as stream:
            process=subprocess.Popen(cmd,cwd=cwd,env=hyperframes_runtime.environment(),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            self.processes.append({'pid':process.pid,'operation':args[0]})
            try:
                while process.poll() is None:
                    # Explicit project-local cancel marker, never an arbitrary PID.
                    if self.cancel and (self.root/'artifacts/cancel.request').exists():
                        cancelled=True
                        stop_owned(process,self.processes[-1]);break
                    if time.monotonic()-started>min(timeout,180):raise subprocess.TimeoutExpired(cmd,180)
                    time.sleep(.1)
            finally:
                if process.poll() is None:
                    stop_owned(process,self.processes[-1])
                self.processes[-1].update(exit_code=process.returncode,elapsed_seconds=time.monotonic()-started,cancelled=cancelled)
        text=log.read_text(encoding='utf-8',errors='replace')
        return subprocess.CompletedProcess(cmd,130 if cancelled else process.returncode,text,'')


