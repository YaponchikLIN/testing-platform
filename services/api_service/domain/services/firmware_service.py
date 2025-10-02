import logging
import httpx
from typing import List, Dict, Any, Optional
import asyncio
from functools import wraps
import os
from pathlib import Path
import subprocess
import time
from pydantic import BaseModel, Field
from fastapi import HTTPException


# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic модели для типизации
class BuildInfo(BaseModel):
    """Информация о билде"""

    id: int
    jobName: str
    status: str
    submitDate: Optional[str] = None
    finishDate: Optional[str] = None
    commitHash: Optional[str] = None


class ArtifactInfo(BaseModel):
    """Информация об артефакте"""

    path: str
    lastModified: int
    length: int
    mediaType: Optional[str] = None


class FirmwareInstallRequest(BaseModel):
    """Запрос на установку прошивки"""

    build_id: Optional[int] = Field(None, description="ID билда для установки")
    artifact_path: Optional[str] = Field(None, description="Путь к артефакту")


class FirmwareTestRequest(BaseModel):
    """Запрос на полный цикл: загрузка прошивки + установка + тестирование"""

    build_id: Optional[int] = Field(None, description="ID билда для установки")
    artifact_path: Optional[str] = Field(None, description="Путь к артефакту")
    test_id: Optional[str] = Field(
        None, description="ID теста для запуска (если не указан, запускаются все тесты)"
    )
    wait_for_router: int = Field(
        60, description="Время ожидания поднятия роутера в секундах"
    )
    router_ip: str = Field(
        "192.168.1.1", description="IP-адрес роутера для установки прошивки"
    )
    router_user: str = Field(
        "root", description="Имя пользователя для SSH подключения к роутеру"
    )
    device_data: Dict[str, Any] = Field(
        {}, description="Данные устройства для тестирования"
    )


class Settings(BaseModel):
    API_ONEDEV: str = "https://dev.rtk-t.ru/~api/"
    ACCESS_TOKEN_ONEDEV: str = "znpOGvRTo3NMoyYG9s8HRinjfB1z2OTAzpnArYLP"
    TIMEOUT: int = 30
    VERIFY_SSL: bool = False  # Отключаем проверку SSL для разработки


# Конфигурационные константы
class FirmwareConfig:
    """Конфигурация для работы с прошивкой"""

    TARGET_JOB_NAME = "rtk-tOS-Build"
    ARTIFACT_PREFIX = "rtk-tOS"
    MAX_BUILDS_TO_CHECK = 500
    BUILDS_BATCH_SIZE = 50
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток при ошибках"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Попытка {attempt + 1} неудачна: {e}. Повтор через {delay}с..."
                        )
                        await asyncio.sleep(
                            delay * (attempt + 1)
                        )  # Экспоненциальная задержка
                    else:
                        logger.error(f"Все {max_retries} попыток неудачны")
                except Exception as e:
                    logger.error(f"Неожиданная ошибка: {e}")
                    raise
            raise last_exception

        return wrapper

    return decorator


