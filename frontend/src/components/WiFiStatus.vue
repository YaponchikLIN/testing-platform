<template>
  <div class="wifi-status-container">
    <!-- WiFi Test Header -->
    <div class="test-header">
      <div class="test-title">
        <i class="pi pi-wifi" style="margin-right: 8px;"></i>
        <span>WiFi Test</span>
      </div>
      <div class="test-status-badge">
        <Badge 
          :value="wifiTest.status" 
          :severity="getStatusSeverity(wifiTest.status)"
          class="status-badge"
        />
      </div>
    </div>

    <!-- Progress Bar (показываем только если тест выполняется) -->
    <div v-if="wifiTest.status !== 'idle' && wifiTest.status !== 'error'" class="progress-container">
      <ProgressBar 
        :value="wifiTest.result?.progress || 0" 
        :showValue="true"
        class="test-progress"
      />
    </div>

    <!-- WiFi Connection Info -->
    <div v-if="wifiTest.result" class="wifi-info">
      <div class="info-grid">
        <!-- SSID -->
        <div class="info-item" v-if="wifiTest.result.ssid">
          <label>Network (SSID):</label>
          <span class="info-value">{{ wifiTest.result.ssid }}</span>
        </div>

        <!-- Connection Status -->
        <div class="info-item">
          <label>Connection:</label>
          <span 
            class="info-value connection-status"
            :class="getConnectionStatusClass(wifiTest.result.connection_status)"
          >
            {{ formatConnectionStatus(wifiTest.result.connection_status) }}
          </span>
        </div>

        <!-- Signal Strength -->
        <div class="info-item" v-if="wifiTest.result.signal_strength">
          <label>Signal Strength:</label>
          <span class="info-value">{{ wifiTest.result.signal_strength }}%</span>
        </div>

        <!-- IP Address -->
        <div class="info-item" v-if="wifiTest.result.ip_address">
          <label>IP Address:</label>
          <span class="info-value">{{ wifiTest.result.ip_address }}</span>
        </div>

        <!-- Download Speed -->
        <div class="info-item" v-if="wifiTest.result.download_speed_mbps > 0">
          <label>Download Speed:</label>
          <span class="info-value speed-value">
            {{ wifiTest.result.download_speed_mbps }} Mbps
          </span>
        </div>

        <!-- Upload Speed -->
        <div class="info-item" v-if="wifiTest.result.upload_speed_mbps > 0">
          <label>Upload Speed:</label>
          <span class="info-value speed-value">
            {{ wifiTest.result.upload_speed_mbps }} Mbps
          </span>
        </div>

        <!-- Gateway -->
        <div class="info-item" v-if="wifiTest.result.gateway">
          <label>Gateway:</label>
          <span class="info-value">{{ wifiTest.result.gateway }}</span>
        </div>

        <!-- DNS Servers -->
        <div class="info-item" v-if="wifiTest.result.dns_servers && wifiTest.result.dns_servers.length > 0">
          <label>DNS Servers:</label>
          <span class="info-value">{{ wifiTest.result.dns_servers.join(', ') }}</span>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="wifiTest.result?.error_message" class="error-container">
      <Message 
        severity="error" 
        :closable="false"
        class="error-message"
      >
        {{ wifiTest.result.error_message }}
      </Message>
    </div>

    <!-- Test Details -->
    <div v-if="wifiTest.result?.details" class="details-container">
      <div class="details-header">
        <span>Test Details:</span>
      </div>
      <div class="details-content">
        {{ wifiTest.result.details }}
      </div>
    </div>

    <!-- Execution Time -->
    <div v-if="wifiTest.result?.execution_time" class="execution-time">
      <small>Execution Time: {{ wifiTest.result.execution_time }}</small>
    </div>

    <!-- Test Actions -->
    <div class="test-actions">
      <Button 
        label="Details" 
        icon="pi pi-info-circle"
        class="p-button-outlined p-button-sm"
        @click="showDetails"
        :disabled="!wifiTest.result"
      />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useDataStore } from '@/stores/data.store'
import Badge from 'primevue/badge'
import ProgressBar from 'primevue/progressbar'
import Message from 'primevue/message'
import Button from 'primevue/button'

export default {
  name: 'WiFiStatus',
  components: {
    Badge,
    ProgressBar,
    Message,
    Button
  },
  emits: ['show-details'],
  setup(props, { emit }) {
    const dataStore = useDataStore()

    const wifiTest = computed(() => dataStore.tests.wifi)

    const getStatusSeverity = (status) => {
      switch (status) {
        case 'PASS':
          return 'success'
        case 'FAIL':
          return 'danger'
        case 'running':
          return 'info'
        case 'idle':
          return 'secondary'
        default:
          return 'warning'
      }
    }

    const getConnectionStatusClass = (status) => {
      switch (status) {
        case 'success':
        case 'connected':
          return 'status-success'
        case 'fail':
        case 'disconnected':
          return 'status-error'
        default:
          return 'status-warning'
      }
    }

    const formatConnectionStatus = (status) => {
      switch (status) {
        case 'success':
          return 'Connected'
        case 'fail':
          return 'Failed'
        case 'connected':
          return 'Connected'
        case 'disconnected':
          return 'Disconnected'
        default:
          return status || 'Unknown'
      }
    }

    const showDetails = () => {
      emit('show-details', {
        testId: 'wifi',
        testType: 'WiFi',
        result: wifiTest.value.result,
        status: wifiTest.value.status,
        timeStart: wifiTest.value.timeStart,
        timeEnd: wifiTest.value.timeEnd
      })
    }

    return {
      wifiTest,
      getStatusSeverity,
      getConnectionStatusClass,
      formatConnectionStatus,
      showDetails
    }
  }
}
</script>

<style scoped>
.wifi-status-container {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.test-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.test-title .pi-wifi {
  color: #2196F3;
}

.status-badge {
  font-size: 12px;
}

.progress-container {
  margin-bottom: 16px;
}

.test-progress {
  height: 8px;
}

.wifi-info {
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

.info-item label {
  font-weight: 500;
  color: #666;
  margin-right: 8px;
}

.info-value {
  font-weight: 600;
  color: #333;
}

.connection-status.status-success {
  color: #4CAF50;
}

.connection-status.status-error {
  color: #f44336;
}

.connection-status.status-warning {
  color: #ff9800;
}

.speed-value {
  color: #2196F3;
  font-family: 'Courier New', monospace;
}

.error-container {
  margin-bottom: 16px;
}

.error-message {
  margin: 0;
}

.details-container {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

.details-header {
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.details-content {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.execution-time {
  margin-bottom: 16px;
  text-align: right;
  color: #666;
}

.test-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Responsive design */
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .test-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>