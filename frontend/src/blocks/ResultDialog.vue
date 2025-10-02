<template>
  <Dialog
    header="Test Result"
    :visible="visible"
    modal
    :style="{ width: '500px', maxHeight: '70vh' }"
    @update:visible="closeDialog"
  >
    <div class="test-result-container">
      <!-- Result Circle Section -->
      <div class="result-circle-section">
        <div class="result-circle" :class="getResultClass()">
          <i :class="getResultIcon()" style="font-size: 2rem;"></i>
        </div>
        <div class="result-text">{{ getResultText() }}</div>
      </div>

      <!-- Test Information Section -->
      <div class="info-section">
        <h4 class="section-title">Test Information</h4>
        <div class="info-grid">
          <div class="info-item">
            <strong>Test ID:</strong> {{ props.testData?.testId || "N/A" }}
          </div>
          <div class="info-item">
            <strong>Status:</strong>
            <span class="status-text">
              {{ getStatusText(props.testData?.status) }}
            </span>
          </div>
          <div class="info-item" v-if="props.testData?.result?.details">
            <strong>Details:</strong> {{ props.testData.result.details }}
          </div>
          <div class="info-item" v-if="props.testData?.result?.execution_time">
            <strong>Execution Time:</strong> {{ props.testData.result.execution_time }}
          </div>
          <div class="info-item" v-if="props.testData?.result?.completed_interfaces !== undefined && props.testData?.result?.total_interfaces !== undefined">
            <strong>Progress:</strong> {{ props.testData.result.completed_interfaces }}/{{ props.testData.result.total_interfaces }} interfaces
          </div>
          <div class="info-item" v-if="props.testData?.result?.progress !== undefined">
            <strong>Progress:</strong> {{ props.testData.result.progress }}%
          </div>
          <div class="info-item" v-if="props.testData?.result?.timestamp">
            <strong>Timestamp:</strong> {{ formatDateTime(props.testData.result.timestamp) }}
          </div>
        </div>
      </div>

      <!-- Failed Conditions Section -->
      <div class="info-section" v-if="failedConditions.length > 0">
        <h4 class="section-title">Failed Conditions</h4>
        <div class="failed-conditions-list">
          <div
            v-for="condition in failedConditions"
            :key="condition"
            class="failed-condition-item"
          >
            <i class="pi pi-times-circle"></i>
            {{ condition }}
          </div>
        </div>
      </div>

      <!-- JSON Data Section -->
      <div class="info-section">
        <h4 class="section-title">Raw JSON Data</h4>
        <div class="json-container">
          <VueJsonPretty
            :data="props.testData?.result"
            :showLine="true"
            theme="dark"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        label="Download JSON"
        icon="pi pi-download"
        class="p-button-outlined"
        @click="downloadJson"
        :disabled="!props.testData?.result"
      />
      <Button
        label="Close"
        icon="pi pi-times"
        class="p-button-text"
        @click="closeDialog"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { computed, defineProps, defineEmits } from "vue";
import VueJsonPretty from "vue-json-pretty";
import "vue-json-pretty/lib/styles.css";
import Tag from "primevue/tag";

const props = defineProps({
  visible: Boolean,
  testData: Object, // Complete test data object
});

const emit = defineEmits(["update:visible"]);

// Format date and time for display
const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return "N/A";
  
  try {
    const date = new Date(dateTimeString);
    return date.toLocaleString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    return dateTimeString; // Return original string if parsing fails
  }
};

// Get status text for display
const getStatusText = (status) => {
  if (!status) return "Unknown";

  switch (status.toLowerCase()) {
    case "completed":
      return "Test Completed";
    case "failed":
      return "Test Failed";
    case "error":
      return "Execution Error";
    case "running":
      return "Running";
    case "executing":
      return "Executing";
    case "idle":
      return "Idle";
    default:
      return status;
  }
};

// Get status severity for Tag component
const getStatusSeverity = (status) => {
  if (!status) return "info";

  switch (status.toLowerCase()) {
    case "completed":
      return "success";
    case "failed":
    case "error":
      return "danger";
    case "running":
    case "executing":
      return "warning";
    case "idle":
      return "secondary";
    default:
      return "info";
  }
};

// Get overall test result
const getOverallResult = () => {
  if (!props.testData || !props.testData.result || !props.testData.result.data) {
    return 'unknown';
  }

  const testId = props.testData.testId;
  const data = props.testData.result.data;
  let hasFailures = false;

  if (testId === "sim") {
    // Check result property for SIM tests
    if (data.slot_1 && data.slot_1.result === "fail") {
      hasFailures = true;
    }
    if (data.slot_2 && data.slot_2.result === "fail") {
      hasFailures = true;
    }
  }

  if (testId === "ethernets") {
    // Check result property for Ethernet tests
    if (data.result === "fail") {
      hasFailures = true;
    }
  }

  if (testId === "wifi") {
    // Check conditions for WiFi tests
    if (data.interfaces) {
      data.interfaces.forEach((iface) => {
        if (iface.ping_result !== "success") {
          hasFailures = true;
        }
      });
    } else if (data.connection_status) {
      if (data.connection_status !== "connected" || 
          (data.signal_strength && data.signal_strength <= -70) || 
          data.ping_result !== "success") {
        hasFailures = true;
      }
    }
  }

  return hasFailures ? 'fail' : 'success';
};

