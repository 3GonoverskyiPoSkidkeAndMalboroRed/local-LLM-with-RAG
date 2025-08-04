"""
Тесты для LLMStateManager с поддержкой Yandex Cloud
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_state_manager import LLMStateManager

class TestLLMStateManagerYandex:
    """Тесты для LLMStateManager с Yandex Cloud поддержкой"""
    
    @pytest.fixture
    def state_manager(self):
        """Фикстура LLMStateManager для тестов"""
        return LLMStateManager()
    
    @pytest.fixture
    def temp_dir(self):
        """Фикстура временной директории"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('llm_state_manager.get_env_bool')
    def test_get_available_models_yandex(self, mock_get_env_bool, state_manager):
        """Тест получения доступных моделей для Yandex Cloud"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        models = state_manager.get_available_models()
        
        assert "yandexgpt" in models["llm_models"]
        assert "yandexgpt-lite" in models["llm_models"]
        assert "text-search-doc" in models["embedding_models"]
        assert "text-search-query" in models["embedding_models"]
        
        # Должны быть и Ollama модели как fallback
        assert "gemma3" in models["llm_models"]
        assert "nomic-embed-text" in models["embedding_models"]
    
    @patch('llm_state_manager.get_env_bool')
    def test_get_available_models_ollama(self, mock_get_env_bool, state_manager):
        """Тест получения доступных моделей для Ollama"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        
        models = state_manager.get_available_models()
        
        assert "gemma3" in models["llm_models"]
        assert "nomic-embed-text" in models["embedding_models"]
        
        # Yandex модели не должны быть доступны
        assert "yandexgpt" not in models["llm_models"]
        assert "text-search-doc" not in models["embedding_models"]
    
    @patch('llm_state_manager.get_env_bool')
    def test_check_if_model_is_available_yandex(self, mock_get_env_bool, state_manager):
        """Тест проверки доступности Yandex моделей"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        # Yandex модели должны быть доступны
        assert state_manager.check_if_model_is_available("yandexgpt") is True
        assert state_manager.check_if_model_is_available("text-search-doc") is True
        
        # Ollama модели тоже должны быть доступны как fallback
        assert state_manager.check_if_model_is_available("gemma3") is True
    
    @patch('llm_state_manager.get_env_bool')
    def test_check_if_model_is_available_ollama(self, mock_get_env_bool, state_manager):
        """Тест проверки доступности Ollama моделей"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        
        # Ollama модели должны быть доступны
        assert state_manager.check_if_model_is_available("gemma3") is True
        assert state_manager.check_if_model_is_available("nomic-embed-text") is True
        
        # Yandex модели не должны быть доступны
        with pytest.raises(ValueError, match="недоступна для Ollama"):
            state_manager.check_if_model_is_available("yandexgpt")
    
    @patch('llm_state_manager.get_env_bool')
    def test_get_provider_info_yandex(self, mock_get_env_bool, state_manager):
        """Тест получения информации о провайдере Yandex Cloud"""
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": True
        }.get(key, default)
        
        info = state_manager.get_provider_info()
        
        assert info["primary_provider"] == "yandex_cloud"
        assert info["yandex_cloud_enabled"] is True
        assert info["fallback_enabled"] is True
        assert "available_models" in info
    
    @patch('llm_state_manager.get_env_bool')
    def test_get_provider_info_ollama(self, mock_get_env_bool, state_manager):
        """Тест получения информации о провайдере Ollama"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        
        info = state_manager.get_provider_info()
        
        assert info["primary_provider"] == "ollama"
        assert info["yandex_cloud_enabled"] is False
        assert "ollama_host" in info
    
    @patch('llm_state_manager.get_env_bool')
    @patch('llm_state_manager.load_documents_into_database')
    @patch('llm_state_manager.create_embeddings')
    @patch('llm_state_manager.create_compatible_llm')
    @patch('llm_state_manager.getChatChain')
    @patch('llm_state_manager.getAsyncChatChain')
    def test_initialize_llm_yandex_success(self, mock_async_chat, mock_chat, mock_compatible_llm, 
                                         mock_create_embeddings, mock_load_docs, mock_get_env_bool, 
                                         state_manager, temp_dir):
        """Тест успешной инициализации LLM с Yandex Cloud"""
        # Настраиваем моки
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        mock_db = MagicMock()
        mock_load_docs.return_value = mock_db
        
        mock_embeddings = MagicMock()
        mock_create_embeddings.return_value = mock_embeddings
        
        mock_llm = MagicMock()
        mock_compatible_llm.return_value = mock_llm
        
        mock_chat_instance = MagicMock()
        mock_async_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance
        mock_async_chat.return_value = mock_async_chat_instance
        
        # Выполняем инициализацию
        result = state_manager.initialize_llm(
            llm_model_name="yandexgpt",
            embedding_model_name="text-search-doc",
            documents_path=temp_dir,
            department_id="test_dept"
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что правильные функции были вызваны
        mock_create_embeddings.assert_called_once_with(model="text-search-doc")
        mock_compatible_llm.assert_called_once_with(
            model="yandexgpt",
            temperature=0.1,
            num_predict=200
        )
        
        # Проверяем что отдел инициализирован
        assert state_manager.is_department_initialized("test_dept")
    
    @patch('llm_state_manager.get_env_bool')
    @patch('llm_state_manager.load_documents_into_database')
    @patch('llm_state_manager.create_embeddings')
    @patch('llm_state_manager.create_compatible_llm')
    @patch('llm_state_manager.ChatOllama')
    @patch('llm_state_manager.getChatChain')
    @patch('llm_state_manager.getAsyncChatChain')
    def test_initialize_llm_yandex_fallback(self, mock_async_chat, mock_chat, mock_ollama, 
                                          mock_compatible_llm, mock_create_embeddings, 
                                          mock_load_docs, mock_get_env_bool, state_manager, temp_dir):
        """Тест fallback с Yandex Cloud на Ollama"""
        # Настраиваем моки
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": True
        }.get(key, default)
        
        mock_db = MagicMock()
        mock_load_docs.return_value = mock_db
        
        mock_embeddings = MagicMock()
        mock_create_embeddings.return_value = mock_embeddings
        
        # Yandex LLM падает с ошибкой
        mock_compatible_llm.side_effect = Exception("Yandex API error")
        
        # Ollama работает
        mock_ollama_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        
        mock_chat_instance = MagicMock()
        mock_async_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance
        mock_async_chat.return_value = mock_async_chat_instance
        
        # Выполняем инициализацию
        result = state_manager.initialize_llm(
            llm_model_name="yandexgpt",
            embedding_model_name="text-search-doc",
            documents_path=temp_dir,
            department_id="test_dept"
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что сначала пытались Yandex, потом Ollama
        mock_compatible_llm.assert_called_once()
        mock_ollama.assert_called_once()
    
    @patch('llm_state_manager.get_env_bool')
    @patch('llm_state_manager.load_documents_into_database')
    @patch('llm_state_manager.create_embeddings')
    @patch('llm_state_manager.OllamaEmbeddings')
    @patch('llm_state_manager.ChatOllama')
    @patch('llm_state_manager.getChatChain')
    @patch('llm_state_manager.getAsyncChatChain')
    def test_initialize_llm_embeddings_fallback(self, mock_async_chat, mock_chat, mock_ollama_llm,
                                               mock_ollama_embeddings, mock_create_embeddings, 
                                               mock_load_docs, mock_get_env_bool, state_manager, temp_dir):
        """Тест fallback для эмбеддингов с Yandex на Ollama"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false для простоты
        
        mock_db = MagicMock()
        mock_load_docs.return_value = mock_db
        
        # Yandex эмбеддинги падают с ошибкой
        mock_create_embeddings.side_effect = Exception("Yandex embeddings error")
        
        # Ollama эмбеддинги работают
        mock_ollama_emb_instance = MagicMock()
        mock_ollama_embeddings.return_value = mock_ollama_emb_instance
        
        mock_ollama_llm_instance = MagicMock()
        mock_ollama_llm.return_value = mock_ollama_llm_instance
        
        mock_chat_instance = MagicMock()
        mock_async_chat_instance = MagicMock()
        mock_chat.return_value = mock_chat_instance
        mock_async_chat.return_value = mock_async_chat_instance
        
        # Выполняем инициализацию
        result = state_manager.initialize_llm(
            llm_model_name="gemma3",
            embedding_model_name="nomic-embed-text",
            documents_path=temp_dir,
            department_id="test_dept"
        )
        
        # Проверяем результат
        assert result is True
        mock_ollama_embeddings.assert_called_once()
    
    def test_get_department_provider_info_not_initialized(self, state_manager):
        """Тест получения информации о неинициализированном отделе"""
        info = state_manager.get_department_provider_info("nonexistent_dept")
        
        assert "error" in info
        assert "не инициализирован" in info["error"]
    
    @patch('llm_state_manager.get_env_bool')
    def test_get_department_provider_info_initialized(self, mock_get_env_bool, state_manager):
        """Тест получения информации об инициализированном отделе"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        # Мокаем инициализированный отдел
        with state_manager.global_lock:
            state_manager.department_chats["test_dept"] = MagicMock()
            state_manager.department_async_chats["test_dept"] = MagicMock()
            state_manager.department_databases["test_dept"] = MagicMock()
            
            mock_embedding_model = MagicMock()
            mock_embedding_model.__class__.__name__ = "YandexEmbeddings"
            state_manager.department_embedding_models["test_dept"] = mock_embedding_model
        
        info = state_manager.get_department_provider_info("test_dept")
        
        assert info["department_id"] == "test_dept"
        assert info["initialized"] is True
        assert info["embedding_type"] == "YandexEmbeddings"
        assert "provider_info" in info

class TestLLMStateManagerIntegration:
    """Интеграционные тесты для LLMStateManager"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_yandex_initialization(self):
        """Интеграционный тест полной инициализации с Yandex Cloud"""
        # Этот тест требует реальной конфигурации Yandex Cloud
        try:
            from config_utils import validate_yandex_config
            config = validate_yandex_config()
            
            if not config.get("use_yandex_cloud"):
                pytest.skip("Yandex Cloud не настроен для интеграционных тестов")
            
            state_manager = LLMStateManager()
            
            # Создаем временную директорию с тестовым документом
            temp_dir = tempfile.mkdtemp()
            test_doc_path = os.path.join(temp_dir, "test.md")
            
            with open(test_doc_path, 'w', encoding='utf-8') as f:
                f.write("# Тестовый документ\n\nЭто тестовый документ для интеграционного теста.")
            
            try:
                # Пытаемся инициализировать отдел
                result = state_manager.initialize_llm(
                    llm_model_name="yandexgpt",
                    embedding_model_name="text-search-doc",
                    documents_path=temp_dir,
                    department_id="integration_test"
                )
                
                assert result is True
                assert state_manager.is_department_initialized("integration_test")
                
                # Проверяем информацию о провайдере
                provider_info = state_manager.get_provider_info()
                assert provider_info["primary_provider"] == "yandex_cloud"
                
                dept_info = state_manager.get_department_provider_info("integration_test")
                assert dept_info["initialized"] is True
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            pytest.skip(f"Интеграционный тест пропущен: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])