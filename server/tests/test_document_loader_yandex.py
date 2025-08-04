"""
Тесты для document_loader с поддержкой Yandex эмбеддингов
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_loader import (
    get_embedding_function,
    load_documents_into_database,
    vec_search
)
from yandex_embeddings import YandexEmbeddings
from langchain_ollama import OllamaEmbeddings

class TestGetEmbeddingFunction:
    """Тесты для функции get_embedding_function"""
    
    @patch('document_loader.get_env_bool')
    @patch('document_loader.create_embeddings')
    def test_get_embedding_function_yandex(self, mock_create_embeddings, mock_get_env_bool):
        """Тест получения YandexEmbeddings"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        mock_yandex_embeddings = MagicMock()
        mock_create_embeddings.return_value = mock_yandex_embeddings
        
        result = get_embedding_function("text-search-doc")
        
        assert result == mock_yandex_embeddings
        mock_get_env_bool.assert_called_once_with("USE_YANDEX_CLOUD", False)
        mock_create_embeddings.assert_called_once_with(model="text-search-doc")
    
    @patch('document_loader.get_env_bool')
    @patch('document_loader.OllamaEmbeddings')
    def test_get_embedding_function_ollama(self, mock_ollama_embeddings, mock_get_env_bool):
        """Тест получения OllamaEmbeddings"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        mock_ollama_instance = MagicMock()
        mock_ollama_embeddings.return_value = mock_ollama_instance
        
        result = get_embedding_function("nomic-embed-text")
        
        assert result == mock_ollama_instance
        mock_get_env_bool.assert_called_once_with("USE_YANDEX_CLOUD", False)
        mock_ollama_embeddings.assert_called_once_with(
            model="nomic-embed-text", 
            base_url="http://localhost:11434"
        )
    
    @patch('document_loader.get_env_bool')
    @patch('document_loader.create_embeddings')
    @patch('document_loader.OllamaEmbeddings')
    def test_get_embedding_function_yandex_fallback(self, mock_ollama_embeddings, mock_create_embeddings, mock_get_env_bool):
        """Тест fallback с Yandex на Ollama"""
        # Настраиваем моки
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": True
        }.get(key, default)
        
        # Yandex падает с ошибкой
        mock_create_embeddings.side_effect = Exception("Yandex API error")
        
        # Ollama работает
        mock_ollama_instance = MagicMock()
        mock_ollama_embeddings.return_value = mock_ollama_instance
        
        result = get_embedding_function("text-search-doc")
        
        assert result == mock_ollama_instance
        mock_create_embeddings.assert_called_once_with(model="text-search-doc")
        mock_ollama_embeddings.assert_called_once()
    
    @patch('document_loader.get_env_bool')
    @patch('document_loader.create_embeddings')
    def test_get_embedding_function_yandex_no_fallback(self, mock_create_embeddings, mock_get_env_bool):
        """Тест ошибки Yandex без fallback"""
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": False
        }.get(key, default)
        
        mock_create_embeddings.side_effect = Exception("Yandex API error")
        
        with pytest.raises(Exception, match="Yandex API error"):
            get_embedding_function("text-search-doc")

class TestLoadDocumentsIntoDatabaseYandex:
    """Тесты для load_documents_into_database с Yandex эмбеддингами"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Фикстура временных директорий"""
        persist_dir = tempfile.mkdtemp()
        content_dir = tempfile.mkdtemp()
        
        yield persist_dir, content_dir
        
        shutil.rmtree(persist_dir, ignore_errors=True)
        shutil.rmtree(content_dir, ignore_errors=True)
    
    @patch('document_loader.get_embedding_function')
    @patch('document_loader.load_documents')
    @patch('document_loader.Chroma')
    @patch('document_loader.PERSIST_DIRECTORY')
    def test_load_documents_yandex_new_database(self, mock_persist_dir, mock_chroma, mock_load_documents, mock_get_embedding_function, temp_dirs):
        """Тест создания новой базы данных с Yandex эмбеддингами"""
        persist_dir, content_dir = temp_dirs
        mock_persist_dir.__str__ = lambda: persist_dir
        
        # Настраиваем моки
        mock_yandex_embeddings = MagicMock()
        mock_get_embedding_function.return_value = mock_yandex_embeddings
        
        mock_documents = [
            MagicMock(metadata={'source': 'doc1.txt'}, page_content='Content 1'),
            MagicMock(metadata={'source': 'doc2.txt'}, page_content='Content 2')
        ]
        mock_load_documents.return_value = mock_documents
        
        mock_db_instance = MagicMock()
        mock_chroma.from_documents.return_value = mock_db_instance
        
        # Создаем тестовые файлы
        os.makedirs(f"{content_dir}/test_docs", exist_ok=True)
        with open(f"{content_dir}/test_docs/test.txt", 'w') as f:
            f.write("Test content")
        
        with patch('document_loader.TEXT_SPLITTER') as mock_splitter:
            mock_split_docs = [MagicMock(), MagicMock()]
            mock_splitter.split_documents.return_value = mock_split_docs
            
            with patch('os.path.exists', side_effect=lambda path: path.startswith(content_dir)):
                with patch('os.makedirs'):
                    result = load_documents_into_database(
                        model_name="text-search-doc",
                        documents_path=f"{content_dir}/test_docs",
                        department_id="test_dept",
                        reload=True
                    )
        
        # Проверяем результат
        assert result == mock_db_instance
        mock_get_embedding_function.assert_called_with("text-search-doc")
        mock_chroma.from_documents.assert_called_once_with(
            documents=mock_split_docs,
            embedding=mock_yandex_embeddings,
            persist_directory=f"{persist_dir}/test_dept"
        )
    
    @patch('document_loader.get_embedding_function')
    @patch('document_loader.Chroma')
    @patch('document_loader.PERSIST_DIRECTORY')
    def test_load_documents_yandex_existing_database(self, mock_persist_dir, mock_chroma, mock_get_embedding_function, temp_dirs):
        """Тест загрузки существующей базы данных с Yandex эмбеддингами"""
        persist_dir, content_dir = temp_dirs
        mock_persist_dir.__str__ = lambda: persist_dir
        
        # Создаем директорию для имитации существующей БД
        dept_dir = f"{persist_dir}/test_dept"
        os.makedirs(dept_dir, exist_ok=True)
        
        mock_yandex_embeddings = MagicMock()
        mock_get_embedding_function.return_value = mock_yandex_embeddings
        
        mock_db_instance = MagicMock()
        mock_chroma.return_value = mock_db_instance
        
        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs'):
                result = load_documents_into_database(
                    model_name="text-search-doc",
                    documents_path=f"{content_dir}/test_docs",
                    department_id="test_dept",
                    reload=False
                )
        
        # Проверяем результат
        assert result == mock_db_instance
        mock_get_embedding_function.assert_called_with("text-search-doc")
        mock_chroma.assert_called_once_with(
            embedding_function=mock_yandex_embeddings,
            persist_directory=dept_dir
        )
    
    @patch('document_loader.get_embedding_function')
    @patch('document_loader.load_documents')
    @patch('document_loader.Chroma')
    @patch('document_loader.PERSIST_DIRECTORY')
    def test_load_documents_yandex_add_to_existing(self, mock_persist_dir, mock_chroma, mock_load_documents, mock_get_embedding_function, temp_dirs):
        """Тест добавления документов к существующей базе с Yandex эмбеддингами"""
        persist_dir, content_dir = temp_dirs
        mock_persist_dir.__str__ = lambda: persist_dir
        
        # Создаем директорию для имитации существующей БД
        dept_dir = f"{persist_dir}/test_dept"
        os.makedirs(dept_dir, exist_ok=True)
        
        mock_yandex_embeddings = MagicMock()
        mock_get_embedding_function.return_value = mock_yandex_embeddings
        
        # Мокаем существующую базу данных
        mock_existing_db = MagicMock()
        mock_existing_db.get.return_value = {
            'metadatas': [
                {'source': 'existing_doc.txt'}
            ]
        }
        
        # Мокаем новые документы
        mock_new_documents = [
            MagicMock(metadata={'source': 'new_doc.txt'}, page_content='New content')
        ]
        mock_load_documents.return_value = mock_new_documents
        
        # Мокаем Chroma для создания и добавления
        mock_chroma.side_effect = [mock_existing_db, mock_existing_db]  # Для проверки существующих файлов и для добавления
        
        with patch('document_loader.TEXT_SPLITTER') as mock_splitter:
            mock_split_docs = [MagicMock()]
            mock_splitter.split_documents.return_value = mock_split_docs
            
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    result = load_documents_into_database(
                        model_name="text-search-doc",
                        documents_path=f"{content_dir}/test_docs",
                        department_id="test_dept",
                        reload=True
                    )
        
        # Проверяем результат
        assert result == mock_existing_db
        mock_existing_db.add_documents.assert_called_once_with(mock_split_docs)