// Get result class for styling
const getResultClass = () => {
  const result = getOverallResult();
  return {
    'result-success': result === 'success',
    'result-fail': result === 'fail',
    'result-unknown': result === 'unknown'
  };
};

// Get result icon
const getResultIcon = () => {
  const result = getOverallResult();
  switch (result) {
    case 'success':
      return 'pi pi-check';
    case 'fail':
      return 'pi pi-times';
    default:
      return 'pi pi-question';
  }
};

// Get result text
const getResultText = () => {
  const result = getOverallResult();
  switch (result) {
    case 'success':
      return 'SUCCESS';
    case 'fail':
      return 'FAIL';
    default:
      return 'UNKNOWN';
  }
};

// Get failed conditions from test data
const failedConditions = computed(() => {
  if (
    !props.testData ||
    !props.testData.result ||
    !props.testData.result.data
  ) {
    return [];
  }

  const failedConditions = [];
  const testId = props.testData.testId;
  const data = props.testData.result.data;

  if (testId === "sim") {
    // Check conditions for SIM tests
    if (data.slot_1) {
      if (data.slot_1.active !== "yes")
        failedConditions.push("Slot 1: not active");
      if (data.slot_1.connected !== "connected")
        failedConditions.push("Slot 1: not connected");
      if (data.slot_1.ping_result !== "success")
        failedConditions.push("Slot 1: ping failed");
      if (data.slot_1.rssi === "--")
        failedConditions.push("Slot 1: RSSI signal missing");
    }

    if (data.slot_2) {
      if (data.slot_2.active !== "yes")
        failedConditions.push("Slot 2: not active");
      if (data.slot_2.connected !== "connected")
        failedConditions.push("Slot 2: not connected");
      if (data.slot_2.ping_result !== "success")
        failedConditions.push("Slot 2: ping failed");
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
});

const closeDialog = () => {
  emit("update:visible", false);
};

const downloadJson = () => {
  if (!props.testData?.result) return;

  const jsonString = JSON.stringify(props.testData.result, null, 2);
  const blob = new Blob([jsonString], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `test-result-${
    props.testData.testId || "unknown"
  }-${Date.now()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.test-result-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.result-circle-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin-bottom: 30px;
}

.result-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 4px solid;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.result-circle.result-success {
  background-color: #e8f5e8;
  border-color: #4caf50;
  color: #4caf50;
}

.result-circle.result-fail {
  background-color: #ffeaea;
  border-color: #f44336;
  color: #f44336;
}

.result-circle.result-unknown {
  background-color: #fff3e0;
  border-color: #ff9800;
  color: #ff9800;
}

.result-text {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
}

.result-circle-section .result-text {
  color: inherit;
}

.result-circle.result-success + .result-text {
  color: #4caf50;
}

.result-circle.result-fail + .result-text {
  color: #f44336;
}

.result-circle.result-unknown + .result-text {
  color: #ff9800;
}

.info-section {
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1rem;
  background-color: var(--surface-ground);
}

.section-title {
  margin: 0 0 1rem 0;
  color: var(--primary-color);
  font-size: 1.1rem;
  font-weight: 600;
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background-color: var(--surface-card);
  border-radius: 4px;
  border-left: 3px solid var(--primary-color);
}

.info-item strong {
  min-width: 80px;
  color: var(--text-color-secondary);
}

.status-text {
  font-weight: 500;
}

.failed-conditions-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.failed-condition-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-weight: 500;
}

.failed-condition-item i {
  color: #dc2626;
  font-size: 1rem;
}

.json-container {
  max-height: 40vh;
  overflow-y: auto;
  border-radius: 6px;
  padding: 1rem;
  background-color: var(--surface-section);
  border: 1px solid var(--surface-border);
}

/* Dark theme adjustments */
:global(.p-dark) .failed-condition-item {
  background-color: #450a0a;
  border-color: #7f1d1d;
  color: #fca5a5;
}

:global(.p-dark) .failed-condition-item i {
  color: #fca5a5;
}

/* Fix z-index for dialog overlay */
:deep(.p-dialog-mask) {
  z-index: 1100 !important;
}

:deep(.p-dialog) {
  z-index: 1101 !important;
}

/* Responsive design */
@media (max-width: 768px) {
  .test-details-container {
    gap: 1rem;
  }

  .info-section {
    padding: 0.75rem;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .info-item strong {
    min-width: auto;
  }
}
</style>
