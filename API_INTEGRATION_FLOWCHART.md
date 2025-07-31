# Блок-схема интеграции с внешним API ИИ

## Общая архитектура системы

```mermaid
graph TB
    %% Пользовательский интерфейс
    UI[Frontend Vue.js<br/>Веб-интерфейс пользователя]
    
    %% Основные сервисы
    API[Backend API<br/>FastAPI + Python]
    DB[(База данных<br/>MySQL)]
    EXTERNAL_AI[Внешний API ИИ<br/>OpenAI/Claude/др.]
    
    %% Дополнительные компоненты
    LANGCHAIN[LangChain<br/>Оркестрация ИИ]
    VECTOR_DB[(Векторная БД<br/>Chroma/Pinecone)]
    DOC_PROC[Обработчик документов<br/>Embeddings]
    QUEUE[RabbitMQ<br/>Очередь задач]
    
    %% Соединения
    UI -->|HTTP запросы| API
    API -->|CRUD операции| DB
    API -->|Вопросы пользователя| LANGCHAIN
    LANGCHAIN -->|API вызовы| EXTERNAL_AI
    LANGCHAIN -->|Поиск контекста| VECTOR_DB
    API -->|Асинхронные задачи| QUEUE
    QUEUE -->|Обработка| DOC_PROC
    DOC_PROC -->|Векторные embeddings| VECTOR_DB
    
    %% Стили
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef ai fill:#fff3e0
    classDef queue fill:#fce4ec
    
    class UI frontend
    class API backend
    class DB,VECTOR_DB database
    class EXTERNAL_AI,LANGCHAIN,DOC_PROC ai
    class QUEUE queue
```

## Детальный процесс обработки запроса пользователя

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant F as Frontend
    participant B as Backend API
    participant L as LangChain
    participant AI as Внешний API ИИ
    participant V as Векторная БД
    participant DB as MySQL БД
    
    U->>F: Задает вопрос в чате
    F->>B: POST /api/llm/query
    B->>DB: Сохранение задачи в БД
    B->>L: Передача вопроса в LangChain
    
    L->>V: Поиск релевантных документов
    V-->>L: Возврат контекста
    
    L->>AI: Формирование промпта с контекстом
    AI-->>L: Ответ от ИИ
    
    L-->>B: Обработанный ответ
    B->>DB: Обновление статуса задачи
    B-->>F: Результат обработки
    F-->>U: Отображение ответа
```

## Процесс загрузки и обработки документов

```mermaid
flowchart TD
    A[Загрузка документа<br/>через админ-панель] --> B{Тип документа}
    
    B -->|PDF| C[PDF обработчик]
    B -->|DOCX| D[DOCX обработчик]
    B -->|TXT| E[TXT обработчик]
    
    C --> F[Извлечение текста]
    D --> F
    E --> F
    
    F --> G[Разбиение на чанки]
    G --> H[Генерация embeddings]
    H --> I[Сохранение в векторную БД]
    I --> J[Метаданные в MySQL]
    
    J --> K[Документ готов к поиску]
    
    %% Стили
    classDef upload fill:#e3f2fd
    classDef process fill:#f1f8e9
    classDef storage fill:#fff8e1
    
    class A upload
    class B,C,D,E,F,G,H process
    class I,J,K storage
```

## Компоненты системы и их взаимодействие

### 1. Frontend (Vue.js)
- **Роль**: Пользовательский интерфейс
- **Взаимодействие**: Отправляет HTTP запросы к Backend API
- **Основные функции**: Чат с ИИ, загрузка документов, управление контентом

### 2. Backend API (FastAPI + Python)
- **Роль**: Центральный сервер приложения
- **Взаимодействие**: 
  - Принимает запросы от Frontend
  - Управляет базой данных MySQL
  - Оркестрирует работу с LangChain
  - Обрабатывает файлы и документы

### 3. LangChain (Python библиотека)
- **Роль**: Оркестрация работы с ИИ
- **Взаимодействие**:
  - Формирует промпты для внешнего API ИИ
  - Управляет поиском в векторной базе данных
  - Обрабатывает контекст и ответы
  - Интегрируется с различными провайдерами ИИ

### 4. Внешний API ИИ
- **Роль**: Генерация ответов на основе промптов
- **Варианты**: OpenAI GPT, Anthropic Claude, Google Gemini, др.
- **Взаимодействие**: Получает структурированные запросы от LangChain

### 5. Векторная база данных
- **Роль**: Хранение и поиск семантических представлений документов
- **Варианты**: Chroma, Pinecone, Weaviate, Qdrant
- **Взаимодействие**: Предоставляет релевантный контекст для запросов

### 6. MySQL база данных
- **Роль**: Хранение структурированных данных
- **Содержит**: Пользователи, документы, метаданные, задачи
- **Взаимодействие**: CRUD операции через SQLAlchemy

### 7. RabbitMQ (опционально)
- **Роль**: Очередь для асинхронных задач
- **Применение**: Обработка больших документов, фоновые задачи
- **Взаимодействие**: Координация между компонентами

## Преимущества архитектуры с внешним API

1. **Масштабируемость**: Легко переключаться между провайдерами ИИ
2. **Гибкость**: Возможность использования разных моделей для разных задач
3. **Производительность**: Не требует локальных вычислительных ресурсов
4. **Обновляемость**: Автоматические обновления моделей от провайдеров
5. **Интеграция**: Простая интеграция с существующими системами

## Конфигурация для разных провайдеров

```python
# Пример конфигурации в settings.py
AI_PROVIDERS = {
    "openai": {
        "api_key": "sk-...",
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1"
    },
    "anthropic": {
        "api_key": "sk-ant-...",
        "model": "claude-3-sonnet",
        "base_url": "https://api.anthropic.com"
    },
    "google": {
        "api_key": "...",
        "model": "gemini-pro",
        "base_url": "https://generativelanguage.googleapis.com"
    }
}
```

## Безопасность и мониторинг

- **API ключи**: Безопасное хранение в переменных окружения
- **Rate limiting**: Ограничение запросов к внешним API
- **Логирование**: Мониторинг использования и ошибок
- **Fallback**: Резервные провайдеры при сбоях
- **Кэширование**: Сохранение частых запросов 