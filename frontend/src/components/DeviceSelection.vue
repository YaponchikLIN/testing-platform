<template>
  <div class="card flex justify-center">
    <Select
      v-model="dataStore.deviceType"
      editable
      :options="dataStore.deviceTypes"
      optionLabel="name"
      placeholder="Select type"
      class="w-full md:w-56"
      style="width: 100%"
    />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
