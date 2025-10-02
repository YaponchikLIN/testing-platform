# Техническая документация разработчика

## Обзор архитектуры

### Общая архитектура системы

Платформа тестирования RTK построена на микросервисной архитектуре с четким разделением ответственности между компонентами:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Service   │    │   Database      │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Robot Framework │
                       │ Test Executor   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Hardware Layer  │
                       │ (Orange Pi)     │
                       └─────────────────┘
```

### Архитектурные паттерны

#### 1. Микросервисная архитектура
- **Frontend Service**: Vue.js приложение для пользовательского интерфейса
- **API Service**: FastAPI сервис для обработки запросов и управления тестами
- **Database Service**: PostgreSQL для хранения данных
- **Test Executor**: Robot Framework для выполнения тестов

#### 2. Паттерн адаптера устройств
```python
# Абстрактный интерфейс для устройств
class DeviceAdapter:
    def connect(self) -> bool: pass
    def test(self) -> TestResult: pass
    def disconnect(self) -> bool: pass

# Конкретные реализации
class SIMAdapter(DeviceAdapter): ...
class EthernetAdapter(DeviceAdapter): ...
class PortAdapter(DeviceAdapter): ...
```

#### 3. Repository Pattern
```python
class TestRepository:
    def save_test_execution(self, execution: TestExecution) -> str: pass
    def get_test_execution(self, execution_id: str) -> TestExecution: pass
    def get_test_history(self, filters: dict) -> List[TestExecution]: pass
```

#### 4. Event Sourcing + CQRS
- **Commands**: Команды для изменения состояния (запуск тестов, остановка)
- **Events**: События о изменениях состояния (тест запущен, завершен)
- **Queries**: Запросы для чтения данных (результаты, статистика)

## Структура проекта

### Детальная структура директорий

```
testing-platform/
├── frontend/                    # Vue.js приложение
│   ├── src/
│   │   ├── components/         # Vue компоненты
│   │   │   ├── TestControl.vue # Панель управления тестами
│   │   │   ├── TestResults.vue # Отображение результатов
│   │   │   ├── TestHistory.vue # История тестов
│   │   │   └── StatusPanel.vue # Панель статуса
│   │   ├── stores/             # Pinia stores
│   │   │   ├── testStore.js    # Состояние тестов
│   │   │   ├── uiStore.js      # Состояние UI
│   │   │   └── authStore.js    # Аутентификация
│   │   ├── services/           # API сервисы
│   │   │   ├── api.js          # Основной API клиент
│   │   │   ├── websocket.js    # WebSocket клиент
│   │   │   └── auth.js         # Сервис аутентификации
│   │   ├── router/             # Vue Router
│   │   ├── assets/             # Статические ресурсы
│   │   └── utils/              # Утилиты
│   ├── public/                 # Публичные файлы
│   ├── package.json            # Зависимости Node.js
│   └── vite.config.js          # Конфигурация Vite
│
├── api-service/                # FastAPI сервис
│   ├── app/
│   │   ├── main.py             # Точка входа FastAPI
│   │   ├── models/             # Модели данных
│   │   │   ├── test_models.py  # Модели тестов
│   │   │   ├── user_models.py  # Модели пользователей
│   │   │   └── device_models.py# Модели устройств
│   │   ├── routers/            # API роутеры
│   │   │   ├── tests.py        # Эндпоинты тестов
│   │   │   ├── results.py      # Эндпоинты результатов
│   │   │   ├── devices.py      # Эндпоинты устройств
│   │   │   └── auth.py         # Эндпоинты аутентификации
│   │   ├── services/           # Бизнес-логика
│   │   │   ├── test_service.py # Сервис тестов
│   │   │   ├── device_service.py# Сервис устройств
│   │   │   └── notification_service.py # Уведомления
│   │   ├── repositories/       # Репозитории данных
│   │   │   ├── test_repository.py
│   │   │   ├── user_repository.py
│   │   │   └── device_repository.py
│   │   ├── adapters/           # Адаптеры устройств
│   │   │   ├── sim_adapter.py  # Адаптер SIM
│   │   │   ├── ethernet_adapter.py # Адаптер Ethernet
│   │   │   └── port_adapter.py # Адаптер портов
│   │   ├── core/               # Основные компоненты
│   │   │   ├── config.py       # Конфигурация
│   │   │   ├── database.py     # Подключение к БД
│   │   │   ├── security.py     # Безопасность
│   │   │   └── exceptions.py   # Исключения
│   │   └── utils/              # Утилиты
│   ├── requirements.txt        # Python зависимости
│   └── Dockerfile              # Docker образ
│
├── robot-tests/                # Robot Framework тесты
│   ├── tests/
│   │   ├── sim.robot           # SIM тесты
│   │   ├── ethernets.robot     # Ethernet тесты
│   │   └── ports.robot         # Тесты портов
│   ├── keywords/               # Ключевые слова
│   │   ├── sim_keywords.robot  # SIM ключевые слова
│   │   ├── ethernet_keywords.robot
│   │   └── port_keywords.robot
│   ├── libraries/              # Python библиотеки
│   │   ├── SIMLibrary.py       # Библиотека SIM
│   │   ├── EthernetLibrary.py  # Библиотека Ethernet
│   │   └── PortLibrary.py      # Библиотека портов
│   ├── resources/              # Ресурсы и конфигурация
│   │   ├── config.json         # Конфигурация тестов
│   │   └── variables.robot     # Переменные
│   └── results/                # Результаты тестов
│
├── database/                   # База данных
│   ├── migrations/             # Миграции
│   ├── init.sql               # Инициализация БД
│   └── schema.sql             # Схема БД
│
├── docker/                     # Docker конфигурация
│   ├── docker-compose.yml      # Основная конфигурация
│   ├── docker-compose.dev.yml  # Разработка
│   └── docker-compose.prod.yml # Продакшн
│
├── docs/                       # Документация
│   ├── README.md               # Основная документация
│   ├── API_DOCUMENTATION.md    # API документация
│   ├── DEPLOYMENT_GUIDE.md     # Руководство по развертыванию
│   ├── USER_GUIDE.md           # Руководство пользователя
│   └── DEVELOPER_GUIDE.md      # Руководство разработчика
│
├── scripts/                    # Скрипты
│   ├── setup.sh               # Скрипт установки
│   ├── deploy.sh              # Скрипт развертывания
│   └── backup.sh              # Скрипт резервного копирования
│
└── monitoring/                 # Мониторинг
    ├── prometheus.yml          # Конфигурация Prometheus
    ├── grafana/               # Дашборды Grafana
    └── alerts/                # Правила алертов
