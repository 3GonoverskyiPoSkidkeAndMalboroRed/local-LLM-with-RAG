# Переменные окружения

Данный документ содержит полное описание всех переменных окружения, используемых в системе RAG с интеграцией Yandex Cloud.

## 📋 Обзор

Система поддерживает конфигурацию через переменные окружения для максимальной гибкости развертывания. Все переменные можно задать в файле `.env` или через системные переменные окружения.

**🔄 Приоритет загрузки конфигурации:**
1. Системные переменные окружения (высший приоритет)
2. Файл `.env` в корне проекта
3. Файл `.env.local` (игнорируется git)
4. Значения по умолчанию в коде

**📁 Файлы конфигурации:**
- `.env.example` - шаблон конфигурации
- `.env.development` - настройки для разработки
- `.env.testing` - настройки для тестирования
- `.env.staging` - настройки для staging среды
- `.env.production` - настройки для production

## 🔑 Yandex Cloud Configuration

### Обязательные переменные

| Переменная | Тип | Описание | Пример | Валидация |
|------------|-----|----------|--------|-----------|
| `YANDEX_API_KEY` | string | API ключ сервисного аккаунта Yandex Cloud | `AQVNxxxxxxxxxxxxxxxxx` | Длина > 20, только [A-Za-z0-9_-] |
| `YANDEX_FOLDER_ID` | string | ID каталога в Yandex Cloud | `b1g2xxxxxxxxxxxxxxxxx` | Формат: b1g[0-9a-z]{20} |

**🔍 Как получить эти значения:**

1. **YANDEX_API_KEY**:
   ```bash
   # В консоли Yandex Cloud:
   # 1. IAM → Сервисные аккаунты → Создать
   # 2. Назначить роль: ai.languageModels.user
   # 3. API-ключи → Создать API-ключ
   # 4. Скопировать ключ (показывается только один раз!)
   ```

2. **YANDEX_FOLDER_ID**:
   ```bash
   # В консоли Yandex Cloud:
   # 1. Выберите каталог в верхней части страницы
   # 2. ID каталога отображается в URL или в настройках каталога
   # Или через CLI:
   yc config list
   ```

### Основные настройки

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `USE_YANDEX_CLOUD` | boolean | `false` | Включение интеграции с Yandex Cloud |
| `YANDEX_LLM_MODEL` | string | `yandexgpt` | Модель для генерации текста |
| `YANDEX_EMBEDDING_MODEL` | string | `text-search-doc` | Модель для создания эмбеддингов |

### API настройки

| Переменная | Тип | По умолчанию | Диапазон | Описание |
|------------|-----|--------------|----------|----------|
| `YANDEX_BASE_URL` | string | `https://llm.api.cloud.yandex.net` | - | Базовый URL API Yandex Cloud |
| `YANDEX_TIMEOUT` | integer | `30` | 5-300 | Таймаут запросов в секундах |
| `YANDEX_MAX_TOKENS` | integer | `2000` | 1-8000 | Максимальное количество токенов |
| `YANDEX_TEMPERATURE` | float | `0.1` | 0.0-1.0 | Температура генерации |

### Retry и обработка ошибок

| Переменная | Тип | По умолчанию | Диапазон | Описание |
|------------|-----|--------------|----------|----------|
| `YANDEX_MAX_RETRIES` | integer | `3` | 0-10 | Максимальное количество повторных попыток |
| `YANDEX_RETRY_DELAY` | float | `1.0` | 0.1-10.0 | Базовая задержка между попытками (сек) |
| `YANDEX_FALLBACK_TO_OLLAMA` | boolean | `true` | - | Fallback на Ollama при ошибках |

### Лимиты и производительность

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `YANDEX_MAX_REQUESTS_PER_MINUTE` | integer | `60` | Лимит запросов в минуту |
| `YANDEX_MAX_CONCURRENT` | integer | `10` | Максимальное количество одновременных запросов |
| `YANDEX_FALLBACK_TIMEOUT` | integer | `60` | Таймаут для fallback провайдера |

