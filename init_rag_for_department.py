#!/usr/bin/env python3
"""
Скрипт для инициализации RAG для конкретного отдела
"""

import asyncio
import sys
import os

# Добавляем путь к серверу
sys.path.append('server')

# Устанавливаем переменные окружения
os.environ.setdefault('DATABASE_URL', 'mysql+mysqlconnector://root:123123@localhost:3306/db_test')

from yandex_rag_service import YandexRAGService
from database import SessionLocal
from models_db import Department, Content, RAGSession, DocumentChunk

async def init_rag_for_department(department_id: int, force_reload: bool = True):
    """Инициализирует RAG для конкретного отдела"""
    
    print(f"🚀 Инициализация RAG для отдела {department_id}")
    
    # Создаем экземпляр RAG сервиса
    rag_service = YandexRAGService()
    
    # Подключаемся к базе данных
    db = SessionLocal()
    
    try:
        # Проверяем существование отдела
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            print(f"❌ Отдел с ID {department_id} не найден")
            return False
        
        print(f"📁 Отдел: {department.department_name}")
        
        # Проверяем документы
        contents = db.query(Content).filter(Content.department_id == department_id).all()
        print(f"📄 Документов в отделе: {len(contents)}")
        
        if not contents:
            print("❌ Нет документов для инициализации RAG")
            return False
        
        # Показываем документы
        for content in contents:
            print(f"   - {content.title} (ID: {content.id})")
            print(f"     Путь: {content.file_path}")
        
        # Проверяем текущий статус RAG
        rag_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
        if rag_session:
            print(f"📊 Текущий RAG статус:")
            print(f"   Инициализирована: {'✅ Да' if rag_session.is_initialized else '❌ Нет'}")
            print(f"   Документов в RAG: {rag_session.documents_count}")
            print(f"   Чанков в RAG: {rag_session.chunks_count}")
        
        # Проверяем существующие чанки
        existing_chunks = db.query(DocumentChunk).filter(DocumentChunk.department_id == department_id).count()
        print(f"🔍 Существующих чанков: {existing_chunks}")
        
        if force_reload and existing_chunks > 0:
            print("🗑️ Удаляем существующие чанки (force_reload=True)")
            db.query(DocumentChunk).filter(DocumentChunk.department_id == department_id).delete()
            db.commit()
        
        # Инициализируем RAG
        print("⚙️ Запускаем инициализацию RAG...")
        result = await rag_service.initialize_rag(department_id=department_id, force_reload=force_reload)
        
        print(f"📋 Результат инициализации:")
        print(f"   Успех: {'✅ Да' if result.get('success') else '❌ Нет'}")
        print(f"   Сообщение: {result.get('message', 'Нет сообщения')}")
        print(f"   Обработано документов: {result.get('documents_processed', 0)}")
        print(f"   Создано чанков: {result.get('chunks_created', 0)}")
        
        # Проверяем результат
        if result.get('success'):
            # Проверяем новые чанки
            new_chunks = db.query(DocumentChunk).filter(DocumentChunk.department_id == department_id).count()
            print(f"🔍 Новых чанков после инициализации: {new_chunks}")
            
            # Проверяем обновленный статус RAG
            updated_session = db.query(RAGSession).filter(RAGSession.department_id == department_id).first()
            if updated_session:
                print(f"📊 Обновленный RAG статус:")
                print(f"   Инициализирована: {'✅ Да' if updated_session.is_initialized else '❌ Нет'}")
                print(f"   Документов в RAG: {updated_session.documents_count}")
                print(f"   Чанков в RAG: {updated_session.chunks_count}")
                print(f"   Последнее обновление: {updated_session.last_updated}")
            
            return True
        else:
            print(f"❌ Ошибка инициализации: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False
    finally:
        db.close()

async def test_rag_query(department_id: int):
    """Тестирует RAG запрос для отдела"""
    
    print(f"\n🔍 Тестирование RAG запроса для отдела {department_id}")
    
    rag_service = YandexRAGService()
    
    try:
        # Проверяем статус
        status = await rag_service.get_rag_status(department_id)
        print(f"📊 RAG статус: {status}")
        
        if status.get('is_initialized', False):
            # Пробуем сделать запрос
            result = await rag_service.query_rag(
                department_id=department_id,
                question="Что такое RAG система?"
            )
            print(f"💬 Результат запроса:")
            print(f"   Ответ: {result.get('answer', 'Нет ответа')}")
            print(f"   Источники: {len(result.get('sources', []))}")
            print(f"   Использовано контекста: {result.get('context_used', 0)}")
        else:
            print("❌ RAG не инициализирована для этого отдела")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

async def main():
    """Основная функция"""
    
    print("🎯 Инициализация RAG для отделов")
    print("=" * 50)
    
    # Список отделов для инициализации
    departments_to_init = [1, 5]  # Отделы с документами
    
    for dept_id in departments_to_init:
        print(f"\n{'='*50}")
        success = await init_rag_for_department(dept_id, force_reload=True)
        
        if success:
            await test_rag_query(dept_id)
        
        print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(main())
