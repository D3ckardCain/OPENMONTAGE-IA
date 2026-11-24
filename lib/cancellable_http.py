"""Owned loopback HTTP socket; cancellation closes transport, not the server."""
import http.client
import json
import socket
import threading
from urllib.parse import urlsplit


class CancelledRequest(Exception):
    pass


def request(base, path, data, *, timeout, cancel, progress=None):
    from lib.production_studio import local_url
    url = urlsplit(local_url(base))
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Ruta HTTP local inválida')
    connection = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=timeout)
    finished = threading.Event()
    owned_socket = [None]
    evidence = {'request_sent': False, 'response_open': False, 'content_chunks': 0,
                'done_received': False, 'socket_shutdown_requested': False,
                'transport_closed': False, 'server_inference_stopped': 'not_verified'}
    def notify():
        if progress: progress(dict(evidence))
    def check():
        if cancel.is_set(): raise CancelledRequest('Petición local cancelada; resultado parcial descartado')
    def watch():
        while not finished.wait(0.025):
            if cancel.is_set():
                sock = owned_socket[0] or connection.sock
                if sock is not None:
                    evidence['socket_shutdown_requested'] = True
                    try: sock.shutdown(socket.SHUT_RDWR)
                    except OSError: pass
                    # shutdown interrupts a blocked getresponse/read on Windows too.
                    return
    watcher = threading.Thread(target=watch, daemon=True, name='local-http-cancel')
    response = None
    try:
        check()
        watcher.start()
        connection.request('POST', path, json.dumps(data).encode(), {'Content-Type': 'application/json'})
        owned_socket[0] = connection.sock
        evidence['request_sent'] = True
        notify()
        check()
        response = connection.getresponse()
        evidence['response_open'] = True
        notify()
        if response.status != 200:
            raise ValueError('HTTP local: ' + str(response.status))
        if not data.get('stream'):
            raw = response.read(16_000_001)
            check()
            if len(raw) > 16_000_000: raise ValueError('Respuesta local demasiado grande')
            return json.loads(raw)
        # Streaming is used only by the fixed text diagnostic (no tool fragments).
        content, total = [], 0
        while True:
            line = response.readline(65_537)
            check()
            if not line: raise ValueError('Stream local incompleto: falta done')
            total += len(line)
            if len(line) > 65_536 or total > 16_000_000:
                raise ValueError('Respuesta local demasiado grande')
            row = json.loads(line)
            if row.get('error'): raise ValueError('Ollama: ' + str(row['error'])[:600])
            message = row.get('message', {})
            if message.get('tool_calls'): raise ValueError('La sonda textual no admite herramientas en streaming')
            text = message.get('content', '')
            if text:
                content.append(text)
                evidence['content_chunks'] += 1
            evidence['done_received'] = bool(row.get('done'))
            notify()
            if row.get('done'):
                return {**row, 'message': {'role': 'assistant', 'content': ''.join(content)}}
    except (OSError, http.client.HTTPException, ValueError):
        check()
        raise
    finally:
        finished.set()
        # HTTPResponse may own a detached socket after Connection: close.
        try:
            if response is not None: response.close()
        finally:
            connection.close()
            if watcher.ident is not None: watcher.join(timeout=1)
            evidence['transport_closed'] = True
            notify()
