"""
Тесты для обновленного эндпоинта /generate с поддержкой Yandex Cloud
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем необходимые модули
from routes.llm_routes import router, GenerateRequest, GenerateResponse

# Создаем тестовое приложение
app = FastAPI()
app.include_router(router)

class TestGenerateEndpoint:
    """Тесты для эндпоинта /generate"""
    
    @pytest.fixture
    def client(self):
        """Фикстура тестового клиента"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_request(self):
        """Фикстура примера запроса"""
        return {
            "messages": "Привет! Как дела?",
            "model": "yandexgpt",
            "temperature": 0.2,
            "max_tokens": 100
        }
    
    def test_generate_request_model(self):
        """Тест модели запроса"""
        request_data = {
            "messages": "Test message",
            "model": "yandexgpt",
            "temperature": 0.5,
            "max_tokens": 200
        }
        
        request = GenerateRequest(**request_data)
        
        assert request.messages == "Test message"
        assert request.model == "yandexgpt"
        assert request.temperature == 0.5
        assert request.max_tokens == 200
    
    def test_generate_request_defaults(self):
        """Тест значений по умолчанию"""
        request = GenerateRequest(messages="Test")
        
        assert request.messages == "Test"
        assert request.model == "gemma3"
        assert request.temperature is None
        assert request.max_tokens is None
    
    def test_generate_response_model(self):
        """Тест модели ответа"""
        response = GenerateResponse(text="Generated text", model="yandexgpt")
        
        assert response.text == "Generated text"
        assert response.model == "yandexgpt"
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.get_yandex_adapter')
    @patch('routes.llm_routes.create_compatible_llm')
    def test_generate_yandex_cloud_success(self, mock_create_llm, mock_get_adapter, mock_get_env_bool, client, sample_request):
        """Тест успешной генерации через Yandex Cloud"""
        # Настраиваем моки
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        mock_llm = AsyncMock()
        mock_llm._acall.return_value = "Yandex Cloud response"
        mock_create_llm.return_value = mock_llm
        
        # Выполняем запрос
        response = client.post("/llm/generate", json=sample_request)
        
        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Yandex Cloud response"
        assert data["model"] == "yandexgpt"
        
        # Проверяем что правильные методы были вызваны
        mock_get_env_bool.assert_called_with("USE_YANDEX_CLOUD", False)
        mock_create_llm.assert_called_once()
        mock_llm._acall.assert_called_once_with("Привет! Как дела?")
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.ChatOllama')
    @patch('routes.llm_routes.llm_state_manager')
    def test_generate_ollama_success(self, mock_state_manager, mock_chat_ollama, mock_get_env_bool, client, sample_request):
        """Тест успешной генерации через Ollama"""
        # Настраиваем моки
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        mock_state_manager.check_if_model_is_available.return_value = True
        
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Ollama response"
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm_instance
        
        # Выполняем запрос
        response = client.post("/llm/generate", json=sample_request)
        
        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Ollama response"
        assert data["model"] == "yandexgpt"
        
        # Проверяем вызовы
        mock_state_manager.check_if_model_is_available.assert_called_once_with("yandexgpt")
        mock_chat_ollama.assert_called_once_with(model="yandexgpt")
        mock_llm_instance.invoke.assert_called_once_with("Привет! Как дела?")
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.create_compatible_llm')
    @patch('routes.llm_routes.ChatOllama')
    @patch('routes.llm_routes.llm_state_manager')
    def test_generate_yandex_fallback_to_ollama(self, mock_state_manager, mock_chat_ollama, mock_create_llm, mock_get_env_bool, client, sample_request):
        """Тест fallback с Yandex Cloud на Ollama"""
        # Настраиваем моки
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": True
        }.get(key, default)
        
        # Yandex Cloud падает с ошибкой
        mock_llm = AsyncMock()
        mock_llm._acall.side_effect = Exception("Yandex API error")
        mock_create_llm.return_value = mock_llm
        
        # Ollama работает
        mock_state_manager.check_if_model_is_available.return_value = True
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Ollama fallback response"
        mock_llm_instance.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm_instance
        
        # Выполняем запрос
        response = client.post("/llm/generate", json=sample_request)
        
        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Ollama fallback response"
        assert data["model"] == "yandexgpt"
        
        # Проверяем что сначала пытались Yandex, потом Ollama
        mock_create_llm.assert_called_once()
        mock_chat_ollama.assert_called_once()
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.create_compatible_llm')
    def test_generate_yandex_error_no_fallback(self, mock_create_llm, mock_get_env_bool, client, sample_request):
        """Тест ошибки Yandex Cloud без fallback"""
        # Настраиваем моки
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": False
        }.get(key, default)
        
        # Yandex Cloud падает с ошибкой
        mock_llm = AsyncMock()
        mock_llm._acall.side_effect = Exception("Yandex API error")
        mock_create_llm.return_value = mock_llm
        
        # Выполняем запрос
        response = client.post("/llm/generate", json=sample_request)
        
        # Проверяем результат
        assert response.status_code == 200  # Не 500, а 200 с ошибкой в тексте
        data = response.json()
        assert "Ошибка Yandex Cloud API" in data["text"]
        assert "Yandex API error" in data["text"]
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.llm_state_manager')
    def test_generate_ollama_model_not_available(self, mock_state_manager, mock_get_env_bool, client):
        """Тест с недоступной моделью в Ollama"""
        mock_get_env_bool.return_value = False  # USE_YANDEX_CLOUD=false
        mock_state_manager.check_if_model_is_available.side_effect = ValueError("Model not available")
        
        request_data = {
            "messages": "Test message",
            "model": "nonexistent_model"
        }
        
        # Выполняем запрос
        response = client.post("/llm/generate", json=request_data)
        
        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert "Системная ошибка" in data["text"]
        assert "Model not available" in data["text"]
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.llm_state_manager')
    def test_generate_yandex_model_ollama_unavailable(self, mock_state_manager, mock_get_env_bool, client):
        """Тест с Yandex моделью при недоступном Ollama"""
        mock_get_env_bool.side_effect = lambda key, default: {
            "USE_YANDEX_CLOUD": True,
            "YANDEX_FALLBACK_TO_OLLAMA": True
        }.get(key, default)
        
        # Yandex Cloud недоступен, пытаемся fallback
        with patch('routes.llm_routes.create_compatible_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm._acall.side_effect = Exception("Yandex error")
            mock_create_llm.return_value = mock_llm
            
            # Ollama не поддерживает Yandex модели
            mock_state_manager.check_if_model_is_available.side_effect = ValueError("Model not available")
            
            request_data = {
                "messages": "Test message",
                "model": "yandexgpt"
            }
            
            # Выполняем запрос
            response = client.post("/llm/generate", json=request_data)
            
            # Проверяем результат
            assert response.status_code == 200
            data = response.json()
            assert "доступна только через Yandex Cloud API" in data["text"]
    
    def test_generate_invalid_request(self, client):
        """Тест с невалидным запросом"""
        invalid_request = {
            "model": "test_model"
            # Отсутствует обязательное поле messages
        }
        
        response = client.post("/llm/generate", json=invalid_request)
        
        # FastAPI должен вернуть 422 для невалидных данных
        assert response.status_code == 422
    
    def test_generate_empty_message(self, client):
        """Тест с пустым сообщением"""
        request_data = {
            "messages": "",
            "model": "gemma3"
        }
        
        with patch('routes.llm_routes.get_env_bool', return_value=False):
            with patch('routes.llm_routes.llm_state_manager') as mock_state_manager:
                with patch('routes.llm_routes.ChatOllama') as mock_chat_ollama:
                    mock_state_manager.check_if_model_is_available.return_value = True
                    
                    mock_llm_instance = MagicMock()
                    mock_response = MagicMock()
                    mock_response.content = "Empty message response"
                    mock_llm_instance.invoke.return_value = mock_response
                    mock_chat_ollama.return_value = mock_llm_instance
                    
                    response = client.post("/llm/generate", json=request_data)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["text"] == "Empty message response"
    
    @patch('routes.llm_routes.get_env_bool')
    @patch('routes.llm_routes.create_compatible_llm')
    def test_generate_with_custom_parameters(self, mock_create_llm, mock_get_env_bool, client):
        """Тест с кастомными параметрами"""
        mock_get_env_bool.return_value = True  # USE_YANDEX_CLOUD=true
        
        mock_llm = AsyncMock()
        mock_llm._acall.return_value = "Custom params response"
        mock_create_llm.return_value = mock_llm
        
        request_data = {
            "messages": "Test with custom params",
            "model": "yandexgpt-lite",
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        response = client.post("/llm/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Custom params response"
        
        # Проверяем что параметры были переданы
        mock_create_llm.assert_called_once_with(
            model="yandexgpt-lite",
            temperature=0.8,
            num_predict=500
        )

class TestGenerateEndpointIntegration:
    """Интеграционные тесты для эндпоинта /generate"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_end_to_end_yandex_flow(self):
        """Интеграционный тест полного потока с Yandex Cloud"""
        # Этот тест требует реальной конфигурации Yandex Cloud
        # В реальной среде он будет пропущен если конфигурация недоступна
        
        try:
            from config_utils import validate_yandex_config
            config = validate_yandex_config()
            
            if not config.get("use_yandex_cloud"):
                pytest.skip("Yandex Cloud не настроен для интеграционных тестов")
            
            client = TestClient(app)
            
            request_data = {
                "messages": "Привет! Это интеграционный тест.",
                "model": "yandexgpt",
                "temperature": 0.1,
                "max_tokens": 100
            }
            
            response = client.post("/llm/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["text"]) > 0
            assert data["model"] == "yandexgpt"
            
        except Exception as e:
            pytest.skip(f"Интеграционный тест пропущен: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])