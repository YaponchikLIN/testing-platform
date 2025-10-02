import apiClient from './apiClient';

export async function patchOneDevice(deviceArray) {
    if (deviceArray.length == 0) throw new Error('All data is required');

    const response = await apiClient.patch(`/1C/oneDevice`, deviceArray);

    return response.data;
}