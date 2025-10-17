*** Settings ***
Library    OperatingSystem
Library    String
Library    Collections
Library    DateTime
Library    Process

*** Variables ***
${DEFAULT_SSID}          rtk-tOS-5EF0
${DEFAULT_PASSWORD}      123456789
${SSID}                  ${DEFAULT_SSID}
${PASSWORD}              ${DEFAULT_PASSWORD}
${CONNECTION_TIMEOUT}    300s
${INTERFACE}             wlan0
${MEASUREMENT_TIME}      10s
${JSON_PATH}             ${CURDIR}${/}wifi_results.json
${EMPTY}

*** Test Cases ***
Connect To WiFi And Measure Speed
    [Documentation]    Подключение к WiFi сети и измерение скорости
    
    # Засекаем время начала теста
    ${start_time}=    Get Current Date    result_format=epoch
    
    # Инициализируем структуру данных для отчета
    ${wifi_data}=    Create Dictionary
    ...    ssid=${SSID}
    ...    interface=${INTERFACE}
    ...    connection_status=fail
    ...    download_speed_bps=0
    ...    upload_speed_bps=0
    ...    download_speed_human=0 bps
    ...    upload_speed_human=0 bps
    ...    error_message=${EMPTY}
    
    TRY
        Set WiFi Credentials From Arguments
        Detect Wireless Interface
        Get Initial Network Stats
        Connect To WiFi With NMCLI
        
        # Если подключение успешно, обновляем статус
        Set To Dictionary    ${wifi_data}    connection_status    success
        
        Wait For Stable Connection    5s
        Perform Network Activity
        Get Final Network Stats
        ${download_speed}    ${upload_speed}=    Calculate Network Speeds
        
        # Обновляем данные о скоростях
        Set To Dictionary    ${wifi_data}    
        ...    download_speed_mbps=${download_speed}
        ...    upload_speed_mbps=${upload_speed}
        
    EXCEPT    AS    ${error}
        Log    Ошибка в WiFi тесте: ${error}
        Set To Dictionary    ${wifi_data}    error_message    ${error}
    END
    
    # Вычисляем время выполнения
    ${end_time}=    Get Current Date    result_format=epoch
    ${execution_time}=    Evaluate    round(${end_time} - ${start_time}, 2)
    
    # Генерируем JSON отчет
    Generate WiFi JSON Report    ${wifi_data}    ${execution_time}

*** Keywords ***
Set WiFi Credentials From Arguments
    [Documentation]    Установка SSID и пароля из аргументов командной строки
    ${ssid_arg}    Get Variable Value    ${SSID_ARG}    ${EMPTY}
    ${password_arg}    Get Variable Value    ${PASSWORD_ARG}    ${EMPTY}
    
    IF    "${ssid_arg}" != "${EMPTY}"
        Set Global Variable    ${SSID}    ${ssid_arg}
        Log    Используется SSID из аргументов: ${SSID}
    ELSE
        Log    Используется SSID по умолчанию: ${SSID}
    END
    
    IF    "${password_arg}" != "${EMPTY}"
        Set Global Variable    ${PASSWORD}    ${password_arg}
        Log    Используется пароль из аргументов
    ELSE
        Log    Используется пароль по умолчанию
    END

Detect Wireless Interface
    [Documentation]    Автоопределение беспроводного интерфейса
    ${rc}    ${output}    Run And Return Rc And Output    ip link show | grep -o "wlan[0-9]\\|wlp[0-9]s[0-9]" | head -1
    IF    ${rc} == 0 and "${output}" != "${EMPTY}"
        Set Global Variable    ${INTERFACE}    ${output}
        Log    Автоопределен интерфейс: ${INTERFACE}
    ELSE
        Log    Используется интерфейс по умолчанию: ${INTERFACE}
    END

Get Initial Network Stats
    [Documentation]    Получение начальной статистики по интерфейсу через команду ip
    ${stats}    Get Interface Stats With IP    ${INTERFACE}
    Set Global Variable    ${INITIAL_RX_BYTES}    ${stats['rx_bytes']}
    Set Global Variable    ${INITIAL_TX_BYTES}    ${stats['tx_bytes']}
    Set Global Variable    ${INITIAL_RX_PACKETS}    ${stats['rx_packets']}
    Set Global Variable    ${INITIAL_TX_PACKETS}    ${stats['tx_packets']}
    Log    Начальная статистика: RX=${INITIAL_RX_BYTES} bytes, TX=${INITIAL_TX_BYTES} bytes

