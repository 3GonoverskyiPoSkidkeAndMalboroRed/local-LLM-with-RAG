<template>
  <div class="container-fluid mt-4">
    <div class="row">
      <div class="col-12">
        <div class="card mb-4">
          <div class="card-header pb-0">
            <h6>Чат с LLM</h6>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <label class="form-label fw-bold">Режим чата</label>
              
              <!-- RAG режим -->
              <div class="chat-mode-block mb-3">
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="chatMode" id="modeRAG" value="rag" v-model="chatMode">
                  <label class="form-check-label fw-semibold" for="modeRAG">
                    <i class="fas fa-database me-2"></i>
                    С базой знаний (RAG)
                  </label>
                </div>
                <div v-if="chatMode === 'rag'" class="sub-mode-block mt-2">
                  <label class="form-label text-muted small">Режим RAG:</label>
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="ragMode" id="modeRAGOnly" value="ragOnly" v-model="ragMode">
                    <label class="form-check-label" for="modeRAGOnly">
                      Обычный RAG
                    </label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="ragMode" id="modeRAGWeb" value="ragWeb" v-model="ragMode">
                    <label class="form-check-label" for="modeRAGWeb">
                      <i class="fas fa-search me-1"></i>
                      RAG + Поиск в интернете
                    </label>
                  </div>
                </div>
              </div>
              
              <!-- Простой чат -->
              <div class="chat-mode-block">
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="chatMode" id="modeSimple" value="simple" v-model="chatMode">
                  <label class="form-check-label fw-semibold" for="modeSimple">
                    <i class="fas fa-comments me-2"></i>
                    Простой чат
                  </label>
                </div>
                <div v-if="chatMode === 'simple'" class="sub-mode-block mt-2">
                  <label class="form-label text-muted small">Режим простого чата:</label>
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="simpleMode" id="modeGeneration" value="generation" v-model="simpleMode">
                    <label class="form-check-label" for="modeGeneration">
                      Обычная генерация
                    </label>
                  </div>
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="simpleMode" id="modeWebSearch" value="webSearch" v-model="simpleMode">
                    <label class="form-check-label" for="modeWebSearch">
                      <i class="fas fa-search me-1"></i>
                      Поиск в интернете
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Чат -->
            <div class="chat-container mb-4" style="height: 400px; overflow-y: auto; border: 1px solid #eee; border-radius: 10px; padding: 15px;">
              <div v-for="(message, index) in chatMessages" :key="index" class="mb-3">
                <div :class="message.role === 'user' ? 'text-end' : 'text-start'">
                  <div 
                    :class="[
                      'p-3 rounded d-inline-block', 
                      message.role === 'user' 
                        ? 'bg-gradient-info text-white' 
                        : 'bg-gray-100'
                    ]"
                    style="max-width: 80%"
                  >
                    <div v-html="formatMessage(message.content)"></div>
                    
                    <!-- Отображение источников для ответов ассистента в режиме RAG -->
                    <div v-if="message.role === 'assistant' && message.sources && message.sources.length > 0 && chatMode === 'rag' && !message.no_sources_found && !isNoSourcesResponse(message.content)" class="mt-3">
                      <SourceDisplay 
                        :sources="message.sources"
                        :userQuery="message.userQuery || ''"
                        @show-notification="showNotification"
                        @open-source-modal="openSourceModal"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="isLoading" class="text-center">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Загрузка...</span>
                </div>
              </div>
            </div>
            
            <!-- Форма ввода -->
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <div class="input-group">
                    <input 
                      type="text" 
                      class="form-control" 
                      placeholder="Введите ваш вопрос..." 
                      v-model="userMessage"
                      @keyup.enter="sendMessage"
                      :disabled="isLoading"
                    >
                    <button 
                      class="btn btn-info mb-0" 
                      style="background-color: #173376; border-color: #7b7b7b; color: #fff;"
                      @click="sendMessage"
                      :disabled="isLoading || !userMessage.trim()"
                    >
                      <i class="fas fa-paper-plane"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для детальной информации об источнике -->
    <SourceModal 
      :source="selectedSourceForModal"
      :isMainSource="selectedSourceIsMain"
      @show-notification="showNotification"
    />
  </div>
</template>

<script>
import axios from 'axios';
import SourceDisplay from '../components/SourceDisplay.vue';
import SourceModal from '../components/SourceModal.vue';

