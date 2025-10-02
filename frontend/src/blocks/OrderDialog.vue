<template>
  <Dialog
    header="Select Order"
    :visible="visible"
    modal
    :closable="false"
    :style="{ width: '500px' }"
  >
    <div class="field centered-content-container">
      <Select
        v-model="dataStore.order"
        editable
        :options="dataStore.orders"
        optionLabel="name"
      />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <Button label="Back" severity="secondary" @click="goBack" />
        <Button
          label="Next"
          @click="confirmOrder"
          :disabled="!dataStore.order"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch } from "vue";
import { useToast } from "primevue/usetoast";
import { useDataStore } from "@/stores/data.store";

const dataStore = useDataStore();

const props = defineProps({
  visible: Boolean,
  orders: Array,
});
const emit = defineEmits(["update:visible", "order-selected", "go-back"]);
const toast = useToast();

const confirmOrder = () => {
  if (dataStore.order) {
    emit("order-selected", dataStore.order);
    emit("update:visible", false);
  } else {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: "Please select a Order",
    });
  }
};

const goBack = () => {
  emit("go-back");
  emit("update:visible", false);
};
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.footer-button {
  flex: 1;
}

.centered-content-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