Get Final Network Stats
    [Documentation]    Получение конечной статистики по интерфейсу через команду ip
    ${stats}    Get Interface Stats With IP    ${INTERFACE}
    Set Global Variable    ${FINAL_RX_BYTES}    ${stats['rx_bytes']}
    Set Global Variable    ${FINAL_TX_BYTES}    ${stats['tx_bytes']}
    Set Global Variable    ${FINAL_RX_PACKETS}    ${stats['rx_packets']}
    Set Global Variable    ${FINAL_TX_PACKETS}    ${stats['tx_packets']}
    Log    Конечная статистика: RX=${FINAL_RX_BYTES} bytes, TX=${FINAL_TX_BYTES} bytes

Get Interface Stats With IP
    [Documentation]    Получение статистики через команду ip
    [Arguments]    ${interface}
    ${rc}    ${output}    Run And Return Rc And Output    ip -s link show ${interface}
    IF    ${rc} != 0
        Fail    Не удалось получить статистику для интерфейса ${interface}
    END
    
    # Парсим вывод команды ip
    @{lines}    Split To Lines    ${output}
    ${rx_bytes}    Set Variable    0
    ${rx_packets}    Set Variable    0
    ${tx_bytes}    Set Variable    0
    ${tx_packets}    Set Variable    0
    
    ${is_rx_section}    Set Variable    ${FALSE}
    ${is_tx_section}    Set Variable    ${FALSE}
    
    FOR    ${line}    IN    @{lines}
        ${line}    Strip String    ${line}
        IF    "RX:" in "${line}"
            ${is_rx_section}    Set Variable    ${TRUE}
            ${is_tx_section}    Set Variable    ${FALSE}
        ELSE IF    "TX:" in "${line}"
            ${is_rx_section}    Set Variable    ${FALSE}
            ${is_tx_section}    Set Variable    ${TRUE}
        ELSE IF    ${is_rx_section} and "bytes" in "${line}" and "packets" in "${line}"
            @{parts}    Split String    ${line}    ${SPACE}
            ${rx_bytes}    Set Variable    ${parts[0]}
            ${rx_packets}    Set Variable    ${parts[2]}
        ELSE IF    ${is_tx_section} and "bytes" in "${line}" and "packets" in "${line}"
            @{parts}    Split String    ${line}    ${SPACE}
            ${tx_bytes}    Set Variable    ${parts[0]}
            ${tx_packets}    Set Variable    ${parts[2]}
        END
    END
    
    &{stats}    Create Dictionary
    ...    rx_bytes=${rx_bytes}
    ...    rx_packets=${rx_packets}
    ...    tx_bytes=${tx_bytes}
    ...    tx_packets=${tx_packets}
    
    RETURN    ${stats}

Connect To WiFi With NMCLI
    [Documentation]    Подключение к WiFi с помощью команды nmcli с таймаутом и механизмом ожидания
    Log    Попытка подключения к WiFi: ${SSID} с таймаутом ${CONNECTION_TIMEOUT}
    
    # Проверяем, доступен ли nmcli
    Run Keyword And Ignore Error    Check NMCLI Available
    
    # Формируем команду для подключения с таймаутом
    ${command}    Set Variable    timeout ${CONNECTION_TIMEOUT} nmcli d wifi connect "${SSID}" password "${PASSWORD}"
    Log    Выполняется команда: ${command}
    
    # Выполняем команду через Execute Command
    ${rc}    ${output}    Run And Return Rc And Output    ${command}
    
    IF    ${rc} == 0
        Log    Успешное подключение к WiFi: ${SSID}
        Log    Вывод команды: ${output}
        
        # Ожидаем стабилизации подключения и получения IP адреса
        Wait For IP Address Assignment    ${CONNECTION_TIMEOUT}
    ELSE IF    ${rc} == 124
        Log    Таймаут подключения к WiFi ${SSID} (${CONNECTION_TIMEOUT})
        Fail    Таймаут подключения к WiFi ${SSID} после ${CONNECTION_TIMEOUT}
    ELSE
        Log    Ошибка подключения к WiFi. Код возврата: ${rc}
        Log    Вывод команды: ${output}
        Fail    Не удалось подключиться к WiFi ${SSID}
    END

Check NMCLI Available
    [Documentation]    Проверка доступности утилиты nmcli
    ${rc}    ${output}    Run And Return Rc And Output    which nmcli
    Should Be Equal As Integers    ${rc}    0    nmcli не найден в системе
    Log    nmcli доступен в системе

