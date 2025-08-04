# Примеры конфигурации

Данный документ содержит готовые примеры конфигурации для различных сред развертывания системы RAG с интеграцией Yandex Cloud.

## 📋 Обзор

Каждая среда имеет свои особенности и требования к конфигурации:

- **Development** - максимальная отладочная информация, fallback на Ollama
- **Testing** - стабильная конфигурация для автоматических тестов
- **Staging** - максимально близко к production, но с дополнительным логированием
- **Production** - оптимизированная конфигурация для высокой производительности

## 🔧 Development Environment

### .env.development

```bash
# ===========================================
# DEVELOPMENT CONFIGURATION
# ===========================================

# Yandex Cloud Configuration
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxx
YANDEX_FOLDER_ID=b1g2xxxxxxxxxxxxxxxxx
USE_YANDEX_CLOUD=true

# Yandex Cloud Models
YANDEX_LLM_MODEL=yandexgpt-lite
YANDEX_EMBEDDING_MODEL=text-search-doc

# Yandex Cloud API Settings (развитие)
YANDEX_MAX_TOKENS=1000
YANDEX_TEMPERATURE=0.3
YANDEX_TIMEOUT=60
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net

# Retry settings (более терпимые для разработки)
YANDEX_MAX_RETRIES=5
YANDEX_RETRY_DELAY=2.0
YANDEX_FALLBACK_TO_OLLAMA=true
YANDEX_FALLBACK_TIMEOUT=120

# Performance settings (консервативные)
YANDEX_MAX_REQUESTS_PER_MINUTE=30
YANDEX_MAX_CONCURRENT=3

# Caching (включено для ускорения разработки)
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_DIR=/app/files/dev_cache
YANDEX_CACHE_TTL_HOURS=6
YANDEX_EMBEDDINGS_CACHE_DIR=/app/files/dev_embeddings_cache

# Monitoring (полное логирование)
YANDEX_ENABLE_METRICS=true
YANDEX_METRICS_FILE=/app/files/dev_yandex_metrics.json
YANDEX_ENABLE_PERFORMANCE_MONITORING=true

# Ollama Configuration (для fallback)
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=90
OLLAMA_MAX_RETRIES=3
OLLAMA_LLM_MODEL=gemma3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database Configuration
DATABASE_URL=mysql+mysqlconnector://root:devpassword@localhost:3306/rag_development
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Application Configuration
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### docker-compose.dev.yml

```yaml
version: '3.8'

services:
  rag-app-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - dev_cache:/app/files/dev_cache
      - dev_embeddings:/app/files/dev_embeddings_cache
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    env_file:
      - .env.development
    depends_on:
      - mysql-dev
      - ollama-dev
    restart: unless-stopped

  mysql-dev:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: devpassword
      MYSQL_DATABASE: rag_development
      MYSQL_USER: devuser
      MYSQL_PASSWORD: devpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_dev_data:/var/lib/mysql
    restart: unless-stopped

  ollama-dev:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_dev_data:/root/.ollama
    restart: unless-stopped

volumes:
  dev_cache:
  dev_embeddings:
  mysql_dev_data:
  ollama_dev_data:
```

## 🧪 Testing Environment

### .env.testing

```bash
# ===========================================
# TESTING CONFIGURATION
# ===========================================

# Yandex Cloud Configuration (тестовые ключи)
YANDEX_API_KEY=AQVNtest_key_for_automated_tests
YANDEX_FOLDER_ID=b1g2test_folder_id
USE_YANDEX_CLOUD=true

# Yandex Cloud Models (стабильные модели)
YANDEX_LLM_MODEL=yandexgpt
YANDEX_EMBEDDING_MODEL=text-search-doc

# Yandex Cloud API Settings (быстрые ответы для тестов)
YANDEX_MAX_TOKENS=500
YANDEX_TEMPERATURE=0.0
YANDEX_TIMEOUT=30
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net

