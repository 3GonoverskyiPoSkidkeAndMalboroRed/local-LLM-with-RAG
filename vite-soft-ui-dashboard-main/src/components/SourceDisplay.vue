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
                      @click="openSourceModal(source)"
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
      
      console.log(`🔍 Обработка ${this.sources.length} источников для дедупликации`);
      
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
            console.log(`✅ Добавлен уникальный источник: ${fileName} (${source.chunk_id})`);
          } else {
            // Если нашли дубликат по содержимому, проверяем, какой источник лучше
            const existingChunkId = contentHashMap.get(contentKey);
            const existingSource = uniqueMap.get(existingChunkId);
            
            console.log(`🔄 Найден дубликат по содержимому: ${fileName}`);
            console.log(`   Существующий: ${existingSource.chunk_id} (релевантность: ${existingSource.similarity_score})`);
            console.log(`   Новый: ${source.chunk_id} (релевантность: ${source.similarity_score})`);
            
            // Предпочитаем источник с более высокой релевантностью
            if (source.similarity_score && existingSource.similarity_score) {
              if (source.similarity_score > existingSource.similarity_score) {
                // Заменяем существующий источник на более релевантный
                uniqueMap.delete(existingChunkId);
                uniqueMap.set(source.chunk_id, source);
                contentHashMap.set(contentKey, source.chunk_id);
                console.log(`   ✅ Заменен на более релевантный: ${source.chunk_id}`);
              } else {
                console.log(`   ❌ Оставлен существующий: ${existingChunkId}`);
              }
            } else if (source.similarity_score && !existingSource.similarity_score) {
              // Предпочитаем источник с релевантностью
              uniqueMap.delete(existingChunkId);
              uniqueMap.set(source.chunk_id, source);
              contentHashMap.set(contentKey, source.chunk_id);
              console.log(`   ✅ Заменен на источник с релевантностью: ${source.chunk_id}`);
            } else {
              console.log(`   ❌ Оставлен существующий: ${existingChunkId}`);
            }
          }
        } else {
          console.log(`⚠️ Дубликат chunk_id: ${source.chunk_id} для файла ${fileName}`);
        }
      });
      
      const result = Array.from(uniqueMap.values());
      console.log(`📊 Результат дедупликации: ${result.length} уникальных источников из ${this.sources.length} исходных`);
      
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
      
      const maxLength = 150;
      
      // Если запрос пользователя не задан, возвращаем начало текста
      if (!this.userQuery || !this.userQuery.trim()) {
        if (text.length <= maxLength) {
          return text;
        }
        return text.substring(0, maxLength) + '...';
      }
      
      // Ищем наиболее релевантную часть текста
      const relevantPart = this.findMostRelevantPart(text, this.userQuery, maxLength);
      
      if (relevantPart) {
        return relevantPart;
      }
      
      // Если не нашли релевантную часть, возвращаем начало
      if (text.length <= maxLength) {
        return text;
      }
      return text.substring(0, maxLength) + '...';
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
          score += 2;
        }
        
        if (score > bestScore) {
          bestScore = score;
          bestSentence = sentence.trim();
        }
      });
      
      if (bestSentence && bestScore > 0) {
        // Если предложение слишком длинное, обрезаем его
        if (bestSentence.length > maxLength) {
          // Пытаемся найти лучшее место для обрезки
          const words = bestSentence.split(' ');
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
            return truncated + '...';
          } else {
            return bestSentence.substring(0, maxLength - 3) + '...';
          }
        }
        
        return bestSentence;
      }
      
      // Если не нашли подходящее предложение, ищем фрагмент с ключевыми словами
      const queryLower = query.toLowerCase();
      const textLower = text.toLowerCase();
      
      const index = textLower.indexOf(queryLower);
      if (index !== -1) {
        const start = Math.max(0, index - 50);
        const end = Math.min(text.length, index + query.length + 50);
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
          fragment = fragment.substring(0, maxLength - 3) + '...';
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
    
    openSourceModal(source) {
      this.$emit('open-source-modal', source);
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