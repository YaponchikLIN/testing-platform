-- Создание базы данных для платформы тестирования
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица для хранения информации о тестах
CREATE TABLE IF NOT EXISTS tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id VARCHAR(50) NOT NULL,
    test_name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения результатов выполнения тестов
CREATE TABLE IF NOT EXISTS test_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- idle, running, executing, completed, error
    time_start TIMESTAMP WITH TIME ZONE,
    time_end TIMESTAMP WITH TIME ZONE,
    execution_time INTEGER, -- время выполнения в секундах
    progress INTEGER DEFAULT 0, -- прогресс в процентах
    result_passed BOOLEAN,
    result_details TEXT,
    result_data JSONB, -- полные данные результата в JSON формате
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения результатов SIM тестов
CREATE TABLE IF NOT EXISTS sim_test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES test_executions(id) ON DELETE CASCADE,
    slot_number INTEGER NOT NULL,
    state_failed_reason VARCHAR(100),
    active VARCHAR(10),
    connected VARCHAR(20),
    ping_result VARCHAR(20),
    packet_loss VARCHAR(20),
    response_time VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения результатов Ethernet тестов
CREATE TABLE IF NOT EXISTS ethernet_test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES test_executions(id) ON DELETE CASCADE,
    interface_name VARCHAR(50) NOT NULL,
    ip_address INET,
    ping_result VARCHAR(20),
    packet_loss DECIMAL(5,2),
    response_time DECIMAL(10,3),
    status VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_test_executions_test_id ON test_executions(test_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_status ON test_executions(status);
CREATE INDEX IF NOT EXISTS idx_test_executions_created_at ON test_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_sim_results_execution_id ON sim_test_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_ethernet_results_execution_id ON ethernet_test_results(execution_id);

-- Вставка базовых тестов
INSERT INTO tests (test_id, test_name, description) VALUES 
('sim', 'SIM Card Test', 'Тестирование SIM-карт через ubus call mmm getStatus'),
('ethernets', 'Ethernet Interface Test', 'Тестирование интерфейсов Cisco с интеграцией во фронтенд'),
('wifi', 'WiFi Test', 'Тестирование WiFi соединения'),
('all', 'All Tests', 'Последовательное выполнение всех тестов')
ON CONFLICT DO NOTHING;

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_tests_updated_at BEFORE UPDATE ON tests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_executions_updated_at BEFORE UPDATE ON test_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();