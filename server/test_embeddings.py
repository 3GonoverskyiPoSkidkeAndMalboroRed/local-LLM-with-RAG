#!/usr/bin/env python3
"""
Тест эмбеддингов
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_embeddings():
    """Тестирование эмбеддингов"""
    print("🔍 Тестирование эмбеддингов...")
    
    try:
        from yandex_embeddings import create_embeddings
        
        # Создаем эмбеддинги
        embeddings = create_embeddings(model="text-search-doc")
        
        # Тестовый текст
        test_texts = [
            "Привет! Это тестовый документ для проверки работы RAG системы.",
            "RAG - это технология, которая объединяет возможности языковых моделей с поиском по базе знаний."
        ]
        
        print(f"📝 Тестируем {len(test_texts)} текстов...")
        
        for i, text in enumerate(test_texts):
            print(f"\n📄 Текст {i+1}: {text[:50]}...")
            
            try:
                # Создаем эмбеддинг
                embedding = embeddings.embed_query(text)
                print(f"✅ Эмбеддинг создан, размер: {len(embedding)}")
            except Exception as e:
                print(f"❌ Ошибка создания эмбеддинга: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования эмбеддингов: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_embeddings_batch():
    """Тестирование batch эмбеддингов"""
    print("\n🔍 Тестирование batch эмбеддингов...")
    
    try:
        from yandex_embeddings import create_embeddings
        
        # Создаем эмбеддинги
        embeddings = create_embeddings(model="text-search-doc")
        
        # Тестовые тексты
        test_texts = [
            "Привет! Это тестовый документ для проверки работы RAG системы.",
            "RAG - это технология, которая объединяет возможности языковых моделей с поиском по базе знаний.",
            "Система работает следующим образом: пользователь задает вопрос, система ищет релевантные документы."
        ]
        
        print(f"📝 Тестируем batch из {len(test_texts)} текстов...")
        
        try:
            # Создаем batch эмбеддинги
            batch_embeddings = embeddings.embed_documents(test_texts)
            print(f"✅ Batch эмбеддинги созданы, количество: {len(batch_embeddings)}")
            
            for i, embedding in enumerate(batch_embeddings):
                print(f"  Эмбеддинг {i+1}: размер {len(embedding)}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка создания batch эмбеддингов: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования batch эмбеддингов: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования эмбеддингов...")
    
    tests = [
        ("Эмбеддинги", test_embeddings),
        ("Batch эмбеддинги", test_embeddings_batch),
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
        print("\n🎉 Все тесты пройдены! Эмбеддинги работают корректно.")
        return True
    else:
        print(f"\n⚠️ {len(results) - success_count} тестов провалено.")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 