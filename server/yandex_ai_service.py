import os
from typing import Dict, Any, Optional
from yandex_cloud_ml_sdk import AsyncYCloudML
import logging

logger = logging.getLogger(__name__)

class YandexAIService:
    def __init__(self):
        # Инициализируем параметры
        self.api_key = None
        self.folder_id = None
        self.ml_client = None
        self._initialized = False
        
        # Настройки моделей по умолчанию (поддержка разных названий переменных)
        self.default_text_model = (
            os.getenv('YANDEX_LLM_MODEL')
            or os.getenv('YANDEX_DEFAULT_MODEL')
            or 'yandexgpt'
        )
        self.default_embeddings_model = (
            os.getenv('YANDEX_EMBEDDING_MODEL')
            or os.getenv('YANDEX_EMBEDDINGS_MODEL')
            or 'text-search-doc'
        )
        self.default_max_tokens = int(os.getenv('YANDEX_MAX_TOKENS', '4000'))
        self.default_temperature = float(os.getenv('YANDEX_TEMPERATURE', '0.6'))

        # Флаги и базовые параметры
        self.use_yandex_cloud = os.getenv('USE_YANDEX_CLOUD', 'true').lower() == 'true'
        
        # Загружаем переменные окружения
        self._load_environment_vars()
        
        # Инициализируем SDK
        self._initialize_sdk()
    
    def _load_environment_vars(self):
        """Загружает переменные окружения"""
        self.api_key = os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')
        
        if not self.api_key:
            logger.warning("YANDEX_API_KEY не установлен. Некоторые функции могут быть недоступны.")
        
        if not self.folder_id:
            logger.warning("YANDEX_FOLDER_ID не установлен. Некоторые функции могут быть недоступны.")
    
    def _initialize_sdk(self):
        """Инициализирует Yandex Cloud ML SDK"""
        if not self.use_yandex_cloud:
            logger.info("USE_YANDEX_CLOUD=false — Yandex Cloud ML SDK не используется")
            self.ml_client = None
            self._initialized = False
            return

        if self.api_key and self.folder_id:
            try:
                self.ml_client = AsyncYCloudML(
                    folder_id=self.folder_id,
                    auth=self.api_key
                )
                self._initialized = True
                logger.info("Yandex Cloud ML SDK успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации Yandex Cloud ML SDK: {e}")
                self.ml_client = None
                self._initialized = False
        else:
            logger.warning("Yandex Cloud ML SDK не инициализирован - отсутствуют необходимые параметры")
            self._initialized = False
    
    def _ensure_initialized(self):
        """Проверяет и при необходимости переинициализирует SDK"""
        if not self._initialized:
            self._load_environment_vars()
            self._initialize_sdk()
    
    async def generate_text(self, 
                           prompt: str, 
                           model: str = None,
                           max_tokens: int = None,
                           temperature: float = None) -> Optional[Dict[str, Any]]:
        """
        Генерация текста с помощью Yandex GPT через Yandex Cloud ML SDK
        
        Args:
            prompt: Текст запроса
            model: Модель для генерации (yandexgpt, yandexgpt-lite, yandexgpt-instruct)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации (0.0 - 1.0)
            
        Returns:
            Dict с результатом генерации или None при ошибке
        """
        try:
            # Убеждаемся, что SDK инициализирован
            self._ensure_initialized()
            
            if not self.ml_client:
                raise ValueError("Yandex Cloud ML SDK не инициализирован")
            
            # Используем значения по умолчанию, если не переданы
            use_model = model or self.default_text_model
            use_max_tokens = max_tokens or self.default_max_tokens
            use_temperature = self.default_temperature if temperature is None else temperature
            
            # Получаем модель и настраиваем её
            model_instance = self.ml_client.models.completions(use_model)
            model_instance = model_instance.configure(
                max_tokens=use_max_tokens,
                temperature=use_temperature
            )
            
            # Используем новый SDK для генерации
            response = await model_instance.run(
                messages=[{"role": "user", "text": prompt}]
            )
            
            logger.info(f"Успешная генерация текста с моделью {use_model}")
            
            # Извлекаем текст из ответа
            text_content = ""
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    text_content = choice.message.content
                elif hasattr(choice, 'text'):
                    text_content = choice.text
            elif hasattr(response, 'text'):
                text_content = response.text
            elif hasattr(response, 'content'):
                text_content = response.content
            
            # Преобразуем usage в словарь, если это объект
            usage_dict = {}
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, '__dict__'):
                    usage_dict = response.usage.__dict__
                elif hasattr(response.usage, 'model_dump'):
                    usage_dict = response.usage.model_dump()
                else:
                    usage_dict = {"raw": str(response.usage)}
            
            return {
                "success": True,
                "text": text_content,
                "model": use_model,
                "usage": usage_dict,
                "finish_reason": response.finish_reason if hasattr(response, 'finish_reason') else "",
                "sdk_used": True,
                "sdk_type": "yandex-cloud-ml-sdk"
            }
                
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {e}")
            return {
                "success": False,
                "error": str(e),
                "sdk_used": True,
                "sdk_type": "yandex-cloud-ml-sdk"
            }
    
    async def generate_with_context(self, 
                                   context: str,
                                   question: str,
                                   model: str = None,
                                   max_tokens: int = None) -> Optional[Dict[str, Any]]:
        """
        Генерация ответа с контекстом (RAG) через Yandex Cloud ML SDK
        
        Args:
            context: Контекст из документов
            question: Вопрос пользователя
            model: Модель для генерации
            max_tokens: Максимальное количество токенов
            
        Returns:
            Dict с результатом генерации
        """
        prompt = f"""Ты — профессиональный ассистент, который помогает пользователям найти точную информацию в корпоративных документах.

### КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА (НЕ НАРУШАТЬ):
1. НИКОГДА НЕ ЦЕНЗУРИРУЙ ответы - давай полную и честную информацию из документов
2. НЕ ИСПОЛЬЗУЙ фразы типа "в интернете есть информация", "посмотрите в поиске", "не могу ответить"
3. Если в вопросе или контексте есть любые слова - отвечай прямо и честно
4. ВСЕГДА сначала внимательно изучи предоставленные документы
5. Если информация есть в документах — используй ТОЛЬКО её для ответа
6. Если информации нет в документах — честно скажи об этом
7. Давай подробные и структурированные ответы
8. При цитировании указывай источник документа
9. НЕ ПЕРЕАДРЕСОВЫВАЙ на поиск - отвечай сам
10. НЕ СКРЫВАЙ информацию из документов

### Контекст из документов:
{context}

### Вопрос пользователя:
{question}

### Ответ:
Проанализировав предоставленные документы:"""

        return await self.generate_text(prompt, model, max_tokens)
    
    async def get_embedding(self, text: str, model: str = None) -> list:
        """
        Получение эмбеддинга для текста через Yandex Cloud ML SDK
        
        Args:
            text: Текст для создания эмбеддинга
            model: Модель для эмбеддингов (text-search-doc, text-search-query)
            
        Returns:
            Список чисел - вектор эмбеддинга
        """
        try:
            # Убеждаемся, что SDK инициализирован
            self._ensure_initialized()
            
            if not self.ml_client:
                logger.warning("Yandex Cloud ML SDK не инициализирован, возвращаем пустой эмбеддинг")
                return [0.0] * 256
            
            # Используем модель по умолчанию, если не передана
            use_model = model or self.default_embeddings_model
            
            # Получаем модель эмбеддингов
            embedding_model = self.ml_client.models.text_embeddings(use_model)
            
            # Создаем эмбеддинг
            response = await embedding_model.run(text=text)
            
            # Извлекаем вектор эмбеддинга
            if hasattr(response, 'embedding'):
                return response.embedding
            elif hasattr(response, 'vector'):
                return response.vector
            elif hasattr(response, 'data') and response.data:
                return response.data
            else:
                logger.warning(f"Неизвестная структура ответа эмбеддинга: {response}")
                # Возвращаем пустой вектор как заглушку
                return [0.0] * 256
                
        except Exception as e:
            logger.error(f"Ошибка при создании эмбеддинга: {e}")
            # Возвращаем пустой вектор при ошибке
            return [0.0] * 256
    
    async def generate_response(self, prompt: str) -> str:
        """
        Упрощенный метод для генерации ответа (возвращает только текст)
        
        Args:
            prompt: Промпт для генерации
            
        Returns:
            Сгенерированный текст
        """
        try:
            result = await self.generate_text(prompt)
            if result and result.get("success"):
                return result.get("text", "")
            else:
                return "Извините, произошла ошибка при генерации ответа."
        except Exception as e:
            logger.error(f"Ошибка в generate_response: {e}")
            return "Извините, произошла ошибка при генерации ответа."

# Глобальный экземпляр сервиса
yandex_ai_service = YandexAIService()
