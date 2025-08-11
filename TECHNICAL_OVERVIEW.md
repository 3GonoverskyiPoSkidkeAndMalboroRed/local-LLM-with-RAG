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
```

### Компоненты системы

#### Frontend (Vue.js)
- **Фреймворк**: Vue.js 3 с Composition API
- **UI библиотека**: Soft UI Dashboard
- **Сборщик**: Vite
- **Стилизация**: Bootstrap 5 + Custom CSS
- **HTTP клиент**: Axios

#### Backend (FastAPI)
- **Фреймворк**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **Аутентификация**: JWT токены
- **Валидация**: Pydantic
- **Асинхронность**: asyncio

#### База данных (MySQL)
- **СУБД**: MySQL 8.0
- **Миграции**: Alembic
- **Пулинг соединений**: SQLAlchemy Engine

#### ИИ-сервисы
- **Провайдер**: Yandex Cloud ML SDK
- **Модели**: YandexGPT для генерации, text-search-doc для эмбеддингов
- **Векторная БД**: Локальное хранение в JSON формате

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

#### RAG система
```sql
-- Чанки документов для RAG
CREATE TABLE document_chunks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT NOT NULL,
    department_id INT NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INT NOT NULL,
    embedding_vector JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE
);

-- Сессии RAG
CREATE TABLE rag_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    department_id INT NOT NULL,
    is_initialized BOOLEAN DEFAULT FALSE,
    documents_count INT DEFAULT 0,
    chunks_count INT DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE
);
```

## API Endpoints

### Аутентификация
- `POST /auth/login` - Вход в систему
- `POST /auth/logout` - Выход из системы
- `GET /auth/me` - Информация о текущем пользователе

### Управление документами
- `GET /api/departments` - Список отделов
- `GET /api/access_levels` - Уровни доступа
- `POST /upload-files` - Загрузка файлов
- `GET /search-documents` - Поиск документов

### ИИ-ассистент
- `POST /api/yandex-ai/generate` - Генерация текста
- `POST /api/yandex-ai/chat` - Чат с ИИ

### RAG система
- `POST /api/yandex-rag/initialize` - Инициализация RAG
- `GET /api/yandex-rag/status/{department_id}` - Статус RAG
- `POST /api/yandex-rag/query` - RAG запрос
- `DELETE /api/yandex-rag/reset/{department_id}` - Сброс RAG

### Тестирование
- `GET /quizzes` - Список тестов
- `POST /quizzes/{quiz_id}/attempt` - Начать тест
- `POST /quizzes/submit` - Отправить ответы

## Безопасность

### Аутентификация и авторизация
- **Хеширование паролей**: bcrypt
- **Сессии**: JWT токены
- **Контроль доступа**: Role-based access control (RBAC)
- **Валидация**: Pydantic модели для всех входных данных

### Защита данных
- **SQL инъекции**: Защита через ORM (SQLAlchemy)
- **XSS**: Санитизация входных данных
- **CSRF**: CORS политики
- **Файловая безопасность**: Проверка типов и размеров файлов

## Производительность

### Оптимизации базы данных
- **Индексы**: На часто используемых полях (department_id, access_level)
- **Пулинг соединений**: SQLAlchemy connection pooling
- **Кеширование**: Redis для часто запрашиваемых данных (опционально)

### Оптимизации RAG
- **Векторные операции**: NumPy для быстрых вычислений
- **Батчинг**: Обработка эмбеддингов группами
- **Кеширование**: Локальное хранение векторных индексов

### Frontend оптимизации
- **Lazy loading**: Компоненты загружаются по требованию
- **Минификация**: Vite автоматически минифицирует код
- **Кеширование**: HTTP кеширование статических ресурсов

## Мониторинг и логирование

### Логирование
```python
# Настройка логирования
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Метрики
- **Время отклика API**: Middleware для измерения времени
- **Использование ресурсов**: CPU, память, дисковое пространство
- **Ошибки**: Количество и типы ошибок
- **Пользовательская активность**: Количество запросов, популярные функции

## Развертывание

### Docker контейнеры
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./server
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+mysqlconnector://root:password@db:3306/db_test
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
    
  frontend:
    build: ./vite-soft-ui-dashboard-main
    ports:
      - "3000:80"
    
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=db_test
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

### Переменные окружения
```bash
# Backend
DATABASE_URL=mysql+mysqlconnector://user:password@host:port/database
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_yandex_folder_id
JWT_SECRET_KEY=your_jwt_secret

# Frontend
VITE_API_URL=http://localhost:8000
```

## Масштабирование

### Горизонтальное масштабирование
- **Load Balancer**: Nginx для распределения нагрузки
- **Микросервисы**: Разделение на отдельные сервисы (Auth, Documents, AI)
- **Кеширование**: Redis для сессий и часто используемых данных

### Вертикальное масштабирование
- **CPU**: Увеличение количества ядер для обработки ИИ запросов
- **RAM**: Больше памяти для векторных операций
- **Storage**: SSD для быстрого доступа к документам

## Резервное копирование

### Стратегия бэкапов
```bash
# Ежедневный бэкап базы данных
mysqldump -u root -p db_test > backup_$(date +%Y%m%d).sql

# Бэкап файлов
tar -czf files_backup_$(date +%Y%m%d).tar.gz /app/files/

# Бэкап векторных индексов
tar -czf vector_backup_$(date +%Y%m%d).tar.gz /app/files/vector_db/
```

### Восстановление
```bash
# Восстановление БД
mysql -u root -p db_test < backup_20240101.sql

# Восстановление файлов
tar -xzf files_backup_20240101.tar.gz -C /
```

## Troubleshooting

### Частые проблемы

**Проблема**: Медленные RAG запросы
**Диагностика**: 
```python
import time
start_time = time.time()
# RAG операция
end_time = time.time()
print(f"RAG query took {end_time - start_time} seconds")
```

**Проблема**: Ошибки подключения к БД
**Диагностика**:
```python
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
try:
    connection = engine.connect()
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

**Проблема**: Ошибки Yandex API
**Диагностика**:
```python
import logging
logger = logging.getLogger(__name__)

try:
    response = await yandex_client.generate(prompt)
except Exception as e:
    logger.error(f"Yandex API error: {e}")
    # Fallback logic
```

## Контакты разработчиков

**Backend**: backend-team@company.com
**Frontend**: frontend-team@company.com
**DevOps**: devops-team@company.com
**Архитектор**: architect@company.com

---

*Документ обновлен: [дата]*
*Версия системы: 2.0*