# Retry settings (быстрые фейлы для тестов)
YANDEX_MAX_RETRIES=2
YANDEX_RETRY_DELAY=0.5
YANDEX_FALLBACK_TO_OLLAMA=false
YANDEX_FALLBACK_TIMEOUT=30

# Performance settings
YANDEX_MAX_REQUESTS_PER_MINUTE=100
YANDEX_MAX_CONCURRENT=5

# Caching (отключено для чистых тестов)
YANDEX_ENABLE_CACHING=false
YANDEX_CACHE_DIR=/tmp/test_cache
YANDEX_CACHE_TTL_HOURS=1
YANDEX_EMBEDDINGS_CACHE_DIR=/tmp/test_embeddings_cache

# Monitoring (минимальное для тестов)
YANDEX_ENABLE_METRICS=false
YANDEX_METRICS_FILE=/tmp/test_yandex_metrics.json
YANDEX_ENABLE_PERFORMANCE_MONITORING=false

# Ollama Configuration (для некоторых тестов)
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=30
OLLAMA_MAX_RETRIES=1
OLLAMA_LLM_MODEL=gemma3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database Configuration (тестовая БД)
DATABASE_URL=mysql+mysqlconnector://test_user:test_password@localhost:3306/rag_test
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=10
DB_POOL_RECYCLE=300

# Application Configuration
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=testing
SECRET_KEY=test-secret-key-for-testing-only
ALLOWED_HOSTS=localhost,testserver
```

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html
    --cov-report=term-missing
env_files = .env.testing
markers =
    unit: Unit tests
    integration: Integration tests
    yandex: Tests requiring Yandex Cloud API
    ollama: Tests requiring Ollama
    slow: Slow tests
```

## 🎭 Staging Environment

### .env.staging

```bash
# ===========================================
# STAGING CONFIGURATION
# ===========================================

# Yandex Cloud Configuration
YANDEX_API_KEY=AQVNstaging_api_key_here
YANDEX_FOLDER_ID=b1g2staging_folder_id
USE_YANDEX_CLOUD=true

# Yandex Cloud Models
YANDEX_LLM_MODEL=yandexgpt
YANDEX_EMBEDDING_MODEL=text-search-doc

# Yandex Cloud API Settings
YANDEX_MAX_TOKENS=1500
YANDEX_TEMPERATURE=0.1
YANDEX_TIMEOUT=45
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net

# Retry settings (умеренные)
YANDEX_MAX_RETRIES=3
YANDEX_RETRY_DELAY=1.5
YANDEX_FALLBACK_TO_OLLAMA=false
YANDEX_FALLBACK_TIMEOUT=60

# Performance settings (средние нагрузки)
YANDEX_MAX_REQUESTS_PER_MINUTE=80
YANDEX_MAX_CONCURRENT=8

# Caching (оптимизированное)
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_DIR=/app/files/staging_cache
YANDEX_CACHE_TTL_HOURS=12
YANDEX_EMBEDDINGS_CACHE_DIR=/app/files/staging_embeddings_cache

# Monitoring (полное)
YANDEX_ENABLE_METRICS=true
YANDEX_METRICS_FILE=/app/files/staging_yandex_metrics.json
YANDEX_ENABLE_PERFORMANCE_MONITORING=true

# Ollama Configuration (не используется в staging)
OLLAMA_HOST=http://ollama-staging:11434
OLLAMA_TIMEOUT=60
OLLAMA_MAX_RETRIES=2

# Database Configuration
DATABASE_URL=mysql+mysqlconnector://staging_user:staging_secure_password@staging-mysql:3306/rag_staging
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25
DB_POOL_TIMEOUT=45
DB_POOL_RECYCLE=2700

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=staging
SECRET_KEY=staging-secret-key-change-in-production
ALLOWED_HOSTS=staging.yourdomain.com,staging-api.yourdomain.com
```

### docker-compose.staging.yml

