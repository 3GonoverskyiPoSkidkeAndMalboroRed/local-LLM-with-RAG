<template>
  <transition
    :name="currentTransitionName"
    :mode="currentMode"
    @before-enter="beforeEnter"
    @enter="enter"
    @leave="leave"
    @after-enter="afterEnter"
    @after-leave="afterLeave"
  >
    <slot />
  </transition>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'PageTransition',
  props: {
    transitionName: {
      type: String,
      default: null // Если не указан, будет использоваться из store
    },
    mode: {
      type: String,
      default: null // Если не указан, будет использоваться из store
    },
    duration: {
      type: Number,
      default: null // Если не указан, будет использоваться из store
    }
  },
  computed: {
    ...mapGetters(['getRouteTransition']),
    currentTransitionName() {
      // Приоритет: props -> route-specific -> default
      if (this.transitionName) {
        return this.transitionName;
      }
      
      const route = this.$route;
      return this.getRouteTransition(route.name);
    },
    currentMode() {
      return this.mode || this.$store.state.pageTransition.mode;
    },
    currentDuration() {
      return this.duration || this.$store.state.pageTransition.duration;
    }
  },
  methods: {
    beforeEnter(el) {
      // Начальное состояние
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px) scale(0.9)';
      el.style.filter = 'blur(2px)';
    },
    enter(el, done) {
      const duration = this.currentDuration;
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Плавная анимация с easing
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        
        el.style.opacity = easeOutQuart;
        el.style.transform = `translateY(${30 * (1 - easeOutQuart)}px) scale(${0.9 + 0.1 * easeOutQuart})`;
        el.style.filter = `blur(${2 * (1 - easeOutQuart)}px)`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          done();
        }
      };
      
      requestAnimationFrame(animate);
    },
    leave(el, done) {
      const duration = this.currentDuration * 0.7;
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Плавная анимация с easing
        const easeInQuart = progress * progress * progress * progress;
        
        el.style.opacity = 1 - easeInQuart;
        el.style.transform = `translateY(${-20 * easeInQuart}px) scale(${1 - 0.05 * easeInQuart})`;
        el.style.filter = `blur(${1 * easeInQuart}px)`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          done();
        }
      };
      
      requestAnimationFrame(animate);
    },
    afterEnter(el) {
      // Восстанавливаем стили после анимации
      el.style.opacity = '';
      el.style.transform = '';
      el.style.filter = '';
    },
    afterLeave(el) {
      // Очищаем стили после анимации
      el.style.opacity = '';
      el.style.transform = '';
      el.style.filter = '';
    }
  }
}
</script>

<style scoped>
/* Новый эффект slide-fade как в вашем примере */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.8s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

/* Дополнительные стили для различных типов переходов */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
  filter: blur(2px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
  filter: blur(1px);
}

/* Специальные эффекты для разных направлений */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

.slide-right-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Эффект масштабирования */
.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s ease;
}

.scale-enter-from {
  transform: scale(0.8);
  opacity: 0;
}

.scale-leave-to {
  transform: scale(1.2);
  opacity: 0;
}

/* Эффект вращения */
.rotate-enter-active,
.rotate-leave-active {
  transition: all 0.4s ease;
}

.rotate-enter-from {
  transform: rotate(-180deg) scale(0.8);
  opacity: 0;
}

.rotate-leave-to {
  transform: rotate(180deg) scale(1.2);
  opacity: 0;
}

/* Эффект fade */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Эффект slide-up */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(50px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(-50px);
  opacity: 0;
}

/* Эффект slide-down */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(-50px);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(50px);
  opacity: 0;
}
</style> 