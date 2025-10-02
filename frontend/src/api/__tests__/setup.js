// Jest setup file
// Настройка для тестирования API

// Мокаем axios для предотвращения реальных HTTP запросов
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  })),
}));

// Глобальные настройки для тестов
global.console = {
  ...console,
  // Отключаем логи в тестах, кроме ошибок
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: console.error,
};

// Настройка таймаутов для тестов
jest.setTimeout(10000);