```yaml
version: '3.8'

services:
  rag-app-staging:
    image: your-registry/rag-app:staging
    ports:
      - "8000:8000"
    volumes:
      - staging_cache:/app/files/staging_cache
      - staging_embeddings:/app/files/staging_embeddings_cache
      - staging_logs:/app/logs
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    env_file:
      - .env.staging
    depends_on:
      - mysql-staging
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mysql-staging:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: staging_root_password
      MYSQL_DATABASE: rag_staging
      MYSQL_USER: staging_user
      MYSQL_PASSWORD: staging_secure_password
    volumes:
      - mysql_staging_data:/var/lib/mysql
      - ./mysql/staging.cnf:/etc/mysql/conf.d/staging.cnf
    restart: unless-stopped

  nginx-staging:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - staging_ssl_certs:/etc/ssl/certs
    depends_on:
      - rag-app-staging
    restart: unless-stopped

volumes:
  staging_cache:
  staging_embeddings:
  staging_logs:
  mysql_staging_data:
  staging_ssl_certs:
```

## 🚀 Production Environment

### .env.production

```bash
# ===========================================
# PRODUCTION CONFIGURATION
# ===========================================

# Yandex Cloud Configuration
YANDEX_API_KEY=AQVNproduction_api_key_here
YANDEX_FOLDER_ID=b1g2production_folder_id
USE_YANDEX_CLOUD=true

# Yandex Cloud Models (стабильные)
YANDEX_LLM_MODEL=yandexgpt
YANDEX_EMBEDDING_MODEL=text-search-doc

# Yandex Cloud API Settings (оптимизированные)
YANDEX_MAX_TOKENS=2000
YANDEX_TEMPERATURE=0.05
YANDEX_TIMEOUT=60
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net

# Retry settings (продакшн)
YANDEX_MAX_RETRIES=3
YANDEX_RETRY_DELAY=1.0
YANDEX_FALLBACK_TO_OLLAMA=false
YANDEX_FALLBACK_TIMEOUT=30

# Performance settings (высокие нагрузки)
YANDEX_MAX_REQUESTS_PER_MINUTE=200
YANDEX_MAX_CONCURRENT=20

# Caching (агрессивное кэширование)
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_DIR=/app/files/cache
YANDEX_CACHE_TTL_HOURS=48
YANDEX_EMBEDDINGS_CACHE_DIR=/app/files/embeddings_cache

# Monitoring (полное с алертами)
YANDEX_ENABLE_METRICS=true
YANDEX_METRICS_FILE=/app/files/yandex_metrics.json
YANDEX_ENABLE_PERFORMANCE_MONITORING=true

# Database Configuration (продакшн пул)
DATABASE_URL=mysql+mysqlconnector://prod_user:very_secure_production_password@prod-mysql-cluster:3306/rag_production
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50
DB_POOL_TIMEOUT=60
DB_POOL_RECYCLE=3600

# Application Configuration
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production
SECRET_KEY=super-secure-production-secret-key-change-me
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com,www.yourdomain.com

# Security settings
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
```

### docker-compose.production.yml

```yaml
version: '3.8'

services:
  rag-app-prod:
    image: your-registry/rag-app:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    volumes:
      - prod_cache:/app/files/cache
      - prod_embeddings:/app/files/embeddings_cache
      - prod_logs:/app/logs
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    env_file:
      - .env.production
    depends_on:
      - mysql-prod
      - redis-prod
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  mysql-prod:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
      MYSQL_DATABASE: rag_production
      MYSQL_USER: prod_user
      MYSQL_PASSWORD_FILE: /run/secrets/mysql_password
    volumes:
      - mysql_prod_data:/var/lib/mysql
      - ./mysql/production.cnf:/etc/mysql/conf.d/production.cnf
    secrets:
      - mysql_root_password
      - mysql_password
    restart: unless-stopped
    command: --default-authentication-plugin=mysql_native_password

  redis-prod:
    image: redis:7-alpine
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

  nginx-prod:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/production.conf:/etc/nginx/nginx.conf
      - prod_ssl_certs:/etc/ssl/certs
      - prod_logs:/var/log/nginx
    depends_on:
      - rag-app-prod
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    restart: unless-stopped

volumes:
  prod_cache:
  prod_embeddings:
  prod_logs:
  mysql_prod_data:
  redis_prod_data:
  prod_ssl_certs:
  prometheus_data:
  grafana_data:

secrets:
  mysql_root_password:
    file: ./secrets/mysql_root_password.txt
  mysql_password:
    file: ./secrets/mysql_password.txt
```

