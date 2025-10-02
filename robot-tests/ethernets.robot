*** Settings ***
Documentation     Тестирование интерфейсов Cisco с интеграцией во фронтенд
Library           SSHLibrary
Library           Collections
Library           DateTime
Library           OperatingSystem
Library           String

*** Variables ***
${SWITCH_IP}      192.168.1.209
${USERNAME}       cisco
${PASSWORD}       cisco
${ENABLE_PASSWORD}    cisco
${TARGET_IP}      192.168.1.1
@{INTERFACES}     GigabitEthernet1    GigabitEthernet2    GigabitEthernet3    GigabitEthernet4
${JSON_PATH}      ${CURDIR}${/}ethernets.json

*** Test Cases ***
Test Cisco Interfaces Connectivity
    [Documentation]    Проверка подключения через последовательное включение интерфейсов
    ${start_time}=    Get Current Date
    
    # Инициализируем начальный прогресс
    Initialize Test Progress
    
    Open SSH Connection To Switch
    Disbale Logging Console
    Disable All Interfaces
    ${test_results}=    Test Interfaces Sequence
    ${end_time}=    Get Current Date
    ${execution_time}=    Subtract Date From Date    ${end_time}    ${start_time}
    ${execution_time}=    Convert Time    ${execution_time}    verbose

    # Enable All Interfaces
    Enable Interface    GigabitEthernet3
    Generate Frontend Report    ${test_results}    ${execution_time}
    [Teardown]    Close All Connections

