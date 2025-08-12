<template>
  <div class="sidenav-container">
    <!-- Overlay для мобильных устройств -->
    <div 
      v-if="isMobile && isOpen" 
      class="sidenav-overlay"
      @click="closeSidenav"
    ></div>
    
    <!-- Основной sidenav -->
    <aside
      id="sidenav-main"
      class="sidenav navbar navbar-vertical navbar-expand-xs border-radius-xl"
      :class="[
        $store.state.isRTL ? 'me-3 rotate-caret' : 'ms-3',
        isMobile ? 'sidenav-mobile' : 'sidenav-desktop',
        isOpen ? 'sidenav-open' : 'sidenav-closed'
      ]"
      :data-color="sidenavActiveBgColors"
    >
      <!-- Header с кнопкой закрытия для мобильных -->
      <div class="sidenav-header d-flex align-items-center justify-content-between">
        <a class="m-0 navbar-brand" href="/">
          <span class="ms-1 font-weight-bold">НПО "СПЕКТРОН"</span>
        </a>
        <button 
          v-if="isMobile"
          class="btn-close sidenav-close-btn"
          @click="closeSidenav"
          aria-label="Закрыть меню"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <hr class="mt-0 horizontal dark" />
      
      <!-- Список навигации -->
      <sidenav-list :card-bg="customClass" @nav-click="handleNavClick" />
      


    </aside>

    <!-- Кнопка открытия меню для мобильных -->
    <button 
      v-if="isMobile && !isOpen"
      class="btn btn-primary sidenav-open-btn"
      @click="openSidenav"
      aria-label="Открыть меню"
    >
      <i class="fas fa-bars"></i>
    </button>
  </div>
</template>



<script>
import SidenavList from "./SidenavList.vue";
import logo from "@/assets/img/logo-ct.png";

export default {
  name: "IndexComponent",
  components: {
    SidenavList,
  },
  props: {
    customClass: {
      type: String,
      default: ""
    },
  },
  data() {
    return {
      logo,
      sidenavActiveBgColors: 'success',
      isOpen: false,
      isMobile: false,
      userName: localStorage.getItem('user_name') || 'Пользователь',
      userRole: localStorage.getItem('role_name') || 'Гость'
    };
  },
  mounted() {
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
    // Открываем меню по умолчанию на десктопе
    if (!this.isMobile) this.isOpen = true;
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobile);
  },
  methods: {
    checkMobile() {
      this.isMobile = window.innerWidth < 992;
      if (!this.isMobile) this.isOpen = true;
      else this.isOpen = false;
    },
    openSidenav() {
      this.isOpen = true;
    },
    closeSidenav() {
      this.isOpen = false;
    },
    handleNavClick() {
      // Автоматически закрывать меню на мобильных после перехода
      if (this.isMobile) this.closeSidenav();
    }
  }
};
</script>

<style scoped>
.sidenav-container {
  position: relative;
}
.sidenav-mobile {
  position: fixed;
  top: 0; left: 0;
  height: 100vh;
  width: 260px;
  z-index: 1050;
  background: #fff;
  transform: translateX(-100%);
  transition: transform 0.3s;
}
.sidenav-open.sidenav-mobile {
  transform: translateX(0);
  box-shadow: 0 0 2rem rgba(0,0,0,0.2);
}
.sidenav-closed.sidenav-mobile {
  transform: translateX(-100%);
}
.sidenav-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3);
  z-index: 1049;
}
.sidenav-open-btn {
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 1100;
}
.sidenav-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
}
@media (min-width: 992px) {
  .sidenav-mobile, .sidenav-open-btn, .sidenav-overlay {
    display: none !important;
  }
  .sidenav-desktop {
    position: sticky;
    top: 0;
    height: 100vh;
    z-index: 100;
    background: #fff;
  }
}
</style>
