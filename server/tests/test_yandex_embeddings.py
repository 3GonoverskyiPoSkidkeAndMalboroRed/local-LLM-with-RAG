"""
Unit тесты для YandexEmbeddings класса
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yandex_embeddings import (
    YandexEmbeddings,
    create_yandex_embeddings,
    create_embeddings,
    get_cached_embeddings
)
from yandex_cloud_adapter import YandexCloudAdapter

class TestYandexEmbeddings:
    """Тесты для YandexEmbeddings класса"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Фикстура временной директории для кэша"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def embeddings(self, temp_cache_dir):
        """Фикстура YandexEmbeddings для тестов"""
        return YandexEmbeddings(
            model="text-search-doc",
            cache_dir=temp_cache_dir,
            cache_enabled=True
        )
    
    @pytest.fixture
    def embeddings_no_cache(self):
        """Фикстура YandexEmbeddings без кэша"""
        return YandexEmbeddings(
            model="text-search-doc",
            cache_enabled=False
        )
    
    def test_embeddings_initialization(self, embeddings, temp_cache_dir):
        """Тест инициализации YandexEmbeddings"""
        assert embeddings.model == "text-search-doc"
        assert embeddings.cache_enabled is True
        assert str(embeddings.cache_dir) == temp_cache_dir
        assert embeddings.cache_dir.exists()
    
    def test_embeddings_initialization_no_cache(self, embeddings_no_cache):
        """Тест инициализации без кэша"""
        assert embeddings_no_cache.model == "text-search-doc"
        assert embeddings_no_cache.cache_enabled is False
    
    def test_get_cache_key(self, embeddings):
        """Тест генерации ключа кэша"""
        key1 = embeddings._get_cache_key("test text")
        key2 = embeddings._get_cache_key("test text")
        key3 = embeddings._get_cache_key("different text")
        
        # Одинаковые тексты должны давать одинаковые ключи
        assert key1 == key2
        # Разные тексты должны давать разные ключи
        assert key1 != key3
        # Ключ должен быть MD5 хешем (32 символа)
        assert len(key1) == 32
    
    def test_cache_operations(self, embeddings):
        """Тест операций с кэшем"""
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        cache_key = "test_key"
        
        # Изначально в кэше ничего нет
        assert embeddings._load_from_cache(cache_key) is None
        
        # Сохраняем в кэш
        embeddings._save_to_cache(cache_key, test_embedding)
        
        # Загружаем из кэша
        loaded_embedding = embeddings._load_from_cache(cache_key)
        assert loaded_embedding == test_embedding
    
    def test_cache_operations_disabled(self, embeddings_no_cache):
        """Тест операций с кэшем при отключенном кэшировании"""
        test_embedding = [0.1, 0.2, 0.3]
        cache_key = "test_key"
        
        # При отключенном кэше операции не должны ничего делать
        embeddings_no_cache._save_to_cache(cache_key, test_embedding)
        assert embeddings_no_cache._load_from_cache(cache_key) is None
    
    def test_batch_texts_with_cache(self, embeddings):
        """Тест разделения текстов на кэшированные и новые"""
        # Сохраняем один эмбеддинг в кэш
        test_embedding = [0.1, 0.2, 0.3]
        cache_key = embeddings._get_cache_key("cached text")
        embeddings._save_to_cache(cache_key, test_embedding)
        
        texts = ["cached text", "new text 1", "new text 2"]
        texts_to_process, cached_embeddings = embeddings._batch_texts_with_cache(texts)
        
        # Один текст должен быть в кэше
        assert len(cached_embeddings) == 1
        assert 0 in cached_embeddings
        assert cached_embeddings[0] == test_embedding
        
        # Два текста должны требовать обработки
        assert len(texts_to_process) == 2
        assert texts_to_process[0] == (1, "new text 1")
        assert texts_to_process[1] == (2, "new text 2")
    
    @pytest.mark.asyncio
    async def test_aembed_documents_success(self, embeddings):
        """Тест асинхронного создания эмбеддингов для документов"""
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            texts = ["text 1", "text 2"]
            result = await embeddings._aembed_documents(texts)
            
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]
            
            mock_adapter.create_embeddings.assert_called_once_with(texts, "text-search-doc")
    
    @pytest.mark.asyncio
    async def test_aembed_documents_with_cache(self, embeddings):
        """Тест создания эмбеддингов с использованием кэша"""
        # Предварительно сохраняем один эмбеддинг в кэш
        cached_embedding = [0.1, 0.2, 0.3]
        cache_key = embeddings._get_cache_key("cached text")
        embeddings._save_to_cache(cache_key, cached_embedding)
        
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [[0.4, 0.5, 0.6]]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            texts = ["cached text", "new text"]
            result = await embeddings._aembed_documents(texts)
            
            assert len(result) == 2
            assert result[0] == cached_embedding  # Из кэша
            assert result[1] == [0.4, 0.5, 0.6]   # Из API
            
            # API должен быть вызван только для одного текста
            mock_adapter.create_embeddings.assert_called_once_with(["new text"], "text-search-doc")
    
    @pytest.mark.asyncio
    async def test_aembed_documents_all_cached(self, embeddings):
        """Тест когда все эмбеддинги в кэше"""
        # Сохраняем все эмбеддинги в кэш
        embeddings._save_to_cache(embeddings._get_cache_key("text 1"), [0.1, 0.2])
        embeddings._save_to_cache(embeddings._get_cache_key("text 2"), [0.3, 0.4])
        
        mock_adapter = AsyncMock()
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            texts = ["text 1", "text 2"]
            result = await embeddings._aembed_documents(texts)
            
            assert len(result) == 2
            assert result[0] == [0.1, 0.2]
            assert result[1] == [0.3, 0.4]
            
            # API не должен вызываться
            mock_adapter.create_embeddings.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_aembed_query_success(self, embeddings):
        """Тест асинхронного создания эмбеддинга для запроса"""
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            result = await embeddings._aembed_query("test query")
            
            assert result == [0.1, 0.2, 0.3]
            mock_adapter.create_embeddings.assert_called_once_with(["test query"], "text-search-doc")
    
    @pytest.mark.asyncio
    async def test_aembed_query_with_cache(self, embeddings):
        """Тест создания эмбеддинга запроса с кэшем"""
        # Предварительно сохраняем в кэш
        cached_embedding = [0.1, 0.2, 0.3]
        cache_key = embeddings._get_cache_key("cached query")
        embeddings._save_to_cache(cache_key, cached_embedding)
        
        mock_adapter = AsyncMock()
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            result = await embeddings._aembed_query("cached query")
            
            assert result == cached_embedding
            # API не должен вызываться
            mock_adapter.create_embeddings.assert_not_called()
    
    def test_embed_documents_sync(self, embeddings):
        """Тест синхронного создания эмбеддингов для документов"""
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = MagicMock()
                mock_get_loop.return_value = mock_loop
                mock_loop.is_running.return_value = False
                mock_loop.run_until_complete.return_value = [
                    [0.1, 0.2, 0.3],
                    [0.4, 0.5, 0.6]
                ]
                
                texts = ["text 1", "text 2"]
                result = embeddings.embed_documents(texts)
                
                assert len(result) == 2
                assert result[0] == [0.1, 0.2, 0.3]
                assert result[1] == [0.4, 0.5, 0.6]
                
                mock_loop.run_until_complete.assert_called_once()
    
    def test_embed_query_sync(self, embeddings):
        """Тест синхронного создания эмбеддинга для запроса"""
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = MagicMock()
                mock_get_loop.return_value = mock_loop
                mock_loop.is_running.return_value = False
                mock_loop.run_until_complete.return_value = [0.1, 0.2, 0.3]
                
                result = embeddings.embed_query("test query")
                
                assert result == [0.1, 0.2, 0.3]
                mock_loop.run_until_complete.assert_called_once()
    
    def test_clear_cache(self, embeddings):
        """Тест очистки кэша"""
        # Создаем несколько файлов в кэше
        embeddings._save_to_cache("key1", [0.1, 0.2])
        embeddings._save_to_cache("key2", [0.3, 0.4])
        embeddings._save_to_cache("key3", [0.5, 0.6])
        
        # Проверяем что файлы созданы
        cache_files = list(embeddings.cache_dir.glob("*.pkl"))
        assert len(cache_files) == 3
        
        # Очищаем кэш
        deleted_count = embeddings.clear_cache()
        
        assert deleted_count == 3
        
        # Проверяем что файлы удалены
        cache_files = list(embeddings.cache_dir.glob("*.pkl"))
        assert len(cache_files) == 0
    
    def test_clear_cache_disabled(self, embeddings_no_cache):
        """Тест очистки кэша при отключенном кэшировании"""
        deleted_count = embeddings_no_cache.clear_cache()
        assert deleted_count == 0
    
    def test_get_cache_stats(self, embeddings):
        """Тест получения статистики кэша"""
        # Создаем несколько файлов в кэше
        embeddings._save_to_cache("key1", [0.1, 0.2])
        embeddings._save_to_cache("key2", [0.3, 0.4])
        
        stats = embeddings.get_cache_stats()
        
        assert stats["cache_enabled"] is True
        assert stats["files_count"] == 2
        assert stats["total_size_mb"] > 0
        assert stats["model"] == "text-search-doc"
        assert "cache_dir" in stats
    
    def test_get_cache_stats_disabled(self, embeddings_no_cache):
        """Тест статистики кэша при отключенном кэшировании"""
        stats = embeddings_no_cache.get_cache_stats()
        
        assert stats["cache_enabled"] is False
        assert stats["files_count"] == 0
        assert stats["total_size_mb"] == 0

