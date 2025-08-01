<template>
  <div class="transition-examples">
    <div class="row">
      <div class="col-12">
        <h3 class="mb-4">Примеры переходов между страницами</h3>
        <p class="text-muted">Выберите тип перехода для демонстрации:</p>
      </div>
    </div>
    
    <div class="row mb-4">
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'slide-fade'"
          :class="{ 'btn-primary': currentTransition === 'slide-fade' }"
        >
          Slide Fade
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'slide-left'"
          :class="{ 'btn-primary': currentTransition === 'slide-left' }"
        >
          Slide Left
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'scale'"
          :class="{ 'btn-primary': currentTransition === 'scale' }"
        >
          Scale
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'fade'"
          :class="{ 'btn-primary': currentTransition === 'fade' }"
        >
          Fade
        </button>
      </div>
    </div>
    
    <div class="row">
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'slide-up'"
          :class="{ 'btn-primary': currentTransition === 'slide-up' }"
        >
          Slide Up
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'slide-down'"
          :class="{ 'btn-primary': currentTransition === 'slide-down' }"
        >
          Slide Down
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'rotate'"
          :class="{ 'btn-primary': currentTransition === 'rotate' }"
        >
          Rotate
        </button>
      </div>
      <div class="col-md-3 col-sm-6 mb-3">
        <button 
          class="btn btn-outline-primary w-100" 
          @click="currentTransition = 'page-transition'"
          :class="{ 'btn-primary': currentTransition === 'page-transition' }"
        >
          Default
        </button>
      </div>
    </div>
    
    <div class="row mt-4">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h5>Демонстрация перехода: {{ currentTransition }}</h5>
          </div>
          <div class="card-body">
            <PageTransition :transition-name="currentTransition" mode="out-in">
              <div :key="currentContent" class="demo-content">
                <h4>{{ currentContent }}</h4>
                <p>Это демонстрация перехода типа "{{ currentTransition }}". 
                   Нажмите кнопку ниже, чтобы увидеть анимацию.</p>
                <button class="btn btn-info" @click="changeContent">
                  Сменить контент
                </button>
              </div>
            </PageTransition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PageTransition from './PageTransition.vue'

export default {
  name: 'TransitionExamples',
  components: {
    PageTransition
  },
  data() {
    return {
      currentTransition: 'slide-fade',
      currentContent: 'Контент 1',
      contentIndex: 1
    }
  },
  methods: {
    changeContent() {
      this.contentIndex = this.contentIndex === 1 ? 2 : 1;
      this.currentContent = `Контент ${this.contentIndex}`;
    }
  }
}
</script>

<style scoped>
.transition-examples {
  padding: 20px;
}

.demo-content {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.demo-content h4 {
  margin-bottom: 20px;
  font-weight: 600;
}

.demo-content p {
  margin-bottom: 30px;
  font-size: 16px;
  opacity: 0.9;
}

.btn {
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style> 