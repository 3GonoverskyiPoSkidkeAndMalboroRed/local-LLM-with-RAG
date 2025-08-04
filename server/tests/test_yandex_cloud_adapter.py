"""
Unit тесты для YandexCloudAdapter
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yandex_cloud_adapter import (
    YandexCloudAdapter, 
    YandexCloudConfig, 
    YandexCloudError,
    YandexCloudAuthError,
    YandexCloudRateLimitError,
    YandexCloudTimeoutError,
    YandexCloudMetrics
)

class TestYandexCloudConfig:
    """Тесты для YandexCloudConfig"""
    
    def test_config_creation(self):
        """Тест создания конфигурации"""
        config = YandexCloudConfig(
            api_key="test_key",
            folder_id="test_folder"
        )
        
        assert config.api_key == "test_key"
        assert config.folder_id == "test_folder"
        assert config.llm_model == "yandexgpt"
        assert config.embedding_model == "text-search-doc"
        assert config.max_tokens == 2000
        assert config.temperature == 0.1
    
    @patch.dict(os.environ, {
        'YANDEX_API_KEY': 'env_test_key',
        'YANDEX_FOLDER_ID': 'env_test_folder',
        'YANDEX_LLM_MODEL': 'custom_model',
        'YANDEX_MAX_TOKENS': '3000',
        'YANDEX_TEMPERATURE': '0.5'
    })
    def test_config_from_env(self):
        """Тест создания конфигурации из переменных окружения"""
        config = YandexCloudConfig.from_env()
        
        assert config.api_key == "env_test_key"
        assert config.folder_id == "env_test_folder"
        assert config.llm_model == "custom_model"
        assert config.max_tokens == 3000
        assert config.temperature == 0.5
    
    def test_config_from_env_missing_required(self):
        """Тест ошибки при отсутствии обязательных переменных"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="YANDEX_API_KEY"):
                YandexCloudConfig.from_env()

class TestYandexCloudMetrics:
    """Тесты для YandexCloudMetrics"""
    
    def test_metrics_initialization(self):
        """Тест инициализации метрик"""
        metrics = YandexCloudMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_tokens_used == 0
        assert metrics.average_response_time == 0.0
        assert metrics.last_error is None
    
    def test_metrics_update_success(self):
        """Тест обновления метрик при успешном запросе"""
        metrics = YandexCloudMetrics()
        
        metrics.update_request(success=True, duration=1.5, tokens=100)
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_tokens_used == 100
        assert metrics.average_response_time == 1.5
        assert metrics.last_error is None
    
    def test_metrics_update_failure(self):
        """Тест обновления метрик при неуспешном запросе"""
        metrics = YandexCloudMetrics()
        
        metrics.update_request(success=False, duration=2.0, error="Test error")
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.total_tokens_used == 0
        assert metrics.average_response_time == 2.0
        assert metrics.last_error == "Test error"
    
    def test_metrics_average_calculation(self):
        """Тест расчета среднего времени ответа"""
        metrics = YandexCloudMetrics()
        
        metrics.update_request(success=True, duration=1.0)
        metrics.update_request(success=True, duration=3.0)
        
        assert metrics.average_response_time == 2.0

class TestYandexCloudAdapter:
    """Тесты для YandexCloudAdapter"""
    
    @pytest.fixture
    def config(self):
        """Фикстура конфигурации для тестов"""
        return YandexCloudConfig(
            api_key="test_api_key",
            folder_id="test_folder_id"
        )
    
    @pytest.fixture
    def adapter(self, config):
        """Фикстура адаптера для тестов"""
        return YandexCloudAdapter(config)
    
    def test_adapter_initialization(self, adapter, config):
        """Тест инициализации адаптера"""
        assert adapter.config == config
        assert isinstance(adapter.metrics, YandexCloudMetrics)
        assert adapter._session is None
    
    def test_auth_headers(self, adapter):
        """Тест генерации заголовков аутентификации"""
        headers = adapter._get_auth_headers()
        
        expected_headers = {
            "Authorization": "Api-Key test_api_key",
            "x-folder-id": "test_folder_id"
        }
        
        assert headers == expected_headers
    
    def test_extract_token_count(self, adapter):
        """Тест извлечения количества токенов"""
        # Тест с totalTokens
        response_data = {"usage": {"totalTokens": 150}}
        assert adapter._extract_token_count(response_data) == 150
        
        # Тест с total_tokens
        response_data = {"usage": {"total_tokens": 200}}
        assert adapter._extract_token_count(response_data) == 200
        
        # Тест без usage
        response_data = {}
        assert adapter._extract_token_count(response_data) == 0
    
    def test_extract_error_message(self, adapter):
        """Тест извлечения сообщения об ошибке"""
        # Тест с error.message
        response_data = {"error": {"message": "Test error message"}}
        assert adapter._extract_error_message(response_data, 400) == "Test error message"
        
        # Тест с error.description
        response_data = {"error": {"description": "Test description"}}
        assert adapter._extract_error_message(response_data, 400) == "Test description"
        
        # Тест с message
        response_data = {"message": "Direct message"}
        assert adapter._extract_error_message(response_data, 400) == "Direct message"
        
        # Тест без сообщения
        response_data = {}
        message = adapter._extract_error_message(response_data, 404)
        assert "HTTP 404" in message