```

## Технологический стек

### Frontend

#### Vue.js 3 + Composition API
```javascript
// Пример компонента с Composition API
import { ref, computed, onMounted } from 'vue'
import { useTestStore } from '@/stores/testStore'

export default {
  setup() {
    const testStore = useTestStore()
    const isLoading = ref(false)
    
    const canStartTest = computed(() => 
      !testStore.isRunning && !isLoading.value
    )
    
    const startTest = async (testType) => {
      isLoading.value = true
      try {
        await testStore.startTest(testType)
      } finally {
        isLoading.value = false
      }
    }
    
    return { canStartTest, startTest }
  }
}
```

#### Pinia для управления состоянием
```javascript
// stores/testStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTestStore = defineStore('test', () => {
  const currentTest = ref(null)
  const testHistory = ref([])
  const isRunning = ref(false)
  
  const latestTest = computed(() => 
    testHistory.value[0] || null
  )
  
  const startTest = async (testType) => {
    isRunning.value = true
    // API вызов
  }
  
  return { 
    currentTest, 
    testHistory, 
    isRunning, 
    latestTest, 
    startTest 
  }
})
```

#### PrimeVue для UI компонентов
```vue
<template>
  <div class="test-control">
    <Button 
      label="Запустить SIM тест" 
      icon="pi pi-play"
      :loading="isLoading"
      @click="startTest('sim')"
      class="p-button-success"
    />
    
    <ProgressBar 
      :value="progress" 
      :showValue="true"
      class="mt-3"
    />
    
    <DataTable 
      :value="testHistory" 
      :paginator="true"
      :rows="10"
    >
      <Column field="date" header="Дата" />
      <Column field="type" header="Тип" />
      <Column field="status" header="Статус" />
    </DataTable>
  </div>
</template>
```

### Backend

#### FastAPI с асинхронной обработкой
```python
# main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(title="RTK Testing Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/tests/run")
async def run_test(test_request: TestRequest):
    """Запуск теста"""
    execution_id = await test_service.start_test(test_request)
    return {"execution_id": execution_id}

