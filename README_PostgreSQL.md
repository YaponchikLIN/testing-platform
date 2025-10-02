# Интеграция PostgreSQL для сохранения результатов тестов

## Описание

Данная интеграция позволяет сохранять результаты тестов из JSON файлов в базу данных PostgreSQL. После завершения тестов их результаты автоматически сохраняются в базе данных для дальнейшего анализа и отчетности.

## Настройка и запуск

### 1. Запуск PostgreSQL в Docker

```bash
# Перейти в директорию проекта
cd c:\Projects\RTK\testing-platform

# Запустить PostgreSQL контейнер
docker-compose up -d
```

### 2. Установка зависимостей

```bash
# Перейти в директорию API сервиса
cd services\api-service

# Установить зависимости
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Файл `.env` уже создан в `services/api-service/.env` со следующими настройками:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testing_platform
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
```

### 4. Запуск API сервиса

```bash
# Из директории services/api-service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Структура базы данных

### Таблицы:

1. **tests** - Основная таблица тестов
   - `id` (UUID) - Уникальный идентификатор
   - `test_id` (VARCHAR) - ID теста (wifi, sim, ethernets, all)
   - `name` (VARCHAR) - Название теста
   - `description` (TEXT) - Описание теста

2. **test_executions** - Выполнения тестов
   - `id` (UUID) - Уникальный идентификатор выполнения
   - `test_id` (UUID) - Ссылка на тест
   - `status` (VARCHAR) - Статус выполнения
   - `start_time` (TIMESTAMP) - Время начала
   - `end_time` (TIMESTAMP) - Время окончания
   - `progress` (INTEGER) - Прогресс выполнения
   - `result_data` (JSONB) - Результаты в формате JSON

3. **sim_test_results** - Детальные результаты SIM тестов
   - `id` (UUID) - Уникальный идентификатор
   - `execution_id` (UUID) - Ссылка на выполнение
   - `slot_number` (INTEGER) - Номер слота
   - `state_failed_reason` (TEXT) - Причина ошибки
   - `active` (BOOLEAN) - Активность
   - `connected` (BOOLEAN) - Подключение
   - `ping_result` (BOOLEAN) - Результат пинга
   - `packet_loss` (DECIMAL) - Потеря пакетов
   - `response_time` (DECIMAL) - Время отклика
   - `progress` (INTEGER) - Прогресс

4. **ethernet_test_results** - Детальные результаты Ethernet тестов
   - `id` (UUID) - Уникальный идентификатор
   - `execution_id` (UUID) - Ссылка на выполнение
   - `interface_name` (VARCHAR) - Название интерфейса
   - `ping_success` (BOOLEAN) - Успешность пинга
   - `details` (JSONB) - Детальная информация

## Новые API эндпоинты

### Получение списка выполнений тестов
```
GET /tests/executions?test_id=sim&limit=50
```

### Получение деталей выполнения теста
```
GET /tests/executions/{execution_id}
```

### Получение статистики тестов
```
GET /tests/statistics
```

### Получение последнего результата теста
```
GET /tests/results/{test_id}/latest
```

## Как это работает

1. **Выполнение тестов**: При запуске тестов через существующий API, результаты сохраняются в JSON файлы как раньше.

2. **Автоматическое сохранение**: После завершения теста функция `save_test_results_to_db()` автоматически:
   - Создает запись о выполнении теста
   - Анализирует JSON результаты
   - Определяет успешность теста
   - Сохраняет детальные результаты в соответствующие таблицы

3. **Доступ к данным**: Через новые API эндпоинты можно получать:
   - Историю выполнений тестов
   - Детальную информацию о каждом выполнении
   - Статистику по тестам
   - Последние результаты

## Логика определения успешности тестов

- **SIM тесты**: Успешны, если `test_status` = "completed" и нет слотов с `state-failed-reason`
- **Ethernet тесты**: Успешны, если `test_status` = "completed" и все интерфейсы прошли пинг
- **Другие тесты**: Успешны, если `test_status` = "completed"

## Мониторинг и отладка

Все операции с базой данных логируются. Проверить логи можно в консоли API сервиса.

## Резервное копирование

Данные PostgreSQL сохраняются в Docker volume `postgres_data`. Для резервного копирования:

```bash
# Создать бэкап
docker exec -t testing-platform-postgres-1 pg_dump -U test_user testing_platform > backup.sql

# Восстановить из бэкапа
docker exec -i testing-platform-postgres-1 psql -U test_user testing_platform < backup.sql
```