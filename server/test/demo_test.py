#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования чата RAG
Показывает основные возможности тестов с минимальной нагрузкой
"""

import asyncio
import aiohttp
import time
import random
from datetime import datetime

# Конфигурация для демо
DEMO_CONFIG = {
    "base_url": "https://77.222.42.53/api",
    "department_id": "5",
    "concurrent_users": 5,  # Минимальная нагрузка для демо
    "test_duration_seconds": 30,  # Короткий тест
    "questions": [
        "Что такое машинное обучение?",
        "Объясните принципы работы нейронных сетей",
        "Какие есть типы алгоритмов машинного обучения?",
        "Что такое глубокое обучение?",
        "Расскажите про обработку естественного языка"
    ]
}

class DemoChatTester:
    def __init__(self, config):
        self.config = config
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    async def send_query(self, session, user_id, question):
        """Отправляет запрос и возвращает task_id"""
        try:
            start_time = time.time()
            
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

    async def get_result(self, session, task_id, user_id):
        """Получает результат по task_id с опросом"""
        max_attempts = 20  # Короткий таймаут для демо
        
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
                                "attempt": attempt + 1,
                                "answer_preview": data.get("answer", "")[:100] + "..." if data.get("answer") else ""
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
                await asyncio.sleep(2)
                
        return {
            "user_id": user_id,
            "task_id": task_id,
            "status": "timeout",
            "error": f"Timeout after {max_attempts} attempts",
            "attempt": max_attempts
        }

    async def simulate_user(self, session, user_id):
        """Симулирует одного пользователя"""
        print(f"👤 Пользователь {user_id} начинает тест")
        
        # Выбираем случайный вопрос
        question = random.choice(self.config["questions"])
        
        start_time = time.time()
        
        # 1. Отправляем запрос
        query_result = await self.send_query(session, user_id, question)
        
        if query_result["status"] == "failed":
            query_result["total_time"] = time.time() - start_time
            self.errors.append(query_result)
            print(f"❌ Пользователь {user_id} - ошибка при отправке запроса")
            return query_result
        
        task_id = query_result["task_id"]
        print(f"📤 Пользователь {user_id} отправил запрос, task_id: {task_id}")
        
        # 2. Получаем результат
        result = await self.get_result(session, task_id, user_id)
        
        # Объединяем результаты
        final_result = {**query_result, **result}
        final_result["total_time"] = time.time() - start_time
        
        if result["status"] == "completed":
            print(f"✅ Пользователь {user_id} получил ответ за {final_result['total_time']:.2f}с")
            print(f"   📝 Ответ: {result.get('answer_preview', 'Нет ответа')}")
            self.results.append(final_result)
        else:
            print(f"❌ Пользователь {user_id} - {result['status']}: {result.get('error', 'Unknown')}")
            self.errors.append(final_result)
            
        return final_result

    async def run_demo(self):
        """Запускает демонстрационный тест"""
        print("🎬 ДЕМОНСТРАЦИОННЫЙ ТЕСТ ЧАТА RAG")
        print("="*50)
        print(f"👥 Количество пользователей: {self.config['concurrent_users']}")
        print(f"⏱️  Длительность теста: {self.config['test_duration_seconds']} секунд")
        print(f"🎯 URL: {self.config['base_url']}")
        print(f"🏢 Отдел: {self.config['department_id']}")
        print("-" * 50)
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Создаем задачи для всех пользователей
            tasks = [
                self.simulate_user(session, user_id) 
                for user_id in range(1, self.config['concurrent_users'] + 1)
            ]
            
            # Запускаем все задачи одновременно
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = time.time()
        
        # Анализируем результаты
        self.analyze_demo_results()
        
        return results

    def analyze_demo_results(self):
        """Анализирует и выводит результаты демо-теста"""
        print("\n" + "="*50)
        print("📊 РЕЗУЛЬТАТЫ ДЕМО-ТЕСТА")
        print("="*50)
        
        total_time = self.end_time - self.start_time
        successful = len(self.results)
        failed = len(self.errors)
        total = successful + failed
        
        print(f"👥 Всего пользователей: {self.config['concurrent_users']}")
        print(f"📨 Всего запросов: {total}")
        print(f"✅ Успешных запросов: {successful} ({successful/total*100:.1f}%)")
        print(f"❌ Неудачных запросов: {failed} ({failed/total*100:.1f}%)")
        print(f"⏱️  Общее время теста: {total_time:.2f} секунд")
        
        if self.results:
            times = [r["total_time"] for r in self.results]
            query_times = [r["query_time"] for r in self.results]
            answer_lengths = [r.get("answer_length", 0) for r in self.results]
            
            print(f"\n⏱️  ВРЕМЯ ОТВЕТА:")
            print(f"   Среднее: {sum(times)/len(times):.2f}с")
            print(f"   Минимальное: {min(times):.2f}с")
            print(f"   Максимальное: {max(times):.2f}с")
            
            print(f"\n📤 ВРЕМЯ ОТПРАВКИ ЗАПРОСА:")
            print(f"   Среднее: {sum(query_times)/len(query_times):.3f}с")
            print(f"   Максимальное: {max(query_times):.3f}с")
            
            print(f"\n📝 КАЧЕСТВО ОТВЕТОВ:")
            print(f"   Средняя длина ответа: {sum(answer_lengths)/len(answer_lengths):.0f} символов")
            
            # Пропускная способность
            rps = successful / total_time
            print(f"\n🚀 ПРОИЗВОДИТЕЛЬНОСТЬ:")
            print(f"   Запросов в секунду: {rps:.2f}")
        
        if self.errors:
            print(f"\n❌ ОШИБКИ:")
            error_types = {}
            for error in self.errors:
                error_type = error.get("error", "Unknown")[:50]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count}")
        
        print("="*50)
        print("🎉 Демо-тест завершен!")
        print("💡 Для более серьезного тестирования используйте:")
        print("   python run_tests.py multi --users 20 --duration 3")
        print("   python run_tests.py stress --users 50 --duration 5")

async def main():
    print("🎬 Запуск демонстрационного теста чата RAG...")
    print("Этот тест покажет основные возможности системы с минимальной нагрузкой.")
    print()
    
    tester = DemoChatTester(DEMO_CONFIG)
    await tester.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 