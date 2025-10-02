# Платформа тестирования RTK

## Описание проекта

Платформа тестирования RTK - это комплексная система для автоматизированного тестирования сетевого оборудования, включающая тестирование SIM-карт, Ethernet интерфейсов и других компонентов сетевой инфраструктуры. Система построена на микросервисной архитектуре и использует Robot Framework для выполнения тестов.

## Архитектура системы

### Основные компоненты

1. **Frontend (Vue.js)** - Веб-интерфейс для управления тестами
2. **API Service (FastAPI)** - Backend сервис для управления тестами и данными
3. **Robot Framework Tests** - Автоматизированные тесты оборудования
4. **PostgreSQL Database** - База данных для хранения результатов тестов
5. **Hardware Integration** - Интеграция с физическим оборудованием

### Технологический стек

- **Frontend**: Vue.js 3, PrimeVue, Pinia, Sass
- **Backend**: FastAPI, Python, asyncpg
- **Database**: PostgreSQL 15
- **Testing**: Robot Framework
- **Containerization**: Docker, Docker Compose
- **Real-time Communication**: WebSockets

## Структура проекта

```
testing-platform/
├── frontend/                    # Vue.js фронтенд приложение
│   ├── src/
│   │   ├── components/         # Vue компоненты
│   │   ├── stores/            # Pinia stores
│   │   ├── api/               # API клиенты
│   │   └── App.vue            # Главный компонент
│   └── package.json
├── services/
│   └── api-service/            # FastAPI backend сервис
│       ├── main.py            # Главный файл приложения
│       ├── test_service.py    # Логика выполнения тестов
│       ├── db/                # Модули базы данных
│       ├── websocket/         # WebSocket endpoints
│       └── requirements.txt
├── robot-tests/                # Robot Framework тесты
│   ├── sim.robot             # Тесты SIM-карт
│   ├── ethernets.robot       # Тесты Ethernet
│   ├── ports.robot           # Тесты портов
│   └── config.json           # Конфигурация тестов
├── docs/                      # Документация проекта
├── hardware-integration/      # Интеграция с оборудованием
├── docker-compose.yml         # Docker конфигурация
└── init.sql                  # Инициализация БД
```

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Node.js 16+ (для разработки frontend)
- Python 3.8+ (для разработки backend)
- Robot Framework

### Установка и запуск

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd testing-platform
```

2. **Запуск базы данных**
```bash
docker-compose up -d
```

3. **Запуск API сервиса**
```bash
cd services/api-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Запуск frontend приложения**
```bash
cd frontend
npm install
npm run serve
```

5. **Доступ к приложению**
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432

## Функциональность

### Типы тестов

1. **SIM тесты** - Тестирование SIM-карт и мобильных соединений
2. **Ethernet тесты** - Тестирование сетевых интерфейсов
3. **Порты тесты** - Тестирование портов коммутатора

### Основные возможности

- ✅ Запуск автоматизированных тестов через веб-интерфейс
- ✅ Мониторинг выполнения тестов в реальном времени
- ✅ Сохранение и анализ результатов тестов
- ✅ Интеграция с PostgreSQL для хранения данных
- ✅ WebSocket для обновлений в реальном времени
- ✅ REST API для интеграции с внешними системами

## API Endpoints

### Основные endpoints

- `GET /tests/executions` - Получение списка выполнений тестов
- `GET /tests/executions/{execution_id}` - Детали выполнения теста
- `GET /tests/statistics` - Статистика тестов
- `GET /tests/results/{test_id}/latest` - Последний результат теста
- `POST /tests/run` - Запуск теста
- `WebSocket /ws` - Real-time обновления

Полная документация API доступна по адресу: http://localhost:8000/docs

## База данных

### Структура таблиц

1. **tests** - Основная таблица тестов
2. **test_executions** - Выполнения тестов
3. **sim_test_results** - Результаты SIM тестов
4. **ethernet_test_results** - Результаты Ethernet тестов

### Подключение к базе данных

```bash
# Подключение к PostgreSQL
docker exec -it testing_platform_postgres psql -U test_user -d testing_platform

# Создание бэкапа
docker exec -t testing_platform_postgres pg_dump -U test_user testing_platform > backup.sql
```

## Разработка

### Структура кода

#### Frontend (Vue.js)
- Компонентная архитектура
- Управление состоянием через Pinia
- Адаптивный дизайн с PrimeVue
- TypeScript поддержка

#### Backend (FastAPI)
- Асинхронная архитектура
- Модульная структура
- WebSocket поддержка
- PostgreSQL интеграция

#### Robot Framework тесты
- Page Object Model паттерн
- Модульная организация тестов
- JSON отчеты
- Интеграция с оборудованием

### Добавление новых тестов

1. Создать новый .robot файл в папке `robot-tests/`
2. Определить ключевые слова и тест-кейсы
3. Добавить конфигурацию в `config.json`
4. Обновить API для поддержки нового типа теста

### Конфигурация

Основные конфигурационные файлы:
- `robot-tests/config.json` - Конфигурация тестов
- `services/api-service/.env` - Переменные окружения
- `docker-compose.yml` - Docker конфигурация

## Мониторинг и логирование

- Логи API сервиса выводятся в консоль
- Результаты тестов сохраняются в JSON формате
- PostgreSQL логи доступны через Docker
- WebSocket события для real-time мониторинга

## Безопасность

- JWT аутентификация (в разработке)
- CORS настройки для frontend
- Валидация входных данных
- Безопасное хранение конфигураций

## Производительность

- Асинхронная обработка запросов
- Параллельное выполнение тестов
- Оптимизированные SQL запросы
- Кэширование результатов

## Развертывание

### Production развертывание

1. Настроить переменные окружения
2. Собрать frontend: `npm run build`
3. Запустить через Docker Compose
4. Настроить reverse proxy (nginx)
5. Настроить SSL сертификаты

### Docker развертывание

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

## Тестирование

### Запуск тестов

```bash
# Robot Framework тесты
cd robot-tests
robot sim.robot

# API тесты
cd services/api-service
python -m pytest

# Frontend тесты
cd frontend
npm run test
```

## Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к БД**
   - Проверить статус Docker контейнера
   - Проверить переменные окружения

2. **Тесты не запускаются**
   - Проверить конфигурацию Robot Framework
   - Проверить доступность оборудования

3. **Frontend не загружается**
   - Проверить CORS настройки
   - Проверить доступность API

## Вклад в проект

1. Fork репозитория
2. Создать feature branch
3. Внести изменения
4. Добавить тесты
5. Создать Pull Request

## Лицензия

[Указать лицензию проекта]

## Контакты

[Указать контактную информацию команды разработки]

---

Для получения дополнительной информации см. документацию в папке `docs/`.