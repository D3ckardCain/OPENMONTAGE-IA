"""Bounded, optional host RAM and NVIDIA VRAM sampling during local production."""
import ctypes
import os
import shutil
import subprocess
import threading


def host_ram_mb():
    try:
        if os.name == 'nt':
            class Status(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                            ('total_physical', ctypes.c_ulonglong), ('available_physical', ctypes.c_ulonglong),
                            ('total_page', ctypes.c_ulonglong), ('available_page', ctypes.c_ulonglong),
                            ('total_virtual', ctypes.c_ulonglong), ('available_virtual', ctypes.c_ulonglong),
                            ('available_extended', ctypes.c_ulonglong)]
            status=Status();status.length=ctypes.sizeof(Status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            return round((status.total_physical-status.available_physical)/1048576)
        with open('/proc/meminfo',encoding='ascii') as stream:
            values={key.strip(':'):int(value.split()[0]) for key,value in
                    (line.split(':',1) for line in stream if ':' in line)}
        return round((values['MemTotal']-values['MemAvailable'])/1024)
    except (OSError, ValueError, KeyError, AttributeError):
        return None


def nvidia_vram_mb(executable):
    if not executable:
        return None
    try:
        result=subprocess.run([executable,'--query-gpu=memory.used','--format=csv,noheader,nounits'],
                              capture_output=True,text=True,timeout=3)
        if result.returncode:
            return None
        values=[int(line.strip()) for line in result.stdout.splitlines()]
        return max(values) if values and all(value>=0 for value in values) else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


class ResourceSampler:
    def __init__(self, interval=5):
        self.interval=interval;self.stop_event=threading.Event();self.thread=None
        self.nvidia=shutil.which('nvidia-smi');self.ram_peak_mb=None;self.vram_peak_mb=None
        self.samples=0

    def sample(self):
        ram=host_ram_mb();vram=nvidia_vram_mb(self.nvidia)
        if ram is not None:self.ram_peak_mb=max(self.ram_peak_mb or 0,ram)
        if vram is not None:self.vram_peak_mb=max(self.vram_peak_mb or 0,vram)
        self.samples+=1

    def start(self):
        self.sample()
        def loop():
            while not self.stop_event.wait(self.interval):self.sample()
        self.thread=threading.Thread(target=loop,daemon=True,name='production-resource-sampler')
        self.thread.start()

    def finish(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=4)
        return {'host_ram_peak_mb':self.ram_peak_mb,'gpu_vram_peak_mb':self.vram_peak_mb,
                'samples':self.samples,'sampling_interval_seconds':self.interval,
                'scope':'whole_host_and_busiest_nvidia_gpu_not_project_attribution'}
