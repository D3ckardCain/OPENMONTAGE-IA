"""Real loopback sockets and disconnect detection, simulated HTTP server, no model."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
from types import SimpleNamespace
import pytest
from lib.cancellable_http import request, CancelledRequest


@pytest.fixture
def server():
    state=SimpleNamespace(mode='headers_wait',entered=threading.Event(),disconnected=threading.Event())
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            state.entered.set()
            self.connection.settimeout(3)
            if state.mode=='stream_wait':
                self.send_response(200)
                self.send_header('Content-Type','application/x-ndjson')
                self.send_header('Connection','close')
                self.end_headers()
                self.wfile.write(b'{"message":{"content":"A"},"done":false}\n')
                self.wfile.flush()
            elif state.mode in ('complete','truncated','oversize','redirect','json'):
                self.send_response(302 if state.mode=='redirect' else 200)
                self.send_header('Connection','close')
                self.end_headers()
                payload=(b'{"message":{"content":"OK"},"done":true}\n' if state.mode=='complete'
                         else b'{"message":{"content":"OK"}}' if state.mode=='json'
                         else b'x'*65_537 if state.mode=='oversize' else b'')
                try:self.wfile.write(payload)
                except (BrokenPipeError,ConnectionResetError):pass
                return
            try:
                if self.connection.recv(1)==b'':state.disconnected.set()
            except (ConnectionResetError,OSError):state.disconnected.set()
    http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=http.serve_forever,daemon=True)
    thread.start()
    yield 'http://127.0.0.1:'+str(http.server_port),state
    http.shutdown();http.server_close();thread.join(timeout=2)


@pytest.mark.parametrize('mode',['headers_wait','stream_wait'])
def test_cancel_closes_real_socket_before_headers_or_mid_stream(server,mode):
    base,state=server;state.mode=mode
    stop=threading.Event();observed=[];errors=[]
    def run():
        try:request(base,'/api/chat',{'stream':mode=='stream_wait'},timeout=5,cancel=stop,progress=observed.append)
        except BaseException as exc:errors.append(exc)
    worker=threading.Thread(target=run)
    worker.start()
    assert state.entered.wait(2)
    if mode=='stream_wait':
        deadline=time.monotonic()+2
        while not any(x['content_chunks'] for x in observed) and time.monotonic()<deadline:time.sleep(.01)
        assert any(x['content_chunks'] for x in observed)
    started=time.monotonic();stop.set();worker.join(timeout=2)
    assert not worker.is_alive()
    assert time.monotonic()-started<2
    assert isinstance(errors[0],CancelledRequest)
    assert state.disconnected.wait(1)
    assert observed[-1]['transport_closed']
    # Cancellation may be observed just before getresponse starts, in which case
    # finally closes the socket directly. A blocked read uses watcher shutdown.
    assert observed[-1]['socket_shutdown_requested'] or not observed[-1]['response_open']
    assert observed[-1]['server_inference_stopped']=='not_verified'


def test_complete_stream_has_done_and_closes_transport(server):
    base,state=server;state.mode='complete';observed=[]
    result=request(base,'/api/chat',{'stream':True},timeout=2,cancel=threading.Event(),progress=observed.append)
    assert result['message']['content']=='OK'
    assert observed[-1]['done_received'] and observed[-1]['transport_closed']


def test_existing_non_streaming_json_contract_and_timeout(server):
    base,state=server;state.mode='json';observed=[]
    assert request(base,'/api/chat',{'stream':False},timeout=2,cancel=threading.Event(),progress=observed.append)['message']['content']=='OK'
    state.mode='headers_wait'
    with pytest.raises(TimeoutError):
        request(base,'/api/chat',{'stream':False},timeout=.1,cancel=threading.Event(),progress=observed.append)
    assert observed[-1]['transport_closed']


@pytest.mark.parametrize('mode,match',[('truncated','incompleto'),('oversize','grande'),('redirect','302')])
def test_protocol_errors_close_transport_without_redirect_or_partial_success(server,mode,match):
    base,state=server;state.mode=mode;observed=[]
    with pytest.raises(ValueError,match=match):
        request(base,'/api/chat',{'stream':True},timeout=2,cancel=threading.Event(),progress=observed.append)
    assert observed[-1]['transport_closed']


def test_cancel_before_connect_and_remote_url_denied():
    stop=threading.Event();stop.set();observed=[]
    with pytest.raises(CancelledRequest):
        request('http://127.0.0.1:1','/api/chat',{},timeout=1,cancel=stop,progress=observed.append)
    assert observed[-1]['transport_closed'] and not observed[-1]['request_sent']
    with pytest.raises(ValueError,match='local'):
        request('https://remote.example','/api/chat',{},timeout=1,cancel=stop)
