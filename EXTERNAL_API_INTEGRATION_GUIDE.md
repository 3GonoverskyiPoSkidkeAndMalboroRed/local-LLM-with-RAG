# Руководство по интеграции внешнего API ИИ

## Обзор изменений

Данное руководство описывает процесс перехода от локального Ollama к внешним API ИИ (OpenAI, Claude, Gemini и др.) с использованием LangChain.

## Структура изменений

### 1. Новые зависимости

```python
# requirements.txt - добавить:
langchain==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.1.0
langchain-google-genai==0.0.6
langchain-community==0.0.20
chromadb==0.4.22
sentence-transformers==2.2.2
```

### 2. Конфигурация API провайдеров

```python
# server/config/ai_config.py
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AIProviderConfig:
    api_key: str
    model: str
    base_url: str = None
    max_tokens: int = 4000
    temperature: float = 0.7

class AIConfig:
    def __init__(self):
        self.providers = {
            "openai": AIProviderConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            ),
            "anthropic": AIProviderConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet"),
                base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            ),
            "google": AIProviderConfig(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=os.getenv("GOOGLE_MODEL", "gemini-pro"),
                base_url=os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com")
            )
        }
        
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "openai")
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
```

### 3. Обновленный LLM модуль

```python
# server/llm.py
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.llms import GoogleGenerativeAI
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from typing import Dict, List, Any
import chromadb

from config.ai_config import AIConfig

class ExternalLLMService:
    def __init__(self):
        self.config = AIConfig()
        self.vector_store = None
        self.chat_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
    def initialize_vector_store(self, documents_path: str):
        """Инициализация векторной базы данных"""
        # Создание embeddings
        embeddings = self._get_embeddings()
        
        # Создание векторного хранилища
        self.vector_store = Chroma(
            persist_directory=self.config.vector_db_path,
            embedding_function=embeddings
        )
        
    def _get_embeddings(self):
        """Получение модели embeddings в зависимости от провайдера"""
        provider = self.config.default_provider
        
        if provider == "openai":
            return OpenAIEmbeddings(
                openai_api_key=self.config.providers["openai"].api_key,
                model="text-embedding-ada-002"
            )
        elif provider == "anthropic":
            # Используем HuggingFace embeddings для Claude
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def _get_llm(self, provider: str = None):
        """Получение LLM модели"""
        if not provider:
            provider = self.config.default_provider
            
        config = self.config.providers[provider]
        
        if provider == "openai":
            return ChatOpenAI(
                openai_api_key=config.api_key,
                model_name=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                anthropic_api_key=config.api_key,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
        elif provider == "google":
            return GoogleGenerativeAI(
                google_api_key=config.api_key,
                model=config.model,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def create_chat_chain(self, provider: str = None):
        """Создание цепочки для чата"""
        llm = self._get_llm(provider)
        
        self.chat_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            ),
            memory=self.memory,
            return_source_documents=True
        )
        
        return self.chat_chain
    
    async def query(self, question: str, provider: str = None) -> Dict[str, Any]:
        """Выполнение запроса к ИИ"""
        if not self.chat_chain:
            self.create_chat_chain(provider)
            
        try:
            result = await self.chat_chain.ainvoke({
                "question": question
            })
            
            return {
                "answer": result["answer"],
                "source_documents": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    } for doc in result["source_documents"]
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "answer": "Произошла ошибка при обработке запроса"
            }

# Глобальный экземпляр сервиса
llm_service = ExternalLLMService()
```

### 4. Обновленные маршруты