### Кэширование

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `YANDEX_ENABLE_CACHING` | boolean | `true` | Включение кэширования эмбеддингов |
| `YANDEX_CACHE_DIR` | string | `/app/files/cache` | Директория для кэша |
| `YANDEX_CACHE_TTL_HOURS` | integer | `24` | Время жизни кэша в часах |
| `YANDEX_EMBEDDINGS_CACHE_DIR` | string | `/app/files/embeddings_cache` | Директория кэша эмбеддингов |

### Мониторинг и метрики

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `YANDEX_ENABLE_METRICS` | boolean | `true` | Включение сбора метрик |
| `YANDEX_METRICS_FILE` | string | `/app/files/yandex_metrics.json` | Файл для сохранения метрик |
| `YANDEX_ENABLE_PERFORMANCE_MONITORING` | boolean | `true` | Мониторинг производительности |

## 🤖 Ollama Configuration (Fallback)

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `OLLAMA_HOST` | string | `http://localhost:11434` | URL сервера Ollama |
| `OLLAMA_TIMEOUT` | integer | `60` | Таймаут запросов к Ollama |
| `OLLAMA_MAX_RETRIES` | integer | `3` | Максимальное количество повторных попыток |
| `OLLAMA_LLM_MODEL` | string | `gemma3` | Модель LLM по умолчанию для Ollama |
| `OLLAMA_EMBEDDING_MODEL` | string | `nomic-embed-text` | Модель эмбеддингов для Ollama |

## 🗄️ Database Configuration

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `DATABASE_URL` | string | `mysql+mysqlconnector://root:123123@localhost:3306/db_test` | Строка подключения к БД |
| `DB_POOL_SIZE` | integer | `10` | Размер пула соединений |
| `DB_MAX_OVERFLOW` | integer | `20` | Максимальное переполнение пула |
| `DB_POOL_TIMEOUT` | integer | `30` | Таймаут получения соединения |
| `DB_POOL_RECYCLE` | integer | `3600` | Время переиспользования соединения |

## 🚀 Application Configuration

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `DEBUG` | boolean | `false` | Режим отладки |
| `LOG_LEVEL` | string | `INFO` | Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENVIRONMENT` | string | `development` | Среда выполнения (development, testing, staging, production) |
| `SECRET_KEY` | string | - | Секретный ключ приложения |
| `ALLOWED_HOSTS` | string | - | Разрешенные хосты (через запятую) |

## 📝 Примеры конфигурации

### Development (.env)

```bash
# Yandex Cloud
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxx
YANDEX_FOLDER_ID=b1g2xxxxxxxxxxxxxxxxx
USE_YANDEX_CLOUD=true
YANDEX_FALLBACK_TO_OLLAMA=true

# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Database
DATABASE_URL=mysql+mysqlconnector://root:password@localhost:3306/rag_dev

# Ollama fallback
OLLAMA_HOST=http://localhost:11434
```

### Staging (.env.staging)

```bash
# Yandex Cloud
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxx
YANDEX_FOLDER_ID=b1g2xxxxxxxxxxxxxxxxx
USE_YANDEX_CLOUD=true
YANDEX_FALLBACK_TO_OLLAMA=false
YANDEX_TIMEOUT=45
YANDEX_MAX_TOKENS=1500

# Staging settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=staging

# Database
DATABASE_URL=mysql+mysqlconnector://user:password@staging-db:3306/rag_staging

# Performance tuning
YANDEX_MAX_CONCURRENT=5
YANDEX_CACHE_TTL_HOURS=12
```

### Production (.env.production)

```bash
# Yandex Cloud
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxx
YANDEX_FOLDER_ID=b1g2xxxxxxxxxxxxxxxxx
USE_YANDEX_CLOUD=true
YANDEX_FALLBACK_TO_OLLAMA=false
YANDEX_TIMEOUT=60
YANDEX_MAX_TOKENS=2000
YANDEX_TEMPERATURE=0.05

# Production settings
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database
DATABASE_URL=mysql+mysqlconnector://prod_user:secure_password@prod-db:3306/rag_production

