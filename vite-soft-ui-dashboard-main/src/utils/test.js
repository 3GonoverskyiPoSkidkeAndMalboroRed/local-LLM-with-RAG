import http from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Настраиваемые метрики
const endpointErrors = new Counter('endpoint_errors');
const endpointRequests = new Counter('endpoint_requests');
const successRate = new Rate('success_rate');
const responseTimes = new Trend('response_times');

// Конфигурация теста
export let options = {
  stages: [
    { duration: '1m', target: 20 },   // Разогрев: постепенно увеличиваем до 20 пользователей
    { duration: '2m', target: 50 },   // Увеличиваем до 50 пользователей
    { duration: '5m', target: 50 },   // Поддерживаем 50 пользователей в течение 5 минут
    { duration: '2m', target: 100 },  // Увеличиваем до 100 пользователей
    { duration: '5m', target: 100 },  // Поддерживаем 100 пользователей в течение 5 минут
    { duration: '2m', target: 0 },    // Постепенное завершение
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],   // Менее 5% запросов должны завершиться неудачно
    http_req_duration: ['p(95)<3000'], // 95% запросов должны завершиться менее чем за 3 секунды
    'success_rate': ['rate>0.95'],    // Успешность выполнения должна быть выше 95%
    'endpoint_errors': ['count<100'],  // Не более 100 ошибок за весь тест
  },
};

// Базовый URL API через Nginx
const baseUrl = 'http://192.168.81.10:8081/api';

// Функция для авторизации пользователя
function getAuthToken() {
  const payload = JSON.stringify({
    login: 'Pavel2',
    password: '123123'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const loginRes = http.post(`${baseUrl}/user/login`, payload, params);
  
  if (loginRes.status === 200) {
    return loginRes.json().auth_key;
  }
  
  return null;
}

// Тестирование эндпоинта
function testEndpoint(token, endpoint, method = 'GET', data = null) {
  endpointRequests.add(1);
  
  const url = `${baseUrl}${endpoint}`;
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  // Добавляем токен авторизации, если он есть
  if (token) {
    params.headers['Authorization'] = `Bearer ${token}`;
  }
  
  const startTime = new Date();
  let response;
  
  // Выполняем запрос в зависимости от метода
  switch(method.toUpperCase()) {
    case 'GET':
      response = http.get(url, params);
      break;
    case 'POST':
      response = http.post(url, data ? JSON.stringify(data) : '', params);
      break;
    case 'PUT':
      response = http.put(url, data ? JSON.stringify(data) : '', params);
      break;
    case 'DELETE':
      response = http.del(url, null, params);
      break;
    default:
      response = http.get(url, params);
  }
  
  // Измеряем время ответа
  const responseTime = new Date() - startTime;
  responseTimes.add(responseTime);
  
  // Проверяем успешность запроса
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response is valid': (r) => r.status < 400,
  });
  
  successRate.add(success);
  
  if (!success) {
    endpointErrors.add(1);
    console.log(`Ошибка при запросе к ${url}: ${response.status} ${response.body}`);
  }
  
  return response;
}

// Основная функция теста
export default function() {
  // Получаем токен авторизации один раз для каждого виртуального пользователя
  const token = getAuthToken();
  
  group('API Endpoints', function() {
    // Тестируем различные эндпоинты
    
    // 1. Получение списка пользователей
    group('Users Endpoint', function() {
      const usersResponse = testEndpoint(token, '/user/users', 'GET');
      
      if (usersResponse.status === 200) {
        // Дополнительные проверки для ответа
        check(usersResponse, {
          'has users array': (r) => Array.isArray(r.json()),
          'users not empty': (r) => r.json().length > 0,
        });
      }
      
      sleep(1);
    });
    
    // 2. Тестирование чата
    group('Chat Endpoint', function() {
      const chatData = {
        question: 'Тестовый вопрос для проверки работы чата',
        department_id: 1
      };
      
      // const chatResponse = testEndpoint(token, '/llm/query-sync', 'POST', chatData); // Удалено - больше не используется
      
      if (chatResponse.status === 200) {
        check(chatResponse, {
          'has answer': (r) => r.json().hasOwnProperty('answer'),
          'answer not empty': (r) => r.json().answer.length > 0,
        });
      }
      
      sleep(3);
    });
    
    // 3. Получение контента
    group('Content Endpoint', function() {
      const contentResponse = testEndpoint(token, '/content', 'GET');
      
      if (contentResponse.status === 200) {
        check(contentResponse, {
          'content is valid': (r) => r.json() !== null,
        });
      }
      
      sleep(1);
    });
    
    // 4. Тестирование тегов
    group('Tags Endpoint', function() {
      const tagsResponse = testEndpoint(token, '/tags', 'GET');
      
      if (tagsResponse.status === 200) {
        check(tagsResponse, {
          'has tags array': (r) => Array.isArray(r.json()),
        });
      }
      
      sleep(1);
    });
  });
  
  // Пауза между итерациями теста
  sleep(Math.random() * 2 + 1);
}

// Функция для выполнения перед началом теста
export function setup() {
  console.log('Начало тестирования API эндпоинтов через Nginx');
  return { startTime: new Date() };
}

// Функция для выполнения после завершения теста
export function teardown(data) {
  const testDuration = (new Date() - data.startTime) / 1000;
  console.log(`Тест завершен. Продолжительность: ${testDuration} секунд`);
}