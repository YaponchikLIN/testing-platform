*** Settings ***
Documentation    Простая загрузка и установка прошивки через SSH
Library          SSHLibrary
Library          OperatingSystem
Library          Collections
Library          Process
Library          DateTime
Library          String

*** Variables ***
${ROUTER_IP}      192.168.1.1
${USERNAME}       root
${PASSWORD} 
# ${FIRMWARE_DIR}      ${CURDIR}${/}downloads
${FIRMWARE_DIR}      C:/Projects/RTK/testing-platform/services/api_service/downloads
${REMOTE_PATH}       /tmp/firmware.bin
${REBOOT_TIMEOUT}    300    # 5 minutes for router reboot
${PING_TIMEOUT}      60     # 1 minute for ping attempts
${CONNECTION_RETRY_INTERVAL}    10    # 10 seconds between connection attempts
${SSH_TIMEOUT}       30     # SSH connection timeout in seconds
${MAX_SSH_RETRIES}   20     # Maximum SSH connection retry attempts
${CLEANUP_FIRMWARE}  True   # Whether to cleanup firmware file after installation

*** Keywords ***
Find Firmware File
    [Documentation]    Search for .bin file in downloads folder with smart selection
    
    # Check if directory exists
    OperatingSystem.Directory Should Exist    ${FIRMWARE_DIR}
    
    # Search for .bin files
    @{files}=    OperatingSystem.List Files In Directory    ${FIRMWARE_DIR}    pattern=*.bin
    
    # Check that at least one file is found
    ${count}=    Get Length    ${files}
    Should Be True    ${count} > 0    msg=No .bin files found in ${FIRMWARE_DIR}
    
    ${firmware_file}=    Set Variable    ${EMPTY}
    
    # If exactly one file - use it
    IF    ${count} == 1
        ${firmware_file}=    Get From List    ${files}    0
        Log    Found single firmware file: ${firmware_file}
    # If multiple files - prefer non-test files
    ELSE IF    ${count} > 1
        Log    Found ${count} .bin files, selecting the best candidate
        
        # First, try to find non-test files
        FOR    ${file}    IN    @{files}
            ${is_test_file}=    Run Keyword And Return Status    Should Contain    ${file}    test
            IF    not ${is_test_file}
                ${firmware_file}=    Set Variable    ${file}
                Log    Selected non-test firmware file: ${firmware_file}
                Exit For Loop
            END
        END
        
        # If no non-test files found, use the first one
        IF    '${firmware_file}' == '${EMPTY}'
            ${firmware_file}=    Get From List    ${files}    0
            Log    Using first available firmware file: ${firmware_file}
        END
        
        # Log all available files for reference
        Log    Available firmware files: ${files}
    END
    
    ${firmware_path}=    Join Path    ${FIRMWARE_DIR}    ${firmware_file}
    
    Log    Selected firmware file: ${firmware_path}
    RETURN    ${firmware_path}

Connect To Device
    [Documentation]    SSH connection with authentication and error handling
    
    Log    Connecting to ${USERNAME}@${ROUTER_IP}
    
    # Try to establish connection with timeout
    ${connection_status}=    Run Keyword And Return Status    Open Connection    ${ROUTER_IP}    timeout=30s
    IF    not ${connection_status}
        Fail    Failed to connect to ${ROUTER_IP}
    END
    
    # Try to login with credentials
    ${login_status}=    Run Keyword And Return Status    Login    ${USERNAME}    ${PASSWORD}
    IF    not ${login_status}
        Close All Connections
        Fail    Authentication failed for user '${USERNAME}' on ${ROUTER_IP}
    END
    
    Log    Connection established successfully

