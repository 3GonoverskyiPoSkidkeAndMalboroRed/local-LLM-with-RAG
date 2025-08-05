#!/usr/bin/env python3
"""
Тест RAG эндпоинта с реальным запросом
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_rag_endpoint():
    """Тестирование RAG эндпоинта"""
    print("🔍 Тестирование RAG эндпоинта...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # Тестовый запрос (такой же как в примере пользователя)
        test_request = {
            "query": "привет",
            "department_id": "5",
            "max_chunks": 5,
            "similarity_threshold": 0.7,
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
            print(f"📄 Ответ: {result.get('answer', 'Нет ответа')[:100]}...")
            print(f"🔗 Источники: {len(result.get('sources', []))}")
            print(f"📝 Чанки: {len(result.get('chunks_used', []))}")
            print(f"⚡ Время обработки: {result.get('processing_time', 0):.2f}с")
            return True
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования RAG эндпоинта: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rag_service_direct():
    """Прямое тестирование RAG сервиса"""
    print("\n🔍 Прямое тестирование RAG сервиса...")
    
    try:
        from yandex_rag_service import get_rag_service, RAGContext
        from database import get_db
        
        # Получаем RAG сервис
        rag_service = await get_rag_service()
        
        # Создаем контекст
        context = RAGContext(
            query="привет",
            department_id="5",
            max_chunks=3,
            similarity_threshold=0.7,
            include_metadata=True
        )
        
        print(f"📤 Выполняем RAG запрос: {context.query}")
        
        # Получаем сессию БД
        db_session = next(get_db())
        
        # Выполняем RAG запрос
        result = await rag_service.query_with_rag(
            context=context,
            db_session=db_session,
            use_cache=True
        )
        
        print("✅ RAG запрос выполнен успешно!")
        print(f"📄 Ответ: {result.answer[:100]}...")
        print(f"🔗 Источники: {len(result.sources)}")
        print(f"📝 Чанки: {len(result.chunks_used)}")
        print(f"⚡ Время обработки: {result.processing_time:.2f}с")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка прямого тестирования RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rag_metrics():
    """Тестирование метрик RAG"""
    print("\n🔍 Тестирование метрик RAG...")
    
    try:
        from yandex_rag_service import get_rag_service
        
        rag_service = await get_rag_service()
        metrics = rag_service.get_metrics()
        
        print("✅ Метрики RAG получены:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения метрик: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования RAG эндпоинта...")
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("RAG эндпоинт", test_rag_endpoint),
        ("Прямое тестирование RAG", test_rag_service_direct),
        ("Метрики RAG", test_rag_metrics),
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
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
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
        print("\n🎉 Все тесты пройдены! RAG работает корректно.")
        return True
    else:
        print(f"\n⚠️  {len(results) - success_count} тестов провалено.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 