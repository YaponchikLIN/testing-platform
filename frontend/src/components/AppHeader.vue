<template>
    <header class="flex justify-between items-center p-4 border-b">
        <h1 class="text-xl font-bold">Startup Utility</h1>
        <div class="flex items-center gap-4">
            <Button
                @click="toggleTheme"
                icon="pi pi-moon"
                class="p-button-rounded p-button-text"
                v-tooltip="'Switch theme'"
            />
        </div>
    </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useConfigStore } from '../stores/config.store';
import Button from 'primevue/button';
import Tooltip from 'primevue/tooltip';
import {
  connectWebSocket,
  connectGpioWebSocket,
  disconnectGpioWebSocket,
} from "../services/websocket.service.js";

const configStore = useConfigStore();

const toggleTheme = () => {
    configStore.toggleTheme();
};

const gpioValue = ref(null);

const handleGpioChange = (value) => {
  gpioValue.value = value;
  if (gpioValue.value === "1" && !statusRunFullCycle.value) {
    runFullCycle();
  }
};

onMounted(() => {
  connectGpioWebSocket(handleGpioChange);
});

onUnmounted(() => {
  disconnectGpioWebSocket();
});
</script>