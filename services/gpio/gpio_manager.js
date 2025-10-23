const Gpio = require('onoff').Gpio;
const GPIOMeasure = require('./gpio_measure');


class GPIOMonitor {
    constructor(gpioNumber) {
        this.gpioNumber = gpioNumber;
        this.gpio = null;
        this.lastValue = null;
        this.isMonitoring = false;
    }

    start() {
        try {
            console.log(`Инициализация GPIO: ${this.gpioNumber}`);

            this.gpio = new Gpio(this.gpioNumber, 'in', 'both');
            this.lastValue = this.gpio.readSync();

            console.log(`✅ Мониторинг запущен на GPIO ${this.gpioNumber}`);
            console.log(`Начальное значение: ${this.lastValue}`);
            console.log('Ожидание событий... (Ctrl+C для остановки)');

            // Обработчик событий
            this.gpio.watch((err, value) => {
                if (err) {
                    console.error('❌ Ошибка:', err);
                    return;
                }

                if (value !== this.lastValue) {
                    const eventType = value === 1 ? '🔼 ПОДЪЕМ' : '🔽 СПАД';
                    console.log(`Событие: ${eventType} | GPIO: ${value} | Время: ${new Date().toLocaleTimeString()}`);
                    this.lastValue = value;
                }
            });

            this.isMonitoring = true;

        } catch (error) {
            console.error('❌ Ошибка инициализации:', error.message);
        }
    }

    stop() {
        console.log('\n🛑 Остановка мониторинга...');
        if (this.gpio) {
            this.gpio.unwatchAll();
            this.gpio.unexport();
        }
    }
}

/**
 * Класс для сброса и настройки указанных GPIO пинов
 * GPIO 8 - устанавливается как INPUT
 * GPIO 10, 11, 12, 13, 15 - устанавливаются как OUTPUT со значением 0
 */
class GPIOReset {
    constructor() {
        this.gpioInstances = [];
        this.isInitialized = false;
        this.inputPin = 33;
        this.outputPins = [32, 36, 97, 39, 40];

        // Автоматическая инициализация при создании экземпляра
        this.initialize();
    }

    /**
     * Инициализация и настройка всех GPIO пинов
     * @returns {Object} Результат операции
     */
    initialize() {
        // Если уже инициализирован, возвращаем успешный результат
        if (this.isInitialized) {
            console.log('ℹ️ GPIO Reset уже инициализирован');
            return {
                success: true,
                message: 'GPIO пины уже настроены',
                gpioInstances: this.gpioInstances
            };
        }

        try {
            console.log('🔄 Начинаем сброс GPIO пинов...');

            // Очищаем предыдущие экземпляры, если они есть
            this.cleanup();

            // GPIO 8 - устанавливаем как INPUT
            console.log(`📥 Настройка GPIO ${this.inputPin} как INPUT...`);
            const gpio8 = new GPIOMeasure(this.inputPin);
            gpio8.initialize('in');
            this.gpioInstances.push(gpio8);
            console.log(`✅ GPIO ${this.inputPin} настроен как INPUT`);

            // GPIO 32, 36, 97, 39, 40 - устанавливаем как OUTPUT со значением 0
            for (const pin of this.outputPins) {
                console.log(`📤 Настройка GPIO ${pin} как OUTPUT и установка в состояние 0...`);
                const gpio = new GPIOMeasure(pin);
                gpio.initialize('out');
                gpio.setState(0);
                this.gpioInstances.push(gpio);
                console.log(`✅ GPIO ${pin} настроен как OUTPUT и установлен в состояние 0`);
            }

            this.isInitialized = true;
            console.log('🎉 Все GPIO пины успешно настроены!');

            // Показываем итоговое состояние
            this.showStatus();

            return {
                success: true,
                message: 'GPIO пины успешно настроены',
                gpioInstances: this.gpioInstances
            };

        } catch (error) {
            console.error('❌ Ошибка при настройке GPIO:', error.message);

            // Очищаем частично созданные экземпляры в случае ошибки
            this.cleanup();

            return {
                success: false,
                message: `Ошибка при настройке GPIO: ${error.message}`,
                gpioInstances: []
            };
        }
    }

