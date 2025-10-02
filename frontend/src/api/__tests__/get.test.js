// Тесты для get.js
import { getSNandMAC, getOrders, getOneDevice } from '../get';
import apiClient from '../apiClient';

// Мокаем apiClient
jest.mock('../apiClient');
const mockedApiClient = apiClient;

describe('get.js API functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getSNandMAC', () => {
    test('должен успешно получать SN и MAC по order_uid', async () => {
      const mockResponse = {
        data: {
          serial_number: 'SN123456',
          mac_address: '00:11:22:33:44:55'
        }
      };

      mockedApiClient.get.mockResolvedValue(mockResponse);

      const result = await getSNandMAC('order123');

      expect(mockedApiClient.get).toHaveBeenCalledWith('/1C/SNandMAC?order_uid=order123');
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если order_uid не передан', async () => {
      await expect(getSNandMAC()).rejects.toThrow('Order is required');
      await expect(getSNandMAC('')).rejects.toThrow('Order is required');
      await expect(getSNandMAC(null)).rejects.toThrow('Order is required');
    });

    test('должен обрабатывать ошибки API', async () => {
      const mockError = new Error('API Error');
      mockedApiClient.get.mockRejectedValue(mockError);

      await expect(getSNandMAC('order123')).rejects.toThrow('API Error');
    });
  });

  describe('getOrders', () => {
    test('должен успешно получать заказы за период', async () => {
      const mockResponse = {
        data: [
          { id: 1, order_uid: 'order1', date: '2024-01-15' },
          { id: 2, order_uid: 'order2', date: '2024-01-16' }
        ]
      };

      const period = {
        dateFrom: '2024-01-15',
        dateTo: '2024-01-16'
      };

      mockedApiClient.get.mockResolvedValue(mockResponse);

      const result = await getOrders(period);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/1C/orders?date_from=2024-01-15&date_to=2024-01-16'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если period не передан', async () => {
      await expect(getOrders()).rejects.toThrow('Period is required');
      await expect(getOrders(null)).rejects.toThrow('Period is required');
    });

    test('должен корректно формировать URL с параметрами периода', async () => {
      const mockResponse = { data: [] };
      mockedApiClient.get.mockResolvedValue(mockResponse);

      const period = {
        dateFrom: '2024-01-01',
        dateTo: '2024-12-31'
      };

      await getOrders(period);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/1C/orders?date_from=2024-01-01&date_to=2024-12-31'
      );
    });
  });

  describe('getOneDevice', () => {
    test('должен успешно получать информацию об устройстве', async () => {
      const mockResponse = {
        data: {
          serial_number: 'SN123456',
          mac_address: '00:11:22:33:44:55',
          status: 'ВПроцессе'
        }
      };

      const deviceData = {
        serial_number: 'SN123456',
        mac_address: '00:11:22:33:44:55',
        status: 'active'
      };

      mockedApiClient.get.mockResolvedValue(mockResponse);

      const result = await getOneDevice(deviceData);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/1C/oneDevice?serial_number=SN123456&mac_address=00:11:22:33:44:55&change_status_to=ВПроцессе'
      );
      expect(result).toEqual(mockResponse.data);
    });

    test('должен выбрасывать ошибку если данные неполные', async () => {
      await expect(getOneDevice()).rejects.toThrow('All data is required');
      await expect(getOneDevice({})).rejects.toThrow('All data is required');
      await expect(getOneDevice({ serial_number: 'SN123' })).rejects.toThrow('All data is required');
      await expect(getOneDevice({
        serial_number: 'SN123',
        mac_address: '00:11:22:33:44:55'
      })).rejects.toThrow('All data is required');
    });

    test('должен корректно формировать URL с параметрами устройства', async () => {
      const mockResponse = { data: {} };
      mockedApiClient.get.mockResolvedValue(mockResponse);

      const deviceData = {
        serial_number: 'TEST123',
        mac_address: 'AA:BB:CC:DD:EE:FF',
        status: 'Успешно'
      };

      await getOneDevice(deviceData);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/1C/oneDevice?serial_number=TEST123&mac_address=AA:BB:CC:DD:EE:FF&change_status_to=ВПроцессе'
      );
    });

    test('должен всегда использовать статус "ВПроцессе" независимо от входного статуса', async () => {
      const mockResponse = { data: {} };
      mockedApiClient.get.mockResolvedValue(mockResponse);

      const deviceData = {
        serial_number: 'TEST123',
        mac_address: 'AA:BB:CC:DD:EE:FF',
        status: 'any_status'
      };

      await getOneDevice(deviceData);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('change_status_to=ВПроцессе')
      );
    });
  });
});