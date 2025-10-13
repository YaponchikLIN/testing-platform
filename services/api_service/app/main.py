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
from api_service.websocket.endpoint import parse_and_broadcast_gpio_event
import subprocess
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

gpio_process = None


@app.on_event("startup")
async def startup_event():
    """Инициализация подключения к PostgreSQL при запуске"""
    try:
        await db.connect()
        print("PostgreSQL подключение установлено")

        global gpio_process
        gpio_process = await asyncio.create_subprocess_exec(
            "node",
            "gpio_manager.js",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        print("✅ GPIO монитор запущен как демон")

        # Чтение вывода в отдельном потоке
        def read_output():
            while True:
                output = gpio_process.stdout.readline()
                if output:
                    print(f"[GPIO] {output.strip()}")
                if gpio_process.poll() is not None:
                    break

        threading.Thread(target=read_output, daemon=True).start()

    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")


async def read_gpio_output():
    """Чтение вывода GPIO процесса"""
    while True:
        line = await gpio_process.stdout.readline()
        if line:
            line = line.decode().strip()
            print(f"[GPIO] {line}")
            await parse_and_broadcast_gpio_event(line)
        else:
            break


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие подключения к PostgreSQL при остановке"""
    await db.disconnect()
    print("PostgreSQL подключение закрыто")

    global gpio_process
    if gpio_process:
        gpio_process.terminate()
        gpio_process.wait()
        print("✅ GPIO монитор остановлен")


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
