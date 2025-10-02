# Руководство по развертыванию

## Обзор

Данное руководство описывает процесс развертывания платформы тестирования RTK в различных окружениях: разработка, тестирование и продакшн.

## Системные требования

### Минимальные требования

- **CPU**: 2 ядра, 2.0 GHz
- **RAM**: 4 GB
- **Диск**: 20 GB свободного места
- **ОС**: Ubuntu 20.04+, CentOS 8+, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

### Рекомендуемые требования

- **CPU**: 4 ядра, 3.0 GHz
- **RAM**: 8 GB
- **Диск**: 50 GB SSD
- **Сеть**: 1 Gbps

## Предварительная настройка

### 1. Установка Docker

#### Ubuntu/Debian
```bash
# Обновление пакетов
sudo apt update

# Установка зависимостей
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### CentOS/RHEL
```bash
# Установка Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка пользователя

```bash
# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перезагрузка для применения изменений
sudo reboot
```

## Развертывание для разработки

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd testing-platform
```

### 2. Настройка переменных окружения

```bash
# Создание файла .env для API сервиса
cd services/api-service
cat > .env << EOF
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testing_platform
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
SECRET_KEY=your-secret-key-here
DEBUG=true
EOF
```

### 3. Запуск базы данных

```bash
# Возврат в корневую директорию
cd ../../

# Запуск PostgreSQL
docker-compose up -d postgres

# Проверка статуса
docker-compose ps
```

### 4. Установка зависимостей Python

```bash
cd services/api-service

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 5. Установка зависимостей Node.js

```bash
cd ../../frontend

# Установка зависимостей
npm install
```

### 6. Запуск сервисов

```bash
# Терминал 1: API сервис
cd services/api-service
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Frontend
cd frontend
npm run serve
```

### 7. Проверка работоспособности

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

## Развертывание для тестирования

### 1. Подготовка окружения

```bash
# Клонирование репозитория
git clone <repository-url>
cd testing-platform

# Создание конфигурации для тестирования
cp docker-compose.yml docker-compose.test.yml
```

### 2. Настройка конфигурации

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: testing_platform_postgres_test
    environment:
      POSTGRES_DB: testing_platform_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  api:
    build: ./services/api-service
    container_name: testing_platform_api_test
    environment:
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: testing_platform_test
      DATABASE_USER: test_user
      DATABASE_PASSWORD: test_password
    ports:
      - "8001:8000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    container_name: testing_platform_frontend_test
    ports:
      - "3001:80"
    depends_on:
      - api

volumes:
  postgres_test_data:
```

### 3. Создание Dockerfile для API

```dockerfile
# services/api-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Создание Dockerfile для Frontend

```dockerfile
# frontend/Dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 5. Запуск тестового окружения

```bash
# Сборка и запуск
docker-compose -f docker-compose.test.yml up --build -d

# Проверка статуса
docker-compose -f docker-compose.test.yml ps

# Просмотр логов
docker-compose -f docker-compose.test.yml logs -f
```

## Развертывание в продакшн

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y nginx certbot python3-certbot-nginx ufw

# Настройка файрвола
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Настройка SSL сертификата

```bash
# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавить строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Конфигурация Nginx

```nginx
# /etc/nginx/sites-available/testing-platform
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Продакшн конфигурация Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: testing_platform_postgres_prod
    environment:
      POSTGRES_DB: testing_platform
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - app-network

  api:
    build: ./services/api-service
    container_name: testing_platform_api_prod
    environment:
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: testing_platform
      DATABASE_USER: ${DB_USER}
      DATABASE_PASSWORD: ${DB_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: false
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - app-network

  frontend:
    build: ./frontend
    container_name: testing_platform_frontend_prod
    ports:
      - "127.0.0.1:3000:80"
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_prod_data:

networks:
  app-network:
    driver: bridge
```

### 5. Настройка переменных окружения

```bash
# Создание .env файла для продакшн
cat > .env << EOF
DB_USER=prod_user
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
EOF

# Установка прав доступа
chmod 600 .env
```

