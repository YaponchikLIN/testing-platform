from api.routes.requests_1c import patch_one_device_1c
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.patch("/1C/oneDevice")
async def patch_one_device(deviceArray: List[dict]):
    try:
        logger.info(f"Тип deviceArray: {type(deviceArray)}")
        logger.info(f"Длина deviceArray: {len(deviceArray)}")

        return await patch_one_device_1c(deviceArray)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
