<template>
  <sidenav
    v-if="$store.state.showSidenav"
    :custom_class="$store.state.mcolor"
    :class="[
      $store.state.isTransparent,
      $store.state.isRTL ? 'fixed-end' : 'fixed-start',
    ]"
    @sidenav-state="onSidenavState"
  />
  <main
    class="main-content position-relative max-height-vh-100 h-100 border-radius-lg"
    :class="{
      'content-shifted': sidenavMobileOpen,
      'content-overlayed': sidenavMobileOpen
    }"
    :style="$store.state.isRTL ? 'overflow-x: hidden' : ''"
    @click="closeSidenavOnMobile"
  >
    <!-- nav -->
    <navbar
      v-if="$store.state.showNavbar"
      :class="[navClasses]"
      :text-white="$store.state.isAbsolute ? 'text-white opacity-8' : ''"
      :min-nav="navbarMinimize"
    />
    
    <!-- Эффект перехода между страницами -->
    <PageTransition>
      <router-view :key="$route.fullPath" />
    </PageTransition>
    
    <app-footer v-show="$store.state.showFooter" />
    <!-- <configurator
      :toggle="toggleConfigurator"
      :class="[
        $store.state.showConfig ? 'show' : '',
        $store.state.hideConfigButton ? 'd-none' : '',
      ]"
    /> -->
  </main>
  
  <!-- Индикатор загрузки при переходах -->
  <LoadingSpinner :is-loading="isPageLoading" />
</template>
<script>
import Sidenav from "./examples/Sidenav/index.vue";
import Configurator from "@/examples/Configurator.vue";
import Navbar from "@/examples/Navbars/Navbar.vue";
import AppFooter from "@/examples/Footer.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import PageTransition from "@/components/PageTransition.vue";
import { mapMutations, mapActions } from "vuex";

export default {
  name: "App",
  components: {
    Sidenav,
    Configurator,
    Navbar,
    AppFooter,
    LoadingSpinner,
    PageTransition,
  },

  computed: {
    navClasses() {
      return {
        "position-sticky blur shadow-blur mt-4 left-auto top-1 z-index-sticky":
          this.$store.state.isNavFixed,
        "position-absolute px-4 mx-0 w-100 z-index-2":
          this.$store.state.isAbsolute,
        "px-0 mx-4 mt-4": !this.$store.state.isAbsolute,
      };
    },
  },
  beforeMount() {
    this.$store.state.isTransparent = "bg-transparent";
  },
  created() {
    this.restoreAuthentication();
    // Добавляем обработчики событий роутера для управления загрузкой
    this.$router.beforeEach((to, from, next) => {
      this.isPageLoading = true;
      next();
    });
    
    this.$router.afterEach(() => {
      // Небольшая задержка для плавности
      setTimeout(() => {
        this.isPageLoading = false;
      }, 200);
    });
  },
  data() {
    return {
      sidenavMobileOpen: false,
      isPageLoading: false,
    };
  },
  methods: {
    ...mapMutations(["toggleConfigurator", "navbarMinimize"]),
    ...mapActions(["restoreAuthentication"]),
    onSidenavState(isOpen) {
      this.sidenavMobileOpen = isOpen;
    },
    closeSidenavOnMobile() {
      // Закрывать меню при клике вне меню на мобильных
      if (this.sidenavMobileOpen && window.innerWidth < 992) {
        this.sidenavMobileOpen = false;
        // Можно вызвать метод закрытия через $refs, если нужно
      }
    }
  },
};
</script>

<style>
@media (max-width: 991px) {
  .main-content.content-shifted {
    filter: blur(2px);
    pointer-events: none;
    user-select: none;
  }
  .main-content.content-overlayed {
    /* Можно добавить затемнение, если не хотите блюр */
    /* background: rgba(0,0,0,0.1); */
  }
}
@media (min-width: 992px) {
  .main-content {
    margin-left: 260px; /* ширина сайдбара */
    transition: margin-left 0.3s;
  }
}

/* Плавная прокрутка для всего приложения */
html {
  scroll-behavior: smooth;
}

/* Улучшенные переходы для интерактивных элементов */
.btn, .card, .form-control {
  transition: all 0.2s ease-in-out;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}
</style>
