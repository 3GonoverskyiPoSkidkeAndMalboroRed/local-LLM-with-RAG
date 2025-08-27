<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="card mb-4">
          <div class="card-header pb-0">
            <h6>Система предложений контента</h6>
            <p class="text-sm mb-0">
              <i class="fa fa-info text-info" aria-hidden="true"></i>
              <span class="font-weight-bold">Создавайте предложения для загрузки контента</span>
            </p>
          </div>
          <div class="card-body px-0 pt-0 pb-2">
            <!-- Навигационные вкладки -->
            <ul class="nav nav-tabs" id="proposalTabs" role="tablist">
              <li class="nav-item" role="presentation">
                <button class="nav-link active" id="create-proposal-tab" data-bs-toggle="tab" data-bs-target="#create-proposal" type="button" role="tab" aria-controls="create-proposal" aria-selected="true">
                  Создать предложение
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button class="nav-link" id="my-proposals-tab" data-bs-toggle="tab" data-bs-target="#my-proposals" type="button" role="tab" aria-controls="my-proposals" aria-selected="false">
                  Мои предложения
                </button>
              </li>
              <li class="nav-item" role="presentation" v-if="isReviewer">
                <button class="nav-link" id="review-proposals-tab" data-bs-toggle="tab" data-bs-target="#review-proposals" type="button" role="tab" aria-controls="review-proposals" aria-selected="false">
                  Рассмотрение предложений
                </button>
              </li>
            </ul>
            
            <div class="tab-content" id="proposalTabsContent">
              <!-- Вкладка создания предложения -->
              <div class="tab-pane fade show active" id="create-proposal" role="tabpanel" aria-labelledby="create-proposal-tab">
                <div class="p-4">
                  <form @submit.prevent="createProposal">
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label for="title" class="form-label">Название контента *</label>
                        <input type="text" class="form-control" id="title" v-model="proposalForm.title" required>
                      </div>
                      <div class="col-md-6 mb-3">
                        <label for="access_level" class="form-label">Уровень доступа *</label>
                        <select class="form-select" id="access_level" v-model="proposalForm.access_level" required>
                          <option value="">Выберите уровень доступа</option>
                          <option v-for="access in accessLevels" :key="access.id" :value="access.id">
                            {{ access.access_name }}
                          </option>
                        </select>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label for="tag_id" class="form-label">Тег (необязательно)</label>
                        <select class="form-select" id="tag_id" v-model="proposalForm.tag_id">
                          <option value="">Без тега</option>
                          <option v-for="tag in tags" :key="tag.id" :value="tag.id">
                            {{ tag.tag_name }}
                          </option>
                        </select>
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">Отдел</label>
                        <input type="text" class="form-control" :value="userDepartment" readonly>
                        <small class="text-muted">Отдел заполняется автоматически</small>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-12 mb-3">
                        <label for="description" class="form-label">Описание</label>
                        <textarea class="form-control" id="description" rows="3" v-model="proposalForm.description" placeholder="Опишите содержание документа..."></textarea>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-12 mb-3">
                        <label for="file" class="form-label">Файл *</label>
                        <input type="file" class="form-control" id="file" @change="handleFileUpload" required>
                        <small class="text-muted">Выберите файл для загрузки</small>
                      </div>
                    </div>
                    <button type="submit" class="btn btn-info" :disabled="isSubmitting">
                      <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      {{ isSubmitting ? 'Отправка...' : 'Отправить предложение' }}
                    </button>
                  </form>
                  
                  <div v-if="message" :class="['alert', messageStatus ? 'alert-success' : 'alert-danger', 'mt-3']">
                    {{ message }}
                  </div>
                </div>
              </div>
              
              <!-- Вкладка моих предложений -->
              <div class="tab-pane fade" id="my-proposals" role="tabpanel" aria-labelledby="my-proposals-tab">
                <div class="p-4">
                  <div class="table-responsive">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Название</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Отдел</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Статус</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Дата создания</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="proposal in myProposals" :key="proposal.id">
                          <td>
                            <div class="d-flex px-2 py-1">
                              <div class="d-flex flex-column justify-content-center">
                                <h6 class="mb-0 text-sm">{{ proposal.title }}</h6>
                                <p class="text-xs text-secondary mb-0">{{ proposal.description }}</p>
                              </div>
                            </div>
                          </td>
                          <td>
                            <p class="text-xs font-weight-bold mb-0">{{ proposal.department_name }}</p>
                          </td>
                          <td>
                            <span :class="getStatusBadgeClass(proposal.status)">
                              {{ getStatusText(proposal.status) }}
                            </span>
                          </td>
                          <td>
                            <p class="text-xs font-weight-bold mb-0">{{ formatDate(proposal.created_at) }}</p>
                          </td>
                          <td>
                            <button class="btn btn-sm btn-outline-info" @click="viewProposal(proposal)">
                              Просмотр
                            </button>
                            <button v-if="proposal.status === 'pending'" class="btn btn-sm btn-outline-danger ms-1" @click="deleteProposal(proposal.id)">
                              Удалить
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  
                  <div v-if="myProposals.length === 0" class="text-center py-4">
                    <p class="text-muted">У вас пока нет предложений</p>
                  </div>
                </div>
              </div>
              
              <!-- Вкладка рассмотрения предложений (только для рецензентов) -->
              <div class="tab-pane fade" id="review-proposals" role="tabpanel" aria-labelledby="review-proposals-tab" v-if="isReviewer">
                <div class="p-4">
                  <div class="table-responsive">
                    <table class="table align-items-center mb-0">
                      <thead>
                        <tr>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Название</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Автор</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Отдел</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Дата создания</th>
                          <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7 ps-2">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="proposal in pendingProposals" :key="proposal.id">
                          <td>
                            <div class="d-flex px-2 py-1">
                              <div class="d-flex flex-column justify-content-center">
                                <h6 class="mb-0 text-sm">{{ proposal.title }}</h6>
                                <p class="text-xs text-secondary mb-0">{{ proposal.description }}</p>
                              </div>
                            </div>
                          </td>
                          <td>
                            <p class="text-xs font-weight-bold mb-0">{{ proposal.proposer_name }}</p>
                          </td>
                          <td>
                            <p class="text-xs font-weight-bold mb-0">{{ proposal.department_name }}</p>
                          </td>
                          <td>
                            <p class="text-xs font-weight-bold mb-0">{{ formatDate(proposal.created_at) }}</p>
                          </td>
                          <td>
                            <button class="btn btn-sm btn-outline-info" @click="viewProposal(proposal)">
                              Просмотр
                            </button>
                            <button class="btn btn-sm btn-outline-success ms-1" @click="approveProposal(proposal.id)">
                              Одобрить
                            </button>
                            <button class="btn btn-sm btn-outline-danger ms-1" @click="rejectProposal(proposal.id)">
                              Отклонить
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  
                  <div v-if="pendingProposals.length === 0" class="text-center py-4">
                    <p class="text-muted">Нет предложений для рассмотрения</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для просмотра предложения -->
    <div class="modal fade" id="proposalModal" tabindex="-1" aria-labelledby="proposalModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="proposalModalLabel">Детали предложения</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-if="selectedProposal">
            <div class="row">
              <div class="col-md-6">
                <h6>Основная информация</h6>
                <p><strong>Название:</strong> {{ selectedProposal.title }}</p>
                <p><strong>Описание:</strong> {{ selectedProposal.description || 'Не указано' }}</p>
                <p><strong>Автор:</strong> {{ selectedProposal.proposer_name }}</p>
                <p><strong>Отдел:</strong> {{ selectedProposal.department_name }}</p>
                <p><strong>Уровень доступа:</strong> {{ selectedProposal.access_name }}</p>
                <p><strong>Тег:</strong> {{ selectedProposal.tag_name || 'Не указан' }}</p>
                <p><strong>Статус:</strong> 
                  <span :class="getStatusBadgeClass(selectedProposal.status)">
                    {{ getStatusText(selectedProposal.status) }}
                  </span>
                </p>
                <p><strong>Дата создания:</strong> {{ formatDate(selectedProposal.created_at) }}</p>
              </div>
              <div class="col-md-6">
                <h6>Файл</h6>
                <p v-if="selectedProposal.file_path">
                  <strong>Файл:</strong> {{ getFileName(selectedProposal.file_path) }}
                  <br>
                  <a :href="`${apiUrl}/proposals/${selectedProposal.id}/download`" class="btn btn-sm btn-outline-info mt-2">
                    Скачать файл
                  </a>
                </p>
                <p v-else class="text-muted">Файл не прикреплен</p>
                
                <div v-if="selectedProposal.review_comment" class="mt-3">
                  <h6>Комментарий рецензента</h6>
                  <p class="text-muted">{{ selectedProposal.review_comment }}</p>
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
  </div>
