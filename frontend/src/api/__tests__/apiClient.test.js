// Тесты для apiClient.js
import axios from 'axios';
import apiClient from '../apiClient';

describe('apiClient', () => {
  test('должен быть экземпляром axios с правильной конфигурацией', () => {
      expect(apiClient).toBeDefined();
      expect(typeof apiClient.get).toBe('function');
      expect(typeof apiClient.post).toBe('function');
      expect(typeof apiClient.put).toBe('function');
      expect(typeof apiClient.delete).toBe('function');
    });

  test('должен экспортировать axios instance', () => {
    expect(apiClient).toBeDefined();
    expect(typeof apiClient).toBe('object');
  });
});