# Performance optimization
YANDEX_MAX_CONCURRENT=20
YANDEX_MAX_REQUESTS_PER_MINUTE=100
YANDEX_CACHE_TTL_HOURS=48
YANDEX_ENABLE_PERFORMANCE_MONITORING=true

# Database pool optimization
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=60
```

## 🔒 Безопасность

### Обязательные меры безопасности

1. **Никогда не коммитьте .env файлы** в репозиторий
2. **Используйте сильные пароли** для всех секретных переменных
3. **Регулярно ротируйте API ключи** Yandex Cloud
4. **Ограничьте права доступа** к файлам конфигурации

### Рекомендации по API ключам

#### 🔐 Безопасность
- **Минимальная длина**: 20 символов
- **Формат**: Только буквы, цифры, подчеркивания и дефисы
- **Роли**: Используйте минимально необходимые роли (`ai.languageModels.user`)
- **Ротация**: Меняйте ключи каждые 90 дней
- **Хранение**: Никогда не коммитьте в репозиторий

#### 📊 Мониторинг
- Отслеживайте использование через консоль Yandex Cloud
- Настройте алерты на превышение лимитов
- Мониторьте метрики через `/llm/metrics` эндпоинт
- Логируйте все API вызовы для аудита

#### 🚨 Что делать при компрометации ключа
```bash
# 1. Немедленно отзовите скомпрометированный ключ
# 2. Создайте новый ключ
# 3. Обновите переменные окружения
export YANDEX_API_KEY=new_secure_key_here
# 4. Перезапустите приложение
systemctl restart your-rag-app
# 5. Проверьте логи на подозрительную активность
```

### Валидация переменных

Система автоматически валидирует все переменные окружения при запуске:

```bash
# Проверка конфигурации
python test_config.py

# Валидация всех настроек
python -c "from config_utils import validate_all_config_new; validate_all_config_new()"
```

## 🐳 Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
      - USE_YANDEX_CLOUD=true
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=production
    env_file:
      - .env.production
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
data:
  USE_YANDEX_CLOUD: "true"
  YANDEX_LLM_MODEL: "yandexgpt"
  YANDEX_EMBEDDING_MODEL: "text-search-doc"
  YANDEX_TIMEOUT: "30"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
type: Opaque
stringData:
  YANDEX_API_KEY: "your-api-key-here"
  YANDEX_FOLDER_ID: "your-folder-id-here"
  DATABASE_URL: "mysql+mysqlconnector://user:pass@host:3306/db"
```

## 🔧 Troubleshooting

### Частые ошибки конфигурации

1. **"YANDEX_API_KEY environment variable is required"**
   ```bash
   # Проверьте наличие переменной
   echo $YANDEX_API_KEY
   # Или в .env файле
   grep YANDEX_API_KEY .env
   ```

2. **"Invalid API key format"**
   ```bash
   # API ключ должен быть длиннее 20 символов
   # и содержать только буквы, цифры, _ и -
   ```

3. **"Configuration validation failed"**
   ```bash
   # Запустите валидацию для диагностики
   python -c "
   from config_utils import validate_all_config_new
   try:
       config = validate_all_config_new()
       print('Конфигурация валидна')
   except Exception as e:
       print(f'Ошибка: {e}')
   "
   ```

### Диагностические команды

```bash
# Проверка всех переменных
python -c "
from config_utils import get_runtime_config
import json
config = get_runtime_config()
print(json.dumps(config, indent=2, ensure_ascii=False))
"

# Тест подключения к Yandex Cloud
python test_config.py

# Проверка доступности моделей
python -c "
from yandex_cloud_adapter import YandexCloudAdapter
from config_utils import YandexCloudConfig
config = YandexCloudConfig.from_env()
print('Доступные LLM модели:', list(config.llm_models.keys()))
print('Доступные Embedding модели:', list(config.embedding_models.keys()))
"
```

## 📚 Дополнительные ресурсы

- [Основная документация](../README.md)
- [Настройка Yandex Cloud](README_YANDEX_CLOUD.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Примеры конфигурации](CONFIG_EXAMPLES.md)
- [Документация Yandex Cloud](https://cloud.yandex.ru/docs/foundation-models/)