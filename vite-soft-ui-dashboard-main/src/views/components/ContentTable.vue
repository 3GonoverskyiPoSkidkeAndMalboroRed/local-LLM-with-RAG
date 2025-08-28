<template>
  <div>
    <div class="card mb-4">
      <div class="card-header pb-0 d-flex justify-content-between align-items-center">
      <h6>Таблица контента {{ isAdmin ? '(Режим администратора)' : '' }}</h6>
      <span v-if="isAdmin" class="badge bg-gradient-success">Администратор</span>
    </div>
    <div class="card-body px-0 pt-0 pb-2">
      <div class="table-responsive p-0">
        <table class="table align-items-center mb-0">
          <thead>
            <tr>
              <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Название</th>
              <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Описание</th>
              <th class="text-center text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Отдел</th>
              <th class="text-center text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Уровень доступа</th>
              <th v-if="isAdmin" class="text-center text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Доступность</th>
              <th class="text-center text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="content in contents" :key="content.id">
              <td>
                <div class="d-flex px-2 py-1">
                  <div class="d-flex flex-column justify-content-center">
                    <h6 class="mb-0 text-sm">{{ content.title }}</h6>
                    <p class="text-xs text-secondary mb-0">{{ content.file_path }}</p>
                  </div>
                </div>
              </td>
              <td>
                <p class="text-xs text-secondary mb-0">{{ content.description }}</p>
              </td>
              <td class="align-middle text-center text-sm">
                <p class="text-xs font-weight-bold mb-0">{{ departments[content.department_id] || 'Неизвестный отдел' }}</p>
              </td>
              <td class="align-middle text-center">
                <span class="text-secondary text-xs font-weight-bold">{{ accessLevels[content.access_level] || 'Неизвестный уровень' }}</span>
              </td>
              <td v-if="isAdmin" class="align-middle text-center">
                <span 
                  :class="[
                    'badge', 
                    content.access_level > 1 ? 'bg-gradient-warning' : 'bg-gradient-success'
                  ]"
                >
                  {{ content.access_level > 1 ? 'Ограниченный' : 'Общедоступный' }}
                </span>
              </td>
              <td class="align-middle text-center">
                <div class="d-flex justify-content-center">
                  <button
                    v-if="isDocumentFormat(getFileExtension(content.file_path))"
                    @click="viewDocument(content)"
                    class="btn btn-sm btn-outline-secondary me-2"
                    title="Просмотреть документ"
                  >
                    <i class="fas fa-eye me-1"></i>Просмотр
                  </button>
                  <button
                    @click="downloadDocument(content)"
                    class="btn btn-sm btn-outline-secondary me-2"
                    title="Скачать файл"
                  >
                    <i class="fas fa-download me-1"></i>Скачать
                  </button>
                  <a
                    v-if="isAdmin"
                    href="#"
                    class="btn btn-sm btn-outline-danger"
                    title="Удалить контент"
                    @click.prevent="deleteContent(content.id)"
                  >
                    <i class="fas fa-trash me-1"></i>Удалить
                  </a>
                </div>
              </td>
            </tr>
            <tr v-if="contents.length === 0">
              <td colspan="5" class="text-center py-4">
                <p class="text-secondary mb-0">Контент не найден</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>
  </div>
</template>

<script>
import axiosInstance from '@/utils/axiosConfig';