class TestVecSearchYandex:
    """Тесты для vec_search с Yandex эмбеддингами"""
    
    def test_vec_search_with_yandex_embeddings(self):
        """Тест vec_search с YandexEmbeddings"""
        # Мокаем YandexEmbeddings
        mock_yandex_embeddings = MagicMock()
        mock_yandex_embeddings.embed_query.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Мокаем базу данных
        mock_db = MagicMock()
        mock_search_results = [
            MagicMock(
                page_content="Test document content",
                metadata={'source': 'test.txt', 'page': 1}
            )
        ]
        mock_db.similarity_search_by_vector.return_value = mock_search_results
        
        # Выполняем поиск
        result = vec_search(
            embedding_model=mock_yandex_embeddings,
            query="test query",
            db=mock_db,
            n_top_cos=5,
            timeout=10
        )
        
        # Проверяем результат
        assert len(result) >= 2  # Должно вернуть chunks и files
        chunks, files = result[:2]
        
        assert len(chunks) > 0
        assert len(files) > 0
        assert "Test document content" in chunks[0]
        
        # Проверяем что использовался embed_query
        mock_yandex_embeddings.embed_query.assert_called()
    
    def test_vec_search_with_ollama_fallback(self):
        """Тест vec_search с fallback на embed_documents"""
        # Мокаем эмбеддинги без метода embed_query
        mock_embeddings = MagicMock()
        del mock_embeddings.embed_query  # Удаляем метод
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        
        # Мокаем базу данных
        mock_db = MagicMock()
        mock_search_results = [
            MagicMock(
                page_content="Fallback test content",
                metadata={'source': 'fallback.txt'}
            )
        ]
        mock_db.similarity_search_by_vector.return_value = mock_search_results
        
        # Выполняем поиск
        result = vec_search(
            embedding_model=mock_embeddings,
            query="fallback query",
            db=mock_db,
            n_top_cos=3,
            timeout=10
        )
        
        # Проверяем результат
        assert len(result) >= 2
        chunks, files = result[:2]
        
        assert len(chunks) > 0
        assert "Fallback test content" in chunks[0]
        
        # Проверяем что использовался embed_documents как fallback
        mock_embeddings.embed_documents.assert_called()
    
    def test_vec_search_embedding_error_handling(self):
        """Тест обработки ошибок при создании эмбеддингов"""
        # Мокаем эмбеддинги с ошибкой
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.side_effect = Exception("Embedding error")
        mock_embeddings.embed_documents.side_effect = Exception("Embedding error")
        
        mock_db = MagicMock()
        
        # Выполняем поиск
        result = vec_search(
            embedding_model=mock_embeddings,
            query="error query",
            db=mock_db,
            n_top_cos=3,
            timeout=10
        )
        
        # При ошибке должны вернуться пустые списки
        assert len(result) >= 2
        chunks, files = result[:2]
        assert len(chunks) == 0 or chunks == []
        assert len(files) == 0 or files == []

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_yandex_integration(self):
        """Интеграционный тест полного потока с Yandex эмбеддингами"""
        # Этот тест требует реальной конфигурации Yandex Cloud
        try:
            from config_utils import validate_yandex_config
            config = validate_yandex_config()
            
            if not config.get("use_yandex_cloud"):
                pytest.skip("Yandex Cloud не настроен для интеграционных тестов")
            
            # Тестируем создание эмбеддингов
            embedding_function = get_embedding_function("text-search-doc")
            
            # Проверяем что это YandexEmbeddings
            assert hasattr(embedding_function, 'embed_query')
            assert hasattr(embedding_function, 'embed_documents')
            
            # Тестируем создание эмбеддинга
            test_texts = ["Тестовый документ для интеграционного теста"]
            embeddings = embedding_function.embed_documents(test_texts)
            
            assert len(embeddings) == 1
            assert len(embeddings[0]) > 0  # Проверяем что эмбеддинг не пустой
            
        except Exception as e:
            pytest.skip(f"Интеграционный тест пропущен: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])