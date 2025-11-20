from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.api.deps import get_connection_manager
from app.realtime.connection_manager import ConnectionManager


logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/rates")
async def rates_websocket(
    websocket: WebSocket,
    manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> None:
    """
    WebSocket endpoint used by frontend clients to receive live rate updates.

    Clients do not need to send any messages; this connection is essentially
    server-push only. The server will broadcast updates whenever new ticks arrive.
    """
    await manager.connect(websocket)

    try:
        # Keep the connection open until the client disconnects.
        while True:
            # We do not expect messages from the client.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.exception("Unexpected error in WebSocket connection: %s", exc)
        manager.disconnect(websocket)
