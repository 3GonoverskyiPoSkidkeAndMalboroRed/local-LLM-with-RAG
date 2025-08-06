import os
import json
import aiohttp
from typing import Dict, Any, Optional
import logging
from yandex_config import YANDEX_API_KEY, YANDEX_FOLDER_ID

logger = logging.getLogger(__name__)

class YandexAIService:
    def __init__(self):
        # Используем HTTP API напрямую
        self.api_key = os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY') or YANDEX_API_KEY
        self.folder_id = os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID') or YANDEX_FOLDER_ID
        
        if not self.api_key:
            logger.warning("YANDEX_API_KEY не установлен. Некоторые функции могут быть недоступны.")
        
        if not self.folder_id:
            logger.warning("YANDEX_FOLDER_ID не установлен. Некоторые функции могут быть недоступны.")
        
        # URL для Yandex Cloud AI API
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
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
            
            # Используем HTTP API для генерации
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "modelUri": f"gpt://{self.folder_id}/{model}",
                "completionOptions": {
                    "maxTokens": max_tokens,
                    "temperature": temperature
                },
                "messages": [
                    {
                        "role": "user",
                        "text": prompt
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Извлекаем текст из ответа
                        if "result" in result and "alternatives" in result["result"]:
                            text = result["result"]["alternatives"][0]["message"]["text"]
                            usage = result.get("usage", {})
                            
                            logger.info(f"Успешная генерация текста с моделью {model}")
                            return {
                                "success": True,
                                "text": text,
                                "model": model,
                                "usage": usage,
                                "finish_reason": "stop",
                                "sdk_used": False,
                                "sdk_type": "http-api"
                            }
                        else:
                            raise ValueError("Неожиданная структура ответа от API")
                    else:
                        error_text = await response.text()
                        raise ValueError(f"API вернул статус {response.status}: {error_text}")
                
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {e}")
            return {
                "success": False,
                "error": str(e),
                "sdk_used": False,
                "sdk_type": "http-api"
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
