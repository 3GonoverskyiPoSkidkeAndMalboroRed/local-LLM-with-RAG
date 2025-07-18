/*
=========================================================
* Vite Soft UI Dashboard - v1.0.0
=========================================================
* Product Page: https://creative-tim.com/product/vite-soft-ui-dashboard
* Copyright 2022 Creative Tim (https://www.creative-tim.com)
Coded by www.creative-tim.com
* Licensed under MIT (https://github.com/creativetimofficial/vite-soft-ui-dashboard/blob/556f77210e261adc3ec12197dab1471a1295afd8/LICENSE.md)
=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*/ 

import { createApp } from 'vue'
import App from './App.vue'
import store from "./store";
import router from "./router";
import "./assets/css/nucleo-icons.css";
import "./assets/css/nucleo-svg.css";
import SoftUIDashboard from "./soft-ui-dashboard";

// Подключаем ваш custom.css ПОСЛЕ SoftUIDashboard для большего приоритета
import "./assets/css/custom.css";
import axios from 'axios';
import axiosInstance from './utils/axiosConfig';
import { setupGlobalErrorHandlers } from './utils/errorLogger';
import { clearExpiredCache } from './utils/localStorageCache';

// Устанавливаем глобальный экземпляр Axios
window.axios = axiosInstance;

// Заменяем стандартный axios на настроенный экземпляр
// для использования в компонентах, которые импортируют axios напрямую
axios.defaults.baseURL = axiosInstance.defaults.baseURL;
axios.interceptors.request = axiosInstance.interceptors.request;
axios.interceptors.response = axiosInstance.interceptors.response;

// Устанавливаем глобальные обработчики ошибок
setupGlobalErrorHandlers();

// Очищаем просроченные элементы кэша
clearExpiredCache();

createApp(App)
    .use(store)
    .use(router)
    .use(SoftUIDashboard)
    .mount('#app')
