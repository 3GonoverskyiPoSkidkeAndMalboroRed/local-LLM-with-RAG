# Rate Limiting Guide

## Обзор

Rate limiting защищает приложение от злоупотреблений и DDoS атак, ограничивая количество запросов, которые может сделать клиент за определенный период времени.

## Настройки Rate Limiting

### Глобальные лимиты

- **Глобальный лимит**: 100 запросов в минуту для всех эндпоинтов
- **DDoS защита**: 200 запросов в минуту (всплеск), 1000 запросов в час (устойчивый)

### Лимиты по эндпоинтам

| Эндпоинт | Лимит | Описание |
|----------|-------|----------|
| `/user/login` | 10/минуту | Попытки входа |
| `/user/register` | 5/минуту | Регистрация пользователей |
| `/content/upload-content` | 20/минуту | Загрузка контента |
| `/content/upload-files` | 10/минуту | Массовая загрузка файлов |
| `/feedback/create` | 30/минуту | Создание обратной связи |
| `/yandex-ai/generate` | 60/минуту | Генерация текста AI |
| `/yandex-rag/query` | 30/минуту | RAG запросы |

### Лимиты по ролям пользователей

- **Админы**: 2x лимит (в 2 раза больше запросов)
- **Обычные пользователи**: 1x лимит (стандартный)
- **Гости**: 0.5x лимит (в 2 раза меньше запросов)

## Реализация

### 1. Установка зависимостей

```bash
pip install slowapi
```

### 2. Инициализация в app.py

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Инициализация rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 3. Применение к эндпоинтам

```python
@router.post("/login")
@limiter.limit("10/minute")
async def login(user_data: UserLogin, db: Session = Depends(get_db), request: Request = Depends()):
    # Логика эндпоинта
    pass
```

### 4. Глобальный middleware

```python
@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    try:
        client_ip = get_remote_address(request)
        await limiter.check_request_limit(request, "100/minute", client_ip)
        response = await call_next(request)
        return response
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={"detail": "Слишком много запросов. Попробуйте позже."}
        )
```

## Мониторинг

### Эндпоинт статуса

```
GET /rate-limit-status
```

Возвращает:
```json
{
    "client_ip": "127.0.0.1",
    "global_limit": "100/minute",
    "endpoint_limits": {
        "login": "10/minute",
        "register": "5/minute",
        // ...
    },
    "message": "Rate limiting активен"
}
```

### Заголовки ответа

При превышении лимита возвращается:
- **Status Code**: 429 (Too Many Requests)
- **Retry-After**: Время ожидания в секундах
- **X-RateLimit-Limit**: Максимальное количество запросов
- **X-RateLimit-Remaining**: Оставшееся количество запросов
- **X-RateLimit-Reset**: Время сброса лимита

## Тестирование

### Запуск тестов

```bash
python test_rate_limiting.py
```

### Ручное тестирование

```bash
# Тест логина (должен сработать после 10 запросов)
for i in {1..12}; do
    curl -X POST http://localhost:8000/user/login \
        -H "Content-Type: application/json" \
        -d '{"login":"test","password":"test"}'
    echo "Запрос $i"
done
```

## Настройка

### Изменение лимитов

Отредактируйте файл `rate_limiting_config.py`:

```python
RATE_LIMITS = {
    "login": "15/minute",  # Увеличить до 15 запросов в минуту
    "register": "10/minute",  # Увеличить до 10 запросов в минуту
    # ...
}
```

### Добавление нового эндпоинта

```python
@router.post("/new-endpoint")
@limiter.limit("50/minute")  # Установить лимит
async def new_endpoint(request: Request = Depends()):
    # Логика эндпоинта
    pass
```

## Лучшие практики

1. **Градуированные лимиты**: Более строгие лимиты для критических операций
2. **Мониторинг**: Регулярно проверяйте логи превышения лимитов
3. **Уведомления**: Настройте алерты при превышении лимитов
4. **Документация**: Информируйте пользователей о лимитах
5. **Тестирование**: Регулярно тестируйте rate limiting

## Устранение неполадок

### Проблема: Rate limiting не работает

1. Проверьте, что slowapi установлен
2. Убедитесь, что middleware добавлен в app.py
3. Проверьте логи на ошибки

### Проблема: Слишком строгие лимиты

1. Увеличьте лимиты в конфигурации
2. Добавьте исключения для определенных IP
3. Настройте разные лимиты для разных пользователей

### Проблема: Ложные срабатывания

1. Проверьте настройки прокси/nginx
2. Убедитесь, что IP адреса определяются корректно
3. Настройте whitelist для доверенных IP

## Безопасность

- Rate limiting защищает от:
  - Brute force атак
  - DDoS атак
  - Злоупотребления API
  - Исчерпания ресурсов

- Дополнительные меры:
  - IP whitelist для критических операций
  - Логирование подозрительной активности
  - Автоматические блокировки при превышении лимитов