## ☸️ Kubernetes Configuration

### namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: rag-system
  labels:
    name: rag-system
    environment: production
```

### configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
  namespace: rag-system
data:
  USE_YANDEX_CLOUD: "true"
  YANDEX_LLM_MODEL: "yandexgpt"
  YANDEX_EMBEDDING_MODEL: "text-search-doc"
  YANDEX_MAX_TOKENS: "2000"
  YANDEX_TEMPERATURE: "0.05"
  YANDEX_TIMEOUT: "60"
  YANDEX_MAX_RETRIES: "3"
  YANDEX_RETRY_DELAY: "1.0"
  YANDEX_FALLBACK_TO_OLLAMA: "false"
  YANDEX_MAX_REQUESTS_PER_MINUTE: "200"
  YANDEX_MAX_CONCURRENT: "20"
  YANDEX_ENABLE_CACHING: "true"
  YANDEX_CACHE_TTL_HOURS: "48"
  YANDEX_ENABLE_METRICS: "true"
  YANDEX_ENABLE_PERFORMANCE_MONITORING: "true"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  ENVIRONMENT: "production"
  DB_POOL_SIZE: "30"
  DB_MAX_OVERFLOW: "50"
  DB_POOL_TIMEOUT: "60"
  DB_POOL_RECYCLE: "3600"
```

### secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
  namespace: rag-system
type: Opaque
stringData:
  YANDEX_API_KEY: "your-production-api-key-here"
  YANDEX_FOLDER_ID: "your-production-folder-id-here"
  DATABASE_URL: "mysql+mysqlconnector://prod_user:secure_password@mysql-service:3306/rag_production"
  SECRET_KEY: "super-secure-production-secret-key"
```

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-app
  namespace: rag-system
  labels:
    app: rag-app
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-app
  template:
    metadata:
      labels:
        app: rag-app
        version: v1
    spec:
      containers:
      - name: rag-app
        image: your-registry/rag-app:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: rag-config
        - secretRef:
            name: rag-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: cache-volume
          mountPath: /app/files/cache
        - name: embeddings-volume
          mountPath: /app/files/embeddings_cache
      volumes:
      - name: cache-volume
        persistentVolumeClaim:
          claimName: rag-cache-pvc
      - name: embeddings-volume
        persistentVolumeClaim:
          claimName: rag-embeddings-pvc
```

## 🔄 Migration Scripts

### migrate_config.py

