<template>
  <div class="p-4 test-statuses-container" style="margin-top: 20px">
    <Message
      v-if="errorMessage"
      severity="error"
      :closable="true"
      @close="errorMessage = ''"
      class="mb-4"
    >
      {{ errorMessage }}
    </Message>

    <div class="table-controls">
      <Button
        icon="pi pi-info-circle"
        :label="showDetailColumns ? 'Hide Details' : 'Show details'"
        class="details-toggle-btn"
        @click="toggleDetailColumns"
        :class="{ expanded: showDetailColumns }"
      />
    </div>

    <DataTable
      :value="dataStore.tests"
      responsiveLayout="stack"
      breakpoint="768px"
      stripedRows
      :paginator="dataStore.tests.length > 50"
      :rows="5"
      :rowsPerPageOptions="[5, 10, 20]"
      class="p-datatable-sm modern-responsive-table"
      :scrollable="false"
    >
      <Column
        field="testId"
        header="Test ID"
        class="test-id-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <div class="test-id-cell">
            <span class="test-id-badge">{{ slotProps.data.testId }}</span>
          </div>
        </template>
      </Column>

      <Column
        field="status"
        header="Status"
        class="status-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <div class="status-cell">
            <Tag
              :value="slotProps.data.status"
              :severity="getStatusSeverity(slotProps.data)"
              :class="getStatusTagClass(slotProps.data)"
            />
          </div>
        </template>
      </Column>
      <!-- Start Time Column - conditionally visible -->
      <Column
        v-if="showDetailColumns"
        field="timeStart"
        header="Start Time"
        class="time-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <span>{{ formatDateTime(slotProps.data.timeStart) }}</span>
        </template>
      </Column>

      <!-- Updated Column - conditionally visible -->
      <Column
        v-if="showDetailColumns"
        field="updatedAt"
        header="Updated"
        class="time-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <span>{{ formatDateTime(slotProps.data.updatedAt) }}</span>
        </template>
      </Column>

      <!-- Completed Column - conditionally visible -->
      <Column
        v-if="showDetailColumns"
        field="timeEnd"
        header="Completed"
        class="time-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <span>{{ formatDateTime(slotProps.data.timeEnd) }}</span>
        </template>
      </Column>

      <Column
        field="result"
        header="Results"
        class="results-column"
        headerClass="column-header"
      >
        <template #body="slotProps">
          <div class="result-container">
            <!-- Progress bar for all statuses except idle and error -->
            <ProgressBar
              v-if="
                slotProps.data.status !== 'idle' &&
                slotProps.data.status !== 'error'
              "
              :value="getProgressValue(slotProps.data)"
              :class="getProgressBarClass(slotProps.data)"
              class="compact-progress"
              :mode="getProgressMode(slotProps.data.status)"
              :showValue="false"
            />

            <!-- Result details -->
            <div
              v-if="
                slotProps.data.result &&
                typeof slotProps.data.result === 'object'
              "
              class="result-details"
            >
              <!-- Show interface progress for ethernets tests -->
              <div
                v-if="
                  slotProps.data.testId === 'ethernets' &&
                  slotProps.data.result?.completed_interfaces !== undefined &&
                  slotProps.data.result?.total_interfaces !== undefined
                "
                class="interface-progress"
              >
                <strong>Interfaces:</strong>
                {{ slotProps.data.result.completed_interfaces }}/{{
                  slotProps.data.result.total_interfaces
                }}
              </div>

              <!-- Show WiFi connection info -->
              <div
                v-if="
                  slotProps.data.testId === 'wifi' &&
                  slotProps.data.result
                "
                class="wifi-info"
              >
                <div v-if="slotProps.data.result.ssid" class="wifi-detail">
                  <strong>SSID:</strong> {{ slotProps.data.result.ssid }}
                </div>
                <div v-if="slotProps.data.result.connection_status" class="wifi-detail">
                  <strong>Connection:</strong> 
                  <span :class="getWiFiConnectionClass(slotProps.data.result.connection_status)">
                    {{ formatWiFiConnectionStatus(slotProps.data.result.connection_status) }}
                  </span>
                </div>
                <div v-if="slotProps.data.result.download_speed_mbps > 0 || slotProps.data.result.upload_speed_mbps > 0" class="wifi-speeds">
                  <span v-if="slotProps.data.result.download_speed_mbps > 0">
                    <strong>↓</strong> {{ slotProps.data.result.download_speed_mbps }} Mbps
                  </span>
                  <span v-if="slotProps.data.result.upload_speed_mbps > 0" style="margin-left: 10px;">
                    <strong>↑</strong> {{ slotProps.data.result.upload_speed_mbps }} Mbps
                  </span>
                </div>
                <div v-if="slotProps.data.result.signal_strength" class="wifi-detail">
                  <strong>Signal:</strong> {{ slotProps.data.result.signal_strength }}%
                </div>
              </div>

              <!-- Show failed conditions -->
              <div
                v-if="getFailedConditions(slotProps.data).length > 0"
                class="failed-conditions"
              >
                <strong>Failed conditions:</strong>
                <ul>
                  <li
                    v-for="condition in getFailedConditions(slotProps.data)"
                    :key="condition"
                  >
                    {{ condition }}
                  </li>
                </ul>
              </div>

              <!-- Details Button -->
              <div style="margin-top: 10px">
                <Button
                  label="Details"
                  :class="`details-btn-${getStatusSeverity(slotProps.data)}`"
                  @click="openResultDialog(slotProps.data)"
                  v-tooltip.top="'View detailed test information'"
                />
              </div>
            </div>
            <span v-else-if="slotProps.data.status === 'idle'">{{
              slotProps.data.result || "—"
            }}</span>
            <span v-else-if="slotProps.data.status === 'running'"
              >Initializing...</span
            >
            <span v-else-if="slotProps.data.status === 'executing'"
              >Running tests...</span
            >
            <span v-else-if="slotProps.data.status === 'error'"
              >Execution error</span
            >
          </div>
        </template>
      </Column>

      <template #empty> There is no data to display </template>
    </DataTable>
    <ResultDialog
      :visible="showResultDialog"
      :testData="selectedTestData"
      @update:visible="showResultDialog = $event"
    />

    <!-- Test Results Summary Dialog -->
    <Dialog
      v-model:visible="showResultsSummary"
      modal
      header="Test Results Summary"
      :style="{ width: '450px' }"
      :closable="true"
      @hide="closeResultsSummary"
      class="results-summary-dialog"
    >
      <div class="results-summary-content">
        <div class="results-circles">
          <!-- Overall Test Result Circle -->
          <div class="result-circle-container">
            <div class="result-circle" :class="overallTestResult.status">
              <!-- Общий результат -->
            </div>
            <div class="circle-label">{{ overallTestResult.label }}</div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button
          label="Close"
          icon="pi pi-times"
          @click="closeResultsSummary"
          class="p-button-text"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useDataStore } from "@/stores/data.store";
