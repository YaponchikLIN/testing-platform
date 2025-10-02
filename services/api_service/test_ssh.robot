*** Settings ***
Documentation    Минимальная проверка SSH соединения
Library          SSHLibrary

*** Variables ***
${ROUTER_IP}      192.168.1.1
${USERNAME}       root
${PASSWORD}       ${EMPTY}

*** Test Cases ***
Simple SSH Test
    [Documentation]    Простейшая проверка SSH
    
    Log    Пытаюсь подключиться к ${USERNAME}@${ROUTER_IP}
    Log    Используется пароль: '${PASSWORD}' (длина: ${{len('${PASSWORD}')}})
    
    # Пытаемся подключиться
    Open Connection    ${ROUTER_IP}    timeout=15s
    Run Keyword If    '${PASSWORD}' == '${EMPTY}'
    ...    Login    ${USERNAME}    ${EMPTY}
    ...    ELSE
    ...    Login    ${USERNAME}    ${PASSWORD}
    
    # Выполняем простую команду
    ${result}=    Execute Command    uname -a
    Log    Системная информация: ${result}
    
    # Закрываем соединение
    Close Connection
    
    Log    ✅ SSH тест пройден успешно!

SSH Test With Error Handling
    [Documentation]    Проверка SSH с обработкой ошибок
    
    Log    Пытаюсь подключиться с параметрами:
    Log    - IP: ${ROUTER_IP}
    Log    - User: ${USERNAME}
    Log    - Password: '${PASSWORD}'
    
    ${success}=    Run Keyword And Return Status
    ...    Run Keywords
    ...    Open Connection    ${ROUTER_IP}    timeout=10s    AND
    ...    Run Keyword If    '${PASSWORD}' == '${EMPTY}'
    ...        Login    ${USERNAME}    ${EMPTY}
    ...        ELSE
    ...        Login    ${USERNAME}    ${PASSWORD}
    
    IF    ${success}
        ${hostname}=    Execute Command    hostname || echo "unknown"
        Log    ✅ Успех! Хост: ${hostname}
    ELSE
        Log    ❌ Ошибка SSH подключения
        Log    Проверьте:
        Log    - IP адрес: ${ROUTER_IP}
        Log    - Логин: ${USERNAME}
        Log    - Пароль: '${PASSWORD}'
        Log    - Доступность роутера по сети
    END
    
    Run Keyword And Ignore Error    Close All Connections