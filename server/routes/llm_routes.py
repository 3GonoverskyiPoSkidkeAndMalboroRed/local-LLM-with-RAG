from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
import traceback
import time
import asyncio
import uuid
import logging
import sys
import os
from collections import defaultdict
from datetime import datetime, timedelta

from database import get_db
from models_db import Department
from document_loader import vec_search
from llm_state_manager import get_llm_state_manager
from yandex_metrics import get_metrics_instance
from performance_monitor import get_performance_monitor
from config_utils import get_runtime_config, validate_all_config_new, print_config_validation_report
from yandex_cache import get_cache

# Получаем единственный экземпляр менеджера
llm_state_manager = get_llm_state_manager()

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем маршрутизатор
router = APIRouter(prefix="/llm", tags=["llm"])

# Константы для таймаутов
LLM_REQUEST_TIMEOUT = 120  # 2 минуты для LLM запросов
EMBEDDING_REQUEST_TIMEOUT = 30  # 30 секунд для embedding запросов

# Защита от рекурсии GET запросов
_get_request_counts = defaultdict(list)  # task_id -> [timestamps]
MAX_GET_REQUESTS_PER_MINUTE = 30  # Максимум 30 GET запросов в минуту к одной задаче

# Модели данных
class SourceInfo(BaseModel):
    """Информация об источнике документа"""
    file_name: str
    file_path: str
    chunk_content: str
    chunk_id: str
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None

class QueryRequest(BaseModel):
    question: str
    department_id: str = "default"

class QueryResponse(BaseModel):
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    message: str

class QueryResultResponse(BaseModel):
    task_id: str
    status: str
    answer: str = ""
    chunks: List[str] = []
    files: List[str] = []
    sources: List[SourceInfo] = []  # Детальная информация об источниках
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
    model: str = "gemma3"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    class Config:
        # Примеры для документации API
        json_schema_extra = {
            "example": {
                "messages": "Привет! Расскажи про искусственный интеллект",
                "model": "yandexgpt",
                "temperature": 0.1,
                "max_tokens": 2000
            }
        }

class GenerateResponse(BaseModel):
    text: str
    model: str = "gemma3"

class QueueStatusResponse(BaseModel):
    department_id: str
    initialized: bool
    max_concurrent: int = 0
    available_slots: int = 0
    processing_count: int = 0
    pending_count: int = 0
    total_active_tasks: int = 0

