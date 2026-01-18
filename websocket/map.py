import socketio
from socketio import AsyncNamespace
from core.logger import setup_logger
from repositories.rentals import get_rental_repo

logger = setup_logger(__name__)

class MapNamespace(socketio.AsyncNamespace):
    namespace = "/map"

    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.rental_repo = get_rental_repo()

    def on_connect(self, sid, environ):
        logger.info(f"[Map] Connected: {sid}")

    def on_disconnect(self, sid):
        logger.warning(f"[Map] Disconnected: {sid}")

    async def on_get_heat_maps(self, sid, data):
        try:
            logger.info('heat map data: %s', data)
            if not data.get('latitude') or not data.get('longitude'):
                return

            rentals = await self.rental_repo.get_nearby_rentals(
                data.get('latitude'),
                data.get('longitude'),
                data.get('radius') or 10
            )

            await self.emit(
                "live_on_map_heatmaps",
                {"heat_maps": {"rentals": self.rental_repo._level_2_rental_heatmap_to_dict(rental)  for rental in rentals}},
                room=sid,
            )
        except Exception as e:
            logger.exception(f"[MapNamespace Error]: {e}")