import ResultDialog from "./ResultDialog.vue";
import { ProgressBar } from "primevue";
import Button from "primevue/button";

const dataStore = useDataStore();
// Toggle detail columns visibility
const showDetailColumns = ref(false);
// Test results summary dialog
const showResultsSummary = ref(false);
const hasShownSummary = ref(false);

const toggleDetailColumns = () => {
  showDetailColumns.value = !showDetailColumns.value;
};

// Check if all tests are completed
const allTestsCompleted = computed(() => {
  const tests = dataStore.tests;
  if (!tests || tests.length === 0) return false;

  return tests.every(
    (test) =>
      test.status === "completed" ||
      test.status === "failed" ||
      test.status === "error"
  );
});

// Get test results summary
const testResultsSummary = computed(() => {
  const tests = dataStore.tests;
  const summary = {
    passed: [],
    failed: [],
    error: [],
  };

  tests.forEach((test) => {
    if (test.status === "completed") {
      const progressValue = progress.value[test.testId] || 0;
      if (progressValue >= 80) {
        summary.passed.push(test.testId);
      } else {
        summary.failed.push(test.testId);
      }
    } else if (test.status === "failed") {
      summary.failed.push(test.testId);
    } else if (test.status === "error") {
      summary.error.push(test.testId);
    }
  });

  return summary;
});

// Overall test result
const overallTestResult = computed(() => {
  const hasFailures =
    testResultsSummary.value.failed.length > 0 ||
    testResultsSummary.value.error.length > 0;

  if (hasFailures) {
    return {
      status: "failed",
      label: "FAIL",
      // message: "Обнаружены проблемы в одном или нескольких тестах",
    };
  } else {
    return {
      status: "passed",
      label: "SUCCESS",
      // message: "Все компоненты системы работают корректно",
    };
  }
});

