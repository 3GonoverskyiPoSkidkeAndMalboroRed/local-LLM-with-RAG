# Интеграция OnlyOffice Document Server

Этот проект теперь поддерживает отображение и редактирование Word документов через OnlyOffice Document Server.

## Возможности

- **Просмотр документов**: Отображение Word, Excel, PowerPoint и PDF файлов в браузере
- **Редактирование**: Полнофункциональное редактирование документов
- **Комментарии**: Добавление комментариев к документам
- **Совместная работа**: Возможность совместного редактирования
- **Поддерживаемые форматы**: doc, docx, odt, rtf, txt, pdf, xls, xlsx, ods, ppt, pptx, odp

## Установка и настройка

### 1. Переменные окружения

Создайте файл `.env` в корневой директории проекта:

```env
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

### 2. Запуск сервисов

```bash
docker-compose up -d
```

Это запустит:
- Backend сервер (порт 8000)
- Frontend (порт 8080)
- Nginx прокси (порт 8081)
- OnlyOffice Document Server (порт 8082)
- MySQL база данных (порт 3307)
- Ollama (порт 11434)
- RabbitMQ (порт 5672, веб-интерфейс 15672)

### 3. Проверка работы

1. Откройте http://localhost:8080 в браузере
2. Войдите в систему
3. Загрузите Word документ
4. Нажмите кнопку "Просмотр" рядом с документом
5. Документ откроется в OnlyOffice редакторе

## Использование

### Просмотр документов

1. В таблице контента найдите нужный документ
2. Нажмите кнопку "Просмотр" (глаз)
3. Документ откроется в полноэкранном режиме

### Режимы работы

- **Просмотр**: Только просмотр документа без возможности редактирования
- **Редактирование**: Полное редактирование документа
- **Комментарии**: Добавление комментариев к документу

### Сохранение изменений

При редактировании документа изменения автоматически сохраняются на сервере.

## API Endpoints

### Получение конфигурации OnlyOffice
```
GET /content/onlyoffice/{content_id}
```

### Сохранение документа
```
POST /content/save-onlyoffice/{content_id}
```

### Открытие редактора
```
GET /content/onlyoffice-editor/{content_id}
```

## Безопасность

- Все запросы к OnlyOffice защищены JWT токенами
- Проверка прав доступа к документам
- Валидация типов файлов

## Поддерживаемые форматы

### Текстовые документы
- .doc, .docx (Microsoft Word)
- .odt (OpenDocument Text)
- .rtf (Rich Text Format)
- .txt (Plain Text)

### Электронные таблицы
- .xls, .xlsx (Microsoft Excel)
- .ods (OpenDocument Spreadsheet)

### Презентации
- .ppt, .pptx (Microsoft PowerPoint)
- .odp (OpenDocument Presentation)

### Другие форматы
- .pdf (Portable Document Format)

## Устранение неполадок

### OnlyOffice не запускается

1. Проверьте логи:
```bash
docker-compose logs onlyoffice
```

2. Убедитесь, что порт 8082 свободен:
```bash
netstat -tulpn | grep 8082
```

### Документы не открываются

1. Проверьте, что файл имеет поддерживаемый формат
2. Убедитесь, что файл не поврежден
3. Проверьте права доступа к файлу

### Ошибки JWT

1. Проверьте переменную `ONLYOFFICE_JWT_SECRET`
2. Убедитесь, что токен не истек
3. Проверьте настройки JWT в OnlyOffice

## Производительность

- OnlyOffice требует значительных ресурсов
- Рекомендуется минимум 4GB RAM для сервера
- Для больших документов может потребоваться больше времени загрузки

## Лицензия

OnlyOffice Document Server доступен в двух версиях:
- Community Edition (бесплатная)
- Enterprise Edition (платная)

Этот проект использует Community Edition. 