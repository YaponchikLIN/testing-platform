<template>
  <Toast />
  <div class="workflow-container">
    <div class="main-layout" v-if="dataStore.tests.length !== 0">
      <div class="sidebar-panel">
        <WorkflowControls
          :selectedPeriod="selectedPeriod"
          :selectedOrder="dataStore.order"
          :selectedDeviceType="selectedDeviceType"
          :useSelectionContainerClass="false"
          @show-sn-mac-dialog="showSNandMACDialog = $event"
        />
      </div>
      <div class="table-area">
        <TestStatuses />
      </div>
    </div>
    <div v-else class="centered-fields">
      <WorkflowControls
        :selectedPeriod="selectedPeriod"
        :selectedOrder="dataStore.order"
        :selectedDeviceType="selectedDeviceType"
        :useSelectionContainerClass="true"
        @show-sn-mac-dialog="showSNandMACDialog = $event"
      />
    </div>
    <!-- Диалоги ... -->

    <!-- Диалоги -->
    <PeriodDialog
      :visible="showPeriodDialog"
      @update:visible="showPeriodDialog = $event"
      @period-selected="handlePeriodSelected"
      @go-back="handlePeriodGoBack"
    />

    <OrderDialog
      :visible="showOrderDialog"
      @update:visible="showOrderDialog = $event"
      @order-selected="handleOrderSelected"
      @go-back="handleOrderGoBack"
    />

    <DeviceTypeDialog
      :visible="showDeviceTypeDialog"
      @update:visible="showDeviceTypeDialog = $event"
      @device-type-selected="handleDeviceTypeSelected"
      @go-back="handleDeviceTypeGoBack"
    />
    <SNandMACDialog
      :visible="showSNandMACDialog"
      @update:visible="showSNandMACDialog = $event"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted,onUnmounted } from "vue";
import { useToast } from "primevue/usetoast";
import SelectPeriod from "./SelectPeriod.vue";
import SelectDeviceType from "./SelectDeviceType.vue";
import SelectFirmware from "./SelectFirmware.vue";
import SelectOrder from "./SelectOrder.vue";
import ButtonStart from "../components/ButtonStart.vue";
import ButtonSNandMAC from "../components/ButtonSNandMAC.vue";
import OrderDialog from "./OrderDialog.vue";
import PeriodDialog from "./PeriodDialog.vue";
import DeviceTypeDialog from "./DeviceTypeDialog.vue";
import TestStatuses from "./TestStatuses.vue";
import SNandMACDialog from "./SNandMACDialog.vue";
import { useDataStore } from "@/stores/data.store";
import WorkflowControls from "./WorkflowControls.vue";
import { useOrders } from "@/composables/useOrders.js";
import { useSNandMAC } from "@/composables/useSNandMAC.js";

import {
  connectWebSocket,
  connectGpioWebSocket,
  disconnectGpioWebSocket,
} from "../services/websocket.service.js";

const gpioValue = ref(null);

const handleGpioChange = (value) => {
  gpioValue.value = value;
  if (gpioValue.value === "1" && !statusRunFullCycle.value) {
    runFullCycle();
  }
};

onMounted(() => {
  connectGpioWebSocket(handleGpioChange);
});

onUnmounted(() => {
  disconnectGpioWebSocket();
});

const dataStore = useDataStore();
const { loading, error, fetchOrders } = useOrders();
const { fetchSNandMAC } = useSNandMAC();

const toast = useToast();

const selectedPeriod = ref(null);
const selectedDeviceType = ref(null);

const showPeriodDialog = ref(true);
const showOrderDialog = ref(false);
const showDeviceTypeDialog = ref(false);
const showSNandMACDialog = ref(false);

const handlePeriodSelected = async (period) => {
  showPeriodDialog.value = false;
  selectedPeriod.value = period;
  showOrderDialog.value = true;
  const [dateFrom, dateTo] = period.sort((a, b) => new Date(a) - new Date(b));
  try {
    await fetchOrders(dateFrom, dateTo);
    console.log("Orders loaded successfully");
  } catch (error) {
    console.error("Failed to load orders:", error);
  }
};

