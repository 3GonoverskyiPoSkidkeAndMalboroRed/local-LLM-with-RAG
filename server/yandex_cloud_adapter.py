"""
Yandex Cloud API Adapter для интеграции с YandexGPT и Embeddings API.
Этот модуль обеспечивает единую точку взаимодействия с облачными сервисами Yandex.
"""

import os
import asyncio
import aiohttp
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class YandexCloudConfig:
    """Конфигурация для работы с Yandex Cloud API"""
    api_key: str
    folder_id: str
    llm_model: str = "yandexgpt"
    embedding_model: str = "text-search-doc"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 30
    base_url: str = "https://llm.api.cloud.yandex.net"
    
    @classmethod
    def from_env(cls) -> 'YandexCloudConfig':
        """Создание конфигурации из переменных окружения"""
        api_key = os.getenv("YANDEX_API_KEY")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
        
        if not api_key:
            raise ValueError("YANDEX_API_KEY environment variable is required")
        if not folder_id:
            raise ValueError("YANDEX_FOLDER_ID environment variable is required")
            
        return cls(
            api_key=api_key,
            folder_id=folder_id,
            llm_model=os.getenv("YANDEX_LLM_MODEL", "yandexgpt"),
            embedding_model=os.getenv("YANDEX_EMBEDDING_MODEL", "text-search-doc"),
            max_tokens=int(os.getenv("YANDEX_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("YANDEX_TEMPERATURE", "0.1")),
            timeout=int(os.getenv("YANDEX_TIMEOUT", "30")),
            base_url=os.getenv("YANDEX_BASE_URL", "https://llm.api.cloud.yandex.net")
        )

@dataclass
class YandexCloudMetrics:
    """Метрики использования Yandex Cloud API"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    average_response_time: float = 0.0
    last_error: Optional[str] = None
    last_request_time: Optional[datetime] = None
    
    def update_request(self, success: bool, duration: float, tokens: int = 0, error: str = None):
        """Обновление метрик после запроса"""
        self.total_requests += 1
        self.last_request_time = datetime.now()
        
        if success:
            self.successful_requests += 1
            self.total_tokens_used += tokens
        else:
            self.failed_requests += 1
            self.last_error = error
            
        # Обновляем среднее время ответа
        if self.total_requests == 1:
            self.average_response_time = duration
        else:
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1) + duration) 
                / self.total_requests
            )

class YandexCloudError(Exception):
    """Базовый класс для ошибок Yandex Cloud API"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}

class YandexCloudAuthError(YandexCloudError):
    """Ошибка аутентификации"""
    pass

class YandexCloudRateLimitError(YandexCloudError):
    """Ошибка превышения лимита запросов"""
    pass

class YandexCloudTimeoutError(YandexCloudError):
    """Ошибка таймаута"""
    pass

class YandexCloudAdapter:
    """Адаптер для работы с API Yandex Cloud"""
    
    def __init__(self, config: YandexCloudConfig):
        self.config = config
        self.metrics = YandexCloudMetrics()
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        logger.info(f"Инициализирован YandexCloudAdapter с моделью {config.llm_model}")
    
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        await self.close()
    
    async def _ensure_session(self):
        """Обеспечивает наличие HTTP сессии"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "YandexCloudAdapter/1.0"
                }
            )
            logger.debug("Создана новая HTTP сессия")
    
    async def close(self):
        """Закрытие HTTP сессии"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP сессия закрыта")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Получение заголовков аутентификации с кэшированием токенов"""
        # Для Yandex Cloud API используем API ключи напрямую
        # Но можем кэшировать вычисленные хеши для оптимизации
        
        try:
            from yandex_cache import get_cache
            import hashlib
            
            # Создаем хеш API ключа для кэширования
            api_key_hash = hashlib.sha256(self.config.api_key.encode()).hexdigest()
            
            # Проверяем кэш токенов (для будущего использования с OAuth)
            cache = get_cache()
            cached_token = cache.get_auth_token(api_key_hash)
            
            if cached_token:
                logger.debug("Используем кэшированный токен аутентификации")
                # В будущем здесь можно использовать OAuth токены
                # Пока что используем API ключ напрямую
            
        except ImportError:
            logger.debug("Кэш недоступен для токенов аутентификации")
        
        return {
            "Authorization": f"Api-Key {self.config.api_key}",
            "x-folder-id": self.config.folder_id
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса к Yandex Cloud API с обработкой ошибок и retry
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: API эндпоинт
            data: Данные запроса
            retry_count: Количество попыток повтора
            
        Returns:
            Ответ API в виде словаря
            
        Raises:
            YandexCloudError: При ошибках API
        """
        await self._ensure_session()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_auth_headers()
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"Запрос к {url}, попытка {attempt + 1}/{retry_count + 1}")
                
                async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None
                ) as response:
                    duration = time.time() - start_time
                    response_data = {}
                    
                    try:
                        response_text = await response.text()
                        if response_text:
                            response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Не удалось декодировать JSON ответ: {e}")
                        response_data = {"raw_response": response_text}
                    
                    # Обработка успешного ответа
                    if response.status == 200:
                        tokens_used = self._extract_token_count(response_data)
                        self.metrics.update_request(True, duration, tokens_used)
                        
                        # Записываем метрику в глобальную систему мониторинга
                        try:
                            from yandex_metrics import record_api_call
                            record_api_call(
                                endpoint=endpoint,
                                method=method,
                                duration=duration,
                                success=True,
                                status_code=response.status,
                                tokens_used=tokens_used,
                                request_size=len(json.dumps(data)) if data else 0,
                                response_size=len(response_text) if 'response_text' in locals() else 0
                            )
                        except ImportError:
                            pass  # Система метрик недоступна
                        
                        logger.debug(f"Успешный запрос за {duration:.2f}с, токенов: {tokens_used}")
                        return response_data
                    
                    # Обработка ошибок
                    error_message = self._extract_error_message(response_data, response.status)
                    
                    if response.status == 401:
                        self.metrics.update_request(False, duration, error=error_message)
                        
                        # Записываем метрику ошибки
                        try:
                            from yandex_metrics import record_api_call
                            record_api_call(
                                endpoint=endpoint,
                                method=method,
                                duration=duration,
                                success=False,
                                status_code=response.status,
                                error_type="AuthError",
                                error_message=error_message,
                                request_size=len(json.dumps(data)) if data else 0,
                                response_size=len(response_text) if 'response_text' in locals() else 0
                            )
                        except ImportError:
                            pass
                        
                        raise YandexCloudAuthError(error_message, response.status, response_data)
                    
                    elif response.status == 429:
                        if attempt < retry_count:
                            delay = 2 ** attempt  # Экспоненциальная задержка
                            logger.warning(f"Rate limit, ожидание {delay}с перед повтором")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            self.metrics.update_request(False, duration, error=error_message)
                            
                            # Записываем метрику ошибки rate limit
                            try:
                                from yandex_metrics import record_api_call
                                record_api_call(
                                    endpoint=endpoint,
                                    method=method,
                                    duration=duration,
                                    success=False,
                                    status_code=response.status,
                                    error_type="RateLimitError",
                                    error_message=error_message,
                                    request_size=len(json.dumps(data)) if data else 0,
                                    response_size=len(response_text) if 'response_text' in locals() else 0
                                )
                            except ImportError:
                                pass
                            
                            raise YandexCloudRateLimitError(error_message, response.status, response_data)
                    
                    elif 500 <= response.status < 600:
                        if attempt < retry_count:
                            delay = 2 ** attempt
                            logger.warning(f"Серверная ошибка {response.status}, ожидание {delay}с")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            self.metrics.update_request(False, duration, error=error_message)
                            
                            # Записываем метрику серверной ошибки
                            try:
                                from yandex_metrics import record_api_call
                                record_api_call(
                                    endpoint=endpoint,
                                    method=method,
                                    duration=duration,
                                    success=False,
                                    status_code=response.status,
                                    error_type="ServerError",
                                    error_message=error_message,
                                    request_size=len(json.dumps(data)) if data else 0,
                                    response_size=len(response_text) if 'response_text' in locals() else 0
                                )
                            except ImportError:
                                pass
                            
                            raise YandexCloudError(error_message, response.status, response_data)
                    
                    else:
                        self.metrics.update_request(False, duration, error=error_message)
                        
                        # Записываем метрику общей ошибки
                        try:
                            from yandex_metrics import record_api_call
                            record_api_call(
                                endpoint=endpoint,
                                method=method,
                                duration=duration,
                                success=False,
                                status_code=response.status,
                                error_type="APIError",
                                error_message=error_message,
                                request_size=len(json.dumps(data)) if data else 0,
                                response_size=len(response_text) if 'response_text' in locals() else 0
                            )
                        except ImportError:
                            pass
                        
                        raise YandexCloudError(error_message, response.status, response_data)
            
            except asyncio.TimeoutError as e:
                last_error = f"Таймаут запроса: {str(e)}"
                if attempt < retry_count:
                    logger.warning(f"Таймаут, попытка {attempt + 1}/{retry_count + 1}")
                    await asyncio.sleep(1)
                    continue
                else:
                    duration = time.time() - start_time
                    self.metrics.update_request(False, duration, error=last_error)
                    
                    # Записываем метрику таймаута
                    try:
                        from yandex_metrics import record_api_call
                        record_api_call(
                            endpoint=endpoint,
                            method=method,
                            duration=duration,
                            success=False,
                            error_type="TimeoutError",
                            error_message=last_error,
                            request_size=len(json.dumps(data)) if data else 0
                        )
                    except ImportError:
                        pass
                    
                    raise YandexCloudTimeoutError(last_error)
            
            except aiohttp.ClientError as e:
                last_error = f"Ошибка HTTP клиента: {str(e)}"
                if attempt < retry_count:
                    logger.warning(f"HTTP ошибка, попытка {attempt + 1}/{retry_count + 1}: {e}")
                    await asyncio.sleep(1)
                    continue
                else:
                    duration = time.time() - start_time
                    self.metrics.update_request(False, duration, error=last_error)
                    
                    # Записываем метрику клиентской ошибки
                    try:
                        from yandex_metrics import record_api_call
                        record_api_call(
                            endpoint=endpoint,
                            method=method,
                            duration=duration,
                            success=False,
                            error_type="ClientError",
                            error_message=last_error,
                            request_size=len(json.dumps(data)) if data else 0
                        )
                    except ImportError:
                        pass
                    
                    raise YandexCloudError(last_error)
        
        # Если все попытки исчерпаны
        duration = time.time() - start_time
        self.metrics.update_request(False, duration, error=last_error)
        
        # Записываем метрику исчерпания попыток
        try:
            from yandex_metrics import record_api_call
            record_api_call(
                endpoint=endpoint,
                method=method,
                duration=duration,
                success=False,
                error_type="RetriesExhausted",
                error_message=f"Все попытки исчерпаны. Последняя ошибка: {last_error}",
                request_size=len(json.dumps(data)) if data else 0
            )
        except ImportError:
            pass
        
        raise YandexCloudError(f"Все попытки исчерпаны. Последняя ошибка: {last_error}")
    
    def _extract_token_count(self, response_data: Dict[str, Any]) -> int:
        """Извлечение количества использованных токенов из ответа"""
        # Yandex Cloud может возвращать информацию о токенах в разных форматах
        usage = response_data.get("usage", {})
        if isinstance(usage, dict):
            return usage.get("totalTokens", 0) or usage.get("total_tokens", 0)
        return 0
    
    def _extract_error_message(self, response_data: Dict[str, Any], status_code: int) -> str:
        """Извлечение сообщения об ошибке из ответа API"""
        if isinstance(response_data, dict):
            # Различные форматы ошибок Yandex Cloud
            error = response_data.get("error", {})
            if isinstance(error, dict):
                message = error.get("message") or error.get("description")
                if message:
                    return message
            
            # Альтернативные форматы
            message = response_data.get("message") or response_data.get("detail")
            if message:
                return message
        
        return f"HTTP {status_code}: Неизвестная ошибка API"
    
    async def generate_text(
        self, 
        messages: Union[str, List[Dict[str, str]]], 
        model: str = None,
        use_error_handler: bool = True,
        **kwargs
    ) -> str:
        """
        Генерация текста через YandexGPT API
        
        Args:
            messages: Текст запроса или список сообщений
            model: Модель для использования (по умолчанию из конфигурации)
            use_error_handler: Использовать ли error handler для retry и circuit breaker
            **kwargs: Дополнительные параметры генерации
            
        Returns:
            Сгенерированный текст
        """
        model = model or self.config.llm_model
        
        # Валидация параметров
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        
        # Валидация temperature
        if not 0.0 <= temperature <= 1.0:
            logger.warning(f"Temperature {temperature} вне диапазона [0.0, 1.0], используем {self.config.temperature}")
            temperature = self.config.temperature
        
        # Валидация max_tokens
        if max_tokens <= 0 or max_tokens > 8000:
            logger.warning(f"max_tokens {max_tokens} вне диапазона [1, 8000], используем {self.config.max_tokens}")
            max_tokens = self.config.max_tokens
        
        # Формирование запроса в формате Yandex Cloud
        if isinstance(messages, str):
            # Простой текстовый запрос
            formatted_messages = [
                {
                    "role": "user",
                    "text": messages
                }
            ]
        elif isinstance(messages, list):
            # Список сообщений (для диалогов)
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict) and "role" in msg:
                    # Уже правильный формат
                    if "text" in msg:
                        formatted_messages.append(msg)
                    elif "content" in msg:
                        # Конвертируем из OpenAI формата
                        formatted_messages.append({
                            "role": msg["role"],
                            "text": msg["content"]
                        })
                elif isinstance(msg, str):
                    # Простая строка - считаем пользовательским сообщением
                    formatted_messages.append({
                        "role": "user",
                        "text": msg
                    })
            
            if not formatted_messages:
                raise ValueError("Не удалось обработать список сообщений")
        else:
            raise ValueError(f"Неподдерживаемый тип messages: {type(messages)}")
        
        request_data = {
            "modelUri": f"gpt://{self.config.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": formatted_messages
        }
        
        logger.debug(f"Генерация текста с моделью {model}, temperature={temperature}, max_tokens={max_tokens}")
        
        # Записываем дополнительную информацию о модели в метрики
        model_info = model
        
        try:
            # Используем error handler если включен
            if use_error_handler:
                try:
                    from yandex_error_handler import get_error_handler
                    error_handler = get_error_handler()
                    
                    response = await error_handler.execute_with_retry(
                        self._make_request,
                        f"generate_text({model})",
                        "POST", 
                        "/foundationModels/v1/completion", 
                        request_data
                    )
                    
                    # Обновляем метрику с информацией о модели
                    try:
                        from yandex_metrics import get_metrics_instance
                        metrics = get_metrics_instance()
                        # Обновляем последний вызов с информацией о модели
                        if metrics.api_calls:
                            last_call = metrics.api_calls[-1]
                            last_call.model = model
                    except ImportError:
                        pass
                except ImportError:
                    logger.warning("YandexCloudErrorHandler недоступен, используем базовый retry")
                    response = await self._make_request("POST", "/foundationModels/v1/completion", request_data)
                    
                    # Обновляем метрику с информацией о модели
                    try:
                        from yandex_metrics import get_metrics_instance
                        metrics = get_metrics_instance()
                        if metrics.api_calls:
                            last_call = metrics.api_calls[-1]
                            last_call.model = model
                    except ImportError:
                        pass
            else:
                response = await self._make_request("POST", "/foundationModels/v1/completion", request_data)
                
                # Обновляем метрику с информацией о модели
                try:
                    from yandex_metrics import get_metrics_instance
                    metrics = get_metrics_instance()
                    if metrics.api_calls:
                        last_call = metrics.api_calls[-1]
                        last_call.model = model
                except ImportError:
                    pass
            
            # Извлечение сгенерированного текста из ответа
            result = response.get("result", {})
            alternatives = result.get("alternatives", [])
            
            if alternatives and len(alternatives) > 0:
                message = alternatives[0].get("message", {})
                text = message.get("text", "")
                if text:
                    logger.debug(f"Получен ответ длиной {len(text)} символов")
                    return text.strip()  # Убираем лишние пробелы
            
            logger.warning("Пустой ответ от YandexGPT API")
            return "Извините, не удалось сгенерировать ответ."
            
        except YandexCloudError:
            # Переброс специфичных ошибок Yandex Cloud
            raise
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            # Оборачиваем в YandexCloudError для единообразной обработки
            raise YandexCloudError(f"Неожиданная ошибка при генерации текста: {str(e)}")
    
    async def generate_text_stream(
        self, 
        messages: Union[str, List[Dict[str, str]]], 
        model: str = None,
        **kwargs
    ):
        """
        Потоковая генерация текста через YandexGPT API (для будущего использования)
        
        Args:
            messages: Текст запроса или список сообщений
            model: Модель для использования
            **kwargs: Дополнительные параметры
            
        Yields:
            Части сгенерированного текста
        """
        # TODO: Реализовать потоковую генерацию когда Yandex Cloud добавит поддержку
        # Пока что используем обычную генерацию
        full_text = await self.generate_text(messages, model, **kwargs)
        
        # Имитируем потоковую передачу разбивая на слова
        words = full_text.split()
        for i, word in enumerate(words):
            if i == len(words) - 1:
                yield word
            else:
                yield word + " "
            await asyncio.sleep(0.01)  # Небольшая задержка для имитации потока
    
    async def create_embeddings(
        self, 
        texts: List[str], 
        model: str = None,
        use_error_handler: bool = True
    ) -> List[List[float]]:
        """
        Создание эмбеддингов через Yandex Embeddings API
        
        Args:
            texts: Список текстов для создания эмбеддингов
            model: Модель эмбеддингов (по умолчанию из конфигурации)
            use_error_handler: Использовать ли error handler для retry и circuit breaker
            
        Returns:
            Список векторов эмбеддингов
        """
        model = model or self.config.embedding_model
        
        # Yandex Cloud может иметь ограничения на batch размер
        batch_size = 100  # Предполагаемое ограничение
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            request_data = {
                "modelUri": f"emb://{self.config.folder_id}/{model}",
                "texts": batch_texts
            }
            
            logger.debug(f"Создание эмбеддингов для {len(batch_texts)} текстов")
            
            try:
                # Используем error handler если включен
                if use_error_handler:
                    try:
                        from yandex_error_handler import get_error_handler
                        error_handler = get_error_handler()
                        
                        response = await error_handler.execute_with_retry(
                            self._make_request,
                            f"create_embeddings({model}, {len(batch_texts)} texts)",
                            "POST", 
                            "/foundationModels/v1/textEmbedding", 
                            request_data
                        )
                    except ImportError:
                        logger.warning("YandexCloudErrorHandler недоступен, используем базовый retry")
                        response = await self._make_request("POST", "/foundationModels/v1/textEmbedding", request_data)
                else:
                    response = await self._make_request("POST", "/foundationModels/v1/textEmbedding", request_data)
                
                embeddings = response.get("embeddings", [])
                if not embeddings:
                    logger.warning("Пустой ответ от Embeddings API")
                    # Возвращаем нулевые векторы в случае ошибки
                    embeddings = [[0.0] * 256 for _ in batch_texts]  # Предполагаемая размерность
                
                all_embeddings.extend(embeddings)
                
            except Exception as e:
                logger.error(f"Ошибка создания эмбеддингов для batch {i//batch_size + 1}: {e}")
                # В случае ошибки возвращаем нулевые векторы для этого batch
                all_embeddings.extend([[0.0] * 256 for _ in batch_texts])
        
        logger.debug(f"Создано {len(all_embeddings)} эмбеддингов")
        return all_embeddings
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик использования API"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / self.metrics.total_requests 
                if self.metrics.total_requests > 0 else 0
            ),
            "total_tokens_used": self.metrics.total_tokens_used,
            "average_response_time": self.metrics.average_response_time,
            "last_error": self.metrics.last_error,
            "last_request_time": (
                self.metrics.last_request_time.isoformat() 
                if self.metrics.last_request_time else None
            )
        }
    
    def reset_metrics(self):
        """Сброс метрик"""
        self.metrics = YandexCloudMetrics()
        logger.info("Метрики сброшены")

# Глобальный экземпляр адаптера (будет инициализирован при первом использовании)
_global_adapter: Optional[YandexCloudAdapter] = None

async def get_yandex_adapter() -> YandexCloudAdapter:
    """Получение глобального экземпляра YandexCloudAdapter"""
    global _global_adapter
    
    if _global_adapter is None:
        try:
            config = YandexCloudConfig.from_env()
            _global_adapter = YandexCloudAdapter(config)
            logger.info("Глобальный YandexCloudAdapter инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации YandexCloudAdapter: {e}")
            raise
    
    return _global_adapter

async def close_yandex_adapter():
    """Закрытие глобального адаптера"""
    global _global_adapter
    
    if _global_adapter:
        await _global_adapter.close()
        _global_adapter = None
        logger.info("Глобальный YandexCloudAdapter закрыт")