```python
#!/usr/bin/env python3
"""
Скрипт для миграции конфигурации между средами
"""

import os
import shutil
import argparse
from pathlib import Path

def migrate_config(source_env: str, target_env: str, dry_run: bool = False):
    """Миграция конфигурации между средами"""
    
    source_file = f".env.{source_env}"
    target_file = f".env.{target_env}"
    
    if not Path(source_file).exists():
        print(f"❌ Файл {source_file} не найден")
        return False
    
    if Path(target_file).exists() and not dry_run:
        backup_file = f"{target_file}.backup"
        shutil.copy2(target_file, backup_file)
        print(f"📦 Создана резервная копия: {backup_file}")
    
    # Читаем исходную конфигурацию
    with open(source_file, 'r') as f:
        config_lines = f.readlines()
    
    # Применяем изменения для целевой среды
    updated_lines = []
    for line in config_lines:
        if line.startswith('ENVIRONMENT='):
            updated_lines.append(f'ENVIRONMENT={target_env}\n')
        elif line.startswith('DEBUG=') and target_env == 'production':
            updated_lines.append('DEBUG=false\n')
        elif line.startswith('LOG_LEVEL=') and target_env == 'production':
            updated_lines.append('LOG_LEVEL=WARNING\n')
        else:
            updated_lines.append(line)
    
    if dry_run:
        print(f"🔍 Предварительный просмотр изменений для {target_file}:")
        for line in updated_lines:
            print(f"  {line.rstrip()}")
        return True
    
    # Записываем обновленную конфигурацию
    with open(target_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Конфигурация мигрирована: {source_file} → {target_file}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Миграция конфигурации между средами")
    parser.add_argument("source", help="Исходная среда (development, staging, production)")
    parser.add_argument("target", help="Целевая среда (development, staging, production)")
    parser.add_argument("--dry-run", action="store_true", help="Предварительный просмотр без изменений")
    
    args = parser.parse_args()
    migrate_config(args.source, args.target, args.dry_run)
```

## 📊 Monitoring Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'rag-app'
    static_configs:
      - targets: ['rag-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-exporter:9104']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### grafana-dashboard.json

```json
{
  "dashboard": {
    "id": null,
    "title": "RAG System with Yandex Cloud",
    "tags": ["rag", "yandex-cloud", "llm"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Yandex Cloud API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(yandex_api_requests_total[5m])",
            "legendFormat": "{{method}} - {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(yandex_api_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 🔧 Utility Scripts

### validate_config.sh

```bash
#!/bin/bash
# Скрипт валидации конфигурации

set -e

ENV=${1:-development}
CONFIG_FILE=".env.${ENV}"

echo "🔍 Валидация конфигурации для среды: ${ENV}"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Файл конфигурации не найден: $CONFIG_FILE"
    exit 1
fi

# Загружаем переменные
source "$CONFIG_FILE"