@app.websocket("/ws/test-status")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await websocket.accept()
    while True:
        status = await get_test_status()
        await websocket.send_json(status)
        await asyncio.sleep(1)
```

#### Pydantic модели
```python
# models/test_models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TestType(str, Enum):
    SIM = "sim"
    ETHERNET = "ethernet"
    PORTS = "ports"
    FULL = "full"

class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TestRequest(BaseModel):
    test_type: TestType
    parameters: Optional[dict] = {}
    
class TestExecution(BaseModel):
    id: str
    test_type: TestType
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None  # секунды
    results: Optional[dict] = None
    error_message: Optional[str] = None
    
class TestResult(BaseModel):
    execution_id: str
    component: str
    status: str
    details: dict
    timestamp: datetime
```

#### SQLAlchemy с асинхронным драйвером
```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/rtk_testing"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# models/database_models.py
from sqlalchemy import Column, String, DateTime, JSON, Integer
from core.database import Base

class TestExecutionDB(Base):
    __tablename__ = "test_executions"
    
    id = Column(String, primary_key=True)
    test_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration = Column(Integer)
    results = Column(JSON)
    error_message = Column(String)
```

### Robot Framework

#### Структура тестов
```robot
# tests/sim.robot
*** Settings ***
Documentation    SIM карты тестирование
Library          ../libraries/SIMLibrary.py
Resource         ../keywords/sim_keywords.robot
Variables        ../resources/variables.robot

*** Test Cases ***
Test SIM Slot 1
    [Documentation]    Тестирование SIM слота 1
    [Tags]    sim    slot1
    ${result}=    Test SIM Slot    1
    Should Be Equal    ${result.status}    success
    
Test SIM Slot 2
    [Documentation]    Тестирование SIM слота 2
    [Tags]    sim    slot2
    ${result}=    Test SIM Slot    2
    Should Be Equal    ${result.status}    success

*** Keywords ***
Test SIM Slot
    [Arguments]    ${slot_number}
    [Documentation]    Тестирование конкретного SIM слота
    
    Log    Тестирование SIM слота ${slot_number}
    
    # Проверка активности SIM карты
    ${is_active}=    Check SIM Activity    ${slot_number}
    Should Be True    ${is_active}    SIM карта в слоте ${slot_number} неактивна
    
    # Проверка подключения к сети
    ${network_status}=    Check Network Connection    ${slot_number}
    Should Be Equal    ${network_status}    connected
    
    # Ping тест
    ${ping_result}=    Ping Test    ${slot_number}    ${PING_TARGET}
    Should Be True    ${ping_result.success}
    Should Be Less Than    ${ping_result.avg_time}    ${MAX_PING_TIME}
    
    [Return]    Create Dictionary    
    ...    status=success    
    ...    slot=${slot_number}    
    ...    ping_time=${ping_result.avg_time}
```

#### Python библиотеки для Robot Framework
```python
# libraries/SIMLibrary.py
from robot.api.deco import keyword
import subprocess
import json
import time

class SIMLibrary:
    """Библиотека для тестирования SIM карт"""
    
    def __init__(self):
        self.ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    
    @keyword
    def check_sim_activity(self, slot_number):
        """Проверка активности SIM карты в слоте"""
        try:
            # Выполнение команды для проверки SIM
            result = subprocess.run(
                ['mmcli', '-L'], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                # Парсинг вывода для определения активности
                return self._parse_sim_status(result.stdout, slot_number)
            else:
                return False
                
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"Ошибка проверки SIM: {e}")
            return False
    
    @keyword
    def ping_test(self, slot_number, target_ip, count=10):
        """Ping тест через SIM соединение"""
        interface = f"wwan{slot_number}"
        
        try:
            result = subprocess.run([
                'ping', '-I', interface, '-c', str(count), target_ip
            ], capture_output=True, text=True, timeout=60)
            
            return self._parse_ping_result(result.stdout)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'avg_time': 0,
                'packet_loss': 100
            }
    
    def _parse_sim_status(self, output, slot_number):
        """Парсинг статуса SIM карты"""
        # Логика парсинга вывода mmcli
        lines = output.split('\n')
        for line in lines:
            if f"Modem/{slot_number}" in line and "state: connected" in line:
                return True
        return False
    
    def _parse_ping_result(self, output):
        """Парсинг результатов ping"""
        lines = output.split('\n')
        
        # Поиск строки со статистикой
        for line in lines:
            if 'packet loss' in line:
                # Извлечение процента потерь
                loss_percent = float(line.split('%')[0].split()[-1])
                
            if 'avg' in line and 'ms' in line:
                # Извлечение среднего времени
                avg_time = float(line.split('/')[1])
                
        return {
            'success': loss_percent < 100,
            'avg_time': avg_time,
            'packet_loss': loss_percent
        }
