<template>
  <Dialog
    header="Select Period"
    :visible="visible"
    modal
    :closable="false"
    :style="{ width: '500px' }"
  >
    <div class="field centered-content-container">
      <DatePicker
        v-model="dataStore.period"
        selectionMode="range"
        :manualInput="false"
      />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <Button
          label="Next"
          @click="confirmPeriod"
          :disabled="!dataStore.period"
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
});

const emit = defineEmits(["update:visible", "period-selected", "go-back"]);
const toast = useToast();

const confirmPeriod = () => {
  if (dataStore.period) {
    emit("period-selected", dataStore.period);
    emit("update:visible", false);
  } else {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: "Please select a period",
      life: 3000,
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
