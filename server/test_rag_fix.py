#!/usr/bin/env python3
"""
Тест для проверки исправлений RAG
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_rag_imports():
    """Тестирование импортов RAG компонентов"""
    print("🔍 Тестирование импортов RAG компонентов...")
    
    try:
        from yandex_rag_service import YandexRAGService, RAGContext, get_rag_service
        print("✅ yandex_rag_service импорт OK")
        
        from document_loader import vec_search
        print("✅ document_loader.vec_search импорт OK")
        
        from routes.yandex_rag_routes import router
        print("✅ yandex_rag_routes импорт OK")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

async def test_rag_service_creation():
    """Тестирование создания RAG сервиса"""
    print("\n🔍 Тестирование создания RAG сервиса...")
    
    try:
        from yandex_rag_service import get_rag_service
        
        rag_service = await get_rag_service()
        print("✅ RAG сервис создан успешно")
        
        # Проверяем основные атрибуты
        assert hasattr(rag_service, '_error_handler'), "Отсутствует _error_handler"
        assert hasattr(rag_service, '_cache'), "Отсутствует _cache"
        assert hasattr(rag_service, 'llm_model'), "Отсутствует llm_model"
        assert hasattr(rag_service, 'embedding_model'), "Отсутствует embedding_model"
        
        print("✅ Все атрибуты RAG сервиса присутствуют")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания RAG сервиса: {e}")
        return False

async def test_rag_context():
    """Тестирование создания RAG контекста"""
    print("\n🔍 Тестирование создания RAG контекста...")
    
    try:
        from yandex_rag_service import RAGContext
        
        context = RAGContext(
            query="тестовый запрос",
            department_id="5",
            max_chunks=3,
            similarity_threshold=0.7
        )
        
        print(f"✅ RAG контекст создан: query='{context.query}', department_id='{context.department_id}'")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания RAG контекста: {e}")
        return False

async def test_vec_search_function():
    """Тестирование функции vec_search"""
    print("\n🔍 Тестирование функции vec_search...")
    
    try:
        from document_loader import vec_search
        
        # Проверяем сигнатуру функции
        import inspect
        sig = inspect.signature(vec_search)
        params = list(sig.parameters.keys())
        
        expected_params = ['embedding_model', 'query', 'db', 'n_top_cos', 'timeout']
        for param in expected_params:
            assert param in params, f"Отсутствует параметр {param}"
        
        print("✅ Сигнатура vec_search корректна")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования vec_search: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования исправлений RAG...")
    
    tests = [
        ("Импорты RAG", test_rag_imports),
        ("Создание RAG сервиса", test_rag_service_creation),
        ("RAG контекст", test_rag_context),
        ("Функция vec_search", test_vec_search_function),
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
        print("\n🎉 Все тесты пройдены! RAG исправления работают корректно.")
        return True
    else:
        print(f"\n⚠️  {len(results) - success_count} тестов провалено. Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 