```

## API Документация

### REST API Endpoints

#### Управление тестами

```python
# routers/tests.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid

router = APIRouter(prefix="/api/tests", tags=["tests"])

@router.post("/run", response_model=TestExecutionResponse)
async def run_test(
    test_request: TestRequest,
    test_service: TestService = Depends(get_test_service)
):
    """
    Запуск нового теста
    
    - **test_type**: Тип теста (sim, ethernet, ports, full)
    - **parameters**: Дополнительные параметры теста
    """
    try:
        execution_id = await test_service.start_test(test_request)
        return TestExecutionResponse(execution_id=execution_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=TestExecution)
async def get_test_execution(
    execution_id: str,
    test_service: TestService = Depends(get_test_service)
):
    """Получение информации о выполнении теста"""
    execution = await test_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Test execution not found")
    return execution

@router.get("/executions", response_model=List[TestExecution])
async def get_test_history(
    limit: int = 50,
    offset: int = 0,
    test_type: Optional[TestType] = None,
    status: Optional[TestStatus] = None,
    test_service: TestService = Depends(get_test_service)
):
    """Получение истории тестов с фильтрацией"""
    filters = {}
    if test_type:
        filters['test_type'] = test_type
    if status:
        filters['status'] = status
        
    return await test_service.get_test_history(
        limit=limit, 
        offset=offset, 
        filters=filters
    )

@router.post("/executions/{execution_id}/stop")
async def stop_test_execution(
    execution_id: str,
    test_service: TestService = Depends(get_test_service)
):
    """Остановка выполняющегося теста"""
    success = await test_service.stop_test(execution_id)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Cannot stop test execution"
        )
    return {"message": "Test execution stopped"}
```

#### WebSocket для real-time обновлений

```python
# routers/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Удаление неактивных соединений
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws/test-status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Отправка текущего статуса каждую секунду
            status = await get_current_test_status()
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Сервисный слой

```python
# services/test_service.py
from typing import Optional, List, Dict
import asyncio
import uuid
from datetime import datetime

class TestService:
    def __init__(self, test_repository: TestRepository, robot_executor: RobotExecutor):
        self.test_repository = test_repository
        self.robot_executor = robot_executor
        self.running_tests: Dict[str, asyncio.Task] = {}
    
    async def start_test(self, test_request: TestRequest) -> str:
        """Запуск нового теста"""
        execution_id = str(uuid.uuid4())
        
        # Создание записи о выполнении
        execution = TestExecution(
            id=execution_id,
            test_type=test_request.test_type,
            status=TestStatus.PENDING,
            started_at=datetime.utcnow(),
            parameters=test_request.parameters
        )
        
        await self.test_repository.save_execution(execution)
        
        # Запуск теста в фоне
        task = asyncio.create_task(
            self._execute_test(execution_id, test_request)
        )
        self.running_tests[execution_id] = task
        
        return execution_id
    
    async def _execute_test(self, execution_id: str, test_request: TestRequest):
        """Выполнение теста"""
        try:
            # Обновление статуса на "выполняется"
            await self.test_repository.update_status(
                execution_id, 
                TestStatus.RUNNING
            )
            
            # Выполнение Robot Framework тестов
            results = await self.robot_executor.run_test(
                test_request.test_type,
                test_request.parameters
            )
            
            # Сохранение результатов
            await self.test_repository.update_results(
                execution_id,
                TestStatus.COMPLETED,
                results,
                datetime.utcnow()
            )
            
        except Exception as e:
            # Обработка ошибок
            await self.test_repository.update_results(
                execution_id,
                TestStatus.FAILED,
                None,
                datetime.utcnow(),
                str(e)
            )
        finally:
            # Удаление из списка выполняющихся
            self.running_tests.pop(execution_id, None)
    
    async def stop_test(self, execution_id: str) -> bool:
        """Остановка теста"""
        if execution_id in self.running_tests:
            task = self.running_tests[execution_id]
            task.cancel()
            
            await self.test_repository.update_status(
                execution_id,
                TestStatus.CANCELLED
            )
            return True
        return False
    
    async def get_execution(self, execution_id: str) -> Optional[TestExecution]:
        """Получение информации о выполнении"""
        return await self.test_repository.get_execution(execution_id)
    
    async def get_test_history(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        filters: dict = None
    ) -> List[TestExecution]:
        """Получение истории тестов"""
        return await self.test_repository.get_history(limit, offset, filters)
```

