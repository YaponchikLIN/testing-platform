export class ApiService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async fetchDevices() {
        // Test device data
        const testDevices = [
            { id: 1, name: 'Device 1', status: 'active' },
    { id: 2, name: 'Device 2', status: 'inactive' },
    { id: 3, name: 'Device 3', status: 'active' }
        ];
        return testDevices;
    }

    async fetchOrders() {
        // Test order data
        const testOrders = [
            { id: 1, deviceId: 1, date: '2023-01-01', status: 'completed' },
            { id: 2, deviceId: 2, date: '2023-01-02', status: 'pending' },
            { id: 3, deviceId: 3, date: '2023-01-03', status: 'processing' }
        ];
        return testOrders;
    }

    async startUpdate(payload) {
        const response = await fetch(`${this.baseUrl}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    }
}

export const apiService = new ApiService('http://your-1c-api-url');