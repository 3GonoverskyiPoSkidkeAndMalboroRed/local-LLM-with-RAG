<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="card mb-4">
          <div class="card-header pb-0">
            <div class="d-flex justify-content-between align-items-center">
              <h6>{{ tagName }}</h6>
              <router-link to="/library" class="btn btn-sm btn-info">
                <i class="fas fa-arrow-left me-2"></i>
                Назад к библиотеке
              </router-link>
            </div>
            <input
              type="text"
              class="form-control mt-2"
              v-model="searchQuery"
              @input="searchDocuments"
              placeholder="Поиск по названию, описанию или имени файла"
            />
          </div>
          <div class="card-body px-0 pt-0 pb-2">
            <div class="p-4">
              <!-- Загрузка данных -->
              <div v-if="loading" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="mt-2">Загрузка данных...</p>
              </div>

              <!-- Сообщение об ошибке -->
              <div v-else-if="error" class="alert alert-danger">
                {{ error }}
              </div>

              <!-- Список документов -->
              <div v-else>
                <div v-if="documents.length === 0" class="alert alert-info">
                  В этой категории нет документов.
                </div>
                
                <div v-else class="table-responsive">
                  <table class="table align-items-center mb-0">
                    <thead>
                      <tr>
                        <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Документ</th>
                        <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Описание</th>
                        <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Файл</th>
                        <th class="text-secondary opacity-7"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="doc in documents" :key="doc.id">
                        <td>
                          <div class="d-flex px-2 py-1">
                            <div>
                              <i :class="getFileIconClass(doc.file_path)" class="me-3"></i>
                            </div>
                            <div class="d-flex flex-column justify-content-center">
                              <h6 class="mb-0 text-sm">{{ doc.title || 'Без названия' }}</h6>
                            </div>
                          </div>
                        </td>
                        <td>
                          <p class="text-xs text-secondary mb-0">{{ doc.description || 'Нет описания' }}</p>
                        </td>
                        <td>
                          <p class="text-xs text-secondary mb-0">{{ getFileName(doc.file_path) }}</p>
                        </td>
                        <td class="align-middle">
                          <button class="btn btn-sm btn-outline-secondary me-2" @click="viewDocument(doc)">
                            <i class="fas fa-eye"></i>
                          </button>
                          <button class="btn btn-sm btn-outline-secondary me-2" @click="downloadDocument(doc)">
                            <i class="fas fa-download"></i>
                          </button>
                          <button class="btn btn-sm btn-info me-2" @click="copyLink(doc.id, 'view')">
                            <i class="fas fa-share-alt"></i> Просмотр
                          </button>
                          <button class="btn btn-sm btn-info" @click="copyLink(doc.id, 'download')">
                            <i class="fas fa-share-alt"></i> Скачать
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно для просмотра медиа файлов -->
    <div class="modal fade" id="mediaPlayerModal" tabindex="-1" aria-labelledby="mediaPlayerModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="mediaPlayerModalLabel">{{ currentMediaTitle }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center">
            <!-- Аудио плеер -->
            <audio v-if="isAudioFile" controls class="w-100 mb-3" ref="audioPlayer">
              <source :src="currentMediaUrl" :type="currentMediaType">
              Ваш браузер не поддерживает аудио элемент.
            </audio>
            
            <!-- Видео плеер -->
            <video v-if="isVideoFile" controls class="w-100" ref="videoPlayer">
              <source :src="currentMediaUrl" :type="currentMediaType">
              Ваш браузер не поддерживает видео элемент.
            </video>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <a :href="currentMediaUrl" download class="btn btn-primary">Скачать</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Всплывающее уведомление о копировании ссылки -->
    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 5">
      <div id="copyToast" class="toast align-items-center text-white bg-success" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            Ссылка скопирована в буфер обмена!
          </div>
          <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    </div>
    

  </div>
</template>

<script>
import axiosInstance from '@/utils/axiosConfig';
import { Modal, Toast } from 'bootstrap';