export default {
  name: "ContentTable",
  data() {
    return {
      contents: [],
      isAdmin: false,
      departments: {
        1: "Клиенты",
        2: "Сервисная служба",
        3: "Отдел Продаж",
        4: "Отдел Методик",
        5: "Админ",
      },
      accessLevels: {
        1: "Базовый",
        2: "Повышенный",
        3: "Админ",
      }
    };
  },
  async created() {
    await this.checkIfAdmin();
    await this.fetchAllContent();
  },
  methods: {
    // Проверка, является ли пользователь администратором
    async checkIfAdmin() {
      try {
        // Получаем данные о пользователе по JWT
        const { data: user } = await axiosInstance.get(`/user/me`);
        
        // Проверяем, является ли пользователь администратором (access_id = 3)
        this.isAdmin = user.access_id === 3;
      } catch (error) {
        console.error('Ошибка при проверке прав администратора:', error);
        this.isAdmin = false;
      }
    },
    
    // Получение всего контента
    async fetchAllContent() {
      try {
        const userId = localStorage.getItem("userId");
        if (!userId) {
          return;
        }
        
        if (this.isAdmin) {
          // Если пользователь - администратор, получаем весь контент
          const response = await axiosInstance.get(`${import.meta.env.VITE_API_URL}/content/all`);
          this.contents = response.data;
        } else {
          // Для обычных пользователей получаем только доступный им контент
          const response = await axiosInstance.get(`${import.meta.env.VITE_API_URL}/content/all`);
          this.contents = response.data;
        }
      } catch (error) {
        console.error('Ошибка при загрузке контента:', error);
        this.contents = [];
      }
    },
    
    // Получение ссылки для скачивания файла
    async getDownloadLink(contentId) {
      try {
        // Получаем токен для скачивания
        const tokenResponse = await axiosInstance.get(`/content/download-token/${contentId}`);
        const downloadToken = tokenResponse.data.download_token;
        return `${import.meta.env.VITE_API_URL}/content/public-download/${contentId}?token=${downloadToken}`;
      } catch (error) {
        console.error("Ошибка при получении токена для скачивания:", error);
        // Fallback к старому методу
        return `${import.meta.env.VITE_API_URL}/content/download-file/${contentId}`;
      }
    },
    
    // Удаление контента
    async deleteContent(contentId) {
      if (confirm('Вы уверены, что хотите удалить этот контент?')) {
        try {
          await axiosInstance.delete(`${import.meta.env.VITE_API_URL}/content/content/${contentId}`);
          this.fetchAllContent(); // Обновляем список контента
        } catch (error) {
          console.error('Ошибка при удалении контента:', error);
          alert('Произошла ошибка при удалении контента');
        }
      }
    },
    
    // Получение расширения файла
    getFileExtension(filePath) {
      return filePath.toLowerCase().split('.').pop();
    },
    
    // Проверка, является ли файл документом для просмотра
    isDocumentFormat(extension) {
      return ['doc', 'docx', 'pdf', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'rtf'].includes(extension);
    },
    
    // Просмотр документа
    async viewDocument(content) {
      try {
        const fileExtension = this.getFileExtension(content.file_path);
        
        // Для PDF файлов открываем напрямую в браузере
        if (fileExtension === 'pdf') {
          // Получаем токен для скачивания
          const tokenResponse = await axiosInstance.get(`/content/download-token/${content.id}`);
          const downloadToken = tokenResponse.data.download_token;
          const directUrl = `${import.meta.env.VITE_API_URL}/content/public-download/${content.id}?token=${downloadToken}`;
          window.open(directUrl, '_blank');
        } else {
          // Для остальных форматов используем Google Docs Viewer
          const viewerUrl = `${import.meta.env.VITE_API_URL}/content/document-viewer/${content.id}`;
          window.open(viewerUrl, '_blank');
        }
      } catch (error) {
        console.error("Ошибка при просмотре документа:", error);
        // Fallback к старому методу
        const viewerUrl = `${import.meta.env.VITE_API_URL}/content/document-viewer/${content.id}`;
        window.open(viewerUrl, '_blank');
      }
    },

    // Скачивание файла с правильной аутентификацией
    async downloadDocument(content) {
      try {
        // Используем axios для скачивания файла с правильной аутентификацией
        const response = await axiosInstance.get(`/content/download-file/${content.id}`, {
          responseType: 'blob' // Важно для скачивания файлов
        });
        
        // Создаем blob URL для скачивания
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        
        // Создаем временную ссылку для скачивания
        const link = document.createElement('a');
        link.href = url;
        link.download = this.getFileName(content.file_path);
        document.body.appendChild(link);
        link.click();
        
        // Очищаем ресурсы
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
      } catch (error) {
        console.error("Ошибка при скачивании документа:", error);
        // Fallback к старому методу с токеном
        try {
          const tokenResponse = await axiosInstance.get(`/content/download-token/${content.id}`);
          const downloadToken = tokenResponse.data.download_token;
          window.location.href = `${import.meta.env.VITE_API_URL}/content/public-download/${content.id}?token=${downloadToken}`;
        } catch (fallbackError) {
          console.error("Ошибка при fallback скачивании:", fallbackError);
        }
      }
    },
    
    // Получение имени файла из пути
    getFileName(filePath) {
      if (!filePath) return 'document';
      const parts = filePath.split('/');
      return parts[parts.length - 1];
    }
  }
};
</script>

<style scoped>
.table th, .table td {
  padding: 12px;
}

.table th {
  font-size: 0.65rem;
}

.table tbody tr:hover {
  background-color: #f8f9fa;
}
</style> 