# УРЕЗАННАЯ ВЕРСИЯ БЕЗ OLLAMA - ЗАГЛУШКА
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database import get_db

# Создаем маршрутизатор
router = APIRouter(prefix="/llm", tags=["llm"])

# Модели данных (заглушки)
class QueryRequest(BaseModel):
    question: str
    department_id: str = "default"

class QueryResponse(BaseModel):
    task_id: str
    status: str
    message: str

class QueryResultResponse(BaseModel):
    task_id: str
    status: str
    answer: str = ""
    chunks: List[str] = []
    files: List[str] = []
    error: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""

class InitRequest(BaseModel):
    model_name: str
    embedding_model_name: str
    documents_path: str
    department_id: str = "default"

class GenerateRequest(BaseModel):
    messages: str
    model: str = "disabled"

class GenerateResponse(BaseModel):
    text: str
    model: str = "disabled"

class QueueStatusResponse(BaseModel):
    department_id: str
    initialized: bool
    max_concurrent: int = 0
    available_slots: int = 0
    processing_count: int = 0
    pending_count: int = 0
    total_active_tasks: int = 0

# Заглушки для всех эндпоинтов
@router.post("/debug/query-request")
async def debug_query_request(request: QueryRequest):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/debug/department-state/{department_id}")
async def debug_department_state(department_id: str):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/debug/reinitialize/{department_id}")
async def debug_reinitialize_department(department_id: str):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, background_tasks: BackgroundTasks):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/query/{task_id}", response_model=QueryResultResponse)
async def get_query_result(task_id: str):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/queue/status/{department_id}", response_model=QueueStatusResponse)
async def get_queue_status(department_id: str):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/queue/cleanup/{department_id}")
async def cleanup_queue(department_id: str, max_age_minutes: int = 60):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/queue/force-cleanup/{department_id}")
async def force_cleanup_department(department_id: str):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/queue/force-cleanup-all")
async def force_cleanup_all_departments():
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/queue/stuck-tasks")
async def get_stuck_tasks(max_processing_minutes: int = 5):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/initialize")
async def initialize_model(request: InitRequest, db: Session = Depends(get_db)):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/models")
async def get_models():
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/models/llm")
async def get_llm_models():
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/models/embedding")
async def get_embedding_models():
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.post("/query-sync")
async def query_sync(request: QueryRequest):
    raise HTTPException(status_code=503, detail="LLM functionality disabled")

@router.get("/initialized-departments")
async def get_initialized_departments():
    raise HTTPException(status_code=503, detail="LLM functionality disabled")
