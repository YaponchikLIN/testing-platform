<template>
  <div>
    <strong style="font-size: 20px">Order</strong>
    <div class="grid">
      <div class="formgrid grid">
        <div class="col-12 md:col-6">
          <OrderSelection />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import OrderSelection from "../components/OrderSelection.vue";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();
</script>
