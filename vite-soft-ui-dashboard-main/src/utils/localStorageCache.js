/**
 * Утилита для кэширования данных в localStorage с поддержкой TTL
 */

// Префикс для ключей кэша
const CACHE_PREFIX = 'app_cache_';

// Время жизни кэша по умолчанию (24 часа в миллисекундах)
const DEFAULT_TTL = 24 * 60 * 60 * 1000;

/**
 * Сохраняет данные в кэш
 * @param {string} key - Ключ для сохранения данных
 * @param {any} data - Данные для сохранения
 * @param {number} ttl - Время жизни кэша в миллисекундах
 */
export const setCacheItem = (key, data, ttl = DEFAULT_TTL) => {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    const cacheData = {
      data,
      expires: Date.now() + ttl
    };
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    return true;
  } catch (error) {
    console.error('Ошибка при сохранении данных в кэш:', error);
    return false;
  }
};

/**
 * Получает данные из кэша
 * @param {string} key - Ключ для получения данных
 * @returns {any|null} - Данные из кэша или null, если данные не найдены или истек срок действия
 */
export const getCacheItem = (key) => {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    const cachedItem = localStorage.getItem(cacheKey);
    
    if (!cachedItem) return null;
    
    const { data, expires } = JSON.parse(cachedItem);
    
    // Проверяем, не истек ли срок действия кэша
    if (Date.now() > expires) {
      // Удаляем просроченные данные
      localStorage.removeItem(cacheKey);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Ошибка при получении данных из кэша:', error);
    return null;
  }
};

/**
 * Удаляет данные из кэша
 * @param {string} key - Ключ для удаления данных
 */
export const removeCacheItem = (key) => {
  try {
    const cacheKey = `${CACHE_PREFIX}${key}`;
    localStorage.removeItem(cacheKey);
    return true;
  } catch (error) {
    console.error('Ошибка при удалении данных из кэша:', error);
    return false;
  }
};

/**
 * Очищает все данные кэша
 */
export const clearCache = () => {
  try {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
    return true;
  } catch (error) {
    console.error('Ошибка при очистке кэша:', error);
    return false;
  }
};

/**
 * Очищает просроченные элементы кэша
 */
export const clearExpiredCache = () => {
  try {
    const now = Date.now();
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(CACHE_PREFIX)) {
        try {
          const cachedItem = JSON.parse(localStorage.getItem(key));
          if (cachedItem.expires && now > cachedItem.expires) {
            localStorage.removeItem(key);
          }
        } catch (e) {
          // Если элемент не может быть прочитан, удаляем его
          localStorage.removeItem(key);
        }
      }
    });
    return true;
  } catch (error) {
    console.error('Ошибка при очистке просроченных элементов кэша:', error);
    return false;
  }
};

/**
 * Создает кэшированную версию асинхронной функции
 * @param {Function} fn - Асинхронная функция для кэширования
 * @param {string} keyPrefix - Префикс ключа кэша
 * @param {number} ttl - Время жизни кэша в миллисекундах
 * @returns {Function} - Кэшированная функция
 */
export const createCachedFunction = (fn, keyPrefix, ttl = DEFAULT_TTL) => {
  return async (...args) => {
    // Создаем ключ кэша на основе аргументов функции
    const cacheKey = `${keyPrefix}_${JSON.stringify(args)}`;
    
    // Проверяем, есть ли данные в кэше
    const cachedData = getCacheItem(cacheKey);
    if (cachedData !== null) {
      return cachedData;
    }
    
    // Если данных в кэше нет, вызываем оригинальную функцию
    const result = await fn(...args);
    
    // Сохраняем результат в кэше
    setCacheItem(cacheKey, result, ttl);
    
    return result;
  };
};

// Автоматически очищаем просроченные элементы кэша при загрузке
clearExpiredCache(); 