# Функция для асинхронного выполнения векторного поиска
async def async_vec_search(embedding_model, query, db, n_top_cos: int = 10):
    """Асинхронная обертка для vec_search"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, vec_search, embedding_model, query, db, n_top_cos)
    return result

# Функция для обработки задачи в фоне
async def process_query_task(task_id: str):
    """Асинхронно обрабатывает задачу запроса с поддержкой Yandex Cloud"""
    task = llm_state_manager.get_task_by_id(task_id)
    if not task:
        print(f"Задача {task_id} не найдена")
        return

    department_id = task.department_id
    user_question = task.question
    
    print(f"Начинаем обработку задачи {task_id} для отдела {department_id}")
    
    # Обновляем статус на "обработка"
    llm_state_manager.update_task_status(task_id, "processing")
    
    # Добавляем задачу в список активных
    with llm_state_manager.global_lock:
        if department_id not in llm_state_manager.active_tasks:
            llm_state_manager.active_tasks[department_id] = []
        llm_state_manager.active_tasks[department_id].append(task)
    
    # Получаем семафор для отдела
    semaphore = llm_state_manager.get_department_semaphore(department_id)
    
    if not semaphore:
        error_msg = f"Семафор для отдела {department_id} не найден"
        print(error_msg)
        llm_state_manager.update_task_status(task_id, "failed", error=error_msg)
        return
    
    # Ждем доступный слот в семафоре
    async with semaphore:
        try:
            start_time = time.time()
            
            # Получаем модель встраивания и базу данных
            embedding_model = llm_state_manager.get_department_embedding_model(department_id)
            department_db = llm_state_manager.get_department_db(department_id)
            
            if not embedding_model or not department_db:
                raise ValueError(f"Модель встраивания или база данных для отдела {department_id} не найдены")
            
            print(f"Задача {task_id}: Выполняем векторный поиск...")
            
            # Проверяем, используем ли Yandex Cloud для эмбеддингов
            from config_utils import get_env_bool
            use_yandex_cloud = get_env_bool("USE_YANDEX_CLOUD", False)
            
            try:
                # Выполняем векторный поиск фрагментов асинхронно с тайм-аутом
                search_result = await asyncio.wait_for(
                    async_vec_search(
                        embedding_model, 
                        user_question, 
                        department_db, 
                        n_top_cos=6  # Уменьшено для ускорения
                    ),
                    timeout=EMBEDDING_REQUEST_TIMEOUT
                )
                
                # Распаковываем результат поиска
                if len(search_result) >= 3:
                    top_chunks, scores, metadata = search_result
                    # Создаем detailed_results из metadata
                    detailed_results = []
                    for i, (chunk, score, meta) in enumerate(zip(top_chunks, scores, metadata)):
                        # Извлекаем file_path из metadata
                        file_path = meta.get('file_path', f'unknown_file_{i}')
                        detailed_results.append({
                            'file_path': file_path,
                            'chunk_content': chunk,
                            'metadata': {
                                'page': meta.get('page'),
                                'score': score
                            }
                        })
                    # Для совместимости создаем top_files
                    top_files = [meta.get('file_path', f'unknown_file_{i}') for i, meta in enumerate(metadata)]
                else:
                    top_chunks, scores = search_result
                    detailed_results = []
                    top_files = []
                
                print(f"Задача {task_id}: Векторный поиск выполнен за {time.time() - start_time:.2f} секунд")
                
            except Exception as embedding_error:
                # Обработка специфичных ошибок Yandex Cloud для эмбеддингов
                error_msg = f"Ошибка векторного поиска: {str(embedding_error)}"
                print(f"Задача {task_id}: {error_msg}")
                
                if use_yandex_cloud and "yandex" in str(embedding_error).lower():
                    # Специфичная обработка ошибок Yandex Cloud
                    print(f"Задача {task_id}: Обнаружена ошибка Yandex Cloud эмбеддингов")
                    
                    # Проверяем, включен ли fallback
                    fallback_enabled = get_env_bool("YANDEX_FALLBACK_TO_OLLAMA", True)
                    if fallback_enabled:
                        print(f"Задача {task_id}: Попытка fallback на локальные эмбеддинги...")
                        # В этом случае ошибка будет обработана выше в стеке
                    
                raise embedding_error
            
            # Увеличить паузы между операциями:
            await asyncio.sleep(2.0)  # После embedding
            
            if not top_chunks:
                print(f"Задача {task_id}: Векторный поиск не вернул результатов")
                top_chunks = ["Не найдено релевантных фрагментов для вашего запроса."]
                top_files = []
            
            # Создаем детальную информацию об источниках
            sources_info = []
            
            # Используем детальные результаты, если они доступны
            if detailed_results:
                for i, result in enumerate(detailed_results):
                    # Безопасное извлечение данных с fallback значениями
                    file_path = result.get('file_path', f'unknown_file_{i}')
                    chunk_content = result.get('chunk_content', '')
                    metadata = result.get('metadata', {})
                    
                    file_name = file_path.split('/')[-1] if '/' in file_path else file_path
                    
                    source_info = SourceInfo(
                        file_name=file_name,
                        file_path=file_path,
                        chunk_content=chunk_content,
                        chunk_id=f"chunk_{task_id}_{i}",
                        page_number=metadata.get('page', None),
                        similarity_score=metadata.get('score', None)
                    )
                    sources_info.append(source_info)
            else:
                # Fallback к старому методу
                for i, chunk in enumerate(top_chunks):
                    if i < len(top_files):
                        file_path = top_files[i]
                        file_name = file_path.split('/')[-1] if '/' in file_path else file_path
                        
                        source_info = SourceInfo(
                            file_name=file_name,
                            file_path=file_path,
                            chunk_content=chunk,
                            chunk_id=f"chunk_{task_id}_{i}",
                            page_number=None,
                            similarity_score=None
                        )
                        sources_info.append(source_info)
            
            # Получаем асинхронный экземпляр чата
            async_chat_instance = llm_state_manager.get_department_async_chat(department_id)
            
            if not async_chat_instance:
                raise ValueError(f"Асинхронный экземпляр чата для отдела {department_id} не найден")
            
            print(f"Задача {task_id}: Отправляем запрос к LLM...")
            # Устанавливаем таймаут для запроса к LLM
            response_start_time = time.time()
            
            # Перед LLM запросом
            await asyncio.sleep(1.0) 
            
            try:
                # Выполняем асинхронный запрос к LLM с тайм-аутом
                chat_result = await asyncio.wait_for(
                    async_chat_instance(user_question),
                    timeout=LLM_REQUEST_TIMEOUT
                )
                
                print(f"Задача {task_id}: Ответ от LLM получен за {time.time() - response_start_time:.2f} секунд")
                
            except Exception as llm_error:
                # Обработка специфичных ошибок Yandex Cloud для LLM
                error_msg = f"Ошибка LLM: {str(llm_error)}"
                print(f"Задача {task_id}: {error_msg}")
                
                if use_yandex_cloud and ("yandex" in str(llm_error).lower() or "api" in str(llm_error).lower()):
                    # Специфичная обработка ошибок Yandex Cloud LLM
                    print(f"Задача {task_id}: Обнаружена ошибка Yandex Cloud LLM")
                    
                    # Проверяем, включен ли fallback
                    fallback_enabled = get_env_bool("YANDEX_FALLBACK_TO_OLLAMA", True)
                    if fallback_enabled:
                        print(f"Задача {task_id}: Попытка fallback на локальную LLM...")
                        # В этом случае ошибка будет обработана выше в стеке
                
                raise llm_error
            
            if not chat_result.get("success", True):
                print(f"Задача {task_id}: LLM вернул неуспешный результат")
                result = {
                    "answer": chat_result.get("answer", "Не удалось получить ответ от модели"),
                    "chunks": top_chunks,
                    "files": top_files,
                    "sources": sources_info
                }
            else:
                # Объединяем результаты векторного поиска и LLM
                result = {
                    "answer": chat_result.get("answer", ""),
                    "chunks": chat_result.get("chunks", top_chunks),
                    "files": chat_result.get("files", top_files),
                    "sources": sources_info
                }
            
            total_time = time.time() - start_time
            print(f"Задача {task_id}: Общее время обработки: {total_time:.2f} секунд")
            
            # Обновляем статус на "завершено"
            llm_state_manager.update_task_status(task_id, "completed", result=result)
            
        except asyncio.TimeoutError:
            error_message = f"Задача {task_id}: превышен тайм-аут ({LLM_REQUEST_TIMEOUT} сек)"
            print(error_message)
            llm_state_manager.update_task_status(task_id, "failed", error=error_message)
        except Exception as e:
            error_message = f"Ошибка при обработке задачи {task_id}: {str(e)}"
            print(error_message)
            print(traceback.format_exc())
            
            # Специфичная обработка ошибок Yandex Cloud
            if "yandex" in str(e).lower() or "api" in str(e).lower():
                from config_utils import get_env_bool
                use_yandex_cloud = get_env_bool("USE_YANDEX_CLOUD", False)
                if use_yandex_cloud:
                    error_message = f"Ошибка Yandex Cloud API в задаче {task_id}: {str(e)}"
                    print(f"Задача {task_id}: Специфичная ошибка Yandex Cloud обнаружена")
            
            # Обновляем статус на "ошибка"
            llm_state_manager.update_task_status(task_id, "failed", error=error_message)
        
        finally:
            # Удаляем задачу из списка активных
            with llm_state_manager.global_lock:
                if department_id in llm_state_manager.active_tasks:
                    try:
                        llm_state_manager.active_tasks[department_id].remove(task)
                    except ValueError:
                        pass  # Задача уже была удалена


# Эндпоинты

@router.post("/debug/query-request")
async def debug_query_request(request: QueryRequest):
    """
    Диагностический эндпоинт для отладки проблем с запросами.
    """
    try:
        department_id = request.department_id
        print(f"DEBUG: Получен запрос с department_id='{department_id}', question='{request.question[:50]}...'")
        
        # Проверяем инициализацию отдела
        is_initialized = llm_state_manager.is_department_initialized(department_id)
        print(f"DEBUG: Отдел {department_id} инициализирован: {is_initialized}")
        
        # Получаем список всех инициализированных отделов
        initialized_departments = llm_state_manager.get_initialized_departments()
        print(f"DEBUG: Инициализированные отделы: {initialized_departments}")
        
        # Проверяем состояние менеджера
        with llm_state_manager.global_lock:
            sync_chats = list(llm_state_manager.department_chats.keys())
            async_chats = list(llm_state_manager.department_async_chats.keys())
            databases = list(llm_state_manager.department_databases.keys())
            
        return {
            "request": {
                "department_id": department_id,
                "question": request.question[:100] + "..." if len(request.question) > 100 else request.question
            },
            "state": {
                "is_initialized": is_initialized,
                "initialized_departments": initialized_departments,
                "sync_chats": sync_chats,
                "async_chats": async_chats,
                "databases": databases
            }
        }
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/debug/department-state/{department_id}")
async def debug_department_state(department_id: str):
    """
    Диагностический эндпоинт для проверки состояния конкретного отдела.
    """
    try:
        is_initialized = llm_state_manager.is_department_initialized(department_id)
        is_partially = llm_state_manager.is_department_partially_initialized(department_id)
        
        with llm_state_manager.global_lock:
            state = {
                "department_id": department_id,
                "is_fully_initialized": is_initialized,
                "is_partially_initialized": is_partially,
                "components": {
                    "sync_chat": department_id in llm_state_manager.department_chats,
                    "async_chat": department_id in llm_state_manager.department_async_chats,
                    "database": department_id in llm_state_manager.department_databases,
                    "embedding": department_id in llm_state_manager.department_embedding_models,
                    "semaphore": department_id in llm_state_manager.department_semaphores,
                    "queue": department_id in llm_state_manager.department_queues,
                    "active_tasks": department_id in llm_state_manager.active_tasks
                }
            }
            
            # Добавляем информацию о количестве активных задач
            if department_id in llm_state_manager.active_tasks:
                active_tasks = llm_state_manager.active_tasks[department_id]
                state["active_tasks_count"] = len(active_tasks)
                state["task_statuses"] = [task.status for task in active_tasks]
            else:
                state["active_tasks_count"] = 0
                state["task_statuses"] = []
        
        return state
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.post("/debug/reinitialize/{department_id}")
async def debug_reinitialize_department(department_id: str):
    """
    Принудительная переинициализация отдела при потере состояния.
    """
    try:
        print(f"DEBUG: Принудительная переинициализация отдела {department_id}")
        
        # Сначала принудительно очищаем отдел
        cleanup_result = llm_state_manager.force_cleanup_department(department_id)
        print(f"DEBUG: Результат очистки отдела {department_id}: {cleanup_result}")
        
        # Инициализация для всех отделов
        print(f"DEBUG: Вызываем initialize_llm для отдела {department_id}")
        try:
            success = llm_state_manager.initialize_llm(
                "gemma3",
                "nomic-embed-text", 
                department_id,  # Используем department_id как documents_path для автоматического формирования пути
                department_id,
                reload=True
            )
            print(f"DEBUG: Результат initialize_llm для отдела {department_id}: {success}")
        except Exception as e:
            print(f"DEBUG: Ошибка при вызове initialize_llm для отдела {department_id}: {e}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            raise
        
        if success:
            return {
                "message": f"Отдел {department_id} успешно переинициализирован с очисткой старых данных",
                "success": True,
                "cleanup_result": cleanup_result
            }
        else:
            return {
                "message": f"Ошибка при переинициализации отдела {department_id}",
                "success": False,
                "cleanup_result": cleanup_result
            }
            
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Генерирует ответ на запрос без использования RAG.
    Поддерживает как Yandex Cloud, так и локальный Ollama.
    """
    try:
        # Проверяем конфигурацию и выбираем провайдера
        from config_utils import get_env_bool
        use_yandex_cloud = get_env_bool("USE_YANDEX_CLOUD", False)
        
        if use_yandex_cloud:
            # Используем Yandex Cloud
            logger.info(f"Генерация через Yandex Cloud, модель: {request.model}")
            
            try:
                from yandex_cloud_adapter import get_yandex_adapter
                
                # Создаем модель Yandex Cloud напрямую
                from yandex_llm import create_yandex_llm
                yandex_llm = create_yandex_llm(
                    model=request.model,
                    temperature=getattr(request, 'temperature', 0.1),
                    max_tokens=getattr(request, 'max_tokens', 2000)
                )
                
                # Генерируем ответ асинхронно
                response = await yandex_llm._acall(request.messages)
                
                logger.info(f"Yandex Cloud ответ получен, длина: {len(response)} символов")
                return GenerateResponse(text=response, model=request.model)
                
            except Exception as yandex_error:
                logger.error(f"Ошибка Yandex Cloud: {yandex_error}")
                
                # Проверяем, нужно ли делать fallback на Ollama
                fallback_enabled = get_env_bool("YANDEX_FALLBACK_TO_OLLAMA", True)
                
                if fallback_enabled:
                    logger.warning("Переключаемся на Ollama fallback")
                    # Продолжаем выполнение с Ollama ниже
                else:
                    # Возвращаем ошибку Yandex Cloud
                    return GenerateResponse(
                        text=f"Ошибка Yandex Cloud API: {str(yandex_error)}. Проверьте конфигурацию или попробуйте позже.",
                        model=request.model
                    )
        
        # Используем локальный Ollama (или fallback)
        if not use_yandex_cloud:
            logger.info(f"Генерация через Ollama, модель: {request.model}")
        else:
            logger.warning(f"Fallback на Ollama после ошибки Yandex Cloud")
        
        # Проверяем доступность модели для Ollama
        try:
            llm_state_manager.check_if_model_is_available(request.model)
        except ValueError as model_error:
            # Если модель недоступна в Ollama, но запрашивалась Yandex модель
            if use_yandex_cloud and request.model in ["yandexgpt", "yandexgpt-lite"]:
                return GenerateResponse(
                    text=f"Модель {request.model} доступна только через Yandex Cloud API. Проверьте конфигурацию Yandex Cloud.",
                    model=request.model
                )
            raise model_error
        
        # Создаем экземпляр Ollama модели
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=request.model)
        
        # Отправляем запрос к Ollama
        response = llm.invoke(request.messages)
        
        # Извлекаем ответ из объекта response
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        logger.info(f"Ollama ответ получен, длина: {len(response_text)} символов")
        return GenerateResponse(text=response_text, model=request.model)
        
    except Exception as e:
        error_message = f"Ошибка при обработке запроса на генерацию: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        
        # Возвращаем детальную ошибку в зависимости от типа
        if "yandex" in str(e).lower():
            error_detail = f"Ошибка Yandex Cloud API: {str(e)}"
        elif "ollama" in str(e).lower():
            error_detail = f"Ошибка Ollama: {str(e)}"
        else:
            error_detail = f"Системная ошибка: {str(e)}"
        
        return GenerateResponse(
            text=f"Произошла ошибка при генерации ответа. {error_detail}",
            model=request.model
        )

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Создает задачу для обработки запроса к LLM с использованием RAG.
    Возвращает task_id для отслеживания прогресса.
    """
    department_id = request.department_id
    print(f"API: Получен запрос для отдела '{department_id}', вопрос: '{request.question[:50]}...'")
    
    # Проверяем инициализацию отдела с детальным логированием
    is_initialized = llm_state_manager.is_department_initialized(department_id)
    print(f"API: Отдел '{department_id}' инициализирован: {is_initialized}")
    
    if not is_initialized:
        # Получаем дополнительную информацию для диагностики
        initialized_departments = llm_state_manager.get_initialized_departments()
        is_partially = llm_state_manager.is_department_partially_initialized(department_id)
        
        print(f"API: Доступные инициализированные отделы: {initialized_departments}")
        print(f"API: Отдел '{department_id}' частично инициализирован: {is_partially}")
        
        # Проверяем, все ли словари пусты (полная потеря состояния)
        with llm_state_manager.global_lock:
            sync_chats = list(llm_state_manager.department_chats.keys())
            async_chats = list(llm_state_manager.department_async_chats.keys())
            databases = list(llm_state_manager.department_databases.keys())
            embeddings = list(llm_state_manager.department_embedding_models.keys())
            
            print(f"API: Синхронные чаты: {sync_chats}")
            print(f"API: Асинхронные чаты: {async_chats}")
            
            total_components = len(sync_chats) + len(async_chats) + len(databases) + len(embeddings)
            
        # Если все словари пусты И это отдел 5, пытаемся автоматически восстановить
        if total_components == 0 and department_id in ["5" , "1" , "2" , "3" , "4"]:
            print(f"WARNING: Обнаружена полная потеря состояния! Пытаемся автоматически восстановить отдел {department_id}")
            try:
                auto_restore_success = llm_state_manager.initialize_llm(
                    "gemma3",
                    "nomic-embed-text", 
                    department_id,  # Используем department_id как documents_path для автоматического формирования пути
                    department_id,
                    reload=True
                )
                if auto_restore_success:
                    print(f"SUCCESS: Отдел {department_id} автоматически восстановлен!")
                    # Создаем задачу после успешного восстановления
                    task = llm_state_manager.create_query_task(department_id, request.question)
                    background_tasks.add_task(process_query_task, task.id)
                    return QueryResponse(
                        task_id=task.id,
                        status="pending",
                        message=f"Отдел {department_id} был автоматически восстановлен. Задача создана и добавлена в очередь обработки."
                    )
                else:
                    print(f"ERROR: Не удалось автоматически восстановить отдел {department_id}")
            except Exception as auto_restore_error:
                print(f"ERROR: Ошибка автоматического восстановления: {auto_restore_error}")
        
        # Разные сообщения в зависимости от состояния
        if is_partially:
            error_detail = (
                f"LLM для отдела '{department_id}' частично инициализирован (возможна race condition). "
                f"Попробуйте повторить запрос через несколько секунд или переинициализировать отдел через /llm/debug/reinitialize/{department_id}."
            )
        elif total_components == 0:
            error_detail = (
                f"Обнаружена полная потеря состояния LLM! Все отделы утратили инициализацию. "
                f"Автоматическое восстановление {'выполнено' if department_id == '5' else 'недоступно'}. "
                f"Для ручного восстановления используйте POST /llm/debug/reinitialize/{department_id}."
            )
        else:
            error_detail = (
                f"LLM для отдела '{department_id}' не инициализирован. "
                f"Доступные отделы: {initialized_departments}. "
                f"Инициализируйте отдел через POST /llm/initialize с параметрами: "
                f"model_name, embedding_model_name, documents_path, department_id='{department_id}'."
            )
        
        raise HTTPException(status_code=400, detail=error_detail)
    
    # Создаем новую задачу
    task = llm_state_manager.create_query_task(department_id, request.question)
    
    print(f"Создана задача {task.id} для отдела {department_id}: {request.question[:50]}...")
    
    # Запускаем обработку задачи в фоне
    background_tasks.add_task(process_query_task, task.id)
    
    return QueryResponse(
        task_id=task.id,
        status="pending",
        message=f"Задача создана и добавлена в очередь обработки для отдела {department_id}"
    )

def _check_get_request_rate_limit(task_id: str) -> bool:
    """Проверяет, не превышен ли лимит GET запросов для задачи"""
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    
    # Удаляем старые запросы (старше минуты)
    _get_request_counts[task_id] = [
        timestamp for timestamp in _get_request_counts[task_id] 
        if timestamp > one_minute_ago
    ]
    
    # Проверяем лимит
    if len(_get_request_counts[task_id]) >= MAX_GET_REQUESTS_PER_MINUTE:
        return False
    
    # Добавляем текущий запрос
    _get_request_counts[task_id].append(now)
    return True

@router.get("/query/{task_id}", response_model=QueryResultResponse)
async def get_query_result(task_id: str):
    """
    Получает результат выполнения задачи по её ID.
    Защищен от рекурсии чрезмерным количеством запросов.
    """
    # Защита от рекурсии GET запросов
    if not _check_get_request_rate_limit(task_id):
        raise HTTPException(
            status_code=429, 
            detail=f"Слишком много запросов к задаче {task_id}. Максимум {MAX_GET_REQUESTS_PER_MINUTE} запросов в минуту. Возможна рекурсия фронтенда."
        )
    
    task = llm_state_manager.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
    
    response = QueryResultResponse(
        task_id=task.id,
        status=task.status,
        created_at=task.created_at.isoformat() if task.created_at else "",
        started_at=task.started_at.isoformat() if task.started_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else ""
    )
    
    if task.result:
        response.answer = task.result.get("answer", "")
        response.chunks = task.result.get("chunks", [])
        response.files = task.result.get("files", [])
        response.sources = task.result.get("sources", [])
    
    if task.error:
        response.error = task.error
    
    return response

@router.get("/queue/status/{department_id}", response_model=QueueStatusResponse)
async def get_queue_status(department_id: str):
    """
    Получает статус очереди для указанного отдела.
    """
    status = llm_state_manager.get_department_queue_status(department_id)
    return QueueStatusResponse(**status)

@router.post("/queue/cleanup/{department_id}")
async def cleanup_queue(department_id: str, max_age_minutes: int = 60):
    """
    Очищает завершенные задачи старше указанного времени для отдела.
    """
    llm_state_manager.cleanup_completed_tasks(department_id, max_age_minutes)
    return {"message": f"Очистка завершенных задач для отдела {department_id} выполнена"}

@router.post("/queue/force-cleanup/{department_id}")
async def force_cleanup_department(department_id: str):
    """
    Принудительно очищает все зависшие задачи и сбрасывает семафор для отдела.
    """
    try:
        result = llm_state_manager.force_cleanup_department(department_id)
        return {"message": f"Принудительная очистка отдела {department_id} выполнена", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при принудительной очистке: {str(e)}")

@router.post("/queue/force-cleanup-all")
async def force_cleanup_all_departments():
    """
    Принудительно очищает все зависшие задачи во всех отделах.
    """
    try:
        result = llm_state_manager.force_cleanup_all_departments()
        return {"message": "Принудительная очистка всех отделов выполнена", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при принудительной очистке: {str(e)}")

@router.get("/queue/stuck-tasks")
async def get_stuck_tasks(max_processing_minutes: int = 5):
    """
    Возвращает список зависших задач (обрабатываются дольше указанного времени).
    """
    try:
        stuck_tasks = llm_state_manager.get_stuck_tasks(max_processing_minutes)
        return {"stuck_tasks": stuck_tasks, "max_processing_minutes": max_processing_minutes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении зависших задач: {str(e)}")

@router.post("/initialize")
async def initialize_model(request: InitRequest, db: Session = Depends(get_db)):
    """
    Инициализирует модель LLM для указанного отдела.
    """
    try:
        # Проверяем существование отдела в базе данных
        department = db.query(Department).filter(Department.id == int(request.department_id)).first()
        if not department and request.department_id != "default":
            raise HTTPException(status_code=404, detail=f"Отдел с ID {request.department_id} не найден")
        
        # Вызов функции инициализации с учетом отдела
        success = llm_state_manager.initialize_llm(
            request.model_name, 
            request.embedding_model_name, 
            request.documents_path, 
            request.department_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось инициализировать модель")
            
        return {"message": f"Модель для отдела {request.department_id} успешно инициализирована"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_models():
    """
    Возвращает список всех доступных моделей.
    """
    models = llm_state_manager.get_available_models()
    return models

@router.get("/models/llm")
async def get_llm_models():
    """
    Возвращает список доступных моделей LLM.
    """
    models = llm_state_manager.get_available_models()
    return {"models": models["llm_models"]}

@router.get("/models/embedding")
async def get_embedding_models():
    """
    Возвращает список доступных моделей эмбеддингов.
    """
    models = llm_state_manager.get_available_models()
    return {"models": models["embedding_models"]}

@router.post("/query-sync")
async def query_sync(request: QueryRequest):
    """
    Синхронный запрос к LLM с использованием RAG для обратной совместимости.
    Этот эндпоинт блокирует выполнение до получения результата.
    """
    department_id = request.department_id
    
    # Проверяем инициализацию отдела
    if not llm_state_manager.is_department_initialized(department_id):
        raise HTTPException(
            status_code=400, 
            detail=f"LLM для отдела {department_id} не инициализирован. Сначала инициализируйте его через /llm/initialize."
        )
    
    # Создаем новую задачу
    task = llm_state_manager.create_query_task(department_id, request.question)
    
    print(f"Синхронная обработка задачи {task.id} для отдела {department_id}")
    
    # Сразу обрабатываем задачу
    await process_query_task(task.id)
    
    # Ждем завершения и возвращаем результат
    completed_task = llm_state_manager.get_task_by_id(task.id)
    
    if not completed_task:
        raise HTTPException(status_code=500, detail="Задача потеряна во время обработки")
    
    if completed_task.status == "failed":
        error_message = completed_task.error or "Неизвестная ошибка"
        return {
            "answer": f"Произошла ошибка при обработке запроса: {error_message}",
            "chunks": [],
            "files": []
        }
    
    if completed_task.status == "completed" and completed_task.result:
        return {
            "answer": completed_task.result.get("answer", ""),
            "chunks": completed_task.result.get("chunks", []),
            "files": completed_task.result.get("files", [])
        }
    
    # Если задача еще не завершена
    return {
        "answer": "Обработка не завершена, попробуйте позже",
        "chunks": [],
        "files": []
    }

@router.get("/initialized-departments")
async def get_initialized_departments():
    """
    Возвращает список отделов, для которых уже инициализированы модели LLM.
    """
    departments = llm_state_manager.get_initialized_departments()
    return {"departments": departments}

@router.get("/source/{task_id}/{chunk_id}")
async def get_source_details(task_id: str, chunk_id: str):
    """
    Получает детальную информацию об источнике по ID задачи и ID чанка.
    """
    task = llm_state_manager.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")
    
    if not task.result or "sources" not in task.result:
        raise HTTPException(status_code=404, detail="Информация об источниках не найдена")
    
    sources = task.result.get("sources", [])
    source = next((s for s in sources if hasattr(s, 'chunk_id') and s.chunk_id == chunk_id), None)
    
    if not source:
        raise HTTPException(status_code=404, detail=f"Источник с ID {chunk_id} не найден")
    
    return source

# ===== ЭНДПОИНТЫ ДЛЯ МОНИТОРИНГА И МЕТРИК =====

@router.get("/metrics/current")
async def get_current_metrics():
    """
    Возвращает текущие метрики использования Yandex Cloud API
    """
    try:
        metrics = get_metrics_instance()
        return metrics.get_current_metrics()
    except Exception as e:
        logger.error(f"Ошибка получения текущих метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")

@router.get("/metrics/hourly")
async def get_hourly_metrics(hours: int = 24):
    """
    Возвращает часовые метрики за указанное количество часов
    
    Args:
        hours: Количество часов для получения метрик (по умолчанию 24)
    """
    try:
        if hours < 1 or hours > 168:  # Максимум неделя
            raise HTTPException(status_code=400, detail="Количество часов должно быть от 1 до 168")
        
        metrics = get_metrics_instance()
        return {
            "period_hours": hours,
            "metrics": metrics.get_hourly_metrics(hours)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения часовых метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")

@router.get("/metrics/daily")
async def get_daily_metrics(days: int = 7):
    """
    Возвращает дневные метрики за указанное количество дней
    
    Args:
        days: Количество дней для получения метрик (по умолчанию 7)
    """
    try:
        if days < 1 or days > 30:  # Максимум месяц
            raise HTTPException(status_code=400, detail="Количество дней должно быть от 1 до 30")
        
        metrics = get_metrics_instance()
        return {
            "period_days": days,
            "metrics": metrics.get_daily_metrics(days)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения дневных метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")

@router.get("/metrics/errors")
async def get_error_analysis():
    """
    Возвращает анализ ошибок Yandex Cloud API
    """
    try:
        metrics = get_metrics_instance()
        return metrics.get_error_analysis()
    except Exception as e:
        logger.error(f"Ошибка получения анализа ошибок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения анализа ошибок: {str(e)}")

@router.get("/metrics/performance")
async def get_performance_analysis():
    """
    Возвращает анализ производительности Yandex Cloud API
    """
    try:
        metrics = get_metrics_instance()
        return metrics.get_performance_analysis()
    except Exception as e:
        logger.error(f"Ошибка получения анализа производительности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения анализа производительности: {str(e)}")

@router.get("/metrics/export")
async def export_metrics(format: str = "json"):
    """
    Экспортирует метрики в указанном формате
    
    Args:
        format: Формат экспорта ('json' или 'csv')
    """
    try:
        if format.lower() not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Поддерживаемые форматы: json, csv")
        
        metrics = get_metrics_instance()
        exported_data = metrics.export_metrics(format)
        
        if format.lower() == 'csv':
            from fastapi.responses import Response
            return Response(
                content=exported_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=yandex_metrics.csv"}
            )
        else:
            from fastapi.responses import Response
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=yandex_metrics.json"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта метрик: {str(e)}")

@router.post("/metrics/reset")
async def reset_metrics():
    """
    Сбрасывает все метрики (требует подтверждения)
    """
    try:
        metrics = get_metrics_instance()
        metrics.reset_metrics()
        return {"message": "Все метрики успешно сброшены"}
    except Exception as e:
        logger.error(f"Ошибка сброса метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сброса метрик: {str(e)}")

# ===== ЭНДПОИНТЫ ДЛЯ МОНИТОРИНГА ПРОИЗВОДИТЕЛЬНОСТИ =====

@router.get("/performance/current")
async def get_current_performance():
    """
    Возвращает текущие показатели производительности системы
    """
    try:
        monitor = get_performance_monitor()
        return monitor.get_current_performance()
    except Exception as e:
        logger.error(f"Ошибка получения показателей производительности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения показателей производительности: {str(e)}")

@router.get("/performance/history")
async def get_performance_history(hours: int = 24):
    """
    Возвращает историю производительности за указанное количество часов
    
    Args:
        hours: Количество часов для получения истории (по умолчанию 24)
    """
    try:
        if hours < 1 or hours > 168:  # Максимум неделя
            raise HTTPException(status_code=400, detail="Количество часов должно быть от 1 до 168")
        
        monitor = get_performance_monitor()
        return {
            "period_hours": hours,
            "history": monitor.get_performance_history(hours)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения истории производительности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории производительности: {str(e)}")

@router.get("/performance/summary")
async def get_performance_summary():
    """
    Возвращает сводку производительности системы
    """
    try:
        monitor = get_performance_monitor()
        return monitor.get_performance_summary()
    except Exception as e:
        logger.error(f"Ошибка получения сводки производительности: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения сводки производительности: {str(e)}")

@router.get("/performance/alerts")
async def get_alert_status():
    """
    Возвращает статус всех алертов производительности
    """
    try:
        monitor = get_performance_monitor()
        return monitor.get_alert_status()
    except Exception as e:
        logger.error(f"Ошибка получения статуса алертов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса алертов: {str(e)}")

@router.post("/performance/monitoring/start")
async def start_performance_monitoring():
    """
    Запускает мониторинг производительности
    """
    try:
        monitor = get_performance_monitor()
        await monitor.start_monitoring()
        return {"message": "Мониторинг производительности запущен"}
    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска мониторинга: {str(e)}")

@router.post("/performance/monitoring/stop")
async def stop_performance_monitoring():
    """
    Останавливает мониторинг производительности
    """
    try:
        monitor = get_performance_monitor()
        await monitor.stop_monitoring()
        return {"message": "Мониторинг производительности остановлен"}
    except Exception as e:
        logger.error(f"Ошибка остановки мониторинга: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка остановки мониторинга: {str(e)}")

# ===== КОМБИНИРОВАННЫЕ ЭНДПОИНТЫ =====

@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """
    Возвращает данные для дашборда мониторинга (комбинированная информация)
    """
    try:
        metrics = get_metrics_instance()
        monitor = get_performance_monitor()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_metrics": metrics.get_current_metrics(),
            "performance": monitor.get_current_performance(),
            "error_analysis": metrics.get_error_analysis(),
            "performance_summary": monitor.get_performance_summary(),
            "alerts": monitor.get_alert_status()
        }
    except Exception as e:
        logger.error(f"Ошибка получения данных дашборда: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных дашборда: {str(e)}")

@router.get("/monitoring/health")
async def get_system_health():
    """
    Возвращает общее состояние здоровья системы
    """
    try:
        metrics = get_metrics_instance()
        monitor = get_performance_monitor()
        
        # Получаем текущие метрики
        current_metrics = metrics.get_current_metrics()
        current_performance = monitor.get_current_performance()
        
        # Определяем состояние здоровья
        health_status = "healthy"
        issues = []
        
        # Проверяем уровень ошибок
        error_rate = current_performance.get("api", {}).get("error_rate", 0)
        if error_rate > 0.1:  # Более 10% ошибок
            health_status = "degraded"
            issues.append(f"Высокий уровень ошибок API: {error_rate:.1%}")
        
        # Проверяем время ответа
        avg_response_time = current_performance.get("api", {}).get("average_response_time", 0)
        if avg_response_time > 10:  # Более 10 секунд
            health_status = "degraded"
            issues.append(f"Медленное время ответа: {avg_response_time:.2f}с")
        
        # Проверяем использование CPU
        cpu_percent = current_performance.get("system", {}).get("cpu_percent", 0)
        if cpu_percent > 80:
            health_status = "degraded"
            issues.append(f"Высокая загрузка CPU: {cpu_percent:.1f}%")
        
        # Проверяем использование памяти
        memory_percent = current_performance.get("system", {}).get("memory_percent", 0)
        if memory_percent > 85:
            health_status = "degraded"
            issues.append(f"Высокое использование памяти: {memory_percent:.1f}%")
        
        # Если есть критические проблемы
        if error_rate > 0.5 or avg_response_time > 30 or cpu_percent > 95 or memory_percent > 95:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "metrics_summary": {
                "total_requests": current_metrics.get("total_requests", 0),
                "success_rate": current_metrics.get("success_rate", 0),
                "average_response_time": avg_response_time,
                "error_rate": error_rate
            },
            "system_summary": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "active_threads": current_performance.get("system", {}).get("active_threads", 0)
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения состояния здоровья системы: {e}")
        return {
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# ===== ЭНДПОИНТЫ ДЛЯ КОНФИГУРАЦИИ =====

@router.get("/config/runtime")
async def get_runtime_configuration():
    """
    Возвращает конфигурацию времени выполнения
    """
    try:
        config = get_runtime_config()
        return config
    except Exception as e:
        logger.error(f"Ошибка получения runtime конфигурации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения конфигурации: {str(e)}")

@router.get("/config/validation")
async def validate_configuration():
    """
    Валидирует текущую конфигурацию и возвращает отчет
    """
    try:
        # Пытаемся создать полную конфигурацию
        config = validate_all_config_new()
        
        return {
            "status": "valid",
            "message": "Конфигурация валидна",
            "components": {
                "yandex_cloud": "valid",
                "ollama": "valid", 
                "database": "valid",
                "application": "valid"
            },
            "summary": {
                "environment": config.environment,
                "debug": config.debug,
                "yandex_enabled": True,
                "models_count": {
                    "llm": len(config.yandex_cloud.llm_models),
                    "embedding": len(config.yandex_cloud.embedding_models)
                }
            }
        }
    except Exception as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        
        # Определяем какой компонент вызвал ошибку
        error_component = "unknown"
        if "yandex" in str(e).lower():
            error_component = "yandex_cloud"
        elif "ollama" in str(e).lower():
            error_component = "ollama"
        elif "database" in str(e).lower():
            error_component = "database"
        
        return {
            "status": "invalid",
            "message": f"Ошибка валидации конфигурации: {str(e)}",
            "error_component": error_component,
            "error_details": str(e)
        }

@router.get("/config/models")
async def get_available_models():
    """
    Возвращает список всех доступных моделей
    """
    try:
        config = get_runtime_config()
        yandex_models = config.get("yandex_cloud", {}).get("models", {})
        
        return {
            "yandex_cloud": {
                "enabled": config.get("yandex_cloud", {}).get("enabled", False),
                "llm_models": yandex_models.get("llm_models", []),
                "embedding_models": yandex_models.get("embedding_models", []),
                "default_llm": config.get("yandex_cloud", {}).get("default_llm"),
                "default_embedding": config.get("yandex_cloud", {}).get("default_embedding")
            },
            "ollama": {
                "host": config.get("ollama", {}).get("host"),
                "default_llm": config.get("ollama", {}).get("default_llm"),
                "default_embedding": config.get("ollama", {}).get("default_embedding")
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей: {str(e)}")

@router.get("/config/features")
async def get_feature_flags():
    """
    Возвращает состояние функциональных флагов
    """
    try:
        config = get_runtime_config()
        features = config.get("features", {})
        yandex_config = config.get("yandex_cloud", {})
        
        return {
            "yandex_cloud_enabled": yandex_config.get("enabled", False),
            "monitoring_enabled": features.get("monitoring", False),
            "caching_enabled": features.get("caching", False),
            "fallback_enabled": features.get("fallback", False),
            "metrics_enabled": yandex_config.get("metrics_enabled", False),
            "performance_monitoring": features.get("monitoring", False),
            "debug_mode": config.get("application", {}).get("debug", False),
            "environment": config.get("application", {}).get("environment", "unknown")
        }
    except Exception as e:
        logger.error(f"Ошибка получения feature flags: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения feature flags: {str(e)}")

@router.get("/config/environment")
async def get_environment_info():
    """
    Возвращает информацию о среде выполнения
    """
    try:
        config = get_runtime_config()
        app_config = config.get("application", {})
        
        # Получаем информацию о переменных окружения (без чувствительных данных)
        from config_utils import SUPPORTED_ENV_VARS
        
        env_status = {}
        sensitive_vars = ['api_key', 'secret_key', 'password', 'token']
        
        for var in SUPPORTED_ENV_VARS:
            value = os.getenv(var)
            if value is not None:
                # Проверяем, является ли переменная чувствительной
                is_sensitive = any(sensitive in var.lower() for sensitive in sensitive_vars)
                if is_sensitive:
                    env_status[var] = "***SET***"
                else:
                    env_status[var] = value
            else:
                env_status[var] = None
        
        return {
            "environment": app_config.get("environment", "unknown"),
            "debug": app_config.get("debug", False),
            "log_level": app_config.get("log_level", "INFO"),
            "environment_variables": env_status,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": os.name
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о среде: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о среде: {str(e)}")

@router.post("/config/reload")
async def reload_configuration():
    """
    Перезагружает конфигурацию из переменных окружения
    """
    try:
        # Перезагружаем .env файл
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Валидируем новую конфигурацию
        config = validate_all_config_new()
        
        return {
            "status": "success",
            "message": "Конфигурация успешно перезагружена",
            "timestamp": datetime.now().isoformat(),
            "environment": config.environment,
            "yandex_enabled": True,
            "models_available": {
                "llm": len(config.yandex_cloud.llm_models),
                "embedding": len(config.yandex_cloud.embedding_models)
            }
        }
    except Exception as e:
        logger.error(f"Ошибка перезагрузки конфигурации: {e}")
        return {
            "status": "error",
            "message": f"Ошибка перезагрузки конфигурации: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/config/export")
async def export_configuration(format: str = "json", include_sensitive: bool = False):
    """
    Экспортирует текущую конфигурацию
    
    Args:
        format: Формат экспорта ('json' или 'yaml')
        include_sensitive: Включать ли чувствительные данные
    """
    try:
        if format.lower() not in ['json', 'yaml']:
            raise HTTPException(status_code=400, detail="Поддерживаемые форматы: json, yaml")
        
        config = get_runtime_config()
        
        # Добавляем метаданные
        export_data = {
            "_metadata": {
                "exported_at": datetime.now().isoformat(),
                "format": format,
                "sensitive_included": include_sensitive,
                "version": "1.0"
            },
            "configuration": config
        }
        
        if format.lower() == 'json':
            import json
            content = json.dumps(export_data, indent=2, ensure_ascii=False)
            media_type = "application/json"
            filename = f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            try:
                import yaml
                content = yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
                media_type = "application/x-yaml"
                filename = f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            except ImportError:
                raise HTTPException(status_code=500, detail="PyYAML не установлен для экспорта YAML")
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта конфигурации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта конфигурации: {str(e)}")

@router.get("/config/health")
async def get_configuration_health():
    """
    Проверяет здоровье конфигурации и возвращает статус
    """
    try:
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
        # Проверяем Yandex Cloud конфигурацию
        try:
            from config_utils import YandexCloudConfig
            yandex_config = YandexCloudConfig.from_env()
            health_status["components"]["yandex_cloud"] = {
                "status": "healthy",
                "models_count": len(yandex_config.llm_models) + len(yandex_config.embedding_models),
                "caching_enabled": yandex_config.enable_caching,
                "metrics_enabled": yandex_config.enable_metrics
            }
        except Exception as e:
            health_status["components"]["yandex_cloud"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["issues"].append(f"Yandex Cloud: {str(e)}")
            health_status["overall_status"] = "degraded"
        
        # Проверяем Ollama конфигурацию
        try:
            from config_utils import OllamaConfig
            ollama_config = OllamaConfig.from_env()
            health_status["components"]["ollama"] = {
                "status": "healthy",
                "host": ollama_config.host,
                "timeout": ollama_config.timeout
            }
        except Exception as e:
            health_status["components"]["ollama"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_status["issues"].append(f"Ollama: {str(e)}")
        
        # Проверяем Database конфигурацию
        try:
            from config_utils import DatabaseConfig
            db_config = DatabaseConfig.from_env()
            health_status["components"]["database"] = {
                "status": "healthy",
                "pool_size": db_config.pool_size,
                "max_overflow": db_config.max_overflow
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["issues"].append(f"Database: {str(e)}")
        
        # Добавляем рекомендации
        if health_status["overall_status"] == "healthy":
            health_status["recommendations"].append("Конфигурация оптимальна")
        else:
            health_status["recommendations"].append("Проверьте переменные окружения")
            health_status["recommendations"].append("Убедитесь, что все обязательные параметры установлены")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья конфигурации: {e}")
        return {
            "overall_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
# ===== ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ КЭШЕМ =====

@router.get("/cache/stats")
async def get_cache_statistics():
    """
    Возвращает статистику кэша
    """
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Ошибка получения статистики кэша: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики кэша: {str(e)}")

@router.post("/cache/clear")
async def clear_cache(cache_type: Optional[str] = None):
    """
    Очищает кэш полностью или по типу
    
    Args:
        cache_type: Тип кэша для очистки ('embedding', 'llm_response', 'auth_token', 'document')
    """
    try:
        cache = get_cache()
        
        if cache_type:
            # Очищаем кэш по типу
            if cache_type not in ['embedding', 'llm_response', 'auth_token', 'document']:
                raise HTTPException(
                    status_code=400, 
                    detail="Поддерживаемые типы: embedding, llm_response, auth_token, document"
                )
            
            deleted_count = cache.clear_by_type(cache_type)
            return {
                "message": f"Очищен кэш типа '{cache_type}'",
                "deleted_entries": deleted_count,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Очищаем весь кэш
            deleted_count = cache.clear_all()
            return {
                "message": "Весь кэш очищен",
                "deleted_entries": deleted_count,
                "timestamp": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")

@router.post("/cache/cleanup")
async def cleanup_expired_cache():
    """
    Очищает истекшие записи кэша
    """
    try:
        cache = get_cache()
        expired_count = cache.cleanup_expired()
        
        return {
            "message": "Очистка истекших записей завершена",
            "expired_entries_removed": expired_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка очистки истекших записей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки истекших записей: {str(e)}")

@router.post("/cache/optimize")
async def optimize_cache():
    """
    Оптимизирует кэш (очищает истекшие записи и дефрагментирует)
    """
    try:
        cache = get_cache()
        optimization_result = cache.optimize()
        
        return {
            "message": "Оптимизация кэша завершена",
            "optimization_result": optimization_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка оптимизации кэша: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации кэша: {str(e)}")

@router.get("/cache/health")
async def get_cache_health():
    """
    Проверяет здоровье кэша
    """
    try:
        cache = get_cache()
        stats = cache.get_stats()
        
        # Определяем состояние здоровья кэша
        health_status = "healthy"
        issues = []
        recommendations = []
        
        # Проверяем использование места
        usage_percent = stats.get('usage_percent', 0)
        if usage_percent > 90:
            health_status = "critical"
            issues.append(f"Критическое использование места: {usage_percent:.1f}%")
            recommendations.append("Немедленно очистите кэш или увеличьте лимит")
        elif usage_percent > 75:
            health_status = "warning"
            issues.append(f"Высокое использование места: {usage_percent:.1f}%")
            recommendations.append("Рассмотрите очистку старых записей")
        
        # Проверяем количество истекших записей
        expired_entries = stats.get('expired_entries', 0)
        if expired_entries > 100:
            if health_status == "healthy":
                health_status = "warning"
            issues.append(f"Много истекших записей: {expired_entries}")
            recommendations.append("Запустите очистку истекших записей")
        
        # Проверяем общее количество записей
        total_entries = stats.get('total_entries', 0)
        if total_entries > 10000:
            if health_status == "healthy":
                health_status = "warning"
            issues.append(f"Большое количество записей: {total_entries}")
            recommendations.append("Рассмотрите оптимизацию кэша")
        
        if health_status == "healthy":
            recommendations.append("Кэш работает оптимально")
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "recommendations": recommendations,
            "stats_summary": {
                "total_entries": total_entries,
                "total_size_mb": stats.get('total_size_mb', 0),
                "usage_percent": usage_percent,
                "expired_entries": expired_entries
            }
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья кэша: {e}")
        return {
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/cache/settings")
async def get_cache_settings():
    """
    Возвращает настройки кэша
    """
    try:
        cache = get_cache()
        stats = cache.get_stats()
        
        return {
            "ttl_settings": stats.get('ttl_settings', {}),
            "max_size_mb": stats.get('max_size_mb', 0),
            "cache_directory": stats.get('cache_dir', ''),
            "backend_type": "filesystem",
            "features": {
                "automatic_cleanup": True,
                "size_management": True,
                "type_based_clearing": True,
                "statistics_tracking": True
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения настроек кэша: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек кэша: {str(e)}")