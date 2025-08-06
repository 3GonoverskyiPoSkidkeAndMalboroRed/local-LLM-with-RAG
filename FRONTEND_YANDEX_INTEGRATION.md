# Интеграция фронтенда с Yandex AI

## Изменения в простом чате

### Что изменилось:
- **Старый эндпоинт:** `/llm/generate` (Ollama) ❌
- **Новый эндпоинт:** `/api/yandex-ai/generate` (Yandex AI) ✅

### Файл: `vite-soft-ui-dashboard-main/src/views/Billing.vue`

#### Изменения в запросе:
```javascript
// БЫЛО:
response = await axios.post(`${import.meta.env.VITE_API_URL}/llm/generate`, {
  messages: message,
  department_id: departmentId
});

// СТАЛО:
response = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-ai/generate`, {
  prompt: message,
  model: "yandexgpt-lite",
  max_tokens: 1000,
  temperature: 0.6
});
```

#### Изменения в UI:
- Обновлен текст режима: "Простой чат" → "Простой чат (Yandex AI)"
- Улучшена обработка ошибок для Yandex AI

#### Структура ответа:
```javascript
{
  "success": true,
  "text": "Ответ от Yandex AI",
  "model": "yandexgpt-lite",
  "usage": {...},
  "sdk_used": true,
  "sdk_type": "yandex-cloud-ml-sdk"
}
```

### Режимы работы:
1. **RAG режим** - использует `/llm/query` (пока еще Ollama, требует отдельной миграции)
2. **Простой чат** - использует `/api/yandex-ai/generate` (Yandex AI) ✅

### Системный промпт:
Используется встроенный системный промпт профессионального ассистента из `server/routes/yandex_ai_routes.py`

### Тестирование:
- Переключите режим на "Простой чат (Yandex AI)"
- Отправьте сообщение
- Проверьте, что ответ приходит от Yandex AI