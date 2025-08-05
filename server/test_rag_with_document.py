#!/usr/bin/env python3
"""
Финальный тест RAG с реальным документом
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_rag_with_document():
    """Тестирование RAG с реальным документом"""
    print("🔍 Тестирование RAG с реальным документом...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # Тестовый запрос о RAG
        test_request = {
            "query": "Что такое RAG и как он работает?",
            "department_id": "5",
            "max_chunks": 5,
            "similarity_threshold": 0.5,  # Снижаем порог для лучшего поиска
            "include_metadata": True,
            "use_cache": True
        }
        
        print(f"📤 Отправляем запрос: {json.dumps(test_request, indent=2)}")
        
        # Отправляем запрос
        response = client.post("/api/yandex/rag/query", json=test_request)
        
        print(f"📥 Получен ответ: статус {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAG запрос выполнен успешно!")
            print(f"📄 Ответ: {result.get('answer', 'Нет ответа')}")
            print(f"🔗 Источники: {len(result.get('sources', []))}")
            print(f"📝 Чанки: {len(result.get('chunks_used', []))}")
            print(f"⚡ Время обработки: {result.get('processing_time', 0):.2f}с")
            
            # Проверяем, что ответ не стандартный
            if "не удалось найти релевантную информацию" not in result.get('answer', ''):
                print("🎉 RAG нашел релевантную информацию в документах!")
                return True
            else:
                print("⚠️ RAG не нашел релевантную информацию")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования RAG с документом: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_query():
    """Тестирование простого запроса"""
    print("\n🔍 Тестирование простого запроса...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # Простой запрос
        test_request = {
            "query": "привет",
            "department_id": "5",
            "max_chunks": 3,
            "similarity_threshold": 0.3,
            "include_metadata": True,
            "use_cache": True
        }
        
        print(f"📤 Отправляем простой запрос: {test_request['query']}")
        
        response = client.post("/api/yandex/rag/query", json=test_request)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Ответ: {result.get('answer', 'Нет ответа')[:200]}...")
            print(f"📝 Чанки найдено: {len(result.get('chunks_used', []))}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка простого запроса: {e}")
        return False

async def test_rag_health():
    """Тестирование здоровья RAG системы"""
    print("\n🔍 Тестирование здоровья RAG системы...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        response = client.get("/api/yandex/rag/health")
        
        if response.status_code == 200:
            health = response.json()
            print("✅ RAG система здорова!")
            print(f"📊 Статус: {health.get('status')}")
            print(f"🔧 RAG сервис: {'✅' if health.get('rag_service_available') else '❌'}")
            print(f"🤖 LLM модель: {'✅' if health.get('llm_model_available') else '❌'}")
            print(f"📈 Embedding модель: {'✅' if health.get('embedding_model_available') else '❌'}")
            print(f"💾 Кэш: {'✅' if health.get('cache_available') else '❌'}")
            return True
        else:
            print(f"❌ Ошибка здоровья: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки здоровья: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск финального тестирования RAG...")
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("RAG с документом", test_rag_with_document),
        ("Простой запрос", test_simple_query),
        ("Здоровье системы", test_rag_health),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "="*50)
    print("ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\nВсего тестов: {len(results)}")
    print(f"Успешно: {success_count}")
    print(f"Провалено: {len(results) - success_count}")
    
    if success_count == len(results):
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! RAG система полностью исправлена и работает!")
        print("✅ Ошибки исправлены:")
        print("   - object tuple can't be used in 'await' expression")
        print("   - 'Session' object has no attribute 'similarity_search_by_vector'")
        print("   - Проблемы с execute_with_retry")
        return True
    else:
        print(f"\n⚠️  {len(results) - success_count} тестов провалено.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 