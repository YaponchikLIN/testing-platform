<template>
    <div>
        <Card class="mt-6">
            <template #title>Test Statuses</template>
            <template #content>
                <DataTable
                    :value="results"
                    responsiveLayout="scroll"
                    stripedRows
                    v-if="results && results.length > 0"
                >
                    <Column
                        field="id"
                        header="Test ID"
                        :sortable="true"
                    ></Column>
                    <Column
                        field="status"
                        header="Status"
                        :sortable="true"
                    >
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.status"
                                :severity="getStatusSeverity(slotProps.data.status)"
                            />
                        </template>
                    </Column>
                    <Column
                        field="updatedAt"
                        header="Update Time"
                        :sortable="true"
                    >
                        <template #body="slotProps">
                            {{ formatDateTime(slotProps.data.updatedAt) }}
                        </template>
                    </Column>
                    <Column
                        field="results"
                        header="Results"
                    >
                        <template #body="slotProps">
                            <div v-if="slotProps.data.results && typeof slotProps.data.results === 'object'">
                                <div><strong>Status:</strong> {{ slotProps.data.results.passed ? 'Success' : 'Failed'
                }}</div>                }}
                                </div>
                                <div v-if="slotProps.data.results.details"><strong>Details:</strong> {{
                    slotProps.data.results.details
                }}</div>
                            </div>
                            <span v-else>{{ slotProps.data.results || '—' }}</span>
                        </template>
                    </Column>
                    <Column
                        field="results"
                        header="Results"
                    >
                        <template #body="slotProps">
                            <div v-if="slotProps.data.results && typeof slotProps.data.results === 'object'">
                                <div><strong>Status:</strong> {{ slotProps.data.results.passed ? 'Success' : 'Failed'
                }}</div>                }}
                                </div>
                                <div v-if="slotProps.data.results.details"><strong>Details:</strong> {{
                    slotProps.data.results.details
                }}</div>
                            </div>
                            <span v-else>{{ slotProps.data.results || '—' }}</span>
                        </template>
                    </Column>
                    <Column header="Results">
                        <template #body="slotProps">
                            <Button
                                icon="pi pi-eye"
                                :class="['compact-button', { 'has-data': slotProps.data.results.data }]"
                                @click="openResultsDialog(slotProps.data)"
                                v-tooltip.top="'View test results'"
                            />
                        </template>
                    </Column>
                </DataTable>
                <p v-else>No test data to display.</p>
            </template>
        </Card>
        <ResultsDialog
            :visible="showResultsDialog"
            :json-data="currentResults"
            title="Test Results"
        />
    </div>
</template>

<script setup>
import { defineProps } from 'vue';
import Tag from 'primevue/tag'; // Локальный импорт, если не зарегистрирован глобально
import ResultsDialog from './ResultDialog.vue';

const props = defineProps({
    results: Array, // Expecting array of test objects
});

const getStatusSeverity = (status) => {
    if (!status) return 'info';
    switch (status.toLowerCase()) {
        case 'running': return 'info';
        case 'executing': return 'warning';
        case 'completed': return 'success';
        case 'failed': return 'danger';
        case 'error': return 'danger';
        case 'idle': return 'secondary';
        default: return 'info';
    }
};

const formatDateTime = (dateTimeString) => {
    if (!dateTimeString || dateTimeString === '—') return '—';
    try {
        return new Date(dateTimeString).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'medium' });
    } catch (e) {
        return dateTimeString;
    }
};

// States for dialog management
const showResultsDialog = ref(false);
const currentResults = ref(null);
// Function to open results dialog
const openResultsDialog = (rowData) => {
    currentResults.value = rowData.results.data;
    showResultsDialog.value = true;
};
</script>
<style scoped>
/* In global styles or component styles */
.compact-button {
    padding: 0.25rem !important;
    width: 1.5rem !important;
    height: 1.5rem !important;

}

.has-data {
    color: var(--primary-color) !important;
}
</style>