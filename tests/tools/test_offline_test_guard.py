"""Exercise guard entry points without launching any external process."""
import socket
import subprocess
import pytest
from tests.offline_guard import (
    ExternalProcessInTestError, NetworkCallInTestError, check_process, is_loopback,
)

@pytest.mark.parametrize("command,kwargs", [
    (["npx", "hyperframes", "doctor"], {}),
    (["npm", "view", "hyperframes", "version"], {}),
    (["node", "program.js"], {}),
    ([r"C:\Node\npx.cmd", "hyperframes"], {}),
    (["curl", "https://example.com"], {}),
    (["bash", "-lc", "npx hyperframes"], {}),
    ("npx hyperframes", {"shell": True}),
    (["harmless-name"], {"executable": "node"}),
])
def test_blocks_cli_before_process_creation(command, kwargs):
    with pytest.raises(ExternalProcessInTestError):
        subprocess.Popen(command, **kwargs)

def test_blocks_socket_even_when_original_opt_in_is_set(monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_ALLOW_NETWORK", "1")
    with pytest.raises(NetworkCallInTestError):
        socket.create_connection(("203.0.113.1", 443), timeout=0.1)

def test_socket_connect_and_connect_ex_are_guarded():
    with socket.socket() as sock:
        with pytest.raises(NetworkCallInTestError):
            sock.connect(("203.0.113.1", 443))
        with pytest.raises(NetworkCallInTestError):
            sock.connect_ex(("203.0.113.1", 443))

def test_dummy_host_is_blocked_before_dns_resolution():
    with pytest.raises(NetworkCallInTestError):
        socket.getaddrinfo("comfy.test", 80)

def test_http_fixture_cannot_fall_through_to_real_network():
    import requests
    session = requests.Session()
    session.trust_env = False
    with pytest.raises(NetworkCallInTestError):
        session.get("http://comfy.test/system_stats", timeout=0.1)

@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_loopback_recognized(host):
    assert is_loopback((host, 8188))

@pytest.mark.parametrize("host", ["127.evil.example", "192.168.1.1", "0.0.0.0", ""])
def test_other_hosts_not_treated_as_local(host):
    assert not is_loopback((host, 8188))

def test_ffmpeg_argv_is_accepted_without_launching():
    check_process(["ffmpeg", "-version"])
