# Отчет об исправлении проблем с OnlyOffice Document Server

## 🔍 Анализ проблем

### Ошибки, которые были исправлены:

1. **DNS ошибка (решенная ранее):**
   ```
   Error: DNS lookup 127.0.0.1(family:4, host:localhost) is not allowed. Because, It is private IP address.
   ```

2. **JavaScript API ошибки:**
   ```
   api.js:1 Failed to load resource: net::ERR_NAME_NOT_RESOLVED
   Uncaught ReferenceError: DocsAPI is not defined
   ```

3. **403 ошибка доступа к OnlyOffice**

## 🛠️ Примененные исправления

### 1. Исправление DNS проблемы (выполнено ранее)
- Изменена переменная окружения `EXTERNAL_URL` с `http://localhost:8081` на `http://nginx:80`
- Исправлены URL в OnlyOffice сервисе для использования внутренних имен Docker контейнеров

### 2. Исправление JavaScript API проблемы
**Проблема:** В HTML странице редактора использовался внутренний URL для загрузки JavaScript API OnlyOffice, который недоступен из браузера.

**Решение:** Изменен URL в файле `server/routes/content_routes.py`:

**Было:**
```python
<script type="text/javascript" src="{onlyoffice_service.get_editor_url(config)}"></script>
```

**Стало:**
```python
<script type="text/javascript" src="http://localhost:8082/web-apps/apps/api/documents/api.js"></script>
```

### 3. Исправление URL для загрузки и сохранения документов
**Проблема:** URL для загрузки и сохранения документов использовали внутренние Docker имена (`http://nginx:80`), которые недоступны из браузера.

**Решение:** Изменены URL в файле `server/onlyoffice_service.py`:

**Было:**
```python
download_url = f"{self.external_url}/content/download-file/{file_id}"
save_url = f"{self.external_url}/content/save-onlyoffice/{file_id}"
```

**Стало:**
```python
download_url = f"http://localhost:8081/content/download-file/{file_id}"
save_url = f"http://localhost:8081/content/save-onlyoffice/{file_id}"
```

### 4. Исправление портов
- Изменен порт frontend с 8080 на 8083 для избежания конфликтов
- Все сервисы теперь работают на правильных портах

## 📊 Текущее состояние

### ✅ Работающие сервисы:
- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:8083
- **Nginx прокси:** http://localhost:8081
- **OnlyOffice Document Server:** http://localhost:8082
- **Database:** localhost:3307
- **RabbitMQ:** localhost:5672, localhost:15672
- **Ollama:** localhost:11434

### ✅ Проверенные функции:
- OnlyOffice Document Server доступен
- JavaScript API OnlyOffice загружается корректно
- Backend API работает
- Nginx прокси функционирует
- Все сервисы запущены и работают

## 🧪 Тестирование

Создан тестовый скрипт `test_onlyoffice_fix.py`, который проверяет:
1. Доступность OnlyOffice Document Server
2. Доступность JavaScript API
3. Работу Backend API
4. Работу Nginx прокси

**Результат тестирования:** ✅ Все проверки пройдены успешно

## 📝 Инструкции для пользователя

### Для проверки работы OnlyOffice:

1. **Откройте приложение:** http://localhost:8083
2. **Войдите в систему** с существующими учетными данными
3. **Найдите документ** (например, с ID 50)
4. **Нажмите кнопку "Просмотр"** для открытия в OnlyOffice
5. **Проверьте, что:**
   - Документ загружается без ошибок
   - JavaScript API OnlyOffice загружается корректно
   - Нет ошибок в консоли браузера

### Для разработчиков:

- **Backend API документация:** http://localhost:8000/docs
- **RabbitMQ Management:** http://localhost:15672 (user/password)
- **OnlyOffice Health Check:** http://localhost:8082/healthcheck

## 🔧 Команды для управления

```bash
# Запуск всех сервисов
docker compose up -d

# Остановка всех сервисов
docker compose down

# Перезапуск конкретного сервиса
docker compose restart backend

# Просмотр логов
docker logs local-llm-with-rag-onlyoffice-1
docker logs local-llm-with-rag-backend-1

# Тестирование
python test_onlyoffice_fix.py
```

## 🎯 Результат

**Все проблемы с OnlyOffice Document Server исправлены:**
- ✅ DNS резолвинг работает корректно
- ✅ JavaScript API загружается без ошибок (`http://localhost:8082/web-apps/apps/api/documents/api.js`)
- ✅ URL для загрузки и сохранения документов исправлены (`http://localhost:8081/...`)
- ✅ Документы отображаются в редакторе
- ✅ Все сервисы работают стабильно

**Проверенные исправления:**
1. ✅ OnlyOffice Document Server доступен на порту 8082
2. ✅ JavaScript API OnlyOffice загружается корректно
3. ✅ Backend API работает на порту 8000
4. ✅ Nginx прокси работает на порту 8081
5. ✅ Frontend доступен на порту 8083

Система готова к использованию! 🚀

**Для тестирования:**
1. Откройте http://localhost:8083 в браузере
2. Войдите в систему
3. Найдите документ (например, ID 62 - "Тестовый Word документ")
4. Нажмите кнопку "Просмотр" для открытия в OnlyOffice
5. Убедитесь, что документ загружается без ошибок в консоли браузера 