const handleOrderSelected = async (order) => {
  dataStore.order = order;
  showOrderDialog.value = false;
  showDeviceTypeDialog.value = true;
  try {
    await fetchSNandMAC(order.order_uid);
  } catch (error) {
    // Ошибка уже обработана в композабле
    console.error("Failed to load SN and MAC:", error);
  }
};

const handleDeviceTypeSelected = (deviceType) => {
  selectedDeviceType.value = deviceType;
  showDeviceTypeDialog.value = false;
};

// Функции навигации назад
const handlePeriodGoBack = () => {
  // Первый диалог - просто закрываем или можем показать предупреждение
  showPeriodDialog.value = false;
  toast.add({
    severity: 'info',
    summary: 'Info',
    detail: 'Period selection cancelled',
    life: 3000,
  });
};

const handleOrderGoBack = () => {
  // Возвращаемся к выбору периода
  showOrderDialog.value = false;
  showPeriodDialog.value = true;
  // Очищаем выбранные заказы
  dataStore.orders = [];
};

const handleDeviceTypeGoBack = () => {
  // Возвращаемся к выбору заказа
  showDeviceTypeDialog.value = false;
  showOrderDialog.value = true;
  // Очищаем данные SN и MAC
  dataStore.SNandMAC = [];
};
</script>

<style scoped>
/* Основной контейнер workflow */
.workflow-container {
  width: 100%;
  height: 100%;
}

/* Layout с боковой панелью */
.main-layout {
  display: flex;
  gap: 1.5rem;
  height: 100%;
  min-height: 600px;
}

/* Боковая панель */
.sidebar-panel {
  width: 280px;
  min-width: 280px;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  /* display: flex; */
  flex-direction: column;
  gap: 1.5rem;
}

/* Контейнер полей */
.fields-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex: 1;
}

/* Компактные поля */
.field-item {
  width: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Контейнер кнопок в боковой панели */
.sidebar-panel .buttons-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: auto;
}

/* Кнопки одинакового размера */
.action-button {
  /* width: 100%; */
  height: 40px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Область таблицы */
.table-area {
  flex: 1;
  min-width: 0;
  border-radius: 12px;
  overflow: hidden;
}

/* Центрированные поля (когда нет таблицы) */
.centered-fields {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 2rem;
}

/* Современный адаптивный контейнер для выбора */
.selection-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
  align-items: start;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.selection-item {
  width: 100%;
  max-width: 300px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
}

/* Центрированные кнопки */
.buttons-container.centered {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0;
}

.buttons-container.centered .action-button {
  width: 200px;
  height: 40px;
}

/* Общие стили для кнопок */
:deep(.p-button) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 8px;
  font-weight: 600;
  letter-spacing: 0.025em;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Адаптивность */
@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
    gap: 1rem;
  }

  .sidebar-panel {
    width: 100%;
    min-width: auto;
    flex-direction: row;
    align-items: center;
    padding: 1rem;
  }

  .fields-container {
    flex-direction: row;
    flex: 1;
    gap: 1rem;
  }

  .sidebar-panel .buttons-container {
    flex-direction: row;
    margin-top: 0;
    gap: 0.5rem;
  }

  .action-button {
    width: 120px;
    height: 36px;
  }
}

@media (max-width: 768px) {
  .sidebar-panel {
    flex-direction: column;
    gap: 1rem;
  }

  .fields-container {
    flex-direction: column;
  }

  .sidebar-panel .buttons-container {
    flex-direction: column;
    width: 100%;
  }

  .action-button {
    width: 100%;
    height: 40px;
  }
}

@media (max-width: 576px) {
  .selection-container {
    grid-template-columns: 1fr;
    gap: 1.25rem;
    padding: 1.5rem 1rem;
  }

  .selection-item {
    max-width: 100%;
  }
}

/* FullHD оптимизация */
@media (min-width: 1400px) and (max-width: 1920px) {
  .sidebar-panel {
    width: 320px;
    min-width: 320px;
    padding: 2rem;
  }

  .fields-container {
    gap: 1.25rem;
  }

  .action-button {
    height: 44px;
  }
}

@media (min-width: 1921px) {
  .sidebar-panel {
    width: 360px;
    min-width: 360px;
    /* padding: 2.5rem; */
  }

  .fields-container {
    gap: 1.5rem;
  }

  .action-button {
    height: 48px;
  }
}
</style>
