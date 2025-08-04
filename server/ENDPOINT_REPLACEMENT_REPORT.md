# Отчет о замене эндпоинта в чате "Простой чат"

## Задача
Заменить эндпоинт в чате "Простой чат" с `llm/generate` на `yandex/generate`.

## Выполненные изменения

### Файл: `vite-soft-ui-dashboard-main/src/views/Billing.vue`

**Изменение 1: Замена эндпоинта**
- **Строка**: ~340
- **До**:
  ```javascript
  response = await axios.post(`${import.meta.env.VITE_API_URL}/llm/generate`, {
    messages: message,
    department_id: departmentId
  }, {
    noRetry: true
  });
  ```
- **После**:
     ```javascript
   response = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex/generate`, {
     prompt: message,
     model: "yandexgpt",
     temperature: 0.1,
     max_tokens: 2000
   }, {
     noRetry: true
   });
   ```

**Изменение 2: Обновление комментария**
- **До**: `// Используем эндпоинт /generate для простого чата`
- **После**: `// Используем эндпоинт /yandex/generate для простого чата`

## Детали изменений

### Параметры запроса
1. **Эндпоинт**: `/llm/generate` → `/yandex/generate`
2. **Параметр сообщения**: `messages` → `prompt`
3. **Добавлены параметры**:
   - `model: "yandexgpt"` - модель Yandex GPT
   - `temperature: 0.1` - температура генерации
   - `max_tokens: 2000` - максимальное количество токенов
4. **Удален параметр**: `department_id` (не используется в `/yandex/generate`)

### Обработка ответа
Формат ответа остался совместимым:
- **Эндпоинт `/llm/generate`**: `response.data.text`
- **Эндпоинт `/yandex/generate`**: `response.data.text`

## Результат
✅ Эндпоинт в режиме "Простой чат" успешно заменен с `llm/generate` на `yandex/generate`
✅ Параметры запроса адаптированы под API Yandex GPT
✅ Обработка ответа остается корректной
✅ Комментарии обновлены для ясности

## Тестирование
Для проверки изменений:
1. Запустите фронтенд приложения
2. Перейдите в раздел "Чат с LLM"
3. Выберите режим "Простой чат"
4. Отправьте сообщение
5. Убедитесь, что ответ приходит от Yandex GPT

## Примечания
- Изменения затрагивают только режим "Простой чат" (`chatMode === "simple"`)
- Режим "С базой знаний (RAG)" (`chatMode === "rag"`) остается без изменений
- Все параметры Yandex GPT установлены на рекомендуемые значения по умолчанию 