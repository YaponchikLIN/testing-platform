from fastapi import HTTPException, Query
import httpx
from pydantic import BaseModel
import logging
import asyncio
import json
from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime


class Settings(BaseModel):
    BASE_1C_URL: str = "http://1c-server.rtk-t.ru/unf/"
    API_ENDPOINT: str = (
        "hs/api/"  # Это значение может потребоваться уточнить, если эндпоинт для getSNandMAC другой
    )
    TIMEOUT: int = 300000
    AUTH: tuple = (
        "Администратор",
        "",
    )  # Basic Auth как в 1С: HTTPCоединение("localhost", 80, "Администратор", "")


settings = Settings()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_1c_exceptions(operation: str = "запросе к 1С"):
    """Декоратор для универсальной обработки исключений 1С"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Ошибка API 1C при {operation}: {e.response.status_code} {e.response.text}"
                )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Ошибка API 1C: {e.response.status_code} - {e.response.text}",
                )
            except httpx.RequestError as e:
                logger.error(f"Ошибка соединения при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Сервис недоступен: не удалось подключиться к 1С ({e.__class__.__name__})",
                )
            except ValueError as e:
                logger.error(f"Ошибка формата ответа при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=502, detail="Неверный формат ответа от 1С"
                )
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Внутренняя ошибка сервера при {operation}: {e.__class__.__name__}",
                )

        return wrapper

    return decorator


async def make_1c_request(
    endpoint: str, params: Any = None, method: str = "GET"
) -> Dict[str, Any]:
    """Универсальная функция для запросов к 1С"""
    url = f"{settings.BASE_1C_URL}{settings.API_ENDPOINT}{endpoint}"

    async with httpx.AsyncClient(
        auth=settings.AUTH, timeout=settings.TIMEOUT
    ) as client:
        logger.info(f"Запрос {method} на {url} с параметрами")
        logger.info(
            f"Аутентификация: {settings.AUTH[0]} / {'пустой пароль' if settings.AUTH[1] == '' else 'с паролем'}"
        )

        if method.upper() in ["POST", "PATCH", "PUT"]:
            # Явная сериализация данных в JSON для корректной передачи в 1С
            serialized_params = json.dumps(params, ensure_ascii=False)
            logger.info(f"Размер данных: {len(serialized_params)} символов")

            # Отправляем сериализованную строку как content с правильным Content-Type
            response = await client.request(
                method,
                url,
                content=serialized_params,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
        else:
            logger.info(f"Отправляем query параметры: {params}")
            response = await client.request(method, url, params=params)

        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"Заголовки ответа: {dict(response.headers)}")
        response.raise_for_status()

        try:
            response_data = response.json()
            logger.info(
                f"Получен JSON ответ: {len(response_data) if isinstance(response_data, list) else 'данные получены'}"
            )
            # Возвращаем исходную структуру от 1С без дополнительной обертки
            return response_data
        except ValueError:
            response_text = response.text
            logger.info(f"Получен текстовый ответ: {response_text}")
            return {"status": "success", "data": response_text}


@handle_1c_exceptions("получении данных заказа")
async def fetch_1c_data(order_id: int):
    """
    Получение данных из 1С по ID заказа

    Args:
        order_id: ID заказа в 1С

    Returns:
        dict: Данные заказа из 1С
    """
    result = await make_1c_request(f"getOrderData/{order_id}")
    return result["data"]


@handle_1c_exceptions("получении SN и MAC")
async def get_sn_and_mac_from_1c(order_uid):
    """Получение SN и MAC из 1С"""
    return await make_1c_request("SNandMAC", {"order_uid": order_uid})


@handle_1c_exceptions("обновление статуса")
async def patch_one_device_1c(deviceArray):
    """Обновление статуса устройства"""
    logger.info(f"Тип deviceArray: {type(deviceArray)}")
    logger.info(
        f"Длина deviceArray: {len(deviceArray) if hasattr(deviceArray, '__len__') else 'не определена'}"
    )

    if len(deviceArray) == 0:
        logger.warning("deviceArray пустой")

    return await make_1c_request(
        "oneDevice",
        deviceArray,
        method="PATCH",
    )


@handle_1c_exceptions("получении заказов")
async def get_orders(date_from: Optional[str] = None, date_to: Optional[str] = None):
    """
    Получение заказов из 1С

    Args:
        date_from: Дата начала периода (может быть URL-encoded)
        date_to: Дата окончания периода (может быть URL-encoded)

    Returns:
        dict: Ответ от 1С с заказами
    """
    import urllib.parse

    # Декодируем URL-параметры на случай, если они закодированы
    decoded_date_from = urllib.parse.unquote(date_from) if date_from else None
    decoded_date_to = urllib.parse.unquote(date_to) if date_to else None

    logger.info(f"Исходные параметры: date_from={date_from}, date_to={date_to}")
    logger.info(
        f"Декодированные параметры: date_from={decoded_date_from}, date_to={decoded_date_to}"
    )

    api_format_date_from = None
    api_format_date_to = None

    if decoded_date_from:
        try:
            # Парсим дату в формате "Sun Jan 01 2023 00:00:00 GMT+0300 (Москва, стандартное время)"
            date_part = decoded_date_from.split("GMT")[0].strip()
            date_obj = datetime.strptime(date_part, "%a %b %d %Y %H:%M:%S")
            api_format_date_from = date_obj.strftime("%Y-%m-%d")
            logger.info(f"Преобразованная date_from: {api_format_date_from}")
        except Exception as e:
            logger.error(f"Ошибка парсинга date_from '{decoded_date_from}': {e}")
            raise HTTPException(
                status_code=400, detail=f"Неверный формат date_from: {e}"
            )

    if decoded_date_to:
        try:
            # Парсим дату в формате "Wed Dec 03 2025 00:00:00 GMT+0300 (Москва, стандартное время)"
            date_part = decoded_date_to.split("GMT")[0].strip()
            date_obj = datetime.strptime(date_part, "%a %b %d %Y %H:%M:%S")
            api_format_date_to = date_obj.strftime("%Y-%m-%d")
            logger.info(f"Преобразованная date_to: {api_format_date_to}")
        except Exception as e:
            logger.error(f"Ошибка парсинга date_to '{decoded_date_to}': {e}")
            raise HTTPException(status_code=400, detail=f"Неверный формат date_to: {e}")

    params = {
        k: v
        for k, v in {
            "date_from": api_format_date_from,
            "date_to": api_format_date_to,
        }.items()
        if v
    }
    logger.info(f"Параметры для запроса к 1С: {params}")

    return await make_1c_request("orders", params)


# Тестовая функция для проверки работы
async def main_test():
    """Тестирование функций запросов к 1С"""

    # Example of date string parsing
    date_string = "Sat Jun 28 2023 00:00:00 GMT+0300 (Москва, стандартное время)"
    date_obj = datetime.strptime(
        date_string.split("GMT")[0].strip(), "%a %b %d %Y %H:%M:%S"
    )
    api_format_date_from = date_obj.strftime("%Y-%m-%d")

    date_string = "Sat Jun 28 2025 00:00:00 GMT+0300 (Москва, стандартное время)"
    date_obj = datetime.strptime(
        date_string.split("GMT")[0].strip(), "%a %b %d %Y %H:%M:%S"
    )
    api_format_date_to = date_obj.strftime("%Y-%m-%d")

    tests = [
        ("Тест get_sn_and_mac_from_1c", get_sn_and_mac_from_1c()),
        # ("Тест get_orders без параметров", get_orders()),
        # ("Тест get_orders с датами", get_orders(api_format_date_from, api_format_date_to)),
        # ("Тест fetch_1c_data", fetch_1c_data(12345))
    ]

    for test_name, test_coro in tests:
        try:
            logger.info(f"\n=== {test_name} ===")
            result = await test_coro
            logger.info(f"Результат: {result}")
        except HTTPException as e:
            logger.error(f"HTTP ошибка в {test_name}: {e.status_code} - {e.detail}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в {test_name}: {e}")


if __name__ == "__main__":

    asyncio.run(main_test())
