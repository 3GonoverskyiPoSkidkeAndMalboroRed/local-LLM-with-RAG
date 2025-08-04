"""
Система мониторинга производительности для Yandex Cloud интеграции
Отслеживает время ответа, успешность запросов и производительность системы
"""

import time
import threading
import asyncio
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("WARNING: psutil недоступен, системные метрики будут ограничены")
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from contextlib import asynccontextmanager, contextmanager
from functools import wraps

from yandex_metrics import get_metrics_instance, YandexCloudMetrics

logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    """Снимок производительности системы"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    active_threads: int
    active_tasks: int
    api_calls_per_minute: float
    average_response_time: float
    error_rate: float

@dataclass
class AlertRule:
    """Правило для алертов"""
    name: str
    condition: Callable[[PerformanceSnapshot], bool]
    message: str
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None

class PerformanceMonitor:
    """
    Монитор производительности для отслеживания системных метрик
    и производительности Yandex Cloud API
    """
    
    def __init__(self, snapshot_interval: int = 60, max_snapshots: int = 1440):
        """
        Инициализация монитора производительности
        
        Args:
            snapshot_interval: Интервал создания снимков в секундах
            max_snapshots: Максимальное количество снимков в памяти (24 часа по умолчанию)
        """
        self.snapshot_interval = snapshot_interval
        self.max_snapshots = max_snapshots
        
        # История снимков производительности
        self.snapshots: deque[PerformanceSnapshot] = deque(maxlen=max_snapshots)
        
        # Метрики Yandex Cloud
        self.metrics: YandexCloudMetrics = get_metrics_instance()
        
        # Правила алертов
        self.alert_rules: List[AlertRule] = []
        self._setup_default_alerts()
        
        # Состояние мониторинга
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Блокировка для thread-safety
        self._lock = threading.RLock()
        
        # Счетчики для мониторинга
        self.active_api_calls = 0
        self.api_call_times: deque[float] = deque(maxlen=1000)
        
        logger.info("PerformanceMonitor инициализирован")
    
    def _setup_default_alerts(self) -> None:
        """Настройка алертов по умолчанию"""
        self.alert_rules = [
            AlertRule(
                name="high_cpu_usage",
                condition=lambda s: s.cpu_percent > 80,
                message="Высокая загрузка CPU: {cpu_percent:.1f}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_memory_usage",
                condition=lambda s: s.memory_percent > 85,
                message="Высокое использование памяти: {memory_percent:.1f}%",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_error_rate",
                condition=lambda s: s.error_rate > 0.1,  # 10% ошибок
                message="Высокий уровень ошибок API: {error_rate:.1%}",
                cooldown_minutes=10
            ),
            AlertRule(
                name="slow_response_time",
                condition=lambda s: s.average_response_time > 10.0,  # 10 секунд
                message="Медленное время ответа API: {average_response_time:.2f}с",
                cooldown_minutes=5
            ),
            AlertRule(
                name="too_many_active_tasks",
                condition=lambda s: s.active_tasks > 50,
                message="Слишком много активных задач: {active_tasks}",
                cooldown_minutes=5
            )
        ]
    
    async def start_monitoring(self) -> None:
        """Запускает мониторинг производительности"""
        if self.is_monitoring:
            logger.warning("Мониторинг уже запущен")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Мониторинг производительности запущен")
    
    async def stop_monitoring(self) -> None:
        """Останавливает мониторинг производительности"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Мониторинг производительности остановлен")
    
    async def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга"""
        try:
            while self.is_monitoring:
                # Создаем снимок производительности
                snapshot = self._create_performance_snapshot()
                
                with self._lock:
                    self.snapshots.append(snapshot)
                
                # Проверяем алерты
                self._check_alerts(snapshot)
                
                # Ждем до следующего снимка
                await asyncio.sleep(self.snapshot_interval)
                
        except asyncio.CancelledError:
            logger.info("Цикл мониторинга отменен")
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
    
    def _create_performance_snapshot(self) -> PerformanceSnapshot:
        """Создает снимок текущей производительности"""
        try:
            # Системные метрики
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_mb = memory.used / (1024 * 1024)
            else:
                # Заглушки для системных метрик
                cpu_percent = 0.0
                memory_percent = 0.0
                memory_used_mb = 0.0
            
            # Количество потоков
            active_threads = threading.active_count()
            
            # Метрики задач (примерная оценка)
            active_tasks = self.active_api_calls
            
            # Метрики API
            current_metrics = self.metrics.get_current_metrics()
            
            # Вычисляем API calls per minute за последние 5 минут
            recent_time = datetime.now() - timedelta(minutes=5)
            recent_snapshots = [s for s in self.snapshots if s.timestamp > recent_time]
            
            if recent_snapshots:
                api_calls_per_minute = len(recent_snapshots) * (60 / self.snapshot_interval)
            else:
                api_calls_per_minute = 0.0
            
            # Среднее время ответа
            average_response_time = current_metrics.get('average_duration', 0.0)
            
            # Уровень ошибок
            total_requests = current_metrics.get('total_requests', 0)
            failed_requests = current_metrics.get('failed_requests', 0)
            error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
            
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                active_threads=active_threads,
                active_tasks=active_tasks,
                api_calls_per_minute=api_calls_per_minute,
                average_response_time=average_response_time,
                error_rate=error_rate
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания снимка производительности: {e}")
            # Возвращаем пустой снимок в случае ошибки
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                active_threads=0,
                active_tasks=0,
                api_calls_per_minute=0.0,
                average_response_time=0.0,
                error_rate=0.0
            )
    
    def _check_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """Проверяет правила алертов"""
        for rule in self.alert_rules:
            try:
                # Проверяем cooldown
                if (rule.last_triggered and 
                    datetime.now() - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)):
                    continue
                
                # Проверяем условие
                if rule.condition(snapshot):
                    # Форматируем сообщение
                    message = rule.message.format(**snapshot.__dict__)
                    
                    # Логируем алерт
                    logger.warning(f"ALERT [{rule.name}]: {message}")
                    
                    # Обновляем время последнего срабатывания
                    rule.last_triggered = datetime.now()
                    
            except Exception as e:
                logger.error(f"Ошибка проверки алерта {rule.name}: {e}")
    
    @asynccontextmanager
    async def monitor_api_call(self, endpoint: str, method: str = "POST"):
        """
        Контекстный менеджер для мониторинга API вызова
        
        Args:
            endpoint: API эндпоинт
            method: HTTP метод
        """
        start_time = time.time()
        self.active_api_calls += 1
        
        try:
            yield
            # Успешный вызов
            duration = time.time() - start_time
            self.api_call_times.append(duration)
            
            # Записываем метрику
            self.metrics.record_api_call(
                endpoint=endpoint,
                method=method,
                duration=duration,
                success=True
            )
            
        except Exception as e:
            # Неуспешный вызов
            duration = time.time() - start_time
            self.api_call_times.append(duration)
            
            # Записываем метрику с ошибкой
            self.metrics.record_api_call(
                endpoint=endpoint,
                method=method,
                duration=duration,
                success=False,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            raise
        finally:
            self.active_api_calls -= 1
    
    @contextmanager
    def monitor_sync_api_call(self, endpoint: str, method: str = "POST"):
        """
        Синхронный контекстный менеджер для мониторинга API вызова
        
        Args:
            endpoint: API эндпоинт
            method: HTTP метод
        """
        start_time = time.time()
        self.active_api_calls += 1
        
        try:
            yield
            # Успешный вызов
            duration = time.time() - start_time
            self.api_call_times.append(duration)
            
            # Записываем метрику
            self.metrics.record_api_call(
                endpoint=endpoint,
                method=method,
                duration=duration,
                success=True
            )
            
        except Exception as e:
            # Неуспешный вызов
            duration = time.time() - start_time
            self.api_call_times.append(duration)
            
            # Записываем метрику с ошибкой
            self.metrics.record_api_call(
                endpoint=endpoint,
                method=method,
                duration=duration,
                success=False,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            raise
        finally:
            self.active_api_calls -= 1
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Возвращает текущие показатели производительности"""
        with self._lock:
            if not self.snapshots:
                return {"message": "Нет данных о производительности"}
            
            latest_snapshot = self.snapshots[-1]
            
            return {
                "timestamp": latest_snapshot.timestamp.isoformat(),
                "system": {
                    "cpu_percent": latest_snapshot.cpu_percent,
                    "memory_percent": latest_snapshot.memory_percent,
                    "memory_used_mb": latest_snapshot.memory_used_mb,
                    "active_threads": latest_snapshot.active_threads
                },
                "api": {
                    "active_tasks": latest_snapshot.active_tasks,
                    "api_calls_per_minute": latest_snapshot.api_calls_per_minute,
                    "average_response_time": latest_snapshot.average_response_time,
                    "error_rate": latest_snapshot.error_rate
                },
                "monitoring": {
                    "is_active": self.is_monitoring,
                    "snapshots_count": len(self.snapshots),
                    "uptime_minutes": self._get_uptime_minutes()
                }
            }
    
    def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Возвращает историю производительности за указанное количество часов
        
        Args:
            hours: Количество часов для получения истории
            
        Returns:
            Список снимков производительности
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_snapshots = [s for s in self.snapshots if s.timestamp > cutoff_time]
            
            return [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "cpu_percent": snapshot.cpu_percent,
                    "memory_percent": snapshot.memory_percent,
                    "memory_used_mb": snapshot.memory_used_mb,
                    "active_threads": snapshot.active_threads,
                    "active_tasks": snapshot.active_tasks,
                    "api_calls_per_minute": snapshot.api_calls_per_minute,
                    "average_response_time": snapshot.average_response_time,
                    "error_rate": snapshot.error_rate
                }
                for snapshot in recent_snapshots
            ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Возвращает сводку производительности"""
        with self._lock:
            if not self.snapshots:
                return {"message": "Нет данных для анализа"}
            
            # Анализируем последние 24 часа
            recent_time = datetime.now() - timedelta(hours=24)
            recent_snapshots = [s for s in self.snapshots if s.timestamp > recent_time]
            
            if not recent_snapshots:
                return {"message": "Нет данных за последние 24 часа"}
            
            # Вычисляем статистику
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            memory_values = [s.memory_percent for s in recent_snapshots]
            response_times = [s.average_response_time for s in recent_snapshots if s.average_response_time > 0]
            error_rates = [s.error_rate for s in recent_snapshots]
            
            return {
                "period": "24 hours",
                "snapshots_analyzed": len(recent_snapshots),
                "cpu": {
                    "average": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "average": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "api_response_time": {
                    "average": sum(response_times) / len(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "min": min(response_times) if response_times else 0
                },
                "error_rate": {
                    "average": sum(error_rates) / len(error_rates),
                    "max": max(error_rates),
                    "min": min(error_rates)
                },
                "alerts_triggered": self._count_recent_alerts()
            }
    
    def _get_uptime_minutes(self) -> float:
        """Возвращает время работы мониторинга в минутах"""
        if not self.snapshots:
            return 0.0
        
        first_snapshot = self.snapshots[0]
        return (datetime.now() - first_snapshot.timestamp).total_seconds() / 60
    
    def _count_recent_alerts(self) -> int:
        """Подсчитывает количество алертов за последние 24 часа"""
        recent_time = datetime.now() - timedelta(hours=24)
        count = 0
        
        for rule in self.alert_rules:
            if rule.last_triggered and rule.last_triggered > recent_time:
                count += 1
        
        return count
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Добавляет новое правило алерта"""
        self.alert_rules.append(rule)
        logger.info(f"Добавлено правило алерта: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """
        Удаляет правило алерта по имени
        
        Args:
            rule_name: Имя правила для удаления
            
        Returns:
            True если правило было удалено, False если не найдено
        """
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                logger.info(f"Удалено правило алерта: {rule_name}")
                return True
        
        return False
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Возвращает статус всех алертов"""
        return {
            "total_rules": len(self.alert_rules),
            "rules": [
                {
                    "name": rule.name,
                    "message": rule.message,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                    "is_in_cooldown": (
                        rule.last_triggered and 
                        datetime.now() - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)
                    ) if rule.last_triggered else False
                }
                for rule in self.alert_rules
            ]
        }

# Декораторы для мониторинга
def monitor_async_performance(endpoint: str, method: str = "POST"):
    """
    Декоратор для мониторинга асинхронных функций
    
    Args:
        endpoint: API эндпоинт
        method: HTTP метод
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            async with monitor.monitor_api_call(endpoint, method):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_sync_performance(endpoint: str, method: str = "POST"):
    """
    Декоратор для мониторинга синхронных функций
    
    Args:
        endpoint: API эндпоинт
        method: HTTP метод
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.monitor_sync_api_call(endpoint, method):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Глобальный экземпляр монитора
_global_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()

def get_performance_monitor() -> PerformanceMonitor:
    """Получение глобального экземпляра монитора производительности"""
    global _global_monitor
    
    if _global_monitor is None:
        with _monitor_lock:
            if _global_monitor is None:
                _global_monitor = PerformanceMonitor()
                logger.info("Создан глобальный экземпляр PerformanceMonitor")
    
    return _global_monitor