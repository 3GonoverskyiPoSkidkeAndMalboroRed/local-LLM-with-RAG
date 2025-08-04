"""
Роуты для работы с Yandex GPT
Обеспечивает отдельные эндпоинты для генерации с использованием Yandex Cloud API
"""

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from yandex_llm import create_yandex_chat_model, create_yandex_llm
from yandex_cloud_adapter import YandexCloudConfig, get_yandex_adapter
from yandex_error_handler import get_error_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yandex", tags=["yandex-gpt"])

# Модели запросов
class YandexGenerateRequest(BaseModel):
    """Запрос на генерацию текста с Yandex GPT"""
    prompt: str = Field(..., description="Текст для генерации")
    model: str = Field("yandexgpt", description="Модель Yandex GPT")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Температура генерации")
    max_tokens: int = Field(2000, ge=1, le=8000, description="Максимальное количество токенов")
    stream: bool = Field(False, description="Потоковая генерация")

class YandexChatRequest(BaseModel):
    """Запрос на чат с Yandex GPT"""
    messages: List[Dict[str, str]] = Field(..., description="История сообщений")
    model: str = Field("yandexgpt", description="Модель Yandex GPT")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Температура генерации")
    max_tokens: int = Field(2000, ge=1, le=8000, description="Максимальное количество токенов")
    stream: bool = Field(False, description="Потоковая генерация")

class YandexGenerateResponse(BaseModel):
    """Ответ на генерацию текста"""
    text: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None

class YandexChatResponse(BaseModel):
    """Ответ на чат"""
    message: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None

class YandexConfigResponse(BaseModel):
    """Информация о конфигурации Yandex Cloud"""
    is_configured: bool
    model: str
    folder_id: Optional[str] = None
    base_url: str
    max_tokens: int
    temperature: float

def _validate_yandex_config() -> bool:
    """Проверка наличия необходимых переменных окружения для Yandex Cloud"""
    required_vars = ["YANDEX_API_KEY", "YANDEX_FOLDER_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Отсутствуют переменные окружения для Yandex Cloud: {missing_vars}")
        return False
    
    return True

def _get_yandex_config() -> Optional[YandexCloudConfig]:
    """Получение конфигурации Yandex Cloud"""
    try:
        if not _validate_yandex_config():
            return None
        return YandexCloudConfig.from_env()
    except Exception as e:
        logger.error(f"Ошибка при получении конфигурации Yandex Cloud: {e}")
        return None

@router.get("/config", response_model=YandexConfigResponse)
async def get_yandex_config():
    """Получение информации о конфигурации Yandex Cloud"""
    config = _get_yandex_config()
    
    if not config:
        return YandexConfigResponse(
            is_configured=False,
            model="yandexgpt",
            base_url="https://llm.api.cloud.yandex.net",
            max_tokens=2000,
            temperature=0.1
        )
    
    return YandexConfigResponse(
        is_configured=True,
        model=config.llm_model,
        folder_id=config.folder_id,
        base_url=config.base_url,
        max_tokens=config.max_tokens,
        temperature=config.temperature
    )

@router.post("/generate", response_model=YandexGenerateResponse)
async def generate_text(request: YandexGenerateRequest):
    """Генерация текста с использованием Yandex GPT"""
    import time
    
    # Проверяем конфигурацию
    config = _get_yandex_config()
    if not config:
        raise HTTPException(
            status_code=500,
            detail="Yandex Cloud не настроен. Проверьте переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID"
        )
    
    try:
        start_time = time.time()
        
        # Создаем модель LLM
        llm = create_yandex_llm(
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Генерируем текст
        response_text = await llm._acall(request.prompt)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return YandexGenerateResponse(
            text=response_text,
            model=request.model,
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка при генерации текста с Yandex GPT: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации текста: {str(e)}"
        )

@router.post("/chat", response_model=YandexChatResponse)
async def chat_with_yandex(request: YandexChatRequest):
    """Чат с использованием Yandex GPT"""
    import time
    
    # Проверяем конфигурацию
    config = _get_yandex_config()
    if not config:
        raise HTTPException(
            status_code=500,
            detail="Yandex Cloud не настроен. Проверьте переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID"
        )
    
    try:
        start_time = time.time()
        
        # Создаем чат модель
        chat_model = create_yandex_chat_model(
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Конвертируем сообщения в формат langchain
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        messages = []
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        # Генерируем ответ
        result = await chat_model._agenerate(messages)
        response_message = result.generations[0][0].text
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return YandexChatResponse(
            message=response_message,
            model=request.model,
            response_time=response_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка при чате с Yandex GPT: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при чате: {str(e)}"
        )

@router.post("/generate/stream")
async def generate_text_stream(request: YandexGenerateRequest):
    """Потоковая генерация текста с использованием Yandex GPT"""
    from fastapi.responses import StreamingResponse
    
    # Проверяем конфигурацию
    config = _get_yandex_config()
    if not config:
        raise HTTPException(
            status_code=500,
            detail="Yandex Cloud не настроен. Проверьте переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID"
        )
    
    async def generate_stream():
        try:
            adapter = await get_yandex_adapter()
            
            async for chunk in adapter.generate_text_stream(
                messages=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Ошибка при потоковой генерации: {e}")
            yield f"data: error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.get("/health")
async def yandex_health_check():
    """Проверка здоровья Yandex Cloud API"""
    config = _get_yandex_config()
    
    if not config:
        return {
            "status": "error",
            "message": "Yandex Cloud не настроен",
            "configured": False
        }
    
    try:
        # Пробуем создать адаптер и выполнить простой запрос
        adapter = await get_yandex_adapter()
        test_response = await adapter.generate_text(
            messages="Привет",
            model="yandexgpt",
            max_tokens=10
        )
        
        return {
            "status": "healthy",
            "message": "Yandex Cloud API доступен",
            "configured": True,
            "test_response_length": len(test_response)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья Yandex Cloud: {e}")
        return {
            "status": "error",
            "message": f"Ошибка подключения к Yandex Cloud: {str(e)}",
            "configured": True
        }

@router.get("/models")
async def get_available_models():
    """Получение списка доступных моделей Yandex GPT"""
    return {
        "models": [
            {
                "id": "yandexgpt",
                "name": "Yandex GPT",
                "description": "Основная модель Yandex GPT для генерации текста"
            },
            {
                "id": "yandexgpt-lite",
                "name": "Yandex GPT Lite", 
                "description": "Облегченная версия Yandex GPT"
            }
        ],
        "default_model": "yandexgpt"
    } 