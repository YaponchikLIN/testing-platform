// Тесты для tests.js
import { runTest, getTestStatus, getTestResult } from '../tests';
import apiClient from '../apiClient';

// Мокаем apiClient
jest.mock('../apiClient');
const mockedApiClient = apiClient;

describe('tests.js API functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('runTest', () => {
    test('должен успешно запускать тест', async () => {
      const mockResponse = {
        data: {
          test_id: 'test_123',
          status: 'running',
          message: 'Test started successfully'
        }
      };
      
      const testId = 'test_123';
      
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const result = await runTest(testId);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('/tests/run', { test_id: testId });
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если testId не передан', async () => {
      await expect(runTest()).rejects.toThrow('testId is required');
      await expect(runTest(null)).rejects.toThrow('testId is required');
      await expect(runTest('')).rejects.toThrow('testId is required');
    });

    test('должен обрабатывать ошибки API при запуске теста', async () => {
      const mockError = new Error('Failed to start test');
      mockedApiClient.post.mockRejectedValue(mockError);
      
      const testId = 'test_123';
      
      await expect(runTest(testId)).rejects.toThrow('Failed to start test');
    });

    test('должен передавать testId в запросе', async () => {
      const mockResponse = { data: { test_id: 'test_123' } };
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const testId = 'test_456';
      
      await runTest(testId);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('/tests/run', { test_id: testId });
    });
  });

  describe('getTestStatus', () => {
    test('должен успешно получать статус теста', async () => {
      const mockResponse = {
        data: {
          test_id: 'test_123',
          status: 'completed',
          progress: 100,
          current_step: 'finished'
        }
      };
      
      mockedApiClient.get.mockResolvedValue(mockResponse);
      
      const result = await getTestStatus('test_123');
      
      expect(mockedApiClient.get).toHaveBeenCalledWith('/tests/status/test_123');
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если testId не передан', async () => {
      await expect(getTestStatus()).rejects.toThrow('testId is required');
      await expect(getTestStatus('')).rejects.toThrow('testId is required');
      await expect(getTestStatus(null)).rejects.toThrow('testId is required');
    });

    test('должен обрабатывать ошибки API при получении статуса', async () => {
      const mockError = new Error('Test not found');
      mockedApiClient.get.mockRejectedValue(mockError);
      
      await expect(getTestStatus('invalid_test_id')).rejects.toThrow('Test not found');
    });

    test('должен корректно формировать URL с test_id', async () => {
      const mockResponse = { data: { status: 'running' } };
      mockedApiClient.get.mockResolvedValue(mockResponse);
      
      await getTestStatus('test_456');
      
      expect(mockedApiClient.get).toHaveBeenCalledWith('/tests/status/test_456');
    });
  });

  describe('getTestResult', () => {
    test('должен успешно получать результат теста', async () => {
      const mockResponse = {
        data: {
          test_id: 'test_123',
          status: 'completed',
          result: 'passed',
          details: {
            tests_passed: 15,
            tests_failed: 0,
            execution_time: 120
          },
          log: 'Test execution log...'
        }
      };
      
      mockedApiClient.get.mockResolvedValue(mockResponse);
      
      const result = await getTestResult('test_123');
      
      expect(mockedApiClient.get).toHaveBeenCalledWith('/tests/result/test_123');
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если testId не передан', async () => {
      await expect(getTestResult()).rejects.toThrow('testId is required');
      await expect(getTestResult('')).rejects.toThrow('testId is required');
      await expect(getTestResult(null)).rejects.toThrow('testId is required');
    });

    test('должен обрабатывать ошибки API при получении результата', async () => {
      const mockError = new Error('Test result not available');
      mockedApiClient.get.mockRejectedValue(mockError);
      
      await expect(getTestResult('test_123')).rejects.toThrow('Test result not available');
    });

    test('должен корректно формировать URL с test_id', async () => {
      const mockResponse = { data: { result: 'passed' } };
      mockedApiClient.get.mockResolvedValue(mockResponse);
      
      await getTestResult('test_789');
      
      expect(mockedApiClient.get).toHaveBeenCalledWith('/tests/result/test_789');
    });

    test('должен возвращать полную информацию о результате теста', async () => {
      const mockResponse = {
        data: {
          test_id: 'test_123',
          status: 'failed',
          result: 'failed',
          error_message: 'Connection timeout',
          details: {
            tests_passed: 10,
            tests_failed: 5,
            execution_time: 90
          }
        }
      };
      
      mockedApiClient.get.mockResolvedValue(mockResponse);
      
      const result = await getTestResult('test_123');
      
      expect(result).toHaveProperty('test_id', 'test_123');
      expect(result).toHaveProperty('status', 'failed');
      expect(result).toHaveProperty('result', 'failed');
      expect(result).toHaveProperty('error_message', 'Connection timeout');
      expect(result).toHaveProperty('details');
      expect(result.details).toHaveProperty('tests_passed', 10);
      expect(result.details).toHaveProperty('tests_failed', 5);
    });
  });
});