<template>
  <div class="transition-settings">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="fas fa-magic me-2"></i>
          Настройки переходов между страницами
        </h5>
      </div>
      <div class="card-body">
        <!-- Общие настройки -->
        <div class="row mb-4">
          <div class="col-12">
            <h6 class="text-primary mb-3">Общие настройки</h6>
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label">Тип перехода по умолчанию</label>
            <select 
              class="form-select" 
              v-model="defaultTransition"
              @change="updateDefaultTransition"
            >
              <option value="slide-fade">Slide Fade</option>
              <option value="slide-left">Slide Left</option>
              <option value="slide-right">Slide Right</option>
              <option value="slide-up">Slide Up</option>
              <option value="slide-down">Slide Down</option>
              <option value="scale">Scale</option>
              <option value="fade">Fade</option>
              <option value="rotate">Rotate</option>
              <option value="page-transition">Default</option>
            </select>
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label">Режим перехода</label>
            <select 
              class="form-select" 
              v-model="defaultMode"
              @change="updateDefaultTransition"
            >
              <option value="out-in">Out-In</option>
              <option value="in-out">In-Out</option>
            </select>
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label">Длительность (мс)</label>
            <input 
              type="number" 
              class="form-control" 
              v-model="defaultDuration"
              min="100"
              max="2000"
              step="50"
              @change="updateDefaultTransition"
            />
          </div>
        </div>

        <!-- Настройки для конкретных страниц -->
        <div class="row">
          <div class="col-12">
            <h6 class="text-primary mb-3">Настройки для страниц</h6>
            <p class="text-muted small mb-3">
              Выберите специальный тип перехода для каждой страницы
            </p>
          </div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3" v-for="(transition, route) in routeTransitions" :key="route">
            <div class="d-flex align-items-center">
              <div class="flex-grow-1 me-3">
                <label class="form-label small mb-1">{{ getRouteDisplayName(route) }}</label>
                <select 
                  class="form-select form-select-sm" 
                  v-model="routeTransitions[route]"
                  @change="updateRouteTransition(route, $event.target.value)"
                >
                  <option value="">Использовать по умолчанию</option>
                  <option value="slide-fade">Slide Fade</option>
                  <option value="slide-left">Slide Left</option>
                  <option value="slide-right">Slide Right</option>
                  <option value="slide-up">Slide Up</option>
                  <option value="slide-down">Slide Down</option>
                  <option value="scale">Scale</option>
                  <option value="fade">Fade</option>
                  <option value="rotate">Rotate</option>
                </select>
              </div>
              <button 
                class="btn btn-sm btn-outline-secondary"
                @click="previewTransition(routeTransitions[route] || defaultTransition)"
                title="Предварительный просмотр"
              >
                <i class="fas fa-eye"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Кнопки действий -->
        <div class="row mt-4">
          <div class="col-12">
            <div class="d-flex gap-2">
              <button 
                class="btn btn-primary"
                @click="saveSettings"
              >
                <i class="fas fa-save me-2"></i>
                Сохранить настройки
              </button>
              <button 
                class="btn btn-outline-secondary"
                @click="resetToDefaults"
              >
                <i class="fas fa-undo me-2"></i>
                Сбросить к умолчаниям
              </button>
              <button 
                class="btn btn-outline-info"
                @click="showPreview = true"
              >
                <i class="fas fa-play me-2"></i>
                Демонстрация
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно предварительного просмотра -->
    <div class="modal fade" :class="{ show: showPreview }" :style="{ display: showPreview ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Демонстрация переходов</h5>
            <button type="button" class="btn-close" @click="showPreview = false"></button>
          </div>
          <div class="modal-body">
            <TransitionExamples />
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showPreview" @click="showPreview = false"></div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import TransitionExamples from './TransitionExamples.vue';

export default {
  name: 'TransitionSettings',
  components: {
    TransitionExamples
  },
  data() {
    return {
      defaultTransition: 'slide-fade',
      defaultMode: 'out-in',
      defaultDuration: 300,
      routeTransitions: {},
      showPreview: false
    }
  },
  computed: {
    ...mapGetters(['getRouteTransition'])
  },
  created() {
    this.loadSettings();
  },
  methods: {
    ...mapActions(['setPageTransition', 'setRouteTransition']),
    
    loadSettings() {
      const state = this.$store.state;
      this.defaultTransition = state.pageTransition.name;
      this.defaultMode = state.pageTransition.mode;
      this.defaultDuration = state.pageTransition.duration;
      this.routeTransitions = { ...state.routeTransitions };
    },
    
    updateDefaultTransition() {
      this.setPageTransition({
        name: this.defaultTransition,
        mode: this.defaultMode,
        duration: this.defaultDuration
      });
    },
    
    updateRouteTransition(routeName, transitionName) {
      if (transitionName) {
        this.setRouteTransition({ routeName, transitionName });
      } else {
        // Удаляем специальный переход для маршрута
        const newRouteTransitions = { ...this.routeTransitions };
        delete newRouteTransitions[routeName];
        this.routeTransitions = newRouteTransitions;
        
        // Обновляем store
        this.$store.commit('SET_ROUTE_TRANSITION', { routeName, transitionName: null });
      }
    },
    
    getRouteDisplayName(route) {
      const routeNames = {
        'Dashboard': 'Главная',
        'Library': 'Библиотека',
        'Billing': 'Чат',
        'Quizzes': 'Тесты и анкеты',
        'Feedback': 'Обратная связь',
        'Profile': 'Профиль',
        'Tables': 'Админская панель'
      };
      return routeNames[route] || route;
    },
    
    previewTransition(transitionName) {
      // Можно добавить логику предварительного просмотра
      console.log('Preview transition:', transitionName);
    },
    
    saveSettings() {
      // Сохраняем в localStorage для персистентности
      localStorage.setItem('transitionSettings', JSON.stringify({
        defaultTransition: this.defaultTransition,
        defaultMode: this.defaultMode,
        defaultDuration: this.defaultDuration,
        routeTransitions: this.routeTransitions
      }));
      
      // Показываем уведомление
      this.$toast?.success('Настройки переходов сохранены');
    },
    
    resetToDefaults() {
      this.defaultTransition = 'slide-fade';
      this.defaultMode = 'out-in';
      this.defaultDuration = 300;
      this.routeTransitions = {};
      
      this.updateDefaultTransition();
      this.$store.commit('SET_ROUTE_TRANSITION', { routeName: null, transitionName: null });
      
      localStorage.removeItem('transitionSettings');
      this.$toast?.info('Настройки сброшены к умолчаниям');
    }
  }
}
</script>

<style scoped>
.transition-settings {
  padding: 20px;
}

.modal.show {
  background-color: rgba(0, 0, 0, 0.5);
}

.form-select, .form-control {
  transition: all 0.2s ease;
}

.form-select:focus, .form-control:focus {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.btn {
  transition: all 0.2s ease;
}

.btn:hover {
  transform: translateY(-1px);
}
</style> 