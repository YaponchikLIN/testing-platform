import logging

print("--- LOADING GET.PY ROUTER ---")
from fastapi import APIRouter, Depends, HTTPException
from api.routes.requests_1c import get_orders, get_sn_and_mac_from_1c
from db.db_tests import tests_db
from db.postgres_db import db
from typing import Dict, List, Optional

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Получение статуса всех тестов
@router.get("/tests")
async def get_all_tests_status():
    """Получить статус всех тестов"""
    result = []
    for test_id, test_data in tests_db.items():
        test_info = test_data.copy()
        test_info["test_id"] = test_id
        result.append(test_info)
    return result


# Получение результатов
# @router.get("/tests/result/{test_id}")
# async def get_result(test_id: str, user: Dict = Depends(get_current_user)):
#     if test_id not in tests_db:
#         raise HTTPException(status_code=404, detail="Тест не найден")
#     return tests_db[test_id]["result"] or {"message": "Результаты отсутствуют"}


@router.get("/1C/SNandMAC")
async def get_sn_and_mac(order_uid: str):

    try:
        return await get_sn_and_mac_from_1c(order_uid)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/tests/executions")
async def get_test_executions(test_id: Optional[str] = None, limit: int = 100):
    """Получить список выполнений тестов из PostgreSQL"""
    try:
        if db.pool is None:
            raise HTTPException(status_code=503, detail="База данных недоступна")
        executions = await db.get_test_executions(test_id, limit)
        return {"executions": executions, "total": len(executions)}
    except Exception as e:
        logger.error(f"Ошибка получения выполнений тестов: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения данных: {str(e)}"
        )


@router.get("/tests/executions/{execution_id}")
async def get_test_execution_details(execution_id: str):
    """Получить детальную информацию о выполнении теста"""
    try:
        if db.pool is None:
            raise HTTPException(status_code=503, detail="База данных недоступна")
        execution = await db.get_test_execution_details(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Выполнение теста не найдено")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения деталей выполнения теста: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения данных: {str(e)}"
        )


@router.get("/tests/statistics")
async def get_test_statistics():
    """Получить статистику по тестам"""
    try:
        if db.pool is None:
            raise HTTPException(status_code=503, detail="База данных недоступна")
        stats = await db.get_test_statistics()
        return stats
    except Exception as e:
        logger.error(f"Ошибка получения статистики тестов: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения статистики: {str(e)}"
        )


@router.get("/tests/results/{test_id}/latest")
async def get_latest_test_result(test_id: str):
    """Получить последний результат теста"""
    try:
        if db.pool is None:
            raise HTTPException(status_code=503, detail="База данных недоступна")
        executions = await db.get_test_executions(test_id, 1)
        if not executions:
            raise HTTPException(status_code=404, detail="Результаты теста не найдены")

        latest_execution = executions[0]
        details = await db.get_test_execution_details(str(latest_execution["id"]))
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения последнего результата теста: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения данных: {str(e)}"
        )


@router.get("/1C/orders")
async def get_orders_endpoint(date_from: str, date_to: str):
    try:
        return await get_orders(date_from, date_to)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
