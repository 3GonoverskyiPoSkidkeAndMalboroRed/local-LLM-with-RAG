# Техническое описание системы

## Архитектура системы

### Общая схема

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   (MySQL)       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Yandex Cloud   │
                    │   ML SDK        │
                    │                 │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Yandex Search  │
                    │   API v2        │
                    │                 │
                    └─────────────────┘
```

### Компоненты системы

#### Frontend (Vue.js)
- **Фреймворк**: Vue.js 3 с Composition API
- **UI библиотека**: Soft UI Dashboard
- **Сборщик**: Vite
- **Стилизация**: Bootstrap 5 + Custom CSS
- **HTTP клиент**: Axios
- **Роутинг**: Vue Router
- **Состояние**: Vuex Store

#### Backend (FastAPI)
- **Фреймворк**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **Аутентификация**: JWT токены
- **Валидация**: Pydantic с поддержкой Optional типов
- **Асинхронность**: asyncio
- **Кэширование**: Локальное хранение эмбеддингов

#### База данных (MySQL)
- **СУБД**: MySQL 8.0
- **Миграции**: Alembic
- **Пулинг соединений**: SQLAlchemy Engine
- **Иерархическая система прав доступа**

#### ИИ-сервисы
- **Провайдер**: Yandex Cloud ML SDK
- **Модели**: 
  - YandexGPT для генерации текста
  - text-search-doc для эмбеддингов
  - search_api.generative для веб-поиска
- **RAG система**: Retrieval-Augmented Generation
- **Веб-поиск**: Интеграция с Yandex Search API v2

## Структура базы данных

### Основные таблицы

#### Пользователи и доступ
```sql
-- Пользователи
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    login VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INT,
    department_id INT,
    access_id INT,
    auth_key VARCHAR(255),
    full_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);

-- Отделы
CREATE TABLE department (
    id INT PRIMARY KEY AUTO_INCREMENT,
    department_name VARCHAR(255) NOT NULL
);

