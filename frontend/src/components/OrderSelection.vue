<template>
  <div class="card flex justify-center">
    <Select
      v-model="dataStore.order"
      editable
      :options="dataStore.orders"
      optionLabel="name"
      placeholder="Select Order"
      style="width: 100%"
    />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
