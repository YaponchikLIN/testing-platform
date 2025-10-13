import { ref } from "vue";
import { defineStore } from "pinia";

export const useDataStore = defineStore('dataStore', (context) => {

    const tests = ref([
        {
            testId: 'ethernets',
            status: 'idle',
            timeStart: '',
            updatedAt: '',
            timeEnd: '',
            result: null
        },
        {
            testId: 'sim',
            status: 'idle',
            timeStart: '',
            updatedAt: '',
            timeEnd: '',
            result: null
        },
        {
            testId: 'wifi',
            status: 'completed',
            timeStart: '2024-01-15T10:30:00Z',
            updatedAt: '2024-01-15T10:35:00Z',
            timeEnd: '2024-01-15T10:35:00Z',
            result: {
                connected: true,
                ssid: 'TestNetwork_5G',
                downloadSpeed: 850,
                uploadSpeed: 420,
                signalStrength: -45,
                frequency: '5GHz',
                security: 'WPA3'
            }
        }
    ])

    const period = ref(null)
    const order = ref(null)
    const deviceType = ref(null)
    const SNandMAC = ref(null)
    const deviceData = ref(null)

    const orders = ref([])
    const deviceTypes = ref([
        { name: 'Router', code: 'router' },
        { name: 'Switch', code: 'switch' },
    ]);

    return {
        tests,
        period,
        order,
        deviceType,
        orders,
        deviceTypes,
        SNandMAC,
    }
})