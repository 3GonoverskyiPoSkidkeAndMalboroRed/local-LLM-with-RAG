#!/usr/bin/env python3
"""
Тест для прямой проверки адаптера
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_adapter_direct():
    """Прямой тест адаптера"""
    
    print("Прямой тест адаптера...")
    
    try:
        from yandex_cloud_adapter import YandexCloudConfig, YandexCloudAdapter
        
        # Создаем конфигурацию
        print("1. Создаем конфигурацию...")
        config = YandexCloudConfig(
            api_key="test_key",
            folder_id="test_folder",
            embedding_model="text-search-query"
        )
        
        print(f"2. Модель эмбеддингов в конфигурации: {config.embedding_model}")
        
        # Создаем адаптер
        print("3. Создаем адаптер...")
        adapter = YandexCloudAdapter(config)
        
        print(f"4. Модель эмбеддингов в адаптере: {adapter.config.embedding_model}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_adapter_direct() 