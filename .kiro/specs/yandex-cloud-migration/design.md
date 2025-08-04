# Design Document

## Overview

Данный документ описывает архитектурное решение для миграции системы RAG с локального Ollama на облачные сервисы Yandex Cloud. Миграция включает замену трех основных компонентов:

1. **LLM модели** - переход с Ollama на YandexGPT API
2. **Embedding модели** - переход на Yandex Cloud Embeddings API  
3. **Векторная база данных** - оценка возможности использования облачных решений Yandex

Дизайн сохраняет существующую архитектуру системы с минимальными изменениями в API, обеспечивая обратную совместимость и плавную миграцию.

## Architecture

### Текущая архитектура
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│ LLM State Manager│────│   Ollama Local  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  LLM Routes     │    │ Document Loader  │    │  Chroma Vector  │
└─────────────────┘    └──────────────────┘    │      DB         │
                                               └─────────────────┘
```

### Новая архитектура с Yandex Cloud
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│ LLM State Manager│────│  Yandex Cloud   │
└─────────────────┘    └──────────────────┘    │     APIs        │
         │                       │              └─────────────────┘
         │                       │                       │
         ▼                       ▼                       │
┌─────────────────┐    ┌──────────────────┐              │
│  LLM Routes     │    │ Document Loader  │              │
└─────────────────┘    └──────────────────┘              │
                                │                        │
                                ▼                        │
                       ┌─────────────────┐               │
                       │ Yandex Adapter  │◄──────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Chroma Vector  │
                       │      DB         │
                       │   (локально)    │
                       └─────────────────┘
```

## Components and Interfaces

### 1. Yandex Cloud Adapter

Новый компонент, который инкапсулирует всю логику взаимодействия с Yandex Cloud API.

```python
class YandexCloudAdapter:
    """Адаптер для работы с API Yandex Cloud"""
    
    def __init__(self, api_key: str, folder_id: str):
        self.api_key = api_key
        self.folder_id = folder_id
        self.base_url = "https://llm.api.cloud.yandex.net"
        
    async def generate_text(self, messages: str, model: str = "yandexgpt", **kwargs) -> str:
        """Генерация текста через YandexGPT API"""
        
    async def create_embeddings(self, texts: List[str], model: str = "text-search-doc") -> List[List[float]]:
        """Создание эмбеддингов через Yandex Embeddings API"""
        
    async def search_vectors(self, query_vector: List[float], top_k: int = 10) -> List[Dict]:
        """Поиск в векторной БД (если доступна в Yandex Cloud)"""
```

### 2. Обновленный LLM State Manager

Модификация существующего менеджера для работы с Yandex Cloud:

```python
class LLMStateManager:
    def __init__(self):
        # Существующие поля...
        self.yandex_adapter = None
        self.use_yandex_cloud = os.getenv("USE_YANDEX_CLOUD", "false").lower() == "true"
        
    def initialize_yandex_adapter(self):
        """Инициализация адаптера Yandex Cloud"""
        api_key = os.getenv("YANDEX_API_KEY")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
        
        if not api_key or not folder_id:
            raise ValueError("Yandex Cloud credentials not found")
            
        self.yandex_adapter = YandexCloudAdapter(api_key, folder_id)
```

### 3. Обновленный Document Loader

Модификация для поддержки эмбеддингов Yandex Cloud:

```python
class YandexEmbeddings:
    """Класс для создания эмбеддингов через Yandex Cloud API"""
    
    def __init__(self, yandex_adapter: YandexCloudAdapter):
        self.adapter = yandex_adapter
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для документов"""
        
    def embed_query(self, text: str) -> List[float]:
        """Создание эмбеддинга для поискового запроса"""
```

### 4. Обновленные LLM Routes

Минимальные изменения в существующих эндпоинтах:

```python
@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Генерация через Yandex Cloud или Ollama в зависимости от конфигурации"""
    
    if llm_state_manager.use_yandex_cloud:
        # Используем Yandex Cloud
        response = await llm_state_manager.yandex_adapter.generate_text(
            request.messages, 
            request.model
        )
    else:
        # Используем существующую логику Ollama
        # ... существующий код
```

## Data Models

### Конфигурация Yandex Cloud

```python
@dataclass
class YandexCloudConfig:
    api_key: str
    folder_id: str
    llm_model: str = "yandexgpt"
    embedding_model: str = "text-search-doc"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30
```

### Модели запросов и ответов

Существующие модели остаются без изменений для обеспечения обратной совместимости:

- `GenerateRequest` / `GenerateResponse`
- `QueryRequest` / `QueryResponse` 
- `QueryResultResponse`

