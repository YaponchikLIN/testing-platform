import { ref } from 'vue';
import { getOrders } from '@/api/get.js';
import { useToast } from 'primevue/usetoast';
import { useDataStore } from '@/stores/data.store';

export function useOrders() {
    const loading = ref(false);
    const error = ref(null);
    const toast = useToast();
    const dataStore = useDataStore();

    const fetchOrders = async (dateFrom, dateTo) => {
        loading.value = true;
        error.value = null;

        try {
            const response = await getOrders({ dateFrom, dateTo });

            // Теперь response содержит прямой ответ от 1С
            if (response && (Array.isArray(response) || typeof response === 'object')) {
                dataStore.orders = response;
                return response;
            } else {
                throw new Error("Failed to fetch orders");
            }

        } catch (err) {
            error.value = err.message;
            toast.add({
                severity: "error",
                summary: "Error",
                detail: err.message,
                life: 3000,
            });
            throw err;
        } finally {
            loading.value = false;
        }
    };

    return {
        loading,
        error,
        fetchOrders
    };
}