</template>

<script>
import axios from 'axios';
import * as bootstrap from 'bootstrap';

export default {
  name: 'Proposals',
  data() {
    return {
      proposalForm: {
        title: '',
        description: '',
        access_level: '',
        tag_id: ''
      },
      selectedFile: null,
      isSubmitting: false,
      message: '',
      messageStatus: false,
      
      // Данные для списков
      accessLevels: [],
      tags: [],
      myProposals: [],
      pendingProposals: [],
      
      // Модальное окно
      selectedProposal: null,
      proposalModal: null,
      
      // Права пользователя
      isReviewer: false,
      
      // Данные пользователя
      userInfo: null,
      
      userId: localStorage.getItem('userId') || null,
      
      // API URL
      apiUrl: import.meta.env.VITE_API_URL
    };
  },
  computed: {
    userDepartment() {
      return this.userInfo?.department_name || 'Загрузка...';
    }
  },
  mounted() {
    // Проверка авторизации
    if (!this.userId) {
      this.$router.push('/sign-in');
      return;
    }
    
    this.loadInitialData();
    this.loadMyProposals();
    this.checkUserPermissions();
    
    // Инициализация модального окна
    this.proposalModal = new bootstrap.Modal(document.getElementById('proposalModal'));
  },
  methods: {
    async loadInitialData() {
      try {
        // Загружаем уровни доступа
        const accessResponse = await axios.get(`${import.meta.env.VITE_API_URL}/access-levels`);
        this.accessLevels = accessResponse.data;
        
        // Загружаем теги
        const tagsResponse = await axios.get(`${import.meta.env.VITE_API_URL}/tags`);
        this.tags = tagsResponse.data.tags;
      } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
      }
    },
    
    async checkUserPermissions() {
      try {
        const userResponse = await axios.get(`${import.meta.env.VITE_API_URL}/user/me`);
        this.userInfo = userResponse.data;
        
        // Проверяем, является ли пользователь рецензентом (глава отдела или админ)
        this.isReviewer = this.userInfo.role_id === 1 || this.userInfo.role_id === 3; // 1 - админ, 3 - глава отдела
        
        if (this.isReviewer) {
          this.loadPendingProposals();
        }
      } catch (error) {
        console.error('Ошибка при проверке прав пользователя:', error);
      }
    },
    
    async loadMyProposals() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/proposals/`);
        this.myProposals = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке предложений:', error);
      }
    },
    
    async loadPendingProposals() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/proposals/?status_filter=pending`);
        this.pendingProposals = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке предложений для рассмотрения:', error);
      }
    },
    
    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
    },
    
    async createProposal() {
      if (!this.selectedFile) {
        this.message = 'Пожалуйста, выберите файл';
        this.messageStatus = false;
        return;
      }
      
      this.isSubmitting = true;
      this.message = '';
      
      try {
        const formData = new FormData();
        formData.append('title', this.proposalForm.title);
        formData.append('description', this.proposalForm.description);
        formData.append('access_level', this.proposalForm.access_level);
        formData.append('department_id', this.userInfo.department_id); // Автоматически используем отдел пользователя
        formData.append('tag_id', this.proposalForm.tag_id || '');
        formData.append('file', this.selectedFile);
        
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/proposals/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        this.message = 'Предложение успешно создано и отправлено на рассмотрение!';
        this.messageStatus = true;
        
        // Очищаем форму
        this.proposalForm = {
          title: '',
          description: '',
          access_level: '',
          tag_id: ''
        };
        this.selectedFile = null;
        document.getElementById('file').value = '';
        
        // Обновляем списки
        this.loadMyProposals();
        if (this.isReviewer) {
          this.loadPendingProposals();
        }
        
      } catch (error) {
        this.message = error.response?.data?.detail || 'Ошибка при создании предложения';
        this.messageStatus = false;
        console.error('Ошибка создания предложения:', error);
      } finally {
        this.isSubmitting = false;
      }
    },
    
    viewProposal(proposal) {
      this.selectedProposal = proposal;
      this.proposalModal.show();
    },
    
    async deleteProposal(proposalId) {
      if (!confirm('Вы уверены, что хотите удалить это предложение?')) {
        return;
      }
      
      try {
        await axios.delete(`${import.meta.env.VITE_API_URL}/proposals/${proposalId}`);
        this.loadMyProposals();
        this.message = 'Предложение успешно удалено';
        this.messageStatus = true;
      } catch (error) {
        this.message = error.response?.data?.detail || 'Ошибка при удалении предложения';
        this.messageStatus = false;
        console.error('Ошибка удаления предложения:', error);
      }
    },
    
    async approveProposal(proposalId) {
      try {
        await axios.put(`${import.meta.env.VITE_API_URL}/proposals/${proposalId}/review`, {
          status: 'approved',
          review_comment: 'Предложение одобрено'
        });
        
        this.loadMyProposals();
        this.loadPendingProposals();
        this.message = 'Предложение одобрено';
        this.messageStatus = true;
      } catch (error) {
        this.message = error.response?.data?.detail || 'Ошибка при одобрении предложения';
        this.messageStatus = false;
        console.error('Ошибка одобрения предложения:', error);
      }
    },
    
    async rejectProposal(proposalId) {
      const comment = prompt('Укажите причину отклонения:');
      if (comment === null) return; // Пользователь отменил
      
      try {
        await axios.put(`${import.meta.env.VITE_API_URL}/proposals/${proposalId}/review`, {
          status: 'rejected',
          review_comment: comment
        });
        
        this.loadMyProposals();
        this.loadPendingProposals();
        this.message = 'Предложение отклонено';
        this.messageStatus = true;
      } catch (error) {
        this.message = error.response?.data?.detail || 'Ошибка при отклонении предложения';
        this.messageStatus = false;
        console.error('Ошибка отклонения предложения:', error);
      }
    },
    
    getStatusBadgeClass(status) {
      switch (status) {
        case 'pending':
          return 'badge bg-warning';
        case 'approved':
          return 'badge bg-success';
        case 'rejected':
          return 'badge bg-danger';
        default:
          return 'badge bg-secondary';
      }
    },
    
    getStatusText(status) {
      switch (status) {
        case 'pending':
          return 'На рассмотрении';
        case 'approved':
          return 'Одобрено';
        case 'rejected':
          return 'Отклонено';
        default:
          return 'Неизвестно';
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      return new Date(dateString).toLocaleDateString('ru-RU');
    },
    
    getFileName(filePath) {
      if (!filePath) return '';
      return filePath.split('/').pop();
    }
  }
};
</script>

<style scoped>
.nav-tabs .nav-link {
  color: #495057;
  border: none;
  border-bottom: 2px solid transparent;
}

.nav-tabs .nav-link.active {
  color: #5e72e4;
  border-bottom: 2px solid #5e72e4;
  background: none;
}

.btn-info {
  background-color: #5e72e4;
  border-color: #5e72e4;
}

.btn-info:hover {
  background-color: #4a5fd1;
  border-color: #4a5fd1;
}
</style>
