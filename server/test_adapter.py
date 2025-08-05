#!/usr/bin/env python3
"""
Тест для проверки адаптера
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_adapter():
    """Тест адаптера"""
    
    print("Тестируем адаптер...")
    
    try:
        from yandex_cloud_adapter import get_yandex_adapter
        
        # Получаем адаптер
        print("1. Получаем адаптер...")
        adapter = await get_yandex_adapter()
        
        print(f"2. Модель эмбеддингов в адаптере: {adapter.config.embedding_model}")
        
        # Тестируем создание эмбеддингов
        print("3. Тестируем создание эмбеддингов...")
        test_texts = ["тестовый текст"]
        embeddings = await adapter.create_embeddings(test_texts, model="text-search-query")
        
        print(f"4. Создано эмбеддингов: {len(embeddings)}")
        if embeddings:
            print(f"   Размерность: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_adapter()) 