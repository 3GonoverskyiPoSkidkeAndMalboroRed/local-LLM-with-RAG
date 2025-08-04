#!/usr/bin/env python3
"""
Отладочный скрипт для проверки создания модели в роутере
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_model_creation():
    """Отладка создания модели"""
    print("Отладка создания модели YandexGPT...")
    
    try:
        from yandex_llm import create_yandex_llm
        
        # Создаем модель
        print("1. Создание модели...")
        llm = create_yandex_llm(
            model="yandexgpt",
            temperature=0.1,
            max_tokens=100
        )
        
        print(f"   Модель создана: {type(llm)}")
        print(f"   model: {llm.model}")
        print(f"   temperature: {llm.temperature}")
        
        # Проверяем атрибуты
        print("\n2. Проверка атрибутов...")
        print(f"   hasattr(model): {hasattr(llm, 'model')}")
        print(f"   getattr(model): {getattr(llm, 'model', 'NOT_FOUND')}")
        
        # Проверяем dir
        print(f"\n3. dir(llm):")
        for attr in dir(llm):
            if 'model' in attr.lower():
                print(f"   {attr}")
        
        # Проверяем __dict__
        print(f"\n4. __dict__:")
        for key, value in llm.__dict__.items():
            if 'model' in key.lower():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_model_creation() 