#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех компонентов системы
"""

import sys
import os
from dotenv import load_dotenv

def test_imports():
    """Тестирование импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        from database import get_db
        print("✅ Database import OK")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from yandex_cloud_adapter import YandexCloudAdapter
        print("✅ YandexCloudAdapter import OK")
    except Exception as e:
        print(f"❌ YandexCloudAdapter import failed: {e}")
        return False
    
    try:
        from yandex_embeddings import YandexEmbeddings
        print("✅ YandexEmbeddings import OK")
    except Exception as e:
        print(f"❌ YandexEmbeddings import failed: {e}")
        return False
    
    try:
        from yandex_rag_service import get_rag_service
        print("✅ RAG service import OK")
    except Exception as e:
        print(f"❌ RAG service import failed: {e}")
        return False
    
    try:
        from routes.yandex_rag_routes import router
        print("✅ RAG routes import OK")
    except Exception as e:
        print(f"❌ RAG routes import failed: {e}")
        return False
    
    try:
        import app
        print("✅ App import OK")
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    return True

def test_environment():
    """Тестирование переменных окружения"""
    print("\n🔍 Тестирование переменных окружения...")
    
    load_dotenv()
    
    required_vars = [
        'YANDEX_API_KEY',
        'YANDEX_FOLDER_ID',
        'USE_YANDEX_CLOUD'
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: SET")
        else:
            print(f"❌ {var}: NOT SET")
            all_ok = False
    
    return all_ok

def test_database_connection():
    """Тестирование подключения к базе данных"""
    print("\n🔍 Тестирование подключения к базе данных...")
    
    try:
        from database import get_db
        from sqlalchemy.orm import Session
        from sqlalchemy import text
        
        # Создаем сессию
        db = next(get_db())
        
        # Выполняем простой запрос
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        print("✅ Database connection OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_yandex_api():
    """Тестирование Yandex API"""
    print("\n🔍 Тестирование Yandex API...")
    
    try:
        from yandex_cloud_adapter import get_yandex_adapter
        
        # Получаем адаптер
        adapter = await get_yandex_adapter()
        
        print("✅ Yandex API adapter OK")
        return True
    except Exception as e:
        print(f"❌ Yandex API test failed: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы...")
    print("=" * 50)
    
    tests = [
        ("Импорты", test_imports),
        ("Переменные окружения", test_environment),
        ("Подключение к БД", test_database_connection),
        ("Yandex API", test_yandex_api),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Yandex API":
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Все тесты пройдены! Система готова к работе.")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте конфигурацию.")
    
    return all_passed

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 