Wait For Stable Connection
    [Documentation]    Ожидание стабильного подключения
    [Arguments]    ${wait_time}=5s
    Log    Ожидание стабилизации подключения: ${wait_time}
    Sleep    ${wait_time}
    
    # Проверяем, что интерфейс получил IP адрес
    ${rc}    ${output}    Run And Return Rc And Output    ip addr show ${INTERFACE} | grep "inet "
    IF    ${rc} == 0
        Log    Интерфейс ${INTERFACE} получил IP адрес
    ELSE
        Log    Предупреждение: Интерфейс ${INTERFACE} не получил IP адрес
    END

Perform Network Activity
    [Documentation]    Выполнение сетевой активности для измерения скорости
    Log    Выполняем сетевую активность в течение ${MEASUREMENT_TIME}
    ${start_time}    Get Time    epoch
    
    # Создаем фоновый процесс для генерации трафика (ping)
    ${ping_process}    Start Process    ping -c 100 8.8.8.8    shell=True    alias=ping_traffic
    
    # Ждем указанное время
    Sleep    ${MEASUREMENT_TIME}
    
    # Останавливаем процесс
    Terminate Process    ${ping_process}
    Sleep    1s  # Даем время для завершения
    
    ${end_time}    Get Time    epoch
    ${actual_time}    Evaluate    ${end_time} - ${start_time}
    Set Global Variable    ${MEASUREMENT_DURATION}    ${actual_time}
    Log    Фактическое время измерения: ${actual_time} секунд

Calculate Network Speeds
    [Documentation]    Расчет скоростей RX/TX на основе статистики ip
    [Returns]    ${download_speed}    ${upload_speed}
    ${rx_bytes_delta}    Evaluate    int(${FINAL_RX_BYTES}) - int(${INITIAL_RX_BYTES})
    ${tx_bytes_delta}    Evaluate    int(${FINAL_TX_BYTES}) - int(${INITIAL_TX_BYTES})
    ${rx_packets_delta}    Evaluate    int(${FINAL_RX_PACKETS}) - int(${INITIAL_RX_PACKETS})
    ${tx_packets_delta}    Evaluate    int(${FINAL_TX_PACKETS}) - int(${INITIAL_TX_PACKETS})
    
    # Рассчитываем скорости в байтах/сек и битах/сек
    ${rx_speed_bytes_sec}    Evaluate    ${rx_bytes_delta} / ${MEASUREMENT_DURATION}
    ${tx_speed_bytes_sec}    Evaluate    ${tx_bytes_delta} / ${MEASUREMENT_DURATION}
    ${rx_speed_bits_sec}    Evaluate    ${rx_speed_bytes_sec} * 8
    ${tx_speed_bits_sec}    Evaluate    ${tx_speed_bytes_sec} * 8
    
    # Конвертируем в человеко-читаемый формат
    ${rx_speed_human}    Convert To Human Readable Speed    ${rx_speed_bits_sec}
    ${tx_speed_human}    Convert To Human Readable Speed    ${tx_speed_bits_sec}
    
    Log    \n=== РЕЗУЛЬТАТЫ ИЗМЕРЕНИЯ СКОРОСТИ ===
    Log    Интерфейс: ${INTERFACE}
    Log    Время измерения: ${MEASUREMENT_DURATION} секунд
    Log    Передано данных: ${tx_bytes_delta} bytes (${tx_packets_delta} пакетов)
    Log    Получено данных: ${rx_bytes_delta} bytes (${rx_packets_delta} пакетов)
    Log    Скорость отдачи (TX): ${tx_speed_human}
    Log    Скорость загрузки (RX): ${rx_speed_human}
    Log    ====================================
    
    # Возвращаем скорости в Mbps для JSON отчета
    ${download_speed}    Evaluate    round(${rx_speed_bits_sec} / 1000000, 2)
    ${upload_speed}    Evaluate    round(${tx_speed_bits_sec} / 1000000, 2)
    RETURN    ${download_speed}    ${upload_speed}

Convert To Human Readable Speed
    [Documentation]    Конвертация скорости в человеко-читаемый формат
    [Arguments]    ${speed_bits}
    IF    ${speed_bits} > 1000000
        ${result}    Evaluate    round(${speed_bits} / 1000000, 2)
        RETURN    ${result} Mbps
    ELSE IF    ${speed_bits} > 1000
        ${result}    Evaluate    round(${speed_bits} / 1000, 2)
        RETURN    ${result} Kbps
    ELSE
        RETURN    ${speed_bits} bps
    END

