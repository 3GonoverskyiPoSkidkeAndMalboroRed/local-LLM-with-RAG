# Ollama отключена

## Что было закомментировано:

### Docker Compose
- Сервис `ollama` в `docker-compose.yml`
- Volume `ollama_data`
- Переменная окружения `OLLAMA_HOST` в backend сервисе

### Python код
- Импорты `langchain_ollama` в файлах:
  - `server/app.py`
  - `server/llm_state_manager.py`
  - `server/document_loader.py`
  - `server/routes/llm_routes.py`

### Эндпоинты
- `/llm/generate` в `server/routes/llm_routes.py`
- Модели данных `GenerateRequest` и `GenerateResponse`

### Функции
- Инициализация `ChatOllama` и `OllamaEmbeddings` в `llm_state_manager.py`
- Основная логика `load_documents_into_database` в `document_loader.py`

### Конфигурация
- Переменные окружения Ollama в `server/.env`

## Активные сервисы:
- ✅ Yandex Cloud AI через `/api/yandex-ai/` эндпоинты
- ✅ База данных MySQL
- ✅ Frontend и Nginx

## Для восстановления Ollama:
1. Раскомментировать все закомментированные блоки
2. Запустить `docker-compose up ollama -d`
3. Установить модели: `docker exec -it local-llm-with-rag-ollama-1 ollama pull gemma3`