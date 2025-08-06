from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from yandex_ai_service import yandex_ai_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yandex-ai", tags=["Yandex AI"])

# Pydantic модели для запросов
class GenerateTextRequest(BaseModel):
    prompt: str
    model: str = "yandexgpt-lite"
    max_tokens: int = 1000
    temperature: float = 0.6

class GenerateWithContextRequest(BaseModel):
    context: str
    question: str
    model: str = "yandexgpt-lite"
    max_tokens: int = 1000

class GenerateTextResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    details: Optional[str] = None
    sdk_used: Optional[bool] = None
    sdk_type: Optional[str] = None

@router.post("/generate", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """
    Генерация текста с помощью Yandex GPT через Yandex Cloud ML SDK
    
    Использует стандартный системный промпт для профессионального ассистента.
    """
    try:
        # Стандартный системный промпт для профессионального ассистента
        system_prompt = """### Инструкция:
Ты — профессиональный ассистент, который помогает пользователям с различными задачами.

### Правила работы:
1. Давай точные и полезные ответы
2. Будь вежливым и профессиональным
3. Если не знаешь ответ — честно скажи об этом
4. Структурируй ответы для лучшего понимания
5. Используй примеры, когда это уместно

### Запрос пользователя:
{prompt}

### Ответ:
"""
        # Формируем полный промпт с системными инструкциями
        full_prompt = system_prompt.format(prompt=request.prompt)
        
        result = await yandex_ai_service.generate_text(
            prompt=full_prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать текст")
        
        return GenerateTextResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации текста: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации текста: {str(e)}")

@router.post("/generate-with-context", response_model=GenerateTextResponse)
async def generate_with_context(request: GenerateWithContextRequest):
    """
    Генерация ответа с контекстом (RAG) через Yandex Cloud ML SDK
    """
    try:
        result = await yandex_ai_service.generate_with_context(
            context=request.context,
            question=request.question,
            model=request.model,
            max_tokens=request.max_tokens
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать ответ с контекстом")
        
        return GenerateTextResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации с контекстом: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации с контекстом: {str(e)}")
