from api_service.db.db_tests import tests_db
from api_service.db.postgres_db import db
from api_service.app.config import connected_clients
from api_service.domain.models.test_models import TestRequest, TestStatus
import asyncio
import datetime
import os
import json
import re

from api_service.api.routes.requests_1c import patch_one_device_1c


# Безопасная загрузка JSON-данных с обработкой различных кодировок
def safe_load_json(file_path):
    encodings = ["utf-8", "utf-8-sig", "cp1251", "latin1", "windows-1252", "iso-8859-1"]

    # Проверяем существование файла
    if not os.path.exists(file_path):
        raise Exception(f"Файл {file_path} не существует")

    # Пробуем разные кодировки
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
                # Убираем BOM если есть
                if content.startswith("\ufeff"):
                    content = content[1:]
                return json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Не удалось прочитать {file_path} в кодировке {encoding}: {e}")
            continue

    # Fallback: читаем как бинарные данные и очищаем проблемные байты
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()

        # Очищаем проблемные байты
        # Удаляем или заменяем известные проблемные байты
        problem_bytes = [
            b"\x97",
            b"\xce",
            b"\x81",
            b"\x82",
            b"\x83",
            b"\x84",
            b"\x85",
            b"\x86",
            b"\x87",
        ]
        clean_data = raw_data
        for pb in problem_bytes:
            clean_data = clean_data.replace(pb, b"?")

        # Декодируем с заменой проблемных символов
        text_data = clean_data.decode("utf-8", errors="replace")

        # Пытаемся распарсить JSON
        return json.loads(text_data)

    except Exception as e:
        raise Exception(f"Не удалось загрузить JSON файл {file_path}: {e}")


# Функция для отправки статуса
async def broadcast_status(test_dict: dict, status_to_broadcast: str):
    test_id = test_dict.get("test_id")
    if not test_id:
        print(f"Ошибка: 'test_id' не найден в словаре теста: {test_dict}")
        return

    print(f"Изменение статуса теста-отправка через websocket для test_id: {test_id}")
    print(
        f"broadcast_status test_dict: {test_dict}, status_to_broadcast: {status_to_broadcast}"
    )

    print("connected_clients:", connected_clients)
    if test_id in connected_clients:
        clients_to_notify = list(connected_clients[test_id])
        for client in clients_to_notify:
            try:
                # Отправляем полный объект теста вместе со статусом
                print("await client.send_json()", test_dict)
                await client.send_json(test_dict)
            except Exception as e:
                print(f"Ошибка отправки сообщения клиенту: {e}")
                if (
                    test_id in connected_clients
                    and client in connected_clients[test_id]
                ):
                    connected_clients[test_id].remove(client)