### Расширенные модели для мониторинга

```python
@dataclass
class YandexCloudMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    average_response_time: float = 0.0
    last_error: Optional[str] = None
```

## Error Handling

### Стратегия обработки ошибок

1. **Retry механизм** с экспоненциальной задержкой для временных ошибок
2. **Circuit breaker** для предотвращения каскадных сбоев
3. **Graceful degradation** - возврат к локальным моделям при критических ошибках
4. **Детальное логирование** всех взаимодействий с API

```python
class YandexCloudErrorHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    async def handle_api_error(self, error: Exception, attempt: int) -> bool:
        """Обработка ошибок API с retry логикой"""
        
        if attempt >= self.max_retries:
            return False
            
        if isinstance(error, (TimeoutError, ConnectionError)):
            delay = self.base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
            return True
            
        return False
```

### Типы ошибок и их обработка

| Тип ошибки | HTTP код | Действие |
|------------|----------|----------|
| Неверный API ключ | 401 | Логирование, остановка сервиса |
| Превышен лимит | 429 | Retry с задержкой |
| Таймаут | 408 | Retry до 3 раз |
| Сервер недоступен | 5xx | Circuit breaker |
| Неверный запрос | 400 | Логирование, возврат ошибки |

## Testing Strategy

### Unit Tests

1. **YandexCloudAdapter** - тестирование всех методов с mock API
2. **Error handling** - тестирование различных сценариев ошибок
3. **Configuration** - валидация настроек и переменных окружения

### Integration Tests

1. **End-to-end тесты** с реальным API Yandex Cloud (в тестовой среде)
2. **Performance тесты** для сравнения с Ollama
3. **Load тесты** для проверки стабильности под нагрузкой

### Regression Tests

1. **API compatibility** - все существующие эндпоинты должны работать
2. **Response format** - формат ответов должен остаться неизменным
3. **Department isolation** - каждый отдел должен работать независимо

### Test Configuration

```python
# test_config.py
YANDEX_TEST_CONFIG = {
    "api_key": os.getenv("YANDEX_TEST_API_KEY"),
    "folder_id": os.getenv("YANDEX_TEST_FOLDER_ID"),
    "base_url": "https://llm.api.cloud.yandex.net",
    "timeout": 10
}
```

## Migration Strategy

### Поэтапная миграция

**Фаза 1: Подготовка инфраструктуры**
- Создание YandexCloudAdapter
- Настройка конфигурации и переменных окружения
- Базовые unit тесты

**Фаза 2: Миграция генерации текста**
- Обновление `/generate` эндпоинта
- Добавление переключателя между Ollama и Yandex Cloud
- Integration тесты

**Фаза 3: Миграция эмбеддингов**
- Создание YandexEmbeddings класса
- Обновление document_loader
- Тестирование векторного поиска

**Фаза 4: Оптимизация и мониторинг**
- Добавление метрик и мониторинга
- Оптимизация производительности
- Финальное тестирование

### Rollback Strategy

В случае проблем предусмотрен быстрый откат:

1. **Feature flag** `USE_YANDEX_CLOUD=false` для мгновенного отключения
2. **Сохранение Ollama кода** в качестве fallback
3. **Автоматический fallback** при критических ошибках API

## Performance Considerations

### Кэширование

1. **Эмбеддинги документов** - кэширование на уровне файловой системы
2. **Ответы LLM** - кэширование частых запросов (опционально)
3. **API токены** - кэширование токенов аутентификации

### Оптимизация запросов

1. **Batch processing** для эмбеддингов множественных документов
2. **Connection pooling** для HTTP соединений
3. **Асинхронная обработка** всех API вызовов

### Мониторинг производительности

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = YandexCloudMetrics()
        
    async def track_request(self, operation: str, duration: float, success: bool):
        """Отслеживание метрик производительности"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            
        self.metrics.average_response_time = (
            (self.metrics.average_response_time * (self.metrics.total_requests - 1) + duration) 
            / self.metrics.total_requests
        )
```

## Security Considerations

### Аутентификация и авторизация

1. **API ключи** хранятся только в переменных окружения
2. **Folder ID** также через переменные окружения
3. **Ротация ключей** - поддержка обновления без перезапуска

### Защита данных

1. **Логирование** - исключение чувствительных данных из логов
2. **HTTPS** - все запросы только через защищенное соединение
3. **Валидация входных данных** - проверка всех параметров запросов

### Compliance

1. **Данные пользователей** - обеспечение соответствия требованиям по защите данных
2. **Аудит** - логирование всех обращений к внешним API
3. **Резервное копирование** - сохранение возможности работы без внешних сервисов