// Watch for all tests completion
watch(allTestsCompleted, (newValue) => {
  if (newValue && !hasShownSummary.value) {
    showResultsSummary.value = true;
    hasShownSummary.value = true;
  }
});

// Watch for test reset (when any test goes back to idle status)
watch(
  () => dataStore.tests,
  (newTests) => {
    // Check if any test has been reset to idle status
    const hasIdleTests = newTests.some(test => test.status === 'idle');
    const allTestsIdle = newTests.every(test => test.status === 'idle');
    
    // Reset summary flag when tests are reset
    if (allTestsIdle && hasShownSummary.value) {
      hasShownSummary.value = false;
      console.log('Reset hasShownSummary flag - tests have been reset');
    }
  },
  { deep: true }
);

const closeResultsSummary = () => {
  showResultsSummary.value = false;
};

// Адаптивные стили для таблицы
const tableStyle = computed(() => {
  if (window.innerWidth <= 768) {
    return "min-width: 100%; width: 100%;";
  } else if (window.innerWidth <= 992) {
    return "min-width: 600px; width: 100%;";
  } else {
    return "min-width: 800px; width: 100%;";
  }
});

const testIdColumnStyle = computed(() => {
  if (window.innerWidth <= 768) {
    return "width: 30%; min-width: 80px;";
  } else {
    return "width: 20%; min-width: 120px;";
  }
});

const resultsColumnStyle = computed(() => {
  if (window.innerWidth <= 768) {
    return "width: 70%; min-width: 200px;";
  } else {
    return "width: 80%; min-width: 300px;";
  }
});

const testIdInput = ref("");
const errorMessage = ref("");

onMounted(() => {
  const test = dataStore.tests;
  console.log("Running tests");
});

// Используем прогресс, вычисленный на backend
const progress = computed(() => {
  let progressMap = {};

  for (const test of dataStore.tests) {
    // Используем поле progress из backend, если оно доступно
    if (test.result && typeof test.result.progress !== "undefined") {
      progressMap[test.testId] = test.result.progress;
    } else {
      // Fallback для старых данных без поля progress
      progressMap[test.testId] = 0;
    }
  }

  return progressMap;
});

const getStatusSeverity = (testData) => {
  const status = testData.status;
  if (!status) return "info"; // Default

  switch (status.toLowerCase()) {
    case "running":
      return "info"; // Blue (PrimeVue Info)
    case "executing":
      return "warning"; // Yellow/Orange (PrimeVue Warning)
    case "completed":
      // For completed status, determine severity based on progress
      const progressValue = progress.value[testData.testId] || 0;
      if (progressValue >= 80) {
        return "success"; // Green for high progress
      } else if (progressValue >= 50) {
        return "warning"; // Yellow for medium progress
      } else {
        return "danger"; // Red for low progress
      }
    case "failed":
      return "danger"; // Red (PrimeVue Danger)
    case "error":
      return "danger"; // Red (PrimeVue Danger)
    case "idle":
      return "secondary"; // Gray (PrimeVue Secondary)
    default:
      return "info";
  }
};

// Function to get additional CSS class for status tag
const getStatusTagClass = (testData) => {
  const status = testData.status;
  switch (status.toLowerCase()) {
    case "running":
      return "status-running";
    case "executing":
      return "status-executing";
    case "completed":
      // Determine class based on actual progress
      const progressValue = progress.value[testData.testId] || 0;
      if (progressValue >= 80) {
        return "status-completed-high";
      } else if (progressValue >= 50) {
        return "status-completed-medium";
      } else {
        return "status-completed-low";
      }
    case "error":
    case "failed":
      return "status-error";
    default:
      return "";
  }
};

