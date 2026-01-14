import socketio
from uuid import UUID
from datetime import datetime, timedelta
from socketio import AsyncNamespace
from core.logger import setup_logger

logger = setup_logger("socket")


class MainNamespace(socketio.AsyncNamespace):
    namespace = "/main"

    def on_connect(self, sid, environ):
        print(f"[Main] Connected: {sid}")

    def on_disconnect(self, sid):
        print(f"[Main] Disconnected: {sid}")

    async def on_join(self, sid, data): ...

