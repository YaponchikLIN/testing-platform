<template>
  <Dialog
    header="SN and MAC"
    :visible="visible"
    modal
    ref="dt"
    :style="{ width: '800px' }"
    @update:visible="$emit('update:visible', $event)"
  >
    <div style="display: flex; justify-content: flex-end">
      <Button
        style="margin-bottom: 10px"
        label="Export"
        @click="exportCSV($event)"
      />
    </div>
    <DataTable
      ref="dt"
      :value="groupedTableData"
      class="p-datatable-sm"
      :rowHover="true"
      :showGridlines="true"
      scrollable
      scrollHeight="400px"
      :virtualScrollerOptions="{ itemSize: 35 }"
    >
      <Column field="type" style="display: none"></Column>
      <Column header="Device Name" style="width: 30%">
        <template #body="{ data }">
          <div v-if="data.type === 'header'" class="device-header">
            <strong>{{ data.deviceName }}</strong>
          </div>
          <div v-else class="device-data">
            <!-- Пустое место для выравнивания -->
          </div>
        </template>
      </Column>
      <Column header="SN" style="width: 35%">
        <template #body="{ data }">
          <span v-if="data.type === 'data'">{{ data.serial_number }}</span>
        </template>
      </Column>
      <Column header="MAC" style="width: 35%">
        <template #body="{ data }">
          <span v-if="data.type === 'data'">{{ data.mac_address }}</span>
        </template>
      </Column>
    </DataTable>
  </Dialog>
</template>

<script setup>
import { computed, ref } from "vue";
import { useToast } from "primevue/usetoast";
import { useDataStore } from "@/stores/data.store";
import Dialog from "primevue/dialog";
import DataTable from "primevue/datatable";
import Column from "primevue/column";

const dataStore = useDataStore();
const toast = useToast();

const props = defineProps({
  visible: Boolean,
});
const emit = defineEmits(["update:visible"]);

// Группированные данные с заголовками
const groupedTableData = computed(() => {
  const result = [];
  const deviceGroups = new Map();

  // Группируем данные по устройствам
  dataStore.SNandMAC.forEach((device) => {
    const deviceData = device.data.flatMap((item) =>
      item.mac_address.map((macAddress) => ({
        deviceName: device.deviceName,
        serial_number: item.serial_number,
        mac_address: macAddress,
        test_status: item.test_status,
        type: "data",
      }))
    );
    deviceGroups.set(device.deviceName, deviceData);
  });

  // Создаем плоский массив с заголовками
  deviceGroups.forEach((data, deviceName) => {
    // Добавляем заголовок устройства
    result.push({
      type: "header",
      deviceName: deviceName,
      serial_number: "",
      mac_address: "",
    });

    // Добавляем данные устройства
    data.sort((a, b) => {
      const snCompare = a.serial_number.localeCompare(b.serial_number);
      if (snCompare !== 0) return snCompare;
      return a.mac_address.localeCompare(b.mac_address);
    });

    result.push(...data);
  });

  return result;
});

const dt = ref();

const exportCSV = () => {
  // Для экспорта создаем данные без заголовков
  const exportData = groupedTableData.value
    .filter((item) => item.type === "data")
    .map((item) => ({
      "Device Name": item.deviceName,
      SN: item.serial_number,
      MAC: item.mac_address,
    }));

  // Создаем временную таблицу для экспорта
  const csvContent = [
    ["Device Name", "SN", "MAC"],
    ...exportData.map((row) => [row["Device Name"], row["SN"], row["MAC"]]),
  ]
    .map((row) => row.join(","))
    .join("\n");

  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sn-mac-data.csv";
  a.click();
  window.URL.revokeObjectURL(url);
};
</script>

<style scoped>
.device-header {
  background-color: #f3f4f6;
  padding: 8px;
  border-radius: 4px;
  font-weight: bold;
  color: var(--p-button-primary-background);
}

.device-data {
  padding-left: 16px;
}

.p-datatable .p-datatable-thead > tr > th {
  background-color: #1e3a8a;
  color: white;
  font-weight: bold;
}

.p-datatable .p-datatable-tbody > tr:nth-child(even) {
  background-color: #f9fafb;
}

.p-datatable .p-datatable-tbody > tr:hover {
  background-color: #e5e7eb;
}
</style>