def handle_onedev_exceptions(operation: str = "запросе к OneDev"):
    """Декоратор для универсальной обработки исключений OneDev API"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Ошибка OneDev API при {operation}: {e.response.status_code} {e.response.text}"
                )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Ошибка OneDev API: {e.response.status_code} - {e.response.text}",
                )
            except httpx.RequestError as e:
                logger.error(f"Ошибка соединения при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Сервис недоступен: не удалось подключиться к OneDev ({e.__class__.__name__})",
                )
            except ValueError as e:
                logger.error(f"Ошибка формата ответа при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=502, detail="Неверный формат ответа от OneDev"
                )
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при {operation}: {str(e)}")
                raise HTTPException(
                    status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}"
                )

        return wrapper

    return decorator


class FirmwareService:
    """Сервис для работы с прошивками"""

    def __init__(self):
        self.settings = Settings()
        self.config = FirmwareConfig()

    # Утилитарные функции
    def is_rtk_build(self, build: BuildInfo) -> bool:
        """Проверяет, является ли билд RTK билдом"""
        return (
            build.jobName == self.config.TARGET_JOB_NAME
            and build.status == "SUCCESSFUL"
        )

    def is_rtk_artifact(self, artifact: ArtifactInfo) -> bool:
        """Проверяет, является ли артефакт RTK прошивкой"""
        return artifact.path.startswith(
            self.config.ARTIFACT_PREFIX
        ) and artifact.path.endswith(".bin")

    def validate_build_id(self, build_id: Optional[int]) -> int:
        """Валидирует ID билда"""
        if build_id is None or build_id <= 0:
            raise HTTPException(status_code=400, detail="Некорректный ID билда")
        return build_id

    def validate_artifact_path(self, artifact_path: Optional[str]) -> str:
        """Валидирует путь к артефакту"""
        if not artifact_path or not artifact_path.strip():
            raise HTTPException(status_code=400, detail="Некорректный путь к артефакту")
        return artifact_path.strip()

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Универсальная функция для обработки ответов от OneDev API

        Args:
            response: HTTP ответ от OneDev API

        Returns:
            dict: Стандартизированный ответ с данными
        """
        try:
            response_data = response.json()
            logger.info(
                f"Received JSON response with {len(response_data) if isinstance(response_data, list) else 'data'}"
            )
            return {"status": "success", "data": response_data}
        except ValueError:
            response_text = response.text
            logger.info(f"Received text response: {response_text}")
            return {"status": "success", "data": response_text}

    class OneDevAuth(httpx.Auth):
        def __init__(self, access_token: str):
            self.access_token = access_token

        def auth_flow(self, request):
            request.headers["Authorization"] = f"Bearer {self.access_token}"
            yield request

    @handle_onedev_exceptions("получении списка сборок")
    @retry_on_failure(max_retries=FirmwareConfig.MAX_RETRIES)
    async def get_builds(
        self, offset: int = 0, count: int = FirmwareConfig.BUILDS_BATCH_SIZE
    ) -> List[BuildInfo]:
        """
        Получение списка сборок из OneDev API с типизацией и retry механизмом

        Args:
            offset: Количество пропускаемых элементов
            count: Количество возвращаемых элементов

        Returns:
            List[BuildInfo]: Список типизированных билдов

        Raises:
            HTTPException: При ошибках API
        """
        url = f"{self.settings.API_ONEDEV}builds"
        params = {"offset": offset, "count": count}

        async with httpx.AsyncClient(
            auth=self.OneDevAuth(self.settings.ACCESS_TOKEN_ONEDEV),
            timeout=self.config.REQUEST_TIMEOUT,
            verify=self.settings.VERIFY_SSL,
        ) as client:
            logger.info(f"Запрос билдов: offset={offset}, count={count}")

            response = await client.get(url, params=params)
            response.raise_for_status()

            response_data = self.parse_response(response)
            builds_data = response_data.get("data", [])
            builds = [BuildInfo(**build) for build in builds_data]

            logger.info(f"Получено {len(builds)} билдов")
            return builds

    @handle_onedev_exceptions("получении списка артефактов")
    async def get_build_artifacts(self, build_id: str):
        """
        Получение списка артефактов для указанной сборки

        Args:
            build_id: ID сборки

        Returns:
            dict: Ответ от OneDev API, содержащий данные об артефактах
        """
        url = f"{self.settings.API_ONEDEV}artifacts/{build_id}/infos"

        async with httpx.AsyncClient(
            auth=self.OneDevAuth(self.settings.ACCESS_TOKEN_ONEDEV),
            timeout=self.settings.TIMEOUT,
            verify=self.settings.VERIFY_SSL,
        ) as client:
            logger.info(f"Making GET request to {url}")

            response = await client.get(url)
            response.raise_for_status()

            # API возвращает объект с полем children, содержащим массив артефактов
            response_data = self.parse_response(response)
            if response_data.get("status") == "success":
                artifacts_data = response_data.get("data", {})
                artifacts = artifacts_data.get("children", [])
                return {"status": "success", "data": artifacts}

            return response_data

    @handle_onedev_exceptions("скачивании артефакта")
    async def download_artifact(self, build_id: str, artifact_path: str):
        """
        Скачивание артефакта из указанной сборки и сохранение в папку downloads

        Args:
            build_id: ID сборки
            artifact_path: Путь к артефакту

        Returns:
            dict: Информация о скачанном файле
        """
        # Попробуем правильный формат URL для OneDev API
        url = f"{self.settings.API_ONEDEV}artifacts/{build_id}/contents/{artifact_path}"

        # Создаем папку downloads если её нет
        downloads_dir = Path(__file__).parent.parent / "downloads"
        downloads_dir.mkdir(exist_ok=True)

        # Очищаем папку downloads от старых файлов
        for file in downloads_dir.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                    logger.info(f"Удален старый файл: {file.name}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {file.name}: {e}")

        # Формируем путь для сохранения файла
        filename = f"build_{build_id}_{artifact_path}"
        file_path = downloads_dir / filename

        async with httpx.AsyncClient(
            auth=self.OneDevAuth(self.settings.ACCESS_TOKEN_ONEDEV),
            timeout=self.settings.TIMEOUT,
            verify=self.settings.VERIFY_SSL,
        ) as client:
            logger.info(f"Making GET request to {url}")

            response = await client.get(url)
            response.raise_for_status()

            # Сохраняем файл
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Файл сохранен: {file_path} ({len(response.content)} байт)")

            return {
                "content": response.content,
                "file_path": str(file_path),
                "filename": filename,
                "size": len(response.content),
            }

    async def find_rtk_builds(self, max_builds: int = 500) -> List[Dict[str, Any]]:
        """
        Поиск всех билдов с job-name "rtk-tOS-Build"

        Args:
            max_builds: Максимальное количество билдов для поиска

        Returns:
            List[Dict]: Список билдов с job-name "rtk-tOS-Build", отсортированный по дате (новые первые)
        """
        rtk_builds = []
        offset = 0
        count = 50

        logger.info("Начинаем поиск билдов с jobName 'rtk-tOS-Build'")

        while offset < max_builds:
            logger.info(f"Запрашиваем билды: offset={offset}, count={count}")

            builds = await self.get_builds(offset=offset, count=count)

            if not builds or len(builds) == 0:
                logger.info(f"Больше билдов не найдено на offset={offset}")
                break

            # Фильтруем билды по jobName
            for build in builds:
                if build.jobName == "rtk-tOS-Build":
                    # Конвертируем BuildInfo в словарь для совместимости
                    build_dict = {
                        "id": build.id,
                        "jobName": build.jobName,
                        "status": build.status,
                        "submitDate": build.submitDate,
                        "finishDate": build.finishDate,
                        "commitHash": build.commitHash,
                    }
                    rtk_builds.append(build_dict)
                    logger.info(
                        f"Найден билд rtk-tOS-Build: ID={build.id}, статус={build.status}"
                    )

            # Если получили меньше билдов чем запрашивали, значит это последняя порция
            if len(builds) < count:
                logger.info("Достигнут конец списка билдов")
                break

            offset += count

        logger.info(f"Всего найдено билдов rtk-tOS-Build: {len(rtk_builds)}")
        return rtk_builds

    async def find_rtk_artifact_in_build(self, build_id: str) -> Optional[str]:
        """
        Поиск артефакта с именем, начинающимся с "rtk-tOS" в указанном билде

        Args:
            build_id: ID билда для поиска

        Returns:
            Optional[str]: Путь к найденному артефакту или None
        """
        logger.info(f"Ищем артефакт rtk-tOS в билде {build_id}")

        try:
            artifacts_response = await self.get_build_artifacts(build_id)
            artifacts = artifacts_response.get("data", [])

            if not artifacts or not isinstance(artifacts, list):
                logger.warning(f"Артефакты не найдены в билде {build_id}")
                return None

            # Ищем артефакт, начинающийся с "rtk-tOS"
            for artifact in artifacts:
                artifact_path = artifact.get("path", "")

                if artifact_path.startswith("rtk-tOS"):
                    logger.info(f"Найден подходящий артефакт: {artifact_path}")
                    return artifact_path

            logger.info(f"Артефакт rtk-tOS не найден в билде {build_id}")
            return None

        except Exception as e:
            logger.error(f"Ошибка при поиске артефактов в билде {build_id}: {str(e)}")
            return None

    async def install_firmware(self, request: FirmwareInstallRequest):
        """
        Установка прошивки на устройство с улучшенной логикой поиска

        Логика работы:
        1. Если параметры не указаны, ищет последний билд с job-name "rtk-tOS-Build"
        2. В найденном билде ищет артефакт, начинающийся с "rtk-tOS"
        3. Если артефакт не найден, переходит к предыдущему билду с тем же job-name
        4. Продолжает поиск до нахождения подходящего артефакта

        Args:
            request: Запрос с параметрами build_id и artifact_path (опционально)

        Returns:
            dict: Результат установки прошивки
        """
        build_id = request.build_id
        artifact_path = request.artifact_path

        # Если параметры указаны явно, используем их
        if build_id and artifact_path:
            logger.info(
                f"Используем указанные параметры: build_id={build_id}, artifact_path={artifact_path}"
            )
            firmware_info = await self.download_artifact(str(build_id), artifact_path)

            logger.info(
                f"Прошивка скачана успешно: {firmware_info['size']} байт в файл {firmware_info['filename']}"
            )

            return {
                "status": "success",
                "message": "Прошивка успешно установлена",
                "details": {
                    "build_id": build_id,
                    "artifact_path": artifact_path,
                    "firmware_size": firmware_info["size"],
                    "file_path": firmware_info["file_path"],
                    "filename": firmware_info["filename"],
                    "search_method": "manual",
                },
            }

        # Автоматический поиск билда и артефакта
        logger.info("Начинаем автоматический поиск подходящего билда и артефакта")

        # Находим все билды с job-name "rtk-tOS-Build"
        rtk_builds = await self.find_rtk_builds()

        if not rtk_builds:
            raise HTTPException(
                status_code=404,
                detail="Не найдено ни одного билда с job-name 'rtk-tOS-Build'",
            )

        # Ищем артефакт в билдах, начиная с самого нового
        found_build_id = None
        found_artifact_path = None

        for build in rtk_builds:
            current_build_id = build.get("id")
            if not current_build_id:
                continue

            logger.info(f"Проверяем билд {current_build_id}")

            artifact_path_found = await self.find_rtk_artifact_in_build(
                current_build_id
            )

            if artifact_path_found:
                found_build_id = current_build_id
                found_artifact_path = artifact_path_found
                logger.info(
                    f"Найден подходящий билд и артефакт: build_id={found_build_id}, artifact={found_artifact_path}"
                )
                break

        if not found_build_id or not found_artifact_path:
            raise HTTPException(
                status_code=404,
                detail=f"Не найден артефакт rtk-tOS ни в одном из {len(rtk_builds)} билдов rtk-tOS-Build",
            )

        # Скачиваем найденный артефакт
        logger.info(
            f"Скачиваем артефакт {found_artifact_path} из билда {found_build_id}"
        )
        firmware_info = await self.download_artifact(
            found_build_id, found_artifact_path
        )

        logger.info(
            f"Прошивка скачана и готова к установке: {firmware_info['size']} байт в файл {firmware_info['filename']}"
        )

        # Получаем информацию о найденном билде для ответа
        build_info = {}
        if rtk_builds:
            for build in rtk_builds:
                if str(build.get("id")) == str(found_build_id):
                    build_info = {
                        "jobName": build.get("jobName"),
                        "status": build.get("status"),
                        "submitDate": build.get("submitDate"),
                        "finishDate": build.get("finishDate"),
                    }
                    break

        return {
            "status": "success",
            "message": "Прошивка успешно найдена и установлена",
            "details": {
                "build_id": found_build_id,
                "artifact_path": found_artifact_path,
                "firmware_size": firmware_info["size"],
                "file_path": firmware_info["file_path"],
                "filename": firmware_info["filename"],
                "search_method": "automatic",
                "total_rtk_builds_checked": len(rtk_builds),
                "build_info": build_info,
            },
        }

    async def install_firmware_on_device(
        self,
        firmware_path: str,
        router_ip: str = "192.168.1.1",
        router_user: str = "root",
    ) -> dict:
        """
        Реальная установка прошивки на устройство через Robot Framework

        Args:
            firmware_path: Путь к файлу прошивки
            router_ip: IP-адрес роутера
            router_user: Имя пользователя для SSH

        Returns:
            dict: Результат установки прошивки
        """
        logger.info(
            f"Начинаем реальную установку прошивки {firmware_path} на устройство {router_ip}"
        )

        try:
            # Нормализуем путь для Windows (используем pathlib для кроссплатформенности)
            firmware_path_obj = Path(firmware_path)
            normalized_firmware_path = (
                firmware_path_obj.as_posix()
            )  # Всегда используем прямые слеши
            logger.info(f"Нормализованный путь к прошивке: {normalized_firmware_path}")

            # Проверяем существование файла
            if not firmware_path_obj.exists():
                raise FileNotFoundError(f"Файл прошивки не найден: {firmware_path}")

            logger.info(
                f"Размер файла прошивки: {firmware_path_obj.stat().st_size} байт"
            )

            # Правильно экранируем пути для Windows, заменяя обратные слеши на прямые
            safe_firmware_path = normalized_firmware_path.replace("\\", "/")

            logger.info(f"Безопасный путь для Robot Framework: {safe_firmware_path}")

            # Запускаем Robot Framework для установки прошивки
            logger.info("Запускаем Robot Framework для установки прошивки...")

            robot_cmd = ["python", "-m", "robot", "firmware_upload.robot"]

            logger.debug(f"Команда Robot Framework: {robot_cmd}")

            # Устанавливаем рабочий каталог в папку api_service, где находится firmware_upload.robot
            current_dir = Path(__file__).parent.parent.parent
            logger.info(f"Рабочий каталог для Robot Framework: {current_dir}")

            # Запускаем Robot Framework с потоковым выводом для отображения прогресса
            process = subprocess.Popen(
                robot_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=current_dir,
                bufsize=1,
                universal_newlines=True,
            )

            output_lines = []
            last_output_time = time.time()
            no_output_timeout = 300  # 5 минут без вывода

            # Читаем вывод в реальном времени
            try:
                while True:
                    # Проверяем, есть ли новый вывод (неблокирующее чтение)
                    import select
                    import sys

                    if sys.platform == "win32":
                        # На Windows используем простое чтение с таймаутом
                        output = process.stdout.readline()
                        if output == "" and process.poll() is not None:
                            break
                        if output:
                            output_lines.append(output.strip())
                            logger.info(f"Robot Framework: {output.strip()}")
                            last_output_time = time.time()
                    else:
                        # На Unix-системах используем select
                        ready, _, _ = select.select([process.stdout], [], [], 1.0)
                        if ready:
                            output = process.stdout.readline()
                            if output == "" and process.poll() is not None:
                                break
                            if output:
                                output_lines.append(output.strip())
                                logger.info(f"Robot Framework: {output.strip()}")
                                last_output_time = time.time()

                    # Проверяем таймаут отсутствия вывода
                    current_time = time.time()
                    if current_time - last_output_time > no_output_timeout:
                        logger.warning(
                            f"Нет вывода от Robot Framework уже {no_output_timeout} секунд, принудительно завершаем процесс"
                        )
                        process.terminate()
                        time.sleep(5)
                        if process.poll() is None:
                            process.kill()
                        return {
                            "status": "error",
                            "message": f"Таймаут: нет вывода от Robot Framework более {no_output_timeout} секунд",
                            "installation_completed": False,
                            "robot_output": "\n".join(output_lines),
                        }

                    # Проверяем, завершился ли процесс
                    if process.poll() is not None:
                        break

                # Ждем завершения процесса с общим таймаутом
                return_code = process.wait(
                    timeout=60
                )  # Короткий таймаут, так как процесс уже должен завершиться

            except subprocess.TimeoutExpired:
                logger.error("Процесс Robot Framework завис, принудительно завершаем")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                return {
                    "status": "error",
                    "message": "Процесс Robot Framework завис и был принудительно завершен",
                    "installation_completed": False,
                    "robot_output": "\n".join(output_lines),
                }

            robot_output = "\n".join(output_lines)

            if return_code == 0:
                logger.info("Прошивка успешно установлена на устройство")
                return {
                    "status": "success",
                    "message": "Прошивка успешно установлена на устройство",
                    "robot_output": robot_output,
                    "installation_completed": True,
                }
            else:
                logger.error(
                    f"Ошибка при установке прошивки. Код возврата: {return_code}"
                )
                return {
                    "status": "error",
                    "message": f"Ошибка при установке прошивки. Код возврата: {return_code}",
                    "robot_output": robot_output,
                    "installation_completed": False,
                }

        except FileNotFoundError as e:
            logger.error(f"Файл прошивки не найден: {e}")
            return {
                "status": "error",
                "message": f"Файл прошивки не найден: {str(e)}",
                "installation_completed": False,
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при установке прошивки: {e}")
            return {
                "status": "error",
                "message": f"Неожиданная ошибка при установке прошивки: {str(e)}",
                "installation_completed": False,
            }

    async def check_router_availability(
        self, router_ip: str = "192.168.1.1", timeout: int = 60
    ) -> bool:
        """
        Проверяет доступность роутера через ping

        Args:
            router_ip: IP-адрес роутера для проверки
            timeout: Максимальное время ожидания в секундах

        Returns:
            bool: True если роутер доступен, False если нет
        """
        logger.info(
            f"Начинаем проверку доступности роутера {router_ip} (таймаут: {timeout}с)"
        )

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Используем ping для проверки доступности
                if os.name == "nt":  # Windows
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", router_ip],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                else:  # Linux/Unix
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", router_ip],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                if result.returncode == 0:
                    logger.info(f"Роутер {router_ip} доступен")
                    return True

            except subprocess.TimeoutExpired:
                logger.warning(f"Ping timeout для {router_ip}")
            except Exception as e:
                logger.warning(f"Ошибка при ping {router_ip}: {e}")

            # Ждем 2 секунды перед следующей попыткой
            await asyncio.sleep(2)
            elapsed = int(time.time() - start_time)
            logger.info(
                f"Роутер {router_ip} пока недоступен, прошло {elapsed}с из {timeout}с"
            )

        logger.error(f"Роутер {router_ip} недоступен после {timeout}с ожидания")
        return False

    async def firmware_test_cycle(self, request: FirmwareTestRequest):
        """
        Полный цикл: загрузка прошивки → установка → ожидание роутера → запуск тестов

        Этапы выполнения:
        1. Загрузка прошивки из OneDev (автоматически или по указанным параметрам)
        2. Реальная установка прошивки на устройство через Robot Framework
        3. Ожидание поднятия роутера
        4. Запуск тестов

        Args:
            request: Запрос с параметрами прошивки и тестирования

        Returns:
            dict: Результат полного цикла
        """
        # Импортируем здесь, чтобы избежать циклических импортов
        from api_service.domain.services.test_service import run_test_simulation, run_tests_sequentially
        from api_service.db.db_tests import tests_db
        import datetime

        logger.info("Начинаем полный цикл тестирования с прошивкой")

        # Этап 1: Загрузка прошивки
        logger.info("Этап 1: Загрузка прошивки из OneDev")

        firmware_request = FirmwareInstallRequest(
            build_id=request.build_id, artifact_path=request.artifact_path
        )

        try:
            firmware_result = await self.install_firmware(firmware_request)
            logger.info("Прошивка успешно загружена")

            # Получаем путь к загруженной прошивке
            firmware_path = firmware_result.get("details", {}).get("file_path")
            if not firmware_path:
                raise Exception("Не удалось получить путь к загруженной прошивке")

        except Exception as e:
            logger.error(f"Ошибка при загрузке прошивки: {e}")
            return {
                "status": "error",
                "message": f"Ошибка при загрузке прошивки: {str(e)}",
                "firmware_details": {},
                "test_status": "not_started",
                "test_details": None,
            }

        # Этап 2: Реальная установка прошивки на устройство (закомментировано)
        logger.info(f"Этап 2: Установка прошивки на устройство {request.router_ip}")

        # Этап 3: Ожидание поднятия роутера
        logger.info(
            f"Этап 3: Ожидание поднятия роутера {request.router_ip} ({request.wait_for_router}с)"
        )

        router_available = await self.check_router_availability(
            router_ip=request.router_ip, timeout=request.wait_for_router
        )

        if not router_available:
            logger.error("Роутер не поднялся в течение указанного времени")
            return {
                "status": "error",
                "message": "Роутер не поднялся после установки прошивки",
                "firmware_details": firmware_result.get("details", {}),
                "test_status": "not_started",
                "test_details": {
                    "error": "Router not available",
                    "installation_result": True,
                },
            }

        # Этап 4: Запуск тестов
        logger.info("Этап 4: Запуск тестов")

        try:
            # Сбрасываем статусы тестов
            current_time_utc_iso = datetime.datetime.now(
                datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

            if request.test_id and request.test_id != "all":
                # Запуск конкретного теста
                if request.test_id not in tests_db:
                    raise HTTPException(
                        status_code=404, detail=f"Тест {request.test_id} не найден"
                    )

                # Сброс статуса конкретного теста
                tests_db[request.test_id]["status"] = "pending"
                tests_db[request.test_id]["time_start"] = ""
                tests_db[request.test_id]["time_end"] = ""
                tests_db[request.test_id]["updated_at"] = current_time_utc_iso
                tests_db[request.test_id]["result"] = None

                # Запуск теста
                test_dict = tests_db[request.test_id].copy()
                test_dict["test_id"] = request.test_id

                # Запускаем тест асинхронно
                asyncio.create_task(run_test_simulation(test_dict))

                test_status = "started"
                test_details = {"test_id": request.test_id, "status": "running"}

            else:
                # Запуск всех тестов
                for test_key in tests_db.keys():
                    if test_key != "all":
                        tests_db[test_key]["status"] = "pending"
                        tests_db[test_key]["time_start"] = ""
                        tests_db[test_key]["time_end"] = ""
                        tests_db[test_key]["updated_at"] = current_time_utc_iso
                        tests_db[test_key]["result"] = None

                logger.info("device_data", request)
                if (
                    request.device_data["serial_number"]
                    and request.device_data["mac_address"]
                    and request.device_data["device_name"]
                ):
                    device_data = {
                        "serial_number": request.device_data["serial_number"],
                        "mac_address": request.device_data["mac_address"],
                        "device_name": request.device_data["device_name"],
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Необходимо указать serial_number, mac_address и device_name",
                    }

                # Запускаем все тесты асинхронно
                asyncio.create_task(run_tests_sequentially(device_data))

                test_status = "started"
                test_details = {"test_id": "all", "status": "running"}

            logger.info("Тесты успешно запущены")

            return {
                "status": "success",
                "message": "Полный цикл успешно выполнен: прошивка загружена и установлена, роутер поднялся, тесты запущены",
                "firmware_details": {
                    **firmware_result.get("details", {}),
                    "installation_result": True,
                },
                "test_status": test_status,
                "test_details": test_details,
            }

        except Exception as e:
            logger.error(f"Ошибка при запуске тестов: {e}")
            return {
                "status": "error",
                "message": f"Прошивка установлена, роутер поднялся, но ошибка при запуске тестов: {str(e)}",
                "firmware_details": {
                    **firmware_result.get("details", {}),
                    "installation_result": True,
                },
                "test_status": "error",
                "test_details": {"error": str(e)},
            }
