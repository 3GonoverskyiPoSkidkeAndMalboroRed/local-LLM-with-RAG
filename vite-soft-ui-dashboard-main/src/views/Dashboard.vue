<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="card mb-4">
          <div class="card-header pb-0 text-center">
            <h1 class="display-6 fw-bold text-dark mb-2">
              Корпоративная система управления знаниями НПО «СПЕКТРОН»
            </h1>
          </div>
          <div class="card-body px-0 pt-0 pb-2">
            <div class="p-4 text-center">
              <!-- Дополнительного текста не требуется -->
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

    <!-- Добавляем кнопку для перехода на страницу библиотеки документов -->
    <div class="row mt-4">
      <div class="col-12 text-center">
        <router-link to="/library" class="btn btn-info me-3">
          <i class="fas fa-book me-2"></i>
          Перейти в библиотеку документов
        </router-link>
        <router-link to="/quizzes" class="btn btn-info">
          <i class="fas fa-clipboard-check me-2"></i>
          Перейти к тестам и анкетам
        </router-link>
      </div>
    </div>
    
    <!-- FAQ блок -->
    <div class="row mt-4">
      <div class="col-12">
        <div class="faq-container">
          <div class="faq-header mb-4">
            <i class="fas fa-question-circle me-2 text-info"></i>
            <h4 class="mb-0 fw-bold">Часто задаваемые вопросы</h4>
          </div>
          <div class="faq-content">
            <div class="accordion" id="faqAccordion">
              <!-- Общие вопросы -->
              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingOne">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseOne" aria-expanded="false" aria-controls="faqCollapseOne">
                    <i class="fas fa-search me-2"></i>
                    Я не могу найти нужный документ. Что делать?
                  </button>
                </h2>
                <div id="faqCollapseOne" class="faq-collapse collapse" aria-labelledby="faqHeadingOne" >
                  <div class="faq-body">
                    <p>Попробуйте:</p>
                    <ul>
                      <li>Использовать разные ключевые слова для поиска</li>
                      <li>Обратиться к ИИ-ассистенту в режиме RAG</li>
                      <li>Связаться с администратором для проверки прав доступа</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingTwo">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseTwo" aria-expanded="false" aria-controls="faqCollapseTwo">
                    <i class="fas fa-robot me-2"></i>
                    ИИ-ассистент не отвечает на мой вопрос. Почему?
                  </button>
                </h2>
                <div id="faqCollapseTwo" class="faq-collapse collapse" aria-labelledby="faqHeadingTwo" >
                  <div class="faq-body">
                    <p>Возможные причины:</p>
                    <ul>
                      <li>RAG система не инициализирована для вашего отдела</li>
                      <li>В базе нет документов по вашему вопросу</li>
                      <li>Вопрос сформулирован слишком общо</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingThree">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseThree" aria-expanded="false" aria-controls="faqCollapseThree">
                    <i class="fas fa-folder-open me-2"></i>
                    Как узнать, какие документы доступны моему отделу?
                  </button>
                </h2>
                <div id="faqCollapseThree" class="faq-collapse collapse" aria-labelledby="faqHeadingThree" >
                  <div class="faq-body">
                    <p>Перейдите в раздел "Документы" - там отображаются только доступные вам файлы согласно уровню доступа.</p>
                  </div>
                </div>
              </div>

              <!-- Технические проблемы -->
              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingFour">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseFour" aria-expanded="false" aria-controls="faqCollapseFour">
                    <i class="fas fa-tachometer-alt me-2"></i>
                    Страница загружается медленно
                  </button>
                </h2>
                <div id="faqCollapseFour" class="faq-collapse collapse" aria-labelledby="faqHeadingFour" >
                  <div class="faq-body">
                    <ul>
                      <li>Проверьте интернет-соединение</li>
                      <li>Обновите страницу (F5)</li>
                      <li>Очистите кэш браузера</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingFive">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseFive" aria-expanded="false" aria-controls="faqCollapseFive">
                    <i class="fas fa-upload me-2"></i>
                    Не могу загрузить файл
                  </button>
                </h2>
                <div id="faqCollapseFive" class="faq-collapse collapse" aria-labelledby="faqHeadingFive" >
                  <div class="faq-body">
                    <p>Убедитесь, что:</p>
                    <ul>
                      <li>Размер файла не превышает лимит</li>
                      <li>Формат файла поддерживается (PDF, DOCX, TXT)</li>
                      <li>У вас есть права администратора</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingSix">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseSix" aria-expanded="false" aria-controls="faqCollapseSix">
                    <i class="fas fa-key me-2"></i>
                    Забыл пароль
                  </button>
                </h2>
                <div id="faqCollapseSix" class="faq-collapse collapse" aria-labelledby="faqHeadingSix" >
                  <div class="faq-body">
                    <p>Обратитесь к системному администратору для восстановления доступа.</p>
                  </div>
                </div>
              </div>

              <!-- Работа с ИИ -->
              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingSeven">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseSeven" aria-expanded="false" aria-controls="faqCollapseSeven">
                    <i class="fas fa-brain me-2"></i>
                    Как получить более точные ответы от ИИ?
                  </button>
                </h2>
                <div id="faqCollapseSeven" class="faq-collapse collapse" aria-labelledby="faqHeadingSeven" >
                  <div class="faq-body">
                    <ul>
                      <li>Используйте режим "С базой знаний"</li>
                      <li>Формулируйте вопросы конкретно</li>
                      <li>Используйте терминологию из ваших документов</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingEight">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseEight" aria-expanded="false" aria-controls="faqCollapseEight">
                    <i class="fas fa-history me-2"></i>
                    Можно ли сохранить историю чата?
                  </button>
                </h2>
                <div id="faqCollapseEight" class="faq-collapse collapse" aria-labelledby="faqHeadingEight" >
                  <div class="faq-body">
                    <p>История чата сохраняется в рамках текущей сессии. Для долгосрочного хранения скопируйте важную информацию.</p>
                  </div>
                </div>
              </div>

              <!-- Контакты и поддержка -->
              <div class="faq-block">
                <h2 class="faq-header-item" id="faqHeadingNine">
                  <button class="faq-button collapsed" type="button"  data-bs-target="#faqCollapseNine" aria-expanded="false" aria-controls="faqCollapseNine">
                    <i class="fas fa-headset me-2"></i>
                    Контакты и поддержка
                  </button>
                </h2>
                <div id="faqCollapseNine" class="faq-collapse collapse" aria-labelledby="faqHeadingNine" >
                  <div class="faq-body">
                    <p>При возникновении проблем или вопросов обращайтесь:</p>
                    <ul>
                      <li><strong>Администратор системы:</strong> neverov.p@spectronxray.ru</li>
                      <li><strong>Обратная связь:</strong> используйте встроенную форму в системе</li>
                    </ul>
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
import axiosInstance from '@/utils/axiosConfig';
import { Modal } from 'bootstrap';

