// api/firmware.js
import apiClient from './apiClient';

/**
 * Устанавливает прошивку на устройство
 * @returns {Promise<Object>} - Результат установки прошивки
 */
export async function installFirmware() {
    const response = await apiClient.post('firmware/install', {});
    return response.data;
}

/**
 * Запускает полный цикл: загрузка прошивки → установка → ожидание роутера → запуск тестов
 * @param {Object} params - Параметры для полного цикла
 * @param {string} params.build_id - ID билда (опционально)
 * @param {string} params.artifact_path - Путь к артефакту (опционально)
 * @param {string} params.test_id - ID теста для запуска ("all" для всех тестов)
 * @param {number} params.wait_for_router - Время ожидания роутера в секундах
 * @returns {Promise<Object>} - Результат полного цикла
 */
export async function runFirmwareTestCycle(params = {}) {
    const requestData = {
        build_id: params.build_id || null,
        artifact_path: params.artifact_path || null,
        test_id: params.test_id || "all",
        wait_for_router: params.wait_for_router || 60,
        device_data: params.device_data || {}
    };

    const response = await apiClient.post('firmware/test-cycle', requestData);
    return response.data;
}