// Function to get failed conditions
const getFailedConditions = (testData) => {
  const failedConditions = [];

  if (!testData.result || !testData.result.data) {
    return failedConditions;
  }

  const testId = testData.testId;
  const data = testData.result.data;

  if (testId === "sim") {
    // Check conditions for SIM tests
    if (data.slot_1) {
      if (data.slot_1.active !== "yes")
        failedConditions.push("Slot 1: not active");
      if (data.slot_1.connected !== "connected")
        failedConditions.push("Slot 1: not connected");
      // if (data.slot_1.ping_result !== "succes")
      // failedConditions.push("Slot 1: ping failed");
      if (data.slot_1.rssi === "--")
        failedConditions.push("Slot 1: RSSI signal missing");
    }

    if (data.slot_2) {
      if (data.slot_2.active !== "yes")
        failedConditions.push("Slot 2: not active");
      if (data.slot_2.connected !== "connected")
        failedConditions.push("Slot 2: not connected");
      // if (data.slot_2.ping_result !== "succes")
      // failedConditions.push("Slot 2: ping failed");
      if (data.slot_2.rssi === "--")
        failedConditions.push("Slot 2: RSSI signal missing");
    }
  }

  if (testId === "ethernets") {
    // Check result property for Ethernet tests
    if (data.result === "fail") {
      failedConditions.push("One or more interfaces failed ping test");
    }
  }

  if (testId === "wifi") {
    // Check conditions for WiFi tests
    if (data.interfaces) {
      // If wifi uses interfaces structure similar to ethernets
      data.interfaces.forEach((iface, index) => {
        if (iface.ping_result !== "success") {
          failedConditions.push(`WiFi Interface ${index + 1}: ping failed`);
        }
      });
    } else if (data.connection_status) {
      // Alternative structure for wifi tests
      if (data.connection_status !== "connected")
        failedConditions.push("WiFi: not connected");
      if (data.signal_strength && data.signal_strength <= -70)
        failedConditions.push("WiFi: weak signal strength");
      if (data.ping_result !== "success")
        failedConditions.push("WiFi: ping failed");
    }
  }

  return failedConditions;
};

// Function to get progress value based on status and result
const getProgressValue = (testData) => {
  const status = testData.status;
  const testId = testData.testId;

  switch (status) {
    case "running":
    case "executing":
      return null; // For indeterminate mode
    case "completed":
      // Используем прогресс из backend
      return progress.value[testId] || 0;
    case "error":
    case "failed":
      return 0; // Zero progress for errors
    default:
      return 0;
  }
};

// Function to determine progress bar mode
const getProgressMode = (status) => {
  switch (status.toLowerCase()) {
    case "running":
    case "executing":
      return "indeterminate";
    default:
      return "determinate";
  }
};

// Function to get progress bar CSS class based on status and result
const getProgressBarClass = (testData) => {
  const status = testData.status;
  const testId = testData.testId;

  switch (status.toLowerCase()) {
    case "running":
      return "progress-running";
    case "executing":
      return "progress-executing";
    case "completed":
      // Determine color based on actual progress
      const progressValue = progress.value[testId] || 0;
      if (progressValue >= 80) {
        return "progress-completed-high"; // Green for high progress
      } else if (progressValue >= 50) {
        return "progress-completed-medium"; // Yellow for medium progress
      } else {
        return "progress-completed-low"; // Red for low progress
      }
    case "error":
    case "failed":
      return "progress-error";
    default:
      return "";
  }
};

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString || dateTimeString === "—") return "—";
  try {
    return new Date(dateTimeString).toLocaleString("ru-RU");
  } catch (e) {
    return dateTimeString; // Return original string if date is invalid
  }
};

// WiFi formatting functions
const formatWifiSpeed = (speed) => {
  if (!speed || speed === 0) return "—";
  if (speed >= 1000) {
    return `${(speed / 1000).toFixed(1)} Gbps`;
  }
  return `${speed} Mbps`;
};

const formatSignalStrength = (rssi) => {
  if (!rssi) return "—";
  return `${rssi} dBm`;
};

const getWifiConnectionStatus = (wifiData) => {
  if (!wifiData || !wifiData.result) return "Не подключен";
  
  const result = wifiData.result;
  if (result.connected === true) {
    return "Подключен";
  } else if (result.connected === false) {
    return "Не подключен";
  }
  return "Неизвестно";
};

const getWifiSSID = (wifiData) => {
  if (!wifiData || !wifiData.result || !wifiData.result.ssid) {
    return "—";
  }
  return wifiData.result.ssid;
};

const runSingleTest = () => {
  if (!testIdInput.value.trim()) {
    errorMessage.value = "Please enter test ID.";
    return;
  }
  errorMessage.value = "";
  console.log(`Running test with ID: ${testIdInput.value}`);

  const existingTest = tests.value.find((t) => t.id === testIdInput.value);
  if (existingTest) {
    existingTest.status = "running"; // Simulate start
    existingTest.updatedAt = new Date().toISOString();
    existingTest.result = "—";
  } else {
    // Add new test to the beginning of the list for visibility
    tests.value.unshift({
      id: testIdInput.value,
      status: "running", // Initial status when starting
      updatedAt: new Date().toISOString(),
      result: "—",
    });
  }
  // testIdInput.value = ''; // Clear input field after "start" (optional)
};

