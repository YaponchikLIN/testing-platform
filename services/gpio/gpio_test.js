const { GPIOReset } = require('./gpio_manager');

/**
 * Заглушка функции измерения вольтажа
 * В будущем будет заменена на реальную библиотеку uni-t ut803
 * @returns {Promise<boolean>} Результат измерения (всегда true для заглушки)
 */
async function measureVoltage() {
    console.log('🔬 Начинаем измерение вольтажа...');
    console.log('⏳ Ожидание 5 секунд (заглушка)...');

    // Заглушка с таймаутом 5 секунд
    await sleep(5000);

    console.log('✅ Измерение вольтажа завершено (заглушка)');
    return true;
}

/**
 * Основная функция тестирования GPIO
 * Для каждого outputPin выполняет цикл: установка в 1 -> измерение вольтажа -> установка в 0
 * @returns {Promise<boolean>} Результат теста
 */
async function runGPIOTest() {
    console.log('🚀 Запуск GPIO теста');
    console.log('====================');

    try {
        // Инициализируем GPIOReset
        console.log('🔧 Инициализация GPIO системы...');
        const gpioReset = new GPIOReset();

        // Получаем список выходных пинов
        const outputPins = gpioReset.outputPins; // [32, 36, 97, 39, 40]
        console.log(`📌 Выходные пины: ${outputPins.join(', ')}`);
        console.log(`🔄 Будет выполнен цикл для каждого пина: 1 -> измерение -> 0`);

        // Тестируем каждый пин по очереди
        for (let i = 0; i < outputPins.length; i++) {
            const pin = outputPins[i];
            console.log(`\n🔧 Тестирование GPIO ${pin} (${i + 1}/${outputPins.length})`);
            console.log('─'.repeat(40));

            // 1. Установка пина в состояние 1
            console.log(`  📤 Установка GPIO ${pin} в состояние 1`);
            const setHighResult = gpioReset.setOutputPin(pin, 1);
            
            if (!setHighResult) {
                console.error(`❌ Ошибка установки GPIO ${pin} в состояние 1`);
                return false;
            }
            
            console.log(`  ✅ GPIO ${pin} установлен в состояние 1`);
            
            // 2. Выполнение измерения вольтажа
            console.log(`  🔬 Измерение вольтажа для GPIO ${pin}...`);
            const measurementResult = await measureVoltage();
            
            if (!measurementResult) {
                console.error(`❌ Ошибка при измерении вольтажа для GPIO ${pin}`);
                return false;
            }
            
            console.log(`  ✅ Измерение для GPIO ${pin} завершено успешно`);
            
            // 3. Установка пина в состояние 0
            console.log(`  📥 Установка GPIO ${pin} в состояние 0`);
            const setLowResult = gpioReset.setOutputPin(pin, 0);
            
            if (!setLowResult) {
                console.error(`❌ Ошибка установки GPIO ${pin} в состояние 0`);
                return false;
            }
            
            console.log(`  ✅ GPIO ${pin} установлен в состояние 0`);
            console.log(`  🎯 Тестирование GPIO ${pin} завершено`);
        }

        console.log('\n🎉 Все GPIO пины протестированы успешно!');
        console.log('✅ GPIO тест завершен успешно!');
        return true;

    } catch (error) {
        console.error('❌ Ошибка в GPIO тесте:', error.message);
        return false;
    }
}

/**
 * Функция задержки
 * @param {number} ms Время задержки в миллисекундах
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Обработчик завершения процесса
 */
process.on('SIGINT', () => {
    console.log('\n🛑 Получен сигнал завершения, остановка теста...');
    process.exit(0);
});

// Запуск теста, если файл выполняется напрямую
if (require.main === module) {
    console.log('🎯 Запуск GPIO теста...');
    runGPIOTest()
        .then(result => {
            if (result) {
                console.log('🎉 Тест завершен успешно!');
                process.exit(0);
            } else {
                console.log('❌ Тест завершен с ошибкой!');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('💥 Критическая ошибка:', error);
            process.exit(1);
        });
}

module.exports = {
    runGPIOTest,
    measureVoltage
};