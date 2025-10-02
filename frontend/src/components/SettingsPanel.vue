<template>
    <div class="card">
        <h3>Settings</h3>
        <div
            v-for="(path, deviceType) in configStore.devicePaths"
            :key="deviceType"
            class="mb-4"
        >
            <label :for="`path-${deviceType}`">{{ deviceType }}</label>
            <InputText
                :id="`path-${deviceType}`"
                v-model="configStore.devicePaths[deviceType]"
                class="w-full"
            />
            <Button
                label="Check"
                @click="testPath(deviceType)"
                class="p-button-sm"
            />
        </div>
    </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.store';
import Button from 'primevue/button';

const configStore = useConfigStore();

const testPath = (deviceType) => {
    const path = configStore.devicePaths[deviceType];
    // Here will be folder existence check via NW.js API
    alert(`Path check for ${deviceType}: ${path}`);
};
</script>