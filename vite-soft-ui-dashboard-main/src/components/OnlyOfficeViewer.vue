<template>
  <div class="modal fade" id="onlyofficeViewerModal" tabindex="-1" aria-labelledby="onlyofficeViewerModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-fullscreen">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="onlyofficeViewerModalLabel">{{ documentTitle }}</h5>
          <div class="modal-controls">
            <button type="button" class="btn btn-outline-primary btn-sm me-2" @click="switchMode('view')" :class="{ active: mode === 'view' }">
              <i class="fas fa-eye me-1"></i>Просмотр
            </button>
            <button type="button" class="btn btn-outline-success btn-sm me-2" @click="switchMode('edit')" :class="{ active: mode === 'edit' }">
              <i class="fas fa-edit me-1"></i>Редактирование
            </button>
            <button type="button" class="btn btn-outline-info btn-sm me-2" @click="switchMode('comment')" :class="{ active: mode === 'comment' }">
              <i class="fas fa-comment me-1"></i>Комментарии
            </button>
            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>Закрыть
            </button>
          </div>
        </div>
        <div class="modal-body p-0">
          <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="mt-3">Загрузка документа в OnlyOffice...</p>
          </div>
          <div v-else-if="error" class="alert alert-danger m-3">
            <h5>Ошибка загрузки документа</h5>
            <p>{{ error }}</p>
            <button type="button" class="btn btn-primary" @click="loadDocument">
              <i class="fas fa-redo me-1"></i>Повторить
            </button>
          </div>
          <div v-else class="onlyoffice-container">
            <iframe 
              v-if="editorUrl" 
              :src="editorUrl" 
              class="onlyoffice-iframe"
              frameborder="0"
              allowfullscreen>
            </iframe>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axiosInstance from '../utils/axiosConfig';
import { Modal } from 'bootstrap';

export default {
  name: 'OnlyOfficeViewer',
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
    userId: {
      type: Number,
      default: 1
    },
    userName: {
      type: String,
      default: 'Пользователь'
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      modal: null,
      mode: 'view',
      editorUrl: null,
      config: null
    };
  },
  mounted() {
    this.modal = new Modal(document.getElementById('onlyofficeViewerModal'));
  },
  methods: {
    async loadDocument() {
      this.loading = true;
      this.error = null;
      
      try {
        // Получаем конфигурацию OnlyOffice
        const response = await axiosInstance.get(`/content/onlyoffice/${this.documentId}`, {
          params: {
            user_id: this.userId,
            user_name: this.userName,
            mode: this.mode
          }
        });
        
        this.config = response.data.config;
        
        // Создаем URL для редактора
        this.editorUrl = `/content/onlyoffice-editor/${this.documentId}?user_id=${this.userId}&user_name=${encodeURIComponent(this.userName)}&mode=${this.mode}`;
        
        this.loading = false;
      } catch (error) {
        console.error('Ошибка при загрузке документа в OnlyOffice:', error);
        this.error = error.response?.data?.detail || 'Ошибка при загрузке документа в OnlyOffice';
        this.loading = false;
      }
    },
    
    async switchMode(newMode) {
      this.mode = newMode;
      await this.loadDocument();
    },
    
    show() {
      this.modal.show();
      this.loadDocument();
    },
    
    hide() {
      this.modal.hide();
    },
    
    // Метод для проверки поддержки файла
    isFileSupported(fileName) {
      const supportedExtensions = ['doc', 'docx', 'odt', 'rtf', 'txt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'odp'];
      const extension = fileName.toLowerCase().split('.').pop();
      return supportedExtensions.includes(extension);
    }
  }
};
</script>

<style scoped>
.onlyoffice-container {
  width: 100%;
  height: calc(100vh - 120px);
  position: relative;
}

.onlyoffice-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.modal-fullscreen {
  max-width: 100%;
  margin: 0;
}

.modal-fullscreen .modal-content {
  height: 100vh;
  border-radius: 0;
}

.modal-header {
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  padding: 15px 20px;
}

.modal-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-controls .btn {
  font-size: 12px;
  padding: 6px 12px;
}

.modal-controls .btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.modal-body {
  padding: 0;
  overflow: hidden;
}

@media (max-width: 768px) {
  .modal-controls {
    flex-direction: column;
    gap: 5px;
  }
  
  .modal-controls .btn {
    width: 100%;
    margin-bottom: 5px;
  }
}
</style> 