// Тесты для firmware.js
import { installFirmware, runFirmwareTestCycle } from '../firmware';
import apiClient from '../apiClient';

// Мокаем apiClient
jest.mock('../apiClient');
const mockedApiClient = apiClient;

describe('firmware.js API functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('installFirmware', () => {
    test('должен успешно устанавливать прошивку', async () => {
      const mockResponse = {
        data: {
          installation_id: 'install_123',
          status: 'installing',
          message: 'Firmware installation started'
        }
      };
      
      const firmwareData = {
        serial_number: 'SN123456',
        firmware_version: '2.1.0',
        firmware_url: 'http://example.com/firmware.bin'
      };
      
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const result = await installFirmware(firmwareData);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/install', {});
      expect(result).toEqual(mockResponse.data);
    });

    test('должен обрабатывать ошибки API при установке прошивки', async () => {
      const mockError = new Error('Firmware installation failed');
      mockedApiClient.post.mockRejectedValue(mockError);
      
      await expect(installFirmware()).rejects.toThrow('Firmware installation failed');
    });

    test('должен передавать все поля firmwareData в запросе', async () => {
      const mockResponse = { data: { installation_id: 'install_123' } };
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const firmwareData = {
        serial_number: 'SN123456',
        mac_address: '00:11:22:33:44:55',
        firmware_version: '2.1.0',
        firmware_url: 'http://example.com/firmware.bin',
        checksum: 'abc123def456',
        force_install: true
      };
      
      await installFirmware(firmwareData);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/install', {});
    });
  });

  describe('runFirmwareTestCycle', () => {
    test('должен успешно запускать полный цикл тестирования прошивки', async () => {
      const mockResponse = {
        data: {
          cycle_id: 'cycle_123',
          status: 'running',
          stages: [
            { name: 'firmware_install', status: 'pending' },
            { name: 'basic_tests', status: 'pending' },
            { name: 'advanced_tests', status: 'pending' }
          ]
        }
      };
      
      const cycleData = {
        serial_number: 'SN123456',
        mac_address: '00:11:22:33:44:55',
        firmware_version: '2.1.0',
        test_suite: 'full'
      };
      
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const result = await runFirmwareTestCycle(cycleData);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/test-cycle', {
        build_id: cycleData.build_id || null,
        artifact_path: cycleData.artifact_path || null,
        test_id: cycleData.test_id || "all",
        wait_for_router: cycleData.wait_for_router || 60
      });
      expect(result).toEqual(mockResponse.data);
    });

    test('должен работать с пустыми параметрами используя значения по умолчанию', async () => {
      const mockResponse = { data: { cycle_id: 'cycle_123' } };
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const result = await runFirmwareTestCycle({});
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/test-cycle', {
        build_id: null,
        artifact_path: null,
        test_id: 'all',
        wait_for_router: 60
      });
      expect(result).toEqual(mockResponse.data);
    });

    test('должен обрабатывать ошибки API при запуске цикла тестирования', async () => {
      const mockError = new Error('Test cycle failed to start');
      mockedApiClient.post.mockRejectedValue(mockError);
      
      const cycleData = {
        serial_number: 'SN123456',
        firmware_version: '2.1.0'
      };
      
      await expect(runFirmwareTestCycle(cycleData)).rejects.toThrow('Test cycle failed to start');
    });

    test('должен передавать все параметры цикла тестирования', async () => {
      const mockResponse = {
        data: {
          cycle_id: 'cycle_789',
          status: 'started',
          stages: ['firmware_install', 'router_wait', 'test_execution']
        }
      };
      
      const cycleData = {
        build_id: 'build_123',
        artifact_path: '/path/to/firmware.bin',
        test_id: 'full_test',
        wait_for_router: 120
      };
      
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const result = await runFirmwareTestCycle(cycleData);
      
      expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/test-cycle', {
        build_id: 'build_123',
        artifact_path: '/path/to/firmware.bin',
        test_id: 'full_test',
        wait_for_router: 120
      });
      expect(result).toEqual(mockResponse.data);
    });

    test('должен поддерживать различные типы тестовых наборов', async () => {
      const mockResponse = { data: { cycle_id: 'cycle_123' } };
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const testSuites = ['basic', 'full', 'extended', 'custom'];
      
      for (const testSuite of testSuites) {
        const cycleData = {
          serial_number: 'SN123456',
          firmware_version: '2.1.0',
          test_suite: testSuite
        };
        
        await runFirmwareTestCycle(cycleData);
        
        expect(mockedApiClient.post).toHaveBeenCalledWith('firmware/test-cycle',
          expect.objectContaining({
            build_id: null,
            artifact_path: null,
            test_id: "all",
            wait_for_router: 60
          })
        );
      }
    });

    test('должен возвращать информацию о стадиях тестирования', async () => {
      const mockResponse = {
        data: {
          cycle_id: 'cycle_123',
          status: 'running',
          current_stage: 'firmware_install',
          stages: [
            { name: 'firmware_install', status: 'running', progress: 50 },
            { name: 'basic_tests', status: 'pending', progress: 0 },
            { name: 'advanced_tests', status: 'pending', progress: 0 },
            { name: 'performance_tests', status: 'pending', progress: 0 }
          ],
          estimated_completion: '2024-01-15T14:30:00Z'
        }
      };
      
      mockedApiClient.post.mockResolvedValue(mockResponse);
      
      const cycleData = {
        serial_number: 'SN123456',
        firmware_version: '2.1.0',
        test_suite: 'full'
      };
      
      const result = await runFirmwareTestCycle(cycleData);
      
      expect(result).toHaveProperty('cycle_id', 'cycle_123');
      expect(result).toHaveProperty('status', 'running');
      expect(result).toHaveProperty('current_stage', 'firmware_install');
      expect(result).toHaveProperty('stages');
      expect(result.stages).toHaveLength(4);
      expect(result.stages[0]).toHaveProperty('name', 'firmware_install');
      expect(result.stages[0]).toHaveProperty('status', 'running');
      expect(result.stages[0]).toHaveProperty('progress', 50);
    });
  });
});