import apiClient from './apiClient';

export async function getSNandMAC(order_uid) {
    if (!order_uid) throw new Error('Order is required');
    const response = await apiClient.get(`/1C/SNandMAC?order_uid=${order_uid}`);
    return response.data;
}

export async function getOrders(period) {
    if (!period) throw new Error('Period is required');

    const response = await apiClient.get(`/1C/orders?date_from=${period.dateFrom}&date_to=${period.dateTo}`);
    return response.data;
}


