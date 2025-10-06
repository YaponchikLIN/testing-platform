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
import { useConfigStore } from '../stores/config.store';
import Button from 'primevue/button';
import Tooltip from 'primevue/tooltip';zz

const configStore = useConfigStore();

const toggleTheme = () => {
    configStore.toggleTheme();
};
</script>