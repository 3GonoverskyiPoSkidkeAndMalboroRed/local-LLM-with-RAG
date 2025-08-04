# RAG System with Yandex Cloud Integration

Система RAG (Retrieval-Augmented Generation) с поддержкой локальных моделей Ollama и облачных сервисов Yandex Cloud.

## 🚀 Возможности

- **Многопользовательская система** с поддержкой отделов
- **RAG (Retrieval-Augmented Generation)** для работы с корпоративными документами
- **Двойная поддержка**: Локальный Ollama + Yandex Cloud API
- **Векторный поиск** с использованием Chroma DB
- **Асинхронная обработка** запросов с очередями
- **Мониторинг и метрики** использования API
- **Автоматический fallback** между облачными и локальными моделями

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   FastAPI        │────│  Yandex Cloud   │
│   (React)       │    │   Backend        │    │     APIs        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       │
                       ┌─────────────────┐              │
                       │ LLM State       │              │
                       │ Manager         │              │
                       └─────────────────┘              │
                                │                       │
                                ▼                       │
                       ┌─────────────────┐              │
                       │ Document Loader │              │
                       │ + Embeddings    │◄─────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Chroma Vector  │
                       │      DB         │
                       └─────────────────┘
```

## 🛠️ Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd local-LLM-with-RAG
```

### 2. Установка зависимостей

```bash
cd server
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

#### Для Yandex Cloud (рекомендуется):

```bash
# Yandex Cloud Configuration (обязательные)
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=your_folder_id_here
USE_YANDEX_CLOUD=true

# Yandex Cloud Models (опциональные)
YANDEX_LLM_MODEL=yandexgpt
YANDEX_EMBEDDING_MODEL=text-search-doc

# Yandex Cloud API Settings (опциональные)
YANDEX_MAX_TOKENS=2000
YANDEX_TEMPERATURE=0.1
YANDEX_TIMEOUT=30
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net

# Yandex Cloud Features (опциональные)
YANDEX_FALLBACK_TO_OLLAMA=true
YANDEX_ENABLE_CACHING=true
YANDEX_ENABLE_METRICS=true
```

#### Для локального Ollama:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
USE_YANDEX_CLOUD=false
```

### 4. Настройка базы данных

```bash
# MySQL Configuration
DATABASE_URL=mysql+mysqlconnector://root:password@localhost:3306/db_name
```

### 5. Получение API ключей Yandex Cloud

**📋 Пошаговая инструкция:**

