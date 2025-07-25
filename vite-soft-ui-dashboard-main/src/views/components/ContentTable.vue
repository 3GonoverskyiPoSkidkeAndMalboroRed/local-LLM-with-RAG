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
              <th class="text-secondary opacity-7">Действия</th>
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
                    v-if="isFileSupported(content.file_path)"
                    @click="openOnlyOffice(content)"
                    class="btn btn-sm btn-outline-primary me-2"
                    title="Открыть в OnlyOffice"
                  >
                    <i class="fas fa-eye me-1"></i>Просмотр
                  </button>
                  <a
                    :href="getDownloadLink(content.id)"
                    class="btn btn-sm btn-outline-secondary me-2"
                    title="Скачать файл"
                  >
                    <i class="fas fa-download me-1"></i>Скачать
                  </a>
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
    
    <!-- OnlyOffice Viewer Modal -->
    <OnlyOfficeViewer
      ref="onlyofficeViewer"
      :document-id="selectedDocument.id"
      :document-title="selectedDocument.title"
      :document-description="selectedDocument.description"
      :user-id="currentUserId"
      :user-name="currentUserName"
    />
  </div>
</template>

<script>
import axios from 'axios';
import OnlyOfficeViewer from '../../components/OnlyOfficeViewer.vue';

export default {
  name: "ContentTable",
  components: {
    OnlyOfficeViewer
  },
  data() {
    return {
      contents: [],
      isAdmin: false,
      selectedDocument: {
        id: null,
        title: '',
        description: ''
      },
      currentUserId: 1,
      currentUserName: 'Пользователь',
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
        const userId = localStorage.getItem("userId");
        if (!userId) {
          return;
        }
        
        // Получаем данные о пользователе
        const userResponse = await axios.get(`${import.meta.env.VITE_API_URL}/user/user/${userId}`);
        const user = userResponse.data;
        
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
          const response = await axios.get(`${import.meta.env.VITE_API_URL}/content/all`);
          this.contents = response.data;
        } else {
          // Для обычных пользователей получаем только доступный им контент
          const response = await axios.get(`${import.meta.env.VITE_API_URL}/content/all`);
          this.contents = response.data;
        }
      } catch (error) {
        console.error('Ошибка при загрузке контента:', error);
        this.contents = [];
      }
    },
    
    // Получение ссылки для скачивания файла
    getDownloadLink(contentId) {
      return `${import.meta.env.VITE_API_URL}/content/download-file/${contentId}`;
    },
    
    // Удаление контента
    async deleteContent(contentId) {
      if (confirm('Вы уверены, что хотите удалить этот контент?')) {
        try {
          await axios.delete(`${import.meta.env.VITE_API_URL}/content/content/${contentId}`);
          this.fetchAllContent(); // Обновляем список контента
        } catch (error) {
          console.error('Ошибка при удалении контента:', error);
          alert('Произошла ошибка при удалении контента');
        }
      }
    },
    
    // Проверка поддержки файла OnlyOffice
    isFileSupported(filePath) {
      const supportedExtensions = ['doc', 'docx', 'odt', 'rtf', 'txt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'odp'];
      const extension = filePath.toLowerCase().split('.').pop();
      return supportedExtensions.includes(extension);
    },
    
    // Открытие документа в OnlyOffice
    openOnlyOffice(content) {
      this.selectedDocument = {
        id: content.id,
        title: content.title,
        description: content.description
      };
      
      // Получаем информацию о текущем пользователе
      const userId = localStorage.getItem("userId");
      if (userId) {
        this.currentUserId = parseInt(userId);
      }
      
      // Открываем OnlyOffice viewer
      this.$nextTick(() => {
        this.$refs.onlyofficeViewer.show();
      });
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