export default {
  name: "TagContentPage",
  data() {
    return {
      userId: localStorage.getItem("userId"),
      userRole: localStorage.getItem("role_name"),
      tagId: null,
      tagName: '',
      documents: [],
      allDocuments: [], // Все документы для поиска
      loading: true,
      error: null,
      mediaPlayerModal: null,
      currentMediaUrl: "",
      currentMediaType: "",
      currentMediaTitle: "",
      isAudioFile: false,
      isVideoFile: false,
      copyToast: null,
      searchQuery: "" // Поле для хранения поискового запроса
    };
  },
  async created() {
    if (!this.userId) {
      this.$router.push("/sign-in");
      return;
    }
    
    // Получаем ID и название тега из параметров маршрута
    this.tagId = this.$route.params.tagId;
    this.tagName = this.$route.params.tagName;
    
    // Преобразуем tagId в число, если это не 'untagged'
    if (this.tagId !== 'untagged') {
      this.tagId = parseInt(this.tagId);
    }
    
    await this.fetchTagContent();
  },
  mounted() {
    // Инициализируем модальное окно
    this.mediaPlayerModal = new Modal(document.getElementById('mediaPlayerModal'));
    
    // Инициализируем toast для уведомлений
    this.copyToast = new Toast(document.getElementById('copyToast'));
    
    // Добавляем обработчик события закрытия модального окна
    document.getElementById('mediaPlayerModal').addEventListener('hidden.bs.modal', () => {
      // Останавливаем воспроизведение при закрытии модального окна
      if (this.$refs.audioPlayer) {
        this.$refs.audioPlayer.pause();
      }
      if (this.$refs.videoPlayer) {
        this.$refs.videoPlayer.pause();
      }
      this.currentMediaUrl = "";
      this.currentMediaTitle = "";
      this.currentMediaType = "";
      this.isAudioFile = false;
      this.isVideoFile = false;
    });
  },
  methods: {
    async fetchTagContent() {
      try {
        this.loading = true;
        
        console.log('TagContentPage - tagId:', this.tagId);
        console.log('TagContentPage - userId:', this.userId);
        console.log('TagContentPage - userRole:', this.userRole);
        
        let response;
        
                if (this.tagId === 'untagged') {
          // Получаем документы без тега через общий эндпоинт
          console.log('Получаем документы без тега');
          const allResponse = await axiosInstance.get(`/user/${this.userId}/content/by-tags`);
          console.log('Ответ для untagged:', allResponse.data);
          this.allDocuments = allResponse.data.untagged_content;
          this.documents = [...this.allDocuments];
        } else {
          // Получаем документы по ID тега
          console.log('Получаем документы по тегу ID:', this.tagId);
          response = await axiosInstance.get(`/content/user/${this.userId}/content/by-tags/${this.tagId}`);
          console.log('Ответ для тега:', response.data);
          this.allDocuments = response.data;
          this.documents = [...this.allDocuments];
        }
        
        console.log('Итоговые документы:', this.documents);
        console.log('Количество документов:', this.documents.length);
        
        this.loading = false;
      } catch (error) {
        console.error("Ошибка при получении контента:", error);
        this.error = "Произошла ошибка при загрузке данных";
        this.loading = false;
      }
    },
    searchDocuments() {
      if (this.searchQuery.length > 0) {
        // Нормализуем поисковый запрос (заменяем пробелы на подчеркивания и наоборот)
        const normalizedQuery = this.searchQuery.toLowerCase().replace(/ /g, '_').replace(/_/g, ' ');
        const originalQuery = this.searchQuery.toLowerCase();
        
        // Фильтруем документы с учетом нормализации
        this.documents = this.allDocuments.filter(doc => {
          const title = doc.title.toLowerCase();
          const description = (doc.description || '').toLowerCase();
          const fileName = this.getFileName(doc.file_path).toLowerCase();
          
          // Проверяем оригинальный запрос
          const matchesOriginal = title.includes(originalQuery) ||
                                 description.includes(originalQuery) ||
                                 fileName.includes(originalQuery);
          
          // Проверяем нормализованный запрос
          const matchesNormalized = title.includes(normalizedQuery) ||
                                   description.includes(normalizedQuery) ||
                                   fileName.includes(normalizedQuery);
          
          // Проверяем с заменой подчеркиваний на пробелы в названии
          const titleWithSpaces = title.replace(/_/g, ' ');
          const matchesTitleSpaces = titleWithSpaces.includes(originalQuery);
          
          // Проверяем с заменой пробелов на подчеркивания в названии
          const titleWithUnderscores = title.replace(/ /g, '_');
          const matchesTitleUnderscores = titleWithUnderscores.includes(originalQuery);
          
          return matchesOriginal || matchesNormalized || matchesTitleSpaces || matchesTitleUnderscores;
        });
      } else {
        // Если поле поиска пустое, показываем все документы
        this.documents = [...this.allDocuments];
      }
    },
    getFileName(filePath) {
      if (!filePath) return 'Имя файла недоступно';
      
      // Разделяем путь по слешам и берем последний элемент
      const parts = filePath.split(/[\/]/); // Разделяем по / или \ 
      return parts[parts.length - 1];
    },
    viewDocument(doc) {
      const fileExtension = this.getFileExtension(doc.file_path);
      
      // Проверяем, является ли файл аудио или видео
      if (this.isAudio(fileExtension) || this.isVideo(fileExtension)) {
        // Настраиваем модальное окно для медиа файла
        this.currentMediaUrl = `${axiosInstance.defaults.baseURL}/content/download-file/${doc.id}`;
        this.currentMediaTitle = doc.title || this.getFileName(doc.file_path);
        
        // Устанавливаем тип медиа
        if (this.isAudio(fileExtension)) {
          this.currentMediaType = `audio/${fileExtension}`;
          this.isAudioFile = true;
          this.isVideoFile = false;
        } else if (this.isVideo(fileExtension)) {
          this.currentMediaType = `video/${fileExtension}`;
          this.isAudioFile = false;
          this.isVideoFile = true;
        }
        
        // Открываем модальное окно
        this.mediaPlayerModal.show();
      } else {
        // Для всех остальных файлов используем Google Docs Viewer
        const viewerUrl = `${axiosInstance.defaults.baseURL}/content/document-viewer/${doc.id}`;
        window.open(viewerUrl, '_blank');
      }
    },
    async downloadDocument(doc) {
      try {
        // Скачивание документа
        window.location.href = `${axiosInstance.defaults.baseURL}/content/download-file/${doc.id}`;
      } catch (error) {
        console.error("Ошибка при скачивании документа:", error);
      }
    },
    copyLink(docId, action) {
      const url = action === 'view' 
        ? `${axiosInstance.defaults.baseURL}/content/document-viewer/${docId}` 
        : `${axiosInstance.defaults.baseURL}/content/download-file/${docId}`;
      
      if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
          alert('Ссылка скопирована в буфер обмена!');
        }).catch(err => {
          console.error('Ошибка при копировании ссылки:', err);
        });
      } else {
        // Альтернативный метод копирования для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = url;
        document.body.appendChild(textarea);
        textarea.select();
        try {
          document.execCommand('copy');
          alert('Ссылка скопирована в буфер обмена!');
        } catch (err) {
          console.error('Ошибка при копировании ссылки:', err);
        }
        document.body.removeChild(textarea);
      }
    },
    getFileIconClass(filePath) {
      const extension = this.getFileExtension(filePath);
      switch (extension) {
        case 'pdf':
          return 'fas fa-file-pdf text-danger';
        case 'doc':
        case 'docx':
          return 'fas fa-file-word text-primary';
        case 'xls':
        case 'xlsx':
          return 'fas fa-file-excel text-success';
        case 'ppt':
        case 'pptx':
          return 'fas fa-file-powerpoint text-warning';
        case 'mp3':
        case 'wav':
        case 'ogg':
          return 'fas fa-file-audio text-info';
        case 'mp4':
        case 'webm':
        case 'avi':
        case 'mov':
          return 'fas fa-file-video text-danger';
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif':
          return 'fas fa-file-image text-success';
        default:
          return 'fas fa-file-alt text-secondary';
      }
    },
    getFileExtension(filePath) {
      if (!filePath) return '';
      return filePath.split('.').pop().toLowerCase();
    },
    isAudio(extension) {
      return ['mp3', 'wav', 'ogg'].includes(extension);
    },
    isVideo(extension) {
      return ['mp4', 'webm', 'avi', 'mov'].includes(extension);
    }
  }
};
</script>

<style scoped>
/* Дополнительные стили при необходимости */
.btn-info {
  background-color: #172d76;
  border-color: #7b7b7b;

}
</style> 