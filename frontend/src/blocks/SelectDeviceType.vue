<template>
  <div>
    <strong style="font-size: 20px">Device Type</strong>
    <div class="grid">
      <div class="formgrid grid">
        <div class="col-12 md:col-6">
          <DeviceSelection />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import DeviceSelection from "../components/DeviceSelection.vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