export default {
  name: "DashboardDefault",
  data() {
    return {
      userId: localStorage.getItem("userId"),
      openFolders: [], // Массив ID открытых папок
      contentData: {
        tags: [],
        untagged_content: []
      },
      loading: true,
      error: null,
      searchQuery: "", // Поле для хранения поискового запроса
      documents: [], // Поле для хранения найденных документов
      mediaPlayerModal: null,
      currentMediaUrl: "",
      currentMediaType: "",
      currentMediaTitle: "",
      isAudioFile: false,
      isVideoFile: false
    };
  },
  async created() {
    if (!this.userId) {
      this.$router.push("/sign-in");
      return;
    }
    
    await this.fetchContentByTags();
  },
  mounted() {
    // Инициализируем модальное окно
    this.mediaPlayerModal = new Modal(document.getElementById('mediaPlayerModal'));
    
    // Добавляем обработчик события закрытия модального окна
    document.getElementById('mediaPlayerModal').addEventListener('hidden.bs.modal', () => {
      // Останавливаем воспроизведение при закрытии модального окна
      if (this.$refs.audioPlayer) {
        this.$refs.audioPlayer.pause();
      }
      if (this.$refs.videoPlayer) {
        this.$refs.videoPlayer.pause();
      }
    });
  },
  methods: {
    async fetchContentByTags() {
      try {
        this.loading = true;
        const response = await axiosInstance.get(`/user/${this.userId}/content/by-tags`);
        this.contentData = response.data;

        // Отладка: выводим полученные данные о контенте
        console.log('Полученные данные о контенте:', this.contentData);

        // Выводим информацию о каждом документе
        this.contentData.untagged_content.forEach(doc => {
          console.log(`Документ: ${doc.title}, Описание: ${doc.description}, Путь к файлу: ${doc.file_path}, Имя файла: ${this.getFileName(doc.file_path)}`);
        });

        this.loading = false;
      } catch (error) {
        console.error("Ошибка при получении контента:", error);
        this.error = "Произошла ошибка при загрузке данных";
        this.loading = false;
      }
    },
    async searchDocuments() {
      if (this.searchQuery.length > 0) {
        try {
          const response = await axiosInstance.get(`/content/search-documents?user_id=${this.userId}&search_query=${this.searchQuery}`);
          this.documents = response.data.documents; // Обновляем список документов
        } catch (error) {
          console.error("Ошибка при поиске документов:", error);
          this.error = "Ошибка при поиске документов";
        }
      } else {
        this.documents = []; // Если поле поиска пустое, очищаем список документов
      }
    },
    // Метод для получения имени файла из пути
    getFileName(filePath) {
      if (!filePath) return 'Имя файла недоступно';
      
      // Разделяем путь по слешам и берем последний элемент
      const parts = filePath.split(/[\/\\]/); // Разделяем по / или \
      return parts[parts.length - 1];
    },
    toggleFolder(folderId) {
      if (this.openFolders.includes(folderId)) {
        this.openFolders = this.openFolders.filter(id => id !== folderId);
      } else {
        this.openFolders.push(folderId);
      }
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
        // Используем axios для скачивания файла с правильной аутентификацией
        const response = await axiosInstance.get(`/content/download-file/${doc.id}`, {
          responseType: 'blob' // Важно для скачивания файлов
        });
        
        // Создаем blob URL для скачивания
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку для скачивания
        const link = document.createElement('a');
        link.href = url;
        link.download = this.getFileName(doc.file_path);
        document.body.appendChild(link);
        link.click();
        
        // Очищаем ресурсы
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
      } catch (error) {
        console.error("Ошибка при скачивании документа:", error);
        // Fallback к старому методу с токеном
        try {
          const tokenResponse = await axiosInstance.get(`/content/download-token/${doc.id}`);
          const downloadToken = tokenResponse.data.download_token;
          window.location.href = `${axiosInstance.defaults.baseURL}/content/public-download/${doc.id}?token=${downloadToken}`;
        } catch (fallbackError) {
          console.error("Ошибка при fallback скачивании:", fallbackError);
        }
      }
    },
    async copyLink(docId, action) {
      let url;
      if (action === 'view') {
        url = `${axiosInstance.defaults.baseURL}/content/document-viewer/${docId}`;
      } else {
        try {
          // Получаем токен для скачивания
          const tokenResponse = await axiosInstance.get(`/content/download-token/${docId}`);
          const downloadToken = tokenResponse.data.download_token;
          url = `${axiosInstance.defaults.baseURL}/content/public-download/${docId}?token=${downloadToken}`;
        } catch (error) {
          console.error("Ошибка при получении токена для копирования ссылки:", error);
          // Fallback к старому методу
          url = `${axiosInstance.defaults.baseURL}/content/download-file/${docId}`;
        }
      }
      
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
          return 'fas fa-file-pdf '; // Красный для PDF
        case 'doc':
        case 'docx':
          return 'fas fa-file-word '; // Синий для Word
        case 'xls':
        case 'xlsx':
          return 'fas fa-file-excel'; // Зеленый для Excel
        case 'ppt':
        case 'pptx':
          return 'fas fa-file-powerpoint text-warning'; // Желтый для PowerPoint
        case 'mp3':
        case 'wav':
        case 'ogg':
          return 'fas fa-file-audio text-info'; // Голубой для аудио
        case 'mp4':
        case 'webm':
        case 'avi':
        case 'mov':
          return 'fas fa-file-video text-danger'; // Красный для видео
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif':
          return 'fas fa-file-image text-success'; // Зеленый для изображений
        default:
          return 'fas fa-file-alt text-secondary'; // Серый для других форматов
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
  },
  mounted() {
    // Полностью кастомная реализация FAQ с плавной анимацией
    this.$nextTick(() => {
      const faqButtons = document.querySelectorAll('.faq-button');
      faqButtons.forEach(button => {
        button.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          const targetId = button.getAttribute('data-bs-target');
          const targetElement = document.querySelector(targetId);
          
          if (targetElement) {
            const isOpen = targetElement.classList.contains('show');
            
            if (isOpen) {
              // Плавно закрываем элемент
              targetElement.style.maxHeight = targetElement.scrollHeight + 'px';
              
              // Небольшая задержка для начала анимации
              setTimeout(() => {
                targetElement.style.maxHeight = '0px';
              }, 10);
              
              // Убираем класс show после завершения анимации
              setTimeout(() => {
                targetElement.classList.remove('show');
                targetElement.style.maxHeight = '';
              }, 300);
              
              button.classList.add('collapsed');
              button.setAttribute('aria-expanded', 'false');
            } else {
              // Плавно открываем элемент
              targetElement.classList.add('show');
              targetElement.style.maxHeight = '0px';
              
              // Небольшая задержка для начала анимации
              setTimeout(() => {
                targetElement.style.maxHeight = targetElement.scrollHeight + 'px';
              }, 10);
              
              // Убираем inline стили после завершения анимации
              setTimeout(() => {
                targetElement.style.maxHeight = '';
              }, 300);
              
              button.classList.remove('collapsed');
              button.setAttribute('aria-expanded', 'true');
            }
          }
        });
      });
    });
  }
};
</script>

