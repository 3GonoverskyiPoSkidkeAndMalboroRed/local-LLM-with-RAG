#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Yandex RAG сервиса
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Временно переопределяем DATABASE_URL для Docker
os.environ['DATABASE_URL'] = 'mysql+mysqlconnector://root:123123@localhost:3307/db_test'

async def test_yandex_ai_service():
    """Тестирует Yandex AI сервис"""
    print("🔍 Тестирование Yandex AI сервиса...")
    
    # Проверяем переменные окружения
    api_key = os.getenv('YANDEX_API_KEY') or os.getenv('YC_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID') or os.getenv('YC_FOLDER_ID')
    
    print(f"API Key: {'✅ Установлен' if api_key else '❌ Не установлен'}")
    print(f"Folder ID: {'✅ Установлен' if folder_id else '❌ Не установлен'}")
    
    if not api_key or not folder_id:
        print("❌ Необходимые переменные окружения не установлены")
        print("Убедитесь, что в .env файле установлены:")
        print("YANDEX_API_KEY=ваш_ключ")
        print("YANDEX_FOLDER_ID=ваш_folder_id")
        return False
    
    # Импортируем сервис после загрузки переменных окружения
    from yandex_ai_service import YandexAIService
    
    # Создаем новый экземпляр сервиса
    yandex_ai = YandexAIService()
    
    # Проверяем инициализацию SDK
    if not yandex_ai.ml_client:
        print("❌ Yandex Cloud ML SDK не инициализирован")
        return False
    
    print("✅ Yandex Cloud ML SDK инициализирован")
    
    try:
        # Тестируем генерацию текста
        print("\n📝 Тестирование генерации текста...")
        result = await yandex_ai.generate_text("Привет! Как дела?")
        
        if result and result.get("success"):
            print("✅ Генерация текста работает")
            print(f"Ответ: {result.get('text', '')[:100]}...")
        else:
            print("❌ Ошибка генерации текста")
            print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            return False
        
        # Тестируем создание эмбеддинга
        print("\n🔢 Тестирование создания эмбеддинга...")
        embedding = await yandex_ai.get_embedding("Тестовый текст для эмбеддинга")
        
        if embedding and len(embedding) > 0:
            print(f"✅ Эмбеддинг создан успешно (размер: {len(embedding)})")
        else:
            print("❌ Ошибка создания эмбеддинга")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании Yandex AI: {e}")
        return False

async def test_yandex_rag_service():
    """Тестирует Yandex RAG сервис"""
    print("\n🔍 Тестирование Yandex RAG сервиса...")
    
    # Проверяем подключение к базе данных
    database_url = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:123123@localhost:3307/db_test')
    print(f"Database URL: {database_url}")
    
    try:
        # Импортируем сервис после загрузки переменных окружения
        from yandex_rag_service import YandexRAGService
        
        # Создаем новый экземпляр сервиса
        yandex_rag = YandexRAGService()
        
        # Тестируем получение статуса RAG для отдела 5 (админ)
        print("\n📊 Тестирование получения статуса RAG для отдела 5...")
        status = await yandex_rag.get_rag_status(5)
        
        print("✅ Получение статуса RAG работает")
        print(f"Статус: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании Yandex RAG: {e}")
        print("Убедитесь, что база данных запущена и доступна")
        return False

async def test_rag_initialization():
    """Тестирует инициализацию RAG системы"""
    print("\n🔍 Тестирование инициализации RAG...")
    
    try:
        # Проверяем, есть ли отдел с ID 5 в базе данных
        from database import SessionLocal
        from models_db import Department, Content
        
        db = SessionLocal()
        department = db.query(Department).filter(Department.id == 5).first()
        
        if not department:
            print("❌ Отдел с ID 5 не найден в базе данных")
            db.close()
            return False
        
        print(f"✅ Найден отдел для тестирования: {department.id} - {department.department_name}")
        
        # Проверяем, есть ли документы в отделе
        content_count = db.query(Content).filter(Content.department_id == 5).count()
        print(f"📄 Количество документов в отделе: {content_count}")
        
        db.close()
        
        if content_count == 0:
            print("❌ В отделе нет документов для инициализации RAG")
            return False
        
        # Импортируем сервис после загрузки переменных окружения
        from yandex_rag_service import YandexRAGService
        
        # Создаем новый экземпляр сервиса
        yandex_rag = YandexRAGService()
        
        # Тестируем инициализацию RAG
        print(f"\n🔄 Инициализация RAG для отдела {department.id}...")
        result = await yandex_rag.initialize_rag(5, force_reload=False)
        
        if result.get("success"):
            print("✅ Инициализация RAG работает")
            print(f"Результат: {result}")
        else:
            print("❌ Ошибка инициализации RAG")
            print(f"Ошибка: {result.get('message', 'Неизвестная ошибка')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании инициализации RAG: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Начинаем тестирование Yandex RAG системы...\n")
    
    # Тестируем Yandex AI сервис
    ai_success = await test_yandex_ai_service()
    
    # Тестируем Yandex RAG сервис
    rag_success = await test_yandex_rag_service()
    
    # Тестируем инициализацию RAG
    init_success = await test_rag_initialization()
    
    print("\n" + "="*50)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"Yandex AI сервис: {'✅ РАБОТАЕТ' if ai_success else '❌ НЕ РАБОТАЕТ'}")
    print(f"Yandex RAG сервис: {'✅ РАБОТАЕТ' if rag_success else '❌ НЕ РАБОТАЕТ'}")
    print(f"Инициализация RAG: {'✅ РАБОТАЕТ' if init_success else '❌ НЕ РАБОТАЕТ'}")
    
    if ai_success and rag_success and init_success:
        print("\n🎉 Все тесты прошли успешно!")
        print("✅ RAG система готова к работе!")
    else:
        print("\n⚠️  Есть проблемы, которые нужно исправить")
        print("\n🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        if not ai_success:
            print("1. Проверьте переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID")
            print("2. Убедитесь, что API ключ действителен")
            print("3. Проверьте подключение к Yandex Cloud")
        if not rag_success:
            print("4. Запустите базу данных: docker-compose up db")
            print("5. Проверьте подключение к базе данных")
        if not init_success:
            print("6. Убедитесь, что в отделе 5 есть документы")
            print("7. Проверьте права доступа к файлам документов")

if __name__ == "__main__":
    asyncio.run(main()) 