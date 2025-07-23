import asyncio
import aiohttp
import time
import json
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse
import signal
import sys
import os
from dataclasses import dataclass
from collections import defaultdict, deque

# Конфигурация по умолчанию для стресс-теста
DEFAULT_STRESS_CONFIG = {
    "base_url": "http://localhost:8081/api",
    "concurrent_users": 100,
    "department_id": "5",
    "test_duration_minutes": 10,
    "ramp_up_minutes": 2,
    "ramp_down_minutes": 2,
    "max_wait_time_seconds": 180,
    "enable_monitoring": True,
    "monitoring_interval_seconds": 10,
    "enable_gradual_load": True,
    "max_requests_per_user_per_minute": 5,
    "enable_error_recovery": True,
    "enable_queue_monitoring": True
}

# Вопросы для стресс-теста
STRESS_QUESTIONS = [
    "Что такое машинное обучение и как оно работает?",
    "Объясните принципы работы нейронных сетей и их архитектуру",
    "Какие есть типы алгоритмов машинного обучения и их применение?",
    "Что такое глубокое обучение и чем оно отличается от обычного ML?",
    "Расскажите про обработку естественного языка и современные подходы",
    "Что такое компьютерное зрение и его основные задачи?",
    "Объясните разницу между ИИ и машинным обучением",
    "Что такое reinforcement learning и где оно применяется?",
    "Расскажите про этику в ИИ и основные проблемы",
    "Какие есть применения ИИ в медицине и их эффективность?",
    "Как работает алгоритм градиентного спуска и его варианты?",
    "Объясните концепцию overfitting и методы борьбы с ним",
    "Что такое cross-validation и зачем оно нужно?",
    "Как работает алгоритм k-means и его ограничения?",
    "Объясните принцип работы SVM и его преимущества",
    "Что такое feature engineering и его важность?",
    "Как работает алгоритм Random Forest и его особенности?",
    "Объясните концепцию bias-variance tradeoff",
    "Что такое regularization и его виды?",
    "Как работает алгоритм XGBoost и его преимущества?"
]

