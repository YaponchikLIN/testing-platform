<template>
  <div class="flex items-center gap-4">
    <Button
      style="width: 150px"
      @click="runFullCycle"
      label="Run Test"
      :loading="loading"
    />

    <!-- Progress Dialog -->
    <Dialog
      v-model:visible="showProgressDialog"
      modal
      header="Installing the firmware"
      :style="{ width: '400px' }"
      :closable="false"
      :draggable="false"
      class="progress-dialog"
    >
      <div class="progress-content">
        <!-- Progress Bar -->
        <ProgressBar mode="indeterminate" class="test-progress-bar" />
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import {
  connectWebSocket,
  connectGpioWebSocket,
  disconnectGpioWebSocket,
} from "../services/websocket.service.js";
import { runFirmwareTestCycle } from "../api/firmware";
import { useDataStore } from "@/stores/data.store";
import Dialog from "primevue/dialog";
import ProgressBar from "primevue/progressbar";
import { useOneDevice } from "@/composables/useOneDevice.js";
import { useSNandMAC } from "@/composables/useSNandMAC.js";

const dataStore = useDataStore();
const { fetchSNandMAC } = useSNandMAC();
const { error, fetchOneDevice } = useOneDevice();
const loading = ref(false);
const showProgressDialog = ref(false);
const statusRunFullCycle = ref(false);

const runFullCycle = async () => {
  try {
    loading.value = true;
    showProgressDialog.value = true;
    statusRunFullCycle.value = true;

    console.log("Резервирование данных устройства для теста");
    await fetchSNandMAC(dataStore.order.order_uid);
    const resultFetch = await fetchOneDevice(dataStore.SNandMAC);
    if (resultFetch.data.continue_testing === false) {
      showProgressDialog.value = false;
      return;
    }
    if (
      resultFetch.data.serial_number &&
      resultFetch.data.mac_address &&
      resultFetch.data.device_name
    ) {
      dataStore.deviceData = {
        serial_number: resultFetch.data.serial_number,
        mac_address: resultFetch.data.mac_address,
        device_name: resultFetch.data.device_name,
      };
    }
    // Reset test data before new run
    for (const test of dataStore.tests) {
      test.status = "idle";
      test.timeStart = "";
      test.updatedAt = "";
      test.timeEnd = "";
      test.result = null;
    }

    // Run full cycle through new API
    const response = await runFirmwareTestCycle({
      test_id: "all",
      wait_for_router: 60,
      device_data: dataStore.deviceData,
    });

    console.log("Full cycle response:", response);

    if (response && typeof response === "object") {
      // Establish WebSocket connections for all tests
      for (const test of dataStore.tests) {
        connectWebSocket(test, dataStore);
      }

      console.log("Full cycle completed successfully");
      console.log("Firmware details:", response.firmware_details);
      console.log("Test status:", response.test_status);

      // Auto-close dialog after 3 seconds
      setTimeout(() => {
        showProgressDialog.value = false;
      }, 3000);
    } else {
      throw new Error(
        response.message || "Unknown error occurred during full cycle execution"
      );
    }
    statusRunFullCycle.value = false;
  } catch (error) {
    console.error("Error during full cycle execution:", error);
    statusRunFullCycle.value = false;
    // Auto-close dialog after 5 seconds on error
    setTimeout(() => {
      showProgressDialog.value = false;
    }, 5000);
  } finally {
    loading.value = false;
  }
};

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
</script>

<style scoped>
.progress-dialog {
  font-family: "Inter", sans-serif;
}

.progress-content {
  display: flex;
  justify-content: center;
  padding: 2rem 1rem;
}

.test-progress-bar {
  width: 100%;
  height: 0.75rem !important;
}

/* Progress bar styling */
:deep(.test-progress-bar .p-progressbar-value) {
  background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
  animation: progress-pulse 2s ease-in-out infinite;
}

@keyframes progress-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* Hide progress bar label */
:deep(.test-progress-bar .p-progressbar-label) {
  display: none !important;
}
</style>
