import asyncio
import aiohttp
import time
import json
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse
import sys
import os

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    "base_url": "http://localhost:8081/api",
    "concurrent_users": 50,
    "department_id": "5",
    "test_duration_minutes": 5,
    "request_interval_seconds": 2,
    "max_wait_time_seconds": 120,
    "enable_chat_history": True,
    "enable_feedback": True,
    "enable_rate_limiting": True,
    "rate_limit_requests_per_minute": 30
}

# Расширенные тестовые вопросы для разных сценариев
TEST_QUESTIONS = {
    "general": [
        "Что такое машинное обучение?",
        "Объясните принципы работы нейронных сетей",
        "Какие есть типы алгоритмов машинного обучения?",
        "Что такое глубокое обучение?",
        "Расскажите про обработку естественного языка",
        "Что такое компьютерное зрение?",
        "Объясните разницу между ИИ и машинным обучением",
        "Что такое reinforcement learning?",
        "Расскажите про этику в ИИ",
        "Какие есть применения ИИ в медицине?"
    ],
    "technical": [
        "Как работает алгоритм градиентного спуска?",
        "Объясните концепцию overfitting в машинном обучении",
        "Что такое cross-validation?",
        "Как работает алгоритм k-means?",
        "Объясните принцип работы SVM",
        "Что такое feature engineering?",
        "Как работает алгоритм Random Forest?",
        "Объясните концепцию bias-variance tradeoff",
        "Что такое regularization?",
        "Как работает алгоритм XGBoost?"
    ],
    "conversational": [
        "Привет! Как дела?",
        "Можешь рассказать анекдот про программистов?",
        "Что ты думаешь о будущем ИИ?",
        "Помоги мне с домашним заданием по математике",
        "Расскажи интересный факт о космосе",
        "Какой твой любимый фильм?",
        "Что ты знаешь о квантовых компьютерах?",
        "Расскажи про историю интернета",
        "Какие языки программирования самые популярные?",
        "Что такое блокчейн?"
    ]
}

class MultiUserChatTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = {**DEFAULT_CONFIG, **config}
        self.results = []
        self.errors = []
        self.chat_sessions = {}  # user_id -> [messages]
        self.rate_limit_tracker = {}  # user_id -> [timestamps]
        self.start_time = None
        self.end_time = None
        
    def _get_user_question(self, user_id: int, question_type: str = "general") -> str:
        """Возвращает вопрос для пользователя с учетом истории чата"""
        questions = TEST_QUESTIONS.get(question_type, TEST_QUESTIONS["general"])
        
        if self.config["enable_chat_history"] and user_id in self.chat_sessions:
            # Если есть история чата, выбираем более подходящий вопрос
            chat_history = self.chat_sessions[user_id]
            if len(chat_history) > 2:
                # После нескольких сообщений переходим к более сложным вопросам
                questions = TEST_QUESTIONS.get("technical", questions)
            elif len(chat_history) > 1:
                # После первого ответа добавляем разговорные вопросы
                questions = TEST_QUESTIONS.get("conversational", questions)
        
        return random.choice(questions)
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Проверяет rate limit для пользователя"""
        if not self.config["enable_rate_limiting"]:
            return True
            
        now = time.time()
        one_minute_ago = now - 60
        
        if user_id not in self.rate_limit_tracker:
            self.rate_limit_tracker[user_id] = []
        
        # Удаляем старые запросы
        self.rate_limit_tracker[user_id] = [
            ts for ts in self.rate_limit_tracker[user_id] 
            if ts > one_minute_ago
        ]
        
        # Проверяем лимит
        if len(self.rate_limit_tracker[user_id]) >= self.config["rate_limit_requests_per_minute"]:
            return False
        
        # Добавляем текущий запрос
        self.rate_limit_tracker[user_id].append(now)
        return True
    
    async def send_query(self, session: aiohttp.ClientSession, user_id: int, question: str) -> Dict[str, Any]:
        """Отправляет запрос и возвращает task_id"""
        try:
            start_time = time.time()
            
            # Проверяем rate limit
            if not self._check_rate_limit(user_id):
                return {
                    "user_id": user_id,
                    "error": "Rate limit exceeded",
                    "query_time": 0,
                    "status": "rate_limited"
                }
            
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
                    
                    query_time = time.time() - start_time
                    
                    return {
                        "user_id": user_id,
                        "task_id": task_id,
                        "question": question,
                        "query_sent_at": time.time(),
                        "query_time": query_time,
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
        """Получает результат по task_id с опросом"""
        max_attempts = self.config["max_wait_time_seconds"] // 2
        
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
                                "files_count": len(data.get("files", [])),
                                "attempt": attempt + 1,
                                "answer": data.get("answer", "")[:100] + "..." if data.get("answer") else ""
                            }
                        elif data["status"] == "failed":
                            return {
                                "user_id": user_id,
                                "task_id": task_id,
                                "status": "failed",
                                "error": data.get("error", "Unknown error"),
                                "attempt": attempt + 1
                            }
                        
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Ошибка при получении результата для task {task_id}: {e}")
                await asyncio.sleep(2)
                
        return {
            "user_id": user_id,
            "task_id": task_id,
            "status": "timeout",
            "error": f"Timeout after {max_attempts} attempts",
            "attempt": max_attempts
        }

    async def send_feedback(self, session: aiohttp.ClientSession, task_id: str, user_id: int, rating: int) -> Dict[str, Any]:
        """Отправляет отзыв о качестве ответа"""
        if not self.config["enable_feedback"]:
            return {"status": "disabled"}
            
        try:
            async with session.post(
                f"{self.config['base_url']}/feedback",
                json={
                    "task_id": task_id,
                    "rating": rating,
                    "comment": f"Автоматический отзыв от пользователя {user_id}"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return {"status": "sent"}
                else:
                    return {"status": "failed", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def simulate_user_session(self, session: aiohttp.ClientSession, user_id: int) -> List[Dict[str, Any]]:
        """Симулирует сессию одного пользователя с несколькими сообщениями"""
        print(f"👤 Пользователь {user_id} начинает сессию")
        
        session_results = []
        question_types = ["general", "technical", "conversational"]
        
        # Определяем количество сообщений для пользователя (1-3)
        num_messages = random.randint(1, 3)
        
        for message_num in range(num_messages):
            # Выбираем тип вопроса
            question_type = random.choice(question_types)
            question = self._get_user_question(user_id, question_type)
            
            print(f"📤 Пользователь {user_id} отправляет сообщение {message_num + 1}/{num_messages}")
            
            start_time = time.time()
            
            # 1. Отправляем запрос
            query_result = await self.send_query(session, user_id, question)
            
            if query_result["status"] in ["failed", "rate_limited"]:
                query_result["total_time"] = time.time() - start_time
                session_results.append(query_result)
                print(f"❌ Пользователь {user_id} - ошибка при отправке запроса")
                continue
            
            task_id = query_result["task_id"]
            
            # 2. Получаем результат
            result = await self.get_result(session, task_id, user_id)
            
            # Объединяем результаты
            final_result = {**query_result, **result}
            final_result["total_time"] = time.time() - start_time
            final_result["message_number"] = message_num + 1
            final_result["question_type"] = question_type
            
            # Добавляем в историю чата
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = []
            self.chat_sessions[user_id].append({
                "question": question,
                "answer": result.get("answer", ""),
                "timestamp": time.time()
            })
            
            # 3. Отправляем отзыв (если успешно)
            if result["status"] == "completed":
                rating = random.randint(3, 5)  # Случайная оценка 3-5
                feedback_result = await self.send_feedback(session, task_id, user_id, rating)
                final_result["feedback"] = feedback_result
                print(f"✅ Пользователь {user_id} получил ответ за {final_result['total_time']:.2f}с")
                self.results.append(final_result)
            else:
                print(f"❌ Пользователь {user_id} - {result['status']}: {result.get('error', 'Unknown')}")
                self.errors.append(final_result)
            
            session_results.append(final_result)
            
            # Пауза между сообщениями
            if message_num < num_messages - 1:
                await asyncio.sleep(random.uniform(1, 3))
        
        print(f"🏁 Пользователь {user_id} завершил сессию ({len(session_results)} сообщений)")
        return session_results

    async def run_multi_user_test(self):
        """Запускает многопользовательский тест"""
        print(f"🚀 Запуск многопользовательского теста чата RAG")
        print(f"👥 Количество пользователей: {self.config['concurrent_users']}")
        print(f"⏱️  Длительность теста: {self.config['test_duration_minutes']} минут")
        print(f"🎯 URL: {self.config['base_url']}")
        print(f"🏢 Отдел: {self.config['department_id']}")
        print(f"💬 История чата: {'включена' if self.config['enable_chat_history'] else 'отключена'}")
        print(f"⭐ Отзывы: {'включены' if self.config['enable_feedback'] else 'отключены'}")
        print(f"🚦 Rate limiting: {'включен' if self.config['enable_rate_limiting'] else 'отключен'}")
        print("-" * 60)
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Создаем задачи для всех пользователей
            tasks = [
                self.simulate_user_session(session, user_id) 
                for user_id in range(1, self.config['concurrent_users'] + 1)
            ]
            
            # Запускаем все задачи одновременно
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = time.time()
        
        # Анализируем результаты
        self.analyze_results()
        
        return all_results

    def analyze_results(self):
        """Анализирует и выводит результаты теста"""
        print("\n" + "="*80)
        print("📊 РЕЗУЛЬТАТЫ МНОГОПОЛЬЗОВАТЕЛЬСКОГО ТЕСТА ЧАТА RAG")
        print("="*80)
        
        total_time = self.end_time - self.start_time
        successful = len(self.results)
        failed = len(self.errors)
        total_requests = successful + failed
        
        print(f"👥 Всего пользователей: {self.config['concurrent_users']}")
        print(f"📨 Всего запросов: {total_requests}")
        print(f"✅ Успешных запросов: {successful} ({successful/total_requests*100:.1f}%)")
        print(f"❌ Неудачных запросов: {failed} ({failed/total_requests*100:.1f}%)")
        print(f"⏱️  Общее время теста: {total_time:.2f} секунд")
        print(f"💬 Активных чат-сессий: {len(self.chat_sessions)}")
        
        if self.results:
            times = [r["total_time"] for r in self.results]
            query_times = [r["query_time"] for r in self.results]
            answer_lengths = [r.get("answer_length", 0) for r in self.results]
            chunks_counts = [r.get("chunks_count", 0) for r in self.results]
            
            print(f"\n⏱️  ВРЕМЯ ОТВЕТА:")
            print(f"   Среднее: {statistics.mean(times):.2f}с")
            print(f"   Медиана: {statistics.median(times):.2f}с")
            print(f"   Минимальное: {min(times):.2f}с")
            print(f"   Максимальное: {max(times):.2f}с")
            print(f"   95-й перцентиль: {statistics.quantiles(times, n=20)[18]:.2f}с")
            
            print(f"\n📤 ВРЕМЯ ОТПРАВКИ ЗАПРОСА:")
            print(f"   Среднее: {statistics.mean(query_times):.3f}с")
            print(f"   Максимальное: {max(query_times):.3f}с")
            
            print(f"\n📝 КАЧЕСТВО ОТВЕТОВ:")
            print(f"   Средняя длина ответа: {statistics.mean(answer_lengths):.0f} символов")
            print(f"   Среднее количество чанков: {statistics.mean(chunks_counts):.1f}")
            
            # Пропускная способность
            rps = successful / total_time
            print(f"\n🚀 ПРОИЗВОДИТЕЛЬНОСТЬ:")
            print(f"   Запросов в секунду: {rps:.2f}")
            print(f"   Среднее время на запрос: {total_time/total_requests:.2f}с")
            
            # Анализ по типам вопросов
            question_types = {}
            for result in self.results:
                q_type = result.get("question_type", "unknown")
                question_types[q_type] = question_types.get(q_type, 0) + 1
            
            if question_types:
                print(f"\n📋 РАСПРЕДЕЛЕНИЕ ПО ТИПАМ ВОПРОСОВ:")
                for q_type, count in question_types.items():
                    print(f"   {q_type}: {count} ({count/successful*100:.1f}%)")
        
        if self.errors:
            print(f"\n❌ ОШИБКИ:")
            error_types = {}
            for error in self.errors:
                error_type = error.get("error", "Unknown")[:50]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count}")
        
        # Статистика чат-сессий
        if self.chat_sessions:
            session_lengths = [len(session) for session in self.chat_sessions.values()]
            print(f"\n💬 СТАТИСТИКА ЧАТ-СЕССИЙ:")
            print(f"   Среднее количество сообщений: {statistics.mean(session_lengths):.1f}")
            print(f"   Максимальное количество сообщений: {max(session_lengths)}")
            print(f"   Минимальное количество сообщений: {min(session_lengths)}")
        
        print("="*80)

async def main():
    parser = argparse.ArgumentParser(description="Многопользовательский тест чата RAG")
    parser.add_argument("--users", type=int, default=50, help="Количество одновременных пользователей")
    parser.add_argument("--duration", type=int, default=5, help="Длительность теста в минутах")
    parser.add_argument("--url", type=str, default="http://localhost:8081/api", help="URL API")
    parser.add_argument("--department", type=str, default="5", help="ID отдела")
    parser.add_argument("--no-chat-history", action="store_true", help="Отключить историю чата")
    parser.add_argument("--no-feedback", action="store_true", help="Отключить отправку отзывов")
    parser.add_argument("--no-rate-limit", action="store_true", help="Отключить rate limiting")
    
    args = parser.parse_args()
    
    config = {
        "concurrent_users": args.users,
        "test_duration_minutes": args.duration,
        "base_url": args.url,
        "department_id": args.department,
        "enable_chat_history": not args.no_chat_history,
        "enable_feedback": not args.no_feedback,
        "enable_rate_limiting": not args.no_rate_limit
    }
    
    tester = MultiUserChatTester(config)
    await tester.run_multi_user_test()

if __name__ == "__main__":
    asyncio.run(main()) 