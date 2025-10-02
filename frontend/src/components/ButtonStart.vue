<template>
  <div class="flex items-center gap-4">
    <Button
      style="width: 150px"
      @click="runTests"
      label="Run Tests"
      :loading="isLoading"
    />
    <div v-if="currentStep" class="text-sm text-gray-600">
      {{ currentStep }}
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { connectWebSocket } from "../services/websocket.service.js";
import { runTest } from "../api/tests";
import { installFirmware } from "../api/firmware";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
const isLoading = ref(false);
const currentStep = ref("");
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

const runTests = async () => {
  try {
    isLoading.value = true;
    currentStep.value = "Установка прошивки...";

    // Шаг 1: Установка прошивки
    console.log("Начинаем установку прошивки...");
    const firmwareResult = await installFirmware();
    console.log("Прошивка установлена успешно:", firmwareResult);

    currentStep.value = "Подготовка тестов...";

    // Шаг 2: Сбрасываем данные тестов перед новым запуском
    for (const test of dataStore.tests) {
      test.status = "idle";
      test.timeStart = "";
      test.updatedAt = "";
      test.timeEnd = "";
      test.result = null;
    }

    currentStep.value = "Установка WebSocket соединений...";

    // Шаг 3: Устанавливаем WebSocket соединения для всех тестов
    for (const test of dataStore.tests) {
      connectWebSocket(test, dataStore);
    }

    currentStep.value = "Запуск тестов...";

    // Шаг 4: Запускаем тесты через API
    const response = await runTest("all");

    console.log(
      "Тесты запущены, WebSocket соединения установлены для всех тестов"
    );
    console.log("Ответ от API:", response);

    currentStep.value = "";
  } catch (error) {
    console.error("Ошибка при выполнении процедуры запуска:", error);
    currentStep.value = `Ошибка: ${error.message}`;

    // Сбрасываем состояние через 3 секунды
    setTimeout(() => {
      currentStep.value = "";
    }, 3000);
  } finally {
    isLoading.value = false;
  }
};
</script>