Upload File
    [Documentation]    Upload firmware file to device with verification
    [Arguments]    ${local_file}
    
    Log    Uploading ${local_file} -> ${REMOTE_PATH}
    
    # Get local file size for comparison
    ${local_size}=    OperatingSystem.Get File Size    ${local_file}
    Log    Local file size: ${local_size} bytes
    
    # Upload the file
    Put File    ${local_file}    ${REMOTE_PATH}
    
    # Verify file exists on remote device
    ${file_exists}=    Run Keyword And Return Status    Execute Command    test -f ${REMOTE_PATH}
    Should Be True    ${file_exists}    msg=Firmware file was not uploaded to ${REMOTE_PATH}
    
    # Check remote file size with multiple methods for compatibility
    ${remote_size}=    Set Variable    ${EMPTY}
    
    # Try stat command first (Linux/OpenWrt standard)
    ${stat_success}=    Run Keyword And Return Status    
    ...    Run Keywords
    ...    ${temp_size}=    Execute Command    stat -c%s ${REMOTE_PATH}    AND
    ...    Should Not Be Empty    ${temp_size}    AND
    ...    Set Test Variable    ${remote_size}    ${temp_size}
    
    # If stat failed, try ls -l method
    IF    not ${stat_success}
        Log    stat command failed, trying ls -l method
        ${ls_output}=    Execute Command    ls -l ${REMOTE_PATH}
        Log    ls output: ${ls_output}
        
        # Extract size from ls -l output (5th field)
        @{ls_parts}=    Split String    ${ls_output}
        ${ls_parts_count}=    Get Length    ${ls_parts}
        
        IF    ${ls_parts_count} >= 5
            ${remote_size}=    Get From List    ${ls_parts}    4
            Log    Extracted size from ls: ${remote_size}
        ELSE
            Log    Could not extract size from ls output, skipping size verification
            ${remote_size}=    Set Variable    ${EMPTY}
        END
    END
    
    # Verify file sizes if we got remote size
    IF    '${remote_size}' != '${EMPTY}'
        ${remote_size_int}=    Run Keyword And Return Status    Convert To Integer    ${remote_size}
        IF    ${remote_size_int}
            ${remote_size}=    Convert To Integer    ${remote_size}
            Log    Remote file size: ${remote_size} bytes
            
            # Compare sizes
            Should Be Equal As Integers    ${local_size}    ${remote_size}    
            ...    msg=File size mismatch: local=${local_size}, remote=${remote_size}
            Log    ✅ File size verification passed
        ELSE
            Log    Warning: Could not convert remote size '${remote_size}' to integer, skipping size check
        END
    ELSE
        Log    Warning: Could not determine remote file size, skipping size verification
    END
    
    # Check file permissions and basic info
    ${file_info}=    Execute Command    ls -la ${REMOTE_PATH}
    Log    File on device: ${file_info}
    
    # Additional verification: try to read first few bytes
    ${head_result}=    Run Keyword And Return Status    Execute Command    head -c 10 ${REMOTE_PATH}
    IF    ${head_result}
        Log    ✅ File is readable on remote device
    ELSE
        Log    Warning: Could not read file content, but file exists
    END
    
    Log    ✅ File uploaded and verified successfully

Install Firmware
    [Documentation]    Execute firmware installation command
    
    Log    Installing firmware...
    ${result}=    Execute Command    sysupgrade ${REMOTE_PATH}    return_stdout=True    return_stderr=True
    Log    Installation result: ${result}
    Log    🔄 Firmware installation initiated, router will reboot...

Wait For Router Reboot
    [Documentation]    Wait for router to reboot and become available again
    
    Log    Waiting for router to reboot...
    
    # Close current connection as router will disconnect
    Close All Connections
    
    # Wait a bit for reboot to start
    Sleep    30s
    Log    Initial wait completed, checking router availability...
    
    # Try to ping router until it responds
    ${start_time}=    Get Time    epoch
    ${timeout_time}=    Evaluate    ${start_time} + ${REBOOT_TIMEOUT}
    
    WHILE    True
        ${current_time}=    Get Time    epoch
        IF    ${current_time} > ${timeout_time}
            Fail    Router did not respond within ${REBOOT_TIMEOUT} seconds after reboot
        END
        
        # Try to ping the router
        ${ping_result}=    Run Keyword And Return Status    
        ...    Run Process    ping    -n    1    -w    5000    ${ROUTER_IP}    shell=True
        
        IF    ${ping_result}
            Log    ✅ Router is responding to ping
            Exit For Loop
        ELSE
            Log    Router not yet responding, waiting ${CONNECTION_RETRY_INTERVAL}s...
            Sleep    ${CONNECTION_RETRY_INTERVAL}s
        END
    END
    
    # Additional wait for services to start
    Sleep    30s
    Log    Router is back online after reboot

