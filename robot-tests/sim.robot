*** Settings ***
Documentation     Тестирование SIM-карт через ubus call mmm getStatus
Library           SSHLibrary
Library           Collections
Library           OperatingSystem
Library           String
Library           JSONLibrary

*** Variables ***
${ROUTER_IP}      192.168.1.1
${USERNAME}       root
${PASSWORD}       
${ENABLE_PASSWORD}    secret123    # Укажите пароль для enable, если требуется
${JSON_PATH}      ${CURDIR}${/}sim.json
${TARGET_IP}      8.8.8.8
# Установите в TRUE для включения детального логирования отладки
${DEBUG_MODE}     ${TRUE}

*** Test Cases ***
Test SIM Slots Status
    [Documentation]    Проверка активности SIM-карт и сетевой доступности
    
    # Безопасное подключение к роутеру
    ${connection_status}=    Run Keyword And Return Status    Open SSH Connection To Router
    IF    not ${connection_status}
        Log    Ошибка подключения к роутеру ${ROUTER_IP}
        ${error_result}=    Create Dictionary
        Set To Dictionary    ${error_result}    slot_1    Create Dictionary    error=connection_failed    active=no    connected=error
        Generate JSON Report    ${error_result}
        Fail    Не удалось подключиться к роутеру
    END
    
    ${results}=    Create Dictionary

    FOR    ${slot}    IN RANGE    1    2
        Log    Проверка SIM слота ${slot}
        
        # Безопасное получение статуса SIM
        ${status}=    Get SIM Status
        
        # Проверяем, есть ли state-failed-reason (ошибка SIM)
        ${has_error}=    Run Keyword And Return Status    Dictionary Should Contain Key    ${status}    state-failed-reason
        IF    ${has_error}
            Log    SIM ошибка: ${status['state-failed-reason']}
            # Добавляем стандартные поля для совместимости
            Set To Dictionary    ${status}    active    no
            Set To Dictionary    ${status}    connected    error
            Set To Dictionary    ${status}    ping_result    skipped
            Set To Dictionary    ${status}    packet_loss    N/A
            Set To Dictionary    ${status}    response_time    N/A
        ELSE
            # Проверяем и добавляем маршрут через wwan0 только если SIM активна
            IF    '${status["active"]}' == 'yes'
                ${route_status}=    Run Keyword And Return Status    Check And Add Default Route Through WWAN0
                IF    not ${route_status}
                    Log    Ошибка настройки маршрута через wwan0
                    Set To Dictionary    ${status}    route_error    true
                END
            END
            
            # Выполняем ping только если SIM активна и подключена
            IF    '${status["active"]}' == 'yes' and '${status["connected"]}' == 'connected'
                ${ping_status}=    Run Keyword And Return Status    Ping Target IP
                IF    ${ping_status}
                    ${ping_result}=    Ping Target IP
                    Set To Dictionary    ${status}    ping_result    ${ping_result['status']}
                    Set To Dictionary    ${status}    packet_loss    ${ping_result['packet_loss']}
                    Set To Dictionary    ${status}    response_time    ${ping_result['response_time']}
                ELSE
                    Log    Ошибка выполнения ping
                    Set To Dictionary    ${status}    ping_result    error
                    Set To Dictionary    ${status}    packet_loss    100%
                    Set To Dictionary    ${status}    response_time    N/A
                END
            ELSE
                Log    Пропуск ping - SIM неактивна или не подключена
                Set To Dictionary    ${status}    ping_result    skipped
                Set To Dictionary    ${status}    packet_loss    N/A
                Set To Dictionary    ${status}    response_time    N/A
            END
        END
        
        Set To Dictionary    ${results}    slot_${slot}    ${status}
    END

    Generate JSON Report    ${results}
    Log    Результаты сохранены в ${JSON_PATH}
    [Teardown]    Close All Connections

*** Keywords ***
Run Command And Parse Output
    [Arguments]    ${command}
    [Documentation]    Выполняет команду и парсит вывод JSON
    ${output}=    Execute Command    ${command}    return_stdout=True
    ${json_output}=    Evaluate    json.loads($output)    json
    RETURN    ${json_output}

