from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List
from fastapi import WebSocket

# Типы для WebSocket соединений
ConnectedClients = Dict[str, List[WebSocket]]

# Общие переменные для всего приложения
# Типизированная переменная для WebSocket соединений
connected_clients: ConnectedClients = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
SECRET_KEY = "your-secret-key"