const showResultDialog = ref(false);
const selectedTestData = ref(null);

const openResultDialog = (testData) => {
  console.log("testData :");
  console.log(testData);
  selectedTestData.value = testData;
  showResultDialog.value = true;
};

// Функция для открытия диалога результатов по ID теста
const openResultDialogByTestId = (testId) => {
  const testData = dataStore.tests.find((test) => test.testId === testId);
  if (testData) {
    openResultDialog(testData);
  } else {
    console.warn(`Test with ID ${testId} not found`);
  }
};
</script>

<style scoped>
/* Используются PrimeFlex и глобальные стили Tailwind. */
/* Стили для <pre> для лучшего отображения JSON */

:deep(.p-datatable-sm .p-datatable-tbody > tr > td) {
  padding: 0.5rem;
}

:deep(.p-button-sm) {
  width: 2rem;
  height: 2rem;
}

pre {
  white-space: pre-wrap;
  word-break: break-all;
  background-color: var(--surface-b);
  /* Используем переменную темы PrimeVue для фона */
  color: var(--text-color);
  /* Используем переменную темы PrimeVue для текста */
  padding: 0.5rem;
  border-radius: var(--border-radius);
  /* Используем переменную темы PrimeVue для скругления */
  border: 1px solid var(--surface-d);
  /* Используем переменную темы PrimeVue для рамки */
  font-family: monospace;
}

/* Заголовки Tailwind применяются глобально */
/* PrimeFlex классы (p-4, mb-4, flex, flex-wrap, gap-3, align-items-end, flex-auto, w-full) используются для разметки */
/* DataTable стилизуется темой Lara */

/* Стили для компактного прогресс-бара */
.compact-progress {
  height: 0.5rem !important;
  margin-bottom: 0.5rem;
}

/* Скрываем текст процентов в прогресс-баре */
:deep(.compact-progress .p-progressbar-label) {
  display: none !important;
}

