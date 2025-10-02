import logging
from fastapi import APIRouter, HTTPException
from domain.services.firmware_service import (
    FirmwareService,
    FirmwareInstallRequest,
    FirmwareTestRequest
)

router = APIRouter()
firmware_service = FirmwareService()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/firmware/install")
async def install_firmware(request: FirmwareInstallRequest):
    """
    Установка прошивки на устройство
    """
    try:
        result = await firmware_service.install_firmware(request)
        return result
    except Exception as e:
        logger.error(f"Ошибка при установке прошивки: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/firmware/test-cycle")
async def firmware_test_cycle(request: FirmwareTestRequest):
    """
    Полный цикл тестирования с прошивкой
    """
    try:
        result = await firmware_service.firmware_test_cycle(request)
        return result
    except Exception as e:
        logger.error(f"Ошибка при выполнении цикла тестирования: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
