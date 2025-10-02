<template>
  <div class="card flex justify-center">
    <DatePicker
      v-model="dataStore.period"
      selectionMode="range"
      :manualInput="false"
      placeholder="Select Period"
      style="width: 100%"
    />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
