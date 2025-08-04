"""
Система обработки ошибок и retry механизмов для Yandex Cloud API
Включает circuit breaker, exponential backoff и graceful degradation
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from yandex_cloud_adapter import (
    YandexCloudError, 
    YandexCloudAuthError, 
    YandexCloudRateLimitError, 
    YandexCloudTimeoutError
)

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"      # Нормальная работа
    OPEN = "open"          # Блокировка запросов
    HALF_OPEN = "half_open"  # Тестирование восстановления

@dataclass
class RetryConfig:
    """Конфигурация retry механизма"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # Типы ошибок для retry
    retryable_errors: List[type] = field(default_factory=lambda: [
        YandexCloudRateLimitError,
        YandexCloudTimeoutError,
        ConnectionError,
        TimeoutError
    ])
    
    # Типы ошибок, которые НЕ нужно повторять
    non_retryable_errors: List[type] = field(default_factory=lambda: [
        YandexCloudAuthError,
        ValueError,
        TypeError
    ])

@dataclass
class CircuitBreakerConfig:
    """Конфигурация Circuit Breaker"""
    failure_threshold: int = 5  # Количество ошибок для открытия
    recovery_timeout: float = 60.0  # Время до попытки восстановления (сек)
    success_threshold: int = 3  # Количество успехов для закрытия
    
@dataclass
class ErrorStats:
    """Статистика ошибок"""
    total_errors: int = 0
    auth_errors: int = 0
    rate_limit_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    other_errors: int = 0
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None

