"""
Yandex Cloud Embeddings интеграция для langchain
Обеспечивает совместимость с существующим кодом через langchain интерфейс
"""

import asyncio
import logging
import hashlib
import json
import os
import pickle
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_core.embeddings import Embeddings

from yandex_cloud_adapter import YandexCloudAdapter, YandexCloudConfig, get_yandex_adapter
from config_utils import get_env_bool, get_env_var
from yandex_cache import get_cache

logger = logging.getLogger(__name__)

class YandexEmbeddings(Embeddings):
    """
    Yandex Cloud Embeddings для интеграции с langchain
    Совместим с OllamaEmbeddings интерфейсом
    """
    
    def __init__(
        self,
        model: str = "text-search-doc",
        base_url: str = None,  # Игнорируется для совместимости
        cache_dir: str = None,  # Игнорируется, используется централизованный кэш
        cache_enabled: bool = True,
        **kwargs
    ):
        """
        Инициализация YandexEmbeddings
        
        Args:
            model: Модель эмбеддингов Yandex Cloud
            base_url: Игнорируется (для совместимости с Ollama)
            cache_dir: Игнорируется, используется централизованный кэш
            cache_enabled: Включение кэширования
            **kwargs: Дополнительные параметры
        """
        self.model = model
        self.cache_enabled = cache_enabled
        self._adapter: Optional[YandexCloudAdapter] = None
        
        # Используем централизованный кэш
        if self.cache_enabled:
            self.cache = get_cache()
            logger.info(f"Используется централизованный кэш для эмбеддингов")
        else:
            self.cache = None
        
        logger.info(f"Инициализирован YandexEmbeddings с моделью {model}")
    
    async def _get_adapter(self) -> YandexCloudAdapter:
        """Получение адаптера Yandex Cloud"""
        if self._adapter is None:
            self._adapter = await get_yandex_adapter()
        return self._adapter
    
    def _load_from_cache(self, text: str) -> Optional[List[float]]:
        """Загрузка эмбеддинга из централизованного кэша"""
        if not self.cache_enabled or not self.cache:
            return None
        
        try:
            embedding = self.cache.get_embedding(text, self.model)
            if embedding:
                logger.debug(f"Эмбеддинг загружен из кэша для модели {self.model}")
            return embedding
        except Exception as e:
            logger.warning(f"Ошибка загрузки из кэша: {e}")
            return None
    
    def _save_to_cache(self, text: str, embedding: List[float]) -> None:
        """Сохранение эмбеддинга в централизованный кэш"""
        if not self.cache_enabled or not self.cache:
            return
        
        try:
            success = self.cache.set_embedding(text, self.model, embedding)
            if success:
                logger.debug(f"Эмбеддинг сохранен в кэш для модели {self.model}")
            else:
                logger.warning(f"Не удалось сохранить эмбеддинг в кэш")
        except Exception as e:
            logger.warning(f"Ошибка сохранения в кэш: {e}")
    
    def _batch_texts_with_cache(self, texts: List[str]) -> tuple[List[str], Dict[int, List[float]]]:
        """
        Разделение текстов на те, что есть в кэше, и те, что нужно обработать
        
        Returns:
            tuple: (тексты для обработки, словарь {индекс: эмбеддинг} из кэша)
        """
        if not self.cache_enabled or not self.cache:
            # Если кэш отключен, обрабатываем все тексты
            return [(i, text) for i, text in enumerate(texts)], {}
        
        try:
            # Используем batch операцию централизованного кэша
            cached_embeddings_list, missing_texts = self.cache.get_embeddings_batch(texts, self.model)
            
            # Преобразуем в нужный формат
            texts_to_process = []
            cached_embeddings = {}
            
            for i, (text, embedding) in enumerate(zip(texts, cached_embeddings_list)):
                if embedding is not None:
                    cached_embeddings[i] = embedding
                else:
                    texts_to_process.append((i, text))
            
            logger.debug(f"Из кэша: {len(cached_embeddings)}, к обработке: {len(texts_to_process)}")
            return texts_to_process, cached_embeddings
            
        except Exception as e:
            logger.warning(f"Ошибка работы с кэшем, обрабатываем все тексты: {e}")
            return [(i, text) for i, text in enumerate(texts)], {}
    
    async def _aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Асинхронное создание эмбеддингов для документов"""
        if not texts:
            return []
        
        try:
            # Проверяем кэш
            texts_to_process, cached_embeddings = self._batch_texts_with_cache(texts)
            
            # Если все эмбеддинги в кэше
            if not texts_to_process:
                logger.info(f"Все {len(texts)} эмбеддингов загружены из кэша")
                return [cached_embeddings[i] for i in range(len(texts))]
            
            # Обрабатываем тексты, которых нет в кэше
            adapter = await self._get_adapter()
            texts_for_api = [text for _, text in texts_to_process]
            
            logger.info(f"Создание {len(texts_for_api)} эмбеддингов через Yandex Cloud API")
            new_embeddings = await adapter.create_embeddings(texts_for_api, self.model)
            
            # Сохраняем новые эмбеддинги в кэш
            for (original_index, text), embedding in zip(texts_to_process, new_embeddings):
                self._save_to_cache(text, embedding)
                cached_embeddings[original_index] = embedding
            
            # Собираем результат в правильном порядке
            result = [cached_embeddings[i] for i in range(len(texts))]
            
            logger.info(f"Создано эмбеддингов: {len(new_embeddings)}, из кэша: {len(texts) - len(new_embeddings)}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддингов: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Синхронное создание эмбеддингов для документов с кэшированием
        
        Args:
            texts: Список текстов для создания эмбеддингов
            
        Returns:
            Список векторов эмбеддингов
        """
        # Проверяем кэш перед созданием эмбеддингов
        try:
            from yandex_cache import get_cache
            cache = get_cache()
            
            # Получаем эмбеддинги из кэша
            cached_embeddings, missing_texts = cache.get_embeddings_batch(texts, self.model)
            
            if not missing_texts:
                # Все эмбеддинги найдены в кэше
                logger.info(f"Все {len(texts)} эмбеддингов загружены из кэша")
                return [emb for emb in cached_embeddings if emb is not None]
            
            logger.info(f"Из кэша загружено: {len(texts) - len(missing_texts)}/{len(texts)} эмбеддингов")
            
        except ImportError:
            logger.warning("Кэш недоступен, создаем эмбеддинги без кэширования")
            cached_embeddings = [None] * len(texts)
            missing_texts = texts
        
        # Создаем эмбеддинги для отсутствующих текстов
        if missing_texts:
            # Запускаем асинхронный метод в синхронном контексте
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # Если цикл уже запущен, создаем новый в отдельном потоке
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, missing_texts, 'documents')
                    new_embeddings = future.result()
            else:
                new_embeddings = loop.run_until_complete(self._aembed_documents(missing_texts))
            
            # Сохраняем новые эмбеддинги в кэш
            try:
                cache.set_embeddings_batch(missing_texts, self.model, new_embeddings)
            except:
                pass  # Игнорируем ошибки кэширования
            
            # Объединяем кэшированные и новые эмбеддинги
            result = []
            missing_idx = 0
            
            for i, cached_emb in enumerate(cached_embeddings):
                if cached_emb is not None:
                    result.append(cached_emb)
                else:
                    if missing_idx < len(new_embeddings):
                        result.append(new_embeddings[missing_idx])
                        missing_idx += 1
                    else:
                        # Fallback на пустой вектор
                        result.append([0.0] * 768)
            
            return result
        
        # Возвращаем только кэшированные эмбеддинги
        return [emb for emb in cached_embeddings if emb is not None]
    
    async def _aembed_query(self, text: str) -> List[float]:
        """Асинхронное создание эмбеддинга для поискового запроса"""
        try:
            # Проверяем кэш
            cached_embedding = self._load_from_cache(text)
            
            if cached_embedding is not None:
                logger.debug("Эмбеддинг запроса загружен из кэша")
                return cached_embedding
            
            # Создаем эмбеддинг через API
            adapter = await self._get_adapter()
            
            logger.debug("Создание эмбеддинга запроса через Yandex Cloud API")
            embeddings = await adapter.create_embeddings([text], self.model)
            
            if embeddings:
                embedding = embeddings[0]
                # Сохраняем в кэш
                self._save_to_cache(text, embedding)
                return embedding
            else:
                raise ValueError("Пустой ответ от API эмбеддингов")
                
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга запроса: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Синхронное создание эмбеддинга для поискового запроса с кэшированием
        
        Args:
            text: Текст запроса
            
        Returns:
            Вектор эмбеддинга
        """
        # Проверяем кэш перед созданием эмбеддинга
        try:
            from yandex_cache import get_cached_embedding, cache_embedding
            
            # Пытаемся получить из кэша
            cached_embedding = get_cached_embedding(text, self.model)
            if cached_embedding is not None:
                logger.debug("Эмбеддинг запроса загружен из кэша")
                return cached_embedding
            
        except ImportError:
            logger.warning("Кэш недоступен, создаем эмбеддинг без кэширования")
        
        # Создаем эмбеддинг
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # Если цикл уже запущен, создаем новый в отдельном потоке
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_in_new_loop, [text], 'query')
                result = future.result()
                embedding = result[0] if result else []
        else:
            embedding = loop.run_until_complete(self._aembed_query(text))
        
        # Сохраняем в кэш
        try:
            cache_embedding(text, self.model, embedding)
        except:
            pass  # Игнорируем ошибки кэширования
        
        return embedding
    
    def _run_in_new_loop(self, texts: List[str], mode: str) -> List[List[float]]:
        """Запуск в новом event loop"""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            if mode == 'documents':
                return new_loop.run_until_complete(self._aembed_documents(texts))
            elif mode == 'query':
                result = new_loop.run_until_complete(self._aembed_query(texts[0]))
                return [result]
            else:
                raise ValueError(f"Неизвестный режим: {mode}")
        finally:
            new_loop.close()
    
    def clear_cache(self) -> int:
        """
        Очистка кэша эмбеддингов
        
        Returns:
            Количество удаленных файлов
        """
        if not self.cache_enabled or not self.cache_dir.exists():
            return 0
        
        deleted_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
                deleted_count += 1
            
            logger.info(f"Очищен кэш эмбеддингов: удалено {deleted_count} файлов")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша
        
        Returns:
            Словарь со статистикой кэша
        """
        if not self.cache_enabled or not self.cache_dir.exists():
            return {
                "cache_enabled": False,
                "cache_dir": str(self.cache_dir),
                "files_count": 0,
                "total_size_mb": 0
            }
        
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cache_enabled": True,
                "cache_dir": str(self.cache_dir),
                "files_count": len(cache_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {
                "cache_enabled": True,
                "cache_dir": str(self.cache_dir),
                "error": str(e)
            }

# Фабричная функция для создания совместимых эмбеддингов
def create_yandex_embeddings(
    model: str = "text-search-doc",
    base_url: str = None,  # Игнорируется для совместимости
    cache_enabled: bool = True,
    **kwargs
) -> YandexEmbeddings:
    """
    Создание YandexEmbeddings с совместимостью с OllamaEmbeddings
    
    Args:
        model: Модель эмбеддингов
        base_url: Игнорируется (для совместимости с Ollama)
        cache_enabled: Включение кэширования
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр YandexEmbeddings
    """
    return YandexEmbeddings(
        model=model,
        cache_enabled=cache_enabled,
        **kwargs
    )

# Функция для автоматического выбора провайдера эмбеддингов
def create_embeddings(
    model: str = "text-search-doc",
    base_url: str = None,
    **kwargs
) -> Embeddings:
    """
    Создание эмбеддингов только через Yandex Cloud.
    Ollama fallback отключен для полного использования Yandex API.
    
    Args:
        model: Модель эмбеддингов Yandex Cloud
        base_url: Игнорируется (для совместимости)
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр YandexEmbeddings
    """
    use_yandex_cloud = get_env_bool("USE_YANDEX_CLOUD", False)
    
    if use_yandex_cloud:
        logger.info(f"Используем YandexEmbeddings с моделью {model}")
        return create_yandex_embeddings(model=model, **kwargs)
    else:
        raise ValueError(
            "❌ Yandex Cloud отключен! Для работы RAG функционала установите USE_YANDEX_CLOUD=true. "
            "Ollama fallback отключен для обеспечения полного использования Yandex API."
        )

# Глобальный экземпляр для кэширования
_global_embeddings_cache: Dict[str, YandexEmbeddings] = {}

def get_cached_embeddings(model: str = "text-search-doc") -> YandexEmbeddings:
    """
    Получение кэшированного экземпляра YandexEmbeddings
    
    Args:
        model: Модель эмбеддингов
        
    Returns:
        Кэшированный экземпляр YandexEmbeddings
    """
    if model not in _global_embeddings_cache:
        _global_embeddings_cache[model] = create_yandex_embeddings(model=model)
        logger.info(f"Создан кэшированный экземпляр YandexEmbeddings для модели {model}")
    
    return _global_embeddings_cache[model]