# Система переходов между страницами

## Обзор

В приложении реализована гибкая система переходов между страницами с использованием Vue.js Transition API. Система поддерживает различные типы анимаций и позволяет настраивать переходы как глобально, так и для отдельных страниц.

## Доступные типы переходов

### 1. Slide Fade (по умолчанию)
```css
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
```

### 2. Slide Left
- Страница входит справа, выходит влево

### 3. Slide Right
- Страница входит слева, выходит вправо

### 4. Slide Up
- Страница входит снизу, выходит вверх

### 5. Slide Down
- Страница входит сверху, выходит вниз

### 6. Scale
- Страница масштабируется при входе и выходе

### 7. Fade
- Простое появление/исчезновение

### 8. Rotate
- Страница вращается при переходе

## Использование

### Базовое использование

Компонент `PageTransition` уже интегрирован в `App.vue`:

```vue
<PageTransition>
  <router-view :key="$route.fullPath" />
</PageTransition>
```

### Настройка через props

```vue
<PageTransition 
  transition-name="slide-fade" 
  mode="out-in" 
  :duration="300"
>
  <router-view />
</PageTransition>
```

### Настройка через Vuex Store

```javascript
// Установка глобальных настроек
this.$store.dispatch('setPageTransition', {
  name: 'slide-fade',
  mode: 'out-in',
  duration: 300
});

// Установка перехода для конкретной страницы
this.$store.dispatch('setRouteTransition', {
  routeName: 'Dashboard',
  transitionName: 'slide-left'
});
```

## Структура файлов

### Основные компоненты

1. **`src/components/PageTransition.vue`** - Основной компонент переходов
2. **`src/components/TransitionExamples.vue`** - Демонстрация переходов
3. **`src/components/TransitionSettings.vue`** - Панель настроек

### Store

Настройки переходов хранятся в Vuex store (`src/store/index.js`):

```javascript
state: {
  pageTransition: {
    name: 'slide-fade',
    mode: 'out-in',
    duration: 300
  },
  routeTransitions: {
    'Dashboard': 'slide-fade',
    'Library': 'slide-left',
    'Billing': 'scale',
    // ...
  }
}
```

## Настройка переходов для разных страниц

### Через админскую панель

1. Перейдите в админскую панель
2. Найдите раздел "Настройки переходов"
3. Выберите тип перехода для каждой страницы
4. Сохраните настройки

### Программно

```javascript
// В компоненте
export default {
  created() {
    // Установить переход для текущей страницы
    this.$store.dispatch('setRouteTransition', {
      routeName: this.$route.name,
      transitionName: 'slide-up'
    });
  }
}
```

## Приоритет настроек

1. **Props компонента** - высший приоритет
2. **Настройки для конкретного маршрута** - из `routeTransitions`
3. **Глобальные настройки** - из `pageTransition`

## Кастомизация

### Добавление нового типа перехода

1. Добавьте CSS стили в `PageTransition.vue`:

```css
.my-transition-enter-active,
.my-transition-leave-active {
  transition: all 0.3s ease;
}

.my-transition-enter-from {
  transform: translateY(100px);
  opacity: 0;
}

.my-transition-leave-to {
  transform: translateY(-100px);
  opacity: 0;
}
```

2. Добавьте опцию в компонент настроек:

```vue
<option value="my-transition">My Transition</option>
```

### Изменение длительности

```javascript
// Глобально
this.$store.dispatch('setPageTransition', { duration: 500 });

// Для конкретного перехода
<PageTransition :duration="800">
  <router-view />
</PageTransition>
```

## Производительность

- Переходы используют CSS transforms для лучшей производительности
- Анимации оптимизированы для 60fps
- Поддержка `will-change` для улучшения производительности

## Совместимость

- Vue.js 3.x
- Vue Router 4.x
- Vuex 4.x
- Поддержка всех современных браузеров

## Отладка

Для отладки переходов используйте Vue DevTools:

1. Откройте Vue DevTools
2. Перейдите на вкладку "Timeline"
3. Фильтруйте по "transition" событиям

## Примеры использования

### Простой переход
```vue
<template>
  <PageTransition>
    <div v-if="show" class="content">
      Содержимое страницы
    </div>
  </PageTransition>
</template>
```

### Условный переход
```vue
<template>
  <PageTransition :transition-name="getTransitionName()">
    <router-view />
  </PageTransition>
</template>

<script>
export default {
  methods: {
    getTransitionName() {
      return this.$route.name === 'Dashboard' ? 'slide-fade' : 'fade';
    }
  }
}
</script>
```

### Анимированный контент
```vue
<template>
  <PageTransition>
    <div :key="$route.fullPath" class="page-content">
      {{ $route.name }}
    </div>
  </PageTransition>
</template>
```

## Заключение

Система переходов предоставляет гибкие возможности для создания плавных и красивых переходов между страницами. Она легко настраивается и расширяется под конкретные потребности проекта. 