*** Settings ***
Documentation    Тесты для сброса GPIO пинов в определенное состояние
Library          Process
Library          OperatingSystem
Library          Collections
Library          gpio_utils.GPIOLibrary

*** Variables ***
${GPIO_RESET_SCRIPT}    ${CURDIR}/../services/gpio_reset_example.js
${NODE_COMMAND}         node

*** Test Cases ***
Test GPIO Reset Class Auto Initialization
    [Documentation]    Тестирует автоматическую инициализацию класса GPIOReset
    [Tags]             gpio    reset    auto-init    hardware
    
    Log    🚀 Начинаем тест автоматической инициализации GPIOReset
    
    # Используем новую библиотеку для тестирования
    ${result} =    Reset GPIO Pins    timeout=30
    
    Log    📋 Результат автоматической инициализации:
    Log    ${result}
    
    # Проверяем успешность выполнения
    Should Be True    ${result['success']}
    ...    msg=Автоматическая инициализация GPIO завершилась с ошибкой: ${result.get('stderr', 'Неизвестная ошибка')}
    
    # Проверяем, что в выводе есть сообщение об инициализации
    Should Contain    ${result['stdout']}    Создание экземпляра GPIOReset
    ...    msg=Не найдено сообщение о создании экземпляра GPIOReset
    
    Should Contain    ${result['stdout']}    инициализация завершена успешно
    ...    msg=Не найдено сообщение об успешной инициализации
    
    Log    ✅ Тест автоматической инициализации GPIOReset прошел успешно

Test GPIO Reset Function
    [Documentation]    Тестирует функцию сброса GPIO пинов (обратная совместимость)
    [Tags]             gpio    reset    hardware
    
    Log    🚀 Начинаем тест сброса GPIO пинов
    
    # Запускаем скрипт сброса GPIO
    ${result} =    Run Process    ${NODE_COMMAND}    ${GPIO_RESET_SCRIPT}
    ...            timeout=30s    shell=True
    
    Log    📋 Результат выполнения скрипта:
    Log    ${result.stdout}
    
    # Проверяем, что скрипт выполнился успешно
    Should Be Equal As Integers    ${result.rc}    0    
    ...    msg=Скрипт сброса GPIO завершился с ошибкой: ${result.stderr}
    
    # Проверяем, что в выводе есть сообщение об автоматической инициализации
    Should Contain    ${result.stdout}    Автоматическая инициализация
    ...    msg=Не найдено сообщение об автоматической инициализации GPIO
    
    Log    ✅ Тест сброса GPIO пинов прошел успешно

Test GPIO Reset With Detailed Output
    [Documentation]    Тестирует функцию сброса GPIO с детальным выводом
    [Tags]             gpio    reset    detailed    hardware
    
    Log    🔍 Начинаем детальный тест сброса GPIO пинов
    
    # Запускаем скрипт с детальным выводом
    ${result} =    Run Process    ${NODE_COMMAND}    ${GPIO_RESET_SCRIPT}
    ...            timeout=30s    shell=True
    
    Log    📋 Детальный результат выполнения:
    Log    ${result.stdout}
    
    # Проверяем успешное выполнение
    Should Be Equal As Integers    ${result.rc}    0
    ...    msg=Детальный скрипт завершился с ошибкой: ${result.stderr}
    
    # Проверяем наличие ключевых сообщений
    Should Contain    ${result.stdout}    Начинаем сброс GPIO пинов
    Should Contain    ${result.stdout}    GPIO 8 настроен как INPUT
    Should Contain    ${result.stdout}    GPIO 10 настроен как OUTPUT
    Should Contain    ${result.stdout}    GPIO 11 настроен как OUTPUT
    Should Contain    ${result.stdout}    GPIO 12 настроен как OUTPUT
    Should Contain    ${result.stdout}    GPIO 13 настроен как OUTPUT
    Should Contain    ${result.stdout}    GPIO 15 настроен как OUTPUT
    Should Contain    ${result.stdout}    Все GPIO пины успешно настроены
    
    Log    ✅ Детальный тест прошел успешно

Test GPIO Reset With Testing
    [Documentation]    Тестирует функцию сброса GPIO с последующим тестированием
    [Tags]             gpio    reset    testing    hardware
    
    Log    🧪 Начинаем тест с проверкой функциональности GPIO
    
    # Запускаем скрипт с тестированием
    ${result} =    Run Process    ${NODE_COMMAND}    ${GPIO_RESET_SCRIPT}    test
    ...            timeout=45s    shell=True
    
    Log    📋 Результат тестирования:
    Log    ${result.stdout}
    
    # Проверяем успешное выполнение
    Should Be Equal As Integers    ${result.rc}    0
    ...    msg=Тестовый скрипт завершился с ошибкой: ${result.stderr}
    
    # Проверяем наличие тестовых сообщений
    Should Contain    ${result.stdout}    Тестирование GPIO после сброса
    Should Contain    ${result.stdout}    Тестирование GPIO 10
    Should Contain    ${result.stdout}    Чтение состояния GPIO 8
    
    Log    ✅ Тест с проверкой функциональности прошел успешно

