<template>
  <div class="source-display mt-3">
    <div class="card">
      <div class="card-header pb-0">
        <h6 class="mb-0">
          <i class="fas fa-book-open me-2"></i>
          Источники информации
          <span v-if="uniqueSources.length > 0" class="badge bg-primary ms-2">
            {{ uniqueSources.length }}
          </span>
          <small class="text-muted ms-2">
            <i class="fas fa-star text-success"></i> Первый источник — основной
          </small>
        </h6>
      </div>
      <div class="card-body">
        <div v-if="uniqueSources.length === 0" class="text-muted">
          <i class="fas fa-info-circle me-2"></i>
          Источники не найдены или не найдено релевантной информации
        </div>
        
        <div v-else class="sources-list">
          <div 
            v-for="(source, index) in uniqueSources" 
            :key="source.chunk_id"
            class="source-item mb-3 p-3 border rounded"
            :class="{ 'border-primary': selectedSource === source.chunk_id }"
          >
            <div class="d-flex justify-content-between align-items-start">
              <div class="flex-grow-1">
                <div class="d-flex align-items-center mb-2">
                  <i class="fas fa-file-alt me-2 text-primary"></i>
                  <strong class="text-primary">{{ source.file_name }}</strong>
                  <span v-if="index === 0" class="badge bg-success ms-2" title="Основной источник информации">
                    <i class="fas fa-star"></i> Основной
                  </span>
                  <span v-if="source.page_number" class="badge bg-secondary ms-2">
                    Страница {{ source.page_number }}
                  </span>
                  <span v-if="source.similarity_score" class="badge bg-info ms-2">
                    Релевантность: {{ (source.similarity_score * 100).toFixed(1) }}%
                  </span>
                </div>
                
                <div class="source-preview">
                  <p class="text-muted mb-2">
                    {{ getPreviewText(source.chunk_content) }}
                  </p>
                  
                  <div class="btn-group" role="group">
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="toggleSourceDetails(source.chunk_id)"
                    >
                      <i :class="selectedSource === source.chunk_id ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                      {{ selectedSource === source.chunk_id ? 'Скрыть' : 'Показать' }} полный текст
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-info"
                      @click="openSourceModal(source, index === 0)"
                      title="Открыть в модальном окне"
                    >
                      <i class="fas fa-external-link-alt"></i>
                      Детали
                    </button>
                  </div>
                </div>
                
                <div 
                  v-if="selectedSource === source.chunk_id"
                  class="source-full-content mt-3 p-3 bg-light rounded"
                >
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">Полный текст отрывка:</h6>
                    <button 
                      class="btn btn-sm btn-outline-secondary"
                      @click="copyToClipboard(source.chunk_content)"
                      title="Копировать в буфер обмена"
                    >
                      <i class="fas fa-copy"></i>
                    </button>
                  </div>
                  <div class="source-text">
                    {{ source.chunk_content }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SourceDisplay',
  props: {
    sources: {
      type: Array,
      default: () => []
    },
    userQuery: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      selectedSource: null
    }
  },
  computed: {
    uniqueSources() {
      // Улучшенная дедупликация источников
      const uniqueMap = new Map();
      const contentHashMap = new Map(); // Для отслеживания дубликатов по содержимому
      
      
      this.sources.forEach((source, index) => {
        if (!source.chunk_id) {
          console.warn(`⚠️ Источник ${index} не имеет chunk_id:`, source);
          return;
        }
        
        // Создаем хеш содержимого для дополнительной проверки
        const contentHash = this.hashContent(source.chunk_content);
        const fileName = source.file_name || 'unknown';
        
        // Проверяем уникальность по chunk_id
        if (!uniqueMap.has(source.chunk_id)) {
          // Дополнительная проверка на дубликатов по содержимому и имени файла
          const contentKey = `${contentHash}_${fileName}`;
          
          if (!contentHashMap.has(contentKey)) {
            uniqueMap.set(source.chunk_id, source);
            contentHashMap.set(contentKey, source.chunk_id);
          } else {
            // Если нашли дубликат по содержимому, проверяем, какой источник лучше
            const existingChunkId = contentHashMap.get(contentKey);
            const existingSource = uniqueMap.get(existingChunkId);
            
            
            // Предпочитаем источник с более высокой релевантностью
            if (source.similarity_score && existingSource.similarity_score) {
              if (source.similarity_score > existingSource.similarity_score) {
                // Заменяем существующий источник на более релевантный
                uniqueMap.delete(existingChunkId);
                uniqueMap.set(source.chunk_id, source);
                contentHashMap.set(contentKey, source.chunk_id);
              } else {
              }
            } else if (source.similarity_score && !existingSource.similarity_score) {
              // Предпочитаем источник с релевантностью
              uniqueMap.delete(existingChunkId);
              uniqueMap.set(source.chunk_id, source);
              contentHashMap.set(contentKey, source.chunk_id);
            } else {
            }
          }
        } else {
        }
      });
      
      const result = Array.from(uniqueMap.values());
      
      return result;
    }
  },
  methods: {
    // Простая функция хеширования содержимого
    hashContent(content) {
      if (!content) return '';
      // Создаем простой хеш на основе первых 100 символов и длины
      const preview = content.substring(0, 100).toLowerCase().replace(/\s+/g, ' ');
      return `${preview.length}_${preview}`;
    },
    
    getPreviewText(text) {
      if (!text) return '';
      
      const maxLength = 200; // Увеличиваем длину для лучшего контекста
      
      // Если запрос пользователя не задан, ищем наиболее информативную часть
      if (!this.userQuery || !this.userQuery.trim()) {
        return this.findMostInformativePart(text, maxLength);
      }
      
      // Ищем наиболее релевантную часть текста
      const relevantPart = this.findMostRelevantPart(text, this.userQuery, maxLength);
      
      if (relevantPart) {
        return relevantPart;
      }
      
      // Если не нашли релевантную часть, ищем информативную
      return this.findMostInformativePart(text, maxLength);
    },
    
    findMostInformativePart(text, maxLength) {
      if (!text) return '';
      
      // Разбиваем текст на предложения
      const sentences = text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 10);
      
      if (sentences.length === 0) {
        return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
      }
      
      // Ищем предложение с наибольшей информативностью
      let bestSentence = null;
      let bestScore = 0;
      
      sentences.forEach(sentence => {
        const trimmed = sentence.trim();
        let score = 0;
        
        // Бонус за определения (содержит "—" или "означает")
        if (trimmed.includes('—') || trimmed.includes('означает') || trimmed.includes('это')) {
          score += 50;
        }
        
        // Бонус за термины и сокращения
        if (trimmed.toLowerCase().includes('термины') || trimmed.toLowerCase().includes('сокращения')) {
          score += 40;
        }
        
        // Бонус за технические термины (содержит аббревиатуры)
        const hasAbbreviation = /[А-Я]{2,}/.test(trimmed);
        if (hasAbbreviation) {
          score += 30;
        }
        
        // Бонус за конкретные действия (содержит глаголы)
        const hasAction = /(заполнит|создает|отражает|проверяет|подписывает|получает|ронял|делал)/i.test(trimmed);
        if (hasAction) {
          score += 25;
        }
        
        // Бонус за структурированную информацию (содержит цифры или списки)
        const hasStructure = /\d+/.test(trimmed) || trimmed.includes(':');
        if (hasStructure) {
          score += 20;
        }
        
        // Бонус за имена собственные (содержит заглавные буквы в середине предложения)
        const hasProperNames = /[А-Я][а-я]+/.test(trimmed);
        if (hasProperNames) {
          score += 15;
        }
        
        // Бонус за географические названия (страна, город и т.д.)
        const hasGeography = /(страна|город|область|регион)/i.test(trimmed);
        if (hasGeography) {
          score += 20;
        }
        
        // Штраф за слишком короткие предложения
        if (trimmed.length < 20) {
          score -= 10;
        }
        
        // Штраф за слишком длинные предложения
        if (trimmed.length > 150) {
          score -= 15;
        }
        
        // Штраф за технические команды (Docker, CMD и т.д.)
        if (/(cmd|from|run|copy|expose|workdir)/i.test(trimmed)) {
          score -= 30;
        }
        
        // Штраф за пустые или технические строки
        if (trimmed.length < 5 || /^[0-9\s\-_]+$/.test(trimmed)) {
          score -= 50;
        }
        
        if (score > bestScore) {
          bestScore = score;
          bestSentence = trimmed;
        }
      });
      
      if (bestSentence && bestScore > 0) {
        // Если предложение слишком длинное, обрезаем его умно
        if (bestSentence.length > maxLength) {
          return this.smartTruncate(bestSentence, maxLength);
        }
        return bestSentence;
      }
      
      // Если не нашли подходящее предложение, ищем лучшее начало
      return this.findBestStart(text, maxLength);
    },
    
    findBestStart(text, maxLength) {
      if (!text) return '';
      
      // Ищем первое осмысленное предложение
      const sentences = text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 5);
      
      for (let sentence of sentences) {
        const trimmed = sentence.trim();
        
        // Пропускаем технические строки
        if (/(cmd|from|run|copy|expose|workdir|===|---)/i.test(trimmed)) {
          continue;
        }
        
        // Пропускаем пустые или числовые строки
        if (trimmed.length < 5 || /^[0-9\s\-_]+$/.test(trimmed)) {
          continue;
        }
        
        // Если нашли осмысленное предложение
        if (trimmed.length <= maxLength) {
          return trimmed;
        } else {
          return this.smartTruncate(trimmed, maxLength);
        }
      }
      
      // Если ничего не нашли, возвращаем начало текста
      return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
    },
    
    smartTruncate(text, maxLength) {
      // Пытаемся обрезать по границам предложений или фраз
      const words = text.split(' ');
      let truncated = '';
      
      for (let i = 0; i < words.length; i++) {
        const testTruncated = words.slice(0, i + 1).join(' ');
        if (testTruncated.length <= maxLength - 3) {
          truncated = testTruncated;
        } else {
          break;
        }
      }
      
      if (truncated) {
        // Проверяем, не обрезали ли мы в середине важной фразы
        const lastChar = truncated[truncated.length - 1];
        if (lastChar === '—' || lastChar === ':') {
          // Ищем конец определения
          const remainingText = text.substring(truncated.length);
          const endOfDefinition = remainingText.search(/[.!?]/);
          if (endOfDefinition !== -1 && endOfDefinition < 50) {
            truncated += remainingText.substring(0, endOfDefinition + 1);
          }
        }
        
        return truncated + '...';
      }
      
      return text.substring(0, maxLength - 3) + '...';
    },
    
    findMostRelevantPart(text, query, maxLength) {
      if (!text || !query) return null;
      
      const queryWords = query.toLowerCase().split(/\s+/).filter(word => word.length > 2);
      if (queryWords.length === 0) return null;
      
      // Разбиваем текст на предложения
      const sentences = text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 10);
      
      let bestSentence = null;
      let bestScore = 0;
      
      // Ищем предложение с наибольшим количеством совпадающих слов
      sentences.forEach(sentence => {
        const sentenceLower = sentence.toLowerCase();
        let score = 0;
        
        queryWords.forEach(word => {
          if (sentenceLower.includes(word)) {
            score += 1;
          }
        });
        
        // Дополнительный бонус за точные совпадения фраз
        if (sentenceLower.includes(query.toLowerCase())) {
          score += 5;
        }
        
        // Бонус за определения, содержащие запрос
        if (sentenceLower.includes('—') && queryWords.some(word => sentenceLower.includes(word))) {
          score += 3;
        }
        
        // Бонус за технические термины
        if (sentenceLower.includes('термины') || sentenceLower.includes('сокращения')) {
          score += 2;
        }
        
        if (score > bestScore) {
          bestScore = score;
          bestSentence = sentence.trim();
        }
      });
      
      if (bestSentence && bestScore > 0) {
        // Если предложение слишком длинное, обрезаем его умно
        if (bestSentence.length > maxLength) {
          return this.smartTruncate(bestSentence, maxLength);
        }
        return bestSentence;
      }
      
      // Если не нашли подходящее предложение, ищем фрагмент с ключевыми словами
      const queryLower = query.toLowerCase();
      const textLower = text.toLowerCase();
      
      const index = textLower.indexOf(queryLower);
      if (index !== -1) {
        const start = Math.max(0, index - 80); // Увеличиваем контекст
        const end = Math.min(text.length, index + query.length + 80);
        let fragment = text.substring(start, end);
        
        // Убираем обрезанные слова в начале и конце
        if (start > 0) {
          const firstSpace = fragment.indexOf(' ');
          if (firstSpace !== -1) {
            fragment = fragment.substring(firstSpace + 1);
          }
        }
        
        if (end < text.length) {
          const lastSpace = fragment.lastIndexOf(' ');
          if (lastSpace !== -1) {
            fragment = fragment.substring(0, lastSpace);
          }
        }
        
        if (fragment.length > maxLength) {
          return this.smartTruncate(fragment, maxLength);
        }
        
        return fragment;
      }
      
      return null;
    },
    
    toggleSourceDetails(chunkId) {
      if (this.selectedSource === chunkId) {
        this.selectedSource = null;
      } else {
        this.selectedSource = chunkId;
      }
    },
    
    async copyToClipboard(text) {
      try {
        // Пробуем современный API
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          // Fallback для старых браузеров или HTTP
          const textArea = document.createElement('textarea');
          textArea.value = text;
          textArea.style.position = 'fixed';
          textArea.style.left = '-999999px';
          textArea.style.top = '-999999px';
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          
          try {
            document.execCommand('copy');
            textArea.remove();
          } catch (err) {
            console.error('Fallback copy failed:', err);
            textArea.remove();
            throw err;
          }
        }
        
        this.$emit('show-notification', {
          type: 'success',
          message: 'Текст скопирован в буфер обмена'
        });
      } catch (err) {
        console.error('Ошибка при копировании:', err);
        this.$emit('show-notification', {
          type: 'error',
          message: 'Не удалось скопировать текст. Попробуйте выделить текст вручную.'
        });
      }
    },
    
    openSourceModal(source, isMainSource) {
      this.$emit('open-source-modal', source, isMainSource);
    }
  }
}
</script>

<style scoped>
.source-display {
  font-size: 0.9rem;
}

.source-item {
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.source-item:hover {
  background-color: #e9ecef;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.source-item.border-primary {
  background-color: #e3f2fd;
}

.source-item:first-child {
  border-left: 4px solid #28a745 !important;
  background-color: #f8fff9;
}

.source-item:first-child:hover {
  background-color: #e8f5e8;
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(40, 167, 69, 0.2);
}

.source-preview p {
  font-size: 0.85rem;
  line-height: 1.4;
}

.source-full-content {
  border-left: 3px solid #007bff;
}

.source-text {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.badge {
  font-size: 0.7rem;
}
</style> 