### Robot Framework интеграция

```python
# services/robot_executor.py
import subprocess
import json
import os
from pathlib import Path

class RobotExecutor:
    def __init__(self, robot_tests_path: str):
        self.robot_tests_path = Path(robot_tests_path)
    
    async def run_test(self, test_type: str, parameters: dict) -> dict:
        """Выполнение Robot Framework теста"""
        
        # Определение файла теста
        test_file = self._get_test_file(test_type)
        
        # Подготовка переменных
        variables = self._prepare_variables(parameters)
        
        # Формирование команды
        cmd = [
            'robot',
            '--outputdir', str(self.robot_tests_path / 'results'),
            '--output', f'{test_type}_output.xml',
            '--log', f'{test_type}_log.html',
            '--report', f'{test_type}_report.html',
            '--variable', f'TEST_TYPE:{test_type}',
        ]
        
        # Добавление переменных
        for key, value in variables.items():
            cmd.extend(['--variable', f'{key}:{value}'])
        
        cmd.append(str(test_file))
        
        # Выполнение команды
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Парсинг результатов
        results = await self._parse_results(test_type)
        
        return {
            'return_code': process.returncode,
            'stdout': stdout.decode(),
            'stderr': stderr.decode(),
            'results': results
        }
    
    def _get_test_file(self, test_type: str) -> Path:
        """Получение файла теста по типу"""
        test_files = {
            'sim': 'tests/sim.robot',
            'ethernet': 'tests/ethernets.robot',
            'ports': 'tests/ports.robot',
            'full': 'tests/full_test.robot'
        }
        
        return self.robot_tests_path / test_files[test_type]
    
    def _prepare_variables(self, parameters: dict) -> dict:
        """Подготовка переменных для Robot Framework"""
        variables = {}
        
        # Преобразование параметров в переменные Robot Framework
        for key, value in parameters.items():
            variables[key.upper()] = str(value)
        
        return variables
    
    async def _parse_results(self, test_type: str) -> dict:
        """Парсинг результатов Robot Framework"""
        output_file = self.robot_tests_path / 'results' / f'{test_type}_output.xml'
        
        if not output_file.exists():
            return {}
        
        # Парсинг XML результатов
        # Здесь должна быть логика парсинга XML файла Robot Framework
        # Возвращение структурированных результатов
        
        return {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
```

## База данных

### Схема базы данных

