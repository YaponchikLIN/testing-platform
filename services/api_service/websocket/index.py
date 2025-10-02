from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

connected_clients: Dict[str, WebSocket] = {}