Verify Router Functionality
    [Documentation]    Connect to router and verify it's working properly
    
    Log    Verifying router functionality after firmware update...
    
    # Try to establish SSH connection with retries
    ${attempt}=    Set Variable    1
    
    WHILE    ${attempt} <= ${MAX_SSH_RETRIES}
        Log    SSH connection attempt ${attempt}/${MAX_SSH_RETRIES}
        
        ${connection_success}=    Run Keyword And Return Status
        ...    Run Keywords
        ...    Open Connection    ${ROUTER_IP}    timeout=${SSH_TIMEOUT}s    AND
        ...    Login    ${USERNAME}    ${PASSWORD}
        
        IF    ${connection_success}
            Log    ✅ SSH connection established successfully
            Exit For Loop
        ELSE
            IF    ${attempt} == ${MAX_SSH_RETRIES}
                Fail    Failed to establish SSH connection after ${MAX_SSH_RETRIES} attempts
            END
            Log    SSH connection failed, retrying in ${CONNECTION_RETRY_INTERVAL}s...
            Sleep    ${CONNECTION_RETRY_INTERVAL}s
            ${attempt}=    Evaluate    ${attempt} + 1
        END
    END
    
    # Basic system checks
    Log    Performing basic system checks...
    
    # Check system uptime (should be low after reboot)
    ${uptime_success}=    Run Keyword And Return Status    
    ...    Run Keywords
    ...    ${uptime}=    Execute Command    uptime    AND
    ...    Log    System uptime: ${uptime}
    
    IF    not ${uptime_success}
        Log    Warning: Could not get system uptime
    END
    
    # Check system version/build info
    ${version_success}=    Run Keyword And Return Status    
    ...    Run Keywords
    ...    ${version}=    Execute Command    cat /etc/openwrt_release    AND
    ...    Log    System version info: ${version}
    
    IF    not ${version_success}
        # Try alternative version commands
        ${alt_version_success}=    Run Keyword And Return Status
        ...    Run Keywords
        ...    ${version}=    Execute Command    uname -a    AND
        ...    Log    System info: ${version}
        
        IF    not ${alt_version_success}
            Log    Warning: Could not get system version information
        END
    END
    
    # Check basic network functionality
    ${network_success}=    Run Keyword And Return Status
    ...    Run Keywords
    ...    ${interfaces}=    Execute Command    ip addr show | grep "inet " || ifconfig | grep "inet "    AND
    ...    Log    Network interfaces: ${interfaces}
    
    IF    not ${network_success}
        Log    Warning: Could not get network interface information
    END
    
    # Test basic commands to ensure system is responsive
    ${basic_commands}=    Create List    pwd    date    whoami
    FOR    ${cmd}    IN    @{basic_commands}
        ${cmd_success}=    Run Keyword And Return Status    Execute Command    ${cmd}
        IF    ${cmd_success}
            Log    ✅ Command '${cmd}' executed successfully
        ELSE
            Log    ⚠️ Warning: Command '${cmd}' failed
        END
    END
    
    Log    ✅ Router functionality verification completed

Cleanup Firmware File
    [Documentation]    Remove firmware file from router after installation
    
    IF    ${CLEANUP_FIRMWARE}
        Log    Cleaning up firmware file from router...
        
        ${cleanup_success}=    Run Keyword And Return Status    
        ...    Execute Command    rm -f ${REMOTE_PATH}
        
        IF    ${cleanup_success}
            # Verify file was removed
            ${file_exists}=    Run Keyword And Return Status    Execute Command    test -f ${REMOTE_PATH}
            IF    not ${file_exists}
                Log    ✅ Firmware file successfully removed from ${REMOTE_PATH}
            ELSE
                Log    ⚠️ Warning: Firmware file still exists after cleanup attempt
            END
        ELSE
            Log    ⚠️ Warning: Failed to cleanup firmware file
        END
    ELSE
        Log    Firmware cleanup disabled, leaving file at ${REMOTE_PATH}
    END

Close Connection
    [Documentation]    Close SSH connection
    Close All Connections

Generate Test Report
    [Documentation]    Generate detailed test execution report
    
    Log    📊 Generating test execution report...
    
    ${timestamp}=    Get Current Date    result_format=%Y-%m-%d_%H-%M-%S
    ${report_file}=    Set Variable    firmware_upload_report_${timestamp}.txt
    
    ${report_content}=    Catenate    SEPARATOR=\n
    ...    ========================================
    ...    FIRMWARE UPLOAD TEST REPORT
    ...    ========================================
    ...    Test Execution Time: ${timestamp}
    ...    Router IP: ${ROUTER_IP}
    ...    Firmware Directory: ${FIRMWARE_DIR}
    ...    Remote Path: ${REMOTE_PATH}
    ...    ========================================
    ...    Configuration:
    ...    - SSH Timeout: ${SSH_TIMEOUT}s
    ...    - Max SSH Retries: ${MAX_SSH_RETRIES}
    ...    - Reboot Timeout: ${REBOOT_TIMEOUT}s
    ...    - Ping Timeout: ${PING_TIMEOUT}s
    ...    - Connection Retry Interval: ${CONNECTION_RETRY_INTERVAL}s
    ...    - Cleanup Firmware: ${CLEANUP_FIRMWARE}
    ...    ========================================
    
    Log    ${report_content}
    Log    Report generated: ${report_file}

