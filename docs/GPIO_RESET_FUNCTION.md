# Документация по классу GPIOReset

## Обзор

Класс `GPIOReset` предназначен для автоматической настройки GPIO пинов в определенное состояние. При создании экземпляра класса автоматически настраивается GPIO 8 как входной пин и GPIO 10, 11, 12, 13, 15 как выходные пины со значением 0.

## Функциональность

Класс `GPIOReset` предоставляет следующую функциональность:

### Автоматическая инициализация
- При создании экземпляра автоматически вызывается метод `initialize()`
- GPIO 8 настраивается как входной пин для чтения данных
- GPIO 10, 11, 12, 13, 15 настраиваются как выходные пины со значением 0 (LOW)

### Методы класса
- `initialize()` - инициализация GPIO (вызывается автоматически)
- `showStatus()` - отображение текущего состояния всех GPIO
- `getInfo()` - получение информации о настроенных GPIO
- `readInputPin()` - чтение состояния входного пина (GPIO 8)
- `setOutputPin(pin, state)` - установка состояния выходного пина
- `cleanup()` - освобождение ресурсов GPIO

### Основная функция: `resetSpecificGPIOs()`

```javascript
const { resetSpecificGPIOs, cleanupGPIOs } = require('./gpio_manager');

// Сброс GPIO пинов
const result = resetSpecificGPIOs();

if (result.success) {
    console.log('GPIO пины успешно настроены');
    
    // Работа с GPIO...
    
    // Очистка ресурсов
    cleanupGPIOs(result.gpioInstances);
} else {
    console.error('Ошибка настройки GPIO:', result.error);
}
```

### Конфигурация GPIO пинов

Функция настраивает следующие GPIO пины:

| GPIO | Направление | Состояние | Описание |
|------|-------------|-----------|----------|
| 8    | INPUT       | -         | Входной пин для чтения сигналов |
| 10   | OUTPUT      | 0 (LOW)   | Выходной пин, установлен в LOW |
| 11   | OUTPUT      | 0 (LOW)   | Выходной пин, установлен в LOW |
| 12   | OUTPUT      | 0 (LOW)   | Выходной пин, установлен в LOW |
| 13   | OUTPUT      | 0 (LOW)   | Выходной пин, установлен в LOW |
| 15   | OUTPUT      | 0 (LOW)   | Выходной пин, установлен в LOW |

## Возвращаемое значение

Функция возвращает объект со следующей структурой:

```javascript
{
    success: boolean,           // Успешность операции
    gpioInstances: Array,       // Массив экземпляров GPIO
    error: string,              // Сообщение об ошибке (если success = false)
    message: string             // Описательное сообщение
}
```

### При успешном выполнении:
```javascript
{
    success: true,
    gpioInstances: [gpio8, gpio10, gpio11, gpio12, gpio13, gpio15],
    message: "GPIO пины успешно настроены"
}
```

### При ошибке:
```javascript
{
    success: false,
    gpioInstances: [],
    error: "Описание ошибки",
    message: "Не удалось настроить GPIO пины"
}
```

## Примеры использования

### 1. Простое использование

```javascript
const { GPIOReset } = require('./gpio_manager');

function initializeSystem() {
    try {
        const gpioReset = new GPIOReset();
        console.log('✅ Система инициализирована');
        return gpioReset;
    } catch (error) {
        console.error('❌ Ошибка инициализации:', error.message);
        return null;
    }
}

// Использование
const gpioReset = initializeSystem();
if (gpioReset) {
    // Работа с GPIO...
    gpioReset.showStatus();
    
    // Очистка
    gpioReset.cleanup();
}
```

### 2. Использование в тестах

```javascript
const { resetSpecificGPIOs, cleanupGPIOs } = require('./gpio_manager');

describe('GPIO Tests', () => {
    let gpioInstances;
    
    beforeEach(() => {
        const result = resetSpecificGPIOs();
        expect(result.success).toBe(true);
        gpioInstances = result.gpioInstances;
    });
    
    afterEach(() => {
        if (gpioInstances) {
            cleanupGPIOs(gpioInstances);
        }
    });
    
    test('GPIO configuration', () => {
        // Проверяем конфигурацию GPIO 8 (INPUT)
        const gpio8 = gpioInstances.find(gpio => gpio.getInfo().pin === 8);
        expect(gpio8.getInfo().direction).toBe('in');
        
        // Проверяем конфигурацию GPIO 10 (OUTPUT = 0)
        const gpio10 = gpioInstances.find(gpio => gpio.getInfo().pin === 10);
        expect(gpio10.getInfo().direction).toBe('out');
        expect(gpio10.getState()).toBe(0);
    });
});
```

### 3. Использование с обработкой ошибок

