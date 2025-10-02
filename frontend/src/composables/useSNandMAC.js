import { ref } from 'vue';
import { getSNandMAC } from '@/api/get.js';
import { useToast } from 'primevue/usetoast';
import { useDataStore } from '@/stores/data.store';

export function useSNandMAC() {
  const loading = ref(false);
  const error = ref(null);
  const toast = useToast();
  const dataStore = useDataStore();

  const fetchSNandMAC = async (order) => {
    if (!order) {
      const errorMessage = 'Order with ID is required';
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
      const response = await getSNandMAC(order);

      // Проверяем структуру ответа
      if (!response) {
        throw new Error('Получен пустой ответ от сервера');
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
          detail: 'Данные устройств не найдены для указанного заказа',
          life: 4000,
        });
      }

      // Сохраняем данные в store
      dataStore.SNandMAC = dataToStore;
      console.log('SN and MAC данные загружены:', dataToStore);

      toast.add({
        severity: 'success',
        summary: 'Успех',
        // detail: `SN и MAC данные успешно загружены (${Array.isArray(dataToStore) ? dataToStore.length : 'объект'})`,
        detail: `Данные устройств успешно загружены`,
        life: 3000,
      });

      return response;
    } catch (err) {
      // Определяем тип ошибки для более точного сообщения
      let errorMessage = 'Ошибка при загрузке SN и MAC данных';

      if (err.response) {
        // Ошибка HTTP ответа
        const status = err.response.status;
        switch (status) {
          case 404:
            errorMessage = 'Заказ не найден';
            break;
          case 403:
            errorMessage = 'Нет доступа к данным заказа';
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
        life: 15000,
      });

      throw err;
    } finally {
      loading.value = false;
    }
  };

  const clearSNandMAC = () => {
    dataStore.SNandMAC = null;
    error.value = null;
  };

  return {
    loading,
    error,
    fetchSNandMAC,
    clearSNandMAC
  };
}