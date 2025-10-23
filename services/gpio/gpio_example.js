const GPIOMeasure = require('./gpio_measure');

// Пример использования класса GPIOMeasure для управления GPIO

async function demonstrateGPIOControl() {
    // Создаем экземпляр для GPIO пина 33
    const gpio = new GPIOMeasure(33);

    try {
        console.log('🚀 Демонстрация управления GPIO');
        console.log('================================');

        // Получаем информацию о GPIO
        console.log('\n📋 Информация о GPIO:');
        console.log(gpio.getInfo());

        // Устанавливаем HIGH состояние
        console.log('\n🔼 Установка HIGH состояния...');
        gpio.setHigh();
        await sleep(1000);

        // Устанавливаем LOW состояние
        console.log('\n🔽 Установка LOW состояния...');
        gpio.setLow();
        await sleep(1000);

        // Используем setState с различными форматами
        console.log('\n🔄 Тестирование различных форматов состояния...');

        gpio.setState(1);       // number
        await sleep(500);

        // Переключение состояния (toggle)
        console.log('\n🔀 Переключение состояния...');
        for (let i = 0; i < 3; i++) {
            gpio.toggleState();
            await sleep(500);
        }

        // Чтение состояния (переинициализация как input)
        console.log('\n📖 Чтение текущего состояния...');
        const currentState = gpio.getState();
        console.log(`Текущее состояние: ${currentState}`);

        // Получаем обновленную информацию
        console.log('\n📋 Обновленная информация о GPIO:');
        console.log(gpio.getInfo());

    } catch (error) {
        console.error('❌ Ошибка в демонстрации:', error.message);
    } finally {
        // Обязательно освобождаем ресурсы
        console.log('\n🧹 Освобождение ресурсов...');
        gpio.cleanup();
    }
}

// Пример работы с несколькими GPIO одновременно
async function demonstrateMultipleGPIO() {
    const gpio1 = new GPIOMeasure(18);
    const gpio2 = new GPIOMeasure(19);
    const gpio3 = new GPIOMeasure(20);

    try {
        console.log('\n🚀 Демонстрация работы с несколькими GPIO');
        console.log('==========================================');

        // Инициализируем все GPIO как выходы
        gpio1.initialize('out');
        gpio2.initialize('out');
        gpio3.initialize('out');

        // Создаем последовательность мигания
        console.log('\n💡 Последовательность мигания...');
        for (let cycle = 0; cycle < 3; cycle++) {
            // Включаем по очереди
            gpio1.setHigh();
            await sleep(200);
            gpio2.setHigh();
            await sleep(200);
            gpio3.setHigh();
            await sleep(200);

            // Выключаем по очереди
            gpio1.setLow();
            await sleep(200);
            gpio2.setLow();
            await sleep(200);
            gpio3.setLow();
            await sleep(200);
        }

    } catch (error) {
        console.error('❌ Ошибка в демонстрации множественных GPIO:', error.message);
    } finally {
        // Освобождаем все ресурсы
        console.log('\n🧹 Освобождение всех ресурсов...');
        gpio1.cleanup();
        gpio2.cleanup();
        gpio3.cleanup();
    }
}

// Вспомогательная функция для задержки
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Обработчик для корректного завершения при Ctrl+C
process.on('SIGINT', () => {
    console.log('\n\n🛑 Получен сигнал завершения...');
    process.exit(0);
});

// Запуск демонстрации
if (require.main === module) {
    console.log('🎯 Выберите демонстрацию:');
    console.log('1. Одиночный GPIO (по умолчанию)');
    console.log('2. Множественные GPIO');

    const mode = process.argv[2];

    if (mode === 'multi') {
        demonstrateMultipleGPIO();
    } else {
        demonstrateGPIOControl();
    }
}

module.exports = {
    demonstrateGPIOControl,
    demonstrateMultipleGPIO
};