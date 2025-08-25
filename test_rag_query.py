#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы RAG системы
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

async def test_rag_query():
    """Тестирует запросы к RAG системе"""
    
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
            
            # Проверяем статус RAG
            try:
                status = await rag_service.get_rag_status(dept.id)
                print(f"RAG статус: {status}")
                
                # Если RAG инициализирована, пробуем сделать запрос
                if status.get('is_initialized', False):
                    print("Пробуем выполнить RAG запрос...")
                    try:
                        result = await rag_service.query_rag(
                            department_id=dept.id,
                            question="Что такое RAG система?"
                        )
                        print(f"Результат запроса: {result}")
                    except Exception as e:
                        print(f"Ошибка при выполнении запроса: {e}")
                else:
                    print("RAG не инициализирована для этого отдела")
                    
            except Exception as e:
                print(f"Ошибка при получении статуса: {e}")
                
    except Exception as e:
        print(f"Общая ошибка: {e}")
    finally:
        db.close()

async def check_database_content():
    """Проверяет содержимое базы данных RAG"""
    
    db = SessionLocal()
    
    try:
        print("\n=== Проверка содержимого базы данных ===")
        
        # Проверяем RAG сессии
        rag_sessions = db.query(RAGSession).all()
        print(f"RAG сессий: {len(rag_sessions)}")
        for session in rag_sessions:
            print(f"  - Отдел {session.department_id}: инициализирована={session.is_initialized}, документов={session.documents_count}, чанков={session.chunks_count}")
        
        # Проверяем чанки документов
        chunks = db.query(DocumentChunk).all()
        print(f"Чанков документов: {len(chunks)}")
        for chunk in chunks[:5]:  # Показываем первые 5
            print(f"  - Чанк {chunk.id}: документ={chunk.content_id}, отдел={chunk.department_id}, индекс={chunk.chunk_index}")
        
        # Проверяем документы
        contents = db.query(Content).all()
        print(f"Документов: {len(contents)}")
        for content in contents[:5]:  # Показываем первые 5
            print(f"  - Документ {content.id}: {content.title}, отдел={content.department_id}")
            
    except Exception as e:
        print(f"Ошибка при проверке БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Запуск тестирования RAG запросов...")
    asyncio.run(check_database_content())
    asyncio.run(test_rag_query())
    print("Тестирование завершено.")
