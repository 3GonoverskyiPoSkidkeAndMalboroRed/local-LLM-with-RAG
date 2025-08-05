"""
Специализированный RAG сервис для Yandex Cloud API
Обеспечивает эффективную работу с документами и контекстным поиском
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from yandex_cloud_adapter import YandexCloudAdapter, get_yandex_adapter
from yandex_embeddings import YandexEmbeddings, create_yandex_embeddings
from yandex_error_handler import get_error_handler
from yandex_cache import get_cache
from document_loader import vec_search

logger = logging.getLogger(__name__)

@dataclass
class RAGContext:
    """Контекст для RAG операции"""
    query: str
    department_id: str
    max_chunks: int = 5
    similarity_threshold: float = 0.7
    include_metadata: bool = True

@dataclass
class RAGResult:
    """Результат RAG операции"""
    answer: str
    sources: List[Dict[str, Any]]
    chunks_used: List[str]
    similarity_scores: List[float]
    tokens_used: int
    processing_time: float
    model_used: str

@dataclass
class RAGMetrics:
    """Метрики RAG операций"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_response_time: float = 0.0
    average_chunks_used: float = 0.0
    cache_hit_rate: float = 0.0
    last_query_time: Optional[datetime] = None

class YandexRAGService:
    """
    Специализированный сервис для RAG операций с Yandex Cloud
    """
    
    def __init__(
        self,
        llm_model: str = "yandexgpt",
        embedding_model: str = "text-search-query",
        cache_enabled: bool = True,
        max_retries: int = 3
    ):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        
        # Инициализация компонентов
        self._llm_adapter: Optional[YandexCloudAdapter] = None
        self._embeddings: Optional[YandexEmbeddings] = None
        self._error_handler = get_error_handler()
        self._cache = get_cache() if cache_enabled else None
        self._metrics = RAGMetrics()
        
        logger.info(f"Инициализирован YandexRAGService с моделями: LLM={llm_model}, Embeddings={embedding_model}")
    
    async def _get_llm_adapter(self) -> YandexCloudAdapter:
        """Получение LLM адаптера"""
        if self._llm_adapter is None:
            self._llm_adapter = await get_yandex_adapter()
        return self._llm_adapter
    
    async def _get_embeddings(self) -> YandexEmbeddings:
        """Получение embeddings модели"""
        if self._embeddings is None:
            self._embeddings = create_yandex_embeddings(
                model=self.embedding_model,
                cache_enabled=self.cache_enabled
            )
        return self._embeddings
    
    def _generate_cache_key(self, context: RAGContext) -> str:
        """Генерация ключа кэша для RAG запроса"""
        import hashlib
        cache_data = {
            "query": context.query,
            "department_id": context.department_id,
            "max_chunks": context.max_chunks,
            "similarity_threshold": context.similarity_threshold,
            "model": self.llm_model
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _search_relevant_chunks(
        self, 
        context: RAGContext, 
        db_session
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """Поиск релевантных чанков документов"""
        try:
            from document_loader import load_documents_into_database
            
            # Получаем Chroma vectorstore для данного отдела
            # Принудительно перезагружаем документы для исправления проблем с размерностью
            vectorstore = load_documents_into_database(
                model_name=self.embedding_model,
                documents_path=context.department_id,
                department_id=context.department_id,
                reload=True  # Перезагружаем документы для исправления проблем
            )
            
            embeddings = await self._get_embeddings()
            
            # Выполняем векторный поиск
            chunks, scores, metadata = vec_search(
                embedding_model=embeddings,
                query=context.query,
                db=vectorstore,  # Передаем Chroma vectorstore
                n_top_cos=context.max_chunks
            )
            
            # Фильтруем по порогу схожести
            filtered_chunks = []
            filtered_scores = []
            filtered_results = []
            
            for chunk, score, meta in zip(chunks, scores, metadata):
                if score >= context.similarity_threshold:
                    filtered_chunks.append(chunk)
                    filtered_scores.append(score)
                    filtered_results.append({
                        "chunk": chunk,
                        "score": score,
                        "metadata": meta if context.include_metadata else {}
                    })
            
            logger.debug(f"Найдено {len(filtered_chunks)} релевантных чанков из {len(chunks)}")
            return filtered_chunks, filtered_scores, filtered_results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске чанков: {e}")
            raise
    
    def _build_rag_prompt(self, query: str, chunks: List[str]) -> str:
        """Построение промпта для RAG"""
        context = "\n\n".join([f"Контекст {i+1}: {chunk}" for i, chunk in enumerate(chunks)])
        
        prompt = f"""Ты - полезный ассистент, который отвечает на вопросы на основе предоставленного контекста.

Контекст:
{context}

Вопрос: {query}

Инструкции:
1. Отвечай ТОЛЬКО на основе предоставленного контекста
2. Если в контексте нет информации для ответа, скажи об этом
3. Используй информацию из контекста максимально точно
4. Если нужно, ссылайся на конкретные части контекста

Ответ:"""
        
        return prompt
    
    async def query_with_rag(
        self, 
        context: RAGContext, 
        db_session,
        use_cache: bool = True
    ) -> RAGResult:
        """
        Выполнение RAG запроса с кэшированием и обработкой ошибок
        """
        start_time = datetime.now()
        
        try:
            # Проверяем кэш
            if use_cache and self._cache:
                cache_key = self._generate_cache_key(context)
                cached_result = self._cache.get_rag_result(cache_key)
                if cached_result:
                    self._metrics.cache_hit_rate = (
                        (self._metrics.cache_hit_rate * self._metrics.total_queries + 1) / 
                        (self._metrics.total_queries + 1)
                    )
                    logger.info(f"RAG результат загружен из кэша")
                    return cached_result
            
            # Выполняем RAG операцию с retry
            result = await self._error_handler.execute_with_retry(
                self._execute_rag_query,
                "RAG query",
                context,
                db_session
            )
            
            # Обновляем метрики
            self._update_metrics(True, start_time, len(result.chunks_used))
            
            # Сохраняем в кэш
            if use_cache and self._cache:
                cache_key = self._generate_cache_key(context)
                self._cache.set_rag_result(cache_key, result)
            
            return result
            
        except Exception as e:
            self._update_metrics(False, start_time, 0)
            logger.error(f"Ошибка при выполнении RAG запроса: {e}")
            raise
    
    async def _execute_rag_query(
        self, 
        context: RAGContext, 
        db_session
    ) -> RAGResult:
        """Внутреннее выполнение RAG запроса"""
        start_time = datetime.now()
        
        # Поиск релевантных чанков
        chunks, scores, metadata = await self._search_relevant_chunks(context, db_session)
        
        if not chunks:
            return RAGResult(
                answer="Извините, не удалось найти релевантную информацию для вашего вопроса.",
                sources=[],
                chunks_used=[],
                similarity_scores=[],
                tokens_used=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                model_used=self.llm_model
            )
        
        # Построение промпта
        prompt = self._build_rag_prompt(context.query, chunks)
        
        # Генерация ответа
        llm_adapter = await self._get_llm_adapter()
        response = await llm_adapter.generate_text(
            messages=prompt,
            model=self.llm_model,
            temperature=0.1,
            max_tokens=2000
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RAGResult(
            answer=response,
            sources=metadata,
            chunks_used=chunks,
            similarity_scores=scores,
            tokens_used=len(response.split()),  # Приблизительный подсчет
            processing_time=processing_time,
            model_used=self.llm_model
        )
    
    def _update_metrics(self, success: bool, start_time: datetime, chunks_used: int):
        """Обновление метрик"""
        self._metrics.total_queries += 1
        self._metrics.last_query_time = datetime.now()
        
        if success:
            self._metrics.successful_queries += 1
        else:
            self._metrics.failed_queries += 1
        
        # Обновляем среднее время ответа
        response_time = (datetime.now() - start_time).total_seconds()
        if self._metrics.total_queries == 1:
            self._metrics.average_response_time = response_time
            self._metrics.average_chunks_used = chunks_used
        else:
            self._metrics.average_response_time = (
                (self._metrics.average_response_time * (self._metrics.total_queries - 1) + response_time) /
                self._metrics.total_queries
            )
            self._metrics.average_chunks_used = (
                (self._metrics.average_chunks_used * (self._metrics.total_queries - 1) + chunks_used) /
                self._metrics.total_queries
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик сервиса"""
        return {
            "total_queries": self._metrics.total_queries,
            "successful_queries": self._metrics.successful_queries,
            "failed_queries": self._metrics.failed_queries,
            "success_rate": (
                self._metrics.successful_queries / self._metrics.total_queries 
                if self._metrics.total_queries > 0 else 0
            ),
            "average_response_time": self._metrics.average_response_time,
            "average_chunks_used": self._metrics.average_chunks_used,
            "cache_hit_rate": self._metrics.cache_hit_rate,
            "last_query_time": self._metrics.last_query_time.isoformat() if self._metrics.last_query_time else None,
            "model_used": self.llm_model,
            "embedding_model": self.embedding_model
        }
    
    def reset_metrics(self):
        """Сброс метрик"""
        self._metrics = RAGMetrics()

# Глобальный экземпляр сервиса
_rag_service: Optional[YandexRAGService] = None

async def get_rag_service() -> YandexRAGService:
    """Получение глобального экземпляра RAG сервиса"""
    global _rag_service
    if _rag_service is None:
        _rag_service = YandexRAGService()
    return _rag_service

async def close_rag_service():
    """Закрытие RAG сервиса"""
    global _rag_service
    if _rag_service:
        # Закрываем адаптеры
        if _rag_service._llm_adapter:
            await _rag_service._llm_adapter.close()
        _rag_service = None 