#!/usr/bin/env python3
"""
Отладочный скрипт для проверки модели
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_model():
    """Отладка модели"""
    
    print("Отладка модели...")
    
    try:
        from yandex_embeddings import create_yandex_embeddings
        
        # Создаем эмбеддинги с разными моделями
        models = ["text-search-doc", "text-search-query"]
        
        for model in models:
            print(f"\nТестируем модель: {model}")
            try:
                embeddings = create_yandex_embeddings(model=model)
                print(f"  Модель в объекте: {embeddings.model}")
                
                # Тестируем создание эмбеддинга
                test_text = "тестовый текст"
                result = embeddings.embed_query(test_text)
                print(f"  Размерность: {len(result)}")
                
            except Exception as e:
                print(f"  Ошибка: {e}")
        
        # Тестируем функцию get_embedding_function
        print(f"\nТестируем get_embedding_function...")
        from document_loader import get_embedding_function
        
        for model in models:
            try:
                embedding_func = get_embedding_function(model)
                print(f"  Модель {model}: {type(embedding_func)}")
                if hasattr(embedding_func, 'model'):
                    print(f"    Модель в объекте: {embedding_func.model}")
            except Exception as e:
                print(f"  Ошибка для модели {model}: {e}")
        
    except Exception as e:
        print(f"Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model() 