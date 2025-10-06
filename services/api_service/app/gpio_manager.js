const Gpio = require('onoff').Gpio;

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

// Использование с GPIO номером 33 (gpiochip1 line 1)
const monitor = new GPIOMonitor(33);
monitor.start();

process.on('SIGINT', () => {
    monitor.stop();
    process.exit();
});