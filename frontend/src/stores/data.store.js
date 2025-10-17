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
            status: 'idle',
            timeStart: '',
            updatedAt: '',
            timeEnd: '',
            result: {
                connected: null,
                ssid: '',
                downloadSpeed: null,
                uploadSpeed: null,
                signalStrength: null,
                frequency: '',
                security: ''
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