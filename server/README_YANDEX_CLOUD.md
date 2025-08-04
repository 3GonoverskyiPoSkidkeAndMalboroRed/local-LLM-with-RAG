# Интеграция с Yandex Cloud

Данное руководство описывает настройку и использование интеграции с Yandex Cloud для замены локального Ollama на облачные сервисы YandexGPT и Embeddings.

## Быстрый старт

### 1. Получение API ключей

1. Перейдите в [консоль Yandex Cloud](https://console.cloud.yandex.ru/)
2. Создайте или выберите существующий каталог (folder)
3. Перейдите в раздел "Сервисные аккаунты"
4. Создайте новый сервисный аккаунт с ролью `ai.languageModels.user`
5. Создайте API ключ для сервисного аккаунта
6. Скопируйте ID каталога из URL или настроек каталога

### 2. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

Заполните следующие обязательные переменные:

```bash
# Yandex Cloud Configuration
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=your_folder_id_here
USE_YANDEX_CLOUD=true
```

### 3. Тестирование конфигурации

```bash
# Проверка конфигурации
python test_config.py

# Запуск unit тестов
python -m pytest tests/test_yandex_cloud_adapter.py -v
```

### 4. Запуск приложения

```bash
# Запуск с Yandex Cloud
python app.py --web --port 8000
```

## Подробная конфигурация

### Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|------------|--------------|--------------|----------|
| `YANDEX_API_KEY` | ✅ | - | API ключ сервисного аккаунта |
| `YANDEX_FOLDER_ID` | ✅ | - | ID каталога в Yandex Cloud |
| `USE_YANDEX_CLOUD` | ❌ | `false` | Включение интеграции с Yandex Cloud |
| `YANDEX_FALLBACK_TO_OLLAMA` | ❌ | `true` | Fallback на Ollama при ошибках Yandex Cloud |
| `YANDEX_LLM_MODEL` | ❌ | `yandexgpt` | Модель для генерации текста |
| `YANDEX_EMBEDDING_MODEL` | ❌ | `text-search-doc` | Модель для эмбеддингов |
| `YANDEX_MAX_TOKENS` | ❌ | `2000` | Максимальное количество токенов |
| `YANDEX_TEMPERATURE` | ❌ | `0.1` | Температура генерации (0.0-1.0) |
| `YANDEX_TIMEOUT` | ❌ | `30` | Таймаут запросов в секундах |
| `YANDEX_BASE_URL` | ❌ | `https://llm.api.cloud.yandex.net` | Базовый URL API |
| `YANDEX_EMBEDDINGS_CACHE_DIR` | ❌ | `/app/files/embeddings_cache` | Директория кэша эмбеддингов |

### Доступные модели

#### LLM модели (для генерации текста):
- `yandexgpt` - Основная модель YandexGPT
- `yandexgpt-lite` - Облегченная версия (быстрее, дешевле)

#### Embedding модели (для векторного поиска):
- `text-search-doc` - Для индексации документов (рекомендуется)
- `text-search-query` - Для поисковых запросов

**Использование эмбеддингов:**

```python
from yandex_embeddings import create_yandex_embeddings

# Создание экземпляра
embeddings = create_yandex_embeddings(model="text-search-doc")

# Эмбеддинги для документов
documents = ["Текст 1", "Текст 2", "Текст 3"]
doc_embeddings = embeddings.embed_documents(documents)

# Эмбеддинг для поискового запроса
query = "Поисковый запрос"
query_embedding = embeddings.embed_query(query)
```

## Архитектура

### Компоненты

1. **YandexCloudAdapter** - Основной класс для взаимодействия с API
2. **YandexCloudConfig** - Конфигурация подключения
3. **YandexCloudMetrics** - Метрики использования API
4. **Error Handling** - Обработка ошибок с retry механизмом

### Схема работы

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│ LLM State Manager│────│ YandexCloudAdapter│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  LLM Routes     │    │ Document Loader  │    │  Yandex Cloud   │
│  /generate      │    │ + YandexEmbeddings│    │     APIs        │
│  /query         │    └──────────────────┘    └─────────────────┘
└─────────────────┘
```

## Использование API

### Генерация текста (без RAG)

```bash
# Базовый запрос
curl -X POST "http://localhost:8000/llm/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Привет! Как дела?",
    "model": "yandexgpt"
  }'

# Запрос с кастомными параметрами
curl -X POST "http://localhost:8000/llm/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Придумай короткую историю про робота",
    "model": "yandexgpt",
    "temperature": 0.8,
    "max_tokens": 200
  }'
```

### Генерация с RAG

```bash
# Создание задачи
curl -X POST "http://localhost:8000/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что такое машинное обучение?",
    "department_id": "1"
  }'

# Получение результата
curl "http://localhost:8000/llm/query/{task_id}"
```

### Получение метрик

```bash
curl "http://localhost:8000/llm/metrics"
```

## Мониторинг и отладка

### Логирование

Система логирует все взаимодействия с Yandex Cloud API:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Метрики

Доступные метрики:
- Общее количество запросов
- Успешные/неуспешные запросы
- Использованные токены
- Среднее время ответа
- Последняя ошибка

### Отладочные эндпоинты

```bash
# Проверка состояния отдела
curl "http://localhost:8000/llm/debug/department-state/1"

