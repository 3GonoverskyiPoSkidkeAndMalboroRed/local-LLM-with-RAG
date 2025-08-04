# Yandex GPT Эндпоинты

Документация по использованию эндпоинтов для работы с Yandex GPT через REST API.

## 🚀 Быстрый старт

### 1. Настройка переменных окружения

Создайте файл `.env` в папке `server/` со следующими переменными:

```bash
# Обязательные переменные
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=your_folder_id_here

# Основные настройки
USE_YANDEX_CLOUD=true
YANDEX_LLM_MODEL=yandexgpt
YANDEX_TEMPERATURE=0.1
YANDEX_MAX_TOKENS=2000
```

### 2. Запуск сервера

```bash
cd server
python app.py
```

### 3. Тестирование

```bash
python test_yandex_gpt.py
```

## 📋 Доступные эндпоинты

### Базовый URL
```
http://localhost:8000/api/yandex
```

### 1. Проверка конфигурации
**GET** `/api/yandex/config`

Проверяет настройки Yandex Cloud и возвращает информацию о конфигурации.

**Ответ:**
```json
{
  "is_configured": true,
  "model": "yandexgpt",
  "folder_id": "b1g2xxxxxxxxxxxxxxxxx",
  "base_url": "https://llm.api.cloud.yandex.net",
  "max_tokens": 2000,
  "temperature": 0.1
}
```

### 2. Проверка здоровья API
**GET** `/api/yandex/health`

Проверяет доступность Yandex Cloud API.

**Ответ:**
```json
{
  "status": "healthy",
  "message": "Yandex Cloud API доступен",
  "configured": true,
  "test_response_length": 15
}
```

### 3. Список моделей
**GET** `/api/yandex/models`

Возвращает список доступных моделей Yandex GPT.

**Ответ:**
```json
{
  "models": [
    {
      "id": "yandexgpt",
      "name": "Yandex GPT",
      "description": "Основная модель Yandex GPT для генерации текста"
    },
    {
      "id": "yandexgpt-lite",
      "name": "Yandex GPT Lite",
      "description": "Облегченная версия Yandex GPT"
    }
  ],
  "default_model": "yandexgpt"
}
```

### 4. Генерация текста
**POST** `/api/yandex/generate`

Генерирует текст на основе промпта.

**Запрос:**
```json
{
  "prompt": "Расскажи кратко о преимуществах искусственного интеллекта",
  "model": "yandexgpt",
  "temperature": 0.1,
  "max_tokens": 500,
  "stream": false
}
```

**Ответ:**
```json
{
  "text": "Искусственный интеллект (ИИ) предоставляет множество преимуществ...",
  "model": "yandexgpt",
  "tokens_used": 150,
  "response_time": 2.34
}
```

### 5. Чат
**POST** `/api/yandex/chat`

Ведет диалог с моделью на основе истории сообщений.

**Запрос:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Ты полезный ассистент."
    },
    {
      "role": "user",
      "content": "Привет! Как дела?"
    }
  ],
  "model": "yandexgpt",
  "temperature": 0.1,
  "max_tokens": 300,
  "stream": false
}
```

**Ответ:**
```json
{
  "message": "Привет! У меня все хорошо, спасибо что спросили. Как я могу вам помочь?",
  "model": "yandexgpt",
  "tokens_used": 45,
  "response_time": 1.23
}
```

### 6. Потоковая генерация
**POST** `/api/yandex/generate/stream`

Генерирует текст в потоковом режиме (Server-Sent Events).

**Запрос:**
```json
{
  "prompt": "Напиши короткое стихотворение о программировании",
  "model": "yandexgpt",
  "temperature": 0.7,
  "max_tokens": 200,
  "stream": true
}
```

**Ответ (поток):**
```
data: В мире кода и логики
data: Где алгоритмы как стихи
data: Программист творит чудеса
data: Создавая новые миры
data: [DONE]
```

## 🔧 Параметры запросов

### Общие параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `model` | string | `yandexgpt` | Модель Yandex GPT |
| `temperature` | float | `0.1` | Температура генерации (0.0-1.0) |
| `max_tokens` | int | `2000` | Максимальное количество токенов (1-8000) |
| `stream` | boolean | `false` | Потоковая генерация |

### Параметры чата

| Параметр | Тип | Описание |
|----------|-----|----------|
| `messages` | array | Массив сообщений с ролями и содержимым |
| `role` | string | Роль: `system`, `user`, `assistant` |
| `content` | string | Содержимое сообщения |

## 📝 Примеры использования

### cURL

#### Генерация текста
```bash
curl -X POST "http://localhost:8000/api/yandex/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Объясни квантовую физику простыми словами",
    "temperature": 0.1,
    "max_tokens": 300
  }'
