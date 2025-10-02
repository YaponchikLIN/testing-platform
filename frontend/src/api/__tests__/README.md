# Jest Тесты для API

Эта папка содержит Jest тесты для всех модулей API платформы тестирования RTK.

## Структура тестов

### 📁 Файлы тестов

- **`apiClient.test.js`** - Тесты для базового HTTP клиента
- **`get.test.js`** - Тесты для GET запросов (получение данных)
- **`tests.test.js`** - Тесты для управления тестами
- **`firmware.test.js`** - Тесты для работы с прошивкой
- **`setup.js`** - Настройки Jest для всех тестов

## 🚀 Запуск тестов

### Все тесты

```bash
npm test
```

### Тесты в режиме наблюдения

```bash
npm run test:watch
```

### Тесты с покрытием кода

```bash
npm run test:coverage
```

### Конкретный файл тестов

```bash
npm test apiClient.test.js
npm test get.test.js
npm test tests.test.js
npm test firmware.test.js
```

## 📋 Описание тестируемых модулей

### apiClient.js

**Что тестируется:**

- Создание axios instance с правильной конфигурацией
- Установка базового URL (`http://localhost:8001`)
- Настройка заголовков по умолчанию

**Основные тесты:**

- ✅ Проверка вызова `axios.create` с правильными параметрами
- ✅ Проверка экспорта axios instance
- ✅ Проверка базового URL и заголовков

### get.js

**Что тестируется:**

- `getSNandMAC(order_uid)` - получение серийного номера и MAC адреса
- `getOrders(period)` - получение заказов за период
- `postOneDevice(deviceData)` - получение информации об устройстве

**Основные тесты:**

- ✅ Успешные API вызовы с правильными параметрами
- ✅ Валидация входных данных
- ✅ Обработка ошибок API
- ✅ Корректное формирование URL с параметрами

### tests.js

**Что тестируется:**

- `runTest(testData)` - запуск теста
- `getTestStatus(testId)` - получение статуса теста
- `getTestResult(testId)` - получение результата теста

**Основные тесты:**

- ✅ Запуск тестов с различными параметрами
- ✅ Получение статуса выполнения тестов
- ✅ Получение результатов и логов тестов
- ✅ Валидация test_id
- ✅ Обработка ошибок

### firmware.js

**Что тестируется:**

- `installFirmware(firmwareData)` - установка прошивки
- `runFirmwareTestCycle(cycleData)` - полный цикл тестирования прошивки

**Основные тесты:**

- ✅ Установка прошивки с различными параметрами
- ✅ Запуск полного цикла тестирования
- ✅ Поддержка различных тестовых наборов
- ✅ Отслеживание стадий выполнения
- ✅ Валидация данных прошивки

## 🛠 Конфигурация Jest

### Основные настройки

- **Окружение:** `jsdom` (для браузерного окружения)
- **Трансформация:** Babel для ES6+ синтаксиса
- **Мокирование:** axios автоматически мокается
- **Таймаут:** 10 секунд для каждого теста
- **Покрытие:** Включает все файлы API кроме тестов

### Setup файл

`setup.js` содержит:

- Мокирование axios
- Отключение console.log (кроме ошибок)
- Увеличенный таймаут для тестов

## 📊 Покрытие кода

Тесты настроены для сбора покрытия кода по следующим файлам:

- `src/api/**/*.js` (все API файлы)
- Исключения: `**/__tests__/**`, `**/node_modules/**`

Отчет о покрытии генерируется в форматах:

- `text` - в консоли
- `lcov` - для интеграции с IDE
- `html` - веб-отчет в папке `coverage/`

## 🔧 Мокирование

### axios

Все HTTP запросы мокируются через `jest.mock('axios')`:

```javascript
const mockedAxios = axios;
mockedAxios.get.mockResolvedValue({ data: mockData });
mockedAxios.post.mockResolvedValue({ data: mockResponse });
```

### apiClient

В тестах для модулей API мокируется `../apiClient`:

```javascript
jest.mock("../apiClient");
const mockedApiClient = apiClient;
```

## 📝 Паттерны тестирования

### Структура теста

```javascript
describe("Модуль/Функция", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("должен успешно выполнять операцию", async () => {
    // Arrange
    const mockData = {
      /* тестовые данные */
    };
    mockedApiClient.get.mockResolvedValue({ data: mockData });

    // Act
    const result = await functionUnderTest(inputData);

    // Assert
    expect(mockedApiClient.get).toHaveBeenCalledWith(expectedUrl);
    expect(result).toEqual(mockData);
  });
});
```

### Тестирование ошибок

```javascript
test("должен обрабатывать ошибки API", async () => {
  const mockError = new Error("API Error");
  mockedApiClient.get.mockRejectedValue(mockError);

  await expect(functionUnderTest(inputData)).rejects.toThrow("API Error");
});
```

### Валидация входных данных

```javascript
test("должен выбрасывать ошибку при неверных данных", async () => {
  await expect(functionUnderTest()).rejects.toThrow("Data is required");
  await expect(functionUnderTest(null)).rejects.toThrow("Data is required");
  await expect(functionUnderTest({})).rejects.toThrow("Data is required");
});
```

## 🚨 Важные замечания

1. **Мокирование:** Все HTTP запросы мокируются, реальные API вызовы не выполняются
2. **Изоляция:** Каждый тест изолирован и не влияет на другие
3. **Очистка:** `beforeEach` очищает все моки перед каждым тестом
4. **Асинхронность:** Все API функции асинхронные, используйте `async/await`
5. **Валидация:** Тесты проверяют как успешные сценарии, так и обработку ошибок

## 🔍 Отладка тестов

### Просмотр вызовов моков

```javascript
console.log(mockedApiClient.get.mock.calls);
console.log(mockedApiClient.post.mock.lastCall);
```

### Запуск одного теста

```bash
npm test -- --testNamePattern="должен успешно получать данные"
```

### Подробный вывод

```bash
npm test -- --verbose
```

## 📈 Метрики качества

- **Покрытие кода:** Стремимся к 90%+ покрытию
- **Тестовые сценарии:** Покрываем успешные и неуспешные сценарии
- **Валидация:** Проверяем все входные параметры
- **Ошибки:** Тестируем обработку всех типов ошибок

---

_Этот README автоматически обновляется при изменении структуры тестов._