```sql
-- database/schema.sql

-- Таблица выполнений тестов
CREATE TABLE test_executions (
    id VARCHAR(36) PRIMARY KEY,
    test_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration INTEGER, -- в секундах
    results JSONB,
    error_message TEXT,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица результатов тестов
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES test_executions(id),
    component VARCHAR(50) NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER,
    error_message TEXT
);

-- Таблица устройств
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    configuration JSONB,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сессий
CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_test_executions_type_status ON test_executions(test_type, status);
CREATE INDEX idx_test_executions_started_at ON test_executions(started_at);
CREATE INDEX idx_test_results_execution_id ON test_results(execution_id);
CREATE INDEX idx_test_results_component ON test_results(component);
CREATE INDEX idx_devices_type_status ON devices(type, status);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_test_executions_updated_at 
    BEFORE UPDATE ON test_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Миграции

```python
# database/migrations/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Создание таблиц
    op.create_table(
        'test_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('test_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration', sa.Integer),
        sa.Column('results', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Создание индексов
    op.create_index(
        'idx_test_executions_type_status',
        'test_executions',
        ['test_type', 'status']
    )

def downgrade():
    op.drop_table('test_executions')
```

## Развертывание

### Docker конфигурация

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    depends_on:
      - api-service

  api-service:
    build:
      context: ./api-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://rtk_user:rtk_password@database:5432/rtk_testing
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - database
      - redis
    volumes:
      - ./robot-tests:/app/robot-tests
      - ./logs:/app/logs

  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=rtk_testing
      - POSTGRES_USER=rtk_user
      - POSTGRES_PASSWORD=rtk_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Dockerfile для API сервиса

```dockerfile
# api-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile для Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Копирование исходного кода и сборка
COPY . .
RUN npm run build

# Production образ
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## Мониторинг и логирование

### Prometheus метрики

```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Метрики тестов
test_executions_total = Counter(
    'test_executions_total',
    'Total number of test executions',
    ['test_type', 'status']
)

test_duration_seconds = Histogram(
    'test_duration_seconds',
    'Test execution duration in seconds',
    ['test_type']
)

active_tests_gauge = Gauge(
    'active_tests',
    'Number of currently running tests'
)

# Метрики API
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Middleware для метрик
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Структурированное логирование

```python
# core/logging.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Форматтер для JSON логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Хендлер для файла
        file_handler = logging.FileHandler('/app/logs/app.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_test_event(self, event_type: str, execution_id: str, **kwargs):
        """Логирование событий тестов"""
        log_data = {
            'event_type': event_type,
            'execution_id': execution_id,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_api_request(self, method: str, path: str, status: int, duration: float):
        """Логирование API запросов"""
        log_data = {
            'event_type': 'api_request',
            'method': method,
            'path': path,
            'status': status,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Логирование ошибок"""
        log_data = {
            'event_type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if context:
            log_data['context'] = context
            
        self.logger.error(json.dumps(log_data))

# Использование
logger = StructuredLogger(__name__)

# В сервисе тестов
async def start_test(self, test_request: TestRequest) -> str:
    execution_id = str(uuid.uuid4())
    
    logger.log_test_event(
        'test_started',
        execution_id,
        test_type=test_request.test_type,
        parameters=test_request.parameters
    )
    
    # ... логика запуска теста
```

## Безопасность

### JWT аутентификация

```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Dependency для проверки аутентификации
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = await get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
```

### Валидация входных данных

```python
# models/validation.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re

class TestRequest(BaseModel):
    test_type: TestType
    parameters: Optional[dict] = Field(default_factory=dict)
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        test_type = values.get('test_type')
        
        if test_type == TestType.SIM:
            # Валидация параметров SIM тестов
            if 'slots' in v:
                slots = v['slots']
                if not isinstance(slots, list) or not all(isinstance(s, int) for s in slots):
                    raise ValueError('slots must be a list of integers')
                if not all(1 <= s <= 8 for s in slots):
                    raise ValueError('slot numbers must be between 1 and 8')
        
        elif test_type == TestType.ETHERNET:
            # Валидация параметров Ethernet тестов
            if 'interfaces' in v:
                interfaces = v['interfaces']
                if not isinstance(interfaces, list):
                    raise ValueError('interfaces must be a list')
                for interface in interfaces:
                    if not re.match(r'^eth\d+$', interface):
                        raise ValueError(f'invalid interface name: {interface}')
        
        return v

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('username can only contain letters, numbers and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('password must contain at least one digit')
        return v
```

## Тестирование

### Unit тесты

```python
# tests/test_test_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.test_service import TestService
from app.models.test_models import TestRequest, TestType

@pytest.fixture
def test_service():
    test_repository = AsyncMock()
    robot_executor = AsyncMock()
    return TestService(test_repository, robot_executor)

@pytest.mark.asyncio
async def test_start_test_success(test_service):
    # Arrange
    test_request = TestRequest(test_type=TestType.SIM)
    test_service.robot_executor.run_test.return_value = {
        'return_code': 0,
        'results': {'total_tests': 5, 'passed_tests': 5}
    }
    
    # Act
    execution_id = await test_service.start_test(test_request)
    
    # Assert
    assert execution_id is not None
    test_service.test_repository.save_execution.assert_called_once()

@pytest.mark.asyncio
async def test_start_test_failure(test_service):
    # Arrange
    test_request = TestRequest(test_type=TestType.SIM)
    test_service.robot_executor.run_test.side_effect = Exception("Test failed")
    
    # Act
    execution_id = await test_service.start_test(test_request)
    
    # Assert
    assert execution_id is not None
    # Проверка, что ошибка была обработана
```

### Интеграционные тесты

```python
# tests/test_api_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_run_test_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/tests/run",
            json={"test_type": "sim", "parameters": {}}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data

@pytest.mark.asyncio
async def test_get_test_history():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/tests/executions")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### E2E тесты

```python
# tests/test_e2e.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_full_test_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Переход на главную страницу
        await page.goto("http://localhost:3000")
        
        # Запуск SIM теста
        await page.click('button:has-text("SIM тест")')
        
        # Ожидание завершения теста
        await page.wait_for_selector('.test-completed', timeout=60000)
        
        # Проверка результатов
        results = await page.text_content('.test-results')
        assert "Успешно" in results
        
        await browser.close()
```

## Производительность

### Оптимизация базы данных

```sql
-- Индексы для оптимизации запросов
CREATE INDEX CONCURRENTLY idx_test_executions_composite 
ON test_executions(test_type, status, started_at DESC);

CREATE INDEX CONCURRENTLY idx_test_results_execution_component 
ON test_results(execution_id, component);

-- Партиционирование таблицы результатов по дате
CREATE TABLE test_executions_partitioned (
    LIKE test_executions INCLUDING ALL
) PARTITION BY RANGE (started_at);

-- Создание партиций по месяцам
CREATE TABLE test_executions_2024_01 PARTITION OF test_executions_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Автоматическая очистка старых данных
CREATE OR REPLACE FUNCTION cleanup_old_test_data()
RETURNS void AS $$
BEGIN
    DELETE FROM test_executions 
    WHERE started_at < NOW() - INTERVAL '6 months';
    
    DELETE FROM test_results 
    WHERE execution_id NOT IN (SELECT id FROM test_executions);
END;
$$ LANGUAGE plpgsql;

-- Планировщик для очистки
SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_test_data();');
```

### Кэширование

```python
# core/cache.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: timedelta = timedelta(hours=1)):
        """Сохранение значения в кэш"""
        await self.redis.setex(
            key, 
            int(ttl.total_seconds()), 
            json.dumps(value, default=str)
        )
    
    async def delete(self, key: str):
        """Удаление значения из кэша"""
        await self.redis.delete(key)

# Использование в сервисах
class TestService:
    def __init__(self, test_repository, robot_executor, cache_service):
        self.test_repository = test_repository
        self.robot_executor = robot_executor
        self.cache = cache_service
    
    async def get_test_statistics(self) -> dict:
        """Получение статистики с кэшированием"""
        cache_key = "test_statistics"
        
        # Попытка получить из кэша
        stats = await self.cache.get(cache_key)
        if stats:
            return stats
        
        # Вычисление статистики
        stats = await self.test_repository.get_statistics()
        
        # Сохранение в кэш на 15 минут
        await self.cache.set(cache_key, stats, timedelta(minutes=15))
        
        return stats
```

### Асинхронная обработка

```python
# core/task_queue.py
import asyncio
from typing import Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    priority: int = 0

class TaskQueue:
    def __init__(self, max_workers: int = 5):
        self.queue = asyncio.PriorityQueue()
        self.workers = []
        self.max_workers = max_workers
        self.running = False
    
    async def start(self):
        """Запуск обработчиков задач"""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Остановка обработчиков"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def add_task(self, task: Task):
        """Добавление задачи в очередь"""
        await self.queue.put((task.priority, task))
    
    async def _worker(self, name: str):
        """Обработчик задач"""
        while self.running:
            try:
                priority, task = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=1.0
                )
                
                # Выполнение задачи
                await task.func(*task.args, **task.kwargs)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {name} error: {e}")

# Использование
task_queue = TaskQueue(max_workers=3)

async def send_notification(execution_id: str, status: str):
    """Отправка уведомления"""
    # Логика отправки уведомления
    pass

# Добавление задачи в очередь
await task_queue.add_task(Task(
    id="notification-1",
    func=send_notification,
    args=("exec-123", "completed"),
    kwargs={},
    created_at=datetime.utcnow(),
    priority=1
))
```

---

**Версия документа**: 1.0  
**Дата обновления**: 2024-01-01  
**Применимо к версии системы**: 1.0.0+