    /**
     * Показать текущее состояние всех GPIO пинов
     */
    showStatus() {
        console.log('\n📋 Итоговое состояние GPIO:');
        console.log(`GPIO ${this.inputPin}: INPUT`);
        this.outputPins.forEach(pin => {
            console.log(`GPIO ${pin}: OUTPUT, состояние: 0`);
        });
    }

    /**
     * Получить информацию о настроенных GPIO
     * @returns {Object} Информация о GPIO
     */
    getInfo() {
        return {
            isInitialized: this.isInitialized,
            inputPin: this.inputPin,
            outputPins: this.outputPins,
            totalPins: this.gpioInstances.length,
            gpioInstances: this.gpioInstances
        };
    }

    /**
     * Проверить состояние входного пина (GPIO 8)
     * @returns {number|null} Состояние пина или null в случае ошибки
     */
    readInputPin() {
        if (!this.isInitialized) {
            console.warn('⚠️ GPIO не инициализированы. Вызовите initialize() сначала.');
            return null;
        }

        try {
            const inputGpio = this.gpioInstances.find(gpio => gpio.pin === this.inputPin);
            if (inputGpio) {
                const state = inputGpio.getState();
                console.log(`📖 GPIO ${this.inputPin} (INPUT): ${state}`);
                return state;
            }
            return null;
        } catch (error) {
            console.error(`❌ Ошибка чтения GPIO ${this.inputPin}:`, error.message);
            return null;
        }
    }

    /**
     * Установить состояние выходного пина
     * @param {number} pin - Номер пина
     * @param {number} state - Состояние (0 или 1)
     * @returns {boolean} Успешность операции
     */
    setOutputPin(pin, state) {
        try {
            if (!this.isInitialized) {
                console.warn('⚠️ GPIO не инициализированы. Вызовите initialize() сначала.');
                return false;
            }

            if (!this.outputPins.includes(pin)) {
                console.error(`❌ Пин ${pin} не является выходным пином`);
                return false;
            }


            const outputGpio = this.gpioInstances.find(gpio => gpio.pin === pin);
            if (outputGpio) {
                outputGpio.setState(state);
                console.log(`📝 GPIO ${pin} установлен в состояние: ${state}`);
                return true;
            }
            return false;
        } catch (error) {
            console.error(`❌ Ошибка установки GPIO ${pin}:`, error.message);
            return false;
        }
    }

    /**
     * Очистка всех GPIO ресурсов
     */
    cleanup() {
        console.log('🧹 Очистка GPIO ресурсов...');

        for (const gpio of this.gpioInstances) {
            try {
                if (gpio && typeof gpio.cleanup === 'function') {
                    gpio.cleanup();
                }
            } catch (error) {
                console.error(`❌ Ошибка при очистке GPIO ${gpio.pin}:`, error.message);
            }
        }

        this.gpioInstances = [];
        this.isInitialized = false;
        console.log('✅ Очистка GPIO завершена');
    }
}

// Автоматический запуск при загрузке модуля
console.log('🚀 Запуск GPIO системы...');

// 1. Запуск мониторинга GPIO 33
const monitor = new GPIOMonitor(33);
monitor.start();

// 2. Автоматический сброс GPIO
console.log('🔄 Инициализация GPIO сброса...');
const gpioReset = new GPIOReset();

// Показать статус после инициализации
setTimeout(() => {
    console.log('📊 Статус GPIO системы:');
    gpioReset.showStatus();
}, 1000);

// Глобальная переменная для доступа к экземпляру сброса
global.gpioResetInstance = gpioReset;

process.on('SIGINT', () => {
    console.log('🛑 Остановка GPIO системы...');
    monitor.stop();
    if (gpioReset) {
        gpioReset.cleanup();
    }
    process.exit();
});

// Экспорт функций для использования в других модулях
module.exports = {
    GPIOMonitor,
    GPIOReset
};