Open SSH Connection To Router
    [Documentation]    Универсальное подключение к роутеру по SSH
    Open Connection    ${ROUTER_IP}    timeout=30s
    Login    ${USERNAME}    ${PASSWORD}

    # Автоопределение промпта
    ${raw_output}=    Read    delay=2s
    ${prompt}=    Get Regexp Matches    ${raw_output}    ([>#]\\\\s?$)    flags=IGNORECASE | MULTILINE
    ${prompt}=    Set Variable If    "${prompt}" != "[]"    ${prompt[0]}    #

    Set Client Configuration    prompt=${prompt}
    Log    Промпт установлен: ${prompt}

    # Переход в enable mode (если требуется)
    ${enable_status}=    Run Keyword And Return Status
    ...    Should Contain    ${prompt}    \>
    
    IF    ${enable_status}
        Write    enable
        ${output}=    Read Until    Password:    timeout=10s
        Write    ${ENABLE_PASSWORD}
        ${output}=    Read Until Prompt
        Set Client Configuration    prompt=#    # Обновляем промпт
    END

Switch To SIM Slot
    [Arguments]    ${slot_number}
    Write    ubus call mmm simswitch
    Sleep    5s    # Ждём переключения слота

Get SIM Status
    [Documentation]    Возвращает статус SIM и проверяет сетевой доступ
    
    # Безопасное выполнение команды ubus с обработкой ошибок
    ${status}=    Run Keyword And Return Status    Run Command And Parse Output    ubus call mmm getStatus
    IF    not ${status}
        Log    Ошибка выполнения команды ubus call mmm getStatus
        ${sim_status}=    Create Dictionary
        Set To Dictionary    ${sim_status}    active    no
        Set To Dictionary    ${sim_status}    connected    error
        Set To Dictionary    ${sim_status}    rssi    --
        Set To Dictionary    ${sim_status}    sim_slot    unknown
        Set To Dictionary    ${sim_status}    overall_status    ${False}
        Set To Dictionary    ${sim_status}    error    ubus command failed
        RETURN    ${sim_status}
    END
    
    ${output}=    Run Command And Parse Output    ubus call mmm getStatus
    
    # Безопасное извлечение данных с обработкой отсутствующих ключей
    ${sim}=           Run Keyword And Return Status    Get From Dictionary    ${output}    sim
    ${sim_active}=    Set Variable If    ${sim}    ${output['sim']['properties'].get('active', 'no')}    no
    ${sim_slot}=      Set Variable If    ${sim}    ${output['sim'].get('sim-slot', 'unknown')}    unknown
    
    ${status_exists}=    Run Keyword And Return Status    Get From Dictionary    ${output}    status
    ${connected}=     Set Variable If    ${status_exists}    ${output['status']['generic'].get('state', 'disconnected')}    disconnected
    ${state_failed_reason}=    Set Variable If    ${status_exists}    ${output['status']['generic'].get('state-failed-reason', '')}    ''
    ${signal_exists}=    Run Keyword And Return Status    Get From Dictionary    ${output}    signal
    ${rssi}=         Set Variable If    ${signal_exists}    ${output['signal']['lte'].get('rssi', '--')}    --
    
    # Извлечение operator-name из разных источников
    ${operator_name_sim}=    Set Variable If    ${sim}    ${output['sim']['properties'].get('operator-name', '--')}    --
    ${operator_name_3gpp}=    Set Variable If    ${status_exists}    ${output['status']['3gpp'].get('operator-name', '--')}    --
    ${operator_name}=    Set Variable If    '${operator_name_sim}' != '--'    ${operator_name_sim}    ${operator_name_3gpp}
    
    # Определение активного типа сигнала
    ${signal_type}=    Determine Signal Type    ${output}

    # Проверяем state-failed-reason - если он не равен "--", возвращаем только его
    ${has_failed_reason}=    Evaluate    $state_failed_reason != '--' and $state_failed_reason != ''
    IF    ${has_failed_reason}
        ${sim_status}=    Create Dictionary
        Set To Dictionary    ${sim_status}    state-failed-reason    ${state_failed_reason}
        RETURN    ${sim_status}
    END

    # Формируем результат
    ${sim_status}=    Create Dictionary
    Set To Dictionary    ${sim_status}    active    ${sim_active}
    Set To Dictionary    ${sim_status}    connected    ${connected}
    Set To Dictionary    ${sim_status}    rssi    ${rssi}
    Set To Dictionary    ${sim_status}    sim_slot    ${sim_slot}
    Set To Dictionary    ${sim_status}    operator_name    ${operator_name}
    Set To Dictionary    ${sim_status}    signal    ${signal_type}

    # Вычисляем качество сигнала
    ${signal_strength}=    Calculate Signal Strength    ${rssi}    ${signal_type}
    Set To Dictionary    ${sim_status}    signal_strength    ${signal_strength}

    # Определяем result на основе наличия оператора и качества сигнала
    ${has_operator}=    Evaluate    '${operator_name}' != '--' and '${operator_name}' != ''
    ${has_good_signal}=    Evaluate    ${signal_strength} >= 2  # Удовлетворительно или лучше
    ${result}=    Set Variable If    ${has_operator} and ${has_good_signal}    success    fail
    Set To Dictionary    ${sim_status}    result    ${result}

    # Оцениваем общий статус
    ${sim_ok}=    Run Keyword And Return Status    Should Be Equal    ${sim_active}    yes
    ${conn_ok}=    Run Keyword And Return Status    Should Be Equal    ${connected}    connected
    ${signal_ok}=    Evaluate    ${signal_strength} > 0

    # Вычисляем общий статус
    ${overall_status}=    Evaluate    ${sim_ok} and ${conn_ok} and ${signal_ok}
    Set To Dictionary    ${sim_status}    overall_status    ${overall_status}

    RETURN    ${sim_status}

Determine Signal Type
    [Arguments]    ${output}
    [Documentation]    Определяет активный тип сигнала на основе данных signal
    
    # Проверяем наличие секции signal
    ${signal_exists}=    Run Keyword And Return Status    Get From Dictionary    ${output}    signal
    IF    not ${signal_exists}
        RETURN    --
    END
    
    ${signal_data}=    Get From Dictionary    ${output}    signal
    
    # Проверяем LTE сигнал
    ${lte_exists}=    Run Keyword And Return Status    Get From Dictionary    ${signal_data}    lte
    IF    ${lte_exists}
        ${lte_data}=    Get From Dictionary    ${signal_data}    lte
        ${lte_has_values}=    Check Signal Has Values    ${lte_data}
        IF    ${lte_has_values}
            RETURN    lte
        END
    END
    
    # Проверяем UMTS сигнал
    ${umts_exists}=    Run Keyword And Return Status    Get From Dictionary    ${signal_data}    umts
    IF    ${umts_exists}
        ${umts_data}=    Get From Dictionary    ${signal_data}    umts
        ${umts_has_values}=    Check Signal Has Values    ${umts_data}
        IF    ${umts_has_values}
            RETURN    umts
        END
    END
    
    # Проверяем GSM сигнал
    ${gsm_exists}=    Run Keyword And Return Status    Get From Dictionary    ${signal_data}    gsm
    IF    ${gsm_exists}
        ${gsm_data}=    Get From Dictionary    ${signal_data}    gsm
        ${gsm_has_values}=    Check Signal Has Values    ${gsm_data}
        IF    ${gsm_has_values}
            RETURN    gsm
        END
    END
    
    # Если ни один тип сигнала не имеет значений
    RETURN    --

Check Signal Has Values
    [Arguments]    ${signal_data}
    [Documentation]    Проверяет, есть ли в данных сигнала значения отличные от "--"
    
    ${keys}=    Get Dictionary Keys    ${signal_data}
    FOR    ${key}    IN    @{keys}
        ${value}=    Get From Dictionary    ${signal_data}    ${key}
        IF    '${value}' != '--'
            RETURN    ${True}
        END
    END
    RETURN    ${False}

Calculate Signal Strength
    [Arguments]    ${rssi}    ${signal_type}
    [Documentation]    Вычисляет качество сигнала на основе RSSI и типа сигнала
    
    # Если RSSI недоступен или тип сигнала неизвестен
    IF    '${rssi}' == '--' or '${signal_type}' == '--'
        RETURN    0
    END
    
    # Преобразуем RSSI в число
    ${rssi_int}=    Run Keyword And Return Status    Convert To Number    ${rssi}
    IF    not ${rssi_int}
        RETURN    0
    END
    
    ${rssi_value}=    Convert To Number    ${rssi}
    ${signal_strength}=    Set Variable    0
    
    # Разные пороги для разных типов сетей
    IF    '${signal_type}' == 'gsm' or '${signal_type}' == 'umts'
        # Пороги для GSM/UMTS сетей
        IF    ${rssi_value} >= -70
            ${signal_strength}=    Set Variable    4  # Отлично
        ELSE IF    ${rssi_value} >= -85
            ${signal_strength}=    Set Variable    3  # Хорошо
        ELSE IF    ${rssi_value} >= -100
            ${signal_strength}=    Set Variable    2  # Удовлетворительно
        ELSE IF    ${rssi_value} >= -110
            ${signal_strength}=    Set Variable    1  # Плохо
        ELSE
            ${signal_strength}=    Set Variable    0  # Нет сигнала
        END
    ELSE IF    '${signal_type}' == 'lte'
        # Пороги для LTE сетей (более строгие)
        IF    ${rssi_value} >= -65
            ${signal_strength}=    Set Variable    4  # Отлично
        ELSE IF    ${rssi_value} >= -75
            ${signal_strength}=    Set Variable    3  # Хорошо
        ELSE IF    ${rssi_value} >= -85
            ${signal_strength}=    Set Variable    2  # Удовлетворительно
        ELSE IF    ${rssi_value} >= -95
            ${signal_strength}=    Set Variable    1  # Плохо
        ELSE
            ${signal_strength}=    Set Variable    0  # Нет сигнала
        END
    ELSE
        # Если тип сети неизвестен, используем общие пороги (GSM/UMTS)
        IF    ${rssi_value} >= -70
            ${signal_strength}=    Set Variable    4  # Отлично
        ELSE IF    ${rssi_value} >= -85
            ${signal_strength}=    Set Variable    3  # Хорошо
        ELSE IF    ${rssi_value} >= -100
            ${signal_strength}=    Set Variable    2  # Удовлетворительно
        ELSE IF    ${rssi_value} >= -110
            ${signal_strength}=    Set Variable    1  # Плохо
        ELSE
            ${signal_strength}=    Set Variable    0  # Нет сигнала
        END
    END
    
    RETURN    ${signal_strength}



Ping Target IP
    [Documentation]    Проверяет доступность 8.8.8.8 через wwan0
    ${output}=    Run Command With Timeout    ping -I wwan0 -c 4 ${TARGET_IP}    20s
    
    # Парсим результат пинга
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
    IF    ${loss_match}
        ${packet_loss_percent}=    Set Variable    ${loss_match[0]}
        ${packet_loss}=    Set Variable    ${packet_loss_percent}%
        
        # Если потери меньше 100%, считаем успешным
        ${packet_loss_int}=    Convert To Integer    ${packet_loss_percent}
        IF    ${packet_loss_int} < 100
            ${status}=    Set Variable    success
        END
    END

    # Парсим время отклика (если есть)
    ${time_match}=    Get Regexp Matches    ${output}    time=(\\\\d+\\\\.?\\\\d*)\\\\s*ms
    IF    ${time_match}
        ${response_time}=    Set Variable    ${time_match[0]}ms
    END

    ${result}=    Create Dictionary
    ...    status=${status}
    ...    packet_loss=${packet_loss}
    ...    response_time=${response_time}

    RETURN    ${result}

Run Command And Return Output
    [Arguments]    ${command}
    Write    ${command}
    ${output}=    Read Until Prompt
    RETURN    ${output}

Check And Add Default Route Through WWAN0
    [Documentation]    Проверяет и добавляет маршрут 'default dev wwan0 scope link'
    ${routes}=    Run Command And Return Output    ip route show
    
    # Разбиваем вывод на строки
    ${lines}=    Split String    ${routes}    \n
    
    ${has_route}=    Set Variable    False

    # Проверяем каждую строку
    FOR    ${line}    IN    @{lines}
        # Убираем лишние пробелы
        ${line}=    Strip String    ${line}
        
        # Ищем точное совпадение
        ${match_status}=    Run Keyword And Return Status
        ...    Should Match Regexp    ${line}    ^default dev wwan0 scope link    multiline=True
        
        IF    ${match_status} == 0
            ${has_route}=    Set Variable    True
            Exit For Loop
        END
    END

    # Если маршрут не найден — добавляем его
    IF    not ${has_route}
        Run Command And Log    ip route add default dev wwan0 scope link
    END

Run Command With Timeout
    [Arguments]    ${command}    ${timeout}
    Set Client Configuration    timeout=20s
    Write    ${command}
    ${output}=    Read Until Prompt
    RETURN    ${output}

Run Command And Log
    [Arguments]    ${command}
    Write    ${command}
    ${output}=    Read Until Prompt
    Log    Выполнили команду: ${command}\nВывод:\n${output}

Debug Log
    [Arguments]    ${message}
    [Documentation]    Выводит отладочное сообщение только если включён DEBUG_MODE
    IF    '${DEBUG_MODE}' == 'TRUE'
        Log    ${message}
    END

Calculate Test Progress
    [Arguments]    ${test_results}
    [Documentation]    Вычисляет прогресс SIM тестов на основе результатов
    
    Debug Log    [DEBUG] Начинаем расчёт прогресса SIM тестов
    Debug Log    [DEBUG] Входные данные: ${test_results}
    
    ${total_progress}=    Set Variable    ${0}
    ${slot_count}=    Set Variable    0
    
    # Проходим по всем слотам в результатах
    ${keys}=    Get Dictionary Keys    ${test_results}
    FOR    ${key}    IN    @{keys}
        # Проверяем только слоты (slot_1, slot_2, etc.)
        ${is_slot}=    Run Keyword And Return Status    Should Match Regexp    ${key}    ^slot_\\\\d+$
        IF    ${is_slot}
            Debug Log    [DEBUG] Обрабатываем слот: ${key}
            ${slot_count}=    Evaluate    ${slot_count} + 1
            ${slot_data}=    Get From Dictionary    ${test_results}    ${key}
            Debug Log    [DEBUG] Данные слота ${key}: ${slot_data}
            
            # Пропускаем слоты с ошибками подключения
            ${has_error}=    Run Keyword And Return Status    Dictionary Should Contain Key    ${slot_data}    error
            IF    ${has_error}
                Debug Log    [DEBUG] Слот ${key} содержит ошибку, пропускаем
                CONTINUE
            END
            
            ${slot_progress}=    Set Variable    0
            Debug Log    [DEBUG] Начальный прогресс слота ${key}: ${slot_progress}%
            
            # Активность SIM: 5%
            ${active}=    Get From Dictionary    ${slot_data}    active    default=no
            Debug Log    [DEBUG] Проверяем активность SIM: ${active}
            IF    '${active}' == 'yes'
                ${slot_progress}=    Evaluate    ${slot_progress} + 5
                Debug Log    [DEBUG] SIM активна, добавляем 5%. Текущий прогресс: ${slot_progress}%
            ELSE
                Debug Log    [DEBUG] SIM неактивна, баллы не добавляются
            END
            
            # Подключение: 5%
            ${connected}=    Get From Dictionary    ${slot_data}    connected    default=disconnected
            Debug Log    [DEBUG] Проверяем подключение: ${connected}
            IF    '${connected}' == 'connected'
                ${slot_progress}=    Evaluate    ${slot_progress} + 5
                Debug Log    [DEBUG] SIM подключена, добавляем 5%. Текущий прогресс: ${slot_progress}%
            ELSE
                Debug Log    [DEBUG] SIM не подключена, баллы не добавляются
            END
            
            # Успешный ping: 15%
            ${ping_result}=    Get From Dictionary    ${slot_data}    ping_result    default=error
            Debug Log    [DEBUG] Проверяем результат ping: ${ping_result}
            IF    '${ping_result}' == 'success'
                ${slot_progress}=    Evaluate    ${slot_progress} + 15
                Debug Log    [DEBUG] Ping успешен, добавляем 15%. Текущий прогресс: ${slot_progress}%
            ELSE
                Debug Log    [DEBUG] Ping неуспешен, баллы не добавляются
            END
            
            # Качество сигнала: 25% (если есть имя оператора и тип сигнала)
            ${operator_name}=    Get From Dictionary    ${slot_data}    operator_name    default=
            ${signal}=    Get From Dictionary    ${slot_data}    signal    default=
            Debug Log    [DEBUG] Проверяем оператора: '${operator_name}' и сигнал: '${signal}'
            IF    '${operator_name}' != '' and '${operator_name}' != '--' and '${signal}' != '' and '${signal}' != '--'
                ${slot_progress}=    Evaluate    ${slot_progress} + 25
                Debug Log    [DEBUG] Есть оператор и сигнал, добавляем 25%. Текущий прогресс: ${slot_progress}%
            ELSE
                Debug Log    [DEBUG] Нет оператора или сигнала, баллы не добавляются
            END
            
            # Дополнительные баллы за RSSI (если значение лучше -75): 5%
            ${rssi}=    Get From Dictionary    ${slot_data}    rssi    default=0
            Debug Log    [DEBUG] Проверяем RSSI: ${rssi}
            ${rssi_value}=    Run Keyword And Return Status    Should Be True    '${rssi}' != '0' and '${rssi}' != '--' and float('${rssi}') > -75
            IF    ${rssi_value}
                ${slot_progress}=    Evaluate    ${slot_progress} + 5
                Debug Log    [DEBUG] RSSI хороший (${rssi} > -75), добавляем 5%. Текущий прогресс: ${slot_progress}%
            ELSE
                Debug Log    [DEBUG] RSSI плохой или отсутствует, баллы не добавляются
            END
            
            ${total_progress}=    Evaluate    ${total_progress} + ${slot_progress}
            Debug Log    [DEBUG] Финальный прогресс слота ${key}: ${slot_progress}%. Общий прогресс: ${total_progress}
        END
    END
    
    Debug Log    [DEBUG] Обработано слотов: ${slot_count}, общий прогресс: ${total_progress}
    
    # Вычисляем средний прогресс (максимум 55% на слот)
    ${max_progress}=    Evaluate    ${slot_count} * 55
    Debug Log    [DEBUG] Максимально возможный прогресс: ${max_progress} (${slot_count} слотов × 55%)
    
    ${progress_percent}=    Evaluate    ${total_progress} * 100 // ${max_progress} if ${max_progress} > 0 else 0
    Debug Log    [DEBUG] Расчёт процентов: ${total_progress} × 100 ÷ ${max_progress} = ${progress_percent}%
    
    # Ограничиваем прогресс до 100%
    ${progress_percent}=    Set Variable If    ${progress_percent} > 100    100    ${progress_percent}
    Debug Log    [DEBUG] Итоговый прогресс после ограничения: ${progress_percent}%
    
    RETURN    ${progress_percent}

Generate JSON Report
    [Arguments]    ${data}
    # Вычисляем прогресс тестов
    ${progress}=    Calculate Test Progress    ${data}
    Set To Dictionary    ${data}    progress    ${progress}
    
    # Используем ensure_ascii=True для избежания проблемных символов
    # Передаем data как переменную Python, а не как строку Robot Framework
    ${json_str}=    Evaluate    json.dumps($data, indent=4, ensure_ascii=True)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8