```javascript
const { resetSpecificGPIOs, cleanupGPIOs } = require('./gpio_manager');

async function safeGPIOOperation() {
    let gpioInstances = null;
    
    try {
        // Инициализация GPIO
        const result = resetSpecificGPIOs();
        
        if (!result.success) {
            throw new Error(`GPIO initialization failed: ${result.error}`);
        }
        
        gpioInstances = result.gpioInstances;
        console.log('GPIO инициализированы успешно');
        
        // Получение информации о GPIO
        gpioInstances.forEach(gpio => {
            const info = gpio.getInfo();
            console.log(`GPIO ${info.pin}: ${info.direction} = ${info.state}`);
        });
        
        // Работа с GPIO...
        const gpio10 = gpioInstances.find(gpio => gpio.getInfo().pin === 10);
        gpio10.setHigh();
        console.log('GPIO 10 установлен в HIGH');
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        gpio10.setLow();
        console.log('GPIO 10 установлен в LOW');
        
    } catch (error) {
        console.error('Ошибка операции GPIO:', error.message);
    } finally {
        // Всегда очищаем ресурсы
        if (gpioInstances) {
            cleanupGPIOs(gpioInstances);
            console.log('Ресурсы GPIO очищены');
        }
    }
}

safeGPIOOperation();
```

## Вспомогательная функция: `cleanupGPIOs()`

```javascript
cleanupGPIOs(gpioInstances)
```

### Параметры:
- `gpioInstances` - массив экземпляров GPIO для очистки

### Описание:
Безопасно освобождает ресурсы GPIO, предотвращая утечки памяти и конфликты ресурсов.

## Robot Framework интеграция

### Использование в Robot Framework тестах

```robot
*** Settings ***
Library    gpio_utils.GPIOLibrary

*** Test Cases ***
Test GPIO Reset
    [Documentation]    Тестирует сброс GPIO пинов
    
    # Ожидание готовности системы
    Wait For GPIO Ready    max_wait_time=10
    
    # Сброс GPIO
    Reset GPIO Pins    timeout=30
    
    # Проверка конфигурации
    Verify GPIO Pin Configuration    8    in
    Verify GPIO Pin Configuration    10   out    0
    Verify GPIO Pin Configuration    11   out    0
    Verify GPIO Pin Configuration    12   out    0
    Verify GPIO Pin Configuration    13   out    0
    Verify GPIO Pin Configuration    15   out    0
    
    # Получение сводки
    ${summary} =    Get GPIO Status Summary
    Log    ${summary}
```

### Доступные Robot Framework ключевые слова:

- `Reset GPIO Pins` - сброс GPIO пинов
- `Wait For GPIO Ready` - ожидание готовности GPIO системы
- `Verify GPIO Pin Configuration` - проверка конфигурации пина
- `Get GPIO Status Summary` - получение сводки состояния
- `Test GPIO Functionality` - тестирование функциональности
- `Check GPIO Configuration` - проверка всех конфигураций

## Обработка ошибок

### Типичные ошибки и их решения:

1. **Permission denied**
   ```
   Ошибка: EACCES: permission denied
   Решение: Запустите с правами администратора или настройте udev правила
   ```

2. **GPIO already in use**
   ```
   Ошибка: GPIO pin already exported
   Решение: Освободите GPIO или перезапустите систему
   ```

3. **Invalid GPIO pin**
   ```
   Ошибка: Invalid GPIO pin number
   Решение: Проверьте доступность GPIO пинов на вашей платформе
   ```

## Лучшие практики

### 1. Всегда используйте cleanup
```javascript
const result = resetSpecificGPIOs();
try {
    // Работа с GPIO
} finally {
    if (result.success) {
        cleanupGPIOs(result.gpioInstances);
    }
}
```

### 2. Проверяйте результат операции
```javascript
const result = resetSpecificGPIOs();
if (!result.success) {
    console.error('Initialization failed:', result.error);
    return;
}
```

### 3. Используйте информацию о GPIO
```javascript
result.gpioInstances.forEach(gpio => {
    const info = gpio.getInfo();
    console.log(`GPIO ${info.pin}: ${info.direction}`);
});
```

### 4. Обрабатывайте исключения
```javascript
try {
    const result = resetSpecificGPIOs();
    // работа с GPIO
} catch (error) {
    console.error('GPIO error:', error.message);
}
```

## Системные требования

- **Операционная система**: Linux (Raspberry Pi OS, Ubuntu, Debian)
- **Node.js**: версия 12.0 или выше
- **Зависимости**: `onoff` библиотека
- **Права доступа**: доступ к `/sys/class/gpio/`

## Устранение неполадок

### Проблема: GPIO не инициализируются
**Решение**: 
1. Проверьте права доступа
2. Убедитесь, что GPIO не используются другими процессами
3. Проверьте доступность GPIO пинов

### Проблема: Ошибка "Module not found"
**Решение**:
1. Установите зависимости: `npm install onoff`
2. Проверьте пути к модулям

### Проблема: Тесты не проходят
**Решение**:
1. Проверьте подключение оборудования
2. Убедитесь в правильности конфигурации GPIO
3. Проверьте логи на наличие ошибок

## Заключение

Функция `resetSpecificGPIOs` предоставляет надежный и простой способ инициализации GPIO пинов в определенное состояние. Используйте её в начале тестов или при инициализации системы для обеспечения предсказуемого поведения GPIO.