### 6. Запуск продакшн окружения

```bash
# Запуск сервисов
docker-compose -f docker-compose.prod.yml up -d

# Включение автозапуска
sudo systemctl enable docker

# Создание systemd сервиса
sudo cat > /etc/systemd/system/testing-platform.service << EOF
[Unit]
Description=Testing Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/testing-platform
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable testing-platform
sudo systemctl start testing-platform
```

## Мониторинг и логирование

### 1. Настройка логирования

```bash
# Создание директории для логов
sudo mkdir -p /var/log/testing-platform

# Настройка ротации логов
sudo cat > /etc/logrotate.d/testing-platform << EOF
/var/log/testing-platform/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

### 2. Мониторинг с помощью Docker

```bash
# Просмотр статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Мониторинг ресурсов
docker stats

# Проверка здоровья сервисов
docker-compose exec api curl http://localhost:8000/health
```

### 3. Настройка алертов

```bash
# Создание скрипта проверки здоровья
cat > /opt/testing-platform/health-check.sh << EOF
#!/bin/bash

API_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "API service is down! HTTP code: $RESPONSE"
    # Отправка уведомления (email, Slack, etc.)
    exit 1
fi

echo "API service is healthy"
exit 0
EOF

chmod +x /opt/testing-platform/health-check.sh

# Добавление в crontab
echo "*/5 * * * * /opt/testing-platform/health-check.sh" | crontab -
```

## Резервное копирование

### 1. Автоматическое резервное копирование БД

```bash
# Создание скрипта резервного копирования
cat > /opt/testing-platform/backup.sh << EOF
#!/bin/bash

BACKUP_DIR="/opt/backups/testing-platform"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="testing_platform_postgres_prod"

mkdir -p $BACKUP_DIR

# Создание бэкапа базы данных
docker exec $CONTAINER_NAME pg_dump -U prod_user testing_platform | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
EOF

chmod +x /opt/testing-platform/backup.sh

# Добавление в crontab (ежедневно в 2:00)
echo "0 2 * * * /opt/testing-platform/backup.sh" | crontab -
```

### 2. Восстановление из резервной копии

```bash
# Восстановление базы данных
gunzip -c /opt/backups/testing-platform/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
docker exec -i testing_platform_postgres_prod psql -U prod_user testing_platform
```

## Обновление системы

### 1. Обновление кода

```bash
# Остановка сервисов
docker-compose -f docker-compose.prod.yml down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose -f docker-compose.prod.yml up --build -d
```

### 2. Миграция базы данных

```bash
# Создание бэкапа перед миграцией
./backup.sh

# Применение миграций
docker-compose -f docker-compose.prod.yml exec api python migrate.py
```

## Устранение неполадок

### Частые проблемы

1. **Контейнер не запускается**
```bash
# Проверка логов
docker-compose logs service_name

# Проверка конфигурации
docker-compose config
```

2. **База данных недоступна**
```bash
# Проверка подключения
docker-compose exec postgres psql -U prod_user -d testing_platform

# Проверка статуса
docker-compose ps postgres
```

3. **Проблемы с SSL**
```bash
# Проверка сертификата
sudo certbot certificates

# Обновление сертификата
sudo certbot renew
```

## Безопасность

### Рекомендации по безопасности

1. **Регулярные обновления**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade

# Обновление Docker образов
docker-compose pull
```

2. **Настройка файрвола**
```bash
# Ограничение доступа к базе данных
sudo ufw deny 5432

# Разрешение только необходимых портов
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
```

3. **Мониторинг безопасности**
```bash
# Установка fail2ban
sudo apt install fail2ban

# Настройка для nginx
sudo cat > /etc/fail2ban/jail.local << EOF
[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
```

## Поддержка

Для получения поддержки по развертыванию:
1. Проверьте логи сервисов
2. Изучите документацию
3. Создайте issue в GitHub репозитории
4. Обратитесь к команде разработки