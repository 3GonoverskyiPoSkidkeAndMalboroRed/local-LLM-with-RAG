# Troubleshooting Guide

Руководство по диагностике и решению проблем в системе RAG с интеграцией Yandex Cloud.

## 📋 Содержание

- [Быстрая диагностика](#-быстрая-диагностика)
- [Проблемы конфигурации](#-проблемы-конфигурации)
- [Ошибки Yandex Cloud API](#-ошибки-yandex-cloud-api)
- [Проблемы с базой данных](#-проблемы-с-базой-данных)
- [Проблемы производительности](#-проблемы-производительности)
- [Проблемы с эмбеддингами](#-проблемы-с-эмбеддингами)
- [Проблемы с fallback](#-проблемы-с-fallback)
- [Диагностические команды](#-диагностические-команды)
- [Логирование и мониторинг](#-логирование-и-мониторинг)

## 🚀 Быстрая диагностика

### Проверка общего состояния системы

```bash
# 1. Проверка конфигурации
python test_config.py

# 2. Проверка подключения к API
python -c "
from yandex_cloud_adapter import YandexCloudAdapter
from config_utils import YandexCloudConfig
try:
    config = YandexCloudConfig.from_env()
    adapter = YandexCloudAdapter(config)
    print('✅ Yandex Cloud API доступен')
except Exception as e:
    print(f'❌ Ошибка Yandex Cloud API: {e}')
"

# 3. Проверка базы данных
python -c "
from database import get_database_connection
try:
    conn = get_database_connection()
    print('✅ База данных доступна')
except Exception as e:
    print(f'❌ Ошибка БД: {e}')
"

# 4. Проверка эндпоинтов
curl -f http://localhost:8000/health || echo "❌ Сервер недоступен"
```

### Быстрые исправления

```bash
# Перезапуск с чистой конфигурацией
export USE_YANDEX_CLOUD=false
python app.py --web --port 8000

# Очистка кэша
rm -rf /app/files/cache/*
rm -rf /app/files/embeddings_cache/*

# Переинициализация отдела
curl -X POST "http://localhost:8000/llm/debug/reinitialize/1"
```

## ⚙️ Проблемы конфигурации

### Ошибка: "YANDEX_API_KEY environment variable is required"

**Причина:** Отсутствует или пустая переменная окружения YANDEX_API_KEY.

**Решение:**
```bash
# Проверьте наличие переменной
echo $YANDEX_API_KEY

# Проверьте .env файл
grep YANDEX_API_KEY .env

# Убедитесь что .env файл загружается
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('YANDEX_API_KEY:', os.getenv('YANDEX_API_KEY', 'НЕ НАЙДЕН'))
"

# Установите переменную
export YANDEX_API_KEY=your_api_key_here
# Или добавьте в .env файл
echo "YANDEX_API_KEY=your_api_key_here" >> .env
```

### Ошибка: "Invalid API key format"

**Причина:** API ключ имеет неверный формат или слишком короткий.

**Решение:**
```bash
# Проверьте длину ключа (должен быть > 20 символов)
echo ${#YANDEX_API_KEY}

# Проверьте формат (только буквы, цифры, _, -)
echo $YANDEX_API_KEY | grep -E '^[A-Za-z0-9_-]+$' || echo "Неверный формат"

# Получите новый ключ в консоли Yandex Cloud
# https://console.cloud.yandex.ru/
```

### Ошибка: "Configuration validation failed"

**Причина:** Одна или несколько переменных конфигурации имеют неверные значения.

**Решение:**
```bash
# Запустите полную валидацию
python -c "
from config_utils import validate_all_config_new
try:
    config = validate_all_config_new()
    print('✅ Конфигурация валидна')
    print('Yandex Cloud включен:', config.yandex_cloud.api_key[:8] + '***')
    print('Модель LLM:', config.yandex_cloud.default_llm_model)
    print('Модель эмбеддингов:', config.yandex_cloud.default_embedding_model)
except Exception as e:
    print(f'❌ Ошибка валидации: {e}')
    import traceback
    traceback.print_exc()
"

# Проверьте конкретные параметры
python -c "
from config_utils import get_env_int, get_env_float
try:
    timeout = get_env_int('YANDEX_TIMEOUT', 30, min_value=5, max_value=300)
    temp = get_env_float('YANDEX_TEMPERATURE', 0.1, min_value=0.0, max_value=1.0)
    print(f'✅ Timeout: {timeout}, Temperature: {temp}')
except Exception as e:
    print(f'❌ Ошибка параметров: {e}')
"
```

## 🌐 Ошибки Yandex Cloud API

### Ошибка 401: "Unauthorized"

**Причина:** Неверный API ключ или отсутствуют права доступа.

**Решение:**
```bash
# 1. Проверьте API ключ
curl -H "Authorization: Api-Key $YANDEX_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"modelUri": "gpt://'$YANDEX_FOLDER_ID'/yandexgpt/latest", "completionOptions": {"stream": false, "temperature": 0.1, "maxTokens": 100}, "messages": [{"role": "user", "text": "test"}]}' \
     https://llm.api.cloud.yandex.net/foundationModels/v1/completion

# 2. Проверьте права сервисного аккаунта
# В консоли Yandex Cloud убедитесь что у сервисного аккаунта есть роль:
# - ai.languageModels.user

# 3. Проверьте folder_id
echo "Folder ID: $YANDEX_FOLDER_ID"
```

### Ошибка 429: "Rate limit exceeded"

**Причина:** Превышен лимит запросов к API.

**Решение:**
```bash
# 1. Уменьшите частоту запросов
export YANDEX_MAX_REQUESTS_PER_MINUTE=30
export YANDEX_MAX_CONCURRENT=5

# 2. Увеличьте задержку между retry
export YANDEX_RETRY_DELAY=2.0

# 3. Проверьте текущие лимиты
python -c "
from yandex_metrics import YandexCloudMetrics
metrics = YandexCloudMetrics()
stats = metrics.get_current_stats()
print('Запросов в минуту:', stats.get('requests_per_minute', 0))
print('Активных соединений:', stats.get('active_connections', 0))
"

# 4. Включите кэширование для уменьшения запросов
export YANDEX_ENABLE_CACHING=true
```

### Ошибка 500/502/503: "Server Error"

**Причина:** Временные проблемы на стороне Yandex Cloud.

**Решение:**
```bash
# 1. Включите fallback на Ollama
export YANDEX_FALLBACK_TO_OLLAMA=true

# 2. Увеличьте количество retry
export YANDEX_MAX_RETRIES=5
export YANDEX_RETRY_DELAY=3.0

# 3. Проверьте статус сервисов Yandex Cloud
# https://status.cloud.yandex.ru/

# 4. Мониторьте ошибки
python -c "
from yandex_error_handler import YandexCloudErrorHandler
handler = YandexCloudErrorHandler()
print('Последние ошибки:', handler.get_recent_errors())
"
```

### Ошибка: "Timeout"

**Причина:** Запрос к API превысил установленный таймаут.

**Решение:**
```bash
# 1. Увеличьте таймаут
export YANDEX_TIMEOUT=60

# 2. Уменьшите размер запроса
export YANDEX_MAX_TOKENS=1000

# 3. Проверьте сетевое соединение
ping llm.api.cloud.yandex.net

# 4. Проверьте время ответа
time curl -H "Authorization: Api-Key $YANDEX_API_KEY" \
          https://llm.api.cloud.yandex.net/foundationModels/v1/completion \
          -d '{"modelUri": "gpt://'$YANDEX_FOLDER_ID'/yandexgpt/latest", "completionOptions": {"stream": false, "temperature": 0.1, "maxTokens": 10}, "messages": [{"role": "user", "text": "hi"}]}'
```

### Ошибка 400: "Invalid request format"

**Причина:** Неверный формат запроса к API.

**Решение:**
```bash
# 1. Проверьте формат modelUri
# Правильный формат: gpt://FOLDER_ID/MODEL_NAME/latest
echo "Проверьте modelUri: gpt://$YANDEX_FOLDER_ID/yandexgpt/latest"

# 2. Проверьте структуру сообщений
python -c "
import json
messages = [{'role': 'user', 'text': 'Привет'}]
request_data = {
    'modelUri': f'gpt://$YANDEX_FOLDER_ID/yandexgpt/latest',
    'completionOptions': {
        'stream': False,
        'temperature': 0.1,
        'maxTokens': 100
    },
    'messages': messages
}
print('Корректный формат запроса:')
print(json.dumps(request_data, indent=2, ensure_ascii=False))
"

# 3. Валидация JSON
echo '{"test": "json"}' | python -m json.tool
```

### Ошибка: "Model not found"

**Причина:** Указанная модель недоступна или неверно указана.

**Решение:**
```bash
# 1. Проверьте доступные модели
python -c "
from config_utils import YandexCloudConfig
config = YandexCloudConfig.from_env()
print('Доступные LLM модели:')
for model in ['yandexgpt', 'yandexgpt-lite']:
    print(f'  - {model}')
print('Доступные Embedding модели:')
for model in ['text-search-doc', 'text-search-query']:
    print(f'  - {model}')
"

# 2. Проверьте права доступа к моделям
# В консоли Yandex Cloud убедитесь что у сервисного аккаунта есть доступ к Foundation Models

# 3. Используйте стандартные модели
export YANDEX_LLM_MODEL=yandexgpt
export YANDEX_EMBEDDING_MODEL=text-search-doc
```

### Ошибка: "Quota exceeded"

**Причина:** Превышена квота на использование API.

**Решение:**
```bash
# 1. Проверьте текущие квоты в консоли Yandex Cloud
# Перейдите в раздел "Квоты" вашего каталога

# 2. Запросите увеличение квот через техподдержку
# https://cloud.yandex.ru/support

# 3. Оптимизируйте использование API
export YANDEX_MAX_TOKENS=1000  # Уменьшите количество токенов
export YANDEX_MAX_CONCURRENT=5  # Уменьшите параллельные запросы
export YANDEX_ENABLE_CACHING=true  # Включите кэширование

# 4. Мониторьте использование
python -c "
from yandex_metrics import YandexCloudMetrics
metrics = YandexCloudMetrics()
stats = metrics.get_current_stats()
print(f'Использовано токенов сегодня: {stats.get(\"tokens_used_today\", 0)}')
print(f'Запросов в час: {stats.get(\"requests_per_hour\", 0)}')
"
```

## 🗄️ Проблемы с базой данных

### Ошибка: "Can't connect to MySQL server"

**Причина:** База данных недоступна или неверные параметры подключения.

**Решение:**
```bash
# 1. Проверьте подключение
mysql -h localhost -u root -p -e "SELECT 1;"

# 2. Проверьте DATABASE_URL
echo $DATABASE_URL

# 3. Проверьте статус MySQL
systemctl status mysql
# или
docker ps | grep mysql

# 4. Проверьте сетевое соединение
telnet localhost 3306

# 5. Проверьте логи MySQL
tail -f /var/log/mysql/error.log
```

### Ошибка: "Access denied for user"

**Причина:** Неверные учетные данные или отсутствуют права доступа.

**Решение:**
```bash
# 1. Проверьте учетные данные
mysql -u your_user -p your_database -e "SELECT USER();"

# 2. Создайте пользователя и дайте права
mysql -u root -p -e "
CREATE USER IF NOT EXISTS 'rag_user'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON rag_database.* TO 'rag_user'@'%';
FLUSH PRIVILEGES;
"

# 3. Обновите DATABASE_URL
export DATABASE_URL="mysql+mysqlconnector://rag_user:secure_password@localhost:3306/rag_database"
```

### Ошибка: "Table doesn't exist"

**Причина:** Не выполнена инициализация базы данных.

**Решение:**
```bash
# 1. Запустите инициализацию БД
python init_db.py

# 2. Проверьте существующие таблицы
mysql -u root -p your_database -e "SHOW TABLES;"

# 3. Проверьте структуру таблиц
python -c "
from models_db import Base, engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Таблицы в БД:', tables)
"
```

## ⚡ Проблемы производительности

### Медленные ответы от API

**Диагностика:**
```bash
# 1. Проверьте время ответа API
python -c "
import time
from yandex_cloud_adapter import YandexCloudAdapter
from config_utils import YandexCloudConfig

config = YandexCloudConfig.from_env()
adapter = YandexCloudAdapter(config)

start = time.time()
try:
    response = adapter.generate_text('Привет', model='yandexgpt')
    duration = time.time() - start
    print(f'Время ответа: {duration:.2f} сек')
    print(f'Длина ответа: {len(response)} символов')
except Exception as e:
    print(f'Ошибка: {e}')
"

# 2. Проверьте метрики производительности
python -c "
from performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
stats = monitor.get_performance_stats()
print('Среднее время ответа:', stats.get('avg_response_time', 'N/A'))
print('Успешных запросов:', stats.get('success_rate', 'N/A'))
"
```

**Решения:**
```bash
# 1. Оптимизируйте параметры запросов
export YANDEX_MAX_TOKENS=1000  # Уменьшите количество токенов
export YANDEX_TEMPERATURE=0.0  # Уменьшите температуру для быстрых ответов

# 2. Включите кэширование
export YANDEX_ENABLE_CACHING=true
export YANDEX_CACHE_TTL_HOURS=24

# 3. Оптимизируйте пул соединений
export YANDEX_MAX_CONCURRENT=10
export DB_POOL_SIZE=20

# 4. Используйте более быструю модель
export YANDEX_LLM_MODEL=yandexgpt-lite
```

### Высокое потребление памяти

**Диагностика:**
```bash
# 1. Проверьте использование памяти
ps aux | grep python
free -h

# 2. Проверьте размер кэша
du -sh /app/files/cache/
du -sh /app/files/embeddings_cache/

# 3. Проверьте количество активных соединений
python -c "
from llm_state_manager import LLMStateManager
manager = LLMStateManager()
print('Активных отделов:', len(manager.departments))
for dept_id, dept in manager.departments.items():
    print(f'Отдел {dept_id}: {len(dept.get('documents', []))} документов')
"
```

**Решения:**
```bash
# 1. Очистите кэш
python -c "
from yandex_cache import YandexCache
cache = YandexCache()
deleted = cache.clear_expired_cache()
print(f'Удалено файлов кэша: {deleted}')
"

# 2. Ограничьте размер кэша
export YANDEX_CACHE_TTL_HOURS=6
export YANDEX_MAX_CACHE_SIZE_MB=1000

# 3. Оптимизируйте пул соединений БД
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=15
export DB_POOL_RECYCLE=1800
```

## 🔍 Проблемы с эмбеддингами

### Ошибка: "Failed to create embeddings"

**Причина:** Проблемы с API эмбеддингов или слишком большой текст.

**Решение:**
```bash
# 1. Проверьте API эмбеддингов
python -c "
from yandex_embeddings import create_yandex_embeddings
embeddings = create_yandex_embeddings()
try:
    result = embeddings.embed_query('тест')
    print(f'✅ Эмбеддинг создан, размерность: {len(result)}')
except Exception as e:
    print(f'❌ Ошибка создания эмбеддинга: {e}')
"

# 2. Проверьте размер текста
python -c "
text = 'ваш текст здесь'
print(f'Длина текста: {len(text)} символов')
if len(text) > 8000:
    print('⚠️ Текст слишком длинный, разбейте на части')
"

# 3. Проверьте кэш эмбеддингов
ls -la /app/files/embeddings_cache/
```

### Медленное создание эмбеддингов

**Решение:**
```bash
# 1. Включите кэширование эмбеддингов
export YANDEX_ENABLE_CACHING=true

# 2. Проверьте статистику кэша
python -c "
from yandex_embeddings import create_yandex_embeddings
embeddings = create_yandex_embeddings()
stats = embeddings.get_cache_stats()
print('Файлов в кэше:', stats['files_count'])
print('Размер кэша:', stats['total_size_mb'], 'МБ')
print('Попаданий в кэш:', stats.get('cache_hits', 0))
print('Промахов кэша:', stats.get('cache_misses', 0))
"

# 3. Оптимизируйте batch размер
python -c "
from yandex_embeddings import YandexEmbeddings
# Уменьшите batch_size если есть проблемы с памятью
embeddings = YandexEmbeddings(batch_size=50)
"
```

### Ошибка: "Vector dimension mismatch"

**Причина:** Несоответствие размерности векторов в базе данных.

**Решение:**
```bash
# 1. Проверьте размерность эмбеддингов
python -c "
from yandex_embeddings import create_yandex_embeddings
embeddings = create_yandex_embeddings()
test_embedding = embeddings.embed_query('тест')
print(f'Размерность эмбеддинга: {len(test_embedding)}')
"

# 2. Пересоздайте векторную базу данных
python -c "
from document_loader import DocumentLoader
loader = DocumentLoader()
loader.recreate_vector_database()
print('Векторная БД пересоздана')
"

# 3. Мигрируйте существующие эмбеддинги
python migrate_to_yandex_cloud.py --recreate-embeddings
```

## 🔄 Проблемы с fallback

### Fallback не работает

**Диагностика:**
```bash
# 1. Проверьте настройки fallback
echo "YANDEX_FALLBACK_TO_OLLAMA: $YANDEX_FALLBACK_TO_OLLAMA"
echo "OLLAMA_HOST: $OLLAMA_HOST"

# 2. Проверьте доступность Ollama
curl -f $OLLAMA_HOST/api/tags || echo "❌ Ollama недоступен"

# 3. Проверьте логи fallback
python -c "
from yandex_error_handler import YandexCloudErrorHandler
handler = YandexCloudErrorHandler()
print('Fallback события:', handler.get_fallback_events())
"
```

**Решение:**
```bash
# 1. Включите fallback
export YANDEX_FALLBACK_TO_OLLAMA=true

# 2. Запустите Ollama
docker run -d -p 11434:11434 ollama/ollama
# Или
systemctl start ollama

# 3. Установите модели Ollama
ollama pull gemma3
ollama pull nomic-embed-text

# 4. Проверьте fallback
python -c "
from llm_state_manager import LLMStateManager
manager = LLMStateManager()
# Принудительно вызовите ошибку Yandex Cloud для тестирования fallback
"
```

## 🔧 Диагностические команды

### Полная диагностика системы

```bash
#!/bin/bash
# diagnostic.sh - Полная диагностика системы

echo "🔍 ДИАГНОСТИКА СИСТЕМЫ RAG"
echo "=========================="

# 1. Проверка конфигурации
echo "📋 Конфигурация:"
python -c "
from config_utils import get_runtime_config
import json
config = get_runtime_config()
print(json.dumps(config, indent=2, ensure_ascii=False))
" 2>/dev/null || echo "❌ Ошибка загрузки конфигурации"

# 2. Проверка Yandex Cloud API
echo -e "\n🌐 Yandex Cloud API:"
python -c "
from yandex_cloud_adapter import YandexCloudAdapter
from config_utils import YandexCloudConfig
try:
    config = YandexCloudConfig.from_env()
    adapter = YandexCloudAdapter(config)
    response = adapter.generate_text('test', max_tokens=10)
    print('✅ API работает')
except Exception as e:
    print(f'❌ Ошибка API: {e}')
"

# 3. Проверка базы данных
echo -e "\n🗄️ База данных:"
python -c "
from database import get_database_connection
try:
    conn = get_database_connection()
    result = conn.execute('SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = DATABASE()').fetchone()
    print(f'✅ БД доступна, таблиц: {result[0]}')
except Exception as e:
    print(f'❌ Ошибка БД: {e}')
"

# 4. Проверка эмбеддингов
echo -e "\n🔍 Эмбеддинги:"
python -c "
from yandex_embeddings import create_yandex_embeddings
try:
    embeddings = create_yandex_embeddings()
    test_emb = embeddings.embed_query('test')
    print(f'✅ Эмбеддинги работают, размерность: {len(test_emb)}')
    
    stats = embeddings.get_cache_stats()
    print(f'📊 Кэш: {stats[\"files_count\"]} файлов, {stats[\"total_size_mb\"]} МБ')
except Exception as e:
    print(f'❌ Ошибка эмбеддингов: {e}')
"

# 5. Проверка метрик
echo -e "\n📊 Метрики:"
python -c "
from yandex_metrics import YandexCloudMetrics
try:
    metrics = YandexCloudMetrics()
    stats = metrics.get_current_stats()
    print(f'📈 Всего запросов: {stats.get(\"total_requests\", 0)}')
    print(f'✅ Успешных: {stats.get(\"successful_requests\", 0)}')
    print(f'❌ Ошибок: {stats.get(\"failed_requests\", 0)}')
    print(f'⏱️ Среднее время: {stats.get(\"avg_response_time\", 0):.2f}с')
except Exception as e:
    print(f'❌ Ошибка метрик: {e}')
"

# 6. Проверка дискового пространства
echo -e "\n💾 Дисковое пространство:"
df -h /app/files/ 2>/dev/null || df -h .
du -sh /app/files/cache/ 2>/dev/null || echo "Кэш не найден"
du -sh /app/files/embeddings_cache/ 2>/dev/null || echo "Кэш эмбеддингов не найден"

# 7. Проверка процессов
echo -e "\n🔄 Процессы:"
ps aux | grep -E "(python|mysql|ollama)" | grep -v grep

echo -e "\n✅ Диагностика завершена"
```

### Мониторинг в реальном времени

```bash
# Мониторинг логов
tail -f /var/log/rag-app.log | grep -E "(ERROR|WARNING|Yandex)"

# Мониторинг метрик
watch -n 5 'python -c "
from yandex_metrics import YandexCloudMetrics
metrics = YandexCloudMetrics()
stats = metrics.get_current_stats()
print(f\"Запросов: {stats.get(\"total_requests\", 0)}\")
print(f\"Ошибок: {stats.get(\"failed_requests\", 0)}\")
print(f\"Время ответа: {stats.get(\"avg_response_time\", 0):.2f}с\")
"'

# Мониторинг системных ресурсов
htop
# или
top -p $(pgrep -f "python.*app.py")
```

## 📊 Логирование и мониторинг

### Настройка логирования

```python
# logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level=logging.INFO, log_file=None):
    """Настройка логирования для диагностики"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый хендлер
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Специальные логгеры для компонентов
    yandex_logger = logging.getLogger('yandex_cloud')
    yandex_logger.setLevel(logging.DEBUG)
    
    db_logger = logging.getLogger('database')
    db_logger.setLevel(logging.INFO)
    
    return root_logger

# Использование
if __name__ == "__main__":
    logger = setup_logging(
        level=logging.DEBUG,
        log_file="/app/logs/diagnostic.log"
    )
    logger.info("Логирование настроено")
```

### Алерты и уведомления

```python
# alerts.py
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self, smtp_host, smtp_port, username, password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_alert(self, subject, message, recipients):
        """Отправка алерта по email"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"[RAG System Alert] {subject}"
            msg['From'] = self.username
            msg['To'] = ', '.join(recipients)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Алерт отправлен: {subject}")
        except Exception as e:
            logger.error(f"Ошибка отправки алерта: {e}")
    
    def check_yandex_api_health(self):
        """Проверка здоровья Yandex Cloud API"""
        from yandex_cloud_adapter import YandexCloudAdapter
        from config_utils import YandexCloudConfig
        
        try:
            config = YandexCloudConfig.from_env()
            adapter = YandexCloudAdapter(config)
            adapter.generate_text("test", max_tokens=1)
            return True
        except Exception as e:
            self.send_alert(
                "Yandex Cloud API недоступен",
                f"Ошибка подключения к Yandex Cloud API: {e}\nВремя: {datetime.now()}",
                ["admin@yourdomain.com"]
            )
            return False

# Использование в cron job
# */5 * * * * python -c "from alerts import AlertManager; AlertManager().check_yandex_api_health()"
```

### Метрики для Prometheus

```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Метрики Yandex Cloud API
yandex_requests_total = Counter(
    'yandex_api_requests_total',
    'Total Yandex Cloud API requests',
    ['method', 'status']
)

yandex_request_duration = Histogram(
    'yandex_api_request_duration_seconds',
    'Yandex Cloud API request duration'
)

yandex_active_connections = Gauge(
    'yandex_api_active_connections',
    'Active connections to Yandex Cloud API'
)

# Метрики приложения
app_errors_total = Counter(
    'app_errors_total',
    'Total application errors',
    ['component', 'error_type']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

def track_yandex_request(method, status, duration):
    """Отслеживание запроса к Yandex Cloud API"""
    yandex_requests_total.labels(method=method, status=status).inc()
    yandex_request_duration.observe(duration)

def start_metrics_server(port=8001):
    """Запуск сервера метрик"""
    start_http_server(port)
    print(f"Metrics server started on port {port}")

if __name__ == "__main__":
    start_metrics_server()
```

## 🔧 Специфичные проблемы интеграции

### Проблема: Медленная инициализация отделов

**Симптомы:** Долгая загрузка при первом запросе к отделу.

**Диагностика:**
```bash
# Проверьте время инициализации
python -c "
import time
from llm_state_manager import LLMStateManager

start = time.time()
manager = LLMStateManager()
manager.initialize_department('test_dept', 'yandexgpt', 'text-search-doc', '/path/to/docs')
duration = time.time() - start
print(f'Время инициализации: {duration:.2f} сек')
"
```

**Решение:**
```bash
# 1. Предварительная инициализация отделов
python -c "
from llm_state_manager import LLMStateManager
manager = LLMStateManager()
# Инициализируйте все отделы при старте приложения
for dept_id in ['1', '2', '3']:
    manager.initialize_department(dept_id, 'yandexgpt', 'text-search-doc', f'/app/files/dept_{dept_id}')
"

# 2. Асинхронная инициализация
export ASYNC_DEPARTMENT_INIT=true

# 3. Кэширование состояния отделов
export CACHE_DEPARTMENT_STATE=true
```

### Проблема: Несоответствие эмбеддингов после миграции

**Симптомы:** Поиск возвращает нерелевантные результаты после переключения на Yandex Cloud.

**Диагностика:**
```bash
# Сравните размерности эмбеддингов
python -c "
from yandex_embeddings import create_yandex_embeddings
from langchain.embeddings import OllamaEmbeddings

yandex_emb = create_yandex_embeddings()
ollama_emb = OllamaEmbeddings(model='nomic-embed-text')

test_text = 'Тестовый текст для сравнения'
yandex_vec = yandex_emb.embed_query(test_text)
ollama_vec = ollama_emb.embed_query(test_text)

print(f'Yandex размерность: {len(yandex_vec)}')
print(f'Ollama размерность: {len(ollama_vec)}')
print(f'Совместимы: {len(yandex_vec) == len(ollama_vec)}')
"
```

**Решение:**
```bash
# 1. Полная миграция эмбеддингов
python migrate_to_yandex_cloud.py --recreate-embeddings --department-id all

# 2. Пересоздание векторной базы данных
python -c "
from document_loader import DocumentLoader
loader = DocumentLoader()
loader.recreate_vector_database()
print('Векторная БД пересоздана')
"

# 3. Валидация миграции
python migration_validator.py --validate-embeddings
```

### Проблема: Конфликт версий моделей

**Симптомы:** Ошибки при использовании разных версий моделей в разных отделах.

**Решение:**
```bash
# 1. Стандартизируйте модели для всех отделов
export YANDEX_LLM_MODEL=yandexgpt
export YANDEX_EMBEDDING_MODEL=text-search-doc

# 2. Проверьте совместимость моделей
python -c "
from config_utils import YandexCloudConfig
config = YandexCloudConfig.from_env()
print('Текущие модели:')
print(f'LLM: {config.default_llm_model}')
print(f'Embeddings: {config.default_embedding_model}')
"

# 3. Обновите все отделы
curl -X POST 'http://localhost:8000/llm/debug/update-all-departments' \
     -H 'Content-Type: application/json' \
     -d '{
       "llm_model": "yandexgpt",
       "embedding_model": "text-search-doc"
     }'
```

## 🆘 Получение помощи

### Сбор информации для поддержки

```bash
#!/bin/bash
# collect_support_info.sh

SUPPORT_DIR="/tmp/rag_support_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SUPPORT_DIR"

echo "📦 Сбор информации для поддержки..."

# 1. Системная информация
uname -a > "$SUPPORT_DIR/system_info.txt"
python --version >> "$SUPPORT_DIR/system_info.txt"
pip list > "$SUPPORT_DIR/pip_packages.txt"

# 2. Конфигурация (без секретов)
python -c "
from config_utils import get_runtime_config
import json
config = get_runtime_config()
# Удаляем чувствительные данные
if 'yandex_cloud' in config:
    config['yandex_cloud'].pop('api_key', None)
with open('$SUPPORT_DIR/config.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"

# 3. Логи (последние 1000 строк)
tail -n 1000 /var/log/rag-app.log > "$SUPPORT_DIR/app.log" 2>/dev/null || echo "Логи не найдены"

# 4. Диагностика
bash diagnostic.sh > "$SUPPORT_DIR/diagnostic.txt" 2>&1

# 5. Метрики
python -c "
from yandex_metrics import YandexCloudMetrics
import json
try:
    metrics = YandexCloudMetrics()
    stats = metrics.get_current_stats()
    with open('$SUPPORT_DIR/metrics.json', 'w') as f:
        json.dump(stats, f, indent=2)
except Exception as e:
    with open('$SUPPORT_DIR/metrics_error.txt', 'w') as f:
        f.write(str(e))
"

# 6. Создаем архив
tar -czf "${SUPPORT_DIR}.tar.gz" -C "/tmp" "$(basename $SUPPORT_DIR)"

echo "✅ Информация собрана: ${SUPPORT_DIR}.tar.gz"
echo "📧 Отправьте этот файл в службу поддержки"
```

### Контакты поддержки

- **GitHub Issues**: [Создать issue](https://github.com/your-repo/issues)
- **Email**: support@yourdomain.com
- **Документация**: [README.md](../README.md)
- **Yandex Cloud Support**: [Техническая поддержка](https://cloud.yandex.ru/support)

### Полезные ссылки

- [Документация Yandex Cloud Foundation Models](https://cloud.yandex.ru/docs/foundation-models/)
- [API Reference](https://cloud.yandex.ru/docs/foundation-models/api-ref/)
- [Статус сервисов Yandex Cloud](https://status.cloud.yandex.ru/)
- [Тарифы и лимиты](https://cloud.yandex.ru/docs/foundation-models/pricing)
- [Примеры использования](https://github.com/yandex-cloud/examples)

---

**💡 Совет**: Всегда начинайте диагностику с запуска `python test_config.py` и проверки логов. Большинство проблем связано с конфигурацией или сетевыми проблемами.