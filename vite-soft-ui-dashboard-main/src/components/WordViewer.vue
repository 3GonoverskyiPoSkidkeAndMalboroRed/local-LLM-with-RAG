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
  white-space: pre-wrap;
}

.modal-xl {
  max-width: 90%;
}

.modal-body {
  max-height: 80vh;
  overflow-y: auto;
}
</style> 