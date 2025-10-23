const Gpio = require('onoff').Gpio;

class GPIOMeasure {
    constructor(gpioNumber) {
        this.gpioNumber = gpioNumber;
        this.gpio = null;
        this.isInitialized = false;
        this.currentDirection = null;
    }

    /**
     * Инициализация GPIO с заданным направлением
     * @param {string} direction - 'in' или 'out'
     */
    initialize(direction = 'out') {
        try {
            if (this.isInitialized) {
                this.cleanup();
            }

            this.validateGpioNumber();
            this.validateDirection(direction);

            this.gpio = new Gpio(this.gpioNumber, direction);
            this.currentDirection = direction;
            this.isInitialized = true;

            console.log(`✅ GPIO ${this.gpioNumber} инициализирован как ${direction}`);
            return true;
        } catch (error) {
            console.error(`❌ Ошибка инициализации GPIO ${this.gpioNumber}:`, error.message);
            return false;
        }
    }

    /**
     * Изменение состояния GPIO
     * @param {number|boolean} state - 1/true для состояния 1, 0/false для состояния 0
     */
    setState(state) {
        try {
            if (!this.isInitialized || this.currentDirection !== 'out') {
                if (!this.initialize('out')) {
                    throw new Error('Не удалось инициализировать GPIO для записи');
                }
            }

            const normalizedState = this.normalizeState(state);
            this.gpio.writeSync(normalizedState);

            console.log(`🔄 GPIO ${this.gpioNumber} установлен в состояние: ${normalizedState}`);

            return true;
        } catch (error) {
            console.error(`❌ Ошибка изменения состояния GPIO ${this.gpioNumber}:`, error.message);
            return false;
        }
    }

    /**
     * Чтение текущего состояния GPIO
     * @returns {number} - 1 или 0 (0 при ошибке)
     */
    getState() {
        try {
            if (!this.isInitialized || this.currentDirection !== 'in') {
                if (!this.initialize('in')) {
                    throw new Error('Не удалось инициализировать GPIO для чтения');
                }
            }

            const state = this.gpio.readSync();
            console.log(`📖 GPIO ${this.gpioNumber} текущее состояние: ${state}`);

            return state;
        } catch (error) {
            console.error(`❌ Ошибка чтения состояния GPIO ${this.gpioNumber}:`, error.message);
            return 0; // Возвращаем 0 вместо null при ошибке
        }
    }

    /**
     * Переключение состояния GPIO (toggle)
     */
    toggleState() {
        try {
            const currentState = this.getState();
            const newState = currentState === 1 ? 0 : 1;
            return this.setState(newState);
        } catch (error) {
            console.error(`❌ Ошибка переключения состояния GPIO ${this.gpioNumber}:`, error.message);
            return false;
        }
    }

    /**
     * Установка состояния 1
     */
    setHigh() {
        return this.setState(1);
    }

    /**
     * Установка состояния 0
     */
    setLow() {
        return this.setState(0);
    }

    /**
     * Безопасное закрытие GPIO ресурсов
     */
    cleanup() {
        try {
            if (this.gpio && this.isInitialized) {
                this.gpio.unexport();
                console.log(`🧹 GPIO ${this.gpioNumber} ресурсы освобождены`);
            }
        } catch (error) {
            console.error(`❌ Ошибка при освобождении GPIO ${this.gpioNumber}:`, error.message);
        } finally {
            this.gpio = null;
            this.isInitialized = false;
            this.currentDirection = null;
        }
    }

    /**
     * Валидация номера GPIO
     */
    validateGpioNumber() {
        if (typeof this.gpioNumber !== 'number' || this.gpioNumber < 0) {
            throw new Error(`Некорректный номер GPIO: ${this.gpioNumber}`);
        }
    }

    /**
     * Валидация направления GPIO
     */
    validateDirection(direction) {
        if (!['in', 'out'].includes(direction)) {
            throw new Error(`Некорректное направление GPIO: ${direction}. Используйте 'in' или 'out'`);
        }
    }

    /**
     * Нормализация состояния к числовому значению
     */
    normalizeState(state) {
        if (typeof state === 'boolean') {
            return state ? 1 : 0;
        }
        if (typeof state === 'number') {
            return state > 0 ? 1 : 0;
        }
        if (typeof state === 'string') {
            const lowerState = state.toLowerCase();
            if (['1', 'true', 'on'].includes(lowerState)) {
                return 1;
            }
            if (['0', 'false', 'off'].includes(lowerState)) {
                return 0;
            }
        }
        throw new Error(`Некорректное состояние: ${state}. Используйте 1/0, true/false`);
    }

    /**
     * Получение информации о GPIO
     */
    getInfo() {
        return {
            gpioNumber: this.gpioNumber,
            isInitialized: this.isInitialized,
            direction: this.currentDirection,
            currentState: this.isInitialized && this.currentDirection === 'in' ? this.getState() : 0
        };
    }
}

module.exports = GPIOMeasure;
