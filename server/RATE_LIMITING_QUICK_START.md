# Rate Limiting - Быстрый старт

## Что добавлено

✅ **Rate limiting** для защиты от злоупотреблений и DDoS атак

## Установка

```bash
pip install slowapi
```

## Настройки

### Лимиты по эндпоинтам:
- **Логин**: 10 запросов в минуту
- **Регистрация**: 5 запросов в минуту  
- **Загрузка контента**: 20 запросов в минуту
- **Массовая загрузка**: 10 запросов в минуту
- **Feedback**: 30 запросов в минуту
- **Yandex AI**: 60 запросов в минуту
- **Yandex RAG**: 30 запросов в минуту
- **Глобальный**: 100 запросов в минуту

## Тестирование

### Запуск тестов:
```bash
python test_simple_rate_limit.py
```

### Ручное тестирование:
```bash
# Тест логина (должен сработать после 10 запросов)
for i in {1..12}; do
    curl -X POST http://localhost:8000/user/login \
        -H "Content-Type: application/json" \
        -d '{"login":"test","password":"test"}'
    echo "Запрос $i"
done
```

## Мониторинг

### Проверка статуса:
```bash
curl http://localhost:8000/rate-limit-status
```

### При превышении лимита:
- **Status Code**: 429 (Too Many Requests)
- **Ответ**: `{"detail": "Слишком много запросов. Попробуйте позже."}`

## Файлы

- `rate_limiter.py` - Глобальный rate limiter
- `rate_limiting_config.py` - Конфигурация лимитов
- `test_simple_rate_limit.py` - Тесты
- `RATE_LIMITING_GUIDE.md` - Полная документация

## Настройка лимитов

Отредактируйте `rate_limiting_config.py`:

```python
RATE_LIMITS = {
    "login": "15/minute",  # Увеличить до 15
    "register": "10/minute",  # Увеличить до 10
    # ...
}
```

## Добавление к новому эндпоинту

```python
from rate_limiter import get_limiter

limiter = get_limiter()

@router.post("/new-endpoint")
@limiter.limit("50/minute")
async def new_endpoint(request: Request = Depends()):
    # Логика эндпоинта
    pass
```

## Безопасность

Rate limiting защищает от:
- ✅ Brute force атак
- ✅ DDoS атак  
- ✅ Злоупотребления API
- ✅ Исчерпания ресурсов