*** Keywords ***
Open SSH Connection To Switch
    [Documentation]    Универсальное подключение к Cisco с динамическим определением промпта
    # 1. Открываем соединение без промпта
    TRY
        Log    Попытка подключения к ${SWITCH_IP}...
        Open Connection    ${SWITCH_IP}    timeout=30s
        Log    SSH соединение установлено успешно
    EXCEPT    AS    ${error}
        Log    ОШИБКА: Не удалось установить SSH соединение к ${SWITCH_IP}: ${error}    ERROR
        Fail    SSH подключение не удалось. Проверьте доступность устройства и настройки сети.
    END
    
    # 2. Логин с обработкой разных сценариев
    TRY
        Log    Попытка аутентификации пользователя ${USERNAME}...
        ${login_output}=    Login    ${USERNAME}    ${PASSWORD}
        Log    Аутентификация прошла успешно
    EXCEPT    AS    ${error}
        Log    ОШИБКА: Аутентификация не удалась: ${error}    ERROR
        Fail    Неверные учетные данные или проблема с аутентификацией.
    END
    ${prompt}=    Set Variable    ${EMPTY}
    
    # 3. Динамическое определение промпта
    ${raw_output}=    Read    delay=0.5s
    ${prompt}=    Get Regexp Matches    ${raw_output}    ([>#]\\\\s?$)    flags=IGNORECASE | MULTILINE
    ${prompt}=    Set Variable If    "${prompt}" != "[]"    ${prompt[0]}    #
    
    # 4. Устанавливаем обнаруженный промпт
    Set Client Configuration    prompt=${prompt}
    Log    Установлен промпт: ${prompt}
    
    # 5. Отключаем постраничный вывод
    # Write    terminal length 0
    # ${discard}=    Read Until Prompt
    
    # 6. Переход в enable mode (если требуется)
    ${enable_status}=    Run Keyword And Return Status
    ...    Should Contain    ${prompt}    >
    
    IF    ${enable_status}
        Write    enable
        ${output}=    Read Until    Password:    10s
        Write    ${ENABLE_PASSWORD}
        ${output}=    Read Until Prompt
        Set Client Configuration    prompt=#    # Обновляем промпт для привилегированного режима
    END
    
    # 7. Выполняем тестовую команду
    Write    show version
    ${output}=    Read Until  HW version
  
    # 8. Проверки
    Should Contain    ${output}    HW version

Disable All Interfaces
    [Documentation]    Отключение всех целевых интерфейсов
    FOR    ${interface}    IN    @{INTERFACES}
        # Disable Interface    ${interface}
        Write    configure terminal
        Write    interface range GigabitEthernet1 - 4
        Write    shutdown
        Write    end
    END

Enable All Interfaces
    [Documentation]    Отключение всех целевых интерфейсов
    FOR    ${interface}    IN    @{INTERFACES}
        Write    configure terminal
        Write    interface range GigabitEthernet1 - 4
        Write    no shutdown
        Write    end
    END

Disbale Logging Console
    [Documentation]    Отключение логов в консоли
    Write    configure terminal
    Write    logging synchronous
    Write    no logging console
    Write    end

Disable Interface
    [Arguments]    ${interface}
    [Documentation]    Отключение конкретного интерфейса
    Write    configure terminal
    Write    interface ${interface}
    Write    shutdown
    Write    end
    Sleep    1s    # Даем время на применение изменений

Enable Interface
    [Arguments]    ${interface}
    [Documentation]    Включение конкретного интерфейса
    Write    configure terminal
    Write    interface ${interface}
    Write    no shutdown
    Write    end
    Sleep    1s    # Даем время интерфейсу подняться

Test Interfaces Sequence
    [Documentation]    Последовательное тестирование интерфейсов с промежуточным расчетом прогресса
    @{results}=    Create List
    ${previous_interface}=    Set Variable    ${None}
    ${interface_index}=    Set Variable    0
    ${total_interfaces}=    Get Length    ${INTERFACES}
    
    FOR    ${interface}    IN    @{INTERFACES}
        ${interface_index}=    Evaluate    ${interface_index} + 1
        Log    Тестирование интерфейса ${interface} (${interface_index}/${total_interfaces})
        
        # Включаем текущий интерфейс
        Enable Interface    ${interface}
        
        # Проверяем статус интерфейса
        ${status}=    Get Interface Status    ${interface}
        
        # Выключаем предыдущий интерфейс (если есть)
        Run Keyword If    '${previous_interface}' != '${None}'
        ...    Disable Interface    ${previous_interface}
        
        # Выполняем ping тест
        ${ping_result}=    Ping Target IP
        ${interface_data}=    Create Dictionary
        ...    name=${interface}
        ...    status=${status}
        ...    ping_result=${ping_result['status']}
        ...    packet_loss=${ping_result['packet_loss']}
        ...    response_time=${ping_result['response_time']}
        
        Append To List    ${results}    ${interface_data}
        
        # Вычисляем и сохраняем промежуточный прогресс
        ${current_progress}=    Calculate Test Progress    ${results}    ${interface_index}    ${total_interfaces}
        Save Intermediate Progress    ${results}    ${current_progress}    ${interface_index}    ${total_interfaces}
        
        Set Test Variable    ${previous_interface}    ${interface}
        Sleep    5s    # Пауза между операциями
    END
    
    # Отключаем последний интерфейс после теста
    Disable Interface    ${previous_interface}
    
    RETURN    ${results}

Get Interface Status
    [Arguments]    ${interface}
    [Documentation]    Получение статуса интерфейса

    Set Client Configuration    prompt=#
    Read    delay=0.5s
    
    Write    show interfaces status ${interface}
    ${output}=    Read Until Prompt
    
    # Теперь ищем просто "Up" или "Down"
    ${match}=    Get Regexp Matches    ${output}    \\\\b(Up|Down)\\\\b    flags=IGNORECASE

    # Если найдено — определяем статус
    IF    '${match}' != '[]'
        ${status}=    Set Variable If    '${match}[0]' == 'Up'    enabled    disabled
    ELSE
        ${status}=    Set Variable    unknown
    END
    
    RETURN    ${status}



Ping Target IP
    [Documentation]    Выполнение ping теста с парсингом результатов
    Write    ping ${TARGET_IP} count 4
    ${output}=    Read Until Prompt    # Ждём до конца вывода
    ${ping_data}=    Parse Ping Output    ${output}
    RETURN    ${ping_data}

Parse Ping Output
    [Arguments]    ${output}
    [Documentation]    Парсинг результатов команды ping

    ${status}=    Set Variable    fail
    ${packet_loss}=    Set Variable    100%
    ${response_time}=    Set Variable    N/A

    # Парсим процент потерь пакетов
    ${loss_match}=    Get Regexp Matches    ${output}    (\\\\d+)% packet loss
    Log    loss_match = ${loss_match}

    IF    '${loss_match}' != '[]'
        ${match_length}=    Get Length    ${loss_match[0]}
        IF    ${match_length} > 0
            # Берём первую группу (число перед %)
            ${packet_loss_percent}=    Set Variable    ${loss_match[0][0]}   # ← Вот здесь ключевой момент!

            ${packet_loss}=    Set Variable    ${packet_loss_percent}%
        END

        # Теперь можно безопасно преобразовать в число
        ${success_packets}=    Evaluate    4 - (4 * int($packet_loss_percent) // 100)
        ${status}=    Set Variable If    ${success_packets} > 0    success    fail
    END

    # Парсим время ответа
    ${time_match}=    Get Regexp Matches    ${output}    min/avg/max = (\\\\d+)/(\\\\d+)/(\\\\d+)
    IF    '${time_match}' != '[]'
        ${match_length}=    Get Length    ${time_match[0]}
        IF    ${match_length} > 1
            ${response_time}=    Set Variable    ${time_match[0][1]}ms
        END
    END

    ${result}=    Create Dictionary
    ...    status=${status}
    ...    packet_loss=${packet_loss}
    ...    response_time=${response_time}

    RETURN    ${result}

Calculate Test Progress
    [Arguments]    ${interfaces_results}    ${current_interface_index}=${None}    ${total_interfaces}=${None}
    [Documentation]    Вычисляет прогресс Ethernet тестов на основе результатов
    
    ${total_progress}=    Set Variable    0
    ${interface_count}=    Get Length    ${interfaces_results}
    
    # Если переданы параметры текущего интерфейса, используем их для более точного расчета
    IF    '${current_interface_index}' != '${None}' and '${total_interfaces}' != '${None}'
        # Базовый прогресс по количеству протестированных интерфейсов (60%)
        ${base_progress}=    Evaluate    (${current_interface_index} * 60) // ${total_interfaces}
        
        # Дополнительный прогресс по качеству тестов (40%)
        ${quality_progress}=    Set Variable    0
        FOR    ${interface_data}    IN    @{interfaces_results}
            ${interface_quality}=    Set Variable    0
            
            # Статус интерфейса: 50% от качества
            ${status}=    Get From Dictionary    ${interface_data}    status    default=unknown
            IF    '${status}' == 'enabled'
                ${interface_quality}=    Evaluate    ${interface_quality} + 50
            END
            
            # Успешный ping: 50% от качества
            ${ping_result}=    Get From Dictionary    ${interface_data}    ping_result    default=fail
            IF    '${ping_result}' == 'success'
                ${interface_quality}=    Evaluate    ${interface_quality} + 50
            END
            
            ${quality_progress}=    Evaluate    ${quality_progress} + ${interface_quality}
        END
        
        # Нормализуем качественный прогресс
        ${max_quality}=    Evaluate    ${interface_count} * 100
        ${normalized_quality}=    Set Variable If    ${max_quality} > 0    (${quality_progress} * 40) // ${max_quality}    0
        
        ${total_progress}=    Evaluate    ${base_progress} + ${normalized_quality}
    ELSE
        # Старая логика для обратной совместимости
        FOR    ${interface_data}    IN    @{interfaces_results}
            ${interface_progress}=    Set Variable    0
            
            # Статус интерфейса: 25%
            ${status}=    Get From Dictionary    ${interface_data}    status    default=unknown
            IF    '${status}' == 'enabled'
                ${interface_progress}=    Evaluate    ${interface_progress} + 25
            END
            
            # Успешный ping: 75%
            ${ping_result}=    Get From Dictionary    ${interface_data}    ping_result    default=fail
            IF    '${ping_result}' == 'success'
                ${interface_progress}=    Evaluate    ${interface_progress} + 75
            END
            
            ${total_progress}=    Evaluate    ${total_progress} + ${interface_progress}
        END
        
        # Вычисляем средний прогресс
        ${max_progress}=    Evaluate    ${interface_count} * 100
        ${total_progress}=    Set Variable If    ${max_progress} > 0    ${total_progress * 100 // ${max_progress}}    0
    END
    
    # Ограничиваем прогресс до 100%
    ${progress_percent}=    Set Variable If    ${total_progress} > 100    100    ${total_progress}
    
    RETURN    ${progress_percent}

Save Intermediate Progress
    [Arguments]    ${current_results}    ${progress}    ${current_interface}    ${total_interfaces}
    [Documentation]    Сохраняет промежуточный прогресс тестирования в JSON файл
    
    # Определяем статус выполнения
    ${test_status}=    Set Variable    RUNNING
    ${completed_interfaces}=    Get Length    ${current_results}
    
    # Проверяем, есть ли неудачные тесты среди завершенных
    ${has_failures}=    Set Variable    ${False}
    FOR    ${intf}    IN    @{current_results}
        IF    '${intf['ping_result']}' == 'fail'
            ${has_failures}=    Set Variable    ${True}
            Exit For Loop
        END
    END
    
    # Формируем детали выполнения
    ${details}=    Set Variable    Выполнено ${current_interface}/${total_interfaces} интерфейсов
    IF    ${has_failures}
        ${details}=    Set Variable    ${details} (обнаружены проблемы)
    END
    
    # Создаем промежуточный отчет
    ${intermediate_report}=    Create Dictionary
    ...    test_status=${test_status}
    ...    progress=${progress}
    ...    completed_interfaces=${completed_interfaces}
    ...    total_interfaces=${total_interfaces}
    ...    interfaces=${current_results}
    ...    details=${details}
    ...    timestamp=${EMPTY}
    
    # Добавляем временную метку
    ${current_time}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    Set To Dictionary    ${intermediate_report}    timestamp    ${current_time}
    
    # Сохраняем промежуточный JSON файл
    ${json_str}=    Evaluate    json.dumps(${intermediate_report}, indent=4, ensure_ascii=False)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8
    Log    Промежуточный прогресс сохранен: ${progress}% (${current_interface}/${total_interfaces})

Initialize Test Progress
    [Documentation]    Инициализирует начальное состояние прогресса тестирования
    
    ${total_interfaces}=    Get Length    ${INTERFACES}
    
    # Создаем начальный отчет
    ${initial_report}=    Create Dictionary
    ...    test_status=STARTING
    ...    progress=0
    ...    completed_interfaces=0
    ...    total_interfaces=${total_interfaces}
    ...    interfaces=@{EMPTY}
    ...    details=Инициализация тестирования ${total_interfaces} интерфейсов
    ...    timestamp=${EMPTY}
    
    # Добавляем временную метку
    ${current_time}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    Set To Dictionary    ${initial_report}    timestamp    ${current_time}
    
    # Сохраняем начальный JSON файл
    ${json_str}=    Evaluate    json.dumps(${initial_report}, indent=4, ensure_ascii=False)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8
    Log    Инициализирован прогресс тестирования: 0% (0/${total_interfaces})

Generate Frontend Report
    [Arguments]    ${results}    ${execution_time}
    [Documentation]    Генерация финального JSON отчета для фронтенда
    
    # Определяем общий статус теста
    ${test_status}=    Set Variable    PASS
    FOR    ${intf}    IN    @{results}
        IF    '${intf['ping_result']}' == 'fail'
            ${test_status}=    Set Variable    FAIL
            Exit For Loop
        END
    END
    
    # Определяем result на основе ping_result всех портов
    ${all_ports_success}=    Set Variable    ${True}
    FOR    ${intf}    IN    @{results}
        IF    '${intf['ping_result']}' != 'success'
            ${all_ports_success}=    Set Variable    ${False}
            Exit For Loop
        END
    END
    
    ${result}=    Set Variable If    ${all_ports_success}    success    fail
    
    ${details}=    Set Variable If
    ...    '${test_status}' == 'PASS'    Все интерфейсы прошли проверку
    ...    Обнаружены проблемы с подключением
    
    # Вычисляем финальный прогресс (100% для завершенных тестов)
    ${progress}=    Calculate Test Progress    ${results}
    ${total_interfaces}=    Get Length    ${INTERFACES}
    ${completed_interfaces}=    Get Length    ${results}
    
    # Добавляем временную метку
    ${current_time}=    Get Current Date    result_format=%Y-%m-%d %H:%M:%S
    
    # Формируем финальный отчет
    ${final_report}=    Create Dictionary
    ...    test_status=${test_status}
    ...    execution_time=${execution_time}
    ...    progress=${progress}
    ...    completed_interfaces=${completed_interfaces}
    ...    total_interfaces=${total_interfaces}
    ...    interfaces=${results}
    ...    details=${details}
    ...    timestamp=${current_time}
    ...    result=${result}
    
    # Сохраняем в JSON файл
    ${json_str}=    Evaluate    json.dumps(${final_report}, indent=4, ensure_ascii=False)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8
    Log    Финальный JSON отчет создан: ${JSON_PATH} (Прогресс: ${progress}%)