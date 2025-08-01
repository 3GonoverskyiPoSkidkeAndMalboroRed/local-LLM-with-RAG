# Эффекты переходов и анимации

Этот документ описывает все доступные эффекты переходов и анимации в приложении.

## Компоненты анимаций

### 1. PageTransition
Компонент для плавных переходов между страницами.

```vue
<PageTransition>
  <router-view />
</PageTransition>
```

**Пропсы:**
- `transitionName` (String) - название эффекта перехода (по умолчанию: 'page-transition')
- `mode` (String) - режим перехода (по умолчанию: 'out-in')
- `duration` (Number) - длительность анимации в миллисекундах (по умолчанию: 300)

### 2. LoadingSpinner
Компонент индикатора загрузки.

```vue
<LoadingSpinner :is-loading="isLoading" />
```

**Пропсы:**
- `isLoading` (Boolean) - состояние загрузки

### 3. AnimatedButton
Компонент кнопки с эффектами анимации.

```vue
<AnimatedButton 
  variant="primary" 
  size="md" 
  :loading="isLoading"
  @click="handleClick"
>
  Нажми меня
</AnimatedButton>
```

**Пропсы:**
- `variant` (String) - вариант кнопки: 'primary', 'secondary', 'success', 'danger', 'warning', 'info'
- `size` (String) - размер: 'sm', 'md', 'lg'
- `disabled` (Boolean) - отключена ли кнопка
- `loading` (Boolean) - состояние загрузки

## Доступные эффекты переходов

### CSS классы для transition

1. **fade** - плавное появление/исчезновение
2. **slide-up** - скольжение снизу вверх
3. **slide-down** - скольжение сверху вниз
4. **slide-left** - скольжение справа налево
5. **slide-right** - скольжение слева направо
6. **scale** - масштабирование
7. **bounce** - эффект отскока
8. **flip** - переворот
9. **zoom** - увеличение/уменьшение

### Использование:

```vue
<transition name="fade">
  <div v-if="show">Содержимое</div>
</transition>

<transition name="slide-up">
  <div v-if="show">Содержимое</div>
</transition>
```

## Hover эффекты

### CSS классы для hover эффектов

1. **card-hover** - эффект для карточек
2. **btn-hover** - эффект для кнопок
3. **link-hover** - эффект для ссылок

### Использование:

```vue
<div class="card card-hover">
  Содержимое карточки
</div>

<button class="btn btn-primary btn-hover">
  Кнопка
</button>

<a href="#" class="link-hover">
  Ссылка
</a>
```

## Анимации появления

### CSS классы для анимаций

1. **fade-in** - плавное появление
2. **slide-in-left** - появление слева
3. **slide-in-right** - появление справа
4. **pulse** - пульсация
5. **shake** - тряска
6. **loading-spinner** - спиннер загрузки

### Использование:

```vue
<div class="fade-in">
  Появляющийся элемент
</div>

<div class="slide-in-left">
  Элемент, появляющийся слева
</div>

<div class="pulse">
  Пульсирующий элемент
</div>
```

## Утилиты для анимаций

### Задержки анимаций

- `animate-delay-100` - задержка 0.1s
- `animate-delay-200` - задержка 0.2s
- `animate-delay-300` - задержка 0.3s
- `animate-delay-500` - задержка 0.5s

### Длительности анимаций

- `animate-duration-300` - длительность 0.3s
- `animate-duration-500` - длительность 0.5s
- `animate-duration-700` - длительность 0.7s
- `animate-duration-1000` - длительность 1s

### Использование:

```vue
<div class="fade-in animate-delay-200 animate-duration-500">
  Элемент с задержкой и кастомной длительностью
</div>
```

## Навигационные эффекты

### Сайдбар
- Hover эффекты для ссылок навигации
- Анимация иконок при наведении
- Эффект ripple для кнопки выхода

### Навбар
- Анимация кнопки переключения сайдбара
- Hover эффекты для dropdown элементов

## Мобильная адаптация

Все эффекты автоматически адаптируются для мобильных устройств:
- Отключение hover эффектов на сенсорных экранах
- Упрощенные анимации для лучшей производительности
- Оптимизированные переходы

## Производительность

### Рекомендации:

1. Используйте `transform` и `opacity` для анимаций вместо изменения размеров
2. Избегайте анимаций `box-shadow` на мобильных устройствах
3. Используйте `will-change` для элементов с частыми анимациями
4. Ограничивайте количество одновременно анимируемых элементов

### Пример оптимизации:

```css
.optimized-animation {
  will-change: transform, opacity;
  transform: translateZ(0); /* Включает аппаратное ускорение */
}
```

## Кастомизация

### Создание собственных анимаций:

```css
@keyframes custom-animation {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.custom-animation {
  animation: custom-animation 0.5s ease-out;
}
```

### Переопределение стандартных анимаций:

```css
/* Переопределение стандартного fade эффекта */
.fade-enter-active {
  transition: opacity 0.5s ease; /* Увеличиваем длительность */
}
```

## Отладка анимаций

### Chrome DevTools:
1. Откройте DevTools (F12)
2. Перейдите на вкладку "Animations"
3. Воспроизведите анимацию
4. Анализируйте временную шкалу

### Отключение анимаций для тестирования:

```css
/* Отключение всех анимаций */
* {
  animation: none !important;
  transition: none !important;
}
```

## Совместимость

- **Vue 3**: Все компоненты совместимы с Vue 3
- **Браузеры**: Поддержка всех современных браузеров
- **Мобильные**: Оптимизировано для iOS и Android
- **Доступность**: Учитывает настройки `prefers-reduced-motion`

## Примеры использования

### Полный пример страницы с анимациями:

```vue
<template>
  <div class="page-container">
    <!-- Индикатор загрузки -->
    <LoadingSpinner :is-loading="isLoading" />
    
    <!-- Анимированная карточка -->
    <div class="card card-hover fade-in animate-delay-200">
      <div class="card-body">
        <h5 class="card-title">Заголовок</h5>
        <p class="card-text">Содержимое карточки</p>
        
        <!-- Анимированная кнопка -->
        <AnimatedButton 
          variant="primary" 
          :loading="buttonLoading"
          @click="handleAction"
        >
          Действие
        </AnimatedButton>
      </div>
    </div>
    
    <!-- Анимированный список -->
    <transition-group name="slide-up" tag="ul">
      <li v-for="item in items" :key="item.id" class="list-item">
        {{ item.name }}
      </li>
    </transition-group>
  </div>
</template>

<script>
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import AnimatedButton from '@/components/AnimatedButton.vue'

export default {
  components: {
    LoadingSpinner,
    AnimatedButton
  },
  data() {
    return {
      isLoading: false,
      buttonLoading: false,
      items: []
    }
  },
  methods: {
    async handleAction() {
      this.buttonLoading = true
      // Выполнение действия
      await this.performAction()
      this.buttonLoading = false
    }
  }
}
</script>
```

Этот документ поможет разработчикам эффективно использовать все доступные эффекты переходов и анимации в приложении. 