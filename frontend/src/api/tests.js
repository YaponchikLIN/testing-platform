// api/testsApi.js
import apiClient from './apiClient';

export async function runTest(testId) {
    if (!testId) throw new Error('testId is required');
    const response = await apiClient.post('/tests/run', { test_id: testId });
    return response.data;
}


export async function getTestStatus(testId) {
    if (!testId) throw new Error('testId is required');
    const response = await apiClient.get(`/tests/status/${testId}`);
    return response.data;
}


export async function getTestResult(testId) {
    if (!testId) throw new Error('testId is required');
    const response = await apiClient.get(`/tests/result/${testId}`);
    return response.data;
}