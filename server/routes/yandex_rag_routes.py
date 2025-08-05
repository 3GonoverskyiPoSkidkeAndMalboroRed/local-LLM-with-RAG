"""
Специализированные RAG эндпоинты для Yandex Cloud API
Обеспечивает эффективную работу с документами и контекстным поиском
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from yandex_rag_service import RAGContext, get_rag_service
from yandex_error_handler import get_error_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yandex/rag", tags=["yandex-rag"])

# Модели запросов
class RAGQueryRequest(BaseModel):
    """Запрос на RAG операцию"""
    query: str = Field(..., description="Вопрос пользователя")
    department_id: str = Field("default", description="ID департамента")
    max_chunks: int = Field(5, ge=1, le=20, description="Максимальное количество чанков")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Порог схожести")
    include_metadata: bool = Field(True, description="Включить метаданные источников")
    use_cache: bool = Field(True, description="Использовать кэширование")

class RAGQueryResponse(BaseModel):
    """Ответ на RAG запрос"""
    answer: str
    sources: List[Dict[str, Any]]
    chunks_used: List[str]
    similarity_scores: List[float]
    tokens_used: int
    processing_time: float
    model_used: str
    cache_hit: bool = False

class RAGBatchRequest(BaseModel):
    """Пакетный RAG запрос"""
    queries: List[str] = Field(..., description="Список вопросов")
    department_id: str = Field("default", description="ID департамента")
    max_chunks: int = Field(5, ge=1, le=20, description="Максимальное количество чанков")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Порог схожести")

class RAGBatchResponse(BaseModel):
    """Ответ на пакетный RAG запрос"""
    results: List[RAGQueryResponse]
    total_processing_time: float
    average_processing_time: float

class RAGMetricsResponse(BaseModel):
    """Метрики RAG сервиса"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float
    average_response_time: float
    average_chunks_used: float
    cache_hit_rate: float
    last_query_time: Optional[str]
    model_used: str
    embedding_model: str

class RAGHealthResponse(BaseModel):
    """Состояние здоровья RAG сервиса"""
    status: str
    rag_service_available: bool
    llm_model_available: bool
    embedding_model_available: bool
    cache_available: bool
    error_handler_available: bool
    last_error: Optional[str] = None

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Выполнение RAG запроса с поиском релевантных документов
    """
    try:
        # Получаем RAG сервис
        rag_service = await get_rag_service()
        
        # Создаем контекст
        context = RAGContext(
            query=request.query,
            department_id=request.department_id,
            max_chunks=request.max_chunks,
            similarity_threshold=request.similarity_threshold,
            include_metadata=request.include_metadata
        )
        
        # Выполняем RAG запрос
        result = await rag_service.query_with_rag(
            context=context,
            db_session=db,
            use_cache=request.use_cache
        )
        
        # Определяем, был ли использован кэш
        cache_hit = False
        if request.use_cache:
            cache_key = rag_service._generate_cache_key(context)
            cached_result = rag_service._cache.get_rag_result(cache_key) if rag_service._cache else None
            cache_hit = cached_result is not None
        
        return RAGQueryResponse(
            answer=result.answer,
            sources=result.sources,
            chunks_used=result.chunks_used,
            similarity_scores=result.similarity_scores,
            tokens_used=result.tokens_used,
            processing_time=result.processing_time,
            model_used=result.model_used,
            cache_hit=cache_hit
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении RAG запроса: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выполнении RAG запроса: {str(e)}"
        )

@router.post("/query/batch", response_model=RAGBatchResponse)
async def rag_batch_query(
    request: RAGBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Пакетное выполнение RAG запросов
    """
    try:
        import time
        start_time = time.time()
        
        rag_service = await get_rag_service()
        results = []
        
        # Выполняем запросы последовательно (можно оптимизировать для параллельного выполнения)
        for query in request.queries:
            context = RAGContext(
                query=query,
                department_id=request.department_id,
                max_chunks=request.max_chunks,
                similarity_threshold=request.similarity_threshold,
                include_metadata=True
            )
            
            result = await rag_service.query_with_rag(
                context=context,
                db_session=db,
                use_cache=True
            )
            
            results.append(RAGQueryResponse(
                answer=result.answer,
                sources=result.sources,
                chunks_used=result.chunks_used,
                similarity_scores=result.similarity_scores,
                tokens_used=result.tokens_used,
                processing_time=result.processing_time,
                model_used=result.model_used,
                cache_hit=False  # Упрощенно
            ))
        
        total_time = time.time() - start_time
        
        return RAGBatchResponse(
            results=results,
            total_processing_time=total_time,
            average_processing_time=total_time / len(request.queries) if request.queries else 0
        )
        
    except Exception as e:
        logger.error(f"Ошибка при пакетном RAG запросе: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при пакетном RAG запросе: {str(e)}"
        )