```python
# server/routes/llm_routes.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
import asyncio

from database import get_db
from llm import llm_service
from models_db import QueryTask

router = APIRouter(prefix="/llm", tags=["llm"])

class QueryRequest(BaseModel):
    question: str
    department_id: str = "default"
    provider: str = None

class QueryResponse(BaseModel):
    task_id: str
    status: str
    message: str

class QueryResultResponse(BaseModel):
    task_id: str
    status: str
    answer: str = ""
    source_documents: List[Dict] = []
    error: str = ""
    created_at: str = ""
    completed_at: str = ""

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Асинхронный запрос к ИИ"""
    task_id = str(uuid.uuid4())
    
    # Создание задачи в БД
    task = QueryTask(
        task_id=task_id,
        question=request.question,
        department_id=request.department_id,
        status="pending"
    )
    db.add(task)
    db.commit()
    
    # Добавление фоновой задачи
    background_tasks.add_task(
        process_query_task,
        task_id,
        request.question,
        request.provider,
        db
    )
    
    return QueryResponse(
        task_id=task_id,
        status="pending",
        message="Запрос принят в обработку"
    )

@router.post("/query-sync")
async def query_sync(request: QueryRequest):
    """Синхронный запрос к ИИ"""
    try:
        result = await llm_service.query(request.question, request.provider)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_query_task(task_id: str, question: str, provider: str, db: Session):
    """Обработка задачи в фоновом режиме"""
    try:
        # Обновление статуса
        task = db.query(QueryTask).filter(QueryTask.task_id == task_id).first()
        task.status = "processing"
        db.commit()
        
        # Выполнение запроса
        result = await llm_service.query(question, provider)
        
        # Обновление результата
        task.status = "completed"
        task.answer = result.get("answer", "")
        task.error = result.get("error", "")
        task.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Обработка ошибок
        task = db.query(QueryTask).filter(QueryTask.task_id == task_id).first()
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()

@router.get("/query/{task_id}", response_model=QueryResultResponse)
async def get_query_result(task_id: str, db: Session = Depends(get_db)):
    """Получение результата задачи"""
    task = db.query(QueryTask).filter(QueryTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return QueryResultResponse(
        task_id=task.task_id,
        status=task.status,
        answer=task.answer,
        error=task.error,
        created_at=task.created_at.isoformat() if task.created_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else ""
    )
```

### 5. Обработчик документов

```python
# server/document_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from typing import List, Dict
import os

class DocumentProcessor:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def process_document(self, file_path: str, metadata: Dict = None) -> bool:
        """Обработка документа и добавление в векторную БД"""
        try:
            # Определение типа файла
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Загрузка документа
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_extension == '.txt':
                loader = TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            documents = loader.load()
            
            # Добавление метаданных
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
            
            # Разбиение на чанки
            chunks = self.text_splitter.split_documents(documents)
            
            # Добавление в векторную БД
            self.vector_store.add_documents(chunks)
            
            return True
            
        except Exception as e:
            print(f"Error processing document {file_path}: {e}")
            return False
```

### 6. Переменные окружения

```bash
# .env файл
# AI Providers
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1

ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-sonnet
ANTHROPIC_BASE_URL=https://api.anthropic.com

GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-pro
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com

# Default provider
DEFAULT_AI_PROVIDER=openai

# Vector database
VECTOR_DB_PATH=./vector_db

# Rate limiting
MAX_REQUESTS_PER_MINUTE=60
```

## Миграция с Ollama

### Шаги миграции:

1. **Установка новых зависимостей**
```bash
pip install langchain langchain-openai langchain-anthropic chromadb sentence-transformers
```

2. **Обновление docker-compose.yml**
```yaml
# Удалить Ollama сервис
# Добавить переменные окружения для API ключей
```

3. **Создание новых таблиц БД**
```sql
-- Таблица для хранения задач запросов
CREATE TABLE query_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    error TEXT,
    department_id VARCHAR(255),
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);
```

4. **Обновление фронтенда**
- Изменить URL эндпоинтов
- Добавить выбор провайдера ИИ
- Обновить обработку ответов

## Тестирование интеграции

```python
# test_external_api.py
import asyncio
from llm import llm_service

async def test_query():
    # Инициализация
    llm_service.initialize_vector_store("./documents")
    
    # Тестовый запрос
    result = await llm_service.query(
        "Что такое машинное обучение?",
        provider="openai"
    )
    
    print("Ответ:", result["answer"])
    print("Источники:", result["source_documents"])

if __name__ == "__main__":
    asyncio.run(test_query())
```

## Мониторинг и логирование

```python
# server/utils/ai_monitor.py
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_ai_calls(func):
    """Декоратор для мониторинга вызовов ИИ"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"AI call successful: {func.__name__}, duration: {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"AI call failed: {func.__name__}, duration: {duration:.2f}s, error: {e}")
            raise
    
    return wrapper
```

## Заключение

Данная интеграция позволяет:

1. **Легко переключаться** между разными провайдерами ИИ
2. **Масштабировать** систему без локальных ресурсов
3. **Использовать** самые современные модели ИИ
4. **Сохранить** существующую архитектуру приложения
5. **Добавить** новые возможности (многомодельность, fallback)

Интеграция полностью совместима с существующим кодом и требует минимальных изменений в других частях приложения. 