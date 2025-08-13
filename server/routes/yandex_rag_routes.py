"""
Маршруты для работы с Yandex RAG (Retrieval-Augmented Generation)
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models_db import Department, Content
from yandex_rag_service import yandex_rag_service
from routes.user_routes import require_admin

# Rate limiting import
from rate_limiter import get_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yandex-rag", tags=["Yandex RAG"])

# Получаем глобальный rate limiter
limiter = get_limiter()

# Pydantic модели
class InitializeRAGRequest(BaseModel):
    department_id: int
    force_reload: bool = False

class RAGQueryRequest(BaseModel):
    department_id: int
    question: str

class RAGResponse(BaseModel):
    success: bool
    answer: str
    sources: List[Dict[str, Any]] = []
    context_used: int = 0
    department_id: int = 0
    error: Optional[str] = None

class InitializeResponse(BaseModel):
    success: bool
    message: str
    department_id: int
    documents_processed: int = 0
    error: Optional[str] = None

@router.post("/initialize", response_model=InitializeResponse)
async def initialize_rag_for_department(
    request: InitializeRAGRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    Инициализирует RAG систему для конкретного отдела
    Создает векторную базу данных из документов отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == request.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {request.department_id} не найден")
        
        # Проверяем наличие документов для отдела
        content_count = db.query(Content).filter(Content.department_id == request.department_id).count()
        if content_count == 0:
            return InitializeResponse(
                success=False,
                message=f"Нет документов для инициализации RAG в отделе {request.department_id}",
                department_id=request.department_id,
                error="No documents found"
            )
        
        # Запускаем инициализацию в фоне
        background_tasks.add_task(
            _initialize_rag_background,
            request.department_id,
            request.force_reload
        )
        
        return InitializeResponse(
            success=True,
            message=f"Инициализация RAG для отдела {request.department_id} запущена в фоне",
            department_id=request.department_id,
            documents_processed=content_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при инициализации RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при инициализации RAG: {str(e)}")

async def _initialize_rag_background(department_id: int, force_reload: bool):
    """Фоновая задача для инициализации RAG"""
    try:
        logger.info(f"Начинаем инициализацию RAG для отдела {department_id}")
        
        result = await yandex_rag_service.initialize_rag(
            department_id=department_id,
            force_reload=force_reload
        )
        
        if result.get("success"):
            logger.info(f"RAG успешно инициализирован для отдела {department_id}")
        else:
            logger.error(f"Не удалось инициализировать RAG для отдела {department_id}: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"Ошибка в фоновой инициализации RAG: {e}")

@router.post("/query", response_model=RAGResponse)
@limiter.limit("30/minute")
async def query_rag(
    req: Request,
    request: RAGQueryRequest, 
    db: Session = Depends(get_db),
):
    """
    Выполняет RAG запрос для получения ответа на основе документов отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == request.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {request.department_id} не найден")
        
        # Выполняем RAG запрос
        result = await yandex_rag_service.query_rag(
            department_id=request.department_id,
            question=request.question
        )
        
        return RAGResponse(
            success=True,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            context_used=result.get("context_used", 0),
            department_id=request.department_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при выполнении RAG запроса: {e}")
        return RAGResponse(
            success=False,
            answer="",
            sources=[],
            context_used=0,
            department_id=request.department_id,
            error=str(e)
        )

@router.get("/status/{department_id}")
async def get_rag_status(department_id: int, db: Session = Depends(get_db)):
    """
    Проверяет статус RAG системы для отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Получаем статус RAG системы
        status = await yandex_rag_service.get_rag_status(department_id)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке статуса RAG: {str(e)}")

@router.delete("/reset/{department_id}")
async def reset_rag_for_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    Сбрасывает RAG систему для отдела (удаляет векторную БД)
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Сбрасываем RAG систему
        result = await yandex_rag_service.reset_rag(department_id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message", f"RAG система для отдела {department_id} сброшена"),
                "department_id": department_id
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Ошибка при сбросе RAG"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при сбросе RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сбросе RAG: {str(e)}")

@router.get("/search/{department_id}")
async def search_documents(
    department_id: int, 
    query: str, 
    k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Выполняет поиск похожих документов без генерации ответа
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Выполняем RAG запрос для получения источников
        result = await yandex_rag_service.query_rag(department_id, query)
        
        return {
            "department_id": department_id,
            "query": query,
            "results_count": len(result.get("sources", [])),
            "results": result.get("sources", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при поиске документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске документов: {str(e)}")