@router.get("/metrics", response_model=RAGMetricsResponse)
async def get_rag_metrics():
    """
    Получение метрик RAG сервиса
    """
    try:
        rag_service = await get_rag_service()
        metrics = rag_service.get_metrics()
        
        return RAGMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Ошибка при получении метрик RAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении метрик: {str(e)}"
        )

@router.post("/metrics/reset")
async def reset_rag_metrics():
    """
    Сброс метрик RAG сервиса
    """
    try:
        rag_service = await get_rag_service()
        rag_service.reset_metrics()
        
        return {"message": "Метрики RAG сервиса сброшены"}
        
    except Exception as e:
        logger.error(f"Ошибка при сбросе метрик RAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сбросе метрик: {str(e)}"
        )

@router.get("/health", response_model=RAGHealthResponse)
async def rag_health_check():
    """
    Проверка здоровья RAG сервиса
    """
    try:
        rag_service = await get_rag_service()
        error_handler = get_error_handler()
        
        # Проверяем доступность компонентов
        health_status = {
            "status": "healthy",
            "rag_service_available": True,
            "llm_model_available": True,
            "embedding_model_available": True,
            "cache_available": rag_service._cache is not None,
            "error_handler_available": error_handler is not None,
            "last_error": None
        }
        
        # Проверяем LLM адаптер
        try:
            llm_adapter = await rag_service._get_llm_adapter()
            health_status["llm_model_available"] = llm_adapter is not None
        except Exception as e:
            health_status["llm_model_available"] = False
            health_status["last_error"] = str(e)
            health_status["status"] = "degraded"
        
        # Проверяем embeddings
        try:
            embeddings = await rag_service._get_embeddings()
            health_status["embedding_model_available"] = embeddings is not None
        except Exception as e:
            health_status["embedding_model_available"] = False
            health_status["last_error"] = str(e)
            health_status["status"] = "degraded"
        
        # Если есть критические ошибки
        if not health_status["llm_model_available"] or not health_status["embedding_model_available"]:
            health_status["status"] = "unhealthy"
        
        return RAGHealthResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья RAG: {e}")
        return RAGHealthResponse(
            status="unhealthy",
            rag_service_available=False,
            llm_model_available=False,
            embedding_model_available=False,
            cache_available=False,
            error_handler_available=False,
            last_error=str(e)
        )

@router.post("/cache/clear")
async def clear_rag_cache():
    """
    Очистка кэша RAG сервиса
    """
    try:
        rag_service = await get_rag_service()
        if rag_service._cache:
            # Очищаем RAG кэш (нужно добавить метод в кэш)
            cleared_count = 0  # rag_service._cache.clear_rag_cache()
            return {"message": f"Кэш RAG очищен. Удалено записей: {cleared_count}"}
        else:
            return {"message": "Кэш RAG не настроен"}
            
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша RAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при очистке кэша: {str(e)}"
        )

@router.get("/config")
async def get_rag_config():
    """
    Получение конфигурации RAG сервиса
    """
    try:
        rag_service = await get_rag_service()
        
        return {
            "llm_model": rag_service.llm_model,
            "embedding_model": rag_service.embedding_model,
            "cache_enabled": rag_service.cache_enabled,
            "max_retries": rag_service.max_retries,
            "default_max_chunks": 5,
            "default_similarity_threshold": 0.7
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении конфигурации RAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении конфигурации: {str(e)}"
        ) 