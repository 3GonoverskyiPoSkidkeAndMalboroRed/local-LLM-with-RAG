# Исправление проблем с API на фронтенде

## Проблема
Фронтенд не мог подключиться к API backend'а из-за неправильных URL адресов.

## Что было исправлено:

### 1. Обновлены переменные окружения
**Файл:** `vite-soft-ui-dashboard-main/.env.local`
```bash
# БЫЛО:
VITE_API_URL=http://192.168.81.74:8000

# СТАЛО:
VITE_API_URL=http://localhost:8081/api
```

**Файл:** `vite-soft-ui-dashboard-main/.env`
```bash
# БЫЛО:
VITE_API_URL=http://192.168.81.74:8000

# СТАЛО:
VITE_API_URL=http://localhost:8081/api
```

### 2. Пересобран фронтенд контейнер
```bash
docker-compose build frontend
docker-compose up -d frontend
```

## Текущая архитектура:

### Порты:
- **Backend:** `localhost:8000` (прямой доступ)
- **Frontend:** `localhost:8083` (через nginx)
- **Nginx:** `localhost:8081` (проксирует API)

### API маршруты:
- **Прямой доступ к backend:** `http://localhost:8000/departments`
- **Через nginx:** `http://localhost:8081/api/departments`
- **Фронтенд использует:** `http://localhost:8081/api/` + эндпоинт

### Nginx конфигурация:
```nginx
location /api/ {
    proxy_pass http://backend_servers/;
    # Проксирует /api/departments -> backend:8000/departments
}
```

## Проверка работоспособности:

### Backend эндпоинты (работают):
- ✅ `http://localhost:8000/departments`
- ✅ `http://localhost:8000/user/login`
- ✅ `http://localhost:8000/api/departments`

### Nginx проксирование (работает):
- ✅ `http://localhost:8081/api/departments`
- ✅ `http://localhost:8081/api/user/login`
- ✅ `http://localhost:8081/api/api/yandex-ai/generate`

### Фронтенд:
- ✅ `http://localhost:8083` - доступен
- ✅ Переменные окружения обновлены
- ✅ Контейнер пересобран с новыми настройками

## Результат:
Фронтенд теперь должен корректно подключаться к API через nginx на `localhost:8081/api/`