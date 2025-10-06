# WebSocket-эндпоинт
from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from typing import Dict
from api_service.app.config import connected_clients, ConnectedClients
from db.db_tests import tests_db
import importlib.util
import os
from typing import List
import json

# Загружаем types модуль напрямую
types_path = os.path.join(os.path.dirname(__file__), "types.py")
spec = importlib.util.spec_from_file_location("websocket_types", types_path)
types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(types_module)
TestsDatabase = types_module.TestsDatabase

router = APIRouter()


# Вспомогательная асинхронная функция для регистрации клиента и отправки статуса
async def _subscribe_and_send_initial_status(
    websocket: WebSocket,
    current_test_id: str,
    tests_db_ref: TestsDatabase,
    connected_clients_ref: ConnectedClients,
):
    """
    Регистрирует WebSocket для указанного test_id и отправляет его текущий статус.
    """
    print(f"Подписка клиента на test_id: {current_test_id}")  # Для отладки
    if current_test_id not in connected_clients_ref:
        connected_clients_ref[current_test_id] = []

    # Избегаем дублирования одного и того же websocket в списке для одного test_id
    if websocket not in connected_clients_ref[current_test_id]:
        connected_clients_ref[current_test_id].append(websocket)

    print(f"connected_clients_ref: {connected_clients_ref}")  # Для отладки
    print(f"Отправка начального статуса для test_id: {current_test_id}")  # Для отладки
    if current_test_id in tests_db_ref:
        print("current_test_id: ", current_test_id)
        # print("tests_db_ref: ", tests_db_ref)
        print("tests_db_ref[current_test_id]: ", tests_db_ref[current_test_id])
        await websocket.send_json(
            {
                "test_id": current_test_id,
                "status": tests_db_ref[current_test_id]["status"],
                "time_start": tests_db_ref[current_test_id]["time_start"],
                "updated_at": tests_db_ref[current_test_id]["updated_at"],
                "time_end": tests_db_ref[current_test_id]["time_end"],
                "result": tests_db_ref[current_test_id]["result"],
            }
        )
    else:
        await websocket.send_json(
            {
                "test_id": current_test_id,
                "status": "pending_initiation",
                "time_start": None,
                "updated_at": None,
                "time_end": None,
                "result": None,
            }
        )


gpio_connections: List[WebSocket] = []


