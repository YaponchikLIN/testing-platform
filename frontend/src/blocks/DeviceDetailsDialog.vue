<template>
    <Dialog
        header="Serial Numbers and MAC Addresses"
        :visible="visible"
        modal
        :style="{ width: '600px' }"
        @update:visible="$emit('update:visible', $event)"
    >
        <DataTable
            :value="devices"
            responsiveLayout="scroll"
            v-if="devices && devices.length > 0"
        >
            <Column
                field="sn"
                header="Serial Number (90)"
            ></Column>
            <Column
                field="mac"
                header="MAC Address (120)"
            ></Column>
        </DataTable>
        <p v-else>No device data available.</p>
        <template #footer>
            <Button
                label="Close"
                icon="pi pi-times"
                @click="closeDialog"
            />
        </template>
    </Dialog>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
    visible: Boolean,
    devices: Array, // Expecting array of objects { sn: '...', mac: '...' }
});
const emit = defineEmits(['update:visible']);

const closeDialog = () => {
    emit('update:visible', false);
};
</script>