"""
Unit тесты для YandexLLM классов
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yandex_llm import (
    YandexGPT, 
    YandexChatModel, 
    ChatYandex,
    create_yandex_llm,
    create_yandex_chat_model,
    create_compatible_llm
)
from yandex_cloud_adapter import YandexCloudAdapter, YandexCloudConfig

class TestYandexGPT:
    """Тесты для YandexGPT класса"""
    
    @pytest.fixture
    def llm(self):
        """Фикстура YandexGPT для тестов"""
        return YandexGPT(
            model="yandexgpt",
            temperature=0.2,
            max_tokens=1000
        )
    
    def test_llm_initialization(self, llm):
        """Тест инициализации LLM"""
        assert llm.model == "yandexgpt"
        assert llm.temperature == 0.2
        assert llm.max_tokens == 1000
        assert llm._llm_type == "yandex_gpt"
    
    def test_identifying_params(self, llm):
        """Тест параметров идентификации"""
        params = llm._identifying_params
        
        assert params["model"] == "yandexgpt"
        assert params["temperature"] == 0.2
        assert params["max_tokens"] == 1000
    
    @pytest.mark.asyncio
    async def test_acall_success(self, llm):
        """Тест успешного асинхронного вызова"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Generated response"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            result = await llm._acall("Test prompt")
            
            assert result == "Generated response"
            mock_adapter.generate_text.assert_called_once_with(
                "Test prompt",
                model="yandexgpt",
                temperature=0.2,
                max_tokens=1000
            )
    
    @pytest.mark.asyncio
    async def test_acall_with_stop_sequences(self, llm):
        """Тест с stop sequences"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Generated response STOP more text"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            result = await llm._acall("Test prompt", stop=["STOP"])
            
            assert result == "Generated response "
    
    @pytest.mark.asyncio
    async def test_acall_with_kwargs(self, llm):
        """Тест с дополнительными параметрами"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Custom response"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            result = await llm._acall(
                "Test prompt", 
                temperature=0.5,
                max_tokens=500,
                custom_param="value"
            )
            
            assert result == "Custom response"
            mock_adapter.generate_text.assert_called_once_with(
                "Test prompt",
                model="yandexgpt",
                temperature=0.5,  # Переопределенное значение
                max_tokens=500,   # Переопределенное значение
                custom_param="value"
            )
    
    def test_call_sync(self, llm):
        """Тест синхронного вызова"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Sync response"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            with patch('asyncio.new_event_loop') as mock_loop_create:
                mock_loop = MagicMock()
                mock_loop_create.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "Sync response"
                
                result = llm._call("Test prompt")
                
                assert result == "Sync response"
                mock_loop.run_until_complete.assert_called_once()
                mock_loop.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_astream(self, llm):
        """Тест асинхронного потока"""
        mock_adapter = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "world"
        
        mock_adapter.generate_text_stream = mock_stream
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            chunks = []
            async for chunk in llm._astream("Test prompt"):
                chunks.append(chunk)
            
            assert chunks == ["Hello ", "world"]
    
    @pytest.mark.asyncio
    async def test_astream_with_stop(self, llm):
        """Тест потока с stop sequences"""
        mock_adapter = AsyncMock()
        
        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "STOP more text"
        
        mock_adapter.generate_text_stream = mock_stream
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            chunks = []
            async for chunk in llm._astream("Test prompt", stop=["STOP"]):
                chunks.append(chunk)
            
            assert chunks == ["Hello ", ""]  # Второй chunk обрезается

class TestYandexChatModel:
    """Тесты для YandexChatModel класса"""
    
    @pytest.fixture
    def chat_model(self):
        """Фикстура YandexChatModel для тестов"""
        return YandexChatModel(
            model="yandexgpt",
            temperature=0.3,
            max_tokens=1500
        )
    
    def test_chat_model_initialization(self, chat_model):
        """Тест инициализации chat модели"""
        assert chat_model.model == "yandexgpt"
        assert chat_model.temperature == 0.3
        assert chat_model.max_tokens == 1500
        assert chat_model._llm_type == "yandex_chat"
    
    def test_convert_messages_to_yandex_format(self, chat_model):
        """Тест конвертации сообщений в формат Yandex"""
        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?")
        ]
        
        yandex_messages = chat_model._convert_messages_to_yandex_format(messages)
        
        expected = [
            {"role": "system", "text": "You are a helpful assistant"},
            {"role": "user", "text": "Hello"},
            {"role": "assistant", "text": "Hi there!"},
            {"role": "user", "text": "How are you?"}
        ]
        
        assert yandex_messages == expected
    
    @pytest.mark.asyncio
    async def test_agenerate_success(self, chat_model):
        """Тест успешной генерации чата"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Chat response"
        
        messages = [HumanMessage(content="Hello")]
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            result = await chat_model._agenerate(messages)
            
            assert len(result.generations) == 1
            assert result.generations[0].message.content == "Chat response"
            assert isinstance(result.generations[0].message, AIMessage)
            
            # Проверяем что адаптер был вызван с правильными параметрами
            mock_adapter.generate_text.assert_called_once()
            call_args = mock_adapter.generate_text.call_args
            
            # Проверяем сообщения
            yandex_messages = call_args[0][0]
            assert yandex_messages == [{"role": "user", "text": "Hello"}]
            
            # Проверяем параметры
            kwargs = call_args[1]
            assert kwargs["model"] == "yandexgpt"
            assert kwargs["temperature"] == 0.3
            assert kwargs["max_tokens"] == 1500
    
    @pytest.mark.asyncio
    async def test_agenerate_with_stop(self, chat_model):
        """Тест генерации с stop sequences"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Response STOP extra"
        
        messages = [HumanMessage(content="Test")]
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            result = await chat_model._agenerate(messages, stop=["STOP"])
            
            assert result.generations[0].message.content == "Response "
    
    def test_generate_sync(self, chat_model):
        """Тест синхронной генерации"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Sync chat response"
        
        messages = [HumanMessage(content="Hello")]
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            with patch('asyncio.new_event_loop') as mock_loop_create:
                mock_loop = MagicMock()
                mock_loop_create.return_value = mock_loop
                
                # Создаем mock результат
                from langchain_core.outputs import ChatResult, ChatGeneration
                mock_result = ChatResult(generations=[
                    ChatGeneration(message=AIMessage(content="Sync chat response"))
                ])
                mock_loop.run_until_complete.return_value = mock_result
                
                result = chat_model._generate(messages)
                
                assert result.generations[0].message.content == "Sync chat response"
                mock_loop.run_until_complete.assert_called_once()
                mock_loop.close.assert_called_once()