:deep(.compact-progress .p-progressbar-value) {
  font-size: 0 !important;
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.result-details {
  font-size: 0.875rem;
}

.interface-progress {
  margin-bottom: 0.5rem;
  padding: 0.25rem 0.5rem;
  background-color: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  border-radius: 0.25rem;
  font-size: 0.8rem;
}

.interface-progress strong {
  color: #0369a1;
}

.failed-conditions {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 0.25rem;
}

.failed-conditions ul {
  margin: 0.25rem 0 0 0;
  padding-left: 1rem;
  list-style-type: disc;
}

.failed-conditions li {
  margin: 0.125rem 0;
  font-size: 0.8rem;
  color: #dc2626;
}

.failed-conditions strong {
  color: #dc2626;
}

/* Цветовые схемы для прогресс-баров */
:deep(.progress-running .p-progressbar-value) {
  background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
}

:deep(.progress-executing .p-progressbar-value) {
  background: linear-gradient(90deg, #f59e0b, #fbbf24) !important;
}

:deep(.progress-completed-high .p-progressbar-value) {
  background: linear-gradient(90deg, #10b981, #34d399) !important;
}

:deep(.progress-completed-medium .p-progressbar-value) {
  background: linear-gradient(90deg, #f59e0b, #fbbf24) !important;
}

:deep(.progress-completed-low .p-progressbar-value) {
  background: linear-gradient(90deg, #ef4444, #f87171) !important;
}

:deep(.progress-error .p-progressbar-value) {
  background: linear-gradient(90deg, #ef4444, #f87171) !important;
}

/* Анимация для активных прогресс-баров */
:deep(.progress-running .p-progressbar-value),
:deep(.progress-executing .p-progressbar-value) {
  animation: progress-pulse 2s ease-in-out infinite;
}

@keyframes progress-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Дополнительные стили для тегов статуса */
:deep(.status-running) {
  background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
  border-color: #3b82f6 !important;
}

:deep(.status-executing) {
  background: linear-gradient(90deg, #f59e0b, #fbbf24) !important;
  border-color: #f59e0b !important;
}

:deep(.status-completed-high) {
  background: linear-gradient(90deg, #10b981, #34d399) !important;
  border-color: #10b981 !important;
}

:deep(.status-completed-medium) {
  background: linear-gradient(90deg, #f59e0b, #fbbf24) !important;
  border-color: #f59e0b !important;
}

:deep(.status-completed-low) {
  background: linear-gradient(90deg, #ef4444, #f87171) !important;
  border-color: #ef4444 !important;
}

:deep(.status-error) {
  background: linear-gradient(90deg, #ef4444, #f87171) !important;
  border-color: #ef4444 !important;
}

/* Адаптивные стили для контейнера таблицы */
.test-statuses-container {
  width: 100%;
  overflow-x: auto;
  padding: 0.5rem;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Современные стили для адаптивной таблицы */
:deep(.modern-responsive-table) {
  width: 100%;
}

/* Заголовки колонок */
:deep(.column-header) {
  font-weight: 600 !important;
  padding: 0.75rem !important;
}

/* Ячейки таблицы */
:deep(.p-datatable-tbody > tr > td) {
  padding: 0.75rem !important;
  vertical-align: middle !important;
}

/* Стили для ID теста */
.test-id-cell {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.test-id-badge {
  background: var(--primary-500, #3b82f6);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.875rem;
}

/* Стили для статуса */
.status-cell {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

:deep(.modern-tag) {
  border-radius: 4px !important;
  font-weight: 500 !important;
  font-size: 0.75rem !important;
  padding: 0.25rem 0.5rem !important;
}

/* Стили для времени */
.time-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-color-secondary, #6b7280);
}

/* Стили для действий */
.actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.modern-action-btn) {
  border-radius: 4px !important;
}

/* Mobile-first адаптивные breakpoints */
@media (max-width: 320px) {
  .p-4 {
    padding: 0.5rem !important;
  }

  :deep(.column-header) {
    padding: 0.5rem 0.25rem !important;
    font-size: 0.7rem !important;
  }

  :deep(.p-datatable-tbody > tr > td) {
    padding: 0.5rem 0.25rem !important;
  }

  .test-id-badge {
    padding: 0.25rem 0.5rem;
    font-size: 0.7rem;
  }

  .time-cell {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    font-size: 0.7rem;
  }
}

@media (max-width: 576px) {
  .p-4 {
    padding: 0.75rem !important;
  }

  :deep(.column-header) {
    padding: 0.75rem 0.5rem !important;
    font-size: 0.75rem !important;
  }

  :deep(.p-datatable-tbody > tr > td) {
    padding: 0.75rem 0.5rem !important;
  }

  .test-id-badge {
    font-size: 0.75rem;
  }

  .time-cell {
    font-size: 0.75rem;
  }

  .result-container {
    max-width: 100%;
  }

  .result-details {
    font-size: 0.7rem;
    margin-top: 0.5rem;
  }

  .failed-conditions {
    font-size: 0.7rem;
  }

  .failed-conditions li {
    font-size: 0.65rem;
    margin-bottom: 0.25rem;
  }
}

@media (max-width: 768px) {
  .p-4 {
    padding: 1rem !important;
  }

  /* Стековое отображение на мобильных */
  :deep(.p-datatable-responsive-stack .p-datatable-tbody > tr > td) {
    border: 0 none !important;
    width: 100% !important;
    display: block !important;
    border-bottom: 1px solid var(--surface-200, #e5e7eb) !important;
    padding: 0.75rem !important;
  }

  :deep(.p-datatable-responsive-stack .p-datatable-tbody > tr > td:before) {
    content: attr(data-label) ":" !important;
    font-weight: 600 !important;
    color: var(--text-color-secondary, #6b7280) !important;
    display: inline-block !important;
    width: 30% !important;
    margin-right: 1rem !important;
  }

  .result-container {
    margin-top: 0.5rem;
  }
}

@media (max-width: 992px) {
  :deep(.column-header) {
    padding: 0.875rem 0.625rem !important;
    font-size: 0.8rem !important;
  }

  :deep(.p-datatable-tbody > tr > td) {
    padding: 0.875rem 0.625rem !important;
  }

  .time-cell {
    font-size: 0.8rem;
  }
}

@media (max-width: 1200px) {
  .p-4 {
    padding: 1.25rem !important;
  }
}

/* Улучшения для больших экранов */
@media (min-width: 1400px) {
  .p-4 {
    padding: 2rem !important;
  }

  :deep(.column-header) {
    padding: 1.25rem 1rem !important;
    font-size: 0.9rem !important;
  }

  :deep(.p-datatable-tbody > tr > td) {
    padding: 1.25rem 1rem !important;
  }

  .test-id-badge {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }

  .time-cell {
    font-size: 0.9rem;
  }
}

/* Улучшения для прогресс-бара на мобильных */
@media (max-width: 768px) {
  :deep(.compact-progress) {
    height: 4px !important;
    margin-bottom: 4px !important;
  }
}

/* Стили для кнопок на мобильных */
@media (max-width: 576px) {
  :deep(.p-button-sm) {
    padding: 0.25rem;
    font-size: 0.7rem;
  }

  :deep(.p-button-rounded) {
    width: 1.5rem;
    height: 1.5rem;
  }
}

/* Стили для панели с деталями */
.details-panel {
  background-color: var(--surface-50, #f8fafc);
  border: 1px solid var(--surface-200, #e2e8f0);
  border-radius: 6px;
  padding: 1rem;
  margin: 0.5rem 0;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-item strong {
  color: var(--text-color, #1f2937);
  font-size: 0.875rem;
  font-weight: 600;
}

.detail-item span {
  color: var(--text-color-secondary, #6b7280);
  font-size: 0.875rem;
}

/* Адаптивные стили для панели деталей */
@media (max-width: 768px) {
  .details-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .details-panel {
    padding: 0.75rem;
  }

  .detail-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .detail-item strong {
    min-width: 100px;
  }
}

/* Стили для колонок времени */
.time-column {
  min-width: 150px;
  width: 150px;
}

.time-column .p-column-header-content {
  justify-content: center;
}

.table-controls {
  margin-bottom: 1rem;
  display: flex;
  justify-content: flex-end;
}

.details-toggle-btn {
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white;
  transition: all 0.3s ease;
}

.details-toggle-btn.expanded {
  background: var(--orange-500);
  border-color: var(--orange-500);
}

@media (max-width: 768px) {
  .time-column {
    min-width: 120px;
    width: 120px;
    font-size: 0.875rem;
  }

  .table-controls {
    justify-content: center;
  }
}

/* Test Results Summary Dialog Styles */
.results-summary-dialog {
  font-family: "Inter", sans-serif;
}

.results-summary-content {
  padding: 1rem 0;
}

.results-circles {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 2rem;
  flex-wrap: wrap;
  padding: 1rem 0;
}

.result-circle-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.result-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem auto;
  font-weight: bold;
  font-size: 1.5rem;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.result-circle.passed {
  background: linear-gradient(135deg, #10b981, #059669);
}

.result-circle.failed {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.result-circle.error {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.circle-count {
  font-size: 1.4rem;
  font-weight: 700;
}

.circle-label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  line-height: 1.2;
}

/* Стили для контейнера кнопок Details в диалоге результатов */

.test-summary {
  margin: 1rem 0;
  text-align: left;
  max-width: 300px;
}

.test-group {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
}

.test-group strong {
  color: #374151;
  display: block;
  margin-bottom: 0.25rem;
}

.test-names {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
  line-height: 1.3;
  max-width: 120px;
  word-wrap: break-word;
  margin-bottom: 0.5rem;
  text-align: center;
}

@media (max-width: 480px) {
  .results-circles {
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
  }

  .result-circle-container {
    min-width: auto;
    width: 100%;
    max-width: 200px;
  }

  .test-names {
    max-width: 200px;
  }

  .results-summary-dialog {
    width: 90vw !important;
  }
}

.overall-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  font-size: 0.95rem;
  color: #495057;
  border: 1px solid #e9ecef;
}

/* Стили для кнопок Details в таблице */
.details-btn-success {
  background: linear-gradient(135deg, #22c55e, #16a34a) !important;
  border-color: #16a34a !important;
  color: white !important;
}

.details-btn-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
  border-color: #dc2626 !important;
  color: white !important;
}

.details-btn-warning {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border-color: #d97706 !important;
  color: white !important;
}

.details-btn-info {
  background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
  border-color: #2563eb !important;
  color: white !important;
}

.details-btn-secondary {
  background: linear-gradient(135deg, #6b7280, #4b5563) !important;
  border-color: #4b5563 !important;
  color: white !important;
}
</style>