class YandexCloudErrorHandler:
    """
    Централизованная система обработки ошибок для Yandex Cloud API
    """
    
    def __init__(
        self, 
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        enable_circuit_breaker: bool = True
    ):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Circuit Breaker состояние
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        
        # Статистика ошибок
        self.error_stats = ErrorStats()
        
        # Callbacks для уведомлений
        self.on_circuit_open: Optional[Callable] = None
        self.on_circuit_close: Optional[Callable] = None
        self.on_retry: Optional[Callable] = None
        
        logger.info(f"YandexCloudErrorHandler инициализирован: "
                   f"max_retries={self.retry_config.max_retries}, "
                   f"circuit_breaker={'enabled' if enable_circuit_breaker else 'disabled'}")
    
    def _update_error_stats(self, error: Exception) -> None:
        """Обновление статистики ошибок"""
        self.error_stats.total_errors += 1
        self.error_stats.last_error_time = datetime.now()
        self.error_stats.last_error_message = str(error)
        
        if isinstance(error, YandexCloudAuthError):
            self.error_stats.auth_errors += 1
        elif isinstance(error, YandexCloudRateLimitError):
            self.error_stats.rate_limit_errors += 1
        elif isinstance(error, YandexCloudTimeoutError):
            self.error_stats.timeout_errors += 1
        elif isinstance(error, (ConnectionError, OSError)):
            self.error_stats.connection_errors += 1
        else:
            self.error_stats.other_errors += 1
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Проверка, можно ли повторить запрос при данной ошибке"""
        # Сначала проверяем non-retryable ошибки
        for error_type in self.retry_config.non_retryable_errors:
            if isinstance(error, error_type):
                return False
        
        # Затем проверяем retryable ошибки
        for error_type in self.retry_config.retryable_errors:
            if isinstance(error, error_type):
                return True
        
        # По умолчанию не повторяем неизвестные ошибки
        return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """Вычисление задержки с exponential backoff и jitter"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        if self.retry_config.jitter:
            # Добавляем случайность ±25%
            import random
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _check_circuit_breaker(self) -> bool:
        """
        Проверка состояния Circuit Breaker
        
        Returns:
            True если запрос можно выполнить, False если заблокирован
        """
        if not self.enable_circuit_breaker:
            return True
        
        now = datetime.now()
        
        if self.circuit_state == CircuitBreakerState.CLOSED:
            # Нормальное состояние
            return True
        
        elif self.circuit_state == CircuitBreakerState.OPEN:
            # Проверяем, не пора ли попробовать восстановление
            if (self.last_failure_time and 
                (now - self.last_failure_time).total_seconds() >= self.circuit_breaker_config.recovery_timeout):
                
                logger.info("Circuit Breaker переходит в HALF_OPEN состояние")
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            
            # Еще рано для восстановления
            return False
        
        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Тестируем восстановление
            return True
        
        return False
    
    def _record_success(self) -> None:
        """Регистрация успешного запроса"""
        if not self.enable_circuit_breaker:
            return
        
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.circuit_breaker_config.success_threshold:
                logger.info("Circuit Breaker закрывается после успешного восстановления")
                self.circuit_state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                
                if self.on_circuit_close:
                    self.on_circuit_close()
        
        elif self.circuit_state == CircuitBreakerState.CLOSED:
            # Сбрасываем счетчик ошибок при успехе
            self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self, error: Exception) -> None:
        """Регистрация неуспешного запроса"""
        self._update_error_stats(error)
        
        if not self.enable_circuit_breaker:
            return
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Возвращаемся в OPEN состояние
            logger.warning("Circuit Breaker возвращается в OPEN состояние после ошибки")
            self.circuit_state = CircuitBreakerState.OPEN
            
        elif (self.circuit_state == CircuitBreakerState.CLOSED and 
              self.failure_count >= self.circuit_breaker_config.failure_threshold):
            
            logger.error(f"Circuit Breaker открывается после {self.failure_count} ошибок")
            self.circuit_state = CircuitBreakerState.OPEN
            
            if self.on_circuit_open:
                self.on_circuit_open()
    
    async def execute_with_retry(
        self, 
        operation: Callable,
        operation_name: str = "API call",
        *args, 
        **kwargs
    ) -> Any:
        """
        Выполнение операции с retry механизмом и circuit breaker
        
        Args:
            operation: Асинхронная функция для выполнения
            operation_name: Название операции для логирования
            *args, **kwargs: Аргументы для операции
            
        Returns:
            Результат выполнения операции
            
        Raises:
            YandexCloudError: При исчерпании всех попыток или критических ошибках
        """
        # Проверяем Circuit Breaker
        if not self._check_circuit_breaker():
            raise YandexCloudError(
                f"Circuit Breaker открыт для {operation_name}. "
                f"Следующая попытка через {self.circuit_breaker_config.recovery_timeout}с"
            )
        
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                logger.debug(f"Выполнение {operation_name}, попытка {attempt + 1}/{self.retry_config.max_retries + 1}")
                
                result = await operation(*args, **kwargs)
                
                # Успешное выполнение
                self._record_success()
                
                if attempt > 0:
                    logger.info(f"{operation_name} успешно выполнен с {attempt + 1} попытки")
                
                return result
                
            except Exception as error:
                last_error = error
                self._record_failure(error)
                
                # Проверяем, можно ли повторить
                if not self._is_retryable_error(error):
                    logger.error(f"{operation_name} завершен с неповторяемой ошибкой: {error}")
                    raise
                
                # Если это последняя попытка
                if attempt >= self.retry_config.max_retries:
                    logger.error(f"{operation_name} исчерпал все {self.retry_config.max_retries + 1} попыток")
                    break
                
                # Вычисляем задержку
                delay = self._calculate_delay(attempt)
                
                logger.warning(f"{operation_name} ошибка (попытка {attempt + 1}): {error}. "
                             f"Повтор через {delay:.2f}с")
                
                if self.on_retry:
                    self.on_retry(attempt + 1, error, delay)
                
                await asyncio.sleep(delay)
        
        # Все попытки исчерпаны
        if last_error:
            raise YandexCloudError(f"{operation_name} не удался после {self.retry_config.max_retries + 1} попыток: {last_error}")
        else:
            raise YandexCloudError(f"{operation_name} не удался по неизвестной причине")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики обработки ошибок"""
        return {
            "circuit_breaker": {
                "enabled": self.enable_circuit_breaker,
                "state": self.circuit_state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
            },
            "error_stats": {
                "total_errors": self.error_stats.total_errors,
                "auth_errors": self.error_stats.auth_errors,
                "rate_limit_errors": self.error_stats.rate_limit_errors,
                "timeout_errors": self.error_stats.timeout_errors,
                "connection_errors": self.error_stats.connection_errors,
                "other_errors": self.error_stats.other_errors,
                "last_error_time": self.error_stats.last_error_time.isoformat() if self.error_stats.last_error_time else None,
                "last_error_message": self.error_stats.last_error_message
            },
            "retry_config": {
                "max_retries": self.retry_config.max_retries,
                "base_delay": self.retry_config.base_delay,
                "max_delay": self.retry_config.max_delay,
                "exponential_base": self.retry_config.exponential_base,
                "jitter": self.retry_config.jitter
            }
        }
    
    def reset_circuit_breaker(self) -> None:
        """Принудительный сброс Circuit Breaker"""
        logger.info("Принудительный сброс Circuit Breaker")
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def reset_stats(self) -> None:
        """Сброс статистики ошибок"""
        logger.info("Сброс статистики ошибок")
        self.error_stats = ErrorStats()

class GracefulDegradationManager:
    """
    Менеджер для graceful degradation - переключения на альтернативные сервисы
    """
    
    def __init__(self):
        self.fallback_providers = {}
        self.degradation_active = False
        self.degradation_start_time: Optional[datetime] = None
        
    def register_fallback(self, service_name: str, fallback_provider: Callable) -> None:
        """Регистрация fallback провайдера для сервиса"""
        self.fallback_providers[service_name] = fallback_provider
        logger.info(f"Зарегистрирован fallback для сервиса: {service_name}")
    
    def activate_degradation(self, reason: str) -> None:
        """Активация режима graceful degradation"""
        if not self.degradation_active:
            self.degradation_active = True
            self.degradation_start_time = datetime.now()
            logger.warning(f"Активирован режим graceful degradation: {reason}")
    
    def deactivate_degradation(self) -> None:
        """Деактивация режима graceful degradation"""
        if self.degradation_active:
            duration = (datetime.now() - self.degradation_start_time).total_seconds()
            self.degradation_active = False
            self.degradation_start_time = None
            logger.info(f"Деактивирован режим graceful degradation после {duration:.2f}с")
    
    async def execute_with_fallback(
        self, 
        service_name: str,
        primary_operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Выполнение операции с возможностью fallback
        
        Args:
            service_name: Название сервиса
            primary_operation: Основная операция
            *args, **kwargs: Аргументы для операции
            
        Returns:
            Результат выполнения (основной или fallback)
        """
        # Если degradation уже активен, сразу используем fallback
        if self.degradation_active and service_name in self.fallback_providers:
            logger.info(f"Использование fallback для {service_name} (degradation активен)")
            return await self.fallback_providers[service_name](*args, **kwargs)
        
        try:
            # Пытаемся выполнить основную операцию
            result = await primary_operation(*args, **kwargs)
            
            # Если degradation был активен, но операция прошла успешно
            if self.degradation_active:
                self.deactivate_degradation()
            
            return result
            
        except Exception as error:
            logger.error(f"Ошибка основной операции {service_name}: {error}")
            
            # Активируем degradation если есть fallback
            if service_name in self.fallback_providers:
                self.activate_degradation(f"Ошибка {service_name}: {error}")
                
                try:
                    logger.info(f"Переключение на fallback для {service_name}")
                    return await self.fallback_providers[service_name](*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Ошибка fallback для {service_name}: {fallback_error}")
                    raise YandexCloudError(
                        f"Ошибки как основного сервиса ({error}), так и fallback ({fallback_error})"
                    )
            else:
                # Нет fallback, пробрасываем ошибку
                raise
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса graceful degradation"""
        return {
            "degradation_active": self.degradation_active,
            "degradation_start_time": self.degradation_start_time.isoformat() if self.degradation_start_time else None,
            "registered_fallbacks": list(self.fallback_providers.keys()),
            "degradation_duration": (
                (datetime.now() - self.degradation_start_time).total_seconds() 
                if self.degradation_active and self.degradation_start_time else 0
            )
        }

# Глобальные экземпляры для использования в приложении
_global_error_handler: Optional[YandexCloudErrorHandler] = None
_global_degradation_manager: Optional[GracefulDegradationManager] = None

def get_error_handler() -> YandexCloudErrorHandler:
    """Получение глобального экземпляра error handler"""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = YandexCloudErrorHandler()
        logger.info("Создан глобальный YandexCloudErrorHandler")
    
    return _global_error_handler

def get_degradation_manager() -> GracefulDegradationManager:
    """Получение глобального экземпляра degradation manager"""
    global _global_degradation_manager
    
    if _global_degradation_manager is None:
        _global_degradation_manager = GracefulDegradationManager()
        logger.info("Создан глобальный GracefulDegradationManager")
    
    return _global_degradation_manager

def configure_error_handling(
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    enable_circuit_breaker: bool = True
) -> None:
    """Конфигурация глобальной обработки ошибок"""
    global _global_error_handler
    
    _global_error_handler = YandexCloudErrorHandler(
        retry_config=retry_config,
        circuit_breaker_config=circuit_breaker_config,
        enable_circuit_breaker=enable_circuit_breaker
    )
    
    logger.info("Глобальная обработка ошибок переконфигурирована")