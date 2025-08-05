# Улучшенная архитектура RAG для Yandex Cloud API

## 🎯 Обзор проблем и решений

### Проблемы в исходной архитектуре:

1. **Дублирование логики**: RAG операции смешаны с базовой генерацией текста
2. **Отсутствие специализированных эндпоинтов**: Нет отдельных эндпоинтов для RAG операций
3. **Неэффективное кэширование**: Отсутствует кэширование результатов RAG операций
4. **Слабая обработка ошибок**: Нет централизованной обработки ошибок для RAG
5. **Отсутствие метрик**: Нет детальной аналитики RAG операций

### Решения:

1. **Специализированный RAG сервис** (`yandex_rag_service.py`)
2. **Отдельные RAG эндпоинты** (`yandex_rag_routes.py`)
3. **Улучшенное кэширование** с поддержкой RAG результатов
4. **Централизованная обработка ошибок** с retry механизмами
5. **Детальные метрики** для мониторинга производительности

## 🏗️ Архитектура

### Компоненты системы:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  yandex_routes  │  │ yandex_rag_routes│  │  llm_routes  │ │
│  │   (базовые      │  │  (специализир.   │  │  (legacy)    │ │
│  │   эндпоинты)    │  │   RAG)          │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    YandexRAGService                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   LLM Adapter   │  │  Embeddings     │  │ Error Handler│ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Cache Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  RAG Results    │  │  Embeddings     │  │  LLM Cache   │ │
│  │     Cache       │  │     Cache       │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Yandex Cloud API                         │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   YandexGPT     │  │  Embeddings API │                  │
│  │                 │  │                 │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Новые эндпоинты

### Базовый URL для RAG операций:
```
http://localhost:8000/api/yandex/rag
```

### 1. Основной RAG запрос
**POST** `/api/yandex/rag/query`

```json
{
  "query": "Какие преимущества у искусственного интеллекта?",
  "department_id": "default",
  "max_chunks": 5,
  "similarity_threshold": 0.7,
  "include_metadata": true,
  "use_cache": true
}
```

**Ответ:**
```json
{
  "answer": "Искусственный интеллект предоставляет множество преимуществ...",
  "sources": [
    {
      "chunk": "ИИ может автоматизировать рутинные задачи...",
      "score": 0.85,
      "metadata": {
        "file_name": "ai_benefits.pdf",
        "page_number": 3
      }
    }
  ],
  "chunks_used": ["ИИ может автоматизировать рутинные задачи..."],
  "similarity_scores": [0.85],
  "tokens_used": 150,
  "processing_time": 2.34,
  "model_used": "yandexgpt",
  "cache_hit": false
}
```

### 2. Пакетный RAG запрос
**POST** `/api/yandex/rag/query/batch`

```json
{
  "queries": [
    "Что такое машинное обучение?",
    "Какие типы нейронных сетей существуют?",
    "Как работает deep learning?"
  ],
  "department_id": "default",
  "max_chunks": 3,
  "similarity_threshold": 0.7
}
```

### 3. Метрики RAG сервиса
**GET** `/api/yandex/rag/metrics`

```json
{
  "total_queries": 150,
  "successful_queries": 145,
  "failed_queries": 5,
  "success_rate": 0.967,
  "average_response_time": 2.1,
  "average_chunks_used": 3.2,
  "cache_hit_rate": 0.35,
  "last_query_time": "2024-01-15T10:30:00",
  "model_used": "yandexgpt",
  "embedding_model": "text-search-doc"
}
```

### 4. Проверка здоровья
**GET** `/api/yandex/rag/health`

```json
{
  "status": "healthy",
  "rag_service_available": true,
  "llm_model_available": true,
  "embedding_model_available": true,
  "cache_available": true,
  "error_handler_available": true,
  "last_error": null
}
```

### 5. Конфигурация
**GET** `/api/yandex/rag/config`

```json
{
  "llm_model": "yandexgpt",
  "embedding_model": "text-search-doc",
  "cache_enabled": true,
  "max_retries": 3,
  "default_max_chunks": 5,
  "default_similarity_threshold": 0.7
}
```