class TestYandexCloudAdapterAsync:
    """Асинхронные тесты для YandexCloudAdapter"""
    
    @pytest.fixture
    def config(self):
        return YandexCloudConfig(
            api_key="test_api_key",
            folder_id="test_folder_id"
        )
    
    @pytest.fixture
    def adapter(self, config):
        return YandexCloudAdapter(config)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Тест использования адаптера как контекст менеджера"""
        async with adapter as a:
            assert a is adapter
            assert adapter._session is not None
            assert not adapter._session.closed
        
        # После выхода из контекста сессия должна быть закрыта
        assert adapter._session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, adapter):
        """Тест создания HTTP сессии"""
        assert adapter._session is None
        
        await adapter._ensure_session()
        
        assert adapter._session is not None
        assert isinstance(adapter._session, ClientSession)
        assert not adapter._session.closed
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, adapter):
        """Тест успешного HTTP запроса"""
        mock_response_data = {
            "result": {"alternatives": [{"message": {"text": "Test response"}}]},
            "usage": {"totalTokens": 50}
        }
        
        # Мокаем HTTP сессию
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=json.dumps(mock_response_data))
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        adapter._session = mock_session
        
        result = await adapter._make_request("POST", "/test", {"test": "data"})
        
        assert result == mock_response_data
        assert adapter.metrics.total_requests == 1
        assert adapter.metrics.successful_requests == 1
        assert adapter.metrics.total_tokens_used == 50
    
    @pytest.mark.asyncio
    async def test_make_request_auth_error(self, adapter):
        """Тест ошибки аутентификации"""
        mock_response_data = {"error": {"message": "Invalid API key"}}
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value=json.dumps(mock_response_data))
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        adapter._session = mock_session
        
        with pytest.raises(YandexCloudAuthError) as exc_info:
            await adapter._make_request("POST", "/test", {"test": "data"})
        
        assert "Invalid API key" in str(exc_info.value)
        assert adapter.metrics.failed_requests == 1
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, adapter):
        """Тест retry при превышении лимита запросов"""
        mock_session = AsyncMock()
        
        # Первый запрос - rate limit
        mock_response_429 = AsyncMock()
        mock_response_429.status = 429
        mock_response_429.text = AsyncMock(return_value='{"error": {"message": "Rate limit exceeded"}}')
        
        # Второй запрос - успех
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.text = AsyncMock(return_value='{"result": "success"}')
        
        mock_session.request.return_value.__aenter__.side_effect = [
            mock_response_429,
            mock_response_200
        ]
        
        adapter._session = mock_session
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await adapter._make_request("POST", "/test", {"test": "data"})
        
        assert result == {"result": "success"}
        assert mock_session.request.call_count == 2
        mock_sleep.assert_called_once_with(1)  # Первая задержка 2^0 = 1
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, adapter):
        """Тест успешной генерации текста"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Generated text response"}}
                ]
            },
            "usage": {"totalTokens": 75}
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await adapter.generate_text("Test prompt")
            
            assert result == "Generated text response"
            mock_request.assert_called_once()
            
            # Проверяем параметры запроса
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/foundationModels/v1/completion"
            
            request_data = call_args[0][2]
            assert "modelUri" in request_data
            assert "messages" in request_data
            assert request_data["messages"][0]["text"] == "Test prompt"
    
    @pytest.mark.asyncio
    async def test_generate_text_empty_response(self, adapter):
        """Тест генерации текста с пустым ответом"""
        mock_response_data = {"result": {"alternatives": []}}
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await adapter.generate_text("Test prompt")
            
            assert "не удалось сгенерировать ответ" in result.lower()
    
    @pytest.mark.asyncio
    async def test_generate_text_with_messages_list(self, adapter):
        """Тест генерации текста со списком сообщений"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Response to conversation"}}
                ]
            }
        }
        
        messages = [
            {"role": "user", "text": "Hello"},
            {"role": "assistant", "text": "Hi there!"},
            {"role": "user", "text": "How are you?"}
        ]
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await adapter.generate_text(messages)
            
            assert result == "Response to conversation"
            
            # Проверяем что сообщения переданы правильно
            call_args = mock_request.call_args
            request_data = call_args[0][2]
            assert len(request_data["messages"]) == 3
            assert request_data["messages"][0]["role"] == "user"
            assert request_data["messages"][0]["text"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_generate_text_openai_format_conversion(self, adapter):
        """Тест конвертации из OpenAI формата в Yandex формат"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Converted response"}}
                ]
            }
        }
        
        # OpenAI формат с "content" вместо "text"
        messages = [
            {"role": "user", "content": "Hello from OpenAI format"}
        ]
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await adapter.generate_text(messages)
            
            assert result == "Converted response"
            
            # Проверяем конвертацию
            call_args = mock_request.call_args
            request_data = call_args[0][2]
            assert request_data["messages"][0]["text"] == "Hello from OpenAI format"
            assert "content" not in request_data["messages"][0]
    
    @pytest.mark.asyncio
    async def test_generate_text_parameter_validation(self, adapter):
        """Тест валидации параметров генерации"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Valid response"}}
                ]
            }
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            # Тест с невалидной temperature
            result = await adapter.generate_text(
                "Test", 
                temperature=2.0,  # Вне диапазона [0, 1]
                max_tokens=10000  # Вне диапазона [1, 8000]
            )
            
            assert result == "Valid response"
            
            # Проверяем что использовались значения по умолчанию
            call_args = mock_request.call_args
            request_data = call_args[0][2]
            completion_options = request_data["completionOptions"]
            assert completion_options["temperature"] == adapter.config.temperature
            assert completion_options["maxTokens"] == adapter.config.max_tokens
    
    @pytest.mark.asyncio
    async def test_generate_text_custom_model(self, adapter):
        """Тест использования кастомной модели"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Custom model response"}}
                ]
            }
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await adapter.generate_text("Test", model="yandexgpt-lite")
            
            assert result == "Custom model response"
            
            # Проверяем что использовалась правильная модель
            call_args = mock_request.call_args
            request_data = call_args[0][2]
            expected_uri = f"gpt://{adapter.config.folder_id}/yandexgpt-lite"
            assert request_data["modelUri"] == expected_uri
    
    @pytest.mark.asyncio
    async def test_generate_text_invalid_messages_type(self, adapter):
        """Тест с неподдерживаемым типом сообщений"""
        with pytest.raises(ValueError, match="Неподдерживаемый тип messages"):
            await adapter.generate_text(123)  # Неподдерживаемый тип
    
    @pytest.mark.asyncio
    async def test_generate_text_empty_messages_list(self, adapter):
        """Тест с пустым списком сообщений"""
        with pytest.raises(ValueError, match="Не удалось обработать список сообщений"):
            await adapter.generate_text([])
    
    @pytest.mark.asyncio
    async def test_generate_text_yandex_cloud_error_propagation(self, adapter):
        """Тест проброса ошибок YandexCloudError"""
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = YandexCloudAuthError("Invalid API key", 401)
            
            with pytest.raises(YandexCloudAuthError):
                await adapter.generate_text("Test")
    
    @pytest.mark.asyncio
    async def test_generate_text_unexpected_error_wrapping(self, adapter):
        """Тест оборачивания неожиданных ошибок"""
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = ValueError("Unexpected error")
            
            with pytest.raises(YandexCloudError, match="Неожиданная ошибка при генерации текста"):
                await adapter.generate_text("Test")
    
    @pytest.mark.asyncio
    async def test_generate_text_stream(self, adapter):
        """Тест потоковой генерации текста"""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {"message": {"text": "Hello world test"}}
                ]
            }
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            chunks = []
            async for chunk in adapter.generate_text_stream("Test prompt"):
                chunks.append(chunk)
            
            # Проверяем что текст разбился на слова
            assert len(chunks) == 3  # "Hello ", "world ", "test"
            assert "".join(chunks) == "Hello world test"
    
    @pytest.mark.asyncio
    async def test_create_embeddings_success(self, adapter):
        """Тест успешного создания эмбеддингов"""
        mock_response_data = {
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6]
            ]
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            texts = ["Text 1", "Text 2"]
            result = await adapter.create_embeddings(texts)
            
            assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            mock_request.assert_called_once()
            
            # Проверяем параметры запроса
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/foundationModels/v1/textEmbedding"
            
            request_data = call_args[0][2]
            assert "modelUri" in request_data
            assert "texts" in request_data
            assert request_data["texts"] == texts
    
    @pytest.mark.asyncio
    async def test_create_embeddings_batch_processing(self, adapter):
        """Тест batch обработки эмбеддингов"""
        # Создаем список из 150 текстов (больше чем batch_size=100)
        texts = [f"Text {i}" for i in range(150)]
        
        mock_response_data_1 = {
            "embeddings": [[0.1, 0.2] for _ in range(100)]
        }
        mock_response_data_2 = {
            "embeddings": [[0.3, 0.4] for _ in range(50)]
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response_data_1, mock_response_data_2]
            
            result = await adapter.create_embeddings(texts)
            
            assert len(result) == 150
            assert mock_request.call_count == 2
    
    def test_get_metrics(self, adapter):
        """Тест получения метрик"""
        # Обновляем метрики
        adapter.metrics.update_request(True, 1.5, 100)
        adapter.metrics.update_request(False, 2.0, error="Test error")
        
        metrics = adapter.get_metrics()
        
        assert metrics["total_requests"] == 2
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == 0.5
        assert metrics["total_tokens_used"] == 100
        assert metrics["last_error"] == "Test error"
    
    def test_reset_metrics(self, adapter):
        """Тест сброса метрик"""
        # Устанавливаем некоторые метрики
        adapter.metrics.update_request(True, 1.0, 50)
        
        assert adapter.metrics.total_requests == 1
        
        # Сбрасываем метрики
        adapter.reset_metrics()
        
        assert adapter.metrics.total_requests == 0
        assert adapter.metrics.successful_requests == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])