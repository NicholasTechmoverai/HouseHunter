import socketio
from uuid import UUID
from datetime import datetime, timedelta
from socketio import AsyncNamespace
from core.logger import setup_logger

logger = setup_logger(__name__)


class MainNamespace(socketio.AsyncNamespace):
    namespace = "/main"

    def on_connect(self, sid, environ):
        logger.info(f"[Main] Connected: {sid}")

    def on_disconnect(self, sid):
        logger.warning(f"[Main] Disconnected: {sid}")

    async def on_check_username_availability(self, sid, data):
        try:
            username = data.get("username")
            user_id = data.get("user_id")
            logger.debug(
                f"[Users] Checking availability for username: {username} from {sid}"
            )
            if not username or not user_id:
                logger.warning(f"[Users] Missing username or user_id from {sid}")
                return

            is_available = await self.user_service.check_username_availability(
                username, user_id
            )
            await self.emit(
                "check_username_availability",
                {"username": username, "available": is_available},
                room=sid,
            )
        except Exception as e:
            logger.exception(f"[UsersNamespace Error]: {e}")
            
