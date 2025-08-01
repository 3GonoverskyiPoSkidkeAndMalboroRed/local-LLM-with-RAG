<template>
  <router-link 
    class="nav-link nav-link-animated" 
    :to="to" 
    v-bind="$attrs"
    @click="handleClick"
  >
    <span
      class="nav-link-text"
      :class="$store.state.isRTL ? ' me-1' : 'ms-1'"
      >{{ navText }}</span
    >
  </router-link>
</template>
<script>
export default {
  name: "SidenavCollapse",
  props: {
    to: {
      type: [Object, String],
      required: true,
    },
    navText: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isExpanded: false,
    };
  },
  methods: {
    handleClick() {
      // Добавляем эффект клика
      const link = event.currentTarget;
      link.style.transform = 'scale(0.95)';
      setTimeout(() => {
        link.style.transform = '';
      }, 150);
    }
  },
};
</script>

<style scoped>
.nav-link-animated {
  transition: all 0.2s ease-in-out;
  position: relative;
  overflow: hidden;
}

.nav-link-animated:hover {
  transform: translateX(5px);
  background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
}

.nav-link-animated::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.nav-link-animated:hover::before {
  left: 100%;
}

.nav-link-animated:active {
  transform: scale(0.98);
}

.nav-link-text {
  transition: all 0.2s ease-in-out;
}

.nav-link-animated:hover .nav-link-text {
  font-weight: 600;
}
</style>
