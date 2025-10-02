# Как проверить сохранение результатов тестов в базу данных

## 🔍 Обзор

В системе тестирования результаты сохраняются в PostgreSQL базу данных. Вот несколько способов проверить, что данные корректно сохраняются.

## 📊 Текущее состояние базы данных

По результатам проверки:
- ✅ База данных PostgreSQL запущена и доступна
- ✅ Все таблицы созданы корректно (`tests`, `test_executions`, `sim_test_results`, `ethernet_test_results`)
- ✅ Тестовые данные загружены (4 теста в таблице `tests`)
- ⚠️ Есть 1 запись в `test_executions`, но нет детальных результатов в `sim_test_results` и `ethernet_test_results`

## 🛠️ Способы проверки

### 1. Прямая проверка через SQL команды

```bash
# Подключение к базе данных
docker exec -it testing_platform_postgres psql -U test_user -d testing_platform

# Основные команды для проверки:
\dt                                    # Список таблиц
\d test_executions                     # Структура таблицы выполнений

# Проверка выполнений тестов
SELECT * FROM test_executions ORDER BY created_at DESC LIMIT 5;

# Проверка результатов SIM тестов
SELECT * FROM sim_test_results ORDER BY created_at DESC LIMIT 5;

# Проверка результатов Ethernet тестов
SELECT * FROM ethernet_test_results ORDER BY created_at DESC LIMIT 5;

# Статистика по статусам
SELECT status, COUNT(*) FROM test_executions GROUP BY status;

# Выход
\q
```

### 2. Использование готового скрипта проверки

```bash
# Запуск автоматической проверки
python check_database.py
```

Этот скрипт:
- Проверяет структуру базы данных
- Показывает количество записей в каждой таблице
- Выводит последние выполнения тестов
- Предлагает вставить тестовые данные

### 3. Проверка через API endpoints

```bash
# Запуск тестового скрипта
python test_database_save.py
```

Этот скрипт:
- Проверяет доступность API
- Получает список выполнений через `/tests/executions`
- Показывает статистику через `/tests/statistics`
- Запускает новый тест и проверяет его сохранение

### 4. Ручная проверка через API

```bash
# Получение списка выполнений
curl http://localhost:8000/tests/executions

# Получение статистики
curl http://localhost:8000/tests/statistics

# Получение деталей конкретного выполнения
curl http://localhost:8000/tests/executions/{execution_id}
```

## 🧪 Тестирование сохранения новых результатов

### Запуск SIM теста через API

```bash
curl -X POST http://localhost:8000/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "sim",
    "config": {
      "slots": [1, 2],
      "ping_target": "8.8.8.8",
      "timeout": 30
    }
  }'
```

### Запуск Ethernet теста через API

```bash
curl -X POST http://localhost:8000/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "ethernet",
    "config": {
      "interfaces": ["eth0", "eth1"],
      "ping_target": "8.8.8.8",
      "timeout": 30
    }
  }'
```

## 📈 Мониторинг в реальном времени

### Отслеживание новых записей

```sql
-- Мониторинг новых выполнений (запустить в отдельном терминале)
WATCH 'docker exec testing_platform_postgres psql -U test_user -d testing_platform -c "SELECT COUNT(*) as total_executions FROM test_executions;"'

-- Или через SQL в psql:
SELECT NOW() as check_time, 
       (SELECT COUNT(*) FROM test_executions) as total_executions,
       (SELECT COUNT(*) FROM sim_test_results) as sim_results,
       (SELECT COUNT(*) FROM ethernet_test_results) as ethernet_results;
```

## 🔧 Устранение проблем

### Если результаты не сохраняются:

1. **Проверьте подключение к базе данных:**
   ```bash
   docker logs testing_platform_postgres
   ```

2. **Проверьте логи API сервиса:**
   ```bash
   # Если API запущен через uvicorn, проверьте терминал
   # Или проверьте логи контейнера, если API в Docker
   ```

3. **Проверьте переменные окружения:**
   ```bash
   cat services/api-service/.env
   ```

4. **Проверьте права доступа пользователя базы данных:**
   ```sql
   -- В psql
   \du  -- список пользователей и их прав
   ```

### Если база данных недоступна:

```bash
# Перезапуск контейнера PostgreSQL
docker-compose down
docker-compose up -d

# Проверка статуса
docker ps
docker logs testing_platform_postgres
```

## 📝 Структура данных

### Таблица `test_executions`
- `id` - уникальный идентификатор выполнения
- `test_id` - тип теста (sim, ethernet, all)
- `status` - статус (running, completed, failed)
- `time_start`, `time_end` - время начала и окончания
- `result_passed` - результат теста (true/false)
- `result_details` - детали результата (JSON)

### Таблица `sim_test_results`
- `execution_id` - связь с выполнением
- `slot_number` - номер слота SIM карты
- `active`, `connected` - статусы подключения
- `ping_result`, `packet_loss`, `response_time` - результаты пинга

### Таблица `ethernet_test_results`
- `execution_id` - связь с выполнением
- `interface_name` - имя сетевого интерфейса
- `ip_address` - IP адрес
- `ping_result`, `packet_loss`, `response_time` - результаты пинга
- `status` - статус интерфейса

## ✅ Контрольный список проверки

- [ ] PostgreSQL контейнер запущен
- [ ] API сервис запущен и подключен к базе
- [ ] Таблицы созданы и содержат данные
- [ ] API endpoints отвечают корректно
- [ ] Новые тесты создают записи в `test_executions`
- [ ] Детальные результаты сохраняются в соответствующих таблицах
- [ ] Статистика обновляется после выполнения тестов

---

**💡 Совет:** Для регулярного мониторинга используйте скрипт `check_database.py` или настройте автоматические проверки через cron/планировщик задач.