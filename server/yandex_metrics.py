"""
Система мониторинга и метрик для Yandex Cloud API
Отслеживает использование API, производительность и ошибки
"""

import time
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class APICallMetric:
    """Метрика одного API вызова"""
    timestamp: datetime
    endpoint: str
    method: str
    duration: float
    status_code: Optional[int]
    success: bool
    tokens_used: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    model: Optional[str] = None
    request_size: int = 0
    response_size: int = 0

@dataclass
class AggregatedMetrics:
    """Агрегированные метрики за период"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    success_rate: float = 0.0
    requests_per_minute: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    models_usage: Dict[str, int] = field(default_factory=dict)
    endpoints_usage: Dict[str, int] = field(default_factory=dict)

class YandexCloudMetrics:
    """
    Класс для отслеживания метрик использования Yandex Cloud API
    """
    
    def __init__(self, max_history_size: int = 10000, metrics_file: str = None):
        """
        Инициализация системы метрик
        
        Args:
            max_history_size: Максимальное количество метрик в памяти
            metrics_file: Путь к файлу для сохранения метрик
        """
        self.max_history_size = max_history_size
        self.metrics_file = metrics_file or "/app/files/yandex_metrics.json"
        
        # История API вызовов
        self.api_calls: deque[APICallMetric] = deque(maxlen=max_history_size)
        
        # Агрегированные метрики
        self.hourly_metrics: Dict[str, AggregatedMetrics] = {}
        self.daily_metrics: Dict[str, AggregatedMetrics] = {}
        
        # Счетчики в реальном времени
        self.current_metrics = AggregatedMetrics()
        
        # Блокировка для thread-safety
        self._lock = threading.RLock()
        
        # Время последнего сохранения
        self.last_save_time = datetime.now()
        
        # Загружаем существующие метрики
        self._load_metrics()
        
        logger.info(f"YandexCloudMetrics инициализирован, файл метрик: {self.metrics_file}")
    
    def record_api_call(
        self,
        endpoint: str,
        method: str,
        duration: float,
        success: bool,
        status_code: Optional[int] = None,
        tokens_used: int = 0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        model: Optional[str] = None,
        request_size: int = 0,
        response_size: int = 0
    ) -> None:
        """
        Записывает метрику API вызова
        
        Args:
            endpoint: API эндпоинт
            method: HTTP метод
            duration: Время выполнения в секундах
            success: Успешность вызова
            status_code: HTTP статус код
            tokens_used: Количество использованных токенов
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            model: Используемая модель
            request_size: Размер запроса в байтах
            response_size: Размер ответа в байтах
        """
        with self._lock:
            # Создаем метрику
            metric = APICallMetric(
                timestamp=datetime.now(),
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=status_code,
                success=success,
                tokens_used=tokens_used,
                error_type=error_type,
                error_message=error_message,
                model=model,
                request_size=request_size,
                response_size=response_size
            )
            
            # Добавляем в историю
            self.api_calls.append(metric)
            
            # Обновляем текущие метрики
            self._update_current_metrics(metric)
            
            # Обновляем агрегированные метрики
            self._update_aggregated_metrics(metric)
            
            # Периодически сохраняем метрики
            if datetime.now() - self.last_save_time > timedelta(minutes=5):
                self._save_metrics()
                self.last_save_time = datetime.now()
    
    def _update_current_metrics(self, metric: APICallMetric) -> None:
        """Обновляет текущие метрики"""
        self.current_metrics.total_requests += 1
        self.current_metrics.total_duration += metric.duration
        self.current_metrics.total_tokens += metric.tokens_used
        
        if metric.success:
            self.current_metrics.successful_requests += 1
        else:
            self.current_metrics.failed_requests += 1
            if metric.error_type:
                self.current_metrics.errors_by_type[metric.error_type] = \
                    self.current_metrics.errors_by_type.get(metric.error_type, 0) + 1
        
        # Обновляем статистику времени выполнения
        if metric.duration < self.current_metrics.min_duration:
            self.current_metrics.min_duration = metric.duration
        if metric.duration > self.current_metrics.max_duration:
            self.current_metrics.max_duration = metric.duration
        
        # Пересчитываем среднее время
        if self.current_metrics.total_requests > 0:
            self.current_metrics.average_duration = \
                self.current_metrics.total_duration / self.current_metrics.total_requests
            self.current_metrics.success_rate = \
                self.current_metrics.successful_requests / self.current_metrics.total_requests
        
        # Обновляем статистику по моделям и эндпоинтам
        if metric.model:
            self.current_metrics.models_usage[metric.model] = \
                self.current_metrics.models_usage.get(metric.model, 0) + 1
        
        self.current_metrics.endpoints_usage[metric.endpoint] = \
            self.current_metrics.endpoints_usage.get(metric.endpoint, 0) + 1
    
    def _update_aggregated_metrics(self, metric: APICallMetric) -> None:
        """Обновляет агрегированные метрики по часам и дням"""
        timestamp = metric.timestamp
        
        # Ключи для группировки
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        day_key = timestamp.strftime("%Y-%m-%d")
        
        # Обновляем часовые метрики
        if hour_key not in self.hourly_metrics:
            self.hourly_metrics[hour_key] = AggregatedMetrics()
        self._update_aggregated_metric(self.hourly_metrics[hour_key], metric)
        
        # Обновляем дневные метрики
        if day_key not in self.daily_metrics:
            self.daily_metrics[day_key] = AggregatedMetrics()
        self._update_aggregated_metric(self.daily_metrics[day_key], metric)
        
        # Очищаем старые метрики (старше 7 дней)
        cutoff_date = datetime.now() - timedelta(days=7)
        cutoff_hour = cutoff_date.strftime("%Y-%m-%d %H:00")
        cutoff_day = cutoff_date.strftime("%Y-%m-%d")
        
        # Удаляем старые часовые метрики
        keys_to_remove = [k for k in self.hourly_metrics.keys() if k < cutoff_hour]
        for key in keys_to_remove:
            del self.hourly_metrics[key]
        
        # Удаляем старые дневные метрики (старше 30 дней)
        cutoff_day_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        keys_to_remove = [k for k in self.daily_metrics.keys() if k < cutoff_day_30]
        for key in keys_to_remove:
            del self.daily_metrics[key]
    
    def _update_aggregated_metric(self, agg_metric: AggregatedMetrics, metric: APICallMetric) -> None:
        """Обновляет одну агрегированную метрику"""
        agg_metric.total_requests += 1
        agg_metric.total_duration += metric.duration
        agg_metric.total_tokens += metric.tokens_used
        
        if metric.success:
            agg_metric.successful_requests += 1
        else:
            agg_metric.failed_requests += 1
            if metric.error_type:
                agg_metric.errors_by_type[metric.error_type] = \
                    agg_metric.errors_by_type.get(metric.error_type, 0) + 1
        
        # Обновляем статистику времени
        if metric.duration < agg_metric.min_duration:
            agg_metric.min_duration = metric.duration
        if metric.duration > agg_metric.max_duration:
            agg_metric.max_duration = metric.duration
        
        # Пересчитываем производные метрики
        if agg_metric.total_requests > 0:
            agg_metric.average_duration = agg_metric.total_duration / agg_metric.total_requests
            agg_metric.success_rate = agg_metric.successful_requests / agg_metric.total_requests
        
        # Обновляем статистику использования
        if metric.model:
            agg_metric.models_usage[metric.model] = \
                agg_metric.models_usage.get(metric.model, 0) + 1
        
        agg_metric.endpoints_usage[metric.endpoint] = \
            agg_metric.endpoints_usage.get(metric.endpoint, 0) + 1
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Возвращает текущие метрики"""
        with self._lock:
            metrics = asdict(self.current_metrics)
            
            # Добавляем дополнительную информацию
            metrics['uptime_hours'] = self._get_uptime_hours()
            metrics['last_api_call'] = self._get_last_api_call_time()
            metrics['api_calls_history_size'] = len(self.api_calls)
            
            return metrics
    
    def get_hourly_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Возвращает часовые метрики за указанное количество часов
        
        Args:
            hours: Количество часов для получения метрик
            
        Returns:
            Словарь с часовыми метриками
        """
        with self._lock:
            now = datetime.now()
            result = {}
            
            for i in range(hours):
                hour_time = now - timedelta(hours=i)
                hour_key = hour_time.strftime("%Y-%m-%d %H:00")
                
                if hour_key in self.hourly_metrics:
                    result[hour_key] = asdict(self.hourly_metrics[hour_key])
                else:
                    result[hour_key] = asdict(AggregatedMetrics())
            
            return result
    
    def get_daily_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Возвращает дневные метрики за указанное количество дней
        
        Args:
            days: Количество дней для получения метрик
            
        Returns:
            Словарь с дневными метриками
        """
        with self._lock:
            now = datetime.now()
            result = {}
            
            for i in range(days):
                day_time = now - timedelta(days=i)
                day_key = day_time.strftime("%Y-%m-%d")
                
                if day_key in self.daily_metrics:
                    result[day_key] = asdict(self.daily_metrics[day_key])
                else:
                    result[day_key] = asdict(AggregatedMetrics())
            
            return result
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Возвращает анализ ошибок"""
        with self._lock:
            recent_calls = [call for call in self.api_calls 
                          if call.timestamp > datetime.now() - timedelta(hours=24)]
            
            error_calls = [call for call in recent_calls if not call.success]
            
            error_analysis = {
                'total_errors_24h': len(error_calls),
                'error_rate_24h': len(error_calls) / len(recent_calls) if recent_calls else 0,
                'errors_by_type': defaultdict(int),
                'errors_by_endpoint': defaultdict(int),
                'errors_by_hour': defaultdict(int),
                'recent_errors': []
            }
            
            for error_call in error_calls:
                if error_call.error_type:
                    error_analysis['errors_by_type'][error_call.error_type] += 1
                
                error_analysis['errors_by_endpoint'][error_call.endpoint] += 1
                
                hour_key = error_call.timestamp.strftime("%Y-%m-%d %H:00")
                error_analysis['errors_by_hour'][hour_key] += 1
                
                # Добавляем последние 10 ошибок
                if len(error_analysis['recent_errors']) < 10:
                    error_analysis['recent_errors'].append({
                        'timestamp': error_call.timestamp.isoformat(),
                        'endpoint': error_call.endpoint,
                        'error_type': error_call.error_type,
                        'error_message': error_call.error_message,
                        'status_code': error_call.status_code
                    })
            
            # Конвертируем defaultdict в обычные словари
            error_analysis['errors_by_type'] = dict(error_analysis['errors_by_type'])
            error_analysis['errors_by_endpoint'] = dict(error_analysis['errors_by_endpoint'])
            error_analysis['errors_by_hour'] = dict(error_analysis['errors_by_hour'])
            
            return error_analysis
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Возвращает анализ производительности"""
        with self._lock:
            recent_calls = [call for call in self.api_calls 
                          if call.timestamp > datetime.now() - timedelta(hours=24)]
            
            if not recent_calls:
                return {'message': 'Нет данных за последние 24 часа'}
            
            durations = [call.duration for call in recent_calls]
            successful_calls = [call for call in recent_calls if call.success]
            
            # Вычисляем перцентили
            durations_sorted = sorted(durations)
            n = len(durations_sorted)
            
            performance_analysis = {
                'total_calls_24h': len(recent_calls),
                'successful_calls_24h': len(successful_calls),
                'average_duration': sum(durations) / len(durations),
                'median_duration': durations_sorted[n // 2] if n > 0 else 0,
                'p95_duration': durations_sorted[int(n * 0.95)] if n > 0 else 0,
                'p99_duration': durations_sorted[int(n * 0.99)] if n > 0 else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'slowest_endpoints': self._get_slowest_endpoints(recent_calls),
                'fastest_endpoints': self._get_fastest_endpoints(recent_calls),
                'tokens_per_hour': self._get_tokens_per_hour(recent_calls)
            }
            
            return performance_analysis
    
    def _get_slowest_endpoints(self, calls: List[APICallMetric], limit: int = 5) -> List[Dict[str, Any]]:
        """Возвращает самые медленные эндпоинты"""
        endpoint_durations = defaultdict(list)
        
        for call in calls:
            endpoint_durations[call.endpoint].append(call.duration)
        
        endpoint_avg_durations = []
        for endpoint, durations in endpoint_durations.items():
            avg_duration = sum(durations) / len(durations)
            endpoint_avg_durations.append({
                'endpoint': endpoint,
                'average_duration': avg_duration,
                'call_count': len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations)
            })
        
        return sorted(endpoint_avg_durations, key=lambda x: x['average_duration'], reverse=True)[:limit]
    
    def _get_fastest_endpoints(self, calls: List[APICallMetric], limit: int = 5) -> List[Dict[str, Any]]:
        """Возвращает самые быстрые эндпоинты"""
        endpoint_durations = defaultdict(list)
        
        for call in calls:
            endpoint_durations[call.endpoint].append(call.duration)
        
        endpoint_avg_durations = []
        for endpoint, durations in endpoint_durations.items():
            avg_duration = sum(durations) / len(durations)
            endpoint_avg_durations.append({
                'endpoint': endpoint,
                'average_duration': avg_duration,
                'call_count': len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations)
            })
        
        return sorted(endpoint_avg_durations, key=lambda x: x['average_duration'])[:limit]
    
    def _get_tokens_per_hour(self, calls: List[APICallMetric]) -> Dict[str, int]:
        """Возвращает использование токенов по часам"""
        tokens_per_hour = defaultdict(int)
        
        for call in calls:
            hour_key = call.timestamp.strftime("%Y-%m-%d %H:00")
            tokens_per_hour[hour_key] += call.tokens_used
        
        return dict(tokens_per_hour)
    
    def _get_uptime_hours(self) -> float:
        """Возвращает время работы в часах"""
        if not self.api_calls:
            return 0.0
        
        first_call = min(self.api_calls, key=lambda x: x.timestamp)
        return (datetime.now() - first_call.timestamp).total_seconds() / 3600
    
    def _get_last_api_call_time(self) -> Optional[str]:
        """Возвращает время последнего API вызова"""
        if not self.api_calls:
            return None
        
        last_call = max(self.api_calls, key=lambda x: x.timestamp)
        return last_call.timestamp.isoformat()
    
    def _save_metrics(self) -> None:
        """Сохраняет метрики в файл"""
        try:
            # Создаем директорию если не существует
            metrics_path = Path(self.metrics_file)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Подготавливаем данные для сохранения
            data = {
                'current_metrics': asdict(self.current_metrics),
                'hourly_metrics': {k: asdict(v) for k, v in self.hourly_metrics.items()},
                'daily_metrics': {k: asdict(v) for k, v in self.daily_metrics.items()},
                'last_save_time': datetime.now().isoformat(),
                'api_calls_count': len(self.api_calls)
            }
            
            # Сохраняем в файл
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Метрики сохранены в {self.metrics_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения метрик: {e}")
    
    def _load_metrics(self) -> None:
        """Загружает метрики из файла"""
        try:
            if not os.path.exists(self.metrics_file):
                logger.info("Файл метрик не найден, начинаем с пустых метрик")
                return
            
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем текущие метрики
            if 'current_metrics' in data:
                current_data = data['current_metrics']
                self.current_metrics = AggregatedMetrics(**current_data)
            
            # Загружаем часовые метрики
            if 'hourly_metrics' in data:
                for key, value in data['hourly_metrics'].items():
                    self.hourly_metrics[key] = AggregatedMetrics(**value)
            
            # Загружаем дневные метрики
            if 'daily_metrics' in data:
                for key, value in data['daily_metrics'].items():
                    self.daily_metrics[key] = AggregatedMetrics(**value)
            
            logger.info(f"Метрики загружены из {self.metrics_file}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки метрик: {e}")
    
    def reset_metrics(self) -> None:
        """Сбрасывает все метрики"""
        with self._lock:
            self.api_calls.clear()
            self.current_metrics = AggregatedMetrics()
            self.hourly_metrics.clear()
            self.daily_metrics.clear()
            
            # Удаляем файл метрик
            try:
                if os.path.exists(self.metrics_file):
                    os.remove(self.metrics_file)
                logger.info("Все метрики сброшены")
            except Exception as e:
                logger.error(f"Ошибка удаления файла метрик: {e}")
    
    def export_metrics(self, format: str = 'json') -> str:
        """
        Экспортирует метрики в указанном формате
        
        Args:
            format: Формат экспорта ('json', 'csv')
            
        Returns:
            Строка с экспортированными данными
        """
        with self._lock:
            if format.lower() == 'json':
                return self._export_json()
            elif format.lower() == 'csv':
                return self._export_csv()
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
    
    def _export_json(self) -> str:
        """Экспортирует метрики в JSON формате"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'current_metrics': self.get_current_metrics(),
            'hourly_metrics': self.get_hourly_metrics(24),
            'daily_metrics': self.get_daily_metrics(7),
            'error_analysis': self.get_error_analysis(),
            'performance_analysis': self.get_performance_analysis()
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_csv(self) -> str:
        """Экспортирует метрики в CSV формате"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'timestamp', 'endpoint', 'method', 'duration', 'success',
            'status_code', 'tokens_used', 'error_type', 'model'
        ])
        
        # Данные
        for call in self.api_calls:
            writer.writerow([
                call.timestamp.isoformat(),
                call.endpoint,
                call.method,
                call.duration,
                call.success,
                call.status_code,
                call.tokens_used,
                call.error_type,
                call.model
            ])
        
        return output.getvalue()

# Глобальный экземпляр метрик
_global_metrics: Optional[YandexCloudMetrics] = None
_metrics_lock = threading.Lock()

def get_metrics_instance() -> YandexCloudMetrics:
    """Получение глобального экземпляра метрик"""
    global _global_metrics
    
    if _global_metrics is None:
        with _metrics_lock:
            if _global_metrics is None:
                _global_metrics = YandexCloudMetrics()
                logger.info("Создан глобальный экземпляр YandexCloudMetrics")
    
    return _global_metrics

def record_api_call(
    endpoint: str,
    method: str,
    duration: float,
    success: bool,
    **kwargs
) -> None:
    """Удобная функция для записи API вызова"""
    metrics = get_metrics_instance()
    metrics.record_api_call(endpoint, method, duration, success, **kwargs)