Verify GPIO Configuration
    [Documentation]    Проверяет правильность конфигурации GPIO пинов
    [Tags]             gpio    verification    hardware
    
    Log    🔍 Проверка конфигурации GPIO пинов
    
    # Создаем простой Node.js скрипт для проверки
    ${check_script} =    Set Variable    
    ...    const { resetSpecificGPIOs, cleanupGPIOs } = require('./services/gpio_manager');
    ...    const result = resetSpecificGPIOs();
    ...    if (result.success) {
    ...        result.gpioInstances.forEach(gpio => {
    ...            const info = gpio.getInfo();
    ...            console.log(`GPIO_${info.pin}_${info.direction}_${info.state}`);
    ...        });
    ...        cleanupGPIOs(result.gpioInstances);
    ...    }
    
    # Записываем скрипт во временный файл
    Create File    ${TEMPDIR}/gpio_check.js    ${check_script}
    
    # Выполняем проверку
    ${result} =    Run Process    ${NODE_COMMAND}    ${TEMPDIR}/gpio_check.js
    ...            timeout=20s    shell=True    cwd=${CURDIR}/..
    
    Log    📋 Результат проверки конфигурации:
    Log    ${result.stdout}
    
    # Проверяем успешное выполнение
    Should Be Equal As Integers    ${result.rc}    0
    ...    msg=Проверка конфигурации завершилась с ошибкой: ${result.stderr}
    
    # Проверяем правильность конфигурации
    Should Contain    ${result.stdout}    GPIO_8_in_    msg=GPIO 8 должен быть настроен как INPUT
    Should Contain    ${result.stdout}    GPIO_10_out_0    msg=GPIO 10 должен быть OUTPUT со значением 0
    Should Contain    ${result.stdout}    GPIO_11_out_0    msg=GPIO 11 должен быть OUTPUT со значением 0
    Should Contain    ${result.stdout}    GPIO_12_out_0    msg=GPIO 12 должен быть OUTPUT со значением 0
    Should Contain    ${result.stdout}    GPIO_13_out_0    msg=GPIO 13 должен быть OUTPUT со значением 0
    Should Contain    ${result.stdout}    GPIO_15_out_0    msg=GPIO 15 должен быть OUTPUT со значением 0
    
    # Удаляем временный файл
    Remove File    ${TEMPDIR}/gpio_check.js
    
    Log    ✅ Проверка конфигурации прошла успешно

Test GPIO Using Library
    [Documentation]    Тестирует GPIO используя специальную библиотеку
    [Tags]             gpio    library    reset    hardware
    
    Log    📚 Тестирование GPIO с использованием библиотеки
    
    # Ожидаем готовности GPIO системы
    Wait For GPIO Ready    max_wait_time=10
    
    # Сбрасываем GPIO пины
    ${output} =    Reset GPIO Pins    timeout=30
    Log    📋 Результат сброса GPIO: ${output}
    
    # Проверяем конфигурацию каждого пина
    Verify GPIO Pin Configuration    8    in
    Verify GPIO Pin Configuration    10   out    0
    Verify GPIO Pin Configuration    11   out    0
    Verify GPIO Pin Configuration    12   out    0
    Verify GPIO Pin Configuration    13   out    0
    Verify GPIO Pin Configuration    15   out    0
    
    # Получаем сводку состояния
    ${status_summary} =    Get GPIO Status Summary
    Log    ${status_summary}
    
    Log    ✅ Тест с библиотекой прошел успешно

Test GPIO Functionality Using Library
    [Documentation]    Тестирует функциональность GPIO используя библиотеку
    [Tags]             gpio    library    functionality    hardware
    
    Log    🔧 Тестирование функциональности GPIO с библиотекой
    
    # Ожидаем готовности системы
    Wait For GPIO Ready    max_wait_time=10
    
    # Тестируем функциональность
    ${output} =    Test GPIO Functionality    timeout=45
    Log    📋 Результат тестирования функциональности: ${output}
    
    # Проверяем конфигурацию после тестирования
    ${configurations} =    Check GPIO Configuration
    Log    📊 Конфигурации GPIO: ${configurations}
    
    # Получаем финальную сводку
    ${final_summary} =    Get GPIO Status Summary
    Log    ${final_summary}
    
    Log    ✅ Тест функциональности с библиотекой прошел успешно

*** Keywords ***
Setup GPIO Environment
    [Documentation]    Подготавливает окружение для тестов GPIO
    Log    🔧 Подготовка окружения для тестов GPIO
    
    # Проверяем наличие необходимых файлов
    File Should Exist    ${GPIO_RESET_SCRIPT}    msg=Скрипт сброса GPIO не найден
    File Should Exist    ${CURDIR}/../services/gpio_manager.js    msg=GPIO Manager не найден
    File Should Exist    ${CURDIR}/../services/gpio_measure.js    msg=GPIO Measure не найден

Cleanup GPIO Environment
    [Documentation]    Очищает окружение после тестов GPIO
    Log    🧹 Очистка окружения после тестов GPIO
    
    # Здесь можно добавить дополнительную очистку при необходимости
    Log    Очистка завершена