<style scoped>
.folder-structure {
  font-family: 'Arial', sans-serif;
}

.folder-item {
  margin-bottom: 10px;
}

.folder-header {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #344767;
  transition: background-color 0.3s;
}

.folder-header:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.document-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.document-item:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.fa-folder, .fa-folder-open {
  color: #ffc107;
}

.fa-file-pdf {
  color: rgb(204,20,20);
}

.fa-file-word {
  color: rgb(28,102,228);
}

.fa-file-powerpoint {
  color: rgb(217,101,72);
}

.fa-file-excel {
  color: rgb(35,148,94);
}

.fa-file-audio {
  color: rgb(23,162,184);
}

.fa-file-video {
  color: rgb(220,53,69);
}

.fa-file-image {
  color: rgb(40,167,69);
}

.badge {
  font-size: 0.65em;
}

.fixed-text-container {
  width: 60rem; /* Установите фиксированную ширину */
  overflow: hidden; /* Скрыть переполнение */
  text-overflow: ellipsis; /* Добавить многоточие для длинного текста */
  white-space: nowrap; /* Запретить перенос строк */
}

.highlight {
  background-color: #d1e7dd; /* Цвет фона для подсветки */
}
.btn-info {
  background-color: #173376;
  border-color: #7b7b7b;
}

