#!/usr/bin/env python3
"""
Запуск FastAPI сервера напрямую через Python
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "api_service"))

import asyncio
from fastapi import FastAPI
from app.main import app

if __name__ == "__main__":

    print("🚀 Запуск FastAPI сервера...")
    print("📍 Сервер будет доступен по адресу: http://localhost:8001")
    print("📖 Документация API: http://localhost:8001/docs")
    print("🔄 Интерактивная документация: http://localhost:8001/redoc")
    print("⏹️  Для остановки нажмите Ctrl+C")

    # Запуск сервера
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,  # Автоперезагрузка при изменении файлов
        log_level="info",
        access_log=True,
    )
