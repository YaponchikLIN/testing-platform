"""
GPIO утилиты для Robot Framework тестов
Предоставляет высокоуровневые функции для работы с GPIO в тестах
"""

import subprocess
import json
import os
import time
from typing import Dict, List, Any, Optional


class GPIOTestUtils:
    """Утилиты для тестирования GPIO функциональности"""
    
    def __init__(self, project_root: str = None):
        """
        Инициализация утилит GPIO
        
        Args:
            project_root: Корневая директория проекта
        """
        if project_root is None:
            # Определяем корневую директорию проекта
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.project_root = os.path.dirname(current_dir)
        else:
            self.project_root = project_root
            
        self.gpio_manager_path = os.path.join(self.project_root, 'services', 'gpio_manager.js')
        self.gpio_example_path = os.path.join(self.project_root, 'services', 'gpio_reset_example.js')
    
    def reset_gpio_pins(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Сбрасывает GPIO пины в определенное состояние используя новый класс GPIOReset
        
        Args:
            timeout: Таймаут выполнения в секундах
            
        Returns:
            Словарь с результатами выполнения
        """
        try:
            # Создаем простой скрипт для тестирования GPIOReset
            test_script = '''
const { GPIOReset } = require('./gpio_manager');

console.log('🚀 Создание экземпляра GPIOReset с автоматической инициализацией...');
const gpioReset = new GPIOReset();

setTimeout(() => {
    console.log('📊 Показ статуса GPIO:');
    gpioReset.showStatus();
    
    const info = gpioReset.getInfo();
    console.log('📋 Информация о GPIO:', JSON.stringify(info, null, 2));
    
    console.log('🧹 Очистка ресурсов...');
    gpioReset.cleanup();
    
    console.log('✅ Тест завершен успешно');
}, 2000);
'''
            
            # Записываем временный скрипт
            temp_script_path = os.path.join(self.project_root, 'services', 'temp_gpio_test.js')
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(test_script)
            
            try:
                result = subprocess.run(
                    ['node', temp_script_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.path.join(self.project_root, 'services')
                )
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_script_path):
                    os.remove(temp_script_path)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Timeout after {timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def test_gpio_functionality(self, timeout: int = 45) -> Dict[str, Any]:
        """
        Тестирует функциональность GPIO после сброса
        
        Args:
            timeout: Таймаут выполнения в секундах
            
        Returns:
            Словарь с результатами тестирования
        """
        try:
            result = subprocess.run(
                ['node', self.gpio_example_path, 'test'],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Timeout after {timeout} seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def check_gpio_configuration(self, expected_pins: List[int] = None) -> Dict[str, Any]:
        """
        Проверяет конфигурацию GPIO пинов
        
        Args:
            expected_pins: Список ожидаемых пинов для проверки
            
        Returns:
            Словарь с результатами проверки
        """
        if expected_pins is None:
            expected_pins = [8, 10, 11, 12, 13, 15]
        
        # Создаем временный скрипт для проверки
        check_script = f"""
const {{ resetSpecificGPIOs, cleanupGPIOs }} = require('./services/gpio_manager');

async function checkConfiguration() {{
    try {{
        const result = resetSpecificGPIOs();
        if (!result.success) {{
            console.error('Failed to reset GPIO pins');
            process.exit(1);
        }}
        
        const configurations = [];
        result.gpioInstances.forEach(gpio => {{
            const info = gpio.getInfo();
            configurations.push({{
                pin: info.pin,
                direction: info.direction,
                state: info.state
            }});
        }});
        
        console.log(JSON.stringify(configurations, null, 2));
        
        // Очистка ресурсов
        cleanupGPIOs(result.gpioInstances);
        process.exit(0);
    }} catch (error) {{
        console.error('Error:', error.message);
        process.exit(1);
    }}
}}

checkConfiguration();
"""
        
        # Записываем временный скрипт
        temp_script_path = os.path.join(self.project_root, 'temp_gpio_check.js')
        try:
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(check_script)
            
            # Выполняем скрипт
            result = subprocess.run(
                ['node', temp_script_path],
                capture_output=True,
                text=True,
                timeout=20,
                cwd=self.project_root
            )
            
            # Удаляем временный файл
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            
            if result.returncode == 0:
                try:
                    configurations = json.loads(result.stdout)
                    return {
                        'success': True,
                        'configurations': configurations,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'configurations': [],
                        'stdout': result.stdout,
                        'stderr': f'Failed to parse JSON: {result.stderr}'
                    }
            else:
                return {
                    'success': False,
                    'configurations': [],
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except Exception as e:
            # Убеждаемся, что временный файл удален
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            
            return {
                'success': False,
                'configurations': [],
                'stdout': '',
                'stderr': str(e)
            }
    
    def verify_gpio_pin_configuration(self, pin: int, expected_direction: str, expected_state: Optional[int] = None) -> bool:
        """
        Проверяет конфигурацию конкретного GPIO пина
        
        Args:
            pin: Номер GPIO пина
            expected_direction: Ожидаемое направление ('in' или 'out')
            expected_state: Ожидаемое состояние (для выходных пинов)
            
        Returns:
            True если конфигурация соответствует ожидаемой
        """
        config_result = self.check_gpio_configuration()
        
        if not config_result['success']:
            return False
        
        for config in config_result['configurations']:
            if config['pin'] == pin:
                if config['direction'] != expected_direction:
                    return False
                
                if expected_state is not None and config['state'] != expected_state:
                    return False
                
                return True
        
        return False
    
    def wait_for_gpio_ready(self, max_wait_time: int = 10) -> bool:
        """
        Ожидает готовности GPIO системы
        
        Args:
            max_wait_time: Максимальное время ожидания в секундах
            
        Returns:
            True если система готова
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                result = self.reset_gpio_pins(timeout=5)
                if result['success']:
                    return True
            except:
                pass
            
            time.sleep(0.5)
        
        return False
    
    def get_gpio_status_summary(self) -> str:
        """
        Получает краткую сводку состояния GPIO
        
        Returns:
            Строка с описанием состояния GPIO
        """
        config_result = self.check_gpio_configuration()
        
        if not config_result['success']:
            return "❌ Не удалось получить состояние GPIO"
        
        summary_lines = ["📊 Состояние GPIO пинов:"]
        
        for config in config_result['configurations']:
            pin = config['pin']
            direction = config['direction'].upper()
            state = config.get('state', 'N/A')
            
            if direction == 'IN':
                summary_lines.append(f"  • GPIO {pin}: {direction}")
            else:
                summary_lines.append(f"  • GPIO {pin}: {direction} = {state}")
        
        return "\n".join(summary_lines)


# Robot Framework библиотека
class GPIOLibrary:
    """Robot Framework библиотека для работы с GPIO"""
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    
    def __init__(self):
        self.utils = GPIOTestUtils()
    
    def reset_gpio_pins(self, timeout=30):
        """Сбрасывает GPIO пины в определенное состояние"""
        result = self.utils.reset_gpio_pins(int(timeout))
        if not result['success']:
            raise AssertionError(f"Failed to reset GPIO pins: {result['stderr']}")
        return result['stdout']
    
    def test_gpio_functionality(self, timeout=45):
        """Тестирует функциональность GPIO"""
        result = self.utils.test_gpio_functionality(int(timeout))
        if not result['success']:
            raise AssertionError(f"GPIO functionality test failed: {result['stderr']}")
        return result['stdout']
    
    def verify_gpio_pin_configuration(self, pin, direction, state=None):
        """Проверяет конфигурацию GPIO пина"""
        pin = int(pin)
        expected_state = int(state) if state is not None else None
        
        if not self.utils.verify_gpio_pin_configuration(pin, direction, expected_state):
            raise AssertionError(f"GPIO {pin} configuration mismatch. Expected: {direction}" + 
                               (f" = {expected_state}" if expected_state is not None else ""))
    
    def wait_for_gpio_ready(self, max_wait_time=10):
        """Ожидает готовности GPIO системы"""
        if not self.utils.wait_for_gpio_ready(int(max_wait_time)):
            raise AssertionError(f"GPIO system not ready after {max_wait_time} seconds")
    
    def get_gpio_status_summary(self):
        """Получает краткую сводку состояния GPIO"""
        return self.utils.get_gpio_status_summary()
    
    def check_gpio_configuration(self):
        """Проверяет конфигурацию всех GPIO пинов"""
        result = self.utils.check_gpio_configuration()
        if not result['success']:
            raise AssertionError(f"Failed to check GPIO configuration: {result['stderr']}")
        return result['configurations']


if __name__ == "__main__":
    # Простой тест утилит
    utils = GPIOTestUtils()
    
    print("🧪 Тестирование GPIO утилит...")
    
    # Тест сброса GPIO
    print("\n1. Тестирование сброса GPIO...")
    reset_result = utils.reset_gpio_pins()
    print(f"   Результат: {'✅ Успех' if reset_result['success'] else '❌ Ошибка'}")
    if not reset_result['success']:
        print(f"   Ошибка: {reset_result['stderr']}")
    
    # Тест проверки конфигурации
    print("\n2. Проверка конфигурации GPIO...")
    config_result = utils.check_gpio_configuration()
    print(f"   Результат: {'✅ Успех' if config_result['success'] else '❌ Ошибка'}")
    if config_result['success']:
        print("   Конфигурации:")
        for config in config_result['configurations']:
            print(f"     GPIO {config['pin']}: {config['direction']} = {config.get('state', 'N/A')}")
    
    # Сводка состояния
    print("\n3. Сводка состояния GPIO:")
    print(utils.get_gpio_status_summary())
    
    print("\n✅ Тестирование завершено!")