class TestFactoryFunctions:
    """Тесты для фабричных функций"""
    
    def test_create_yandex_llm(self):
        """Тест создания YandexGPT через фабрику"""
        llm = create_yandex_llm(
            model="yandexgpt-lite",
            temperature=0.7,
            max_tokens=500
        )
        
        assert isinstance(llm, YandexGPT)
        assert llm.model == "yandexgpt-lite"
        assert llm.temperature == 0.7
        assert llm.max_tokens == 500
    
    def test_create_yandex_chat_model(self):
        """Тест создания YandexChatModel через фабрику"""
        chat_model = create_yandex_chat_model(
            model="yandexgpt",
            temperature=0.4,
            max_tokens=800
        )
        
        assert isinstance(chat_model, YandexChatModel)
        assert chat_model.model == "yandexgpt"
        assert chat_model.temperature == 0.4
        assert chat_model.max_tokens == 800
    
    def test_create_compatible_llm(self):
        """Тест создания совместимой модели"""
        llm = create_compatible_llm(
            model="yandexgpt",
            base_url="http://ignored",  # Должен игнорироваться
            temperature=0.6,
            num_predict=1200  # Должен маппиться на max_tokens
        )
        
        assert isinstance(llm, YandexChatModel)
        assert llm.model == "yandexgpt"
        assert llm.temperature == 0.6
        assert llm.max_tokens == 1200
    
    def test_create_compatible_llm_with_max_tokens_override(self):
        """Тест приоритета max_tokens над num_predict"""
        llm = create_compatible_llm(
            model="yandexgpt",
            num_predict=1000,
            max_tokens=1500  # Должен иметь приоритет
        )
        
        assert llm.max_tokens == 1500
    
    def test_chat_yandex_alias(self):
        """Тест алиаса ChatYandex"""
        chat = ChatYandex(model="yandexgpt")
        
        assert isinstance(chat, YandexChatModel)
        assert isinstance(chat, ChatYandex)
        assert chat.model == "yandexgpt"

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_llm_flow(self):
        """Тест полного потока работы LLM"""
        # Мокаем конфигурацию
        mock_config = YandexCloudConfig(
            api_key="test_key",
            folder_id="test_folder"
        )
        
        # Мокаем адаптер
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "End-to-end response"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            llm = YandexGPT(model="yandexgpt", temperature=0.1)
            
            # Тестируем асинхронный вызов
            result = await llm._acall("Test prompt")
            assert result == "End-to-end response"
            
            # Тестируем потоковый вызов
            mock_adapter.generate_text_stream = AsyncMock()
            
            async def mock_stream(*args, **kwargs):
                yield "Stream "
                yield "response"
            
            mock_adapter.generate_text_stream.side_effect = mock_stream
            
            chunks = []
            async for chunk in llm._astream("Test prompt"):
                chunks.append(chunk)
            
            assert chunks == ["Stream ", "response"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_chat_flow(self):
        """Тест полного потока работы Chat модели"""
        mock_adapter = AsyncMock()
        mock_adapter.generate_text.return_value = "Chat end-to-end response"
        
        with patch('yandex_llm.get_yandex_adapter', return_value=mock_adapter):
            chat_model = YandexChatModel(model="yandexgpt")
            
            messages = [
                SystemMessage(content="You are helpful"),
                HumanMessage(content="Hello"),
                AIMessage(content="Hi!"),
                HumanMessage(content="How are you?")
            ]
            
            result = await chat_model._agenerate(messages)
            
            assert len(result.generations) == 1
            assert result.generations[0].message.content == "Chat end-to-end response"
            
            # Проверяем что сообщения были правильно конвертированы
            call_args = mock_adapter.generate_text.call_args[0][0]
            expected_messages = [
                {"role": "system", "text": "You are helpful"},
                {"role": "user", "text": "Hello"},
                {"role": "assistant", "text": "Hi!"},
                {"role": "user", "text": "How are you?"}
            ]
            assert call_args == expected_messages

if __name__ == "__main__":
    pytest.main([__file__, "-v"])