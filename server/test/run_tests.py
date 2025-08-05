#!/usr/bin/env python3
"""
Скрипт для запуска различных тестов чата RAG с детальным выводом
"""

import asyncio
import argparse
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Добавляем путь к модулям тестов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestLogger:
    """Класс для логирования тестов с детальным выводом"""
    
    def __init__(self, verbose: bool = True, save_to_file: bool = False):
        self.verbose = verbose
        self.save_to_file = save_to_file
        self.log_file = None
        self.test_results = []
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = open(f"test_results_{timestamp}.json", "w", encoding="utf-8")
    
    def log(self, message: str, level: str = "INFO"):
        """Логирует сообщение с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        if self.verbose:
            print(formatted_message)
        
        if self.save_to_file:
            self.test_results.append({
                "timestamp": timestamp,
                "level": level,
                "message": message
            })
    
    def log_request(self, user_id: str, question: str, task_id: str = None, duration: float = None):
        """Логирует отправку запроса"""
        self.log(f"👤 Пользователь {user_id} отправляет запрос:")
        self.log(f"   📝 Вопрос: {question}")
        if task_id:
            self.log(f"   🆔 Task ID: {task_id}")
        if duration:
            self.log(f"   ⏱️ Время отправки: {duration:.3f}с")
    
    def log_response(self, user_id: str, task_id: str, response_data: Dict[str, Any], duration: float = None):
        """Логирует получение ответа"""
        status = response_data.get("status", "unknown")
        answer = response_data.get("answer", "")
        chunks = response_data.get("chunks", [])
        files = response_data.get("files", [])
        error = response_data.get("error", "")
        
        self.log(f"👤 Пользователь {user_id} получил ответ:")
        self.log(f"   🆔 Task ID: {task_id}")
        self.log(f"   📊 Статус: {status}")
        
        if status == "completed":
            self.log(f"   ✅ Ответ ({len(answer)} символов):")
            # Показываем первые 200 символов ответа
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            self.log(f"      {preview}")
            
            if chunks:
                self.log(f"   ✅ Найдено фрагментов: {len(chunks)}")
                for i, chunk in enumerate(chunks[:2]):  # Показываем первые 2 фрагмента
                    chunk_preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                    self.log(f"      Фрагмент {i+1}: {chunk_preview}")
            
            if files:
                self.log(f"   📁 Источники: {len(files)} файлов")
                for file in files[:3]:  # Показываем первые 3 файла
                    self.log(f"       {file}")
        
        elif status == "failed":
            self.log(f"   ❌ Ошибка: {error}")
        
        if duration:
            self.log(f"   ⏱️ Общее время: {duration:.3f}с")
    
    def log_summary(self, results: List[Dict[str, Any]]):
        """Логирует итоговую статистику"""
        total_requests = len(results)
        successful = len([r for r in results if r.get("status") == "completed"])
        failed = total_requests - successful
        
        self.log("="*60)
        self.log("📊 ИТОГОВАЯ СТАТИСТИКА:")
        self.log(f"   📈 Всего запросов: {total_requests}")
        self.log(f"   ✅ Успешных: {successful}")
        self.log(f"   ❌ Неудачных: {failed}")
        self.log(f"    Процент успеха: {(successful/total_requests*100):.1f}%" if total_requests > 0 else "    Процент успеха: 0%")
        
        if successful > 0:
            avg_response_time = sum([r.get("total_time", 0) for r in results if r.get("status") == "completed"]) / successful
            self.log(f"   ⏱️ Среднее время ответа: {avg_response_time:.3f}с")
        
        self.log("="*60)
    
    def close(self):
        """Закрывает лог файл"""
        if self.save_to_file and self.log_file:
            json.dump(self.test_results, self.log_file, ensure_ascii=False, indent=2)
            self.log_file.close()

def print_banner():
    """Выводит баннер с информацией о тестах"""
    print("="*80)
    print("🧪 ТЕСТИРОВАНИЕ ЧАТА RAG С ДЕТАЛЬНЫМ ВЫВОДОМ")
    print("="*80)
    print("Доступные тесты:")
    print("1. quick - Быстрый тест работоспособности")
    print("2. multi - Многопользовательский тест с чат-сессиями")
    print("3. stress - Стресс-тест с мониторингом")
    print("4. load - Простой нагрузочный тест")
    print("5. detailed - Детальный тест с выводом всех запросов/ответов")
    print("="*80)

async def run_detailed_test(config: Dict[str, Any], logger: TestLogger):
    """Запускает детальный тест с выводом всех запросов и ответов"""
    import aiohttp
    
    print(f"🔍 Запуск детального теста...")
    
    base_url = config.get("base_url", "http://localhost:8081/api")
    department_id = config.get("department_id", "5")
    num_requests = config.get("num_requests", 5)
    
    # Тестовые вопросы разной сложности
    test_questions = [
        "Привет! Как дела?",
        "Что такое искусственный интеллект?",
        "Расскажи подробно о машинном обучении и его применениях",
        "Какие документы у вас есть в базе знаний?",
        "Объясни принципы работы нейронных сетей простыми словами"
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(min(num_requests, len(test_questions))):
            question = test_questions[i]
            user_id = f"test_user_{i+1}"
            
            logger.log(f"\n🔄 Тест {i+1}/{num_requests}")
            
            # Отправляем запрос
            start_time = time.time()
            try:
                async with session.post(
                    f"{base_url}/llm/query",
                    json={
                        "question": question,
                        "department_id": department_id
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    query_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        task_id = data.get("task_id")
                        
                        logger.log_request(user_id, question, task_id, query_time)
                        
                        # Ждем результат
                        result_start_time = time.time()
                        for attempt in range(30):  # Максимум 30 попыток
                            await asyncio.sleep(2)
                            
                            try:
                                async with session.get(
                                    f"{base_url}/llm/query/{task_id}",
                                    timeout=aiohttp.ClientTimeout(total=10)
                                ) as result_response:
                                    if result_response.status == 200:
                                        result_data = await result_response.json()
                                        total_time = time.time() - start_time
                                        
                                        logger.log_response(user_id, task_id, result_data, total_time)
                                        
                                        results.append({
                                            "user_id": user_id,
                                            "question": question,
                                            "task_id": task_id,
                                            "status": result_data.get("status"),
                                            "total_time": total_time,
                                            "answer_length": len(result_data.get("answer", "")),
                                            "chunks_count": len(result_data.get("chunks", [])),
                                            "files_count": len(result_data.get("files", []))
                                        })
                                        break
                                    else:
                                        logger.log(f"   ⚠️ Попытка {attempt+1}: HTTP {result_response.status}")
                            except Exception as e:
                                logger.log(f"   ⚠️ Попытка {attempt+1}: Ошибка получения результата - {e}")
                        else:
                            logger.log(f"   ⏰ Таймаут ожидания результата для {user_id}")
                            results.append({
                                "user_id": user_id,
                                "question": question,
                                "task_id": task_id,
                                "status": "timeout",
                                "total_time": time.time() - start_time
                            })
                    else:
                        error_text = await response.text()
                        logger.log(f"   ❌ Ошибка отправки запроса: HTTP {response.status} - {error_text}")
                        results.append({
                            "user_id": user_id,
                            "question": question,
                            "status": "failed",
                            "error": f"HTTP {response.status}: {error_text}",
                            "total_time": query_time
                        })
                        
            except Exception as e:
                logger.log(f"   ❌ Ошибка запроса: {e}")
                results.append({
                    "user_id": user_id,
                    "question": question,
                    "status": "failed",
                    "error": str(e),
                    "total_time": time.time() - start_time
                })
    
    # Выводим итоговую статистику
    logger.log_summary(results)
    return results

async def run_quick_test(config: Dict[str, Any], logger: TestLogger):
    """Запускает быстрый тест для проверки работоспособности"""
    import aiohttp
    
    logger.log("⚡ Быстрый тест работоспособности...")
    
    base_url = config.get("base_url", "http://localhost:8081/api")
    department_id = config.get("department_id", "5")
    
    async with aiohttp.ClientSession() as session:
        # Проверяем доступность API
        try:
            async with session.get(f"{base_url}/llm/models", timeout=10) as response:
                if response.status == 200:
                    logger.log("✅ API доступен")
                else:
                    logger.log(f"❌ API недоступен: HTTP {response.status}")
                    return
        except Exception as e:
            logger.log(f"❌ Ошибка подключения к API: {e}")
            return
        
        # Проверяем инициализацию отдела
        try:
            async with session.get(f"{base_url}/llm/queue/status/{department_id}", timeout=10) as response:
                if response.status == 200:
                    status = await response.json()
                    if status.get("initialized"):
                        logger.log(f"✅ Отдел {department_id} инициализирован")
                    else:
                        logger.log(f"⚠️ Отдел {department_id} не инициализирован")
                else:
                    logger.log(f"❌ Ошибка получения статуса отдела: HTTP {response.status}")
        except Exception as e:
            logger.log(f"❌ Ошибка проверки статуса отдела: {e}")
        
        # Отправляем тестовый запрос
        try:
            start_time = time.time()
            async with session.post(
                f"{base_url}/llm/query",
                json={
                    "question": "Привет! Как дела?",
                    "department_id": department_id
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    task_id = data.get("task_id")
                    logger.log(f"✅ Запрос отправлен, task_id: {task_id}")
                    
                    # Ждем результат
                    for attempt in range(20):
                        await asyncio.sleep(2)
                        async with session.get(f"{base_url}/llm/query/{task_id}", timeout=10) as result_response:
                            if result_response.status == 200:
                                result_data = await result_response.json()
                                if result_data["status"] == "completed":
                                    total_time = time.time() - start_time
                                    logger.log(f"✅ Получен ответ за {total_time:.2f}с")
                                    logger.log(f"📝 Длина ответа: {len(result_data.get('answer', ''))} символов")
                                    
                                    # Показываем часть ответа
                                    answer = result_data.get('answer', '')
                                    preview = answer[:200] + "..." if len(answer) > 200 else answer
                                    logger.log(f"📝 Ответ: {preview}")
                                    return
                                elif result_data["status"] == "failed":
                                    logger.log(f"❌ Задача завершилась с ошибкой: {result_data.get('error', 'Unknown')}")
                                    return
                    
                    logger.log("⏰ Таймаут ожидания результата")
                else:
                    error_text = await response.text()
                    logger.log(f"❌ Ошибка отправки запроса: HTTP {response.status} - {error_text}")
        except Exception as e:
            logger.log(f"❌ Ошибка тестового запроса: {e}")

async def run_multi_user_test(config: Dict[str, Any], logger: TestLogger):
    """Запускает многопользовательский тест"""
    from multi_user_chat_test import MultiUserChatTester
    
    logger.log("🚀 Запуск многопользовательского теста...")
    tester = MultiUserChatTester(config)
    await tester.run_multi_user_test()

async def run_stress_test(config: Dict[str, Any], logger: TestLogger):
    """Запускает стресс-тест"""
    from stress_test_chat import StressTestChat
    
    logger.log("🔥 Запуск стресс-теста...")
    tester = StressTestChat(config)
    await tester.run_stress_test()

async def run_load_test(config: Dict[str, Any], logger: TestLogger):
    """Запускает простой нагрузочный тест"""
    from load_test_chat import LoadTester
    
    logger.log("⚡ Запуск нагрузочного теста...")
    tester = LoadTester()
    await tester.run_load_test()

async def main():
    parser = argparse.ArgumentParser(description="Запуск тестов чата RAG с детальным выводом")
    parser.add_argument("test_type", choices=["quick", "detailed", "multi", "stress", "load"], 
                       help="Тип теста для запуска")
    parser.add_argument("--users", type=int, default=50, help="Количество пользователей")
    parser.add_argument("--duration", type=int, default=5, help="Длительность теста в минутах")
    parser.add_argument("--url", type=str, default="http://localhost:8081/api", help="URL API")
    parser.add_argument("--department", type=str, default="5", help="ID отдела")
    parser.add_argument("--ramp-up", type=int, default=2, help="Время нарастания нагрузки (только для stress)")
    parser.add_argument("--ramp-down", type=int, default=2, help="Время снижения нагрузки (только для stress)")
    parser.add_argument("--no-chat-history", action="store_true", help="Отключить историю чата")
    parser.add_argument("--no-feedback", action="store_true", help="Отключить отправку отзывов")
    parser.add_argument("--no-monitoring", action="store_true", help="Отключить мониторинг")
    parser.add_argument("--verbose", action="store_true", default=True, help="Подробный вывод")
    parser.add_argument("--save-log", action="store_true", help="Сохранить лог в файл")
    parser.add_argument("--num-requests", type=int, default=5, help="Количество запросов для detailed теста")
    
    args = parser.parse_args()
    
    # Создаем логгер
    logger = TestLogger(verbose=args.verbose, save_to_file=args.save_log)
    
    try:
        # Общая конфигурация
        config = {
            "base_url": args.url,
            "department_id": args.department,
            "enable_chat_history": not args.no_chat_history,
            "enable_feedback": not args.no_feedback,
            "enable_monitoring": not args.no_monitoring,
            "num_requests": args.num_requests
        }
        
        # Запускаем выбранный тест
        if args.test_type == "quick":
            await run_quick_test(config, logger)
        elif args.test_type == "detailed":
            await run_detailed_test(config, logger)
        elif args.test_type == "multi":
            config.update({
                "concurrent_users": args.users,
                "test_duration_minutes": args.duration
            })
            await run_multi_user_test(config, logger)
        elif args.test_type == "stress":
            config.update({
                "concurrent_users": args.users,
                "test_duration_minutes": args.duration,
                "ramp_up_minutes": args.ramp_up,
                "ramp_down_minutes": args.ramp_down
            })
            await run_stress_test(config, logger)
        elif args.test_type == "load":
            import load_test_chat
            load_test_chat.CONCURRENT_USERS = args.users
            load_test_chat.BASE_URL = args.url
            load_test_chat.DEPARTMENT_ID = args.department
            await run_load_test(config, logger)
    
    finally:
        logger.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_banner()
        print("Использование:")
        print("python run_tests.py <тип_теста> [опции]")
        print("\nПримеры:")
        print("python run_tests.py quick")
        print("python run_tests.py detailed --num-requests 10")
        print("python run_tests.py multi --users 20 --duration 3")
        print("python run_tests.py stress --users 100 --duration 10")
        print("python run_tests.py load --users 50")
        print("\nОпции:")
        print("--verbose          Подробный вывод (по умолчанию)")
        print("--save-log         Сохранить лог в файл")
        print("--num-requests N   Количество запросов для detailed теста")
        sys.exit(1)
    
    asyncio.run(main()) 