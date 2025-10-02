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
${TARGET_IP}      192.168.1.2
@{INTERFACES}     GigabitEthernet1    GigabitEthernet2    GigabitEthernet3    GigabitEthernet4
${JSON_PATH}      ${CURDIR}${/}ethernets.json

*** Test Cases ***
Test Cisco Interfaces Connectivity
    [Documentation]    Проверка подключения через последовательное включение интерфейсов
    ${start_time}=    Get Current Date
    Open SSH Connection To Switch
    Disbale Logging Console
    Disable All Interfaces

    # Enable All Interfaces
    Enable All Interfaces
    [Teardown]    Close All Connections

*** Keywords ***
Open SSH Connection To Switch
    [Documentation]    Универсальное подключение к Cisco с динамическим определением промпта
    # 1. Открываем соединение без промпта
    Open Connection    ${SWITCH_IP}    timeout=10s
    
    # 2. Логин с обработкой разных сценариев
    ${login_output}=    Login    ${USERNAME}    ${PASSWORD}
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
    [Documentation]    Последовательное тестирование интерфейсов
    @{results}=    Create List
    ${previous_interface}=    Set Variable    ${None}
    
    FOR    ${interface}    IN    @{INTERFACES}
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
        # Берём первую группу (число перед %)
        ${packet_loss_percent}=    Set Variable    ${loss_match[0][0]}   # ← Вот здесь ключевой момент!

        ${packet_loss}=    Set Variable    ${packet_loss_percent}%

        # Теперь можно безопасно преобразовать в число
        ${success_packets}=    Evaluate    4 - (4 * int($packet_loss_percent) // 100)
        ${status}=    Set Variable If    ${success_packets} > 0    success    fail
    END

    # Парсим время ответа
    ${time_match}=    Get Regexp Matches    ${output}    min/avg/max = (\\\\d+)/(\\\\d+)/(\\\\d+)
    IF    '${time_match}' != '[]'
        ${response_time}=    Set Variable    ${time_match[0][1]}ms
    END

    ${result}=    Create Dictionary
    ...    status=${status}
    ...    packet_loss=${packet_loss}
    ...    response_time=${response_time}

    RETURN    ${result}

Calculate Test Progress
    [Arguments]    ${interfaces_results}
    [Documentation]    Вычисляет прогресс портов тестов на основе результатов
    
    ${total_progress}=    Set Variable    0
    ${interface_count}=    Get Length    ${interfaces_results}
    
    # Проходим по всем портам
    FOR    ${interface_data}    IN    @{interfaces_results}
        ${interface_progress}=    Set Variable    0
        
        # Статус порта: 30% (enabled/disabled)
        ${status}=    Get From Dictionary    ${interface_data}    status    default=unknown
        IF    '${status}' == 'enabled'
            ${interface_progress}=    Evaluate    ${interface_progress} + 30
        END
        
        # Успешный ping: 70%
        ${ping_result}=    Get From Dictionary    ${interface_data}    ping_result    default=fail
        IF    '${ping_result}' == 'success'
            ${interface_progress}=    Evaluate    ${interface_progress} + 70
        END
        
        ${total_progress}=    Evaluate    ${total_progress} + ${interface_progress}
    END
    
    # Вычисляем средний прогресс (максимум 100% на порт)
    ${max_progress}=    Evaluate    ${interface_count} * 100
    ${progress_percent}=    Set Variable If    ${max_progress} > 0    ${total_progress * 100 // ${max_progress}}    0
    
    # Ограничиваем прогресс до 100%
    ${progress_percent}=    Set Variable If    ${progress_percent} > 100    100    ${progress_percent}
    
    RETURN    ${progress_percent}

Generate Frontend Report
    [Arguments]    ${results}    ${execution_time}
    [Documentation]    Генерация JSON отчета для фронтенда
    
    # Определяем общий статус теста
    ${test_status}=    Set Variable    PASS
    FOR    ${intf}    IN    @{results}
        IF    '${intf['ping_result']}' == 'fail'
            ${test_status}=    Set Variable    FAIL
            Exit For Loop
        END
    END
    
    ${details}=    Set Variable If
    ...    '${test_status}' == 'PASS'    Все интерфейсы прошли проверку
    ...    Обнаружены проблемы с подключением
    
    # Вычисляем прогресс тестов
    ${progress}=    Calculate Test Progress    ${results}
    
    # Формируем финальный отчет
    ${final_report}=    Create Dictionary
    ...    test_status=${test_status}
    ...    execution_time=${execution_time}
    ...    interfaces=${results}
    ...    details=${details}
    ...    progress=${progress}
    
    # Сохраняем в JSON файл
    ${json_str}=    Evaluate    json.dumps(${final_report}, indent=4, ensure_ascii=False)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8
    Log    JSON отчет создан: ${JSON_PATH}