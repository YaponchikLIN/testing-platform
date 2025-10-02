# Техническая документация API

## Обзор API

API сервис построен на FastAPI и предоставляет RESTful интерфейс для управления тестами и получения результатов. Сервис поддерживает асинхронную обработку запросов и WebSocket соединения для real-time обновлений.

## Базовая информация

- **Base URL**: `http://localhost:8000`
- **Документация**: `http://localhost:8000/docs`
- **Формат данных**: JSON
- **Аутентификация**: JWT (в разработке)

## Endpoints

### Управление тестами

#### POST /tests/run
Запуск нового теста

**Параметры запроса:**
```json
{
  "test_id": "sim|ethernets|ports|all",
  "config": {
    // Дополнительные параметры конфигурации
  }
}
```

**Ответ:**
```json
{
  "status": "started",
  "execution_id": "uuid",
  "message": "Test started successfully"
}
```

#### GET /tests/status/{test_id}
Получение статуса выполняющегося теста

**Ответ:**
```json
{
  "test_id": "sim",
  "status": "running|completed|failed",
  "progress": 75,
  "start_time": "2024-01-01T10:00:00Z",
  "estimated_completion": "2024-01-01T10:30:00Z"
}
```

### Результаты тестов

#### GET /tests/executions
Получение списка выполнений тестов

**Параметры запроса:**
- `test_id` (optional): Фильтр по типу теста
- `limit` (optional): Количество записей (по умолчанию 50)
- `offset` (optional): Смещение для пагинации

**Ответ:**
```json
{
  "executions": [
    {
      "id": "uuid",
      "test_id": "sim",
      "status": "completed",
      "start_time": "2024-01-01T10:00:00Z",
      "end_time": "2024-01-01T10:30:00Z",
      "progress": 100,
      "success": true
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### GET /tests/executions/{execution_id}
Получение детальной информации о выполнении теста

**Ответ:**
```json
{
  "id": "uuid",
  "test_id": "sim",
  "status": "completed",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T10:30:00Z",
  "progress": 100,
  "success": true,
  "result_data": {
    // Детальные результаты теста
  },
  "detailed_results": [
    // Массив детальных результатов
  ]
}
```

#### GET /tests/results/{test_id}/latest
Получение последнего результата теста

**Ответ:**
```json
{
  "execution_id": "uuid",
  "test_id": "sim",
  "timestamp": "2024-01-01T10:30:00Z",
  "success": true,
  "summary": {
    "total_slots": 8,
    "successful_slots": 7,
    "failed_slots": 1
  },
  "details": {
    // Детальные результаты
  }
}
```

### Статистика

#### GET /tests/statistics
Получение общей статистики тестов

**Параметры запроса:**
- `period` (optional): Период для статистики (day|week|month)
- `test_id` (optional): Фильтр по типу теста

**Ответ:**
```json
{
  "period": "week",
  "total_executions": 45,
  "successful_executions": 42,
  "failed_executions": 3,
  "success_rate": 93.3,
  "average_duration": "00:25:30",
  "by_test_type": {
    "sim": {
      "executions": 20,
      "success_rate": 95.0
    },
    "ethernets": {
      "executions": 15,
      "success_rate": 90.0
    },
    "ports": {
      "executions": 10,
      "success_rate": 95.0
    }
  }
}
```

## WebSocket API

### Подключение
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### События

#### test_started
Уведомление о начале теста
```json
{
  "event": "test_started",
  "data": {
    "execution_id": "uuid",
    "test_id": "sim",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### test_progress
Обновление прогресса теста
```json
{
  "event": "test_progress",
  "data": {
    "execution_id": "uuid",
    "progress": 45,
    "current_step": "Testing slot 4",
    "timestamp": "2024-01-01T10:15:00Z"
  }
}
```

#### test_completed
Уведомление о завершении теста
```json
{
  "event": "test_completed",
  "data": {
    "execution_id": "uuid",
    "test_id": "sim",
    "success": true,
    "duration": "00:25:30",
    "timestamp": "2024-01-01T10:30:00Z"
  }
}
```

## Модели данных

### TestExecution
```json
{
  "id": "uuid",
  "test_id": "string",
  "status": "pending|running|completed|failed",
  "start_time": "datetime",
  "end_time": "datetime|null",
  "progress": "integer (0-100)",
  "success": "boolean|null",
  "result_data": "object"
}
```

### SimTestResult
```json
{
  "id": "uuid",
  "execution_id": "uuid",
  "slot_number": "integer",
  "state_failed_reason": "string|null",
  "active": "boolean",
  "connected": "boolean",
  "ping_result": "boolean",
  "packet_loss": "decimal",
  "response_time": "decimal",
  "progress": "integer"
}
```

### EthernetTestResult
```json
{
  "id": "uuid",
  "execution_id": "uuid",
  "interface_name": "string",
  "ping_success": "boolean",
  "details": "object"
}
```

## Коды ошибок

### HTTP Status Codes

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс создан
- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Доступ запрещен
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Формат ошибок

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid test_id parameter",
    "details": {
      "field": "test_id",
      "allowed_values": ["sim", "ethernets", "ports", "all"]
    }
  }
}
```

## Примеры использования

### Python
```python
import requests
import asyncio
import websockets

# Запуск теста
response = requests.post('http://localhost:8000/tests/run', 
                        json={'test_id': 'sim'})
execution_id = response.json()['execution_id']

# Получение результатов
result = requests.get(f'http://localhost:8000/tests/executions/{execution_id}')
print(result.json())

# WebSocket подключение
async def listen_updates():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            print(f"Received: {message}")

asyncio.run(listen_updates())
```

### JavaScript
```javascript
// Запуск теста
fetch('http://localhost:8000/tests/run', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({test_id: 'sim'})
})
.then(response => response.json())
.then(data => console.log(data));

// WebSocket подключение
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### cURL
```bash
# Запуск теста
curl -X POST "http://localhost:8000/tests/run" \
     -H "Content-Type: application/json" \
     -d '{"test_id": "sim"}'

# Получение статистики
curl "http://localhost:8000/tests/statistics?period=week"

# Получение последнего результата
curl "http://localhost:8000/tests/results/sim/latest"
```

## Ограничения и рекомендации

### Ограничения
- Максимум 10 одновременных тестов
- Результаты хранятся 30 дней
- WebSocket соединения ограничены 100 одновременными подключениями

### Рекомендации
- Используйте WebSocket для real-time обновлений
- Кэшируйте результаты статистики на клиенте
- Реализуйте retry логику для критических операций
- Используйте пагинацию для больших списков

## Версионирование

API использует семантическое версионирование. Текущая версия: `v1.0.0`

Изменения версий:
- **Major** - Breaking changes
- **Minor** - Новая функциональность (обратно совместимая)
- **Patch** - Исправления ошибок

## Поддержка

Для получения поддержки по API:
1. Проверьте документацию Swagger: `http://localhost:8000/docs`
2. Изучите примеры в репозитории
3. Создайте issue в GitHub репозитории