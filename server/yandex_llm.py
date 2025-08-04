"""
Yandex Cloud LLM интеграция для langchain
Обеспечивает совместимость с существующим кодом через langchain интерфейс
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Iterator, AsyncIterator
from langchain_core.language_models.llms import LLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import LLMResult, Generation, ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun

from yandex_cloud_adapter import YandexCloudAdapter, YandexCloudConfig, get_yandex_adapter

logger = logging.getLogger(__name__)

class YandexGPT(LLM):
    """
    Yandex Cloud LLM для интеграции с langchain
    Совместим с существующим кодом, использующим ChatOllama
    """
    
    def __init__(
        self,
        model: str = "yandexgpt",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        timeout: int = 30,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._adapter: Optional[YandexCloudAdapter] = None
    
    @property
    def _llm_type(self) -> str:
        """Тип LLM для langchain"""
        return "yandex_gpt"
    
    async def _get_adapter(self) -> YandexCloudAdapter:
        """Получение адаптера Yandex Cloud"""
        if self._adapter is None:
            self._adapter = await get_yandex_adapter()
        return self._adapter
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Синхронный вызов LLM"""
        # Запускаем асинхронный метод в синхронном контексте
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._acall(prompt, stop, run_manager, **kwargs))
        finally:
            loop.close()
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Асинхронный вызов LLM с кэшированием"""
        try:
            # Объединяем параметры
            generation_kwargs = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                **kwargs
            }
            
            temperature = generation_kwargs["temperature"]
            
            # Проверяем кэш для частых запросов (только при низкой температуре)
            if temperature <= 0.2:  # Кэшируем только детерминистичные ответы
                try:
                    from yandex_cache import get_cached_llm_response, cache_llm_response
                    
                    cached_response = get_cached_llm_response(prompt, self.model, temperature)
                    if cached_response is not None:
                        logger.debug(f"Ответ LLM загружен из кэша: {self.model}")
                        
                        # Обрабатываем stop sequences
                        if stop:
                            for stop_seq in stop:
                                if stop_seq in cached_response:
                                    cached_response = cached_response.split(stop_seq)[0]
                                    break
                        
                        return cached_response
                        
                except ImportError:
                    logger.debug("Кэш недоступен для LLM ответов")
            
            adapter = await self._get_adapter()
            
            # Генерируем текст
            response = await adapter.generate_text(
                prompt, 
                model=self.model,
                **generation_kwargs
            )
            
            # Обрабатываем stop sequences (если поддерживается)
            if stop:
                for stop_seq in stop:
                    if stop_seq in response:
                        response = response.split(stop_seq)[0]
                        break
            
            # Сохраняем в кэш (только детерминистичные ответы)
            if temperature <= 0.2:
                try:
                    cache_llm_response(prompt, self.model, response, temperature)
                except:
                    pass  # Игнорируем ошибки кэширования
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка в YandexGPT._acall: {e}")
            raise
    
    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Потоковая генерация (синхронная)"""
        # Пока что возвращаем полный ответ как один chunk
        response = self._call(prompt, stop, run_manager, **kwargs)
        yield response
    
    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Потоковая генерация (асинхронная)"""
        try:
            adapter = await self._get_adapter()
            
            generation_kwargs = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                **kwargs
            }
            
            async for chunk in adapter.generate_text_stream(
                prompt, 
                model=self.model,
                **generation_kwargs
            ):
                # Проверяем stop sequences
                if stop:
                    for stop_seq in stop:
                        if stop_seq in chunk:
                            chunk = chunk.split(stop_seq)[0]
                            yield chunk
                            return
                
                yield chunk
                
        except Exception as e:
            logger.error(f"Ошибка в YandexGPT._astream: {e}")
            raise
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Параметры для идентификации модели"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }

class YandexChatModel(BaseChatModel):
    """
    Yandex Cloud Chat Model для langchain
    Поддерживает диалоговый интерфейс с сообщениями
    """
    
    def __init__(
        self,
        model: str = "yandexgpt",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        timeout: int = 30,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._adapter: Optional[YandexCloudAdapter] = None
    
    @property
    def _llm_type(self) -> str:
        """Тип LLM для langchain"""
        return "yandex_chat"
    
    async def _get_adapter(self) -> YandexCloudAdapter:
        """Получение адаптера Yandex Cloud"""
        if self._adapter is None:
            self._adapter = await get_yandex_adapter()
        return self._adapter
    
    def _convert_messages_to_yandex_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Конвертация langchain сообщений в формат Yandex Cloud"""
        yandex_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                # Для неизвестных типов используем user
                role = "user"
            
            yandex_messages.append({
                "role": role,
                "text": message.content
            })
        
        return yandex_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Синхронная генерация чата"""
        # Запускаем асинхронный метод в синхронном контексте
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._agenerate(messages, stop, run_manager, **kwargs))
        finally:
            loop.close()
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Асинхронная генерация чата"""
        try:
            adapter = await self._get_adapter()
            
            # Конвертируем сообщения
            yandex_messages = self._convert_messages_to_yandex_format(messages)
            
            # Объединяем параметры
            generation_kwargs = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                **kwargs
            }
            
            # Генерируем ответ
            response = await adapter.generate_text(
                yandex_messages,
                model=self.model,
                **generation_kwargs
            )
            
            # Обрабатываем stop sequences
            if stop:
                for stop_seq in stop:
                    if stop_seq in response:
                        response = response.split(stop_seq)[0]
                        break
            
            # Создаем результат в формате langchain
            message = AIMessage(content=response)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Ошибка в YandexChatModel._agenerate: {e}")
            raise
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Параметры для идентификации модели"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }

# Фабричные функции для создания моделей
def create_yandex_llm(
    model: str = "yandexgpt",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    **kwargs
) -> YandexGPT:
    """
    Создание YandexGPT LLM
    
    Args:
        model: Название модели
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр YandexGPT
    """
    return YandexGPT(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )

def create_yandex_chat_model(
    model: str = "yandexgpt",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    **kwargs
) -> YandexChatModel:
    """
    Создание YandexChatModel
    
    Args:
        model: Название модели
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр YandexChatModel
    """
    return YandexChatModel(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )

# Совместимость с существующим кодом
class ChatYandex(YandexChatModel):
    """Алиас для совместимости с ChatOllama интерфейсом"""
    pass

# Функция для создания совместимой модели
def create_compatible_llm(
    model: str = "yandexgpt",
    base_url: str = None,  # Игнорируется для совместимости
    temperature: float = 0.1,
    num_predict: int = 2000,  # Маппится на max_tokens
    **kwargs
) -> YandexChatModel:
    """
    Создание LLM совместимого с ChatOllama интерфейсом
    
    Args:
        model: Название модели
        base_url: Игнорируется (для совместимости с Ollama)
        temperature: Температура генерации
        num_predict: Количество токенов (маппится на max_tokens)
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр YandexChatModel
    """
    # Маппинг параметров Ollama на Yandex Cloud
    max_tokens = kwargs.pop('max_tokens', num_predict)
    
    return YandexChatModel(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )