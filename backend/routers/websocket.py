from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from config.logging_config import get_logger

logger = get_logger("websocket")

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """
    Manages active frontend WebSocket subscriptions for real-time tickers and orders.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to broadcast websocket msg: {str(e)}")


ws_manager = ConnectionManager()


@router.websocket("/ticks")
async def websocket_ticks_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Client can send subscription messages
            data = await websocket.receive_text()
            await websocket.send_json({"status": "acknowledged", "received": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