# Переинициализация отдела
curl -X POST "http://localhost:8000/llm/debug/reinitialize/1"
```

## Обработка ошибок

### Типы ошибок

1. **YandexCloudAuthError** (401) - Неверный API ключ
2. **YandexCloudRateLimitError** (429) - Превышен лимит запросов
3. **YandexCloudTimeoutError** - Таймаут запроса
4. **YandexCloudError** - Общие ошибки API

### Retry механизм

- Автоматический retry для временных ошибок (429, 5xx)
- Экспоненциальная задержка: 1s, 2s, 4s
- Максимум 3 попытки

### Fallback на Ollama

Система поддерживает автоматический fallback на локальный Ollama при ошибках Yandex Cloud:

```bash
# Включение fallback (по умолчанию включен)
export YANDEX_FALLBACK_TO_OLLAMA=true

# Отключение fallback (только Yandex Cloud)
export YANDEX_FALLBACK_TO_OLLAMA=false

# Полное отключение Yandex Cloud
export USE_YANDEX_CLOUD=false
```

**Логика работы fallback:**
1. Если `USE_YANDEX_CLOUD=true` - сначала пытается Yandex Cloud
2. При ошибке Yandex Cloud и `YANDEX_FALLBACK_TO_OLLAMA=true` - переключается на Ollama
3. Если `YANDEX_FALLBACK_TO_OLLAMA=false` - возвращает ошибку Yandex Cloud
4. Для Yandex-специфичных моделей (`yandexgpt`, `yandexgpt-lite`) fallback показывает соответствующее сообщение

## Оптимизация производительности

### Кэширование

1. **Эмбеддинги документов** - автоматическое кэширование на файловой системе
2. **HTTP соединения** - используется connection pooling
3. **Токены аутентификации** - кэшируются с автообновлением

**Управление кэшем эмбеддингов:**

```python
from yandex_embeddings import create_yandex_embeddings

embeddings = create_yandex_embeddings(cache_enabled=True)

# Статистика кэша
stats = embeddings.get_cache_stats()
print(f"Файлов в кэше: {stats['files_count']}")
print(f"Размер кэша: {stats['total_size_mb']} МБ")

# Очистка кэша
deleted_count = embeddings.clear_cache()
print(f"Удалено файлов: {deleted_count}")
```

### Batch обработка

Эмбеддинги создаются батчами по 100 текстов для оптимизации:

```python
# Автоматическое разбиение на батчи
embeddings = await adapter.create_embeddings(large_text_list)
```

### Настройка производительности

```bash
# Увеличение таймаута для медленных запросов
YANDEX_TIMEOUT=60

# Уменьшение количества токенов для ускорения
YANDEX_MAX_TOKENS=1000

# Снижение температуры для более предсказуемых ответов
YANDEX_TEMPERATURE=0.0
```

## Безопасность

### Защита API ключей

- Никогда не коммитьте API ключи в репозиторий
- Используйте переменные окружения
- Регулярно ротируйте ключи

### Логирование

- API ключи не логируются (заменяются на ***)
- Чувствительные данные фильтруются из логов

### Валидация

- Автоматическая валидация всех параметров
- Проверка формата API ключей и folder_id

## Миграция с Ollama

### Пошаговая миграция

1. **Подготовка**
   ```bash
   # Создание резервной копии
   cp -r /app/files/storage /app/files/storage_backup
   ```

2. **Настройка Yandex Cloud**
   ```bash
   # Настройка переменных окружения
   export USE_YANDEX_CLOUD=true
   export YANDEX_API_KEY=your_key
   export YANDEX_FOLDER_ID=your_folder
   ```

3. **Тестирование**
   ```bash
   python test_config.py
   ```

4. **Переключение**
   ```bash
   # Перезапуск приложения
   systemctl restart your-app
   ```

### Откат на Ollama

В случае проблем:

```bash
# Быстрый откат
export USE_YANDEX_CLOUD=false
systemctl restart your-app
```

## Troubleshooting

### Частые проблемы

1. **"YANDEX_API_KEY environment variable is required"**
   - Проверьте наличие переменной в .env файле
   - Убедитесь что .env файл загружается

2. **"Invalid API key" (401)**
   - Проверьте правильность API ключа
   - Убедитесь что сервисный аккаунт имеет нужные роли

3. **"Rate limit exceeded" (429)**
   - Уменьшите частоту запросов
   - Проверьте лимиты в консоли Yandex Cloud

4. **Медленные ответы**
   - Увеличьте YANDEX_TIMEOUT
   - Уменьшите YANDEX_MAX_TOKENS
   - Проверьте сетевое соединение

### Диагностика

```bash
# Проверка конфигурации
python -c "from config_utils import print_config_summary; print_config_summary()"

# Тест подключения
python test_config.py

# Проверка логов
tail -f /var/log/your-app.log | grep -i yandex
```

## Поддержка

Для получения поддержки:

1. Проверьте логи приложения
2. Запустите диагностические скрипты
3. Обратитесь к документации Yandex Cloud
4. Создайте issue в репозитории проекта

## Полезные ссылки

- [Документация Yandex Cloud Foundation Models](https://cloud.yandex.ru/docs/foundation-models/)
- [API Reference](https://cloud.yandex.ru/docs/foundation-models/api-ref/)
- [Консоль Yandex Cloud](https://console.cloud.yandex.ru/)
- [Тарифы и лимиты](https://cloud.yandex.ru/docs/foundation-models/pricing)