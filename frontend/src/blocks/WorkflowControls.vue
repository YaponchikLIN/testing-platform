<!-- WorkflowControls.vue -->
<template>
  <div class="selection-container-wrapper">
    <div
      :class="
        props.useSelectionContainerClass
          ? 'selection-container'
          : 'fields-container'
      "
    >
      <SelectPeriod
        v-if="selectedPeriod"
        :class="
          props.useSelectionContainerClass ? 'selection-item' : 'field-item'
        "
      />
      <SelectOrder
        v-if="selectedOrder"
        :class="
          props.useSelectionContainerClass ? 'selection-item' : 'field-item'
        "
      />
      <SelectDeviceType
        v-if="selectedDeviceType"
        :class="
          props.useSelectionContainerClass ? 'selection-item' : 'field-item'
        "
      />
    </div>
    <div
      v-if="selectedOrder && selectedDeviceType"
      class="buttons-container centered"
      style="margin-top: 20px"
    >
      <ButtonSNandMAC
        @click="emit('show-sn-mac-dialog', $event)"
        class="action-button"
      />
      <ButtonFullCycle class="action-button" />
      <!-- <ButtonStart class="action-button" /> -->
    </div>
  </div>
</template>

<script setup>
import SelectPeriod from "./SelectPeriod.vue";
import SelectOrder from "./SelectOrder.vue";
import SelectDeviceType from "./SelectDeviceType.vue";
import ButtonSNandMAC from "../components/ButtonSNandMAC.vue";
import ButtonFullCycle from "../components/ButtonFullCycle.vue";
import ButtonStart from "../components/ButtonStart.vue";

const props = defineProps({
  selectedPeriod: Object,
  selectedOrder: Object,
  selectedDeviceType: Object,
  useSelectionContainerClass: Boolean, // Флаг для выбора класса контейнера
});

const emit = defineEmits(["show-sn-mac-dialog"]);
</script>

<style scoped>
.selection-container-wrapper {
  /* Стили для общего оберточного контейнера, если нужны */
}
/* Сюда можно перенести общие стили для .fields-container, .selection-container, .buttons-container.centered, .action-button, .field-item, .selection-item, если они не зависят от родителя в Workflow.vue */
.fields-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex: 1;
}

.field-item {
  width: 100%;
}

.selection-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
  align-items: start;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.selection-item {
  width: 100%;
  max-width: 200px;
}

.buttons-container.centered {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0;
}

.action-button {
  /* width: 100%; */
  max-width: 200px; /* Убедимся, что это соответствует желанию */
  height: 40px;
}
</style>
