"""Focused shutdown contract; no external paths, models or media."""
import asyncio
from unittest.mock import Mock

import uvicorn
import pytest

from backlot.runtime import StudioServer
from backlot.server import ChangeHub


def test_hub_close_wakes_full_and_filtered_queues():
    hub = ChangeHub()
    library, board = hub.subscribe(), hub.subscribe('film')
    for _ in range(100):
        hub.publish('film')
    assert library.full() and board.full()
    hub.close()
    assert library.get_nowait() is None
    assert board.get_nowait() is None
    hub.publish('film')
    assert library.empty() and board.empty()
    assert hub.subscribe('late').get_nowait() is None
    hub.close()  # idempotent, no full-queue exception
    hub.unsubscribe(board)
    assert board not in hub._subscribers


def test_shutdown_notifies_before_uvicorn_waits(monkeypatch):
    order = []

    async def drain(self, sockets=None):
        order.append(('drain', sockets))

    monkeypatch.setattr(uvicorn.Server, 'shutdown', drain)
    server = StudioServer(uvicorn.Config('unused:app'), stop_notifications=lambda: order.append('notify'))
    asyncio.run(server.shutdown(sockets=['owned']))
    assert order == ['notify', ('drain', ['owned'])]


def test_sigint_cli_boundary_preserves_normal_errors(monkeypatch):
    run = Mock(side_effect=KeyboardInterrupt)
    monkeypatch.setattr(uvicorn.Server, 'run', run)
    server = StudioServer(uvicorn.Config('unused:app'), stop_notifications=lambda: None)
    assert server.run() is None
    run.side_effect = RuntimeError('real startup failure')
    with pytest.raises(RuntimeError, match='real startup failure'):
        server.run()


def test_foreground_cli_uses_notification_aware_server(monkeypatch):
    from backlot import __main__ as cli, server as app_module
    from lib import local_cli_environment

    monkeypatch.setattr(local_cli_environment, 'configured_environment', lambda: {})
    instances = []
    def run(self):
        self.started = True
        instances.append(self)

    monkeypatch.setattr(StudioServer, 'run', run)
    assert cli.cmd_serve(48765) == 0
    assert len(instances) == 1
    assert instances[0].config.port == 48765
    assert instances[0].stop_notifications.__self__ is app_module.hub


def test_foreground_cli_reports_startup_failure(monkeypatch):
    from backlot import __main__ as cli
    from lib import local_cli_environment

    monkeypatch.setattr(local_cli_environment, 'configured_environment', lambda: {})
    monkeypatch.setattr(StudioServer, 'run', lambda self: None)
    assert cli.cmd_serve(48765) == 3


@pytest.mark.parametrize('path', ['/api/library/events', '/api/project/{project_id}/events'])
def test_real_stream_finishes_and_unsubscribes_on_shutdown(path, tmp_path, monkeypatch):
    from backlot import server as module

    hub = ChangeHub()
    monkeypatch.setattr(module, 'hub', hub)
    monkeypatch.setattr(module, 'PROJECTS_DIR', tmp_path)
    (tmp_path / 'film').mkdir()
    app = module.create_app()
    endpoint = next(route.endpoint for route in app.routes if getattr(route, 'path', '') == path)

    class ConnectedRequest:
        async def is_disconnected(self):
            return False

    async def check():
        request = ConnectedRequest()
        response = await (endpoint(request) if path.startswith('/api/library') else endpoint('film', request))
        assert 'hello' in await anext(response.body_iterator)
        assert len(hub._subscribers) == 1
        # Include queued notifications: the terminal wake-up must survive
        # coalescing and complete without a client disconnect or heartbeat.
        hub.publish('film')
        hub.close()
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(response.body_iterator), timeout=.5)
        assert not hub._subscribers

    asyncio.run(check())
