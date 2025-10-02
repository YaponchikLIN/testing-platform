<template>
    <div class="card">
        <h3>Firmware Files</h3>
        <div v-if="files.length">
            <DataTable
                :value="files"
                selectionMode="single"
                v-model:selection="selectedFile"
                dataKey="name"
            >
                <Column
                    field="name"
                    header="File Name"
                ></Column>
                <Column
                    field="size"
                    header="Size"
                ></Column>
            </DataTable>
        </div>
        <div v-else>
            <p>No files in the specified folder</p>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useConfigStore } from '../stores/config.store';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

const configStore = useConfigStore();
const files = ref([]);
const selectedFile = ref(null);

watch(() => configStore.lastUsedDeviceType, async (deviceType) => {
    if (deviceType && configStore.devicePaths[deviceType]) {
        // Here will be logic for reading files from folder via NW.js API
    }
}, { immediate: true });
</script>