# Проверяем обязательные переменные
REQUIRED_VARS=(
    "YANDEX_API_KEY"
    "YANDEX_FOLDER_ID"
    "DATABASE_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Обязательная переменная не установлена: $var"
        exit 1
    fi
done

# Проверяем формат API ключа
if [[ ${#YANDEX_API_KEY} -lt 20 ]]; then
    echo "❌ YANDEX_API_KEY слишком короткий"
    exit 1
fi

# Проверяем подключение к базе данных
echo "🔍 Проверка подключения к базе данных..."
python3 -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine('$DATABASE_URL')
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('✅ Подключение к БД успешно')
except Exception as e:
    print(f'❌ Ошибка подключения к БД: {e}')
    exit(1)
"

# Проверяем конфигурацию Yandex Cloud
echo "🔍 Проверка конфигурации Yandex Cloud..."
python3 -c "
from config_utils import validate_all_config_new
try:
    config = validate_all_config_new()
    print('✅ Конфигурация Yandex Cloud валидна')
except Exception as e:
    print(f'❌ Ошибка конфигурации Yandex Cloud: {e}')
    exit(1)
"

echo "✅ Все проверки пройдены успешно!"
```

### setup_environment.sh

```bash
#!/bin/bash
# Скрипт настройки среды

ENV=${1:-development}
echo "🚀 Настройка среды: $ENV"

# Создаем необходимые директории
mkdir -p files/cache
mkdir -p files/embeddings_cache
mkdir -p logs
mkdir -p secrets

# Копируем конфигурацию
if [[ ! -f ".env.${ENV}" ]]; then
    echo "📋 Создание конфигурации из шаблона..."
    cp ".env.example" ".env.${ENV}"
    echo "⚠️  Не забудьте отредактировать .env.${ENV}"
fi

# Устанавливаем права доступа
chmod 600 .env.${ENV}
chmod 700 secrets/

# Проверяем зависимости
echo "🔍 Проверка зависимостей..."
python3 -m pip install -r requirements.txt

echo "✅ Среда $ENV настроена!"
echo "📝 Следующие шаги:"
echo "   1. Отредактируйте .env.${ENV}"
echo "   2. Запустите: ./validate_config.sh ${ENV}"
echo "   3. Запустите приложение"
```

## 🚀 Дополнительные сценарии развертывания

### Multi-tenant Configuration

```bash
# .env.multitenant
# Конфигурация для мультитенантной среды

# Yandex Cloud (общие настройки)
USE_YANDEX_CLOUD=true
YANDEX_API_KEY=AQVNmultitenant_api_key
YANDEX_FOLDER_ID=b1g2multitenant_folder

# Разные модели для разных тенантов
YANDEX_LLM_MODEL_PREMIUM=yandexgpt
YANDEX_LLM_MODEL_STANDARD=yandexgpt-lite
YANDEX_EMBEDDING_MODEL=text-search-doc

# Лимиты по тенантам
YANDEX_MAX_TOKENS_PREMIUM=2000
YANDEX_MAX_TOKENS_STANDARD=1000
YANDEX_MAX_CONCURRENT_PREMIUM=20
YANDEX_MAX_CONCURRENT_STANDARD=5

# Кэширование по тенантам
YANDEX_CACHE_DIR_TEMPLATE=/app/files/cache/tenant_{tenant_id}
YANDEX_EMBEDDINGS_CACHE_DIR_TEMPLATE=/app/files/embeddings_cache/tenant_{tenant_id}
```

### High-Availability Configuration

```bash
# .env.ha
# Конфигурация для высокой доступности

# Yandex Cloud с резервированием
USE_YANDEX_CLOUD=true
YANDEX_API_KEY=AQVNha_primary_key
YANDEX_API_KEY_BACKUP=AQVNha_backup_key
YANDEX_FOLDER_ID=b1g2ha_primary_folder
YANDEX_FOLDER_ID_BACKUP=b1g2ha_backup_folder

# Агрессивные retry настройки
YANDEX_MAX_RETRIES=5
YANDEX_RETRY_DELAY=0.5
YANDEX_FALLBACK_TO_OLLAMA=true
YANDEX_FALLBACK_TIMEOUT=30

# Мониторинг и алерты
YANDEX_ENABLE_METRICS=true
YANDEX_ENABLE_PERFORMANCE_MONITORING=true
YANDEX_HEALTH_CHECK_INTERVAL=30
YANDEX_ALERT_ON_ERROR_RATE=0.05

# Кластерная база данных
DATABASE_URL=mysql+mysqlconnector://ha_user:secure_pass@ha-mysql-cluster:3306/rag_ha?charset=utf8mb4
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
```

### Edge/CDN Configuration

```bash
# .env.edge
# Конфигурация для edge развертывания

# Yandex Cloud с региональными настройками
USE_YANDEX_CLOUD=true
YANDEX_API_KEY=AQVNedge_api_key
YANDEX_FOLDER_ID=b1g2edge_folder
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net
YANDEX_REGION=ru-central1

# Оптимизация для edge
YANDEX_LLM_MODEL=yandexgpt-lite
YANDEX_MAX_TOKENS=500
YANDEX_TEMPERATURE=0.0
YANDEX_TIMEOUT=15

# Агрессивное кэширование
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_TTL_HOURS=72
YANDEX_CACHE_MAX_SIZE_MB=2000

# Минимальные ресурсы
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
YANDEX_MAX_CONCURRENT=3
```

## 🔧 Утилиты для управления конфигурацией

### config_manager.py

```python
#!/usr/bin/env python3
"""
Утилита для управления конфигурацией
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        
    def list_environments(self) -> list:
        """Список доступных сред"""
        env_files = list(self.config_dir.glob(".env.*"))
        return [f.stem.replace(".env.", "") for f in env_files if f.stem != ".env.example"]
    
    def validate_environment(self, env: str) -> Dict[str, Any]:
        """Валидация конфигурации среды"""
        env_file = self.config_dir / f".env.{env}"
        if not env_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {env_file}")
        
        # Загружаем переменные
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        # Валидация
        errors = []
        warnings = []
        
        # Проверяем обязательные переменные
        required_vars = ['YANDEX_API_KEY', 'YANDEX_FOLDER_ID', 'DATABASE_URL']
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                errors.append(f"Отсутствует обязательная переменная: {var}")
        
        # Проверяем формат API ключа
        if 'YANDEX_API_KEY' in env_vars:
            api_key = env_vars['YANDEX_API_KEY']
            if len(api_key) < 20:
                errors.append("YANDEX_API_KEY слишком короткий")
            if not api_key.replace('_', '').replace('-', '').isalnum():
                errors.append("YANDEX_API_KEY содержит недопустимые символы")
        
        # Проверяем числовые значения
        numeric_vars = {
            'YANDEX_TIMEOUT': (5, 300),
            'YANDEX_MAX_TOKENS': (1, 8000),
            'YANDEX_MAX_RETRIES': (0, 10),
            'DB_POOL_SIZE': (1, 100)
        }
        
        for var, (min_val, max_val) in numeric_vars.items():
            if var in env_vars:
                try:
                    value = int(env_vars[var])
                    if not (min_val <= value <= max_val):
                        warnings.append(f"{var}={value} вне рекомендуемого диапазона [{min_val}, {max_val}]")
                except ValueError:
                    errors.append(f"{var} должен быть числом")
        
        return {
            'environment': env,
            'variables_count': len(env_vars),
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
    
    def compare_environments(self, env1: str, env2: str) -> Dict[str, Any]:
        """Сравнение двух сред"""
        def load_env_vars(env):
            env_file = self.config_dir / f".env.{env}"
            vars_dict = {}
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        vars_dict[key] = value
            return vars_dict
        
        vars1 = load_env_vars(env1)
        vars2 = load_env_vars(env2)
        
        all_keys = set(vars1.keys()) | set(vars2.keys())
        differences = {}
        
        for key in all_keys:
            val1 = vars1.get(key, '<НЕ ЗАДАНО>')
            val2 = vars2.get(key, '<НЕ ЗАДАНО>')
            if val1 != val2:
                differences[key] = {'env1': val1, 'env2': val2}
        
        return {
            'env1': env1,
            'env2': env2,
            'differences': differences,
            'common_vars': len(set(vars1.keys()) & set(vars2.keys())),
            'total_differences': len(differences)
        }
    
    def generate_template(self, env: str, output_file: str = None):
        """Генерация шаблона конфигурации"""
        templates = {
            'development': {
                'USE_YANDEX_CLOUD': 'true',
                'YANDEX_API_KEY': 'your_development_api_key_here',
                'YANDEX_FOLDER_ID': 'your_development_folder_id_here',
                'YANDEX_LLM_MODEL': 'yandexgpt-lite',
                'YANDEX_FALLBACK_TO_OLLAMA': 'true',
                'DEBUG': 'true',
                'LOG_LEVEL': 'DEBUG',
                'DATABASE_URL': 'mysql+mysqlconnector://root:devpass@localhost:3306/rag_dev'
            },
            'production': {
                'USE_YANDEX_CLOUD': 'true',
                'YANDEX_API_KEY': 'your_production_api_key_here',
                'YANDEX_FOLDER_ID': 'your_production_folder_id_here',
                'YANDEX_LLM_MODEL': 'yandexgpt',
                'YANDEX_FALLBACK_TO_OLLAMA': 'false',
                'DEBUG': 'false',
                'LOG_LEVEL': 'WARNING',
                'DATABASE_URL': 'mysql+mysqlconnector://prod_user:secure_pass@prod-db:3306/rag_prod'
            }
        }
        
        template = templates.get(env, templates['development'])
        
        content = f"# Configuration for {env} environment\n"
        content += f"# Generated by ConfigManager\n\n"
        
        for key, value in template.items():
            content += f"{key}={value}\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"Шаблон сохранен: {output_file}")
        else:
            print(content)

def main():
    parser = argparse.ArgumentParser(description="Управление конфигурацией RAG системы")
    parser.add_argument('command', choices=['list', 'validate', 'compare', 'template'])
    parser.add_argument('--env', help="Среда для валидации")
    parser.add_argument('--env1', help="Первая среда для сравнения")
    parser.add_argument('--env2', help="Вторая среда для сравнения")
    parser.add_argument('--output', help="Выходной файл для шаблона")
    
    args = parser.parse_args()
    manager = ConfigManager()
    
    if args.command == 'list':
        envs = manager.list_environments()
        print("Доступные среды:")
        for env in envs:
            print(f"  - {env}")
    
    elif args.command == 'validate':
        if not args.env:
            print("Укажите среду через --env")
            return
        
        result = manager.validate_environment(args.env)
        print(f"Валидация среды: {result['environment']}")
        print(f"Переменных: {result['variables_count']}")
        
        if result['errors']:
            print("\n❌ Ошибки:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("\n⚠️ Предупреждения:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        if result['is_valid']:
            print("\n✅ Конфигурация валидна")
        else:
            print("\n❌ Конфигурация содержит ошибки")
    
    elif args.command == 'compare':
        if not args.env1 or not args.env2:
            print("Укажите обе среды через --env1 и --env2")
            return
        
        result = manager.compare_environments(args.env1, args.env2)
        print(f"Сравнение: {result['env1']} vs {result['env2']}")
        print(f"Общих переменных: {result['common_vars']}")
        print(f"Различий: {result['total_differences']}")
        
        if result['differences']:
            print("\nРазличия:")
            for key, values in result['differences'].items():
                print(f"  {key}:")
                print(f"    {result['env1']}: {values['env1']}")
                print(f"    {result['env2']}: {values['env2']}")
    
    elif args.command == 'template':
        if not args.env:
            print("Укажите среду через --env")
            return
        
        manager.generate_template(args.env, args.output)

if __name__ == "__main__":
    main()
```

### Makefile для управления конфигурацией

```makefile
# Makefile для управления конфигурацией RAG системы

.PHONY: help config-list config-validate config-compare config-template config-deploy

help:
	@echo "Доступные команды:"
	@echo "  config-list      - Список доступных сред"
	@echo "  config-validate  - Валидация конфигурации (ENV=development)"
	@echo "  config-compare   - Сравнение сред (ENV1=dev ENV2=prod)"
	@echo "  config-template  - Генерация шаблона (ENV=development)"
	@echo "  config-deploy    - Развертывание конфигурации (ENV=production)"

config-list:
	@python config_manager.py list

config-validate:
	@python config_manager.py validate --env $(or $(ENV),development)

config-compare:
	@python config_manager.py compare --env1 $(or $(ENV1),development) --env2 $(or $(ENV2),production)

config-template:
	@python config_manager.py template --env $(or $(ENV),development) --output .env.$(or $(ENV),development).template

config-deploy:
	@echo "Развертывание конфигурации для среды: $(or $(ENV),production)"
	@python config_manager.py validate --env $(or $(ENV),production)
	@cp .env.$(or $(ENV),production) .env
	@echo "Конфигурация развернута. Перезапустите приложение."

# Быстрые команды для разных сред
dev-config:
	@make config-deploy ENV=development

staging-config:
	@make config-deploy ENV=staging

prod-config:
	@make config-deploy ENV=production

# Проверка всех сред
validate-all:
	@for env in development testing staging production; do \
		echo "Проверка $$env..."; \
		python config_manager.py validate --env $$env || true; \
		echo ""; \
	done
```

Эти примеры конфигурации и утилиты покрывают все основные сценарии развертывания и обеспечивают гибкость настройки системы для различных сред, включая мультитенантность, высокую доступность и edge развертывание.