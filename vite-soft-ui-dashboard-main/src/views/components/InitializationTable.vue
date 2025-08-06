<template>
  <div>
    <!-- Навигация по подвкладкам -->
    <ul class="nav nav-pills mb-3" id="llmTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link active" id="init-rag-tab" data-bs-toggle="pill" data-bs-target="#init-rag" type="button" role="tab" aria-controls="init-rag" aria-selected="true">Инициализация RAG</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="create-dir-tab" data-bs-toggle="pill" data-bs-target="#create-dir" type="button" role="tab" aria-controls="create-dir" aria-selected="false">Создание директории</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="upload-files-tab" data-bs-toggle="pill" data-bs-target="#upload-files" type="button" role="tab" aria-controls="upload-files" aria-selected="false">Загрузка файлов</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="view-files-tab" data-bs-toggle="pill" data-bs-target="#view-files" type="button" role="tab" aria-controls="view-files" aria-selected="false">Просмотр файлов</button>
      </li>
    </ul>
    
    <!-- Содержимое подвкладок -->
    <div class="tab-content" id="llmTabsContent">
      <!-- Вкладка инициализации RAG -->
      <div class="tab-pane fade show active" id="init-rag" role="tabpanel" aria-labelledby="init-rag-tab">
        <div class="card">
          <div class="card-header pb-0">
            <h6>Инициализация RAG системы с Yandex Cloud ML</h6>
            <p class="text-sm mb-0">Создание векторной базы данных для поиска по документам отдела</p>
          </div>
          <div class="card-body">
            <form @submit.prevent="initializeRAG">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="rag-department-select" class="form-label">Отдел для инициализации RAG</label>
                  <select class="form-control" id="rag-department-select" v-model="ragForm.departmentId" required>
                    <option value="">Выберите отдел</option>
                    <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                      {{ dept.department_name }}
                    </option>
                  </select>
                  <small class="text-muted">Выберите отдел для создания RAG системы</small>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">Параметры инициализации</label>
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" v-model="ragForm.forceReload" id="force-reload-rag">
                    <label class="form-check-label" for="force-reload-rag">
                      Принудительная перезагрузка
                    </label>
                    <small class="form-text text-muted d-block">Удалить существующие данные и создать заново</small>
                  </div>
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-12">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="confirm-rag-init" v-model="ragForm.confirm">
                    <label class="form-check-label" for="confirm-rag-init">
                      Я подтверждаю, что хочу инициализировать RAG систему. Это может занять некоторое время.
                    </label>
                  </div>
                </div>
              </div>
              
              <div class="row">
                <div class="col-md-12">
                  <button 
                    type="submit" 
                    class="btn btn-primary" 
                    :disabled="!ragForm.departmentId || !ragForm.confirm || ragInitializing"
                  >
                    <span v-if="ragInitializing" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ ragInitializing ? 'Инициализация RAG...' : 'Инициализировать RAG' }}
                  </button>
                  
                  <button 
                    type="button"
                    class="btn btn-info ms-2" 
                    @click="checkRAGStatus" 
                    :disabled="!ragForm.departmentId"
                  >
                    Проверить статус
                  </button>
                  
                  <button 
                    type="button"
                    class="btn btn-warning ms-2" 
                    @click="resetRAG" 
                    :disabled="!ragForm.departmentId"
                  >
                    Сбросить RAG
                  </button>
                </div>
              </div>
            </form>
            
            <!-- Сообщения о результате -->
            <div v-if="ragMessage" class="alert mt-3" :class="ragStatus ? 'alert-success' : 'alert-danger'">
              {{ ragMessage }}
            </div>
            
            <!-- Статус RAG системы -->
            <div v-if="ragStatusInfo" class="alert alert-info mt-3">
              <h6>Статус RAG системы для отдела "{{ ragStatusInfo.department_name }}":</h6>
              <ul class="mb-0">
                <li>Инициализирована: {{ ragStatusInfo.is_initialized ? 'Да' : 'Нет' }}</li>
                <li>Документов в БД: {{ ragStatusInfo.documents_in_db }}</li>
                <li>Документов в векторной БД: {{ ragStatusInfo.documents_in_vector_store }}</li>
                <li v-if="ragStatusInfo.needs_reinitialization" class="text-warning">
                  ⚠️ Требуется реинициализация (количество документов не совпадает)
                </li>
                <li v-if="ragStatusInfo.last_updated">
                  Последнее обновление: {{ new Date(ragStatusInfo.last_updated).toLocaleString() }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Вкладка создания директории -->
      <div class="tab-pane fade" id="create-dir" role="tabpanel" aria-labelledby="create-dir-tab">
        <form @submit.prevent="createDirectory">
          <div class="row">
            <div class="col-12 mb-3">
              <label for="dir-path" class="form-label">Путь к директории</label>
              <input type="text" class="form-control" id="dir-path" v-model="directoryForm.path" required placeholder="Например: Research/SubFolder">
              <small class="text-muted">Укажите путь, где должна быть создана директория</small>
            </div>
          </div>
          <button type="submit" class="btn btn-info" :disabled="isCreatingDirectory">
            <span v-if="isCreatingDirectory" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isCreatingDirectory ? 'Создание...' : 'Создать директорию' }}
          </button>
          <div v-if="directoryMessage" :class="['alert', directoryStatus ? 'alert-success' : 'alert-danger', 'mt-3']">
            {{ directoryMessage }}
          </div>
        </form>
      </div>
      
      <!-- Вкладка загрузки файлов для чат-бота -->
      <div class="tab-pane fade" id="upload-files" role="tabpanel" aria-labelledby="upload-files-tab">
        <form @submit.prevent="uploadFiles">
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="access-level" class="form-label">Уровень доступа</label>
              <input type="number" class="form-control" id="access-level" v-model="uploadForm.accessLevel" required min="1" placeholder="Например: 1">
            </div>
            <div class="col-md-6 mb-3">
              <label for="upload-department-id" class="form-label">Идентификатор отдела</label>
              <input type="number" class="form-control" id="upload-department-id" v-model="uploadForm.departmentId" required min="1" placeholder="Например: 5">
              <small class="text-muted">Файлы будут автоматически сохранены в папку ContentForDepartment/{ID отдела}</small>
            </div>
          </div>
          <div class="row">
            <div class="col-12 mb-3">
              <label for="upload-files" class="form-label">Файлы для загрузки</label>
              <input type="file" class="form-control" id="upload-files" ref="fileInput" multiple @change="handleFileChange">
              <small class="text-muted">Выберите один или несколько файлов для загрузки</small>
            </div>
          </div>
          <div class="row mb-3" v-if="selectedFiles.length > 0">
            <div class="col-12">
              <p>Выбрано файлов: {{ selectedFiles.length }}</p>
              <ul class="list-group">
                <li class="list-group-item" v-for="(file, index) in selectedFiles" :key="index">
                  {{ file.name }} ({{ formatFileSize(file.size) }})
                </li>
              </ul>
            </div>
          </div>
          <button type="submit" class="btn btn-info" :disabled="isUploading || selectedFiles.length === 0">
            <span v-if="isUploading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isUploading ? 'Загрузка...' : 'Загрузить файлы' }}
          </button>
          <div v-if="uploadMessage" :class="['alert', uploadStatus ? 'alert-success' : 'alert-danger', 'mt-3']">
            {{ uploadMessage }}
          </div>
                 </form>
       </div>
       
       <!-- Вкладка просмотра файлов -->
       <div class="tab-pane fade" id="view-files" role="tabpanel" aria-labelledby="view-files-tab">
         <div class="row">
           <div class="col-md-6 mb-3">
             <label for="view-department-id" class="form-label">Идентификатор отдела</label>
             <input type="number" class="form-control" id="view-department-id" v-model="viewForm.departmentId" min="1" placeholder="Например: 5">
           </div>
           <div class="col-md-6 mb-3 d-flex align-items-end">
             <button @click="loadDepartmentFiles" class="btn btn-info" :disabled="isLoadingFiles">
               <span v-if="isLoadingFiles" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
               {{ isLoadingFiles ? 'Загрузка...' : 'Показать файлы' }}
             </button>
           </div>
         </div>
         
         <div v-if="departmentFiles" class="row">
           <div class="col-12">
             <div class="card">
               <div class="card-header">
                 <h6 class="mb-0">Файлы отдела {{ viewForm.departmentId }}</h6>
               </div>
               <div class="card-body">
                 <div v-if="departmentFiles.exists">
                   <p class="text-success">{{ departmentFiles.message }}</p>
                   <p><strong>Путь:</strong> {{ departmentFiles.path }}</p>
                   <div v-if="departmentFiles.files.length > 0">
                     <h6>Список файлов ({{ departmentFiles.total_files }}):</h6>
                     <div class="table-responsive">
                       <table class="table table-striped">
                         <thead>
                           <tr>
                             <th>Имя файла</th>
                             <th>Размер</th>
                           </tr>
                         </thead>
                         <tbody>
                           <tr v-for="file in departmentFiles.files" :key="file.name">
                             <td>{{ file.name }}</td>
                             <td>{{ file.size_formatted }}</td>
                           </tr>
                         </tbody>
                       </table>
                     </div>
                   </div>
                   <div v-else>
                     <p class="text-muted">В директории нет файлов</p>
                   </div>
                 </div>
                 <div v-else>
                   <p class="text-warning">{{ departmentFiles.message }}</p>
                 </div>
               </div>
             </div>
           </div>
         </div>
         
         <div v-if="viewMessage" :class="['alert', viewStatus ? 'alert-success' : 'alert-danger', 'mt-3']">
           {{ viewMessage }}
         </div>
       </div>
     </div>
   </div>

  
