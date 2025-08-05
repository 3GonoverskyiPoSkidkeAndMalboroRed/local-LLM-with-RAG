import os
from typing import Dict, Any, Optional
from yandex_cloud_ml_sdk import AsyncYCloudML
import logging

logger = logging.getLogger(__name__)

class YandexAIService:
    def __init__(self):
        # Используем новый Yandex Cloud ML SDK
        self.api_key = os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')
        
        if not self.api_key:
            logger.warning("YANDEX_API_KEY не установлен. Некоторые функции могут быть недоступны.")
        
        if not self.folder_id:
            logger.warning("YANDEX_FOLDER_ID не установлен. Некоторые функции могут быть недоступны.")
        
        # Инициализируем async клиент
        self.ml_client = AsyncYCloudML(
            folder_id=self.folder_id,
            auth=self.api_key
        )
    
    async def generate_text(self, 
                           prompt: str, 
                           model: str = "yandexgpt-lite",
                           max_tokens: int = 1000,
                           temperature: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Генерация текста с помощью Yandex GPT через Yandex Cloud ML SDK
        
        Args:
            prompt: Текст запроса
            model: Модель для генерации (yandexgpt-lite, yandexgpt, yandexgpt-instruct)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации (0.0 - 1.0)
            
        Returns:
            Dict с результатом генерации или None при ошибке
        """
        try:
            if not self.api_key:
                raise ValueError("API ключ не установлен")
            
            if not self.folder_id:
                raise ValueError("Folder ID не установлен")
            
            # Используем новый SDK для генерации
            response = await self.ml_client.generate(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"Успешная генерация текста с моделью {model}")
            return {
                "success": True,
                "text": response.text,
                "model": model,
                "usage": response.usage if hasattr(response, 'usage') else {},
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
                                   model: str = "yandexgpt-lite",
                                   max_tokens: int = 1000) -> Optional[Dict[str, Any]]:
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

### Правила работы:
1. ВСЕГДА сначала внимательно изучи предоставленные документы
2. Если информация есть в документах — используй ТОЛЬКО её для ответа
3. Если информации нет в документах — честно скажи об этом
4. Давай подробные и структурированные ответы
5. При цитировании указывай источник документа

### Контекст из документов:
{context}

### Вопрос пользователя:
{question}

### Ответ:
Проанализировав предоставленные документы:"""

        return await self.generate_text(prompt, model, max_tokens)

# Глобальный экземпляр сервиса
yandex_ai_service = YandexAIService()
