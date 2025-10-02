<template>
    <Card>
        <template #title>Select Firmware</template>
        <template #content>
            <div class="grid">
                <div
                    class="formgrid grid"
                    @click="handleClickOutside"
                >

                    <div class="md:col-span-1">
                        <FirmwareManager />
                    </div>
                </div>
            </div>
        </template>
    </Card>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useConfigStore } from '../stores/config.store';
import AppHeader from '../components/AppHeader.vue';
import OrderSelection from '../components/OrderSelection.vue';
import DeviceSelection from '../components/DeviceSelection.vue';
import FirmwareManager from '../components/FirmwareManager.vue';
import SettingsPanel from '../components/SettingsPanel.vue';

const configStore = useConfigStore();

</script>