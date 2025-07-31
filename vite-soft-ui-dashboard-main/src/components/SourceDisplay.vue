<template>
  <div class="source-display mt-3">
    <div class="card">
      <div class="card-header pb-0">
        <h6 class="mb-0">
          <i class="fas fa-book-open me-2"></i>
          Источники информации
        </h6>
      </div>
      <div class="card-body">
        <div v-if="sources.length === 0" class="text-muted">
          <i class="fas fa-info-circle me-2"></i>
          Источники не найдены
        </div>
        
        <div v-else class="sources-list">
          <div 
            v-for="(source, index) in sources" 
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
    }
  },
  data() {
    return {
      selectedSource: null
    }
  },
  methods: {
    getPreviewText(text) {
      if (!text) return '';
      const maxLength = 150;
      if (text.length <= maxLength) {
        return text;
      }
      return text.substring(0, maxLength) + '...';
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