```

#### Чат
```bash
curl -X POST "http://localhost:8000/api/yandex/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Привет!"}
    ],
    "temperature": 0.1
  }'
```

### Python

#### Генерация текста
```python
import requests

response = requests.post(
    "http://localhost:8000/api/yandex/generate",
    json={
        "prompt": "Напиши краткое эссе о будущем технологий",
        "temperature": 0.1,
        "max_tokens": 500
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Сгенерированный текст: {result['text']}")
    print(f"Время ответа: {result['response_time']:.2f} сек")
```

#### Потоковая генерация
```python
import requests

response = requests.post(
    "http://localhost:8000/api/yandex/generate/stream",
    json={
        "prompt": "Напиши стихотворение о весне",
        "temperature": 0.7,
        "max_tokens": 200,
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = line_str[6:]
            if data == '[DONE]':
                break
            print(data, end='', flush=True)
```

### JavaScript

#### Генерация текста
```javascript
const response = await fetch('http://localhost:8000/api/yandex/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: 'Расскажи о космосе',
    temperature: 0.1,
    max_tokens: 300
  })
});

const result = await response.json();
console.log('Сгенерированный текст:', result.text);
```

#### Потоковая генерация
```javascript
const response = await fetch('http://localhost:8000/api/yandex/generate/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: 'Напиши рассказ',
    temperature: 0.7,
    max_tokens: 500,
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') return;
      console.log(data);
    }
  }
}
```

## ⚠️ Обработка ошибок

### Коды ошибок

| Код | Описание |
|-----|----------|
| `400` | Неверный запрос (некорректные параметры) |
| `500` | Ошибка сервера или Yandex Cloud API |
| `503` | Сервис недоступен |

### Примеры ошибок

```json
{
  "detail": "Yandex Cloud не настроен. Проверьте переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID"
}
```

```json
{
  "detail": "Ошибка при генерации текста: Invalid API key"
}
```

## 🔍 Мониторинг и отладка

### Проверка логов
```bash
# Запуск с подробными логами
python app.py --log-level DEBUG
```

### Тестирование подключения
```bash
# Запуск тестового скрипта
python test_yandex_gpt.py
```

### Проверка метрик
```bash
# Получение метрик Yandex Cloud
curl http://localhost:8000/api/yandex/health
```

## 🚀 Производительность

### Рекомендации

1. **Температура**: Используйте низкую температуру (0.1-0.3) для детерминистичных ответов
2. **Максимальные токены**: Устанавливайте разумные лимиты для экономии ресурсов
3. **Кэширование**: Включите кэширование для повторяющихся запросов
4. **Потоковая генерация**: Используйте для длинных ответов для лучшего UX

### Лимиты

- **Максимальные токены**: 8000
- **Температура**: 0.0 - 1.0
- **Таймаут запроса**: 30 секунд
- **Лимит запросов**: 60 в минуту

## 📚 Дополнительные ресурсы

- [Документация Yandex Cloud](https://cloud.yandex.ru/docs/foundation-models/)
- [Примеры интеграции](https://github.com/yandex-cloud/examples)
- [Настройка сервисного аккаунта](https://cloud.yandex.ru/docs/iam/operations/sa/create) 