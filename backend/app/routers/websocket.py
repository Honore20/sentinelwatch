from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json

logger = logging.getLogger("sentinel.ws")
router = APIRouter()


class ConnectionManager:
    """Gère les connexions WebSocket actives (analystes connectés au dashboard)."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ Client WS connecté (total: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"❌ Client WS déconnecté (total: {len(self.active_connections)})")

    async def broadcast(self, message: dict):
        """Envoie un message à TOUS les clients connectés."""
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        # Nettoyage des connexions mortes
        for conn in dead:
            self.disconnect(conn)


# Instance globale du manager (singleton)
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour le dashboard temps réel."""
    await manager.connect(websocket)
    try:
        while True:
            # On garde la connexion ouverte (le serveur ne reçoit rien, il push)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