@router.websocket("/ws/gpio")
async def gpio_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket для получения событий GPIO в реальном времени
    """
    await websocket.accept()
    gpio_connections.append(websocket)

    print(
        f"✅ Новое GPIO WebSocket подключение. Всего подключений: {len(gpio_connections)}"
    )

    try:
        # Отправляем подтверждение подключения
        await websocket.send_json(
            {
                "type": "connection_established",
                "message": "Подключен к мониторингу GPIO",
                "connections_count": len(gpio_connections),
            }
        )

        # Держим соединение открытым
        while True:
            data = await websocket.receive_text()
            # Обрабатываем входящие сообщения от клиента (например, ping)
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": "..."})

    except WebSocketDisconnect:
        gpio_connections.remove(websocket)
        print(
            f"🔌 GPIO WebSocket отключен. Осталось подключений: {len(gpio_connections)}"
        )

    except Exception as e:
        print(f"❌ Ошибка в GPIO WebSocket: {e}")
        if websocket in gpio_connections:
            gpio_connections.remove(websocket)


# Функция для парсинга GPIO событий из логов Node.js
async def parse_and_broadcast_gpio_event(log_line: str):
    """
    Парсит строку лога Node.js и рассылает события через WebSocket
    """
    try:
        # Парсим события изменения GPIO
        if "Событие:" in log_line and "GPIO:" in log_line:
            parts = log_line.split("|")
            if len(parts) >= 3:
                event_part = parts[0].strip()
                value_part = parts[1].strip()
                time_part = parts[2].strip() if len(parts) > 2 else ""

                # Извлекаем тип события и значение
                event_type = "🔼 ПОДЪЕМ" if "🔼" in event_part else "🔽 СПАД"
                value = int(value_part.replace("GPIO:", "").strip())

                event_data = {
                    "type": "gpio_event",
                    "event": "rising" if "🔼" in event_type else "falling",
                    "value": value,
                    "event_display": event_type,
                    "timestamp": time_part.replace("Время:", "").strip(),
                    "raw_message": log_line.strip(),
                }

                await broadcast_gpio_event(event_data)
                return

        # Парсим ошибки
        elif "❌ Ошибка:" in log_line:
            error_data = {
                "type": "error",
                "message": log_line.replace("❌ Ошибка:", "").strip(),
                "raw_message": log_line.strip(),
            }
            await broadcast_gpio_event(error_data)
            return

        # Логируем другие сообщения для отладки
        elif "✅" in log_line or "Инициализация" in log_line:
            print(f"[GPIO Monitor] {log_line.strip()}")

    except Exception as e:
        print(f"❌ Ошибка парсинга GPIO лога: {e}")


# Функция для парсинга GPIO событий из логов Node.js
async def parse_and_broadcast_gpio_event(log_line: str):
    """
    Парсит строку лога Node.js и рассылает события через WebSocket
    """
    try:
        # Парсим события изменения GPIO
        if "Событие:" in log_line and "GPIO:" in log_line:
            parts = log_line.split("|")
            if len(parts) >= 3:
                event_part = parts[0].strip()
                value_part = parts[1].strip()
                time_part = parts[2].strip() if len(parts) > 2 else ""

                # Извлекаем тип события и значение
                event_type = "🔼 ПОДЪЕМ" if "🔼" in event_part else "🔽 СПАД"
                value = int(value_part.replace("GPIO:", "").strip())

                event_data = {
                    "type": "gpio_event",
                    "event": "rising" if "🔼" in event_type else "falling",
                    "value": value,
                    "event_display": event_type,
                    "timestamp": time_part.replace("Время:", "").strip(),
                    "raw_message": log_line.strip(),
                }

                await broadcast_gpio_event(event_data)
                return

        # Парсим ошибки
        elif "❌ Ошибка:" in log_line:
            error_data = {
                "type": "error",
                "message": log_line.replace("❌ Ошибка:", "").strip(),
                "raw_message": log_line.strip(),
            }
            await broadcast_gpio_event(error_data)
            return

        # Логируем другие сообщения для отладки
        elif "✅" in log_line or "Инициализация" in log_line:
            print(f"[GPIO Monitor] {log_line.strip()}")

    except Exception as e:
        print(f"❌ Ошибка парсинга GPIO лога: {e}")


@router.websocket("/ws/test-status/{test_id}")
async def websocket_endpoint(
    websocket: WebSocket, test_id: str
):  # 'test_id' здесь - это значение из URL
    print("websocket_endpoint")
    print(f"Запрос на подключение к WebSocket для test_id из URL: {test_id}")
    await websocket.accept()

    # Список фактических test_id, на которые этот WebSocket был подписан.
    # Важно для корректной отписки.
    subscribed_ids_for_this_connection = []

    try:
        if test_id == "all":
            # Если клиент хочет подписаться на все тесты
            print("Клиент запросил подписку на все тесты.")
            for (
                actual_db_test_id
            ) in tests_db.keys():  # Используем другое имя переменной для итерации
                await _subscribe_and_send_initial_status(
                    websocket, actual_db_test_id, tests_db, connected_clients
                )
                subscribed_ids_for_this_connection.append(actual_db_test_id)
        else:
            # Если клиент хочет подписаться на конкретный тест
            print(f"Клиент запросил подписку на конкретный test_id: {test_id}")
            await _subscribe_and_send_initial_status(
                websocket,
                test_id,  # Используем test_id из URL
                tests_db,
                connected_clients,
            )
            subscribed_ids_for_this_connection.append(test_id)

        # Держим соединение открытым для получения обновлений
        while True:
            await websocket.receive_text()  # Ожидаем сообщения от клиента (или используйте asyncio.sleep(1) если клиенты только слушают)
            # Например, можно добавить обработку ping от клиента для поддержания соединения
            # data = await websocket.receive_text()
            # if data == "ping":
            #     await websocket.send_text("pong")

    except WebSocketDisconnect:
        exception_websocket_disconnect_endpoint(
            e, websocket, "test_id", test_id, subscribed_ids_for_this_connection
        )

    except Exception as e:
        exception_websocket_endpoint(e, websocket)


async def exception_websocket_endpoint(exception: Exception, websocket: WebSocket):
    print(f"Ошибка в WebSocket: {exception}")
    if not websocket.client_state.DISCONNECTED:
        await websocket.close(code=1008, reason=str(exception))


async def exception_websocket_disconnect_endpoint(
    exception: Exception,
    websocket: WebSocket,
    type_ws_id: str,
    subscribed_id: str,
    subscribed_ids_for_this_connection: list,
):
    print(
        f"Клиент отсоединился (изначальный запрос был для {type_ws_id}: {subscribed_id} ). Очистка подписок..."
    )
    for subscribed_id in subscribed_ids_for_this_connection:
        if (subscribed_id in connected_clients) and (
            websocket in connected_clients[subscribed_id]
        ):
            connected_clients[subscribed_id].remove(websocket)
            if not connected_clients[subscribed_id]:
                del connected_clients[subscribed_id]
                print(
                    f"Удален пустой список клиентов для {type_ws_id}: {subscribed_id}"
                )
    print(
        f"Подписки для отсоединенного клиента (изначальный запрос: '{type_ws_id}: {subscribed_id}') очищены."
    )


async def broadcast_gpio_event(event_data: dict):
    """
    Рассылает событие GPIO всем подключенным WebSocket клиентам
    """
    if not gpio_connections:
        return

    message = json.dumps(event_data, ensure_ascii=False)
    disconnected_connections = []

    for connection in gpio_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"❌ Ошибка отправки GPIO события: {e}")
            disconnected_connections.append(connection)

    # Удаляем отключенные соединения
    for connection in disconnected_connections:
        if connection in gpio_connections:
            gpio_connections.remove(connection)

    if disconnected_connections:
        print(
            f"🔌 Удалено отключенных GPIO соединений: {len(disconnected_connections)}"
        )