</template>

<script>
import axios from 'axios';
import * as bootstrap from 'bootstrap';

export default {
  name: 'LLMInitialization',
  data() {
    return {
      // Данные для инициализации RAG
      ragForm: {
        departmentId: '',
        forceReload: false,
        confirm: false
      },
      ragInitializing: false,
      ragMessage: '',
      ragStatus: false,
      ragStatusInfo: null,
      departments: [], // Список отделов
      
      // Данные для создания директории
      directoryForm: {
        path: ''
      },
      directoryMessage: '',
      directoryStatus: false,
      isCreatingDirectory: false,
      
             // Данные для загрузки файлов
       uploadForm: {
         accessLevel: 1,
         departmentId: 1
       },
       selectedFiles: [],
       uploadMessage: '',
       uploadStatus: false,
       isUploading: false,
       
       // Данные для просмотра файлов
       viewForm: {
         departmentId: 5
       },
       departmentFiles: null,
       viewMessage: '',
       viewStatus: false,
       isLoadingFiles: false
    };
  },
  methods: {
    // Методы для работы с RAG
    async initializeRAG() {
      if (!this.ragForm.departmentId) {
        this.ragMessage = 'Выберите отдел для инициализации';
        this.ragStatus = false;
        return;
      }
      
      if (!this.ragForm.confirm) {
        this.ragMessage = 'Пожалуйста, подтвердите инициализацию';
        this.ragStatus = false;
        return;
      }
      
      try {
        this.ragInitializing = true;
        this.ragMessage = '';
        
        const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-rag/initialize`, {
          department_id: this.ragForm.departmentId,
          force_reload: this.ragForm.forceReload
        });
        
        this.ragMessage = response.data.message;
        this.ragStatus = response.data.success;
        
        if (response.data.success) {
          this.ragForm.confirm = false;
          // Автоматически проверяем статус через несколько секунд
          setTimeout(() => {
            this.checkRAGStatus();
          }, 3000);
        }
        
      } catch (error) {
        console.error('Ошибка при инициализации RAG:', error);
        this.ragMessage = error.response?.data?.detail || 'Ошибка при инициализации RAG';
        this.ragStatus = false;
      } finally {
        this.ragInitializing = false;
      }
    },
    
    async checkRAGStatus() {
      if (!this.ragForm.departmentId) {
        this.ragMessage = 'Выберите отдел для проверки статуса';
        this.ragStatus = false;
        return;
      }
      
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/yandex-rag/status/${this.ragForm.departmentId}`);
        
        this.ragStatusInfo = response.data;
        this.ragMessage = 'Статус RAG системы обновлен';
        this.ragStatus = true;
        
      } catch (error) {
        console.error('Ошибка при проверке статуса RAG:', error);
        this.ragMessage = error.response?.data?.detail || 'Ошибка при проверке статуса RAG';
        this.ragStatus = false;
        this.ragStatusInfo = null;
      }
    },
    
    async resetRAG() {
      if (!this.ragForm.departmentId) {
        this.ragMessage = 'Выберите отдел для сброса RAG';
        this.ragStatus = false;
        return;
      }
      
      if (!confirm('Вы уверены, что хотите сбросить RAG систему для этого отдела? Это удалит всю векторную базу данных.')) {
        return;
      }
      
      try {
        const response = await axios.delete(`${import.meta.env.VITE_API_URL}/api/yandex-rag/reset/${this.ragForm.departmentId}`);
        
        this.ragMessage = response.data.message;
        this.ragStatus = response.data.success;
        this.ragStatusInfo = null;
        
      } catch (error) {
        console.error('Ошибка при сбросе RAG:', error);
        this.ragMessage = error.response?.data?.detail || 'Ошибка при сбросе RAG';
        this.ragStatus = false;
      }
    },
    
    // Метод для создания директории
    async createDirectory() {
      this.isCreatingDirectory = true;
      this.directoryMessage = 'Создание директории...';
      this.directoryStatus = true;
      
      try {
        const dirPath = this.directoryForm.path.trim();
        
        if (!dirPath) {
          this.directoryMessage = 'Путь директории не может быть пустым';
          this.directoryStatus = false;
          this.isCreatingDirectory = false;
          return;
        }
        
        // Отладочный вывод
        console.log('Отправляемые данные на эндпоинт /create, путь директории:', dirPath);
        
        // Используем параметры запроса вместо JSON-тела
        const response = await axios.post(`${import.meta.env.VITE_API_URL}/directory/create?directory_path=${encodeURIComponent(dirPath)}`);
        
        this.directoryMessage = 'Директория успешно создана!';
        this.directoryStatus = true;
        
        // Очистка формы после успешного создания
        this.directoryForm.path = '';
      } catch (error) {
        this.directoryMessage = 'Ошибка создания директории: ' + (error.response?.data?.detail || error.message);
        this.directoryStatus = false;
        console.error('Ошибка создания директории:', error);
      } finally {
        this.isCreatingDirectory = false;
      }
    },
    
    // Метод для обработки выбора файлов
    handleFileChange(event) {
      this.selectedFiles = Array.from(event.target.files);
    },
    
    // Метод для форматирования размера файла
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Байт';
      
      const k = 1024;
      const sizes = ['Байт', 'КБ', 'МБ', 'ГБ'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Метод для загрузки файлов
    async uploadFiles() {
      if (this.selectedFiles.length === 0) {
        this.uploadMessage = 'Пожалуйста, выберите файлы для загрузки';
        this.uploadStatus = false;
        return;
      }
      
      this.isUploading = true;
      this.uploadMessage = 'Загрузка файлов...';
      this.uploadStatus = true;
      
      try {
        const formData = new FormData();
        
        // Добавляем все выбранные файлы в FormData
        this.selectedFiles.forEach(file => {
          formData.append('files', file);
        });
        
        // Формируем URL с query-параметрами
        let url = `${import.meta.env.VITE_API_URL}/content/upload-files`;
        const params = new URLSearchParams();
        
        params.append('access_level', this.uploadForm.accessLevel.toString());
        params.append('department_id', this.uploadForm.departmentId.toString());
        
        // Добавляем параметры к URL
        url += '?' + params.toString();
        
        console.log('Отправка запроса на URL:', url);
        console.log('ID отдела:', this.uploadForm.departmentId);
        
        // Отправляем запрос на сервер
        const response = await axios.post(
          url,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        this.uploadMessage = `Файлы успешно загружены в папку ContentForDepartment/${this.uploadForm.departmentId}! (${this.selectedFiles.length} файл(ов))`;
        this.uploadStatus = true;
        
        // Очищаем форму после успешной загрузки
        this.selectedFiles = [];
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = '';
        }
      } catch (error) {
        this.uploadMessage = 'Ошибка загрузки файлов: ' + (error.response?.data?.detail || error.message);
        this.uploadStatus = false;
        console.error('Ошибка загрузки файлов:', error);
      } finally {
                 this.isUploading = false;
       }
     },
     
     // Метод для загрузки файлов отдела
     async loadDepartmentFiles() {
       if (!this.viewForm.departmentId) {
         this.viewMessage = 'Пожалуйста, укажите ID отдела';
         this.viewStatus = false;
         return;
       }
       
       this.isLoadingFiles = true;
       this.viewMessage = 'Загрузка списка файлов...';
       this.viewStatus = true;
       
       try {
         const response = await axios.get(`${import.meta.env.VITE_API_URL}/content/list-files/${this.viewForm.departmentId}`);
         
         this.departmentFiles = response.data;
         this.viewMessage = 'Список файлов успешно загружен';
         this.viewStatus = true;
       } catch (error) {
         this.viewMessage = 'Ошибка загрузки списка файлов: ' + (error.response?.data?.detail || error.message);
         this.viewStatus = false;
         console.error('Ошибка загрузки файлов:', error);
       } finally {
         this.isLoadingFiles = false;
       }
     },
     
     // Загрузка списка отделов
     async loadDepartments() {
       try {
         const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/departments`);
         this.departments = response.data;
       } catch (error) {
         console.error('Ошибка при загрузке отделов:', error);
         this.ragMessage = 'Ошибка при загрузке списка отделов';
         this.ragStatus = false;
       }
     }
   },
  async mounted() {
    // Инициализация Bootstrap компонентов
    const tabElements = document.querySelectorAll('#llmTabs [data-bs-toggle="pill"]');
    tabElements.forEach(tabElement => {
      new bootstrap.Tab(tabElement);
    });
    
    // Загружаем список отделов
    await this.loadDepartments();
  },
};
</script>

<style scoped>
.nav-pills .nav-link {
  color: #344767;
  border-radius: 0.5rem;
}

.nav-pills .nav-link.active {
  background-color: #17c1e8;
  color: #fff;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.form-label {
  color: #344767;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}
.btn-info {
  background-color: #172d76;
  border-color: #7b7b7b;
  &:hover {
    background-color: #344785;
    border-color: #7b7b7b;
  }
}
</style>
