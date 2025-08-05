<template>
  <div class="modal fade" id="wordViewerModal" tabindex="-1" aria-labelledby="wordViewerModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="wordViewerModalLabel">{{ documentTitle }}</h5>
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
          <div v-else class="word-content">
            <div class="document-header mb-4">
              <h4>{{ documentTitle }}</h4>
              <p class="text-muted">{{ documentDescription }}</p>
            </div>
            <div class="document-content" v-html="documentContent"></div>
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
  name: 'WordViewer',
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
  mounted() {
    this.modal = new Modal(document.getElementById('wordViewerModal'));
  },
  methods: {
    async loadDocument() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axiosInstance.get(`/content/word-content/${this.documentId}`);
        
        // Получаем данные из JSON ответа
        this.documentContent = response.data.content;
        
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
    downloadDocument() {
      window.location.href = `${axiosInstance.defaults.baseURL}/content/download-file/${this.documentId}`;
    }
  }
};
</script>

<style scoped>
.word-content {
  max-height: 70vh;
  overflow-y: auto;
}

.document-header {
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 20px;
}

.document-content {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.8;
  font-size: 16px;
  color: #333;
}

.document-content h1, .document-content h2, .document-content h3, 
.document-content h4, .document-content h5, .document-content h6 {
  color: #2c3e50;
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: 600;
}

.document-content p {
  margin-bottom: 12px;
  text-align: justify;
}

.document-content table {
  width: 100%;
  margin: 15px 0;
  border-collapse: collapse;
  border: 1px solid #ddd;
}

.document-content td {
  padding: 8px;
  border: 1px solid #ddd;
  vertical-align: top;
}

.document-content strong {
  font-weight: 600;
}

.document-content em {
  font-style: italic;
}

.document-content u {
  text-decoration: underline;
}

.document-content del {
  text-decoration: line-through;
  color: #6c757d;
}

.document-content ul {
  margin: 15px 0;
  padding-left: 20px;
}

.document-content li {
  margin-bottom: 5px;
  line-height: 1.6;
}

.docx-list {
  margin: 15px 0;
  padding-left: 20px;
}

.docx-list-item {
  margin-bottom: 5px;
  line-height: 1.6;
}

.modal-xl {
  max-width: 90%;
}

.modal-body {
  max-height: 80vh;
  overflow-y: auto;
}
</style> 