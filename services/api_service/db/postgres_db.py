import asyncpg
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import datetime as dt
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv("DATABASE_HOST", "localhost"),
                port=int(os.getenv("DATABASE_PORT", "5432")),
                database=os.getenv("DATABASE_NAME", "testing_platform"),
                user=os.getenv("DATABASE_USER", "test_user"),
                password=os.getenv("DATABASE_PASSWORD", "test_password"),
                min_size=1,
                max_size=10
            )
            logger.info("Успешное подключение к PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            self.pool = None  # Явно устанавливаем None при ошибке
    
    async def disconnect(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с PostgreSQL закрыто")
    
    async def create_test_execution(self, test_id: str, status: str = 'idle') -> str:
        """Создание новой записи выполнения теста"""
        async with self.pool.acquire() as conn:
            execution_id = await conn.fetchval(
                """
                INSERT INTO test_executions (test_id, status, time_start)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                test_id, status, datetime.now() if status != 'idle' else None
            )
            logger.info(f"Создано выполнение теста {test_id} с ID: {execution_id}")
            return str(execution_id)
    
    async def update_test_execution(self, execution_id: str, **kwargs):
        """Обновление записи выполнения теста"""
        
        print(f"[DEBUG] Обновление выполнения теста {execution_id} с параметрами: {kwargs}")
        logger.info(f"Обновление выполнения теста {execution_id} с параметрами: {kwargs}")
        
        # Формируем SET часть запроса
        set_parts = []
        values = []
        param_count = 1
        
        for key, value in kwargs.items():
            if key in ['status', 'time_start', 'time_end', 'execution_time', 
                      'progress', 'result_passed', 'result_details', 'result_data']:
                set_parts.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not set_parts:
            logger.warning(f"Нет параметров для обновления выполнения теста {execution_id}")
            return
        
        # Добавляем updated_at
        set_parts.append(f"updated_at = ${param_count}")
        values.append(datetime.now(dt.timezone.utc))
        values.append(execution_id)  # для WHERE условия
        
        query = f"""
            UPDATE test_executions 
            SET {', '.join(set_parts)}
            WHERE id = ${param_count + 1}
        """
        
        logger.info(f"Выполняется SQL запрос: {query}")
        logger.info(f"Значения параметров: {values}")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *values)
            logger.info(f"Результат обновления: {result}")
            
            # Проверяем, была ли обновлена строка
            if result == 'UPDATE 1':
                logger.info(f"Успешно обновлено выполнение теста {execution_id}")
            else:
                logger.warning(f"Не удалось обновить выполнение теста {execution_id}. Результат: {result}")
                
            # Проверим, что запись действительно обновилась
            check_row = await conn.fetchrow(
                "SELECT result_passed, result_details FROM test_executions WHERE id = $1",
                execution_id
            )
            if check_row:
                logger.info(f"Проверка после обновления: result_passed={check_row['result_passed']}, result_details={check_row['result_details']}")
            else:
                logger.error(f"Запись с id {execution_id} не найдена после обновления")
    
    async def save_sim_test_results(self, execution_id: str, sim_data: Dict[str, Any]):
        """Сохранение результатов SIM теста"""
        async with self.pool.acquire() as conn:
            for slot_key, slot_data in sim_data.items():
                if slot_key.startswith('slot_') and isinstance(slot_data, dict):
                    slot_number = int(slot_key.split('_')[1])
                    
                    # Обработка packet_loss - убираем символ % если есть
                    packet_loss_str = slot_data.get('packet_loss', '0')
                    packet_loss_value = None
                    if packet_loss_str and packet_loss_str not in ['N/A', '', 'None', None]:
                        try:
                            # Убираем символ % если есть
                            packet_loss_clean = str(packet_loss_str).replace('%', '')
                            packet_loss_value = float(packet_loss_clean)
                        except (ValueError, TypeError):
                            packet_loss_value = None
                    
                    # Обработка response_time - убираем 'ms' если есть
                    response_time_str = slot_data.get('response_time', '0')
                    response_time_value = None
                    if response_time_str and response_time_str not in ['N/A', '', 'None', None]:
                        try:
                            # Убираем 'ms' если есть
                            response_time_clean = str(response_time_str).replace('ms', '')
                            response_time_value = float(response_time_clean)
                        except (ValueError, TypeError):
                            response_time_value = None
                    
                    await conn.execute(
                        """
                        INSERT INTO sim_test_results 
                        (execution_id, slot_number, state_failed_reason, active, 
                         connected, ping_result, packet_loss, response_time)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        execution_id, slot_number,
                        slot_data.get('state-failed-reason'),
                        slot_data.get('active'),
                        slot_data.get('connected'),
                        slot_data.get('ping_result'),
                        packet_loss_value,
                        response_time_value
                    )
            logger.info(f"Сохранены результаты SIM теста для выполнения {execution_id}")
    
    async def save_ethernet_test_results(self, execution_id: str, ethernet_data: Dict[str, Any]):
        """Сохранение результатов Ethernet теста"""
        async with self.pool.acquire() as conn:
            interfaces = ethernet_data.get('interfaces', [])
            
            # Если массив интерфейсов пустой, просто логируем и выходим
            if not interfaces:
                logger.info(f"Нет интерфейсов для сохранения в Ethernet тесте (execution_id: {execution_id})")
                return
            
            for interface in interfaces:
                if isinstance(interface, dict):
                    # Обработка packet_loss - убираем символ % если есть
                    packet_loss_str = interface.get('packet_loss', '0')
                    packet_loss_value = None
                    if packet_loss_str and packet_loss_str not in ['N/A', '', 'None']:
                        try:
                            # Убираем символ % если есть
                            packet_loss_clean = str(packet_loss_str).replace('%', '')
                            packet_loss_value = float(packet_loss_clean)
                        except (ValueError, TypeError):
                            packet_loss_value = None
                    
                    # Обработка response_time - убираем 'ms' если есть
                    response_time_str = interface.get('response_time', '0')
                    response_time_value = None
                    if response_time_str and response_time_str not in ['N/A', '', 'None']:
                        try:
                            # Убираем 'ms' если есть
                            response_time_clean = str(response_time_str).replace('ms', '')
                            response_time_value = float(response_time_clean)
                        except (ValueError, TypeError):
                            response_time_value = None
                    
                    # Убеждаемся, что status - это строка
                    status_value = interface.get('status')
                    if isinstance(status_value, dict):
                        status_value = str(status_value)  # Преобразуем словарь в строку
                    elif status_value is None:
                        status_value = 'unknown'
                    else:
                        status_value = str(status_value)
                    
                    await conn.execute(
                        """
                        INSERT INTO ethernet_test_results 
                        (execution_id, interface_name, ip_address, ping_result, 
                         packet_loss, response_time, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        execution_id,
                        interface.get('name'),  # Используем 'name' вместо 'interface'
                        interface.get('ip_address'),  # Используем 'ip_address'
                        interface.get('ping_result'),
                        packet_loss_value,
                        response_time_value,
                        status_value
                    )
            logger.info(f"Сохранены результаты Ethernet теста для выполнения {execution_id}")
    
    async def get_test_executions(self, test_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Получение списка выполнений тестов"""
        async with self.pool.acquire() as conn:
            if test_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM test_executions 
                    WHERE test_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                    """,
                    test_id, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM test_executions 
                    ORDER BY created_at DESC 
                    LIMIT $1
                    """,
                    limit
                )
            
            return [dict(row) for row in rows]
    
    async def get_test_execution_details(self, execution_id: str) -> Optional[Dict]:
        """Получение детальной информации о выполнении теста"""
        async with self.pool.acquire() as conn:
            # Основная информация о выполнении
            execution = await conn.fetchrow(
                "SELECT * FROM test_executions WHERE id = $1",
                execution_id
            )
            
            if not execution:
                return None
            
            result = dict(execution)
            
            # Получаем детальные результаты в зависимости от типа теста
            if execution['test_id'] == 'sim':
                sim_results = await conn.fetch(
                    "SELECT * FROM sim_test_results WHERE execution_id = $1",
                    execution_id
                )
                result['detailed_results'] = [dict(row) for row in sim_results]
            
            elif execution['test_id'] == 'ethernets':
                ethernet_results = await conn.fetch(
                    "SELECT * FROM ethernet_test_results WHERE execution_id = $1",
                    execution_id
                )
                result['detailed_results'] = [dict(row) for row in ethernet_results]
            
            return result
    
    async def get_test_statistics(self) -> Dict[str, Any]:
        """Получение статистики по тестам"""
        async with self.pool.acquire() as conn:
            # Общая статистика
            total_executions = await conn.fetchval(
                "SELECT COUNT(*) FROM test_executions"
            )
            
            # Статистика по статусам
            status_stats = await conn.fetch(
                """
                SELECT status, COUNT(*) as count 
                FROM test_executions 
                GROUP BY status
                """
            )
            
            # Статистика по типам тестов
            test_type_stats = await conn.fetch(
                """
                SELECT test_id, COUNT(*) as count,
                       AVG(execution_time) as avg_execution_time
                FROM test_executions 
                WHERE execution_time IS NOT NULL
                GROUP BY test_id
                """
            )
            
            # Статистика успешности
            success_stats = await conn.fetch(
                """
                SELECT test_id, 
                       COUNT(*) as total,
                       SUM(CASE WHEN result_passed = true THEN 1 ELSE 0 END) as passed,
                       SUM(CASE WHEN result_passed = false THEN 1 ELSE 0 END) as failed
                FROM test_executions 
                WHERE result_passed IS NOT NULL
                GROUP BY test_id
                """
            )
            
            return {
                'total_executions': total_executions,
                'status_distribution': {row['status']: row['count'] for row in status_stats},
                'test_type_stats': [dict(row) for row in test_type_stats],
                'success_stats': [dict(row) for row in success_stats]
            }

# Глобальный экземпляр базы данных
db = PostgreSQLDatabase()