## 🔧 Конфигурация

### Переменные окружения:

```bash
# Обязательные
YANDEX_API_KEY=your_api_key
YANDEX_FOLDER_ID=your_folder_id

# RAG настройки
YANDEX_RAG_CACHE_ENABLED=true
YANDEX_RAG_MAX_RETRIES=3
YANDEX_RAG_DEFAULT_CHUNKS=5
YANDEX_RAG_SIMILARITY_THRESHOLD=0.7

# Модели
YANDEX_LLM_MODEL=yandexgpt
YANDEX_EMBEDDING_MODEL=text-search-doc
```

## 📊 Мониторинг и метрики

### Ключевые метрики:

1. **Производительность**:
   - Среднее время ответа
   - Количество обработанных запросов
   - Успешность операций

2. **Качество RAG**:
   - Среднее количество используемых чанков
   - Средние scores схожести
   - Hit rate кэша

3. **Системное здоровье**:
   - Доступность компонентов
   - Ошибки и их типы
   - Состояние кэша

## 🚀 Преимущества новой архитектуры

### 1. **Производительность**
- ✅ Кэширование результатов RAG операций
- ✅ Оптимизированный поиск релевантных чанков
- ✅ Batch обработка запросов
- ✅ Retry механизмы с exponential backoff

### 2. **Надежность**
- ✅ Circuit breaker для защиты от сбоев
- ✅ Graceful degradation при недоступности компонентов
- ✅ Централизованная обработка ошибок
- ✅ Детальное логирование

### 3. **Масштабируемость**
- ✅ Модульная архитектура
- ✅ Отдельные эндпоинты для разных типов операций
- ✅ Возможность горизонтального масштабирования
- ✅ Конфигурируемые параметры

### 4. **Мониторинг**
- ✅ Детальные метрики производительности
- ✅ Health checks для всех компонентов
- ✅ Аналитика использования кэша
- ✅ Отслеживание ошибок

## 🔄 Миграция

### Пошаговый план:

1. **Подготовка**:
   ```bash
   # Создайте backup текущей системы
   cp -r server server_backup
   
   # Установите новые зависимости
   pip install -r requirements.txt
   ```

2. **Обновление конфигурации**:
   ```bash
   # Добавьте новые переменные окружения
   echo "YANDEX_RAG_CACHE_ENABLED=true" >> .env
   echo "YANDEX_RAG_MAX_RETRIES=3" >> .env
   ```

3. **Тестирование**:
   ```bash
   # Запустите тесты
   python -m pytest tests/test_yandex_rag.py
   
   # Проверьте health check
   curl http://localhost:8000/api/yandex/rag/health
   ```

4. **Переключение трафика**:
   - Постепенно переводите клиентов на новые эндпоинты
   - Мониторьте метрики и ошибки
   - При необходимости откатитесь к старой версии

## 🧪 Тестирование

### Примеры тестов:

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_rag_query():
    response = client.post("/api/yandex/rag/query", json={
        "query": "Тестовый вопрос",
        "department_id": "default"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data

def test_rag_health():
    response = client.get("/api/yandex/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
```

## 📈 Оптимизация производительности

### Рекомендации:

1. **Кэширование**:
   - Используйте Redis для распределенного кэша
   - Настройте TTL для разных типов данных
   - Мониторьте hit rate

2. **Поиск чанков**:
   - Оптимизируйте размер чанков
   - Используйте индексы в базе данных
   - Настройте пороги схожести

3. **LLM запросы**:
   - Используйте streaming для длинных ответов
   - Оптимизируйте промпты
   - Настройте параметры модели

4. **Мониторинг**:
   - Настройте алерты на критические метрики
   - Ведите логи всех операций
   - Анализируйте паттерны использования

## 🔮 Будущие улучшения

1. **Векторная база данных**: Интеграция с Pinecone или Weaviate
2. **Мультимодальность**: Поддержка изображений и документов
3. **Персонализация**: Адаптация под пользователя
4. **A/B тестирование**: Сравнение разных подходов
5. **Автоматическое обучение**: Улучшение на основе обратной связи 