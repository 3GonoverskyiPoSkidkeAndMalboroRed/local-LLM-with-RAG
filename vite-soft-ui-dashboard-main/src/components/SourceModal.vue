<template>
  <div class="modal fade" id="sourceModal" tabindex="-1" aria-labelledby="sourceModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="sourceModalLabel">
            <i class="fas fa-file-alt me-2"></i>
            Детальная информация об источнике
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body" v-if="source">
          <div class="row">
            <div class="col-12">
              <div class="source-info mb-4">
                <h6 class="text-primary mb-3">
                  <i class="fas fa-file me-2"></i>
                  {{ source.file_name }}
                </h6>
                
                <div class="row mb-3">
                  <div class="col-md-6">
                    <strong>Путь к файлу:</strong>
                    <p class="text-muted">{{ source.file_path }}</p>
                  </div>
                  <div class="col-md-6">
                    <strong>ID фрагмента:</strong>
                    <p class="text-muted">{{ source.chunk_id }}</p>
                  </div>
                </div>
                
                <div class="row mb-3" v-if="source.page_number || source.similarity_score || isMainSource">
                  <div class="col-md-4" v-if="source.page_number">
                    <strong>Номер страницы:</strong>
                    <span class="badge bg-secondary ms-2">{{ source.page_number }}</span>
                  </div>
                  <div class="col-md-4" v-if="source.similarity_score">
                    <strong>Релевантность:</strong>
                    <span class="badge bg-info ms-2">{{ (source.similarity_score * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="col-md-4" v-if="isMainSource">
                    <strong>Статус:</strong>
                    <span class="badge bg-success ms-2">
                      <i class="fas fa-star"></i> Основной источник
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="source-content">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="mb-0">Содержание фрагмента:</h6>
                  <div>
                    <button 
                      class="btn btn-sm btn-outline-primary me-2"
                      @click="copyToClipboard(source.chunk_content)"
                      title="Копировать в буфер обмена"
                    >
                      <i class="fas fa-copy me-1"></i>
                      Копировать
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-secondary"
                      @click="downloadAsFile"
                      title="Скачать как файл"
                    >
                      <i class="fas fa-download me-1"></i>
                      Скачать
                    </button>
                  </div>
                </div>
                
                <div class="source-text-container">
                  <div class="source-text">
                    {{ source.chunk_content }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SourceModal',
  props: {
    source: {
      type: Object,
      default: null
    },
    isMainSource: {
      type: Boolean,
      default: false
    }
  },
  methods: {
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
    
    downloadAsFile() {
      if (!this.source) return;
      
      const content = this.source.chunk_content;
      const fileName = `${this.source.file_name}_fragment.txt`;
      
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
      
      this.$emit('show-notification', {
        type: 'success',
        message: `Файл ${fileName} скачан`
      });
    }
  }
}
</script>

<style scoped>
.source-info {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 0.375rem;
  border-left: 4px solid #007bff;
}

.source-text-container {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.source-text {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #212529;
}

.badge {
  font-size: 0.8rem;
}

.modal-lg {
  max-width: 800px;
}
</style> 