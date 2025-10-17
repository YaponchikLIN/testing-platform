from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
import jwt
from pydantic import BaseModel
from api_service.app.config import oauth2_scheme, SECRET_KEY
from domain.models.test_models import TestRequest
from db.db_tests import tests_db
from domain.services.test_service import (
    broadcast_status,
    run_test_simulation,
    run_tests_sequentially,
)
import asyncio
import datetime

router = APIRouter()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


# Имитация логина
@router.post("/token")
async def login():
    token = jwt.encode({"user_id": "1", "role": "admin"}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/tests/run")
async def run_test(test_request_payload: TestRequest):
    requested_test_id = test_request_payload.test_id

    print(f"Запрос на запуск теста с ID: {requested_test_id}")

    # Сбрасываем данные всех тестов перед новым запуском
    for test_key in tests_db.keys():
        if test_key != "all":  # Не сбрасываем запись "all"
            tests_db[test_key]["status"] = "idle"
            tests_db[test_key]["time_start"] = ""
            tests_db[test_key]["time_end"] = ""
            tests_db[test_key]["updated_at"] = ""
            tests_db[test_key]["result"] = None

    if requested_test_id == "all":
        if not tests_db:
            print("База данных тестов пуста. Нет тестов для запуска.")
            return []

        # Запускаем последовательное выполнение в фоне
        if test_request_payload.status == "Testing":
            return {"status": "success", "message": "Тесты уже запущены"}
        elif test_request_payload.status == "success":
            return {"status": "success", "message": "Тесты уже пройдены"}
        else:
            asyncio.create_task(run_tests_sequentially(test_request_payload))

        # Сразу возвращаем текущее состояние (которое idle)
        tests_to_return = []
        for test_key, test_value in tests_db.items():
            if test_key != "all":
                item = test_value.copy()
                item["test_id"] = test_key
                tests_to_return.append(item)
        return tests_to_return

    else:  # Запуск конкретного теста
        if requested_test_id not in tests_db:
            raise HTTPException(
                status_code=404, detail=f"Тест с ID '{requested_test_id}' не найден"
            )

        print(f"Запуск конкретного теста: {requested_test_id}")
        test_item_in_db = tests_db[requested_test_id]
        test_item_in_db["test_id"] = requested_test_id

        current_time_utc_iso = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        test_item_in_db["status"] = "running"
        test_item_in_db["time_start"] = current_time_utc_iso
        test_item_in_db["updated_at"] = current_time_utc_iso
        test_item_in_db["time_end"] = ""
        test_item_in_db["result"] = None

        if test_item_in_db["status"] == "testing":
            return {"status": "success", "message": "Тесты уже запущены"}
        elif test_item_in_db["status"] == "success":
            return {"status": "success", "message": "Тесты уже пройдены"}
        else:
            asyncio.create_task(
                run_test_simulation(test_item_in_db, test_request_payload)
            )

        # Сразу возвращаем обновленное состояние
        item_to_return = test_item_in_db.copy()
        return [item_to_return]

    # print(f"Запущено тестов: {len(tests_to_return)}. Ответ: {tests_to_return}")
    # return tests_to_return

    #     print(f"Exception в update_device_status_endpoint: {e}")
    #     raise HTTPException(status_code=500, detail=str(e))
