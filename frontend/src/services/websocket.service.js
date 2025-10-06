
let sockets = {}; // Заменяем 'let socket = null;' на объект для хранения сокетов

import { ref } from 'vue';

// const testStatus = ref(''); // Эта переменная, возможно, больше не нужна или требует переосмысления для статуса по каждому тесту

let gpioSocket = null

export function connectGpioWebSocket(callback) {
    // Закрываем старое соединение если есть
    if (gpioSocket) {
        gpioSocket.close()
    }

    console.log('Подключаемся к GPIO WebSocket...')
    gpioSocket = new WebSocket('ws://localhost:8001/ws/gpio')

    gpioSocket.onopen = () => {
        console.log('✅ GPIO WebSocket подключен')
    }

    gpioSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)

            // Ловим только события изменения GPIO
            if (data.type === 'gpio_event') {
                console.log(`🔌 GPIO изменился: ${data.value}`)
                // Вызываем callback с данными
                if (callback) {
                    callback(data.value)
                }
            }
        } catch (e) {
            console.error('Ошибка парсинга:', e)
        }
    }

    gpioSocket.onerror = (error) => {
        console.error('❌ Ошибка WebSocket:', error)
    }

    gpioSocket.onclose = () => {
        console.log('🔌 GPIO WebSocket отключен')
    }
}

export function disconnectGpioWebSocket() {
    if (gpioSocket) {
        gpioSocket.close()
        gpioSocket = null
    }
}

export function connectWebSocket(test, dataStore) {
    const tests = dataStore.tests;
    const testId = test.testId;
    console.log(`Попытка подключения к WebSocket для test_id: ${testId}`);

    // Если сокет для этого testId уже существует и открыт, закроем его перед созданием нового.
    if (sockets[testId] && sockets[testId].readyState === WebSocket.OPEN) {
        console.log(`Закрытие существующего WebSocket для test_id: ${testId}`);
        sockets[testId].onclose = null; // Предотвращаем срабатывание старого onclose
        sockets[testId].close();
    }

    const wsUrl = `ws://localhost:8001/ws/test-status/${testId}`;
    console.log(`Попытка подключения к WebSocket: ${wsUrl}`);
    const currentSocket = new WebSocket(wsUrl);
    sockets[testId] = currentSocket; // Сохраняем новый сокет в объекте

    currentSocket.onopen = () => {
        console.log(`WebSocket соединение установлено для test_id: ${testId}`);
        // testStatus.value = `Соединение для ${testId} установлено...`; // Можно обновить UI специфично для теста
    };

    currentSocket.onmessage = (event) => {
        try {
            console.log(`onmessage для ${testId}:`, event.data); // testId здесь из замыкания, правильный для этого сокета
            const eventData = JSON.parse(event.data);
            const data = {
                testId: eventData.test_id, // Это test_id из сообщения
                status: eventData.status,
                timeStart: eventData.time_start,
                updatedAt: eventData.updated_at,
                timeEnd: eventData.time_end,
                result: eventData.result,
            };

            console.log("data from message: ", data);

            // Находим тест в хранилище, используя testId из сообщения
            const testToUpdate = tests.find(t => t.testId === data.testId);

            if (testToUpdate) {
                // Убедимся, что testId из сообщения совпадает с testId, для которого был открыт этот сокет.
                // Это важно, если сообщения могут быть ошибочно маршрутизированы,
                // или если один сокет предназначен для обработки сообщений для нескольких test_id (что здесь не так).
                if (data.testId === testId) { // testId здесь - это testId, для которого был создан currentSocket
                    testToUpdate.status = data.status;
                    testToUpdate.timeStart = data.timeStart;
                    testToUpdate.updatedAt = data.updatedAt;
                    testToUpdate.timeEnd = data.timeEnd;
                    testToUpdate.result = data.result;
                    console.log(`Статус теста ${data.testId} обновлен: ${data.status}`);
                } else {
                    console.warn(`Получено сообщение для test_id ${data.testId} на сокете для ${testId}. Обновление пропущено, так как testId не совпали.`);
                }
                console.log("dataStore.tests after update: ", tests); // Добавим эту строку для отладки
            } else {
                console.warn(`Тест с testId ${data.testId} (из сообщения) не найден в dataStore.tests.`);
            }

        } catch (e) {
            console.error(`Ошибка парсинга JSON из WebSocket для ${testId}:`, e, event.data);
        }
    };

    currentSocket.onerror = (error) => {
        console.error(`Ошибка WebSocket для ${testId}:`, error);
        const testToUpdate = tests.find(t => t.testId === testId);
        if (testToUpdate) {
            // Можно обновить статус теста в dataStore, чтобы отразить ошибку WebSocket
            // testToUpdate.status = 'error_ws'; // Например
        }
    };

    currentSocket.onclose = (event) => {
        console.log(`WebSocket соединение для ${testId} закрыто:`, event.reason, event.code);
        // testStatus.value = `Соединение WebSocket для ${testId} закрыто`;
        // Удаляем сокет из нашего объекта, только если это тот самый сокет, который мы отслеживаем
        if (sockets[testId] === currentSocket) {
            delete sockets[testId];
        }
    };
}

// Функция для закрытия определенного WebSocket соединения
export function disconnectWebSocket(testId) {
    if (sockets[testId]) {
        console.log(`Закрытие WebSocket для test_id: ${testId} по запросу.`);
        sockets[testId].close();
        // Обработчик onclose сам удалит его из объекта sockets
    }
}

// Функция для закрытия всех WebSocket соединений
export function disconnectAllWebSockets() {
    console.log("Закрытие всех WebSocket соединений.");
    for (const id in sockets) {
        if (sockets[id]) {
            sockets[id].onclose = null; // Предотвращаем множественные логи и попытки удаления
            sockets[id].close();
        }
    }
    sockets = {}; // Очищаем коллекцию
}