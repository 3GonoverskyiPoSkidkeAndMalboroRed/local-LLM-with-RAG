#!/usr/bin/env python3
"""
Скрипт для запуска различных тестов чата RAG
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# Добавляем путь к модулям тестов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Выводит баннер с информацией о тестах"""
    print("="*80)
    print("🧪 ТЕСТИРОВАНИЕ ЧАТА RAG")
    print("="*80)
    print("Доступные тесты:")
    print("1. multi_user_chat_test.py - Многопользовательский тест с чат-сессиями")
    print("2. stress_test_chat.py - Стресс-тест с мониторингом")
    print("3. load_test_chat.py - Простой нагрузочный тест")
    print("="*80)

async def run_multi_user_test(config):
    """Запускает многопользовательский тест"""
    from multi_user_chat_test import MultiUserChatTester
    
    print(f"🚀 Запуск многопользовательского теста...")
    tester = MultiUserChatTester(config)
    await tester.run_multi_user_test()

async def run_stress_test(config):
    """Запускает стресс-тест"""
    from stress_test_chat import StressTestChat
    
    print(f"🔥 Запуск стресс-теста...")
    tester = StressTestChat(config)
    await tester.run_stress_test()

async def run_load_test(config):
    """Запускает простой нагрузочный тест"""
    from load_test_chat import LoadTester
    
    print(f"⚡ Запуск нагрузочного теста...")
    tester = LoadTester()
    await tester.run_load_test()

async def run_quick_test(config):
    """Запускает быстрый тест для проверки работоспособности"""
    import aiohttp
    import time
    
    print(f"⚡ Быстрый тест работоспособности...")
    
    base_url = config.get("base_url", "http://localhost:8081/api")
    department_id = config.get("department_id", "5")
    
    async with aiohttp.ClientSession() as session:
        # Проверяем доступность API
        try:
            async with session.get(f"{base_url}/llm/models", timeout=10) as response:
                if response.status == 200:
                    print("✅ API доступен")
                else:
                    print(f"❌ API недоступен: HTTP {response.status}")
                    return
        except Exception as e:
            print(f"❌ Ошибка подключения к API: {e}")
            return
        
        # Проверяем инициализацию отдела
        try:
            async with session.get(f"{base_url}/llm/queue/status/{department_id}", timeout=10) as response:
                if response.status == 200:
                    status = await response.json()
                    if status.get("initialized"):
                        print(f"✅ Отдел {department_id} инициализирован")
                    else:
                        print(f"⚠️ Отдел {department_id} не инициализирован")
                else:
                    print(f"❌ Ошибка получения статуса отдела: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Ошибка проверки статуса отдела: {e}")
        
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
                    print(f"✅ Запрос отправлен, task_id: {task_id}")
                    
                    # Ждем результат
                    for attempt in range(20):
                        await asyncio.sleep(2)
                        async with session.get(f"{base_url}/llm/query/{task_id}", timeout=10) as result_response:
                            if result_response.status == 200:
                                result_data = await result_response.json()
                                if result_data["status"] == "completed":
                                    total_time = time.time() - start_time
                                    print(f"✅ Получен ответ за {total_time:.2f}с")
                                    print(f"📝 Длина ответа: {len(result_data.get('answer', ''))} символов")
                                    return
                                elif result_data["status"] == "failed":
                                    print(f"❌ Задача завершилась с ошибкой: {result_data.get('error', 'Unknown')}")
                                    return
                    
                    print("⏰ Таймаут ожидания результата")
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка отправки запроса: HTTP {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Ошибка тестового запроса: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Запуск тестов чата RAG")
    parser.add_argument("test_type", choices=["multi", "stress", "load", "quick"], 
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
    
    args = parser.parse_args()
    
    # Общая конфигурация
    config = {
        "base_url": args.url,
        "department_id": args.department,
        "enable_chat_history": not args.no_chat_history,
        "enable_feedback": not args.no_feedback,
        "enable_monitoring": not args.no_monitoring
    }
    
    # Специфичная конфигурация для каждого типа теста
    if args.test_type == "multi":
        config.update({
            "concurrent_users": args.users,
            "test_duration_minutes": args.duration
        })
        await run_multi_user_test(config)
    
    elif args.test_type == "stress":
        config.update({
            "concurrent_users": args.users,
            "test_duration_minutes": args.duration,
            "ramp_up_minutes": args.ramp_up,
            "ramp_down_minutes": args.ramp_down
        })
        await run_stress_test(config)
    
    elif args.test_type == "load":
        # Для load_test_chat.py используем глобальные переменные
        import load_test_chat
        load_test_chat.CONCURRENT_USERS = args.users
        load_test_chat.BASE_URL = args.url
        load_test_chat.DEPARTMENT_ID = args.department
        await run_load_test(config)
    
    elif args.test_type == "quick":
        await run_quick_test(config)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_banner()
        print("Использование:")
        print("python run_tests.py <тип_теста> [опции]")
        print("\nПримеры:")
        print("python run_tests.py quick")
        print("python run_tests.py multi --users 20 --duration 3")
        print("python run_tests.py stress --users 100 --duration 10")
        print("python run_tests.py load --users 50")
        sys.exit(1)
    
    asyncio.run(main()) 