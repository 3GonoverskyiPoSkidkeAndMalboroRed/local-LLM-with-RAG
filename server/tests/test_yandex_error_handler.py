"""
Тесты для YandexCloudErrorHandler и системы обработки ошибок
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yandex_error_handler import (
    YandexCloudErrorHandler,
    GracefulDegradationManager,
    RetryConfig,
    CircuitBreakerConfig,
    CircuitBreakerState,
    get_error_handler,
    get_degradation_manager,
    configure_error_handling
)
from yandex_cloud_adapter import (
    YandexCloudError,
    YandexCloudAuthError,
    YandexCloudRateLimitError,
    YandexCloudTimeoutError
)

class TestRetryConfig:
    """Тесты для RetryConfig"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert YandexCloudRateLimitError in config.retryable_errors
        assert YandexCloudAuthError in config.non_retryable_errors
    
    def test_custom_config(self):
        """Тест кастомной конфигурации"""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            jitter=False
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.jitter is False

class TestCircuitBreakerConfig:
    """Тесты для CircuitBreakerConfig"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 3

class TestYandexCloudErrorHandler:
    """Тесты для YandexCloudErrorHandler"""
    
    @pytest.fixture
    def error_handler(self):
        """Фикстура error handler для тестов"""
        return YandexCloudErrorHandler(
            retry_config=RetryConfig(max_retries=2, base_delay=0.1),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=2),
            enable_circuit_breaker=True
        )
    
    def test_initialization(self, error_handler):
        """Тест инициализации error handler"""
        assert error_handler.circuit_state == CircuitBreakerState.CLOSED
        assert error_handler.failure_count == 0
        assert error_handler.success_count == 0
        assert error_handler.error_stats.total_errors == 0
    
    def test_is_retryable_error(self, error_handler):
        """Тест определения повторяемых ошибок"""
        # Повторяемые ошибки
        assert error_handler._is_retryable_error(YandexCloudRateLimitError("Rate limit")) is True
        assert error_handler._is_retryable_error(YandexCloudTimeoutError("Timeout")) is True
        assert error_handler._is_retryable_error(ConnectionError("Connection failed")) is True
        
        # Неповторяемые ошибки
        assert error_handler._is_retryable_error(YandexCloudAuthError("Auth failed")) is False
        assert error_handler._is_retryable_error(ValueError("Invalid value")) is False
    
    def test_calculate_delay(self, error_handler):
        """Тест вычисления задержки"""
        # Без jitter для предсказуемости
        error_handler.retry_config.jitter = False
        
        delay0 = error_handler._calculate_delay(0)
        delay1 = error_handler._calculate_delay(1)
        delay2 = error_handler._calculate_delay(2)
        
        assert delay0 == 0.1  # base_delay
        assert delay1 == 0.2  # base_delay * 2^1
        assert delay2 == 0.4  # base_delay * 2^2
    
    def test_calculate_delay_with_max(self, error_handler):
        """Тест ограничения максимальной задержки"""
        error_handler.retry_config.jitter = False
        error_handler.retry_config.max_delay = 0.3
        
        delay3 = error_handler._calculate_delay(3)  # Должно быть 0.8, но ограничено 0.3
        assert delay3 == 0.3
    
    def test_update_error_stats(self, error_handler):
        """Тест обновления статистики ошибок"""
        # Тестируем разные типы ошибок
        error_handler._update_error_stats(YandexCloudAuthError("Auth error"))
        assert error_handler.error_stats.auth_errors == 1
        assert error_handler.error_stats.total_errors == 1
        
        error_handler._update_error_stats(YandexCloudRateLimitError("Rate limit"))
        assert error_handler.error_stats.rate_limit_errors == 1
        assert error_handler.error_stats.total_errors == 2
        
        error_handler._update_error_stats(ConnectionError("Connection error"))
        assert error_handler.error_stats.connection_errors == 1
        assert error_handler.error_stats.total_errors == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, error_handler):
        """Тест успешного выполнения без retry"""
        mock_operation = AsyncMock(return_value="success")
        
        result = await error_handler.execute_with_retry(
            mock_operation,
            "test_operation",
            "arg1", "arg2"
        )
        
        assert result == "success"
        mock_operation.assert_called_once_with("arg1", "arg2")
        assert error_handler.error_stats.total_errors == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_failure(self, error_handler):
        """Тест успешного выполнения после нескольких ошибок"""
        mock_operation = AsyncMock()
        mock_operation.side_effect = [
            YandexCloudRateLimitError("Rate limit"),
            YandexCloudTimeoutError("Timeout"),
            "success"
        ]
        
        result = await error_handler.execute_with_retry(
            mock_operation,
            "test_operation"
        )
        
        assert result == "success"
        assert mock_operation.call_count == 3
        assert error_handler.error_stats.total_errors == 2
        assert error_handler.error_stats.rate_limit_errors == 1
        assert error_handler.error_stats.timeout_errors == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, error_handler):
        """Тест с неповторяемой ошибкой"""
        mock_operation = AsyncMock(side_effect=YandexCloudAuthError("Auth failed"))
        
        with pytest.raises(YandexCloudAuthError):
            await error_handler.execute_with_retry(
                mock_operation,
                "test_operation"
            )
        
        # Должна быть только одна попытка
        mock_operation.assert_called_once()
        assert error_handler.error_stats.auth_errors == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self, error_handler):
        """Тест исчерпания всех попыток"""
        mock_operation = AsyncMock(side_effect=YandexCloudRateLimitError("Rate limit"))
        
        with pytest.raises(YandexCloudError, match="не удался после 3 попыток"):
            await error_handler.execute_with_retry(
                mock_operation,
                "test_operation"
            )
        
        # Должно быть max_retries + 1 попыток
        assert mock_operation.call_count == 3  # 2 + 1
        assert error_handler.error_stats.rate_limit_errors == 3
    
    def test_circuit_breaker_closed_state(self, error_handler):
        """Тест Circuit Breaker в закрытом состоянии"""
        assert error_handler._check_circuit_breaker() is True
        assert error_handler.circuit_state == CircuitBreakerState.CLOSED
    
    def test_circuit_breaker_opens_after_failures(self, error_handler):
        """Тест открытия Circuit Breaker после ошибок"""
        # Регистрируем ошибки до достижения порога
        for _ in range(error_handler.circuit_breaker_config.failure_threshold):
            error_handler._record_failure(YandexCloudRateLimitError("Rate limit"))
        
        assert error_handler.circuit_state == CircuitBreakerState.OPEN
        assert error_handler._check_circuit_breaker() is False
    
    def test_circuit_breaker_half_open_transition(self, error_handler):
        """Тест перехода Circuit Breaker в HALF_OPEN состояние"""
        # Открываем circuit breaker
        for _ in range(error_handler.circuit_breaker_config.failure_threshold):
            error_handler._record_failure(YandexCloudRateLimitError("Rate limit"))
        
        assert error_handler.circuit_state == CircuitBreakerState.OPEN
        
        # Имитируем прошедшее время
        error_handler.last_failure_time = datetime.now() - timedelta(seconds=61)
        
        # Проверяем переход в HALF_OPEN
        assert error_handler._check_circuit_breaker() is True
        assert error_handler.circuit_state == CircuitBreakerState.HALF_OPEN
    
    def test_circuit_breaker_closes_after_successes(self, error_handler):
        """Тест закрытия Circuit Breaker после успехов"""
        # Переводим в HALF_OPEN состояние
        error_handler.circuit_state = CircuitBreakerState.HALF_OPEN
        
        # Регистрируем успехи
        for _ in range(error_handler.circuit_breaker_config.success_threshold):
            error_handler._record_success()
        
        assert error_handler.circuit_state == CircuitBreakerState.CLOSED
        assert error_handler.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_requests(self, error_handler):
        """Тест блокировки запросов открытым Circuit Breaker"""
        # Открываем circuit breaker
        for _ in range(error_handler.circuit_breaker_config.failure_threshold):
            error_handler._record_failure(YandexCloudRateLimitError("Rate limit"))
        
        mock_operation = AsyncMock(return_value="success")
        
        with pytest.raises(YandexCloudError, match="Circuit Breaker открыт"):
            await error_handler.execute_with_retry(
                mock_operation,
                "test_operation"
            )
        
        # Операция не должна была вызываться
        mock_operation.assert_not_called()
    
    def test_get_stats(self, error_handler):
        """Тест получения статистики"""
        # Добавляем немного данных
        error_handler._record_failure(YandexCloudAuthError("Auth error"))
        error_handler._record_failure(YandexCloudRateLimitError("Rate limit"))
        
        stats = error_handler.get_stats()
        
        assert stats["circuit_breaker"]["state"] == "closed"
        assert stats["circuit_breaker"]["failure_count"] == 2
        assert stats["error_stats"]["total_errors"] == 2
        assert stats["error_stats"]["auth_errors"] == 1
        assert stats["error_stats"]["rate_limit_errors"] == 1
        assert stats["retry_config"]["max_retries"] == 2
    
    def test_reset_circuit_breaker(self, error_handler):
        """Тест сброса Circuit Breaker"""
        # Открываем circuit breaker
        for _ in range(error_handler.circuit_breaker_config.failure_threshold):
            error_handler._record_failure(YandexCloudRateLimitError("Rate limit"))
        
        assert error_handler.circuit_state == CircuitBreakerState.OPEN
        
        # Сбрасываем
        error_handler.reset_circuit_breaker()
        
        assert error_handler.circuit_state == CircuitBreakerState.CLOSED
        assert error_handler.failure_count == 0
    
    def test_reset_stats(self, error_handler):
        """Тест сброса статистики"""
        error_handler._record_failure(YandexCloudAuthError("Auth error"))
        assert error_handler.error_stats.total_errors == 1
        
        error_handler.reset_stats()
        assert error_handler.error_stats.total_errors == 0

class TestGracefulDegradationManager:
    """Тесты для GracefulDegradationManager"""
    
    @pytest.fixture
    def degradation_manager(self):
        """Фикстура degradation manager для тестов"""
        return GracefulDegradationManager()
    
    def test_initialization(self, degradation_manager):
        """Тест инициализации degradation manager"""
        assert degradation_manager.degradation_active is False
        assert degradation_manager.degradation_start_time is None
        assert len(degradation_manager.fallback_providers) == 0
    
    def test_register_fallback(self, degradation_manager):
        """Тест регистрации fallback провайдера"""
        mock_fallback = AsyncMock()
        
        degradation_manager.register_fallback("test_service", mock_fallback)
        
        assert "test_service" in degradation_manager.fallback_providers
        assert degradation_manager.fallback_providers["test_service"] == mock_fallback
    
    def test_activate_deactivate_degradation(self, degradation_manager):
        """Тест активации и деактивации degradation"""
        assert degradation_manager.degradation_active is False
        
        degradation_manager.activate_degradation("Test reason")
        
        assert degradation_manager.degradation_active is True
        assert degradation_manager.degradation_start_time is not None
        
        degradation_manager.deactivate_degradation()
        
        assert degradation_manager.degradation_active is False
        assert degradation_manager.degradation_start_time is None
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self, degradation_manager):
        """Тест успешного выполнения основной операции"""
        mock_primary = AsyncMock(return_value="primary_result")
        mock_fallback = AsyncMock(return_value="fallback_result")
        
        degradation_manager.register_fallback("test_service", mock_fallback)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            mock_primary,
            "arg1", "arg2"
        )
        
        assert result == "primary_result"
        mock_primary.assert_called_once_with("arg1", "arg2")
        mock_fallback.assert_not_called()
        assert degradation_manager.degradation_active is False
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_primary_fails(self, degradation_manager):
        """Тест fallback при ошибке основной операции"""
        mock_primary = AsyncMock(side_effect=Exception("Primary failed"))
        mock_fallback = AsyncMock(return_value="fallback_result")
        
        degradation_manager.register_fallback("test_service", mock_fallback)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            mock_primary,
            "arg1", "arg2"
        )
        
        assert result == "fallback_result"
        mock_primary.assert_called_once_with("arg1", "arg2")
        mock_fallback.assert_called_once_with("arg1", "arg2")
        assert degradation_manager.degradation_active is True
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_both_fail(self, degradation_manager):
        """Тест когда и основная операция, и fallback не работают"""
        mock_primary = AsyncMock(side_effect=Exception("Primary failed"))
        mock_fallback = AsyncMock(side_effect=Exception("Fallback failed"))
        
        degradation_manager.register_fallback("test_service", mock_fallback)
        
        with pytest.raises(YandexCloudError, match="Ошибки как основного сервиса"):
            await degradation_manager.execute_with_fallback(
                "test_service",
                mock_primary,
                "arg1", "arg2"
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_fallback_registered(self, degradation_manager):
        """Тест без зарегистрированного fallback"""
        mock_primary = AsyncMock(side_effect=Exception("Primary failed"))
        
        with pytest.raises(Exception, match="Primary failed"):
            await degradation_manager.execute_with_fallback(
                "test_service",
                mock_primary
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_degradation_active(self, degradation_manager):
        """Тест использования fallback когда degradation уже активен"""
        mock_primary = AsyncMock(return_value="primary_result")
        mock_fallback = AsyncMock(return_value="fallback_result")
        
        degradation_manager.register_fallback("test_service", mock_fallback)
        degradation_manager.activate_degradation("Test reason")
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            mock_primary
        )
        
        assert result == "fallback_result"
        mock_primary.assert_not_called()  # Основная операция не должна вызываться
        mock_fallback.assert_called_once()
    
    def test_get_status(self, degradation_manager):
        """Тест получения статуса degradation manager"""
        mock_fallback = AsyncMock()
        degradation_manager.register_fallback("test_service", mock_fallback)
        
        status = degradation_manager.get_status()
        
        assert status["degradation_active"] is False
        assert status["registered_fallbacks"] == ["test_service"]
        assert status["degradation_duration"] == 0
        
        # Активируем degradation
        degradation_manager.activate_degradation("Test")
        status = degradation_manager.get_status()
        
        assert status["degradation_active"] is True
        assert status["degradation_duration"] > 0

class TestGlobalFunctions:
    """Тесты для глобальных функций"""
    
    def test_get_error_handler(self):
        """Тест получения глобального error handler"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Должен возвращать тот же экземпляр
        assert handler1 is handler2
        assert isinstance(handler1, YandexCloudErrorHandler)
    
    def test_get_degradation_manager(self):
        """Тест получения глобального degradation manager"""
        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()
        
        # Должен возвращать тот же экземпляр
        assert manager1 is manager2
        assert isinstance(manager1, GracefulDegradationManager)
    
    def test_configure_error_handling(self):
        """Тест конфигурации глобальной обработки ошибок"""
        custom_retry_config = RetryConfig(max_retries=5)
        custom_circuit_config = CircuitBreakerConfig(failure_threshold=10)
        
        configure_error_handling(
            retry_config=custom_retry_config,
            circuit_breaker_config=custom_circuit_config,
            enable_circuit_breaker=False
        )
        
        handler = get_error_handler()
        assert handler.retry_config.max_retries == 5
        assert handler.circuit_breaker_config.failure_threshold == 10
        assert handler.enable_circuit_breaker is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])