Calculate WiFi Test Progress
    [Documentation]    Вычисляет прогресс WiFi теста на основе результатов
    [Arguments]    ${wifi_data}
    
    ${total_progress}=    Set Variable    0
    
    # Проверяем подключение к WiFi: 40%
    ${connection_status}=    Get From Dictionary    ${wifi_data}    connection_status    default=fail
    IF    '${connection_status}' == 'success'
        ${total_progress}=    Evaluate    ${total_progress} + 40
    END
    
    # Проверяем скорость загрузки > 0: 30%
    ${download_speed}=    Get From Dictionary    ${wifi_data}    download_speed_mbps    default=0
    IF    ${download_speed} > 0
        ${total_progress}=    Evaluate    ${total_progress} + 30
    END
    
    # Проверяем скорость отдачи > 0: 30%
    ${upload_speed}=    Get From Dictionary    ${wifi_data}    upload_speed_mbps    default=0
    IF    ${upload_speed} > 0
        ${total_progress}=    Evaluate    ${total_progress} + 30
    END
    
    # Ограничиваем прогресс до 100%
    ${progress_percent}=    Set Variable If    ${total_progress} > 100    100    ${total_progress}
    
    RETURN    ${progress_percent}

Generate WiFi JSON Report
    [Documentation]    Генерация JSON отчета для WiFi теста
    [Arguments]    ${wifi_data}    ${execution_time}
    
    # Определяем общий статус теста на основе новых критериев
    ${connection_status}=    Get From Dictionary    ${wifi_data}    connection_status    default=fail
    ${download_speed}=    Get From Dictionary    ${wifi_data}    download_speed_mbps    default=0
    ${upload_speed}=    Get From Dictionary    ${wifi_data}    upload_speed_mbps    default=0
    
    # Все три условия должны выполняться одновременно
    ${test_status}=    Set Variable If
    ...    '${connection_status}' == 'success' and ${download_speed} > 0 and ${upload_speed} > 0
    ...    PASS    FAIL
    
    ${details}=    Set Variable If
    ...    '${test_status}' == 'PASS'    WiFi подключение успешно, скорости загрузки и отдачи больше 0
    ...    Проблемы с WiFi: подключение или скорость равна 0
    
    # Вычисляем прогресс теста
    ${progress}=    Calculate WiFi Test Progress    ${wifi_data}
    
    # Формируем финальный отчет
    ${final_report}=    Create Dictionary
    ...    test_status=${test_status}
    ...    execution_time=${execution_time}
    ...    wifi_data=${wifi_data}
    ...    details=${details}
    ...    progress=${progress}
    
    # Сохраняем в JSON файл
    ${json_str}=    Evaluate    json.dumps(${final_report}, indent=4, ensure_ascii=False)    modules=json
    Create File    ${JSON_PATH}    ${json_str}    encoding=UTF-8
    Log    WiFi JSON отчет создан: ${JSON_PATH}

Wait For IP Address Assignment
    [Documentation]    Ожидание получения IP адреса интерфейсом с таймаутом
    [Arguments]    ${timeout}=300s
    
    Log    Ожидание получения IP адреса интерфейсом ${INTERFACE} в течение ${timeout}
    
    # Преобразуем таймаут в секунды для цикла
    ${timeout_seconds}=    Convert Time    ${timeout}    result_format=number
    ${check_interval}=    Set Variable    5
    ${elapsed_time}=    Set Variable    0
    
    WHILE    ${elapsed_time} < ${timeout_seconds}
        # Проверяем, получил ли интерфейс IP адрес
        ${rc}    ${output}    Run And Return Rc And Output    ip addr show ${INTERFACE} | grep "inet " | grep -v "127.0.0.1"
        
        IF    ${rc} == 0
            Log    Интерфейс ${INTERFACE} успешно получил IP адрес: ${output}
            RETURN
        END
        
        Log    IP адрес еще не назначен, ожидание ${check_interval} секунд... (прошло ${elapsed_time}/${timeout_seconds} сек)
        Sleep    ${check_interval}s
        ${elapsed_time}=    Evaluate    ${elapsed_time} + ${check_interval}
    END
    
    # Если время истекло, но IP адрес не получен
    Log    Предупреждение: IP адрес не был получен в течение ${timeout}
    ${rc}    ${output}    Run And Return Rc And Output    ip addr show ${INTERFACE}
    Log    Текущее состояние интерфейса ${INTERFACE}: ${output}