export default {
  name: "BillingPage",
  components: {
    SourceDisplay,
    SourceModal
  },
  data() {
    return {
      userMessage: "",
      chatMessages: [],
      isLoading: false,
      chatMode: "rag", // По умолчанию используем режим с RAG
      ragMode: "ragOnly", // По умолчанию обычный RAG
      simpleMode: "generation", // По умолчанию обычная генерация для простого чата
      requestInProgress: false, // Флаг для отслеживания текущего запроса
      requestTimeout: null, // Таймер для отмены запроса
      lastRequestTime: 0, // Время последнего запроса
      selectedSourceForModal: null, // Выбранный источник для модального окна
      selectedSourceIsMain: false // Флаг, указывающий, является ли выбранный источник основным
    };
  },
  methods: {
    formatMessage(text) {
      if (!text) return '';
      // Заменяем \n на <br> для сохранения переносов строк
      return text.replace(/\n/g, '<br>');
    },
    
    isNoSourcesResponse(content) {
      // Проверяем, является ли ответ сообщением о том, что источники не найдены
      const noSourcesKeywords = [
        'не найдено релевантной информации',
        'не найдено информации',
        'информация не найдена',
        'источники не найдены',
        'документы не найдены'
      ];
      
      return noSourcesKeywords.some(keyword => 
        content.toLowerCase().includes(keyword.toLowerCase())
      );
    },
    
    showNotification(notification) {
      try {
        // Простая реализация уведомлений
        const alertClass = notification.type === 'success' ? 'alert-success' : 'alert-danger';
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
        alertDiv.innerHTML = `
          <div class="d-flex align-items-center">
            <i class="fas ${notification.type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'} me-2"></i>
            <span>${notification.message}</span>
          </div>
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Автоматически удаляем уведомление через 4 секунды
        setTimeout(() => {
          if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
          }
        }, 4000);
        
        // Логируем для отладки
        console.log(`Уведомление: ${notification.type} - ${notification.message}`);
      } catch (error) {
        console.error('Ошибка при показе уведомления:', error);
        // Fallback - простой alert
        alert(`${notification.type === 'success' ? 'Успех' : 'Ошибка'}: ${notification.message}`);
      }
    },
    
    openSourceModal(source, isMainSource = false) {
      this.selectedSourceForModal = source;
      this.selectedSourceIsMain = isMainSource;
      
      // Проверяем, что Bootstrap доступен
      if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        try {
          const modalElement = document.getElementById('sourceModal');
          if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
          } else {
            console.error('Элемент модального окна не найден');
            this.showNotification({
              type: 'error',
              message: 'Ошибка открытия модального окна'
            });
          }
        } catch (error) {
          console.error('Ошибка при открытии модального окна:', error);
          this.showNotification({
            type: 'error',
            message: 'Не удалось открыть модальное окно'
          });
        }
      } else {
        console.error('Bootstrap Modal не доступен');
        this.showNotification({
          type: 'error',
          message: 'Bootstrap не загружен. Перезагрузите страницу.'
        });
      }
    },
    
    async processHybridRAG(message, departmentId) {
      try {
        // 1. RAG запрос - получаем информацию из документов
        console.log("Выполняем RAG запрос...");
        const ragResponse = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-rag/query`, { 
          department_id: parseInt(departmentId),
          question: message
        }, {
          noRetry: true
        });
        
        const ragData = ragResponse.data;
        const ragAnswer = ragData.answer || 'Информация из документов не найдена.';
        const ragSources = ragData.sources || [];
        const noSourcesFound = ragData.no_sources_found || false;
        
        // 2. Веб-поиск - получаем актуальную информацию из интернета
        console.log("Выполняем веб-поиск...");
        const webResponse = await axios.post(`${import.meta.env.VITE_API_URL}/api/web-search/query`, {
          query: message
        }, {
          noRetry: true
        });
        
        const webData = webResponse.data;
        const webAnswer = webData.success && webData.results && webData.results.length > 0 
          ? webData.results[0].snippet 
          : 'Информация из интернета не найдена.';
        
        // 3. Объединяем и анализируем информацию через ИИ
        console.log("Объединяем и анализируем информацию...");
        const combinedPrompt = `
Запрос пользователя: "${message}"

ИНФОРМАЦИЯ ИЗ ДОКУМЕНТОВ (RAG):
${ragAnswer}

ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА:
${webAnswer}

Пожалуйста, проанализируй обе части информации и предоставь:
1. Комплексный ответ на запрос пользователя, объединив данные из документов и интернета
2. Рекомендации и дополнительные советы по запросу
3. Оценку актуальности и надежности полученной информации

Ответ должен быть структурированным и полезным для пользователя.
        `;
        
        const analysisResponse = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-ai/generate`, {
          prompt: combinedPrompt,
          model: "yandexgpt",
          max_tokens: 2000,
          temperature: 0.7
        }, {
          noRetry: true
        });
        
        const analysisAnswer = analysisResponse.data.text;
        
        // 4. Формируем итоговый ответ
        const finalAnswer = `
🤖 **АНАЛИЗ И РЕКОМЕНДАЦИИ:**

${analysisAnswer}

---

📄 **ИНФОРМАЦИЯ ИЗ ДОКУМЕНТОВ:**
${noSourcesFound ? '⚠️ В документах не найдено релевантной информации.' : ragAnswer}

🌐 **ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА:**
${webAnswer}

${ragSources.length > 0 ? `
📚 **Источники из документов:**
${ragSources.map((source, index) => `${index + 1}. ${source.title || source.filename || 'Без названия'}`).join('\n')}
` : ''}
        `;
        
        // Добавляем итоговый ответ в чат
        this.chatMessages.push({
          role: 'assistant',
          content: finalAnswer,
          sources: ragSources,
          no_sources_found: noSourcesFound,
          userQuery: message,
          hybridMode: true
        });
        
      } catch (error) {
        console.error("Ошибка в гибридном режиме RAG:", error);
        
        const errorMessage = error.response?.data?.detail || 
                           error.response?.data?.error || 
                           error.message || 
                           'Ошибка при обработке гибридного запроса';
        
        this.chatMessages.push({
          role: 'assistant',
          content: `❌ Ошибка в гибридном режиме: ${errorMessage}`,
          userQuery: message
        });
      }
    },
    
    async sendMessage() {
      if (!this.userMessage.trim()) return;
      
      // Защита от слишком частых запросов
      const now = Date.now();
      if (now - this.lastRequestTime < 1000) { // Минимальный интервал между запросами - 1 секунда
        console.warn("Запросы отправляются слишком часто. Пожалуйста, подождите.");
        return;
      }
      
      // Защита от повторных запросов
      if (this.requestInProgress) {
        console.warn("Предыдущий запрос еще обрабатывается. Пожалуйста, подождите.");
        return;
      }
      
      this.lastRequestTime = now;
      this.requestInProgress = true;
      
      const userId = localStorage.getItem("userId");
      const departmentId = localStorage.getItem("departmentId");
      const isAuthenticated = localStorage.getItem("isAuthenticated");
      
      if (!isAuthenticated || isAuthenticated !== "true") {
        console.error("Пользователь не аутентифицирован.");
        this.requestInProgress = false;
        return; // Прекращаем выполнение, если пользователь не аутентифицирован
      }
      
      if (!departmentId) {
        console.error("department_id не найден. Убедитесь, что пользователь вошел в систему.");
        this.requestInProgress = false;
        return; // Прекращаем выполнение, если departmentId отсутствует
      }
      
      console.log("Отправляемые данные:", {
        question: this.userMessage,
        department_id: departmentId
      });
      
      // Добавляем сообщение пользователя в чат
      let userContent = this.userMessage;
      if (this.chatMode === "simple" && this.simpleMode === "webSearch") {
        userContent += ' 🔍 [Поиск в интернете]';
      } else if (this.chatMode === "rag" && this.ragMode === "ragWeb") {
        userContent += ' 🔄 [RAG + Поиск в интернете]';
      }
      
      this.chatMessages.push({
        role: 'user',
        content: userContent
      });
      
      const message = this.userMessage;
      this.userMessage = "";
      this.isLoading = true;
      
      // Устанавливаем таймаут для запроса (2 минуты)
      this.requestTimeout = setTimeout(() => {
        if (this.isLoading) {
          this.isLoading = false;
          this.requestInProgress = false;
          this.chatMessages.push({
            role: 'assistant',
            content: '⏱️ Обработка запроса занимает больше времени, чем ожидалось. Запрос продолжает обрабатываться на сервере, ответ может прийти позже.',
            userQuery: message
          });
        }
      }, 120000);
      
      try {
        let response;
        
        if (this.chatMode === "rag") {
          // Проверяем статус RAG системы перед отправкой запроса
          try {
            const statusResponse = await axios.get(`${import.meta.env.VITE_API_URL}/api/yandex-rag/status/${departmentId}`);
            const ragStatus = statusResponse.data;
            
            if (!ragStatus.is_initialized) {
              this.chatMessages.push({
                role: 'assistant',
                content: `⚠️ RAG система для отдела "${ragStatus.department_name}" не инициализирована. Пожалуйста, сначала инициализируйте RAG систему в разделе "Инициализация RAG".`,
                userQuery: message
              });
              return;
            }
            
            if (ragStatus.documents_in_db === 0) {
              this.chatMessages.push({
                role: 'assistant',
                content: `⚠️ В отделе "${ragStatus.department_name}" нет документов для поиска. Пожалуйста, добавьте документы в базу знаний.`,
                userQuery: message
              });
              return;
            }
          } catch (statusError) {
            console.error("Ошибка при проверке статуса RAG:", statusError);
            this.chatMessages.push({
              role: 'assistant',
              content: '⚠️ Не удалось проверить статус RAG системы. Попробуйте позже.',
              userQuery: message
            });
            return;
          }
          
          if (this.ragMode === "ragWeb") {
            // Гибридный режим: RAG + веб-поиск
            await this.processHybridRAG(message, departmentId);
          } else {
            // Обычный RAG режим
            response = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-rag/query`, { 
              department_id: parseInt(departmentId),
              question: message
            }, {
              noRetry: true
            });
            
            // Добавляем ответ в чат
            this.chatMessages.push({
              role: 'assistant',
              content: response.data.answer || 'Ответ получен, но содержимое пустое.',
              sources: response.data.sources || [],
              no_sources_found: response.data.no_sources_found || false,
              userQuery: message
            });
          }
          
        } else {
          // Простой чат - проверяем режим
          if (this.simpleMode === "webSearch") {
            // Поиск в интернете
            response = await axios.post(`${import.meta.env.VITE_API_URL}/api/web-search/query`, {
              query: message
            }, {
              noRetry: true
            });
            
            // Добавляем ответ в чат
            if (response.data.success && response.data.results && response.data.results.length > 0) {
              const result = response.data.results[0];
              this.chatMessages.push({
                role: 'assistant',
                content: result.snippet || 'Ответ получен, но содержимое пустое.',
                userQuery: message
              });
            } else {
              this.chatMessages.push({
                role: 'assistant',
                content: '🔍 Поиск в интернете не дал результатов. Попробуйте переформулировать запрос.',
                userQuery: message
              });
            }
          } else {
            // Обычная генерация
            response = await axios.post(`${import.meta.env.VITE_API_URL}/api/yandex-ai/generate`, {
              prompt: message,
              model: "yandexgpt-lite",
              max_tokens: 1000,
              temperature: 0.6
            }, {
              noRetry: true
            });
            
            // Добавляем ответ в чат
            this.chatMessages.push({
              role: 'assistant',
              content: response.data.text
            });
          }
        }
      } catch (error) {
        console.error("Ошибка при отправке сообщения:", error);
        
        // Определяем сообщение об ошибке в зависимости от режима чата
        let errorMessage = 'Неизвестная ошибка';
        
        if (this.chatMode === 'rag') {
          // Для Yandex RAG проверяем специфичные поля ошибки
          errorMessage = error.response?.data?.error || 
                        error.response?.data?.detail || 
                        error.message || 
                        'Ошибка при обращении к Yandex RAG';
        } else {
          // Для простого чата с Yandex AI
          errorMessage = error.response?.data?.error || 
                        error.response?.data?.detail || 
                        error.message || 
                        'Ошибка при обращении к Yandex AI';
        }
        
        // Добавляем сообщение об ошибке в чат
        this.chatMessages.push({
          role: 'assistant',
          content: `❌ Произошла ошибка: ${errorMessage}`,
          userQuery: message // Сохраняем запрос пользователя
        });
      } finally {
        // Очищаем таймаут
        if (this.requestTimeout) {
          clearTimeout(this.requestTimeout);
          this.requestTimeout = null;
        }
        
        this.isLoading = false;
        this.requestInProgress = false;
        
        // Прокручиваем чат вниз
        this.$nextTick(() => {
          const chatContainer = document.querySelector('.chat-container');
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        });
      }
    }
  },
  mounted() {
    // Добавляем приветственное сообщение
    this.chatMessages.push({
      role: 'assistant',
      content: 'Здравствуйте! Я ваш ИИ-ассистент. Как я могу вам помочь сегодня?'
    });
  },
  created() {
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated || isAuthenticated !== "true") {
      this.$router.push("/sign-in"); // Перенаправляем на страницу входа
    }
  }
};
</script>

<style scoped>
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Стили для блоков режимов чата */
.chat-mode-block {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
}

.chat-mode-block:hover {
  border-color: #dee2e6;
  background-color: #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.sub-mode-block {
  border-left: 3px solid #007bff;
  padding-left: 15px;
  margin-left: 10px;
  background-color: #ffffff;
  border-radius: 0 6px 6px 0;
  padding: 10px 15px;
  margin-top: 10px;
}

/* Активный режим */
.chat-mode-block:has(.form-check-input:checked) {
  border-color: #007bff;
  background-color: #e7f3ff;
  box-shadow: 0 2px 8px rgba(0,123,255,0.15);
}

/* Стили для иконок */
.chat-mode-block .fas {
  color: #6c757d;
}

.chat-mode-block:has(.form-check-input:checked) .fas {
  color: #007bff;
}
</style>
