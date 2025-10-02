<template>
  <div>
    <!-- <Card> -->
    <!-- <template #title>Period</template> -->
    <!-- <template #content> -->
    <strong style="font-size: 20px">Period</strong>
    <div class="grid">
      <div class="formgrid grid">
        <div class="col-12 md:col-6">
          <PeriodSelection />
        </div>
      </div>
    </div>
    <!-- </template> -->
    <!-- </Card> -->
  </div>
</template>

<script setup>
import PeriodSelection from "../components/PeriodSelection.vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
