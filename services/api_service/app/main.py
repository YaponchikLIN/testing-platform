from fastapi import FastAPI, Depends, HTTPException
import asyncio
import logging
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
from db import db_tests
from db.postgres_db import db
from domain.models.test_models import *
from api.routes.post import router as post_router
from api.routes.get import router as get_router
from api.routes.firmware import router as firmware_router
from api.routes.patch import router as patch_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Инициализация подключения к PostgreSQL при запуске"""
    try:
        await db.connect()
        print("PostgreSQL подключение установлено")
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        print("Приложение будет работать без сохранения в PostgreSQL")


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие подключения к PostgreSQL при остановке"""
    await db.disconnect()
    print("PostgreSQL подключение закрыто")


# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api_service.websocket.endpoint import router as websocket_router

app.include_router(websocket_router)
app.include_router(post_router)
app.include_router(get_router)
app.include_router(firmware_router)
app.include_router(patch_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
