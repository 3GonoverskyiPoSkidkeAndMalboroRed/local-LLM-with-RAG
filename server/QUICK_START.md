# 🚀 RAG система с Yandex Cloud - Быстрый запуск

## 🔥 СИСТЕМА ОБНОВЛЕНА - ТОЛЬКО YANDEX CLOUD!

### Ollama полностью отключен
- ❌ **Ollama fallback удален** - система работает только через Yandex Cloud API
- ✅ **RAG полностью на Yandex** - эмбеддинги и генерация только через Yandex
- ✅ **Единообразное качество** - все через одну экосистему
- ✅ **Улучшенная производительность** - нет переключений между провайдерами
- ✅ **Фронтенд полностью связан** - Vue.js использует Yandex RAG API

## 📋 Предварительные требования
1. **Python 3.8+**
2. **MySQL** (для базы данных)
3. **Yandex Cloud API ключ** (уже настроен)

## 🔧 Установка и настройка

### 1. Установка зависимостей
```bash
cd server
pip install -r requirements.txt
```

### 2. Настройка базы данных MySQL
```bash
# Создайте базу данных
mysql -u root -p
CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 3. Конфигурация (уже настроена)
Файл `.env` содержит:
- ✅ **API Key**: YOUR_YANDEX_API_KEY_HERE
- ✅ **Folder ID**: YOUR_FOLDER_ID_HERE
- ✅ **USE_YANDEX_CLOUD**: true
- ✅ **YANDEX_FALLBACK_TO_OLLAMA**: false (отключен!)

### 4. Доступные модели (только Yandex Cloud)
- **LLM модели**: `yandexgpt`, `yandexgpt-lite`
- **Embedding модели**: `text-search-doc`, `text-search-query`

## 🧪 Тестирование

### Тест только Yandex Cloud (рекомендуется)
```bash
python test_yandex_only.py
```

### Обычный тест конфигурации
```bash
python test_config.py
```

## 🚀 Запуск системы

### Автоматический запуск
```bash
python start_project.py
```

### Ручной запуск
```bash
# Инициализация базы данных
python init_db.py

# Запуск сервера
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 Использование RAG API

### 1. Инициализация отдела с документами
```bash
curl -X POST "http://localhost:8000/llm/initialize" \
     -H "Content-Type: application/json" \
     -d '{
       "model_name": "yandexgpt",
       "embedding_model_name": "text-search-doc",
       "documents_path": "files/department_1",
       "department_id": "1"
     }'
```

### 2. RAG запрос (используется фронтендом)
```bash
curl -X POST "http://localhost:8000/llm/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Что говорится в документах о машинном обучении?",
       "department_id": "1"
     }'
```

### 3. Получение результата
```bash
curl "http://localhost:8000/llm/query/{task_id}"
```

## 🎯 Связь с фронтендом

Фронтенд (Vue.js) полностью интегрирован с Yandex RAG API:
- **Файл**: `vite-soft-ui-dashboard-main/src/views/Billing.vue`
- **Режим RAG**: `chatMode === "rag"`
- **API вызовы**:
  - `POST /llm/query` - создание задачи
  - `GET /llm/query/{task_id}` - получение результата
- **Отображение**: Ответы с источниками и релевантными фрагментами

## 📊 Что возвращает RAG API

```json
{
  "task_id": "uuid",
  "status": "completed",
  "answer": "Ответ YandexGPT на основе документов",
  "chunks": ["Релевантный фрагмент 1", "Фрагмент 2"],
  "files": ["document1.pdf", "document2.txt"],
  "sources": [
    {
      "file_name": "document1.pdf",
      "file_path": "files/department_1/document1.pdf",
      "chunk_content": "Релевантный текст...",
      "chunk_id": "chunk_1",
      "page_number": 5,
      "similarity_score": 0.95
    }
  ]
}
```

## 🛠️ Полезные команды

```bash
# Проверка доступных моделей
curl "http://localhost:8000/llm/models"

# Проверка состояния отдела
curl "http://localhost:8000/llm/debug/department-state/1"

# Метрики Yandex Cloud
curl "http://localhost:8000/llm/metrics"
```

## 🚨 Устранение проблем

### Ошибка "Модель недоступна"
Система теперь принимает только Yandex Cloud модели:
- ✅ `yandexgpt`, `yandexgpt-lite`
- ✅ `text-search-doc`, `text-search-query`
- ❌ `gemma3`, `nomic-embed-text` (Ollama модели отклоняются)

### Проверка API ключа
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('YANDEX_API_KEY', 'НЕ НАЙДЕН')[:10] + '...')
print('Folder ID:', os.getenv('YANDEX_FOLDER_ID', 'НЕ НАЙДЕН'))
print('Yandex Cloud:', os.getenv('USE_YANDEX_CLOUD', 'НЕ НАЙДЕН'))
print('Fallback отключен:', os.getenv('YANDEX_FALLBACK_TO_OLLAMA', 'НЕ НАЙДЕН'))
"
```

## 🎉 Готово!

Ваша RAG система работает исключительно через Yandex Cloud API:
- 🔥 **Эмбеддинги**: Yandex Cloud `text-search-doc`
- 🔥 **Генерация**: YandexGPT
- 🔥 **Фронтенд**: Полностью интегрирован
- 🔥 **Качество**: Единообразное через Yandex экосистему

**Система доступна**: http://localhost:8000
**API документация**: http://localhost:8000/docs