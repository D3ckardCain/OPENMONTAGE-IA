"""Notify our long-lived SSE streams before Uvicorn drains connections."""
import uvicorn


class StudioServer(uvicorn.Server):
    def __init__(self, config, *, stop_notifications):
        super().__init__(config)
        self.stop_notifications = stop_notifications

    def run(self, sockets=None):
        # Match uvicorn.run's CLI boundary: Uvicorn re-raises captured SIGINT
        # after cleanup, which must not print a misleading failure traceback.
        try:
            return super().run(sockets=sockets)
        except KeyboardInterrupt:
            return None

    async def shutdown(self, sockets=None):
        # Lifespan shutdown runs AFTER Uvicorn waits for connections. An SSE
        # consumer can stay connected forever, so notify it before that wait.
        self.stop_notifications()
        await super().shutdown(sockets=sockets)