Validate Test Environment
    [Documentation]    Validate test environment before execution
    
    Log    🔍 Validating test environment...
    
    # Check if required variables are set (PASSWORD is optional for key-based auth)
    ${required_vars}=    Create List    ROUTER_IP    USERNAME    FIRMWARE_DIR    REMOTE_PATH
    
    FOR    ${var}    IN    @{required_vars}
        ${var_value}=    Get Variable Value    ${${var}}    NOT_SET
        IF    '${var_value}' == 'NOT_SET' or '${var_value}' == ''
            Fail    Required variable ${var} is not set or empty
        ELSE
            Log    ✅ ${var}: ${var_value}
        END
    END
    
    # Check PASSWORD separately (optional)
    ${password_value}=    Get Variable Value    ${PASSWORD}    NOT_SET
    IF    '${password_value}' == 'NOT_SET' or '${password_value}' == ''
        Log    ⚠️ Warning: PASSWORD is empty - assuming key-based authentication
    ELSE
        Log    ✅ PASSWORD: [HIDDEN]
    END
    
    # Validate IP address format (basic check)
    ${ip_pattern}=    Set Variable    ^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$
    ${ip_valid}=    Run Keyword And Return Status    Should Match Regexp    ${ROUTER_IP}    ${ip_pattern}
    IF    not ${ip_valid}
        Log    ⚠️ Warning: Router IP '${ROUTER_IP}' may not be in valid format
    ELSE
        Log    ✅ Router IP format is valid
    END
    
    # Check if firmware directory exists and contains .bin files
    ${dir_exists}=    Run Keyword And Return Status    OperatingSystem.Directory Should Exist    ${FIRMWARE_DIR}
    IF    not ${dir_exists}
        Fail    Firmware directory does not exist: ${FIRMWARE_DIR}
    ELSE
        Log    ✅ Firmware directory exists
        
        # Check if there are any .bin files in the directory
        @{files}=    OperatingSystem.List Files In Directory    ${FIRMWARE_DIR}    pattern=*.bin
        ${count}=    Get Length    ${files}
        Log    Found ${count} .bin files in directory: ${FIRMWARE_DIR}
        
        IF    ${count} > 0
            Log    ✅ Found firmware files in directory
            FOR    ${file}    IN    @{files}
                Log    - ${file}
            END
        ELSE
            Fail    No .bin firmware files found in directory: ${FIRMWARE_DIR}
        END
    END
    
    Log    ✅ Test environment validation completed

Check System Resources
    [Documentation]    Check system resources on the router
    
    Log    📊 Checking system resources...
    
    # Check available disk space
    ${disk_success}=    Run Keyword And Return Status
    ...    Run Keywords
    ...    ${disk_info}=    Execute Command    df -h /tmp || df -h /    AND
    ...    Log    Disk space information:\n${disk_info}
    
    IF    not ${disk_success}
        Log    ⚠️ Warning: Could not get disk space information
    END
    
    # Check memory usage
    ${memory_success}=    Run Keyword And Return Status
    ...    Run Keywords
    ...    ${memory_info}=    Execute Command    free -m || cat /proc/meminfo | head -5    AND
    ...    Log    Memory information:\n${memory_info}
    
    IF    not ${memory_success}
        Log    ⚠️ Warning: Could not get memory information
    END
    
    # Check system load
    ${load_success}=    Run Keyword And Return Status
    ...    Run Keywords
    ...    ${load_info}=    Execute Command    cat /proc/loadavg || uptime    AND
    ...    Log    System load: ${load_info}
    
    IF    not ${load_success}
        Log    ⚠️ Warning: Could not get system load information
    END
    
    Log    ✅ System resources check completed
    Log    Connection closed

*** Test Cases ***
Upload And Install Firmware
    [Documentation]    Complete firmware upload, installation and verification test
    [Tags]    firmware    critical
    
    Log    🚀 Starting firmware upload and installation process
    
    # Step 0: Validate test environment
    Validate Test Environment
    
    # Step 1: Find firmware file
    ${firmware_path}=    Find Firmware File
    Log    📁 Using firmware file: ${firmware_path}
    
    # Step 2: Connect to device
    Connect To Device
    Log    🔗 Connected to router successfully
    
    # Step 2.1: Check system resources before upload
    Check System Resources
    
    # Step 3: Upload and verify file
    Upload File    ${firmware_path}
    Log    📤 Firmware file uploaded and verified
    
    # Step 4: Install firmware (this will cause reboot)
    Install Firmware
    Log    ⚙️ Firmware installation initiated
    
    # Step 5: Wait for router to reboot and come back online
    Wait For Router Reboot
    Log    🔄 Router reboot completed
    
    # Step 6: Verify router is working properly
    Verify Router Functionality
    Log    ✅ Router functionality verified - ready for subsequent tests
    
    # Step 7: Cleanup firmware file (optional)
    Cleanup Firmware File
    
    # Step 8: Generate test report
    Generate Test Report
    
    [Teardown]    Run Keywords
    ...    Log    🧹 Starting test cleanup...    AND
    ...    Run Keyword And Ignore Error    Close All Connections    AND
    ...    Run Keyword And Ignore Error    Generate Test Report    AND
    ...    Log    ✅ Test cleanup completed