1. **Создание аккаунта и каталога**
   - Зарегистрируйтесь в [Yandex Cloud](https://console.cloud.yandex.ru/)
   - Создайте новый каталог или используйте существующий
   - Скопируйте ID каталога (например: `b1g2xxxxxxxxxxxxxxxxx`)

2. **Создание сервисного аккаунта**
   - Перейдите в раздел "Сервисные аккаунты"
   - Нажмите "Создать сервисный аккаунт"
   - Укажите имя (например: `rag-service-account`)
   - Назначьте роль `ai.languageModels.user`

3. **Создание API ключа**
   - Откройте созданный сервисный аккаунт
   - Перейдите на вкладку "API-ключи"
   - Нажмите "Создать API-ключ"
   - **Важно**: Сохраните ключ сразу, он больше не будет показан

4. **Проверка настроек**
   ```bash
   # Проверьте доступность API
   curl -H "Authorization: Api-Key YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"modelUri": "gpt://YOUR_FOLDER_ID/yandexgpt/latest", "completionOptions": {"stream": false, "temperature": 0.1, "maxTokens": 10}, "messages": [{"role": "user", "text": "test"}]}' \
        https://llm.api.cloud.yandex.net/foundationModels/v1/completion
   ```

**📚 Подробная инструкция**: [Настройка Yandex Cloud](server/README_YANDEX_CLOUD.md)

## 🚀 Запуск

### Тестирование конфигурации

```bash
# Проверка настроек
python test_config.py

# Демонстрация YandexGPT API
python demo_yandex_generation.py

# Тестирование эндпоинта /generate
python demo_generate_endpoint.py

# Демонстрация YandexEmbeddings
python demo_yandex_embeddings.py

# Тестирование интеграции с document_loader
python demo_document_loader_integration.py

# Демонстрация LLMStateManager
python demo_llm_state_manager.py

# Запуск тестов
python -m pytest tests/test_yandex_cloud_adapter.py -v
python -m pytest tests/test_yandex_llm.py -v
```

### Запуск сервера

```bash
# Запуск в режиме разработки
python app.py --web --port 8000

# Или через uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker (опционально)

```bash
# Сборка и запуск через Docker Compose
docker-compose up --build
```

## 📚 API Документация

### Основные эндпоинты

#### Генерация текста (без RAG)
```bash
POST /llm/generate
{
  "messages": "Привет! Как дела?",
  "model": "yandexgpt"
}
```

#### Генерация с RAG
```bash
# Создание задачи
POST /llm/query
{
  "question": "Что такое машинное обучение?",
  "department_id": "1"
}

# Получение результата
GET /llm/query/{task_id}
```

#### Инициализация отдела
```bash
POST /llm/initialize
{
  "model_name": "yandexgpt",
  "embedding_model_name": "text-search-doc",
  "documents_path": "/path/to/documents",
  "department_id": "1"
}
```

### Swagger UI

После запуска сервера документация доступна по адресу:
- http://localhost:8000/docs

## 🔧 Конфигурация

### Основные переменные окружения

#### Yandex Cloud (обязательные при USE_YANDEX_CLOUD=true)
| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `USE_YANDEX_CLOUD` | boolean | `false` | Включение Yandex Cloud интеграции |
| `YANDEX_API_KEY` | string | - | API ключ сервисного аккаунта |
| `YANDEX_FOLDER_ID` | string | - | ID каталога в Yandex Cloud |

#### Модели и параметры
| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `YANDEX_LLM_MODEL` | string | `yandexgpt` | Модель для генерации (`yandexgpt`, `yandexgpt-lite`) |
| `YANDEX_EMBEDDING_MODEL` | string | `text-search-doc` | Модель для эмбеддингов |
| `YANDEX_MAX_TOKENS` | integer | `2000` | Максимальное количество токенов (1-8000) |
| `YANDEX_TEMPERATURE` | float | `0.1` | Температура генерации (0.0-1.0) |
| `YANDEX_TIMEOUT` | integer | `30` | Таймаут запросов в секундах (5-300) |

#### Производительность и надежность
| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `YANDEX_FALLBACK_TO_OLLAMA` | boolean | `true` | Fallback на Ollama при ошибках |
| `YANDEX_MAX_RETRIES` | integer | `3` | Максимальное количество повторных попыток |
| `YANDEX_MAX_CONCURRENT` | integer | `10` | Максимальное количество одновременных запросов |
| `YANDEX_ENABLE_CACHING` | boolean | `true` | Включение кэширования эмбеддингов |

#### База данных и Ollama
| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `DATABASE_URL` | string | - | Строка подключения к MySQL |
| `OLLAMA_HOST` | string | `http://localhost:11434` | Адрес Ollama сервера (для fallback) |

**📚 Подробная документация:**
- [Полный список переменных окружения](server/ENVIRONMENT_VARIABLES.md)
- [Примеры конфигурации для разных сред](server/CONFIG_EXAMPLES.md)
- [Настройка Yandex Cloud](server/README_YANDEX_CLOUD.md)

### 🔐 Безопасность и лучшие практики

#### Защита API ключей
- ✅ Используйте переменные окружения, никогда не коммитьте ключи в код
- ✅ Регулярно ротируйте API ключи (рекомендуется каждые 90 дней)
- ✅ Ограничьте права сервисного аккаунта минимально необходимыми
- ✅ Мониторьте использование API через консоль Yandex Cloud

#### Оптимизация затрат
- 💰 Используйте `yandexgpt-lite` для простых задач (дешевле)
- 💰 Включите кэширование эмбеддингов (`YANDEX_ENABLE_CACHING=true`)
- 💰 Настройте разумные лимиты (`YANDEX_MAX_TOKENS`, `YANDEX_MAX_CONCURRENT`)
- 💰 Мониторьте метрики использования через `/llm/metrics`

## 📊 Мониторинг

### Метрики API

```bash
# Получение метрик использования
GET /llm/metrics

# Статус очереди отдела
GET /llm/queue/status/{department_id}

# Зависшие задачи
GET /llm/queue/stuck-tasks
```

### Отладочные эндпоинты

```bash
# Состояние отдела
GET /llm/debug/department-state/{department_id}

# Переинициализация отдела
POST /llm/debug/reinitialize/{department_id}
```

## 🔍 Troubleshooting

### Быстрая диагностика

```bash
# Проверка конфигурации
python test_config.py

# Полная диагностика системы
bash server/diagnostic.sh

# Расширенная диагностика с подробными метриками
bash server/diagnostic.sh --full --output-file diagnostic_report.txt

# Проверка API Yandex Cloud
python -c "
from yandex_cloud_adapter import YandexCloudAdapter
from config_utils import YandexCloudConfig
config = YandexCloudConfig.from_env()
adapter = YandexCloudAdapter(config)
print('API работает:', adapter.generate_text('test', max_tokens=1))
"
```

### 🆘 Сбор информации для поддержки

```bash
# Базовый сбор информации
bash server/collect_support_info.sh

# Полный сбор с логами и статистикой кэша
bash server/collect_support_info.sh --include-logs --include-cache-stats

# Результат: /tmp/rag_support_YYYYMMDD_HHMMSS.tar.gz
# Отправьте этот файл в службу поддержки
```

### Частые проблемы

1. **Ошибка "YANDEX_API_KEY environment variable is required"**
   ```bash
   # Проверьте .env файл
   grep YANDEX_API_KEY .env
   # Установите переменную
   export YANDEX_API_KEY=your_key_here
   ```

2. **Ошибка 401: "Unauthorized"**
   ```bash
   # Проверьте права сервисного аккаунта в консоли Yandex Cloud
   # Роль должна быть: ai.languageModels.user
   ```

3. **Ошибка 429: "Rate limit exceeded"**
   ```bash
   # Уменьшите частоту запросов
   export YANDEX_MAX_REQUESTS_PER_MINUTE=30
   export YANDEX_MAX_CONCURRENT=5
   ```

4. **Медленные ответы от API**
   ```bash
   # Увеличьте таймаут и включите кэширование
   export YANDEX_TIMEOUT=60
   export YANDEX_ENABLE_CACHING=true
   ```

**📚 Подробное руководство:** [TROUBLESHOOTING.md](server/TROUBLESHOOTING.md)

### Логирование

```bash
# Включение debug логов
export LOG_LEVEL=DEBUG
python app.py --web --port 8000

# Мониторинг в реальном времени
tail -f /var/log/rag-app.log | grep -E "(ERROR|WARNING|Yandex)"
```

## 🧪 Тестирование

### Unit тесты

```bash
# Все тесты
python -m pytest tests/ -v

# Только Yandex Cloud
python -m pytest tests/test_yandex_cloud_adapter.py -v

# С покрытием кода
python -m pytest tests/ --cov=. --cov-report=html
```

### Integration тесты

```bash
# Тест реального API (требует настроенные ключи)
python test_config.py
```

## 📁 Структура проекта

```
├── server/
│   ├── yandex_cloud_adapter.py    # Адаптер для Yandex Cloud API
│   ├── llm_state_manager.py       # Управление состоянием LLM
│   ├── llm.py                     # LLM цепочки и промпты
│   ├── document_loader.py         # Загрузка и индексация документов
│   ├── config_utils.py            # Утилиты конфигурации
│   ├── app.py                     # Основное приложение FastAPI
│   ├── routes/
│   │   └── llm_routes.py          # API роуты для LLM
│   ├── tests/
│   │   └── test_yandex_cloud_adapter.py
│   ├── .env.example               # Пример конфигурации
│   └── requirements.txt           # Python зависимости
├── .kiro/specs/yandex-cloud-migration/  # Спецификация миграции
├── docker-compose.yml             # Docker конфигурация
└── README.md                      # Этот файл
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📚 Документация

### Основные руководства

- **[README_YANDEX_CLOUD.md](server/README_YANDEX_CLOUD.md)** - Подробная настройка Yandex Cloud интеграции
- **[ENVIRONMENT_VARIABLES.md](server/ENVIRONMENT_VARIABLES.md)** - Полный справочник переменных окружения
- **[CONFIG_EXAMPLES.md](server/CONFIG_EXAMPLES.md)** - Примеры конфигурации для разных сред
- **[TROUBLESHOOTING.md](server/TROUBLESHOOTING.md)** - Диагностика и решение проблем

### Конфигурация по средам

- **Development**: Максимальная отладочная информация, fallback на Ollama
- **Testing**: Стабильная конфигурация для автоматических тестов  
- **Staging**: Максимально близко к production с дополнительным логированием
- **Production**: Оптимизированная конфигурация для высокой производительности

### Быстрые ссылки

```bash
# Проверка конфигурации
python test_config.py

# Валидация всех настроек
python -c "from config_utils import validate_all_config_new; validate_all_config_new()"

# Диагностика системы
bash server/diagnostic.sh

# Примеры использования
python server/demo_yandex_generation.py
python server/demo_yandex_embeddings.py
```

## 🔗 Полезные ссылки

- [Документация Yandex Cloud Foundation Models](https://cloud.yandex.ru/docs/foundation-models/)
- [API Reference Yandex Cloud](https://cloud.yandex.ru/docs/foundation-models/api-ref/)
- [Консоль Yandex Cloud](https://console.cloud.yandex.ru/)
- [Статус сервисов Yandex Cloud](https://status.cloud.yandex.ru/)
- [Ollama Documentation](https://ollama.ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Chroma DB Documentation](https://docs.trychroma.com/)

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. **Быстрая диагностика**: Запустите `python test_config.py`
2. **Проверьте документацию**: [TROUBLESHOOTING.md](server/TROUBLESHOOTING.md)
3. **Соберите информацию**: `bash server/collect_support_info.sh`
4. **Создайте issue** в репозитории с приложенной диагностической информацией
5. **Обратитесь к команде разработки**

### Сбор диагностической информации

```bash
# Автоматический сбор информации для поддержки
bash server/collect_support_info.sh

# Полный сбор с логами и кэш-статистикой
bash server/collect_support_info.sh --include-logs --include-cache-stats

# Результат: /tmp/rag_support_YYYYMMDD_HHMMSS.tar.gz
# Отправьте этот файл в службу поддержки вместе с описанием проблемы
```

### Автоматическая диагностика

```bash
# Быстрая проверка системы
bash server/diagnostic.sh

# Полная диагностика с сохранением отчета
bash server/diagnostic.sh --full --output-file system_report.txt

# Проверка только конфигурации
python -c "from config_utils import validate_all_config_new; validate_all_config_new()"
```