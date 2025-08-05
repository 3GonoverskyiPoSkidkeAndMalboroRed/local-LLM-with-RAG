#!/usr/bin/env python3
"""
Тест для проверки ChromaDB
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chroma():
    """Тест ChromaDB"""
    
    print("Тестируем ChromaDB...")
    
    try:
        from langchain_community.vectorstores import Chroma
        from yandex_embeddings import create_yandex_embeddings
        
        # Создаем эмбеддинги
        print("1. Создаем эмбеддинги...")
        embeddings = create_yandex_embeddings(model="text-search-query")
        
        # Создаем тестовые документы
        print("2. Создаем тестовые документы...")
        from langchain_core.documents import Document
        documents = [
            Document(page_content="Это тестовый документ для проверки RAG системы.", metadata={"source": "test1.txt"}),
            Document(page_content="RAG система использует векторный поиск для нахождения релевантных документов.", metadata={"source": "test2.txt"})
        ]
        
        # Создаем базу данных
        print("3. Создаем базу данных...")
        db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory="test_chroma"
        )
        
        print("4. База данных создана успешно!")
        
        # Тестируем поиск
        print("5. Тестируем поиск...")
        results = db.similarity_search("как работает RAG", k=2)
        print(f"Найдено результатов: {len(results)}")
        
        for i, doc in enumerate(results):
            print(f"  Результат {i+1}: {doc.page_content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chroma() 