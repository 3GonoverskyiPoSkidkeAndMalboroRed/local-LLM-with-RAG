"""
Система кэширования для Yandex Cloud интеграции
Обеспечивает кэширование эмбеддингов, токенов аутентификации и ответов LLM
"""

import os
import json
import pickle
import hashlib
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Запись в кэше"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Проверяет, истекла ли запись"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Обновляет время последнего доступа и счетчик"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class CacheBackend(ABC):
    """Абстрактный базовый класс для бэкендов кэширования"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Получить значение из кэша"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None, metadata: Dict[str, Any] = None) -> bool:
        """Сохранить значение в кэш"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """Очистить весь кэш"""
        pass
    
    @abstractmethod
    def keys(self) -> List[str]:
        """Получить все ключи"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Получить размер кэша в байтах"""
        pass

class FileSystemCacheBackend(CacheBackend):
    """Файловая система как бэкенд для кэширования"""
    
    def __init__(self, cache_dir: str, max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        
        # Файл для метаданных кэша
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
        
        logger.info(f"FileSystemCacheBackend инициализирован: {cache_dir}, max_size: {max_size_mb}MB")
    
    def _load_metadata(self):
        """Загружает метаданные кэша"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {}
        except Exception as e:
            logger.warning(f"Ошибка загрузки метаданных кэша: {e}")
            self._metadata = {}
    
    def _save_metadata(self):
        """Сохраняет метаданные кэша"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных кэша: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Получает путь к файлу кэша для ключа"""
        # Создаем безопасное имя файла из ключа
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def _calculate_size(self, value: Any) -> int:
        """Вычисляет размер значения в байтах"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode() if isinstance(value, str) else value)
            else:
                return len(pickle.dumps(value))
        except:
            return 0
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Получить значение из кэша"""
        with self._lock:
            try:
                cache_path = self._get_cache_path(key)
                
                if not cache_path.exists():
                    return None
                
                # Загружаем запись из файла
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                
                # Проверяем, не истекла ли запись
                if entry.is_expired():
                    self.delete(key)
                    return None
                
                # Обновляем статистику доступа
                entry.touch()
                
                # Сохраняем обновленную запись
                with open(cache_path, 'wb') as f:
                    pickle.dump(entry, f)
                
                return entry
                
            except Exception as e:
                logger.error(f"Ошибка получения из кэша {key}: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, metadata: Dict[str, Any] = None) -> bool:
        """Сохранить значение в кэш"""
        with self._lock:
            try:
                # Вычисляем размер значения
                size_bytes = self._calculate_size(value)
                
                # Проверяем, не превышает ли размер лимит
                if size_bytes > self.max_size_bytes:
                    logger.warning(f"Значение слишком большое для кэширования: {size_bytes} байт")
                    return False
                
                # Создаем запись
                expires_at = None
                if ttl is not None:
                    expires_at = datetime.now() + timedelta(seconds=ttl)
                
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size_bytes=size_bytes,
                    metadata=metadata or {}
                )
                
                # Проверяем общий размер кэша и очищаем при необходимости
                self._ensure_cache_size()
                
                # Сохраняем в файл
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'wb') as f:
                    pickle.dump(entry, f)
                
                # Обновляем метаданные
                self._metadata[key] = {
                    'created_at': entry.created_at.isoformat(),
                    'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                    'size_bytes': size_bytes,
                    'metadata': metadata or {}
                }
                self._save_metadata()
                
                logger.debug(f"Значение сохранено в кэш: {key} ({size_bytes} байт)")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка сохранения в кэш {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        with self._lock:
            try:
                cache_path = self._get_cache_path(key)
                
                if cache_path.exists():
                    cache_path.unlink()
                
                # Удаляем из метаданных
                if key in self._metadata:
                    del self._metadata[key]
                    self._save_metadata()
                
                logger.debug(f"Значение удалено из кэша: {key}")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка удаления из кэша {key}: {e}")
                return False
    
    def clear(self) -> int:
        """Очистить весь кэш"""
        with self._lock:
            try:
                deleted_count = 0
                
                # Удаляем все файлы кэша
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка удаления файла кэша {cache_file}: {e}")
                
                # Очищаем метаданные
                self._metadata.clear()
                self._save_metadata()
                
                logger.info(f"Кэш очищен: удалено {deleted_count} записей")
                return deleted_count
                
            except Exception as e:
                logger.error(f"Ошибка очистки кэша: {e}")
                return 0
    
    def keys(self) -> List[str]:
        """Получить все ключи"""
        with self._lock:
            return list(self._metadata.keys())
    
    def size(self) -> int:
        """Получить размер кэша в байтах"""
        with self._lock:
            total_size = 0
            for metadata in self._metadata.values():
                total_size += metadata.get('size_bytes', 0)
            return total_size
    
    def _ensure_cache_size(self):
        """Обеспечивает, что размер кэша не превышает лимит"""
        current_size = self.size()
        
        if current_size <= self.max_size_bytes:
            return
        
        logger.info(f"Размер кэша превышен ({current_size} > {self.max_size_bytes}), очищаем старые записи")
        
        # Получаем все записи с временем последнего доступа
        entries_info = []
        for key, metadata in self._metadata.items():
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        entry = pickle.load(f)
                    entries_info.append((key, entry.last_accessed, entry.size_bytes))
                except:
                    # Если не можем прочитать, помечаем для удаления
                    entries_info.append((key, datetime.min, 0))
        
        # Сортируем по времени последнего доступа (старые первыми)
        entries_info.sort(key=lambda x: x[1])
        
        # Удаляем старые записи пока не достигнем целевого размера
        target_size = int(self.max_size_bytes * 0.8)  # Оставляем 20% запаса
        
        for key, _, size_bytes in entries_info:
            if current_size <= target_size:
                break
            
            if self.delete(key):
                current_size -= size_bytes
                logger.debug(f"Удалена старая запись из кэша: {key}")
    
    def cleanup_expired(self) -> int:
        """Очищает истекшие записи"""
        with self._lock:
            expired_keys = []
            
            for key in self.keys():
                entry = self.get(key)  # get() автоматически удалит истекшие записи
                if entry is None:
                    expired_keys.append(key)
            
            logger.info(f"Очищено истекших записей: {len(expired_keys)}")
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику кэша"""
        with self._lock:
            total_entries = len(self._metadata)
            total_size = self.size()
            
            # Подсчитываем статистику по типам
            types_stats = {}
            expired_count = 0
            
            for key, metadata in self._metadata.items():
                entry_type = metadata.get('metadata', {}).get('type', 'unknown')
                if entry_type not in types_stats:
                    types_stats[entry_type] = {'count': 0, 'size': 0}
                
                types_stats[entry_type]['count'] += 1
                types_stats[entry_type]['size'] += metadata.get('size_bytes', 0)
                
                # Проверяем истечение
                expires_at = metadata.get('expires_at')
                if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                    expired_count += 1
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_size_mb': round(self.max_size_bytes / (1024 * 1024), 2),
                'usage_percent': round((total_size / self.max_size_bytes) * 100, 2),
                'expired_entries': expired_count,
                'types_stats': types_stats,
                'cache_dir': str(self.cache_dir)
            }

class YandexCache:
    """Основной класс кэширования для Yandex Cloud"""
    
    def __init__(self, cache_dir: str = "/app/files/cache", max_size_mb: int = 1000):
        self.backend = FileSystemCacheBackend(cache_dir, max_size_mb)
        self._lock = threading.RLock()
        
        # Настройки TTL по умолчанию (в секундах)
        self.default_ttl = {
            'embeddings': 24 * 60 * 60,      # 24 часа
            'llm_responses': 60 * 60,        # 1 час
            'auth_tokens': 50 * 60,          # 50 минут (токены живут час)
            'documents': 7 * 24 * 60 * 60,   # 7 дней
        }
        
        logger.info(f"YandexCache инициализирован: {cache_dir}")
    
    def _make_key(self, prefix: str, *args) -> str:
        """Создает ключ кэша из префикса и аргументов"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    # === КЭШИРОВАНИЕ ЭМБЕДДИНГОВ ===
    
    def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Получает эмбеддинг из кэша"""
        key = self._make_key("embedding", model, text)
        entry = self.backend.get(key)
        
        if entry:
            logger.debug(f"Эмбеддинг найден в кэше: {model}")
            return entry.value
        
        return None
    
    def set_embedding(self, text: str, model: str, embedding: List[float]) -> bool:
        """Сохраняет эмбеддинг в кэш"""
        key = self._make_key("embedding", model, text)
        metadata = {
            'type': 'embedding',
            'model': model,
            'text_length': len(text),
            'embedding_dim': len(embedding)
        }
        
        return self.backend.set(
            key, 
            embedding, 
            ttl=self.default_ttl['embeddings'],
            metadata=metadata
        )
    
    def get_embeddings_batch(self, texts: List[str], model: str) -> Tuple[List[Optional[List[float]]], List[str]]:
        """
        Получает эмбеддинги для списка текстов из кэша
        
        Returns:
            Tuple[List[Optional[List[float]]], List[str]]: (эмбеддинги, тексты_не_в_кэше)
        """
        embeddings = []
        missing_texts = []
        
        for text in texts:
            embedding = self.get_embedding(text, model)
            embeddings.append(embedding)
            
            if embedding is None:
                missing_texts.append(text)
        
        return embeddings, missing_texts
    
    def set_embeddings_batch(self, texts: List[str], model: str, embeddings: List[List[float]]) -> int:
        """Сохраняет список эмбеддингов в кэш"""
        saved_count = 0
        
        for text, embedding in zip(texts, embeddings):
            if self.set_embedding(text, model, embedding):
                saved_count += 1
        
        logger.info(f"Сохранено эмбеддингов в кэш: {saved_count}/{len(texts)}")
        return saved_count
    
    # === КЭШИРОВАНИЕ ОТВЕТОВ LLM ===
    
    def get_llm_response(self, messages: str, model: str, temperature: float = 0.1) -> Optional[str]:
        """Получает ответ LLM из кэша"""
        key = self._make_key("llm_response", model, messages, str(temperature))
        entry = self.backend.get(key)
        
        if entry:
            logger.debug(f"Ответ LLM найден в кэше: {model}")
            return entry.value
        
        return None
    
    def set_llm_response(self, messages: str, model: str, response: str, temperature: float = 0.1) -> bool:
        """Сохраняет ответ LLM в кэш"""
        key = self._make_key("llm_response", model, messages, str(temperature))
        metadata = {
            'type': 'llm_response',
            'model': model,
            'temperature': temperature,
            'messages_length': len(messages),
            'response_length': len(response)
        }
        
        return self.backend.set(
            key,
            response,
            ttl=self.default_ttl['llm_responses'],
            metadata=metadata
        )
    
    # === КЭШИРОВАНИЕ ТОКЕНОВ АУТЕНТИФИКАЦИИ ===
    
    def get_auth_token(self, api_key_hash: str) -> Optional[str]:
        """Получает токен аутентификации из кэша"""
        key = self._make_key("auth_token", api_key_hash)
        entry = self.backend.get(key)
        
        if entry:
            logger.debug("Токен аутентификации найден в кэше")
            return entry.value
        
        return None
    
    def set_auth_token(self, api_key_hash: str, token: str, expires_in: int = 3600) -> bool:
        """Сохраняет токен аутентификации в кэш"""
        key = self._make_key("auth_token", api_key_hash)
        metadata = {
            'type': 'auth_token',
            'expires_in': expires_in
        }
        
        # Используем TTL немного меньше реального времени жизни токена
        ttl = max(expires_in - 300, 300)  # Минимум 5 минут, обычно на 5 минут меньше
        
        return self.backend.set(key, token, ttl=ttl, metadata=metadata)
    
    # === КЭШИРОВАНИЕ ДОКУМЕНТОВ ===
    
    def get_document(self, document_path: str) -> Optional[Dict[str, Any]]:
        """Получает обработанный документ из кэша"""
        key = self._make_key("document", document_path)
        entry = self.backend.get(key)
        
        if entry:
            logger.debug(f"Документ найден в кэше: {document_path}")
            return entry.value
        
        return None
    
    def set_document(self, document_path: str, document_data: Dict[str, Any]) -> bool:
        """Сохраняет обработанный документ в кэш"""
        key = self._make_key("document", document_path)
        metadata = {
            'type': 'document',
            'document_path': document_path,
            'chunks_count': len(document_data.get('chunks', [])),
            'processed_at': datetime.now().isoformat()
        }
        
        return self.backend.set(
            key,
            document_data,
            ttl=self.default_ttl['documents'],
            metadata=metadata
        )
    
    # === УПРАВЛЕНИЕ КЭШЕМ ===
    
    def clear_by_type(self, cache_type: str) -> int:
        """Очищает кэш по типу"""
        with self._lock:
            deleted_count = 0
            keys_to_delete = []
            
            for key in self.backend.keys():
                entry = self.backend.get(key)
                if entry and entry.metadata.get('type') == cache_type:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                if self.backend.delete(key):
                    deleted_count += 1
            
            logger.info(f"Очищен кэш типа '{cache_type}': удалено {deleted_count} записей")
            return deleted_count
    
    def cleanup_expired(self) -> int:
        """Очищает истекшие записи"""
        return self.backend.cleanup_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику кэша"""
        stats = self.backend.get_stats()
        
        # Добавляем информацию о TTL настройках
        stats['ttl_settings'] = self.default_ttl.copy()
        
        return stats
    
    def clear_all(self) -> int:
        """Очищает весь кэш"""
        return self.backend.clear()
    
    def optimize(self) -> Dict[str, Any]:
        """Оптимизирует кэш (очищает истекшие записи и дефрагментирует)"""
        logger.info("Начинаем оптимизацию кэша...")
        
        start_time = time.time()
        initial_stats = self.get_stats()
        
        # Очищаем истекшие записи
        expired_cleaned = self.cleanup_expired()
        
        # Принудительно проверяем размер кэша
        self.backend._ensure_cache_size()
        
        final_stats = self.get_stats()
        duration = time.time() - start_time
        
        optimization_result = {
            'duration_seconds': round(duration, 2),
            'expired_cleaned': expired_cleaned,
            'initial_size_mb': initial_stats['total_size_mb'],
            'final_size_mb': final_stats['total_size_mb'],
            'space_freed_mb': round(initial_stats['total_size_mb'] - final_stats['total_size_mb'], 2),
            'initial_entries': initial_stats['total_entries'],
            'final_entries': final_stats['total_entries']
        }
        
        logger.info(f"Оптимизация кэша завершена: {optimization_result}")
        return optimization_result

# Глобальный экземпляр кэша
_global_cache: Optional[YandexCache] = None
_cache_lock = threading.Lock()

def get_cache() -> YandexCache:
    """Получение глобального экземпляра кэша"""
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                # Получаем настройки из конфигурации
                try:
                    from config_utils import get_runtime_config
                    config = get_runtime_config()
                    yandex_config = config.get('yandex_cloud', {})
                    
                    cache_dir = yandex_config.get('cache_dir', '/app/files/cache')
                    # Предполагаем максимальный размер кэша 1GB по умолчанию
                    max_size_mb = 1000
                    
                except Exception as e:
                    logger.warning(f"Не удалось получить конфигурацию кэша: {e}")
                    cache_dir = '/app/files/cache'
                    max_size_mb = 1000
                
                _global_cache = YandexCache(cache_dir, max_size_mb)
                logger.info("Создан глобальный экземпляр YandexCache")
    
    return _global_cache

# Удобные функции для использования
def cache_embedding(text: str, model: str, embedding: List[float]) -> bool:
    """Удобная функция для кэширования эмбеддинга"""
    return get_cache().set_embedding(text, model, embedding)

def get_cached_embedding(text: str, model: str) -> Optional[List[float]]:
    """Удобная функция для получения эмбеддинга из кэша"""
    return get_cache().get_embedding(text, model)

def cache_llm_response(messages: str, model: str, response: str, temperature: float = 0.1) -> bool:
    """Удобная функция для кэширования ответа LLM"""
    return get_cache().set_llm_response(messages, model, response, temperature)

def get_cached_llm_response(messages: str, model: str, temperature: float = 0.1) -> Optional[str]:
    """Удобная функция для получения ответа LLM из кэша"""
    return get_cache().get_llm_response(messages, model, temperature)