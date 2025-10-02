<template>
  <div class="flex items-center gap-4">
    <Button
      style="width: 150px"
      @click="handleFetchSNandMAC"
      label="SN and MAC"
      :loading="loading"
    />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { connectWebSocket } from "../services/websocket.service.js";
import { useSNandMAC } from "@/composables/useSNandMAC.js";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();

const emit = defineEmits(["click"]);
const { loading, error, fetchSNandMAC } = useSNandMAC();

const fetchData = async (data) => {
  let tests = [];

  try {
    for (const item of data) {
      let test = {};
      test.testId = item.test_id;
      test.status = item.status;
      test.timeStart = item.time_start;
      test.updatedAt = item.updated_at;
      test.timeEnd = item.time_end;
      test.result = item.result;
      tests.push(test);
    }
  } catch (error) {
    console.error("Ошибка при получении данных:", error);
  }

  return tests;
};

const handleFetchSNandMAC = async () => {
  try {
    await fetchSNandMAC(dataStore.order.order_uid);
    emit("click", true);
    // for (const test of dataStore.tests) {
    //     if (test.status === 'running') {
    //         connectWebSocket(test, dataStore);
    //     }
    //     console.log('Тест запущен:', test);
    // }
  } catch (error) {
    // Ошибка уже обработана в композабле
  }
};
</script>
