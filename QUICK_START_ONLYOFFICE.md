мс# Быстрый старт с OnlyOffice

## 🚀 Быстрая установка

### 1. Создайте файл .env
```bash
# Database settings
MYSQL_ROOT_PASSWORD=123123
MYSQL_DATABASE=db

# Debug mode
DEBUG=False

# OnlyOffice settings
ONLYOFFICE_JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# API settings
VITE_API_URL=http://localhost:8081/api
```

### 2. Запустите сервисы
```bash
docker-compose up -d
```

### 3. Проверьте работу
```bash
python test_onlyoffice.py
```

### 4. Откройте приложение
- Frontend: http://localhost:8080
- OnlyOffice: http://localhost:8082
- Backend API: http://localhost:8000

## 📋 Что было добавлено

### Backend (Python/FastAPI)
- ✅ `onlyoffice_service.py` - сервис для работы с OnlyOffice API
- ✅ Новые маршруты в `content_routes.py`:
  - `GET /content/onlyoffice/{content_id}` - конфигурация документа
  - `POST /content/save-onlyoffice/{content_id}` - сохранение изменений
  - `GET /content/onlyoffice-editor/{content_id}` - HTML страница редактора
- ✅ Зависимость PyJWT в `requirements.txt`

### Frontend (Vue.js)
- ✅ `OnlyOfficeViewer.vue` - компонент для отображения документов
- ✅ Обновленный `ContentTable.vue` с кнопками OnlyOffice
- ✅ Поддержка режимов: просмотр, редактирование, комментарии

### Docker
- ✅ OnlyOffice Document Server в `docker-compose.yml`
- ✅ Обновленная nginx конфигурация для проксирования
- ✅ Переменные окружения для OnlyOffice

## 🎯 Использование

1. **Загрузите документ** через веб-интерфейс
2. **Нажмите "Просмотр"** рядом с документом
3. **Выберите режим**:
   - 👁️ Просмотр (только чтение)
   - ✏️ Редактирование (полное редактирование)
   - 💬 Комментарии (добавление комментариев)

## 🔧 Поддерживаемые форматы

- **Документы**: .doc, .docx, .odt, .rtf, .txt
- **Таблицы**: .xls, .xlsx, .ods
- **Презентации**: .ppt, .pptx, .odp
- **PDF**: .pdf

## 🛠️ Устранение неполадок

### OnlyOffice не запускается
```bash
docker-compose logs onlyoffice
```

### Проверка портов
```bash
netstat -tulpn | grep 8082
```

### Перезапуск сервисов
```bash
docker-compose restart onlyoffice backend
```

## 📚 Дополнительная документация

Подробная документация: [README_ONLYOFFICE.md](README_ONLYOFFICE.md) 