/* Стили для FAQ блоков */
.faq-container {
  margin-bottom: 2rem;
}

.faq-header {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.faq-header h4 {
  color: white !important;
}

.faq-header .fas {
  color: white !important;
}

.faq-content {
  padding: 0;
}

.faq-block {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin-bottom: 15px;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
  overflow: hidden;
}

.faq-block:hover {
  border-color: #dee2e6;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.faq-header-item {
  margin: 0;
}

.faq-button {
  width: 100%;
  padding: 20px;
  background: none;
  border: none;
  text-align: left;
  font-weight: 600;
  font-size: 0.9rem;
  color: #344767;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  position: relative;
}

.faq-button:hover {
  background-color: #e7f3ff;
  color: #007bff;
}

.faq-button:not(.collapsed) {
  background-color: #e7f3ff;
  color: #007bff;
  border-bottom: 1px solid #dee2e6;
}

.faq-button::after {
  content: '\f107';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  right: 20px;
  transition: transform 0.3s ease;
}

.faq-button:not(.collapsed)::after {
  transform: rotate(180deg);
}

.faq-collapse {
  background-color: #ffffff;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease-in-out;
}

.faq-collapse.show {
  max-height: 500px; /* Достаточно для любого контента */
}

.faq-body {
  padding: 20px;
  border-top: 1px solid #f8f9fa;
  line-height: 1.6;
}

.faq-body p {
  margin-bottom: 15px;
  color: #495057;
}

.faq-body ul {
  margin-bottom: 15px;
  padding-left: 20px;
}

.faq-body li {
  margin-bottom: 8px;
  color: #6c757d;
}

/* Иконки в FAQ */
.faq-button .fas {
  color: #6c757d;
  transition: color 0.3s ease;
}

.faq-button:hover .fas,
.faq-button:not(.collapsed) .fas {
  color: #007bff;
}

</style>
