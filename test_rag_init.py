#!/usr/bin/env python3
"""
Тестовый скрипт для инициализации RAG системы
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
from models_db import Department, Content, RAGSession

async def test_rag_initialization():
    """Тестирует инициализацию RAG для отделов"""
    
    # Создаем экземпляр RAG сервиса
    rag_service = YandexRAGService()
    
    # Подключаемся к базе данных
    db = SessionLocal()
    
    try:
        # Получаем список всех отделов
        departments = db.query(Department).all()
        print(f"Найдено отделов: {len(departments)}")
        
        for dept in departments:
            print(f"\n--- Отдел: {dept.department_name} (ID: {dept.id}) ---")
            
            # Проверяем количество документов в отделе
            content_count = db.query(Content).filter(Content.department_id == dept.id).count()
            print(f"Документов в отделе: {content_count}")
            
            if content_count == 0:
                print("Нет документов для инициализации RAG")
                continue
            
            # Проверяем текущий статус RAG
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == dept.id).first()
            if rag_session:
                print(f"RAG статус: {'Инициализирована' if rag_session.is_initialized else 'Не инициализирована'}")
                print(f"Документов в RAG: {rag_session.documents_count}")
                print(f"Чанков в RAG: {rag_session.chunks_count}")
            else:
                print("RAG сессия не найдена")
            
            # Пытаемся инициализировать RAG
            print("Пытаемся инициализировать RAG...")
            try:
                result = await rag_service.initialize_rag(department_id=dept.id, force_reload=False)
                print(f"Результат: {result}")
            except Exception as e:
                print(f"Ошибка при инициализации: {e}")
                
    except Exception as e:
        print(f"Общая ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Запуск тестирования RAG инициализации...")
    asyncio.run(test_rag_initialization())
    print("Тестирование завершено.")