# Имитация выполнения теста (замените на запуск Robot Framework)
async def run_robot_test(robot_file, test_id):
    max_retries = 10
    return_code = 1
    attempt = 0
    # Создаем уникальную директорию для каждого теста
    output_dir = f"output_{test_id}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Используется директория вывода: {output_dir} для теста {test_id}")

    # Нормализуем путь к robot файлу для избежания проблем с escape-последовательностями
    normalized_robot_file = robot_file.replace("\\", "/")

    while return_code != 0 and attempt < max_retries:
        process = await asyncio.create_subprocess_exec(
            "robot",
            "--outputdir",
            output_dir,
            normalized_robot_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return_code = process.returncode
        print(f"Attempt {attempt + 1}: robot_file: {robot_file}")
        print(f"return_code: {return_code}")
        if stderr:
            stderr_decoded = stderr.decode("utf-8", errors="replace")
            print(f"stderr: {stderr_decoded}")
        attempt += 1
        if return_code != 0:
            print(f"Основной тест {robot_file} не удался, запуск ports.robot...")
            ports_robot_file = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "robot-tests", "ports.robot"
                )
            )
            # Нормализуем путь для избежания проблем с escape-последовательностями
            ports_robot_file = ports_robot_file.replace("\\", "/")
            process = await asyncio.create_subprocess_exec(
                "robot",
                "--outputdir",
                output_dir,
                ports_robot_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            ports_return_code = process.returncode
            print(f"ports.robot завершился с кодом: {ports_return_code}")
            if stderr:
                stderr_decoded = stderr.decode("utf-8", errors="replace")
                print(f"ports.robot stderr: {stderr_decoded}")

    if return_code != 0:
        raise Exception(f"Robot Framework failed with error after {attempt} attempts")

    print("Тест завершён: ", robot_file)
    return return_code


async def run_tests_sequentially(test_request_payload: TestRequest):
    print("Последовательный запуск всех тестов из test_service.py...")

    test_status = TestStatus.FAIL
    wifi_task = None

    # Определяем порядок тестов: WiFi первым, затем остальные
    test_order = []
    other_tests = []
    
    for test_key in tests_db.keys():
        if test_key != "all":
            if test_key == "wifi":
                test_order.insert(0, test_key)  # WiFi первым
            else:
                other_tests.append(test_key)
    
    test_order.extend(other_tests)  # Добавляем остальные тесты
    
    print(f"Порядок выполнения тестов: {test_order}")

    for test_key in test_order:
        test_item_in_db = tests_db[test_key]
        test_item_in_db["test_id"] = test_key

        current_time_utc_iso = datetime.datetime.now(
            datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        test_item_in_db["status"] = "running"
        test_item_in_db["time_start"] = current_time_utc_iso
        test_item_in_db["updated_at"] = current_time_utc_iso
        test_item_in_db["time_end"] = ""
        test_item_in_db["result"] = None

        await broadcast_status(test_item_in_db, "running")

        # Специальная обработка для WiFi теста - запускаем асинхронно
        if test_key == "wifi":
            print("Запуск WiFi теста асинхронно...")
            wifi_task = asyncio.create_task(
                run_test_simulation(test_item_in_db, test_request_payload)
            )
            # Даем WiFi тесту время на инициализацию
            await asyncio.sleep(5)
            print("WiFi тест запущен в фоновом режиме, продолжаем с другими тестами")
        else:
            # Обычные тесты выполняем синхронно
            result = await run_test_simulation(test_item_in_db, test_request_payload)

            if test_status != TestStatus.ERROR or test_status != TestStatus.FAIL:
                test_status = result

            print(f"Тест завершён: {test_key}")

    # Ожидаем завершения WiFi теста, если он был запущен
    if wifi_task:
        print("Ожидание завершения WiFi теста...")
        try:
            wifi_result = await wifi_task
            print(f"WiFi тест завершён с результатом: {wifi_result}")
            
            # Обновляем общий статус с учетом результата WiFi теста
            if test_status != TestStatus.ERROR or test_status != TestStatus.FAIL:
                test_status = wifi_result
        except Exception as e:
            print(f"Ошибка при выполнении WiFi теста: {e}")
            test_status = TestStatus.ERROR

    # Преобразуем статус для 1C
    if test_status == TestStatus.ERROR:
        test_status = "Ошибка"
    elif test_status == TestStatus.SUCCESS:
        test_status = "Успешно"
    elif test_status == TestStatus.FAIL:
        test_status = "Неудачно"

    await patch_one_device(
        {
            "serial_number": test_request_payload["serial_number"],
            "mac_address": [test_request_payload["mac_address"]],
            "change_status_to": test_status,
        }
    )


async def run_test_simulation(test_dict: dict, test_request_payload: dict):
    try:
        # Получаем данные из payload
        mac_address = test_request_payload["mac_address"]
        serial_number = test_request_payload["serial_number"]

        if not mac_address or not serial_number:
            raise ValueError("MAC адрес и серийный номер обязательны")

        test_id = test_dict.get("test_id")

        if not test_id:
            print(f"Ошибка: 'test_id' не найден в словаре: {test_dict}")
            return

        print(f"run_test_simulation для test_id: {test_id}, data: {test_dict}")
        try:
            # Устанавливаем статус "executing" после начальной фазы
            await asyncio.sleep(2)
            current_time_utc_iso = datetime.datetime.now(
                datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            if test_id in tests_db:
                tests_db[test_id]["status"] = "executing"
                tests_db[test_id]["updated_at"] = current_time_utc_iso
                print(
                    f"action await broadcast_status() для test_id: {test_id}, data: {tests_db[test_id]}"
                )
                await broadcast_status(tests_db[test_id], "executing")
            else:
                print(f"Ошибка: Тест {test_id} не найден в tests_db (executing).")
                return

            # Получаем данные устройства из payload
            mac_address = test_request_payload["mac_address"]
            serial_number = test_request_payload["serial_number"]

            # Запуск теста Robot Framework
            print("Запуск Robot Framework...")
            json_file = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "..",
                    "..",
                    "robot-tests",
                    f"{test_id}.json",
                )
            )
            if os.path.isfile(json_file):
                try:
                    os.remove(json_file)
                    print(f"Удален файл: {json_file}")
                except Exception as e:
                    print(f"Не удалось удалить файл {json_file}: {e}")
            else:
                print(f"Файл {json_file} не существует (это нормально)")

            robot_file = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "..",
                    "..",
                    "robot-tests",
                    f"{test_id}.robot",
                )
            )
            if not os.path.isfile(robot_file):
                print(f"Ошибка: файл {robot_file} не существует")
                raise Exception(f"Файл теста {robot_file} не найден")

            # return_code, stdout_decoded, stderr_decoded = await run_robot_test(robot_file, test_id)
            return_code = await run_robot_test(robot_file, test_id)
            # print("Результат выполнения Robot Framework:")
            # print(f"stdout: {stdout_decoded}")
            # if stderr_decoded:
            #     print(f"stderr: {stderr_decoded}")
            #     raise Exception(stderr_decoded)

            # Ожидаем создания JSON файла тестом Robot Framework
            json_file_check_attempts = 0
            max_json_check_attempts = 30  # 30 секунд ожидания

            while (
                not os.path.isfile(json_file)
                and json_file_check_attempts < max_json_check_attempts
            ):
                await asyncio.sleep(1)
                json_file_check_attempts += 1
                print(
                    f"Ожидание создания JSON файла: {json_file} (попытка {json_file_check_attempts})"
                )

            if not os.path.isfile(json_file):
                print(f"Ошибка: файл {json_file} не был создан тестом")
                # Создаем базовый JSON файл на основе output.xml как fallback
                output_xml_file = f"output_{test_id}/output.xml"
                if os.path.isfile(output_xml_file):
                    # Безопасное чтение XML файла с обработкой различных кодировок
                    xml_content = None
                    encodings = [
                        "utf-8",
                        "utf-8-sig",
                        "cp1251",
                        "windows-1252",
                        "iso-8859-1",
                        "latin1",
                    ]

                    for encoding in encodings:
                        try:
                            with open(output_xml_file, "r", encoding=encoding) as f:
                                xml_content = f.read()
                                # Убираем BOM если есть
                                if xml_content.startswith("\ufeff"):
                                    xml_content = xml_content[1:]
                            break
                        except UnicodeDecodeError as e:
                            print(
                                f"Не удалось прочитать XML в кодировке {encoding}: {e}"
                            )
                            continue

                    if xml_content is None:
                        # Fallback: читаем как бинарные данные и очищаем проблемные символы
                        with open(output_xml_file, "rb") as f:
                            raw_data = f.read()
                            # Очищаем проблемные байты
                            problem_bytes = [
                                b"\x97",
                                b"\xce",
                                b"\x81",
                                b"\x82",
                                b"\x83",
                                b"\x84",
                                b"\x85",
                                b"\x86",
                                b"\x87",
                            ]
                            clean_data = raw_data
                            for pb in problem_bytes:
                                clean_data = clean_data.replace(pb, b"?")
                            xml_content = clean_data.decode("utf-8", errors="replace")

                    # Извлекаем статистику тестов из XML
                    passed_match = re.search(r"(\d+) passed", xml_content)
                    failed_match = re.search(r"(\d+) failed", xml_content)
                    total_match = re.search(r"(\d+) test", xml_content)

                    passed_tests = int(passed_match.group(1)) if passed_match else 0
                    failed_tests = int(failed_match.group(1)) if failed_match else 0
                    total_tests = int(total_match.group(1)) if total_match else 0

                    progress = (
                        int((passed_tests / total_tests) * 100)
                        if total_tests > 0
                        else 0
                    )

                    json_data = {
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "total_tests": total_tests,
                        "progress": progress,
                        "test_status": "COMPLETED" if failed_tests == 0 else "FAILED",
                    }

                    # Создаем JSON файл
                    try:
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=4, ensure_ascii=False)
                        print(f"Создан fallback JSON файл: {json_file}")
                    except Exception as e:
                        print(f"Ошибка создания fallback JSON файла: {e}")
                        json_data = {}  # fallback к пустому словарю
                else:
                    print(f"XML файл {output_xml_file} также не найден")
                    json_data = {}  # fallback к пустому словарю

            # Безопасная загрузка JSON данных
            try:
                json_data = safe_load_json(json_file)
                print(f"Успешно загружен JSON файл: {json_file}")
            except Exception as e:
                print(f"Ошибка загрузки JSON файла {json_file}: {e}")
                json_data = {}  # fallback к пустому словарю

            # Сохранение результатов в PostgreSQL
            test_status_for_1c = await save_test_results_to_db(
                test_id, json_data, mac_address, serial_number
            )

            # Завершение и обновление статуса
            await asyncio.sleep(3)
            current_time_utc_iso = datetime.datetime.now(
                datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            if test_id in tests_db:
                tests_db[test_id]["status"] = "completed"
                tests_db[test_id]["time_end"] = current_time_utc_iso
                tests_db[test_id]["updated_at"] = current_time_utc_iso
                # Извлекаем progress из json_data, если он есть
                progress = (
                    json_data.get("progress", 0) if isinstance(json_data, dict) else 0
                )

                tests_db[test_id]["result"] = {
                    "passed": True,
                    "details": f"Test {test_id} completed",
                    "data": json_data,
                    "progress": progress,
                }
                print(
                    f"actions await broadcast_status() для test_id: {test_id}, data: {tests_db[test_id]}"
                )
                await broadcast_status(tests_db[test_id], "completed")
                return test_status_for_1c  # Сделать возврат в зависимости от прогресса
            else:
                print(f"Ошибка: Тест {test_id} не найден в tests_db (completed).")
                return TestStatus.ERROR

        except Exception as e:
            print(f"Ошибка во время теста {test_id}: {str(e)}")
            import traceback

            traceback.print_exc()  # Для отладки
            if test_id in tests_db:
                current_time_utc_iso = datetime.datetime.now(
                    datetime.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

                tests_db[test_id]["status"] = "error"
                tests_db[test_id]["time_end"] = current_time_utc_iso
                tests_db[test_id]["updated_at"] = current_time_utc_iso
                tests_db[test_id]["result"] = {"passed": False, "details": str(e)}
                print(
                    f"actions await broadcast_status() error для test_id: {test_id}, data: {tests_db[test_id]}"
                )
                await broadcast_status(tests_db[test_id], "error")
                return TestStatus.ERROR
        finally:
            print(f"Устройство обновлено со статусом COMPLETED")
    except Exception as e:

        print(f"Критическая ошибка в run_test_simulation: {str(e)}")
        import traceback

        traceback.print_exc()  # Для отладки

        print(f"Устройство обновлено со статусом ERROR")
        return TestStatus.ERROR


async def patch_one_device(device_for_1C):
    try:
        updated_device_1c = await patch_one_device_1c([device_for_1C])
        if updated_device_1c:  # Получить код и в зависимости от кода выполнить действие
            print(f"Устройство {device_for_1C['serial_number']} обновлено в 1С")
    except Exception as e:
        print(f"Ошибка при обновлении статуса устройства в 1С: {e}")


async def save_test_results_to_db(
    test_id: str, json_data: dict, mac_address: str, serial_number: str
):
    """Сохранение результатов тестов в PostgreSQL базу данных"""
    try:
        # Проверяем, что подключение к базе данных установлено
        if db.pool is None:
            print(f"Предупреждение: PostgreSQL недоступен, результаты теста {test_id} не сохранены")
            return
            
        # Создаем запись выполнения теста
        execution_id = await db.create_test_execution(test_id, "completed")

        # Определяем время выполнения и статус
        time_start = datetime.datetime.now(datetime.timezone.utc)
        time_end = time_start  # Для завершенных тестов
        execution_time = 0

        # Извлекаем данные из JSON
        progress_raw = (
            json_data.get("progress", 0) if isinstance(json_data, dict) else 0
        )
        # Преобразуем progress в целое число
        try:
            progress = int(progress_raw) if progress_raw is not None else 0
        except (ValueError, TypeError):
            progress = 0

        test_status = (
            json_data.get("test_status", "COMPLETED")
            if isinstance(json_data, dict)
            else "COMPLETED"
        )

        # Определяем успешность теста
        test_status_for_1C = TestStatus.SUCCESS
        result_passed = True
        result_details = f"Test {test_id} completed successfully"

        if test_status in ["FAILED", "ERROR"]:
            result_passed = False
            result_details = f"Test {test_id} failed"

            if test_status == "FAILED":
                test_status_for_1C = TestStatus.FAIL
            elif test_status == "ERROR":
                test_status_for_1C = TestStatus.ERROR

        elif isinstance(json_data, dict):
            # Для SIM тестов проверяем результаты слотов
            if test_id == "sim":
                for key, value in json_data.items():
                    if key.startswith("slot_") and isinstance(value, dict):
                        if (
                            value.get("ping_result") == "fail"
                            or value.get("connected") == "error"
                        ):
                            result_passed = False
                            result_details = (
                                f"Test {test_id} failed - slot issues detected"
                            )
                            test_status_for_1C = TestStatus.FAIL
                            break

            # Для Ethernet тестов проверяем интерфейсы
            elif test_id == "ethernets":
                interfaces = json_data.get("interfaces", [])
                # Добавляем дополнительную проверку типа interfaces
                if isinstance(interfaces, list):
                    for interface in interfaces:
                        if (
                            isinstance(interface, dict)
                            and interface.get("ping_result") == "fail"
                        ):
                            result_passed = False
                            result_details = (
                                f"Test {test_id} failed - interface ping failures"
                            )
                            test_status_for_1C = TestStatus.FAIL
                            break
                else:
                    print(
                        f"Предупреждение: interfaces не является списком в тесте {test_id}"
                    )

        # Обновляем основную запись выполнения
        if db.pool is not None:
            await db.update_test_execution(
                execution_id,
                time_start=time_start,
                time_end=time_end,
                execution_time=execution_time,
                progress=progress,
                result_passed=result_passed,
                result_details=result_details,
                result_data=json_data,
            )

        # Обновляем статус в 1С только после успешного сохранения в БД
        # device_for_1C = {
        #     "serial_number": serial_number,
        #     "mac_address": [mac_address],
        #     "change_status_to": test_status_for_1C,
        # }

        # await patch_one_device(device_for_1C)

        # Сохраняем детальные результаты в зависимости от типа теста
        if db.pool is not None:
            if test_id == "sim" and isinstance(json_data, dict):
                await db.save_sim_test_results(execution_id, json_data)
            elif test_id == "ethernets" and isinstance(json_data, dict):
                await db.save_ethernet_test_results(execution_id, json_data)

        print(
            f"Результаты теста {test_id} успешно сохранены в PostgreSQL (execution_id: {execution_id})"
        )

        return test_status_for_1C
    except Exception as e:
        print(f"Ошибка при сохранении результатов теста {test_id} в PostgreSQL: {e}")
        import traceback

        traceback.print_exc()  # Для отладки

        # В случае ошибки сохранения в БД, отправляем статус "Ошибка" в 1С
        # try:
        #     device_for_1C = {
        #         "serial_number": serial_number,
        #         "mac_address": [mac_address],
        #         "change_status_to": "Ошибка",
        #     }

        #     await patch_one_device(device_for_1C)

        # except Exception as e1c:
        #     print(f"Ошибка при отправке статуса ошибки в 1С: {e1c}")

        return
