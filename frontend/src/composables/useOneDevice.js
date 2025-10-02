import { ref } from 'vue';
import { patchOneDevice } from '@/api/patch.js';
import { useToast } from 'primevue/usetoast';
import { useDataStore } from '@/stores/data.store';

export function useOneDevice() {
    const loading = ref(false);
    const error = ref(null);
    const toast = useToast();
    const dataStore = useDataStore();
    const deviceArray = []

    const fetchOneDevice = async (orderData) => {
        if (!orderData || orderData.length == 0) {
            const errorMessage = 'Devices array is required';
            error.value = errorMessage;
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: errorMessage,
                life: 3000,
            });
            throw new Error(errorMessage);
        }

        loading.value = true;
        error.value = null;

        try {

            for (const item of orderData) { // Вместо for можно сделать потом поиск необходимого устройства их массива

                // if Сделать условие, которое проверяет что устройство, то есть номенклатура, которая будет указана на интерфейсе соответствует устройству из массива, если да то пропускает

                for (const device of item.data) {
                    if (device.test_status !== 'Успешно' && device.test_status !== 'ВПроцессе') {
                        const data = {};
                        data.serial_number = device.serial_number;
                        data.mac_address = device.mac_address;
                        data.change_status_to = device.test_status;
                        deviceArray.push(data);
                    }
                }
            }

            // if ((data.serial_number && data.mac_address) && (data.change_status_to === "Успешно" || data.change_status_to === "Тестируется")) {
            if (deviceArray.length === 0) {
                toast.add({
                    severity: 'warn',
                    summary: 'Предупреждение',
                    detail: 'Все устройства протестированы или тестируются',
                    life: 4000,
                });
                throw new Error('Все устройства протестированы или тестируются');
            }

            const response = await patchOneDevice(deviceArray);

            // Проверяем структуру ответа
            if (!response) {
                throw new Error('Получен пустой ответ от сервера');
            }

            // Обработка ответа от 1С с проверкой continue_testing
            if (response && typeof response === 'object' && response.data && 'continue_testing' in response.data) {
                if (response.data.continue_testing === false) {
                    toast.add({
                        severity: 'warn',
                        summary: 'Предупреждение',
                        detail: response.result || 'Устройства из этого документа уже протестированы или тестируются',
                        life: 15000,
                    });
                    // Возвращаем ответ без дальнейшей обработки
                    return response;
                }
            }

            // Проверяем наличие данных
            if (!response.data && !Array.isArray(response)) {
                throw new Error('Некорректная структура данных в ответе');
            }

            // Определяем данные для сохранения
            const dataToStore = response.data || response;

            // Дополнительная проверка на массив устройств
            if (Array.isArray(dataToStore) && dataToStore.length === 0) {
                toast.add({
                    severity: 'warn',
                    summary: 'Предупреждение',
                    detail: 'Данные устройства не найдены',
                    life: 4000,
                });
            }

            // Сохраняем данные в store
            dataStore.deviceData = dataToStore;
            console.log('Данные устройства загружены:', dataToStore);

            toast.add({
                severity: 'success',
                summary: 'Успех',
                detail: `Данные устройства успешно загружены (${Array.isArray(dataToStore) ? dataToStore.length : 'объект'})`,
                life: 3000,
            });

            return response;
        } catch (err) {
            // Определяем тип ошибки для более точного сообщения
            let errorMessage = 'Ошибка при загрузке данных устройства';

            if (err.response) {
                // Ошибка HTTP ответа
                const status = err.response.status;
                switch (status) {
                    case 404:
                        errorMessage = 'Устройство не найдено';
                        break;
                    case 403:
                        errorMessage = 'Нет доступа к данным устройства';
                        break;
                    case 500:
                        errorMessage = 'Внутренняя ошибка сервера';
                        break;
                    default:
                        errorMessage = `Ошибка сервера (${status}): ${err.response.data?.message || err.message}`;
                }
            } else if (err.code === 'NETWORK_ERROR' || err.message.includes('Network')) {
                errorMessage = 'Ошибка сети. Проверьте подключение к интернету';
            } else if (err.name === 'TimeoutError') {
                errorMessage = 'Превышено время ожидания ответа от сервера';
            } else {
                errorMessage = err.message || errorMessage;
            }

            error.value = errorMessage;

            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: errorMessage,
                life: 5000,
            });

            throw err;
        } finally {
            loading.value = false;
        }
    };

    const clearDeviceData = () => {
        dataStore.deviceData = null;
        error.value = null;
    };

    return {
        loading,
        error,
        fetchOneDevice,
        clearDeviceData
    };
}