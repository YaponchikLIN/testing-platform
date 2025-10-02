from typing import Dict, List, Any, Optional
from fastapi import WebSocket
from datetime import datetime

# Типы для WebSocket соединений
WebSocketList = List[WebSocket]
ConnectedClients = Dict[str, WebSocketList]

# Типы для данных тестов
TestData = Dict[str, Any]
TestsDatabase = Dict[str, TestData]

# Типы для данных устройств
DeviceData = Dict[str, Any]
DevicesDatabase = Dict[str, DeviceData]

# Типы для статусов
TestStatus = str  # "pending", "running", "completed", "failed", etc.


# Типы для WebSocket сообщений
class TestStatusMessage:
    test_id: str
    status: TestStatus
    time_start: Optional[datetime]
    updated_at: Optional[datetime]
    time_end: Optional[datetime]
    result: Optional[str]