-- Уровни доступа
CREATE TABLE access (
    id INT PRIMARY KEY AUTO_INCREMENT,
    access_name VARCHAR(50) UNIQUE NOT NULL
);
```

#### Контент и документы
```sql
-- Контент
CREATE TABLE content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(255) NOT NULL,
    access_level INT,
    department_id INT,
    tag_id INT,
    FOREIGN KEY (access_level) REFERENCES access(id),
    FOREIGN KEY (department_id) REFERENCES department(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- Теги
CREATE TABLE tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(255) NOT NULL
);
```

## API Endpoints

### Аутентификация
- `POST /auth/login` - Вход в систему
- `POST /auth/register` - Регистрация (только админы)
- `GET /auth/me` - Получение информации о текущем пользователе

### Контент
- `GET /content/all` - Получение всего контента (только админы)
- `GET /content/{content_id}` - Получение контента по ID
- `PUT /content/{content_id}` - Обновление контента
- `DELETE /content/{content_id}` - Удаление контента
- `POST /content/upload` - Загрузка файлов
- `GET /content/download-file/{content_id}` - Скачивание файла
- `GET /content/public-download/{content_id}` - Публичное скачивание с токеном
- `GET /content/download-token/{content_id}` - Генерация токена для скачивания

### Библиотека документов
- `GET /user/{user_id}/content/by-tags` - Получение контента по тегам
- `GET /content/user/{user_id}/content/by-tags/{tag_id}` - Контент конкретного тега
- `GET /content/search-documents` - Поиск документов

### Чат и ИИ
- `POST /chat/simple` - Простой чат с YandexGPT
- `POST /chat/rag` - Чат с RAG системой
- `POST /web-search` - Веб-поиск с генеративным ответом
- `POST /chat/hybrid-rag` - Гибридный RAG + веб-поиск

### Администрирование
- `GET /departments` - Список отделов
- `GET /tags` - Список тегов
- `GET /users` - Список пользователей (только админы)

## Система прав доступа

### Иерархическая модель
Система использует иерархическую модель прав доступа:

1. **Администраторы** (`role_id = 1`) - полный доступ ко всем ресурсам
2. **Пользователи** - доступ только к контенту своего отдела и уровня доступа

### Принципы доступа
- `Content.access_level <= user.access_id` - пользователь может видеть контент своего уровня и ниже
- `Content.department_id == user.department_id` - пользователь видит только контент своего отдела
- Администраторы имеют доступ ко всему контенту

## Интеграция с Yandex Cloud

### Конфигурация
```python
# Переменные окружения
YANDEX_API_KEY=your_api_key
YANDEX_FOLDER_ID=your_folder_id
SEARCH_API_API_KEY=your_search_api_key
SEARCH_API_IAM_TOKEN=your_iam_token
```

### Сервисы
1. **YandexGPT** - генерация текста
2. **Embeddings** - создание векторных представлений
3. **Search API** - веб-поиск с генеративными ответами

### RAG система
1. Загрузка документов и создание эмбеддингов
2. Хранение в локальном JSON кэше
3. Поиск релевантных фрагментов
4. Генерация ответа на основе найденного контекста

## Функциональность чата

### Режимы работы
1. **Простой чат** - прямая генерация с YandexGPT
2. **RAG чат** - поиск в базе знаний + генерация
3. **Веб-поиск** - поиск в интернете + генерация
4. **Гибридный RAG** - комбинация RAG + веб-поиск

### Подрежимы
- **Обычная генерация** - стандартный режим
- **Поиск в интернете** - с использованием Yandex Search API

## Система файлов

### Загрузка
- Поддержка множественных форматов (PDF, DOC, DOCX, TXT)
- Автоматическое определение MIME-типов
- Валидация размера файлов

### Скачивание
- Защищенное скачивание с проверкой прав
- Публичные ссылки с временными токенами
- Правильная обработка кириллических имен файлов

## Безопасность

### Аутентификация
- JWT токены с временем жизни
- Хеширование паролей (bcrypt)
- Защита от брутфорс атак

### Авторизация
- Проверка прав на уровне эндпоинтов
- Валидация входных данных (Pydantic)
- Защита от SQL-инъекций (SQLAlchemy ORM)

### Файловая безопасность
- Проверка расширений файлов
- Изоляция файлов по отделам
- Временные токены для публичного доступа

## Мониторинг и логирование

### Логирование
- Структурированные логи FastAPI
- Логирование ошибок на фронтенде
- Отслеживание производительности

### Обработка ошибок
- Централизованная обработка исключений
- Пользовательские сообщения об ошибках
- Graceful degradation при сбоях сервисов

## Развертывание

### Docker Compose
```yaml
services:
  backend:
    build: ./server
    ports:
      - "${BACKEND_PORT:-8082}:8000"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/database
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
  
  frontend:
    build: ./vite-soft-ui-dashboard-main
    ports:
      - "${FRONTEND_PORT:-8081}:80"
  
  db:
    image: mysql:8.0
    ports:
      - "${DB_PORT:-3306}:3306"
```

### Переменные окружения
- `BACKEND_PORT` - порт бэкенда (по умолчанию 8082)
- `FRONTEND_PORT` - порт фронтенда (по умолчанию 8081)
- `DB_PORT` - порт базы данных (по умолчанию 3306)
- `YANDEX_API_KEY` - ключ API Yandex Cloud
- `YANDEX_FOLDER_ID` - ID папки в Yandex Cloud
- `SEARCH_API_API_KEY` - ключ для Yandex Search API
- `SEARCH_API_IAM_TOKEN` - IAM токен для Search API

## Производительность

### Оптимизации
- Кэширование эмбеддингов в JSON
- Асинхронная обработка запросов
- Ленивая загрузка документов
- Сжатие ответов

### Масштабируемость
- Микросервисная архитектура
- Контейнеризация с Docker
- Горизонтальное масштабирование готово
- Балансировка нагрузки через Nginx