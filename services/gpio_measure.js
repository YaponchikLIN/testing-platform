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
     * Изменение состояния GPIO (HIGH/LOW)
     * @param {number|boolean} state - 1/true для HIGH, 0/false для LOW
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
            
            const stateText = normalizedState === 1 ? 'HIGH' : 'LOW';
            console.log(`🔄 GPIO ${this.gpioNumber} установлен в состояние: ${stateText}`);
            
            return true;
        } catch (error) {
            console.error(`❌ Ошибка изменения состояния GPIO ${this.gpioNumber}:`, error.message);
            return false;
        }
    }

    /**
     * Чтение текущего состояния GPIO
     * @returns {number|null} - 1 для HIGH, 0 для LOW, null при ошибке
     */
    getState() {
        try {
            if (!this.isInitialized || this.currentDirection !== 'in') {
                if (!this.initialize('in')) {
                    throw new Error('Не удалось инициализировать GPIO для чтения');
                }
            }

            const state = this.gpio.readSync();
            const stateText = state === 1 ? 'HIGH' : 'LOW';
            console.log(`📖 GPIO ${this.gpioNumber} текущее состояние: ${stateText}`);
            
            return state;
        } catch (error) {
            console.error(`❌ Ошибка чтения состояния GPIO ${this.gpioNumber}:`, error.message);
            return null;
        }
    }

    /**
     * Переключение состояния GPIO (toggle)
     */
    toggleState() {
        try {
            const currentState = this.getState();
            if (currentState === null) {
                throw new Error('Не удалось прочитать текущее состояние');
            }

            const newState = currentState === 1 ? 0 : 1;
            return this.setState(newState);
        } catch (error) {
            console.error(`❌ Ошибка переключения состояния GPIO ${this.gpioNumber}:`, error.message);
            return false;
        }
    }

    /**
     * Установка HIGH состояния
     */
    setHigh() {
        return this.setState(1);
    }

    /**
     * Установка LOW состояния
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
            if (['high', '1', 'true', 'on'].includes(lowerState)) {
                return 1;
            }
            if (['low', '0', 'false', 'off'].includes(lowerState)) {
                return 0;
            }
        }
        throw new Error(`Некорректное состояние: ${state}. Используйте 1/0, true/false, 'high'/'low'`);
    }

    /**
     * Получение информации о GPIO
     */
    getInfo() {
        return {
            gpioNumber: this.gpioNumber,
            isInitialized: this.isInitialized,
            direction: this.currentDirection,
            currentState: this.isInitialized && this.currentDirection === 'in' ? this.getState() : null
        };
    }
}

// Устаревший метод для обратной совместимости
GPIOMeasure.prototype.gpioChangeState = function(state) {
    console.warn('⚠️  Метод gpioChangeState устарел. Используйте setState()');
    return this.setState(state);
};

module.exports = GPIOMeasure;
