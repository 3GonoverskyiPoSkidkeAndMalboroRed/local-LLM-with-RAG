<template>
  <div class="modal fade" id="documentViewerModal" tabindex="-1" aria-labelledby="documentViewerModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="documentViewerModalLabel">{{ documentTitle }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="loading" class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="mt-2">Загрузка документа...</p>
          </div>
          <div v-else-if="error" class="alert alert-danger">
            {{ error }}
          </div>
          <div v-else class="document-viewer-content">
            <!-- Информация о поиске -->
            <div v-if="searchQuery" class="search-info alert alert-info">
              <i class="fas fa-search me-2"></i>
              Найдено выделений для запроса: <strong>"{{ searchQuery }}"</strong>
            </div>
            
            <!-- Метаинформация о документе -->
            <div class="document-meta">
              <span class="badge bg-secondary me-2">{{ fileExtension.toUpperCase() }}</span>
              <span class="text-muted">{{ documentSize }} символов</span>
            </div>
            
            <!-- Содержимое документа -->
            <div class="document-content" v-html="highlightedContent"></div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
          <button type="button" class="btn btn-primary" @click="downloadDocument">
            <i class="fas fa-download me-2"></i>Скачать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axiosInstance from '../utils/axiosConfig';
import { Modal } from 'bootstrap';

export default {
  name: 'DocumentViewer',
  props: {
    documentId: {
      type: Number,
      required: true
    },
    documentTitle: {
      type: String,
      default: 'Документ'
    },
    documentDescription: {
      type: String,
      default: ''
    },
    searchQuery: {
      type: String,
      default: ''
    },
    filePath: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      documentContent: '',
      modal: null
    };
  },
  computed: {
    fileExtension() {
      if (!this.filePath) return '';
      const parts = this.filePath.split('.');
      return parts[parts.length - 1] || '';
    },
    documentSize() {
      return this.documentContent.length;
    },
    highlightedContent() {
      if (!this.searchQuery || !this.documentContent) {
        return this.documentContent;
      }
      
      // Выделяем найденные отрывки
      const regex = new RegExp(`(${this.escapeRegExp(this.searchQuery)})`, 'gi');
      return this.documentContent.replace(regex, '<mark>$1</mark>');
    }
  },
  mounted() {
    this.modal = new Modal(document.getElementById('documentViewerModal'));
  },
  methods: {
    escapeRegExp(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },
    async loadDocument() {
      this.loading = true;
      this.error = null;
      
      try {
        // Определяем URL для загрузки документа
        let url = `/content/document-viewer-with-highlight/${this.documentId}`;
        if (this.searchQuery) {
          url += `?search_query=${encodeURIComponent(this.searchQuery)}`;
        }
        
        const response = await axiosInstance.get(url);
        
        // Получаем данные из JSON ответа
        this.documentContent = response.data.content || response.data;
        
        this.loading = false;
      } catch (error) {
        console.error('Ошибка при загрузке документа:', error);
        this.error = 'Ошибка при загрузке документа';
        this.loading = false;
      }
    },
    show() {
      this.modal.show();
      this.loadDocument();
    },
    hide() {
      this.modal.hide();
    },
    async downloadDocument() {
      try {
        // Используем axios для скачивания файла с правильной аутентификацией
        const response = await axiosInstance.get(`/content/download-file/${this.documentId}`, {
          responseType: 'blob' // Важно для скачивания файлов
        });
        
        // Создаем blob URL для скачивания
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку для скачивания
        const link = document.createElement('a');
        link.href = url;
        link.download = this.documentTitle || 'document';
        document.body.appendChild(link);
        link.click();
        
        // Очищаем ресурсы
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
      } catch (error) {
        console.error("Ошибка при скачивании документа:", error);
        // Fallback к старому методу с токеном
        try {
          const tokenResponse = await axiosInstance.get(`/content/download-token/${this.documentId}`);
          const downloadToken = tokenResponse.data.download_token;
          window.location.href = `${axiosInstance.defaults.baseURL}/content/public-download/${this.documentId}?token=${downloadToken}`;
        } catch (fallbackError) {
          console.error("Ошибка при fallback скачивании:", fallbackError);
        }
      }
    }
  }
};
</script>

<style scoped>
.document-viewer-content {
  max-height: 70vh;
  overflow-y: auto;
}

.search-info {
  margin-bottom: 15px;
  padding: 10px 15px;
  border-radius: 6px;
}

.document-meta {
  background: #f8f9fa;
  padding: 10px 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  border: 1px solid #dee2e6;
}

.document-content {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.8;
  font-size: 16px;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 15px;
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 6px;
}

.document-content :deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.modal-xl {
  max-width: 90%;
}

.modal-body {
  max-height: 80vh;
  overflow-y: auto;
}
</style>
