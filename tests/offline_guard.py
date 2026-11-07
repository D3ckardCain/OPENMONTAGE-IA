"""Offline protections for the automated test runner, including collection."""
from __future__ import annotations
import os
import ipaddress
import socket
import subprocess

class NetworkCallInTestError(RuntimeError):
    pass

class ExternalProcessInTestError(subprocess.CalledProcessError):
    def __init__(self, command):
        super().__init__(126, command, stderr="External CLI blocked by offline test policy")

def is_loopback(address):
    if isinstance(address, (str, bytes)):
        return True  # AF_UNIX
    if not isinstance(address, (tuple, list)) or not address:
        return False
    host = address[0]
    if isinstance(host, bytes):
        host = host.decode("utf-8", "replace")
    if not isinstance(host, str):
        return False
    host = host.strip("[]").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False

def check_process(command, *, shell=False, executable=None):
    """Providers/compositors must mock network-capable CLI transports.

    Local FFmpeg fixture processing and existing Python-only helper tests
    continue to run. This is a runner guard, not an OS process sandbox.
    """
    if shell or not isinstance(command, (list, tuple)) or not command:
        raise ExternalProcessInTestError(command)
    blocked = {
        "node", "nodejs", "npm", "npx", "pnpm", "yarn", "bun", "deno",
        "curl", "wget", "powershell", "pwsh", "cmd", "sh", "bash", "zsh",
    }
    for name in [command[0]] + ([executable] if executable else []):
        normalized = os.fsdecode(name).replace("\\", "/").rsplit("/", 1)[-1].lower()
        for suffix in (".exe", ".cmd", ".bat"):
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        if normalized in blocked:
            raise ExternalProcessInTestError(command)

class OfflineTestGuard:
    def __init__(self):
        self.originals = None

    def install(self):
        if self.originals is not None:
            return
        self.originals = (
            socket.socket.connect, socket.socket.connect_ex,
            socket.create_connection, subprocess.Popen, socket.getaddrinfo,
        )
        connect, connect_ex, create_connection, popen, getaddrinfo = self.originals

        def check_address(address):
            if not is_loopback(address):
                raise NetworkCallInTestError(
                    "External network blocked in automated tests, including collection."
                )

        def guarded_connect(sock, address, *args, **kwargs):
            check_address(address)
            return connect(sock, address, *args, **kwargs)

        def guarded_connect_ex(sock, address, *args, **kwargs):
            check_address(address)
            return connect_ex(sock, address, *args, **kwargs)

        def guarded_create_connection(address, *args, **kwargs):
            check_address(address)
            return create_connection(address, *args, **kwargs)

        def guarded_getaddrinfo(host, port, *args, **kwargs):
            # Resolver traffic happens before socket.connect. Test hostnames
            # such as comfy.test must never reach a real DNS server either.
            check_address((host, port))
            return getaddrinfo(host, port, *args, **kwargs)

        def guarded_popen(args, *extra, **kwargs):
            check_process(args, shell=kwargs.get("shell", False),
                          executable=kwargs.get("executable"))
            return popen(args, *extra, **kwargs)

        socket.socket.connect = guarded_connect
        socket.socket.connect_ex = guarded_connect_ex
        socket.create_connection = guarded_create_connection
        subprocess.Popen = guarded_popen
        socket.getaddrinfo = guarded_getaddrinfo

    def restore(self):
        if self.originals is not None:
            (socket.socket.connect, socket.socket.connect_ex,
             socket.create_connection, subprocess.Popen,
             socket.getaddrinfo) = self.originals
            self.originals = None