@dataclass
class TestMetrics:
    """Метрики для мониторинга теста"""
    timestamp: float
    active_users: int
    requests_per_second: float
    avg_response_time: float
    success_rate: float
    error_count: int
    queue_size: int
    processing_count: int
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class StressTestChat:
    def __init__(self, config: Dict[str, Any]):
        self.config = {**DEFAULT_STRESS_CONFIG, **config}
        self.results = []
        self.errors = []
        self.metrics_history = deque(maxlen=1000)
        self.active_users = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.end_time = None
        self.should_stop = False
        self.user_sessions = {}  # user_id -> session_data
        self.request_timestamps = deque(maxlen=10000)
        
    def _calculate_current_load(self) -> int:
        """Вычисляет текущую нагрузку на основе времени"""
        if not self.start_time:
            return 0
            
        elapsed = time.time() - self.start_time
        total_duration = self.config["test_duration_minutes"] * 60
        
        if not self.config["enable_gradual_load"]:
            return self.config["concurrent_users"]
        
        # Ramp up phase
        ramp_up_time = self.config["ramp_up_minutes"] * 60
        if elapsed < ramp_up_time:
            return int(self.config["concurrent_users"] * (elapsed / ramp_up_time))
        
        # Steady state
        steady_state_end = total_duration - (self.config["ramp_down_minutes"] * 60)
        if elapsed < steady_state_end:
            return self.config["concurrent_users"]
        
        # Ramp down phase
        ramp_down_elapsed = elapsed - steady_state_end
        ramp_down_time = self.config["ramp_down_minutes"] * 60
        return int(self.config["concurrent_users"] * (1 - ramp_down_elapsed / ramp_down_time))
    
    def _can_user_send_request(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь отправить новый запрос"""
        now = time.time()
        one_minute_ago = now - 60
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"request_times": []}
        
        # Удаляем старые запросы
        self.user_sessions[user_id]["request_times"] = [
            req_time for req_time in self.user_sessions[user_id]["request_times"]
            if req_time > one_minute_ago
        ]
        
        # Проверяем лимит
        return len(self.user_sessions[user_id]["request_times"]) < self.config["max_requests_per_user_per_minute"]
    
    def _record_user_request(self, user_id: int):
        """Записывает запрос пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"request_times": []}
        
        self.user_sessions[user_id]["request_times"].append(time.time())
    
    async def get_queue_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Получает статус очереди"""
        try:
            async with session.get(
                f"{self.config['base_url']}/llm/queue/status/{self.config['department_id']}",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def send_query(self, session: aiohttp.ClientSession, user_id: int) -> Dict[str, Any]:
        """Отправляет запрос от пользователя"""
        if not self._can_user_send_request(user_id):
            return {
                "user_id": user_id,
                "status": "rate_limited",
                "error": "User rate limit exceeded"
            }
        
        question = random.choice(STRESS_QUESTIONS)
        start_time = time.time()
        
        try:
            self._record_user_request(user_id)
            self.request_timestamps.append(start_time)
            
            async with session.post(
                f"{self.config['base_url']}/llm/query",
                json={
                    "question": question,
                    "department_id": self.config["department_id"]
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    task_id = data.get("task_id")
                    
                    return {
                        "user_id": user_id,
                        "task_id": task_id,
                        "question": question,
                        "query_time": time.time() - start_time,
                        "status": "sent"
                    }
                else:
                    error_text = await response.text()
                    return {
                        "user_id": user_id,
                        "error": f"HTTP {response.status}: {error_text}",
                        "query_time": time.time() - start_time,
                        "status": "failed"
                    }
                    
        except Exception as e:
            return {
                "user_id": user_id,
                "error": str(e),
                "query_time": time.time() - start_time,
                "status": "failed"
            }

    async def get_result(self, session: aiohttp.ClientSession, task_id: str, user_id: int) -> Dict[str, Any]:
        """Получает результат запроса"""
        max_attempts = self.config["max_wait_time_seconds"] // 3
        
        for attempt in range(max_attempts):
            try:
                async with session.get(
                    f"{self.config['base_url']}/llm/query/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data["status"] == "completed":
                            return {
                                "user_id": user_id,
                                "task_id": task_id,
                                "status": "completed",
                                "answer_length": len(data.get("answer", "")),
                                "chunks_count": len(data.get("chunks", [])),
                                "attempt": attempt + 1
                            }
                        elif data["status"] == "failed":
                            return {
                                "user_id": user_id,
                                "task_id": task_id,
                                "status": "failed",
                                "error": data.get("error", "Unknown error"),
                                "attempt": attempt + 1
                            }
                        
                await asyncio.sleep(3)
                
            except Exception as e:
                await asyncio.sleep(3)
                
        return {
            "user_id": user_id,
            "task_id": task_id,
            "status": "timeout",
            "error": f"Timeout after {max_attempts} attempts",
            "attempt": max_attempts
        }

    async def simulate_user_workload(self, session: aiohttp.ClientSession, user_id: int):
        """Симулирует нагрузку от одного пользователя"""
        while not self.should_stop:
            try:
                # Отправляем запрос
                query_result = await self.send_query(session, user_id)
                
                if query_result["status"] == "rate_limited":
                    await asyncio.sleep(10)  # Ждем перед следующей попыткой
                    continue
                
                if query_result["status"] == "failed":
                    self.failed_requests += 1
                    self.errors.append(query_result)
                    await asyncio.sleep(random.uniform(5, 15))
                    continue
                
                task_id = query_result["task_id"]
                
                # Получаем результат
                result = await self.get_result(session, task_id, user_id)
                
                # Объединяем результаты
                final_result = {**query_result, **result}
                final_result["total_time"] = query_result["query_time"] + (result.get("attempt", 0) * 3)
                
                if result["status"] == "completed":
                    self.successful_requests += 1
                    self.results.append(final_result)
                else:
                    self.failed_requests += 1
                    self.errors.append(final_result)
                
                self.total_requests += 1
                
                # Пауза между запросами
                await asyncio.sleep(random.uniform(10, 30))
                
            except Exception as e:
                print(f"Ошибка в пользователе {user_id}: {e}")
                await asyncio.sleep(5)

    async def monitor_system(self, session: aiohttp.ClientSession):
        """Мониторинг системы во время теста"""
        while not self.should_stop:
            try:
                # Получаем статус очереди
                queue_status = await self.get_queue_status(session)
                
                # Вычисляем метрики
                now = time.time()
                one_minute_ago = now - 60
                
                # Подсчитываем запросы за последнюю минуту
                recent_requests = sum(1 for ts in self.request_timestamps if ts > one_minute_ago)
                requests_per_second = recent_requests / 60 if recent_requests > 0 else 0
                
                # Вычисляем среднее время ответа
                recent_results = [r for r in self.results if r.get("total_time", 0) > 0]
                avg_response_time = statistics.mean([r["total_time"] for r in recent_results[-100:]]) if recent_results else 0
                
                # Вычисляем процент успешных запросов
                total_recent = len([r for r in self.results if r.get("timestamp", 0) > one_minute_ago])
                success_rate = (total_recent / (total_recent + len([e for e in self.errors if e.get("timestamp", 0) > one_minute_ago]))) * 100 if total_recent > 0 else 0
                
                # Создаем метрики
                metrics = TestMetrics(
                    timestamp=now,
                    active_users=self._calculate_current_load(),
                    requests_per_second=requests_per_second,
                    avg_response_time=avg_response_time,
                    success_rate=success_rate,
                    error_count=len(self.errors),
                    queue_size=queue_status.get("pending_count", 0),
                    processing_count=queue_status.get("processing_count", 0)
                )
                
                self.metrics_history.append(metrics)
                
                # Выводим текущие метрики
                if self.config["enable_monitoring"]:
                    print(f"📊 [{datetime.fromtimestamp(now).strftime('%H:%M:%S')}] "
                          f"Пользователей: {metrics.active_users}, "
                          f"RPS: {metrics.requests_per_second:.2f}, "
                          f"Время ответа: {metrics.avg_response_time:.2f}с, "
                          f"Успешность: {metrics.success_rate:.1f}%, "
                          f"Очередь: {metrics.queue_size}, "
                          f"Обработка: {metrics.processing_count}")
                
                await asyncio.sleep(self.config["monitoring_interval_seconds"])
                
            except Exception as e:
                print(f"Ошибка мониторинга: {e}")
                await asyncio.sleep(5)

    async def run_stress_test(self):
        """Запускает стресс-тест"""
        print(f"🔥 Запуск стресс-теста чата RAG")
        print(f"👥 Максимум пользователей: {self.config['concurrent_users']}")
        print(f"⏱️  Длительность теста: {self.config['test_duration_minutes']} минут")
        print(f"📈 Ramp up: {self.config['ramp_up_minutes']} минут")
        print(f"📉 Ramp down: {self.config['ramp_down_minutes']} минут")
        print(f"🎯 URL: {self.config['base_url']}")
        print(f"🏢 Отдел: {self.config['department_id']}")
        print(f"📊 Мониторинг: {'включен' if self.config['enable_monitoring'] else 'отключен'}")
        print("-" * 60)
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Запускаем мониторинг
            monitor_task = None
            if self.config["enable_monitoring"]:
                monitor_task = asyncio.create_task(self.monitor_system(session))
            
            # Запускаем пользователей
            user_tasks = []
            for user_id in range(1, self.config["concurrent_users"] + 1):
                task = asyncio.create_task(self.simulate_user_workload(session, user_id))
                user_tasks.append(task)
            
            # Ждем завершения теста
            try:
                await asyncio.sleep(self.config["test_duration_minutes"] * 60)
            except KeyboardInterrupt:
                print("\n⚠️ Получен сигнал остановки...")
            
            # Останавливаем тест
            self.should_stop = True
            
            # Ждем завершения всех задач
            if monitor_task:
                monitor_task.cancel()
            
            for task in user_tasks:
                task.cancel()
            
            await asyncio.gather(*user_tasks, return_exceptions=True)
        
        self.end_time = time.time()
        
        # Анализируем результаты
        self.analyze_stress_results()
        
        return self.results

    def analyze_stress_results(self):
        """Анализирует результаты стресс-теста"""
        print("\n" + "="*80)
        print("🔥 РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТА ЧАТА RAG")
        print("="*80)
        
        total_time = self.end_time - self.start_time
        successful = len(self.results)
        failed = len(self.errors)
        total_requests = successful + failed
        
        print(f"👥 Максимум пользователей: {self.config['concurrent_users']}")
        print(f"📨 Всего запросов: {total_requests}")
        print(f"✅ Успешных запросов: {successful} ({successful/total_requests*100:.1f}%)")
        print(f"❌ Неудачных запросов: {failed} ({failed/total_requests*100:.1f}%)")
        print(f"⏱️  Общее время теста: {total_time:.2f} секунд")
        
        if self.results:
            times = [r["total_time"] for r in self.results]
            query_times = [r["query_time"] for r in self.results]
            
            print(f"\n⏱️  ВРЕМЯ ОТВЕТА:")
            print(f"   Среднее: {statistics.mean(times):.2f}с")
            print(f"   Медиана: {statistics.median(times):.2f}с")
            print(f"   Минимальное: {min(times):.2f}с")
            print(f"   Максимальное: {max(times):.2f}с")
            print(f"   95-й перцентиль: {statistics.quantiles(times, n=20)[18]:.2f}с")
            print(f"   99-й перцентиль: {statistics.quantiles(times, n=100)[98]:.2f}с")
            
            print(f"\n📤 ВРЕМЯ ОТПРАВКИ ЗАПРОСА:")
            print(f"   Среднее: {statistics.mean(query_times):.3f}с")
            print(f"   Максимальное: {max(query_times):.3f}с")
            
            # Пропускная способность
            rps = successful / total_time
            print(f"\n🚀 ПРОИЗВОДИТЕЛЬНОСТЬ:")
            print(f"   Запросов в секунду: {rps:.2f}")
            print(f"   Среднее время на запрос: {total_time/total_requests:.2f}с")
        
        # Анализ метрик во времени
        if self.metrics_history:
            print(f"\n📈 МЕТРИКИ ВО ВРЕМЕНИ:")
            max_rps = max(m.requests_per_second for m in self.metrics_history)
            max_response_time = max(m.avg_response_time for m in self.metrics_history if m.avg_response_time > 0)
            min_success_rate = min(m.success_rate for m in self.metrics_history if m.success_rate > 0)
            
            print(f"   Максимум RPS: {max_rps:.2f}")
            print(f"   Максимальное время ответа: {max_response_time:.2f}с")
            print(f"   Минимальная успешность: {min_success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ ОШИБКИ:")
            error_types = {}
            for error in self.errors:
                error_type = error.get("error", "Unknown")[:50]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count}")
        
        print("="*80)

async def main():
    parser = argparse.ArgumentParser(description="Стресс-тест чата RAG")
    parser.add_argument("--users", type=int, default=100, help="Количество одновременных пользователей")
    parser.add_argument("--duration", type=int, default=10, help="Длительность теста в минутах")
    parser.add_argument("--ramp-up", type=int, default=2, help="Время нарастания нагрузки в минутах")
    parser.add_argument("--ramp-down", type=int, default=2, help="Время снижения нагрузки в минутах")
    parser.add_argument("--url", type=str, default="http://localhost:8081/api", help="URL API")
    parser.add_argument("--department", type=str, default="5", help="ID отдела")
    parser.add_argument("--no-monitoring", action="store_true", help="Отключить мониторинг")
    parser.add_argument("--no-gradual-load", action="store_true", help="Отключить постепенное нарастание нагрузки")
    
    args = parser.parse_args()
    
    config = {
        "concurrent_users": args.users,
        "test_duration_minutes": args.duration,
        "ramp_up_minutes": args.ramp_up,
        "ramp_down_minutes": args.ramp_down,
        "base_url": args.url,
        "department_id": args.department,
        "enable_monitoring": not args.no_monitoring,
        "enable_gradual_load": not args.no_gradual_load
    }
    
    tester = StressTestChat(config)
    await tester.run_stress_test()

if __name__ == "__main__":
    asyncio.run(main()) 