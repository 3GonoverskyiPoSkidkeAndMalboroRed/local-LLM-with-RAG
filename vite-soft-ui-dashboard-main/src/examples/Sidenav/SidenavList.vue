<template>
  <div
    id="sidenav-collapse-main"
    class="w-300 h-auto collapse navbar-collapse max-height-vh-100 h-100"
  >
    <ul class="navbar-nav bg-white rounded-3 border border-1 border-gray-300">
      <li class="nav-item">
        <sidenav-collapse nav-text="Главная" :to="{ name: 'Dashboard' }">
        </sidenav-collapse>
      </li>
      <li class="nav-item">
        <sidenav-collapse nav-text="Библиотека" :to="{ name: 'Library' }">
        </sidenav-collapse>
      </li>
      <li class="nav-item">
        <sidenav-collapse nav-text="Тесты и анкеты" :to="{ name: 'Quizzes' }">
        </sidenav-collapse>
      </li>
      <li class="nav-item" v-if="isAdmin">
        <sidenav-collapse nav-text="Админская панель" :to="{ name: 'Tables' }">
        </sidenav-collapse>
      </li>
      <li class="nav-item"  >
        <sidenav-collapse nav-text="Обратная связь" :to="{ name: 'Feedback' }">
        </sidenav-collapse>
      </li>
      <li class="nav-item">
        <sidenav-collapse nav-text="Чат" :to="{ name: 'Billing' }">
        </sidenav-collapse>
      </li>

      <!-- <li class="nav-item">
        <sidenav-collapse nav-text="Виртуальная реальность" :to="{ name: 'Virtual Reality' }">
          <template #icon>
            <icon name="virtual-reality" />
          </template>
        </sidenav-collapse>
      </li> -->
      <!-- <li class="nav-item">
        <sidenav-collapse nav-text="Правый интерфейс" :to="{ name: 'Rtl' }">
          <template #icon>
            <icon name="rtl-page" />
          </template>
        </sidenav-collapse>
      </li> -->
      <li class="mt-3 nav-item">
        <h6
          class="text-xs ps-4 text-uppercase font-weight-bolder "
          :class="$store.state.isRTL ? 'me-4' : 'ms-2'"
        >Аккаунт</h6>
      </li>
      <li class="nav-item">
        <sidenav-collapse nav-text="Профиль" :to="{ name: 'Profile' }">
        </sidenav-collapse>
      </li>

      <!-- <li class="nav-item">
        <sidenav-collapse nav-text="Регистрация" :to="{ name: 'Sign Up' }">
          <template #icon>
            <icon name="sign-up" />
          </template>
        </sidenav-collapse>
      </li> -->
      <li class="nav-item">
        <a class="nav-link nav-link-animated" href="#" @click.prevent="handleLogout">
          <span class="nav-link-text ms-1">Выход</span>
        </a>
      </li>
    </ul>
  </div>
  <div class="pt-3 mx-3 mt-3 sidenav-footer">
   

  </div>
</template>
<script>
import SidenavCollapse from "./SidenavCollapse.vue";
import SidenavCard from "./SidenavCard.vue";
import { mapActions } from "vuex";
import { useRouter } from "vue-router";

export default {
  name: "SidenavList",
  components: {
    SidenavCollapse,
    SidenavCard,
  },
  props: {
    cardBg: {
      type: String,
      default: ""
    },
  },
  setup() {
    const router = useRouter();
    return { router };
  },
  data() {
    return {
      title: "Vite Soft UI Dashboard",
      controls: "dashboardsExamples",
      isActive: "active",
    };
  },
  computed: {
    isAdmin() {
      return parseInt(localStorage.getItem('role_id')) === 1;
    }
  },
  methods: {
    ...mapActions(['logout']),
    handleLogout() {
      this.logout();
      this.router.push('/sign-in');
    },
    getRoute() {
      const routeArr = this.$route.path.split("/");
      return routeArr[1];
    },
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

.nav-link-animated .nav-link-text {
  transition: all 0.2s ease-in-out;
}

.nav-link-animated:hover .nav-link-text {
  font-weight: 600;
}
</style>
