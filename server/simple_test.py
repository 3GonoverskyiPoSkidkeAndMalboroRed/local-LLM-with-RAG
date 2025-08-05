#!/usr/bin/env python3
"""
Простой тест для проверки работы системы
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_loader import load_documents_into_database, vec_search
from yandex_embeddings import create_yandex_embeddings

def test_simple_rag():
    """Простой тест RAG системы"""
    
    print("Тестируем простую RAG систему...")
    
    try:
        # Создаем эмбеддинги
        print("1. Создаем эмбеддинги...")
        embeddings = create_yandex_embeddings(model="text-search-query")
        
        # Загружаем документы в базу
        print("2. Загружаем документы в базу...")
        db = load_documents_into_database(
            model_name="text-search-query",
            documents_path="5",
            department_id="5",
            reload=True
        )
        
        # Выполняем поиск
        print("3. Выполняем поиск...")
        chunks, scores, metadata = vec_search(
            embedding_model=embeddings,
            query="как работает RAG система",
            db=db,
            n_top_cos=5
        )
        
        print(f"4. Результаты:")
        print(f"   Найдено чанков: {len(chunks)}")
        print(f"   Scores: {scores}")
        print(f"   Metadata: {len(metadata)}")
        
        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            print(f"   Чанк {i+1} (score: {score:.3f}): {chunk[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_rag() 