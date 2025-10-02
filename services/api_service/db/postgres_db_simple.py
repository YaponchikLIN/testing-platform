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

class SimplePostgreSQLDatabase:
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
            raise
    
    async def disconnect(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с PostgreSQL закрыто")
    
    async def save_test_result(self, passed: bool, details: Dict[str, Any]) -> str:
        """Сохранение результата теста в упрощенную таблицу"""
        async with self.pool.acquire() as conn:
            result_id = await conn.fetchval(
                """
                INSERT INTO test_results (passed, details)
                VALUES ($1, $2)
                RETURNING id
                """,
                passed, json.dumps(details)
            )
            logger.info(f"Сохранен результат теста с ID: {result_id}, passed: {passed}")
            return str(result_id)
    
    async def get_test_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение результатов тестов"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, passed, details, created_at, updated_at
                FROM test_results
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )
            
            results = []
            for row in rows:
                result = {
                    'id': str(row['id']),
                    'passed': row['passed'],
                    'details': json.loads(row['details']) if isinstance(row['details'], str) else row['details'],
                    'created_at': row['created_at'].isoformat(),
                    'updated_at': row['updated_at'].isoformat()
                }
                results.append(result)
            
            logger.info(f"Получено {len(results)} результатов тестов")
            return results
    
    async def get_test_result_by_id(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Получение результата теста по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, passed, details, created_at, updated_at
                FROM test_results
                WHERE id = $1
                """,
                result_id
            )
            
            if row:
                result = {
                    'id': str(row['id']),
                    'passed': row['passed'],
                    'details': json.loads(row['details']) if isinstance(row['details'], str) else row['details'],
                    'created_at': row['created_at'].isoformat(),
                    'updated_at': row['updated_at'].isoformat()
                }
                logger.info(f"Найден результат теста с ID: {result_id}")
                return result
            else:
                logger.warning(f"Результат теста с ID {result_id} не найден")
                return None
    
    async def update_test_result(self, result_id: str, passed: bool = None, details: Dict[str, Any] = None) -> bool:
        """Обновление результата теста"""
        set_parts = []
        values = []
        param_count = 1
        
        if passed is not None:
            set_parts.append(f"passed = ${param_count}")
            values.append(passed)
            param_count += 1
        
        if details is not None:
            set_parts.append(f"details = ${param_count}")
            values.append(json.dumps(details))
            param_count += 1
        
        if not set_parts:
            logger.warning(f"Нет параметров для обновления результата теста {result_id}")
            return False
        
        # Добавляем updated_at
        set_parts.append(f"updated_at = ${param_count}")
        values.append(datetime.now(dt.timezone.utc))
        values.append(result_id)  # для WHERE условия
        
        query = f"""
            UPDATE test_results 
            SET {', '.join(set_parts)}
            WHERE id = ${param_count + 1}
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *values)
            
            if result == 'UPDATE 1':
                logger.info(f"Успешно обновлен результат теста {result_id}")
                return True
            else:
                logger.warning(f"Не удалось обновить результат теста {result_id}. Результат: {result}")
                return False
    
    async def delete_test_result(self, result_id: str) -> bool:
        """Удаление результата теста"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM test_results WHERE id = $1",
                result_id
            )
            
            if result == 'DELETE 1':
                logger.info(f"Успешно удален результат теста {result_id}")
                return True
            else:
                logger.warning(f"Не удалось удалить результат теста {result_id}. Результат: {result}")
                return False

# Создаем экземпляр базы данных
db = SimplePostgreSQLDatabase()