class TestFactoryFunctions:
    """Тесты для фабричных функций"""
    
    def test_create_yandex_embeddings(self):
        """Тест создания YandexEmbeddings через фабрику"""
        embeddings = create_yandex_embeddings(
            model="custom-model",
            cache_enabled=False
        )
        
        assert isinstance(embeddings, YandexEmbeddings)
        assert embeddings.model == "custom-model"
        assert embeddings.cache_enabled is False
    
    @patch('yandex_embeddings.get_env_bool')
    def test_create_embeddings_yandex(self, mock_get_env_bool):
        """Тест автоматического выбора YandexEmbeddings"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        embeddings = create_embeddings(model="test-model")
        
        assert isinstance(embeddings, YandexEmbeddings)
        assert embeddings.model == "test-model"
        mock_get_env_bool.assert_called_once_with("USE_YANDEX_CLOUD", False)
    
    @patch('yandex_embeddings.get_env_bool')
    @patch('yandex_embeddings.get_env_var')
    def test_create_embeddings_ollama(self, mock_get_env_var, mock_get_env_bool):
        """Тест автоматического выбора OllamaEmbeddings"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        mock_get_env_var.return_value = "http://localhost:11434"
        
        with patch('yandex_embeddings.OllamaEmbeddings') as mock_ollama:
            mock_instance = MagicMock()
            mock_ollama.return_value = mock_instance
            
            embeddings = create_embeddings(model="test-model")
            
            assert embeddings == mock_instance
            mock_ollama.assert_called_once_with(
                model="test-model", 
                base_url="http://localhost:11434"
            )
    
    def test_get_cached_embeddings(self):
        """Тест получения кэшированного экземпляра"""
        # Очищаем глобальный кэш
        import yandex_embeddings
        yandex_embeddings._global_embeddings_cache.clear()
        
        # Первый вызов должен создать экземпляр
        embeddings1 = get_cached_embeddings("test-model")
        assert isinstance(embeddings1, YandexEmbeddings)
        assert embeddings1.model == "test-model"
        
        # Второй вызов должен вернуть тот же экземпляр
        embeddings2 = get_cached_embeddings("test-model")
        assert embeddings1 is embeddings2
        
        # Другая модель должна создать новый экземпляр
        embeddings3 = get_cached_embeddings("other-model")
        assert embeddings3 is not embeddings1
        assert embeddings3.model == "other-model"

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_embeddings_flow(self, temp_cache_dir):
        """Тест полного потока работы с эмбеддингами"""
        # Мокаем адаптер
        mock_adapter = AsyncMock()
        mock_adapter.create_embeddings.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        
        with patch('yandex_embeddings.get_yandex_adapter', return_value=mock_adapter):
            embeddings = YandexEmbeddings(
                model="text-search-doc",
                cache_dir=temp_cache_dir,
                cache_enabled=True
            )
            
            # Первый запрос - все эмбеддинги создаются через API
            texts = ["doc 1", "doc 2", "doc 3"]
            result1 = await embeddings._aembed_documents(texts)
            
            assert len(result1) == 3
            assert result1[0] == [0.1, 0.2, 0.3]
            assert result1[1] == [0.4, 0.5, 0.6]
            assert result1[2] == [0.7, 0.8, 0.9]
            
            # API должен быть вызван один раз
            assert mock_adapter.create_embeddings.call_count == 1
            
            # Второй запрос - все эмбеддинги должны быть из кэша
            result2 = await embeddings._aembed_documents(texts)
            
            assert result2 == result1
            # API не должен вызываться повторно
            assert mock_adapter.create_embeddings.call_count == 1
            
            # Третий запрос с частично новыми данными
            mock_adapter.create_embeddings.return_value = [[1.0, 1.1, 1.2]]
            
            mixed_texts = ["doc 1", "new doc"]  # Один из кэша, один новый
            result3 = await embeddings._aembed_documents(mixed_texts)
            
            assert len(result3) == 2
            assert result3[0] == [0.1, 0.2, 0.3]  # Из кэша
            assert result3[1] == [1.0, 1.1, 1.2]  # Из API
            
            # API должен быть вызван еще раз только для нового документа
            assert mock_adapter.create_embeddings.call_count == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])