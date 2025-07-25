# Просмотр Word документов

## Описание

Реализована функциональность для просмотра Word документов (.docx) в веб-интерфейсе без нарушения существующего интерфейса.

## Возможности

- ✅ Просмотр Word документов в модальном окне
- ✅ Конвертация .docx в читаемый HTML формат
- ✅ Сохранение форматирования текста
- ✅ Интеграция с существующей системой загрузки документов
- ✅ Поддержка RAG (Retrieval-Augmented Generation) для Word документов

## Техническая реализация

### Backend (Python/FastAPI)

#### Новые маршруты:
- `GET /content/view-word/{content_id}` - Просмотр Word документа в HTML формате
- `GET /content/word-content/{content_id}` - Получение содержимого Word документа в JSON формате

#### Обновленные компоненты:
- `document_loader.py` - Добавлена поддержка загрузки .docx файлов
- `content_routes.py` - Добавлены новые маршруты для работы с Word документами

#### Используемые библиотеки:
- `docx2txt` - Извлечение текста из Word документов
- `python-docx` - Работа с Word документами

### Frontend (Vue.js)

#### Новые компоненты:
- `WordViewer.vue` - Модальное окно для просмотра Word документов

#### Обновленные страницы:
- `LibraryPage.vue` - Интеграция WordViewer
- `TagContentPage.vue` - Поддержка просмотра Word документов
- `Dashboard.vue` - Поддержка просмотра Word документов

## Использование

### Для пользователей:

1. Загрузите Word документ (.docx) через интерфейс загрузки
2. Найдите документ в библиотеке или через поиск
3. Нажмите кнопку "Просмотреть" рядом с Word документом
4. Документ откроется в модальном окне с возможностью прокрутки
5. Используйте кнопку "Скачать" для сохранения оригинального файла

### Для разработчиков:

#### Добавление поддержки Word документов на новую страницу:

```vue
<template>
  <!-- Ваш контент -->
  
  <!-- Добавьте компонент WordViewer -->
  <WordViewer 
    ref="wordViewer"
    :documentId="selectedDocumentId"
    :documentTitle="selectedDocumentTitle"
    :documentDescription="selectedDocumentDescription"
  />
</template>

<script>
import WordViewer from '@/components/WordViewer.vue';

export default {
  components: {
    WordViewer
  },
  data() {
    return {
      selectedDocumentId: null,
      selectedDocumentTitle: '',
      selectedDocumentDescription: ''
    };
  },
  methods: {
    viewDocument(doc) {
      const fileExtension = doc.file_path.split('.').pop().toLowerCase();
      
      if (fileExtension === 'docx') {
        // Для Word документов используем модальное окно
        this.selectedDocumentId = doc.id;
        this.selectedDocumentTitle = doc.title;
        this.selectedDocumentDescription = doc.description;
        this.$nextTick(() => {
          this.$refs.wordViewer.show();
        });
      } else {
        // Для других файлов используем стандартный маршрут
        window.open(`${import.meta.env.VITE_API_URL}/content/view-file/${doc.id}`, '_blank');
      }
    }
  }
};
</script>
```

## API Endpoints

### Просмотр Word документа
```
GET /content/view-word/{content_id}
```
Возвращает HTML страницу с содержимым Word документа.

### Получение содержимого Word документа
```
GET /content/word-content/{content_id}
```
Возвращает JSON с метаданными и содержимым документа:
```json
{
  "title": "Название документа",
  "description": "Описание документа",
  "content": "Текст документа..."
}
```

## Ограничения

- Поддерживаются только файлы формата .docx (не .doc)
- Изображения и сложное форматирование могут отображаться некорректно
- Максимальный размер файла ограничен настройками сервера

## Устранение неполадок

### Документ не загружается:
1. Проверьте, что файл имеет расширение .docx
2. Убедитесь, что файл не поврежден
3. Проверьте логи сервера на наличие ошибок

### Текст отображается некорректно:
1. Убедитесь, что документ не содержит защищенного содержимого
2. Проверьте кодировку документа
3. Попробуйте сохранить документ в более новой версии Word

## Планы развития

- [ ] Поддержка старых форматов .doc
- [ ] Сохранение форматирования (жирный, курсив, списки)
- [ ] Поддержка изображений в документах
- [ ] Экспорт в PDF
- [ ] Редактирование документов в браузере 