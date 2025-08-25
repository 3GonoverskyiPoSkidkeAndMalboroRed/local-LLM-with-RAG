#!/usr/bin/env python3
"""
Скрипт для проверки документов в отделах
"""

import sys
import os

# Добавляем путь к серверу
sys.path.append('server')

# Устанавливаем переменные окружения
os.environ.setdefault('DATABASE_URL', 'mysql+mysqlconnector://root:123123@localhost:3306/db_test')

from database import SessionLocal
from models_db import Department, Content, RAGSession, DocumentChunk

def check_documents():
    """Проверяет документы в отделах"""
    
    db = SessionLocal()
    
    try:
        print("=== Проверка документов в отделах ===\n")
        
        # Получаем все отделы
        departments = db.query(Department).all()
        
        for dept in departments:
            print(f"📁 Отдел: {dept.department_name} (ID: {dept.id})")
            
            # Получаем документы отдела
            contents = db.query(Content).filter(Content.department_id == dept.id).all()
            print(f"   Документов: {len(contents)}")
            
            if contents:
                for content in contents:
                    print(f"   - {content.title} (ID: {content.id})")
                    print(f"     Путь: {content.file_path}")
                    print(f"     Доступ: {content.access_level}")
                    print(f"     Тег: {content.tag_id}")
                    print()
            else:
                print("   Нет документов")
                print()
            
            # Проверяем RAG статус
            rag_session = db.query(RAGSession).filter(RAGSession.department_id == dept.id).first()
            if rag_session:
                print(f"   RAG статус: {'✅ Инициализирована' if rag_session.is_initialized else '❌ Не инициализирована'}")
                print(f"   Документов в RAG: {rag_session.documents_count}")
                print(f"   Чанков в RAG: {rag_session.chunks_count}")
                print(f"   Последнее обновление: {rag_session.last_updated}")
            else:
                print("   RAG сессия не найдена")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

def check_rag_chunks():
    """Проверяет чанки RAG"""
    
    db = SessionLocal()
    
    try:
        print("\n=== Проверка чанков RAG ===\n")
        
        chunks = db.query(DocumentChunk).all()
        print(f"Всего чанков: {len(chunks)}")
        
        if chunks:
            for chunk in chunks:
                print(f"Чанк {chunk.id}:")
                print(f"  Документ: {chunk.content_id}")
                print(f"  Отдел: {chunk.department_id}")
                print(f"  Индекс: {chunk.chunk_index}")
                print(f"  Текст: {chunk.chunk_text[:100]}...")
                print(f"  Эмбеддинг: {'Есть' if chunk.embedding_vector else 'Нет'}")
                print(f"  Изображения: {'Есть' if chunk.images else 'Нет'}")
                print()
        else:
            print("Чанки не найдены")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_documents()
    check_rag_chunks()
