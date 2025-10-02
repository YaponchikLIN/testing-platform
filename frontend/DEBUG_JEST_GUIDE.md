# Руководство по отладке Jest тестов

Это руководство покажет вам различные способы отладки Jest тестов в проекте.

## 🔧 Способы отладки

### 1. Отладка через VS Code (Рекомендуется)

#### Настройка уже готова!
В папке `.vscode/launch.json` уже настроены конфигурации для отладки:

- **Debug Jest Tests** - отладка всех тестов
- **Debug Current Jest Test File** - отладка текущего открытого файла теста
- **Debug Specific Jest Test** - отладка конкретного теста по имени

#### Как использовать:
1. Откройте файл с тестом (например, `src/api/__tests__/get.test.js`)
2. Поставьте точки останова (breakpoints) в нужных местах
3. Нажмите `F5` или перейдите в раздел "Run and Debug" (Ctrl+Shift+D)
4. Выберите нужную конфигурацию отладки
5. Нажмите "Start Debugging"

### 2. Отладка через командную строку

#### Доступные команды:

```bash
# Отладка всех тестов
npm run test:debug

# Отладка с автоперезапуском при изменениях
npm run test:debug-watch

# Подробный вывод тестов
npm run test:verbose

# Запуск конкретного файла теста
npm run test:single src/api/__tests__/get.test.js

# Запуск конкретного теста по имени
npm test -- --testNamePattern="getOneDevice"

# Запуск тестов с покрытием кода
npm run test:coverage
```

#### Отладка через Chrome DevTools:
1. Запустите: `npm run test:debug`
2. Откройте Chrome и перейдите на `chrome://inspect`
3. Нажмите "Open dedicated DevTools for Node"
4. Поставьте точки останова в коде
5. Продолжите выполнение

### 3. Отладка конкретного теста

#### Способ 1: Через VS Code
1. Откройте файл теста
2. Найдите нужный тест (например, `test('should get one device', ...)`)
3. Поставьте точку останова
4. Используйте конфигурацию "Debug Current Jest Test File"

#### Способ 2: Через командную строку
```bash
# Запуск только тестов getOneDevice
npm test -- --testNamePattern="getOneDevice"

# Запуск только файла get.test.js
npm test src/api/__tests__/get.test.js

# Запуск с отладкой конкретного файла
node --inspect-brk node_modules/.bin/jest src/api/__tests__/get.test.js --runInBand
```

### 4. Полезные опции Jest для отладки

```bash
# Запуск тестов последовательно (не параллельно)
npm test -- --runInBand

# Отключение кэша
npm test -- --no-cache

# Подробный вывод
npm test -- --verbose

# Показать только неудачные тесты
npm test -- --onlyFailures

# Остановиться на первой ошибке
npm test -- --bail

# Запуск в режиме наблюдения
npm test -- --watch
```

## 🐛 Советы по отладке

### 1. Использование console.log
```javascript
test('should get one device', async () => {
    const testData = {
        serial_number: 'TEST123',
        mac_address: '00:11:22:33:44:55',
        status: 'Новый'
    };
    
    console.log('Test data:', testData); // Отладочный вывод
    
    const result = await getOneDevice(testData);
    
    console.log('Result:', result); // Отладочный вывод
    
    expect(result).toBeDefined();
});
```

### 2. Использование debugger
```javascript
test('should get one device', async () => {
    const testData = {
        serial_number: 'TEST123',
        mac_address: '00:11:22:33:44:55',
        status: 'Новый'
    };
    
    debugger; // Точка останова в коде
    
    const result = await getOneDevice(testData);
    
    expect(result).toBeDefined();
});
```

### 3. Мокирование для отладки
```javascript
// Добавьте логирование в моки
jest.mock('../apiClient', () => ({
    get: jest.fn().mockImplementation((url) => {
        console.log('API call to:', url); // Отладочный вывод
        return Promise.resolve({
            data: { success: true, device_id: 123 }
        });
    })
}));
```

## 🔍 Отладка конкретных проблем

### Проблема с асинхронными тестами
```javascript
// Используйте async/await
test('async test', async () => {
    const result = await someAsyncFunction();
    expect(result).toBeDefined();
});

// Или return Promise
test('promise test', () => {
    return someAsyncFunction().then(result => {
        expect(result).toBeDefined();
    });
});
```

### Проблема с моками
```javascript
// Очистка моков между тестами
afterEach(() => {
    jest.clearAllMocks();
});

// Проверка вызовов моков
expect(mockedFunction).toHaveBeenCalledWith(expectedArgs);
expect(mockedFunction).toHaveBeenCalledTimes(1);
```

## 📝 Примеры отладки

### Отладка теста getOneDevice
1. Откройте `src/api/__tests__/get.test.js`
2. Найдите тест `getOneDevice`
3. Поставьте точку останова на строке с вызовом функции
4. Запустите отладку через VS Code
5. Изучите переменные в области видимости
6. Пошагово выполните код

### Отладка API вызовов
1. Поставьте точку останова в моке `apiClient.get`
2. Проверьте, какие параметры передаются
3. Убедитесь, что мок возвращает ожидаемые данные

## 🚀 Быстрый старт

1. **Для начинающих**: Используйте VS Code с готовыми конфигурациями
2. **Для опытных**: Используйте `npm run test:debug` + Chrome DevTools
3. **Для CI/CD**: Используйте `npm run test:verbose` для подробных логов

---

**Совет**: Начните с простых `console.log` выводов, затем переходите к полноценной отладке с точками останова.