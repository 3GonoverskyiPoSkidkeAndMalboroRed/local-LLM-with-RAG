#!/usr/bin/env python3
"""
Тест для прямой проверки эмбеддингов
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_embeddings_direct():
    """Прямой тест эмбеддингов"""
    
    print("Прямой тест эмбеддингов...")
    
    try:
        from yandex_embeddings import YandexEmbeddings
        
        # Создаем эмбеддинги напрямую
        print("1. Создаем эмбеддинги напрямую...")
        embeddings = YandexEmbeddings(model="text-search-query")
        
        print(f"2. Модель в объекте: {embeddings.model}")
        
        # Тестируем создание эмбеддинга
        print("3. Тестируем создание эмбеддинга...")
        test_text = "тестовый текст"
        result = embeddings.embed_query(test_text)
        print(f"4. Размерность: {len(result)}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_embeddings_direct() 