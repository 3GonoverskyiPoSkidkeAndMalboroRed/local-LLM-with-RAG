#!/usr/bin/env python3
"""
Тест для проверки размерности эмбеддингов
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yandex_embeddings import create_yandex_embeddings

def test_embedding_dimensions():
    """Тестируем размерности эмбеддингов для разных моделей"""
    
    models = ["text-search-doc", "text-search-query"]
    
    for model in models:
        print(f"\nТестируем модель: {model}")
        try:
            embeddings = create_yandex_embeddings(model=model)
            
            # Тестируем embed_query
            test_text = "тестовый текст"
            result = embeddings.embed_query(test_text)
            print(f"  embed_query размерность: {len(result)}")
            
            # Тестируем embed_documents
            result_docs = embeddings.embed_documents([test_text])
            print(f"  embed_documents размерность: {len(result_docs[0])}")
            
        except Exception as e:
            print(f"  Ошибка: {e}")

if __name__ == "__main__":
    test_embedding_dimensions() 