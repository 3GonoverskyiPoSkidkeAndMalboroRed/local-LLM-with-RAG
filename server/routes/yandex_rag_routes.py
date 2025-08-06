"""
Роуты для Yandex RAG системы
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from database import get_db
from models_db import Department, Content
from yandex_rag_service import yandex_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yandex-rag", tags=["Yandex RAG"])

# Pydantic модели
class InitializeRAGRequest(BaseModel):
    department_id: str
    force_reload: bool = False

class RAGQueryRequest(BaseModel):
    department_id: str
    question: str

class RAGResponse(BaseModel):
    success: bool
    answer: str
    sources: List[Dict[str, Any]] = []
    context_used: int = 0
    department_id: str = ""
    error: Optional[str] = None

class InitializeResponse(BaseModel):
    success: bool
    message: str
    department_id: str
    documents_processed: int = 0
    error: Optional[str] = None

@router.post("/initialize", response_model=InitializeResponse)
async def initialize_rag_for_department(
    request: InitializeRAGRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Инициализирует RAG систему для конкретного отдела
    Создает векторную базу данных из документов отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == int(request.department_id)).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {request.department_id} не найден")
        
        # Проверяем наличие документов для отдела
        content_count = db.query(Content).filter(Content.department_id == int(request.department_id)).count()
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
            request.force_reload,
            db
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

async def _initialize_rag_background(department_id: str, force_reload: bool, db: Session):
    """Фоновая задача для инициализации RAG"""
    try:
        logger.info(f"Начинаем инициализацию RAG для отдела {department_id}")
        
        vector_store = await yandex_rag_service.create_vector_store(
            department_id=department_id,
            db=db,
            force_reload=force_reload
        )
        
        if vector_store:
            logger.info(f"RAG успешно инициализирован для отдела {department_id}")
        else:
            logger.error(f"Не удалось инициализировать RAG для отдела {department_id}")
            
    except Exception as e:
        logger.error(f"Ошибка в фоновой инициализации RAG: {e}")

@router.post("/query", response_model=RAGResponse)
async def query_rag(request: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    Выполняет RAG запрос для получения ответа на основе документов отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == int(request.department_id)).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {request.department_id} не найден")
        
        # Выполняем RAG запрос
        result = await yandex_rag_service.generate_rag_response(
            department_id=request.department_id,
            question=request.question,
            db=db
        )
        
        return RAGResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при выполнении RAG запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении RAG запроса: {str(e)}")

@router.get("/status/{department_id}")
async def get_rag_status(department_id: str, db: Session = Depends(get_db)):
    """
    Проверяет статус RAG системы для отдела
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == int(department_id)).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Проверяем наличие векторной БД
        vector_store = await yandex_rag_service._load_existing_vector_store(department_id)
        is_initialized = vector_store is not None
        
        # Подсчитываем документы в БД
        content_count = db.query(Content).filter(Content.department_id == int(department_id)).count()
        
        # Подсчитываем документы в векторной БД
        vector_docs_count = len(vector_store.get('texts', [])) if vector_store else 0
        
        return {
            "department_id": department_id,
            "department_name": department.department_name,
            "is_initialized": is_initialized,
            "documents_in_db": content_count,
            "documents_in_vector_store": vector_docs_count,
            "needs_reinitialization": content_count != vector_docs_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке статуса RAG: {str(e)}")

@router.delete("/reset/{department_id}")
async def reset_rag_for_department(department_id: str, db: Session = Depends(get_db)):
    """
    Сбрасывает RAG систему для отдела (удаляет векторную БД)
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == int(department_id)).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Удаляем векторную БД
        import shutil
        department_vector_dir = os.path.join(yandex_rag_service.persist_directory, f"dept_{department_id}")
        
        if os.path.exists(department_vector_dir):
            shutil.rmtree(department_vector_dir)
            logger.info(f"Векторная БД для отдела {department_id} удалена")
            
        return {
            "success": True,
            "message": f"RAG система для отдела {department_id} сброшена",
            "department_id": department_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при сбросе RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сбросе RAG: {str(e)}")

@router.get("/search/{department_id}")
async def search_documents(
    department_id: str, 
    query: str, 
    k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Выполняет поиск похожих документов без генерации ответа
    """
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == int(department_id)).first()
        if not department:
            raise HTTPException(status_code=404, detail=f"Отдел с ID {department_id} не найден")
        
        # Выполняем поиск
        results = await yandex_rag_service.similarity_search(department_id, query, k)
        
        return {
            "department_id": department_id,
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при поиске документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске документов: {str(e)}")