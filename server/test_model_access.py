#!/usr/bin/env python3
"""
Простой тест для проверки доступа к полям модели YandexGPT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yandex_llm import YandexGPT, create_yandex_llm

def test_model_creation():
    """Тест создания модели"""
    print("🔍 Тестирование создания модели YandexGPT...")
    
    try:
        # Тест 1: Создание через конструктор
        print("1. Создание через конструктор...")
        llm1 = YandexGPT(model="test-model", temperature=0.5)
        print(f"   ✅ Модель создана: {llm1.model}")
        print(f"   ✅ Температура: {llm1.temperature}")
        
        # Тест 2: Создание через фабричную функцию
        print("2. Создание через фабричную функцию...")
        llm2 = create_yandex_llm(model="test-model-2", temperature=0.7)
        print(f"   ✅ Модель создана: {llm2.model}")
        print(f"   ✅ Температура: {llm2.temperature}")
        
        # Тест 3: Проверка _identifying_params
        print("3. Проверка _identifying_params...")
        params = llm1._identifying_params
        print(f"   ✅ Параметры: {params}")
        
        # Тест 4: Проверка доступа к атрибутам
        print("4. Проверка доступа к атрибутам...")
        print(f"   ✅ model: {llm1.model}")
        print(f"   ✅ temperature: {llm1.temperature}")
        print(f"   ✅ max_tokens: {llm1.max_tokens}")
        print(f"   ✅ timeout: {llm1.timeout}")
        
        print("✅ Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_model_creation() 