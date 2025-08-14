# Rate Limiting добавлен

## ✅ Реализованные меры безопасности

### 1. Rate limiting на логин (5 попыток в минуту)
- **Файл**: `server/routes/user_routes.py`
- **Функция**: Ограничивает количество попыток входа в систему до 5 попыток в минуту
- **Статус**: ✅ Работает

### 2. Валидация файлов с проверкой MIME-типов и сканированием на вредоносный код
- **Файл**: `server/routes/content_routes.py`
- **Функции**:
  - Проверка размера файла (максимум 50MB)
  - Валидация MIME-типов с помощью `python-magic`
  - Сканирование содержимого на вредоносные паттерны
  - Проверка расширений файлов
  - Вычисление хеша файла для предотвращения дублирования
- **Статус**: ✅ Работает

### 3. Security headers в Nginx
- **Файл**: `nginx.conf`
- **Заголовки**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
- **Статус**: ✅ Работает

## 🔧 Добавленные изменения для Rate Limiting

### 1. Импорты в `server/app.py`
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
```

### 2. Инициализация в `server/app.py`
```python
# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 3. Импорты в `server/routes/user_routes.py`
```python
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
```

### 4. Инициализация в `server/routes/user_routes.py`
```python
# Rate limiter
limiter = Limiter(key_func=get_remote_address)
```

### 5. Применение к функции login
```python
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
```

### 6. Зависимость в `server/requirements.txt`
```
slowapi>=0.1.9
```

## 📊 Статус системы

| Сервис | Статус | Порт |
|--------|--------|------|
| Backend | ✅ Работает | 8000 |
| Frontend | ✅ Работает | 8083 |
| Nginx | ✅ Работает | 8081 |
| Database | ✅ Работает | 3307 |

## 🚀 Готово к использованию

Система полностью настроена и готова к работе с реализованными мерами безопасности:

1. **Rate limiting** защищает от брутфорс атак (5 попыток в минуту)
2. **Валидация файлов** предотвращает загрузку вредоносных файлов
3. **Security headers** защищают от XSS и clickjacking атак

## 🔗 Доступ к приложению

- **Основной URL**: http://localhost:8081
- **Frontend**: http://localhost:8083
- **Backend API**: http://localhost:8000

## 📝 Команды для управления

```bash
# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs backend

# Перезапуск
docker compose restart

# Остановка
docker compose down
```
