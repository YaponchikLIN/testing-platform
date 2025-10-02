<template>
  <Dialog
    header="Select Device Type"
    :visible="visible"
    modal
    :closable="false"
    :style="{ width: '400px' }"
  >
    <div class="field centered-content-container">
      <Select
        v-model="dataStore.deviceType"
        editable
        :options="dataStore.deviceTypes"
        optionLabel="name"
      />
    </div>
    <template #footer>
      <div class="dialog-footer">
        <Button label="Back" severity="secondary" @click="goBack" />
        <Button
          label="Next"
          @click="confirmDeviceType"
          :disabled="!dataStore.deviceType"
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
const emit = defineEmits(["update:visible", "device-type-selected", "go-back"]);
const toast = useToast();

const confirmDeviceType = () => {
  if (dataStore.deviceType) {
    emit("device-type-selected", dataStore.deviceType);
    emit("update:visible", false);
  } else {
    toast.add({
      severity: "warn",
      summary: "Warning",
      detail: "Please select a device type.",
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
