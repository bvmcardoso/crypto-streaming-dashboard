from __future__ import annotations

import logging
from typing import Set

from fastapi import WebSocket

from app.schemas.rates import RateUpdateMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts rate updates
    to all connected clients.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and track it."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WebSocket client connected. Total: %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the active set."""
        if websocket in self._connections:
            self._connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. Total: %d", len(self._connections)
            )

    async def broadcast_text(self, message: str) -> None:
        """Broadcast a raw text message to all connected clients."""
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                # Connection is likely dead, mark for removal.
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    async def broadcast_rate_update(self, update: RateUpdateMessage) -> None:
        """Broadcast a rate update message to all connected clients."""
        if not self._connections:
            return

        await self.broadcast_text(update.model_dump_json())
