# Настройка Yandex GPT

Пошаговая инструкция по настройке и запуску Yandex GPT эндпоинтов.

## 🔑 Получение API ключей

### 1. Создание сервисного аккаунта

1. Перейдите в [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Выберите ваш каталог
3. Перейдите в **IAM → Сервисные аккаунты**
4. Нажмите **Создать сервисный аккаунт**
5. Заполните форму:
   - **Имя**: `yandex-gpt-service`
   - **Описание**: `Сервисный аккаунт для работы с Yandex GPT`
6. Нажмите **Создать**

### 2. Назначение ролей

1. В списке сервисных аккаунтов найдите созданный аккаунт
2. Нажмите на него для перехода к настройкам
3. Перейдите на вкладку **Роли**
4. Нажмите **Назначить роли**
5. Добавьте роль: **AI Language Models User** (`ai.languageModels.user`)
6. Нажмите **Сохранить**

### 3. Создание API ключа

1. В настройках сервисного аккаунта перейдите на вкладку **API-ключи**
2. Нажмите **Создать API-ключ**
3. Выберите тип **API-ключ**
4. Скопируйте созданный ключ (показывается только один раз!)

### 4. Получение Folder ID

1. В верхней части консоли Yandex Cloud найдите название каталога
2. Нажмите на него
3. В настройках каталога найдите **ID каталога**
4. Скопируйте ID (формат: `b1g2xxxxxxxxxxxxxxxxx`)

## ⚙️ Настройка переменных окружения

### 1. Создание файла .env

Создайте файл `.env` в папке `server/`:

```bash
# Обязательные переменные
YANDEX_API_KEY=AQVNxxxxxxxxxxxxxxxxx
YANDEX_FOLDER_ID=b1g2xxxxxxxxxxxxxxxxx

# Основные настройки
USE_YANDEX_CLOUD=true
YANDEX_LLM_MODEL=yandexgpt
YANDEX_TEMPERATURE=0.1
YANDEX_MAX_TOKENS=2000

# API настройки
YANDEX_BASE_URL=https://llm.api.cloud.yandex.net
YANDEX_TIMEOUT=30

# Retry и обработка ошибок
YANDEX_MAX_RETRIES=3
YANDEX_RETRY_DELAY=1.0
YANDEX_FALLBACK_TO_OLLAMA=true

# Кэширование
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_DIR=/app/files/cache
YANDEX_CACHE_TTL_HOURS=24

# Мониторинг
YANDEX_ENABLE_METRICS=true
YANDEX_METRICS_FILE=/app/files/yandex_metrics.json
```

### 2. Проверка переменных

```bash
# Проверка наличия переменных
echo $YANDEX_API_KEY
echo $YANDEX_FOLDER_ID

# Или через Python
python -c "import os; print('API Key:', os.getenv('YANDEX_API_KEY', 'НЕ НАЙДЕН')); print('Folder ID:', os.getenv('YANDEX_FOLDER_ID', 'НЕ НАЙДЕН'))"
```

## 🚀 Запуск сервера

### 1. Установка зависимостей

```bash
cd server
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
# Обычный запуск
python app.py

# С подробными логами
python app.py --log-level DEBUG

# На определенном порту
python app.py --port 8001
```

### 3. Проверка запуска

```bash
# Проверка доступности сервера
curl http://localhost:8000/docs

# Проверка Yandex GPT эндпоинтов
curl http://localhost:8000/api/yandex/config
```

## 🧪 Тестирование

### 1. Быстрый тест

```bash
# Запуск быстрого теста
python quick_test_yandex.py
```

### 2. Полный тест

```bash
# Запуск полного теста
python test_yandex_gpt.py
```

### 3. Ручное тестирование

```bash
# Проверка конфигурации
curl http://localhost:8000/api/yandex/config

# Проверка здоровья
curl http://localhost:8000/api/yandex/health

# Тест генерации
curl -X POST http://localhost:8000/api/yandex/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Привет! Как дела?",
    "temperature": 0.1,
    "max_tokens": 100
  }'
```

## 📊 Мониторинг

### 1. Проверка логов

```bash
# Просмотр логов в реальном времени
tail -f logs/app.log

# Поиск ошибок
grep -i error logs/app.log
```

### 2. Проверка метрик

```bash
# Получение метрик Yandex Cloud
curl http://localhost:8000/api/yandex/health

# Проверка файла метрик
cat /app/files/yandex_metrics.json
```

### 3. Проверка кэша

```bash
# Просмотр кэша
ls -la /app/files/cache/

# Очистка кэша
rm -rf /app/files/cache/*
```

## 🔧 Устранение неполадок

### Ошибка: "YANDEX_API_KEY environment variable is required"

**Причина:** Отсутствует или пустая переменная окружения.

**Решение:**
```bash
# Проверьте наличие переменной
echo $YANDEX_API_KEY

# Добавьте в .env файл
echo "YANDEX_API_KEY=your_key_here" >> .env

# Перезапустите сервер
```

### Ошибка: "Invalid API key"

**Причина:** Неверный или истекший API ключ.

**Решение:**
1. Проверьте правильность ключа в консоли Yandex Cloud
2. Создайте новый API ключ
3. Обновите переменную окружения

### Ошибка: "Folder not found"

**Причина:** Неверный Folder ID.

**Решение:**
1. Проверьте ID каталога в консоли Yandex Cloud
2. Убедитесь, что сервисный аккаунт имеет доступ к каталогу
3. Обновите переменную окружения

### Ошибка: "Rate limit exceeded"

**Причина:** Превышен лимит запросов.

**Решение:**
1. Увеличьте `YANDEX_MAX_RETRIES` в настройках
2. Добавьте задержки между запросами
3. Проверьте лимиты в консоли Yandex Cloud

### Ошибка: "Connection timeout"

**Причина:** Проблемы с сетью или Yandex Cloud API.

**Решение:**
1. Проверьте интернет-соединение
2. Увеличьте `YANDEX_TIMEOUT` в настройках
3. Проверьте статус Yandex Cloud API

## 📈 Оптимизация производительности

### 1. Настройка кэширования

```bash
# Включение кэширования
YANDEX_ENABLE_CACHING=true
YANDEX_CACHE_TTL_HOURS=24

# Настройка размера кэша
YANDEX_CACHE_MAX_SIZE=1000
```

### 2. Настройка retry

```bash
# Увеличение количества попыток
YANDEX_MAX_RETRIES=5
YANDEX_RETRY_DELAY=2.0

# Экспоненциальный backoff
YANDEX_EXPONENTIAL_BACKOFF=true
```

### 3. Настройка лимитов

```bash
# Ограничение токенов
YANDEX_MAX_TOKENS=1000

# Ограничение температуры
YANDEX_TEMPERATURE=0.1

# Таймаут запросов
YANDEX_TIMEOUT=60
```

## 🔒 Безопасность

### 1. Защита API ключей

```bash
# Не храните ключи в коде
# Используйте переменные окружения
# Ограничьте доступ к .env файлу
chmod 600 .env
```

### 2. Мониторинг использования

```bash
# Регулярно проверяйте логи
# Мониторьте метрики использования
# Настройте алерты на превышение лимитов
```

### 3. Ротация ключей

```bash
# Регулярно обновляйте API ключи
# Используйте разные ключи для разных окружений
# Настройте автоматическую ротацию
```

## 📚 Дополнительные ресурсы

- [Документация Yandex Cloud](https://cloud.yandex.ru/docs/foundation-models/)
- [API Reference](https://cloud.yandex.ru/docs/foundation-models/api-ref/)
- [Примеры интеграции](https://github.com/yandex-cloud/examples)
- [Настройка сервисного аккаунта](https://cloud.yandex.ru/docs/iam/operations/sa/create)
- [Лимиты и квоты](https://cloud.yandex.ru/docs/foundation-models/concepts/limits) 